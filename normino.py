import subprocess
import textwrap
import argparse
import shutil
from colorama import init, Fore, Style
from concurrent.futures import ProcessPoolExecutor, as_completed
import time
import requests
from difflib import get_close_matches
import os
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import tempfile

init(autoreset=True)


def colorize_text(text, color):
    return f"{color}{text}{Style.RESET_ALL}"


def display_errors(errors, detailed):
    column_width = shutil.get_terminal_size().columns
    if column_width > 137 and not detailed:
        column_width //= 2
        print(errors[0])
        for i in range(1, len(errors), 2):
            left = textwrap.fill(
                errors[i], width=column_width, subsequent_indent="    "
            )
            right = textwrap.fill(
                errors[i + 1] if i + 1 < len(errors) else "",
                width=column_width,
                subsequent_indent="    ",
            )
            print(f"{left:<{column_width}}{right}")
    else:
        for error in errors:
            print(error)


def find_c_and_h_files(path, excludes):
    path = os.path.abspath(path)
    find_all_command = [
        "find",
        path,
        "-type",
        "f",
        "(",
        "-name",
        "*.c",
        "-o",
        "-name",
        "*.h",
        ")",
    ]
    try:
        result_all = subprocess.run(
            find_all_command, text=True, capture_output=True, check=True
        )
        all_files = result_all.stdout.strip().split("\n")
    except subprocess.CalledProcessError as e:
        print(f"Error during file search: {e.stderr.strip()}")
        exit(1)
    excluded_files = set()
    for pattern in excludes:
        exclude_path = os.path.abspath(pattern)
        find_exclude_command = [
            "find",
            exclude_path,
            "-type",
            "f",
            "(",
            "-name",
            "*.c",
            "-o",
            "-name",
            "*.h",
            ")",
        ]
        try:
            result_exclude = subprocess.run(
                find_exclude_command, text=True, capture_output=True, check=True
            )
            excluded_files.update(result_exclude.stdout.strip().split("\n"))
        except subprocess.CalledProcessError as e:
            print(f"Error during exclusion search: {e.stderr.strip()}")

    included_files = [file for file in all_files if file and file not in excluded_files]
    return included_files


def parce_notice_line(line, detailed=False):
    if "Notice:" in line:
        return f"{colorize_text(line, Fore.YELLOW)}"


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
    file_path = parts[0].split(":")[0]
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
        error_info = f"\t{colorize_text(line_number, Fore.YELLOW)}\t{colorize_text(col_number, Fore.YELLOW)}     {colorize_text(error_name, Fore.RED)}"
        return error_info + f" {detail_text}" if detailed else error_info
    elif ": Error!" in line:
        return f"{colorize_text(file_path, Fore.CYAN)}"
    return None


def run_norminette(files, error_only, summary_only, detailed):
    start_time = time.time()
    print(colorize_text("Processing...", Fore.CYAN))
    files_ok, files_failed, errors_by_file = [], [], []
    with ProcessPoolExecutor(max_workers=7) as executor:
        future_to_file = {
            executor.submit(check_file, file, detailed): file for file in files
        }
        for future in as_completed(future_to_file):
            file, status, error_lines = future.result()
            if status == "ok":
                files_ok.append(file)
            elif status == "warning":
                files_ok.append(file)
                errors_by_file.append(
                    (file, [f"{file}: Make sure your global is const or static!"])
                )
            elif status == "error" and error_lines:
                errors_by_file.append((file, error_lines))
            elif status in ["fail", "timeout", "crash"]:
                files_failed.append((file, error_lines))
    print("\033[A                             \033[A")
    if not summary_only:
        if files_ok and not error_only:
            print(colorize_text("══════════════[ PASS ]══════════════════", Fore.GREEN))
            files_ok.sort()
            wrapped_files_ok = textwrap.fill(
                colorize_text(", ".join(files_ok), Fore.GREEN),
                width=shutil.get_terminal_size().columns,
                break_on_hyphens=False,
            )
            print(wrapped_files_ok)
            if errors_by_file:
                print()
        if errors_by_file:
            print(colorize_text("══════════════[ FAIL ]══════════════════", Fore.RED))
            print(
                colorize_text("File    Line    Col    Error Description", Fore.YELLOW)
            )
            errors_by_file.sort
            for file, errors in errors_by_file:
                display_errors(errors, detailed)
        if files_failed:
            print("══════════════[ FAILED ]════════════════")
            files_failed.sort(key=lambda x: x[0])
            for file, msg in files_failed:
                wrapped_failed_msg = textwrap.fill(
                    colorize_text(f"{file}: {msg}", Fore.YELLOW),
                    width=shutil.get_terminal_size().columns,
                    break_on_hyphens=False,
                )
                print("\n".join(wrapped_failed_msg.split("\n")))
    if summary_only or errors_by_file or files_failed:
        print("════════════════════════════════════════")
        unique_files_with_errors = set(file for file, _ in errors_by_file)
        print(colorize_text(f"Correct files: {len(files_ok)}", Fore.GREEN))
        print(
            colorize_text(
                f"Files with errors: {len(unique_files_with_errors)}", Fore.RED
            )
        )
        crashnum = len(files_failed)
        if crashnum != 0:
            print(colorize_text(f"Files that crashed norminette: {crashnum}", Fore.RED))
    end_time = time.time()
    execution_time = end_time - start_time
    print(colorize_text(f"Execution time: {execution_time:.2f} seconds", Fore.BLUE))


def normalize_name(name):
    return name.replace(" ", "").replace("_", "").replace("-", "").lower()


def fetch_available_names():
    response = requests.get("https://smasse.xyz/available.txt")
    if response.status_code == 200:
        names = response.text.split("\n")
        return [name.strip() for name in names if name.strip()]
    else:
        print(
            f"{Fore.RED}{Style.BRIGHT}Error: Unable to fetch the list of available test names."
        )
        return []


def download_directory(base_url, local_path="."):
    local_path = os.path.abspath(local_path)
    parent_path = os.path.abspath(os.path.join(local_path, os.pardir))

    with tempfile.TemporaryDirectory() as temp_dir:
        download_recursive(base_url, temp_dir)

        for item in os.listdir(temp_dir):
            s = os.path.join(temp_dir, item)
            d = os.path.join(parent_path, item)
            if os.path.isdir(s):
                shutil.move(s, d)
            else:
                shutil.move(s, d)


def download_recursive(base_url, local_path):
    try:
        response = requests.get(base_url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Failed to connect to {base_url}: {e}")
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
    print(f"{Fore.GREEN}{Style.BRIGHT}Downloading test for: {name}")
    download_directory(base_url, local_path)
    print(f"{Fore.GREEN}{Style.BRIGHT}Test downloaded for {name}!")


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
                f"{Fore.YELLOW}{Style.BRIGHT}Did you mean: {normalized_available[close_matches[0]]}?"
            )
            exit(0)
        else:
            print(f"{Fore.RED}{Style.BRIGHT}No match found for: {name}")
            exit(0)


def download_available():
    response = requests.get("https://smasse.xyz/available.txt")
    if response.status_code == 200:
        names = response.text.split("\n")
        print(f"{Fore.GREEN}{Style.BRIGHT}Projects with Tests Available:\n")
        for name in names:
            if name.strip():
                print(f"{Fore.CYAN} - {name.strip()}")
        print("\n")
    else:
        print(
            f"{Fore.RED}{Style.BRIGHT}Error: Unable to fetch the list of available test names."
        )


def main():
    parser = argparse.ArgumentParser(description="Run norminette but better!")
    parser.add_argument(
        "paths",
        nargs="*",
        default=["."],
        help="Space-separated directory paths or shell patterns like '*.c'. Default is current directory.",
    )
    parser.add_argument(
        "-x",
        "--exclude",
        nargs="*",
        default=[],
        help="Space-separated list of file patterns to exclude. Example usage: --exclude '*.tmp' 'test/*'",
    )
    parser.add_argument(
        "-e", "--error_only", action="store_true", help="Display only errors."
    )
    parser.add_argument(
        "-s", "--summary_only", action="store_true", help="Display only the summary."
    )
    parser.add_argument(
        "-d", "--detailed", action="store_true", help="Display detailed error messages."
    )
    parser.add_argument(
        "-l",
        "--list_files",
        action="store_true",
        help="List all found .c and .h files and exit.",
    )
    parser.add_argument(
        "-t",
        "--test",
        nargs=argparse.REMAINDER,
        help="Download tests with the given name (which might contain spaces).",
    )
    args = parser.parse_args()
    if args.test is not None:
        test_name = " ".join(args.test) if args.test else ""
        if test_name:
            downloader(test_name)
        else:
            download_available()
        return

    all_files = []
    for path in args.paths:
        all_files.extend(find_c_and_h_files(path, args.exclude))

    if args.list_files:
        for file in all_files:
            print(file)
    else:
        run_norminette(all_files, args.error_only, args.summary_only, args.detailed)


if __name__ == "__main__":
    main()
