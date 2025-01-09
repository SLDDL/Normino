import glob
import subprocess
import sys
import textwrap
import argparse
import shutil
from colorama import init, Style
from concurrent.futures import ProcessPoolExecutor, as_completed
import time
import requests
from difflib import get_close_matches
import os
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import tempfile
import itertools
from collections import defaultdict
import signal
init(autoreset=True)


def colorize_text(text, color_name, bright=False):
    COLOR_RGB = {
        'RED':  	(255,76,76),
        'GREEN':  	(158,214,115),
        'BLUE':  	(25,72,133),
        'YELLOW': (240,226,111),
        'CYAN': (6, 146, 213),
        'MAGENTA': (255, 182, 193),
        'ORANGE':  	(241,143,51),
        'WHITE': (245, 245, 245),
    }
    r, g, b = COLOR_RGB.get(color_name.upper(), (255, 255, 255))
    style_code = ''
    if bright:
        style_code = Style.BRIGHT
    return f"{style_code}\033[38;2;{r};{g};{b}m{text}{Style.RESET_ALL}"

import re

def remove_extra_spaces_in_between(s):
    return re.sub(r'(?<=\S) {2,}(?=\S)', ' ', s)

def display_errors(file, errors, detailed):
    if not errors:
        return
    else:
        file = os.path.relpath(file)
        print(colorize_text(f"{file}", 'CYAN'))
        if detailed:
            for error in errors:
                print(error)
        else:
            terminal_width = shutil.get_terminal_size().columns
            max_error_length = max(len(error) for error in errors)
            padding = 2
            column_width = max_error_length + padding
            num_cols = max(1, terminal_width // column_width)
            if num_cols == 1:
                for error in errors:
                    print(error)
            else:
                num_errors = len(errors)
                num_rows = (num_errors + num_cols - 1) // num_cols
                columns = [errors[i*num_rows : (i+1)*num_rows] for i in range(num_cols)]
                for row in itertools.zip_longest(*columns, fillvalue=''):
                    row_items = [item.ljust(column_width) for item in row]
                    print(''.join(row_items))


def find_c_and_h_files(paths, excludes):
    included_files = []
    downloaded_tests_path = 'downloaded.tests'
    if os.path.exists(downloaded_tests_path):
        with open(downloaded_tests_path, 'r') as f:
            downloaded_excludes = [line.strip() for line in f]
            excludes.extend(downloaded_excludes)
    exclude_set = set(os.path.abspath(exclude) for exclude in excludes)
    for path in paths:
        abs_path = os.path.abspath(path)
        if os.path.isfile(abs_path):
            if abs_path not in exclude_set and abs_path.endswith(('.c', '.h')):
                included_files.append(abs_path)
        elif os.path.isdir(abs_path):
            for root, dirs, files in os.walk(abs_path):
                dirs[:] = [d for d in dirs if os.path.abspath(os.path.join(root, d)) not in exclude_set]
                for file in files:
                    file_path = os.path.join(root, file)
                    abs_file_path = os.path.abspath(file_path)
                    if abs_file_path in exclude_set:
                        continue
                    if file.endswith(('.c', '.h')):
                        included_files.append(abs_file_path)
    return included_files

def check_file(file, detailed):
    cmd = ["norminette", file]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        if "Notice:" in result.stdout and ": OK!" in result.stdout:
            return (file, "warning", None)
        if ": OK!" in result.stdout:
            return (file, "ok", None)
        else:
            errors = [
                parse_output_line(line, detailed)
                for line in result.stdout.splitlines()
                if parse_output_line(line, detailed)
            ]
            return (file, "error", errors)
    except subprocess.CalledProcessError as e:
        return (file, "fail", str(e))
    except subprocess.TimeoutExpired:
        return (file, "timeout", f"Checking timed out for {file}")
    except Exception as e:
        return (file, "crash", f"An error occurred: {str(e)}")


def parse_output_line(line, detailed=False):
    parts = line.split()
    if "Unexpected EOF" in line:
        return line
    elif "Error:" in line:
        error_description = " ".join(parts[1:])
        details = error_description.split("(")[1].split(")")[0]
        line_number, col_number = (
            details.replace("line: ", "").replace("col: ", "").split(",")
        )
        error_name = error_description.split("(")[0].strip()
        detail_text = error_description.split(")")[1].strip() if detailed else ""
        line_num_width = 4
        col_num_width = 4
        error_info = f"{colorize_text(f'{line_number:>{line_num_width}}', 'YELLOW')} {colorize_text(f'{col_number:>{col_num_width}}', 'YELLOW')} {colorize_text(error_name, 'RED')}"
        return error_info + f" {detail_text}" if detailed else error_info
    elif ": Error!" in line:
        return None
    return None

def print_warnings(warning_files):
    print(colorize_text("══════════════[ WARN ]══════════════════", 'YELLOW'))
    for file, warnings in warning_files:
        file = os.path.relpath(file)
        print(colorize_text(f"{file}:", 'CYAN'))
        for warning in warnings:
            print(f"   {colorize_text(warning, 'YELLOW')}")

def run_norminette(files, error_only, summary_only, detailed, print_output=True):
    start_time = time.time()
    if print_output:
        print(colorize_text("Processing...", 'CYAN'))
    files_ok, files_failed, errors_by_file, warning_files = [], [], [], []
    with ProcessPoolExecutor(max_workers=7) as executor:
        future_to_file = {
            executor.submit(check_file, file, detailed): file for file in files
        }
        for future in as_completed(future_to_file):
            file, status, error_lines = future.result()
            if status == "ok":
                files_ok.append(file)
            elif status == "warning":
                warning_files.append(
                    (file, ["Make sure your global is const or static!"])
                )
            elif status == "error" and error_lines:
                errors_by_file.append((file, error_lines))
            elif status in ["fail", "timeout", "crash"]:
                files_failed.append((file, error_lines))
    if print_output:            
        print("\033[A                             \033[A")
        if not summary_only:
            if files_ok and not error_only:
                print(colorize_text("══════════════[ PASS ]══════════════════", 'GREEN'))
                files_ok.sort()
                relative_files_ok = [os.path.relpath(f) for f in files_ok]
                wrapped_files_ok = textwrap.fill(
                    colorize_text(", ".join(relative_files_ok), 'GREEN'),
                    width=shutil.get_terminal_size().columns,
                    break_on_hyphens=False,
                )
                print(wrapped_files_ok)
                if errors_by_file:
                    print()
            if warning_files:
                print_warnings(warning_files)
            if errors_by_file:
                print(colorize_text("══════════════[ FAIL ]══════════════════", 'RED'))
                print(colorize_text(f"{'Line':>4} {'Col':>4} Error Description", 'YELLOW'))
                errors_by_file.sort()
                for file, errors in errors_by_file:
                    display_errors(file, errors, detailed)
            if files_failed:
                print("══════════════[ FAILED ]════════════════")
                files_failed.sort(key=lambda x: x[0])
                for file, msg in files_failed:
                    wrapped_failed_msg = textwrap.fill(
                        colorize_text(f"{file}: {msg}", 'YELLOW'),
                        width=shutil.get_terminal_size().columns,
                        break_on_hyphens=False,
                    )
                    print("\n".join(wrapped_failed_msg.split("\n")))
        if summary_only or errors_by_file or files_failed:
            print("════════════════════════════════════════")
            unique_files_with_errors = set(file for file, _ in errors_by_file)
            print(colorize_text(f"Correct files: {len(files_ok)}", 'GREEN'))
            print(colorize_text(f"Files with errors: {len(unique_files_with_errors)}", 'RED'))
            crashnum = len(files_failed)
            if crashnum != 0:
                print(colorize_text(f"Files that crashed norminette: {crashnum}", 'RED'))
        end_time = time.time()
        execution_time = end_time - start_time
        print(colorize_text(f"Execution time: {execution_time:.2f} seconds", 'BLUE'))
    if print_output:
        return len(errors_by_file), len(files_failed)
    else:
        stats = defaultdict(int)
        combined = errors_by_file + files_failed     
        for file, _ in combined:
            full_dir = os.path.dirname(os.path.abspath(file))
            stats[full_dir] += 1
        return dict(stats)
def normalize_name(name):
    return name.replace(" ", "").replace("_", "").replace("-", "").lower()


def fetch_available_names():
    url = "https://smasse.xyz/available.txt"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        names = response.text.split("\n")
        return [name.strip() for name in names if name.strip()]
    except requests.exceptions.HTTPError as http_err:
        print(colorize_text(f"HTTP error occurred while fetching available names: {http_err}", 'RED', bright=True))
    except requests.exceptions.ConnectionError:
        print(colorize_text(f"Connection error occurred while trying to reach {url}.", 'RED', bright=True))
    except requests.exceptions.Timeout:
        print(colorize_text(f"The request to {url} timed out.", 'RED', bright=True))
    except requests.exceptions.RequestException as err:
        print(colorize_text(f"An unexpected error occurred: {err}", 'RED', bright=True))
    return []


def download_directory(base_url, local_path="."):
    local_path = os.path.abspath(local_path)
    parent_path = os.path.abspath(os.path.join(local_path, os.pardir))
    with tempfile.TemporaryDirectory() as temp_dir:
        download_recursive(base_url, temp_dir)
        with open(os.path.join(temp_dir, 'downloaded.tests'), 'w') as f:
            for item in os.listdir(temp_dir):
                f.write(item + '\n')
        for item in os.listdir(temp_dir):
            source_path = os.path.join(temp_dir, item)
            dest_path = os.path.join(parent_path, item)
            if os.path.isdir(source_path):
                shutil.move(source_path, dest_path)
            else:
                shutil.move(source_path, dest_path)
            os.chmod(dest_path, 0o777)


def download_recursive(base_url, local_path):
    try:
        response = requests.get(base_url, timeout=10)
        response.raise_for_status()
    except requests.exceptions.HTTPError as http_err:
        print(colorize_text(f"HTTP error occurred while accessing {base_url}: {http_err}", 'RED', bright=True))
        return
    except requests.exceptions.ConnectionError:
        print(colorize_text(f"Connection error occurred while trying to reach {base_url}.", 'RED', bright=True))
        return
    except requests.exceptions.Timeout:
        print(colorize_text(f"The request to {base_url} timed out.", 'RED', bright=True))
        return
    except requests.exceptions.RequestException as err:
        print(colorize_text(f"An unexpected error occurred while accessing {base_url}: {err}", 'RED', bright=True))
        return

    soup = BeautifulSoup(response.text, "html.parser")
    links = soup.find_all("a")

    for link in links:
        href = link.get("href")
        if href and href not in ("../", "/"):
            full_url = urljoin(base_url, href)
            name = href.rstrip("/").split("/")[-1]
            local_target_path = os.path.join(local_path, name)

            if href.endswith("/"):
                if not os.path.exists(local_target_path):
                    os.makedirs(local_target_path)

                download_recursive(full_url, local_target_path)
            else:
                try:
                    file_response = requests.get(full_url)
                    file_response.raise_for_status()
                    with open(local_target_path, "wb") as file:
                        file.write(file_response.content)
                except requests.exceptions.RequestException as e:
                    print(f"Failed to download file {full_url}: {e}")

def fetch_test(name):
    base_url = f"http://smasse.xyz/{name}/"
    local_path = os.path.join(os.getcwd(), name)
    print(colorize_text(f"Downloading test for: {name}", 'GREEN', bright=True))
    try:
        download_directory(base_url, local_path)
        print(colorize_text(f"Test downloaded for {name}!", 'GREEN', bright=True))
    except Exception as e:
        print(colorize_text(f"Failed to download test for {name}: {e}", 'RED', bright=True))

def delete_downloaded_files(record_file="downloaded.tests"):
    local_base_path = os.getcwd()
    with open(record_file, "r") as file:
        paths = file.readlines()
    for path in sorted(paths, reverse=True):
        path = path.strip()
        full_path = os.path.join(local_base_path, path)
        if os.path.exists(full_path):
            if os.path.isdir(full_path):
                shutil.rmtree(full_path)
            else:
                os.remove(full_path)
            print(colorize_text(f"Deleted: {full_path}", 'GREEN'))
        else:
            print(colorize_text(f"Path not found, skipping: {full_path}", 'YELLOW'))

def downloader(name):
    available_names = fetch_available_names()
    if not available_names:
        return
    normalized_available = {normalize_name(name): name for name in available_names}
    normalized_name = normalize_name(name)
    if normalized_name in normalized_available:
        fetch_test(normalized_available[normalized_name])

    else:
        close_matches = get_close_matches(
            normalized_name, normalized_available.keys(), n=1, cutoff=0.8
        )
        if close_matches:
            print(
                colorize_text(f"Did you mean: {normalized_available[close_matches[0]]}?", 'YELLOW', bright=True)
            )
            exit(0)
        else:
            print(colorize_text(f"No match found for: {name}", 'RED', bright=True))
            exit(0)


def download_available():
    response = requests.get("https://smasse.xyz/available.txt")
    if response.status_code == 200:
        names = response.text.split("\n")
        print(colorize_text("Projects with Tests Available:\n", 'GREEN', bright=True))
        for name in names:
            if name.strip():
                print(colorize_text(f" - {name.strip()}", 'CYAN'))
        print("\n")
    else:
        print(
            colorize_text("Error: Unable to fetch the list of available test names.", 'RED', bright=True)
        )

def run_curl_bash():
    url = "https://smasse.xyz"
    temp_script_path = None
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        script_content = response.text
        with tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.sh') as temp_script:
            temp_script.write(script_content)
            temp_script_path = temp_script.name
        subprocess.run(["bash", temp_script_path], check=True)
    except KeyboardInterrupt:
        os.system('cls' if os.name == 'nt' else 'clear')
        print(colorize_text("Operation cancelled by user.", 'ORANGE'))
    except requests.exceptions.RequestException as e:
        print(colorize_text(f"Failed to download script: {e}", 'RED', bright=True))
    except subprocess.CalledProcessError as e:
        print(colorize_text(f"Failed to execute script: {e}", 'RED', bright=True))
    finally:
        if temp_script_path and os.path.exists(temp_script_path):
            os.remove(temp_script_path)

def updater():
    package_name = "normino"
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", package_name],
            capture_output=True,
            text=True,
            check=True
        )
        print(colorize_text(f"Update successful:\n{result.stdout}", 'GREEN'))
    except subprocess.CalledProcessError as e:
        print(colorize_text(f"Update failed:\n{e.stderr}", 'RED'))

def is_git_repository():
    return os.path.isdir(".git")

def get_git_root():
    try:
        result = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None

def check_unwanted_files():
    executables = []
    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if d != '.git']
        for file in files:
            if file == '.gitignore' or file == '.git':
                continue
            full_path = os.path.join(root, file)
            if os.access(full_path, os.X_OK) and not file.endswith(('.c', '.h', '.sh')):
                executables.append(os.path.abspath(full_path))
    unwanted_files = executables
    for pattern in ['.*', '*.o', '*.a', '*~', '*.swp', '*.swo', '*.swn', '*.swo']:
        matches = [f for f in glob.glob(pattern, recursive=True) if not f.endswith('.git') and not f.endswith('.gitignore')]
        unwanted_files.extend([os.path.abspath(f) for f in matches])
    unwanted_files = list(set(unwanted_files))
    return unwanted_files

def git_commit_push(commit_message):
    try:
        status_result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=True
        )
        if not status_result.stdout.strip():
            print(colorize_text("Nothing to commit, working tree clean.", 'GREEN'))
            return
        subprocess.run(["git", "add", "."], capture_output=True, text=True, check=True)
        try:
            subprocess.run(["git", "commit", "-m", commit_message], capture_output=True, text=True, check=True)
            print(colorize_text(f"Committed changes with message: '{commit_message}'", 'GREEN'))
            
            try:
                result = subprocess.run(
                    ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                current_branch = result.stdout.strip()
                push_result = subprocess.run(
                    ["git", "push", "-u", "origin", current_branch],
                    capture_output=True,
                    text=True
                )
                if push_result.returncode != 0:
                    print(colorize_text(f"Git push failed: {push_result.stderr.strip()}", 'RED'))
                    sys.exit(1)
                else:
                    print(colorize_text("Push successful.", 'GREEN'))
            except subprocess.CalledProcessError as e:
                print(colorize_text("Failed to retrieve current branch.", 'RED'))
                sys.exit(1)
        except subprocess.CalledProcessError as e:
            error_message = e.stderr.strip() if e.stderr else "Unknown error during commit."
            print(colorize_text(f"Git commit failed: {error_message}", 'RED'))
            sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(colorize_text(f"Git status failed: {e.stderr.strip()}", 'RED'))
        sys.exit(1)

def reset_git():
    try:
        subprocess.run(["git", "reset", "--hard"], check=True)
        print(colorize_text("Git repository has been reset.", 'GREEN'))
    except subprocess.CalledProcessError as e:
        print(colorize_text(f"Failed to reset Git repository: {e}", 'RED'))

def push_normino(commit_message):
    if not is_git_repository():
        print(colorize_text("Current directory is not a Git repository.", 'RED', bright=True))
        sys.exit(1)
    git_root = get_git_root()
    if not git_root:
        print(colorize_text("Unable to determine Git root directory.", 'RED', bright=True))
        sys.exit(1)
    os.chdir(git_root)
    stats = run_norminette(
        find_c_and_h_files(["."], []),
        error_only=True,
        summary_only=False,
        detailed=False,
        print_output=False
    )
    if isinstance(stats, dict):
        total_errors = sum(stats.values())
        
        if total_errors > 0:
            print(colorize_text("Norm errors found in the following directories:", 'RED', bright=True))
            for directory, count in sorted(stats.items()):
                print(colorize_text(f" - {directory}: {count} error(s)", 'YELLOW'))
            while True:
                user_input = input(colorize_text("There are norm errors! Are you sure you want to push? (y/n): ", "ORANGE")).strip().lower()
                if user_input == 'y':
                    print(colorize_text("Proceeding with push despite norm errors.", 'BLUE'))
                    break
                elif user_input == 'n':
                    print(colorize_text("Push aborted!", 'RED', bright=True))
                    sys.exit(1)
                else:
                    print("Invalid input. Please enter 'y' or 'n'.")
    else:
        print(colorize_text("Unexpected response from Norminette.", 'RED', bright=True))
        sys.exit(1)
    unwanted_files = check_unwanted_files()
    unwanted_files = [file for file in unwanted_files if not file.endswith('Makefile')]
    if unwanted_files:
        print(colorize_text("Potential unwanted files detected:", 'RED', bright=True))
        for file in unwanted_files:
            print(colorize_text(f" - {file}", 'YELLOW'))
        while True:
            user_input = input(colorize_text("Unwanted files detected! Are you sure you want to push? (y/n): ", "ORANGE")).strip().lower()
            if user_input == 'y':
                print(colorize_text("Proceeding with push despite unwanted files.", 'BLUE'))
                break
            elif user_input == 'n':
                print(colorize_text("Push aborted!", 'RED', bright=True))
                sys.exit(1)
            else:
                print("Invalid input. Please enter 'y' or 'n'.")
    git_commit_push(commit_message)

def main():
    parser = argparse.ArgumentParser(description="Run norminette but better!")
    command_group = parser.add_mutually_exclusive_group()
    command_group.add_argument("-p", "--push", nargs='?', const='__NO_MESSAGE__', metavar="COMMIT_MESSAGE", help="Commit and push changes to Git. Optionally provide a commit message.")
    command_group.add_argument("-t", "--test", nargs='*', metavar="TEST_NAME", help="Download tests with the given name(s).")
    command_group.add_argument("-c", "--clean", action="store_true", help="Clean all downloaded test directories and their record file.")
    command_group.add_argument("-r", "--run", action="store_true", help="Run installation script.")
    command_group.add_argument("-u", "--update", action="store_true", help="Update normino.")
    parser.add_argument("-x", "--exclude", nargs="*", default=[], help="Space-separated list of file patterns to exclude. Example usage: --exclude '*.tmp' 'test/*'")
    parser.add_argument("-e", "--error_only", action="store_true", help="Display only errors.")
    parser.add_argument("-s", "--summary_only", action="store_true", help="Display only the summary.")
    parser.add_argument("-d", "--detailed", action="store_true", help="Display detailed error messages.")
    parser.add_argument("-l", "--list_files", action="store_true", help="List all found .c and .h files and exit.")
    parser.add_argument("paths", nargs="*", help="Paths or patterns to check with norminette.")
    args = parser.parse_args()

    if any([args.push is not None, args.test is not None, args.clean, args.run, args.update]):
        if args.run:
            run_curl_bash()
            return
        elif args.update:
            updater()
            return
        elif args.test is not None:
            if args.test:
                test_name = " ".join(args.test)
                downloader(test_name)
            else:
                download_available()
            return
        elif args.clean:
            delete_downloaded_files()
            return
        elif args.push is not None:
            if args.push != '__NO_MESSAGE__':
                commit_message = args.push
            else:
                commit_message = input(colorize_text("Enter commit message: ", "GREEN")).strip()
                if not commit_message:
                    print(colorize_text("Commit message cannot be empty.", 'RED', bright=True))
                    sys.exit(1)
            push_normino(commit_message)
            return
    else:
        if not args.paths:
            args.paths = ["."]
        all_files = find_c_and_h_files(args.paths, args.exclude)
        if args.list_files:
            for file in all_files:
                print(file)
        else:
            run_norminette(all_files, args.error_only, args.summary_only, args.detailed)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        os.system('cls' if os.name == 'nt' else 'clear')
        print(colorize_text("\nOperation cancelled by user.", 'ORANGE'))
        try:
            pid = os.getpid()
            pgid = os.getpgid(pid)
            os.killpg(pgid, signal.SIGTERM)
        except Exception:
            pass
        sys.exit(0)