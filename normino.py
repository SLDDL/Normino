import subprocess
import textwrap
import argparse
import shutil
from colorama import init, Fore, Style
from concurrent.futures import ProcessPoolExecutor, as_completed
import time


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
                errors[i], width=column_width, subsequent_indent='    ')
            right = textwrap.fill(errors[i + 1] if i + 1 < len(errors)
                                  else '', width=column_width, subsequent_indent='    ')
            print(f"{left:<{column_width}}{right}")
    else:
        for error in errors:
            print(error)


def find_c_and_h_files(path, excludes):
    find_all_command = ["find", path, "-type", "f","(", "-name", "*.c", "-o", "-name", "*.h", ")"]
    try:
        result_all = subprocess.run(
            find_all_command, text=True, capture_output=True, check=True)
        all_files = result_all.stdout.strip().split('\n')
    except subprocess.CalledProcessError as e:
        print(colorize_text(
            f"Error during file search: {e.stderr.strip()}", Fore.RED))
        exit(1)
    excluded_files = set()
    for pattern in excludes:
        find_exclude_command = ["find", pattern, "-type",
                                "f", "(", "-name", "*.c", "-o", "-name", "*.h", ")"]
        try:
            result_exclude = subprocess.run(
                find_exclude_command, text=True, capture_output=True, check=True)
            excluded_files.update(result_exclude.stdout.strip().split('\n'))
        except subprocess.CalledProcessError as e:
            print(colorize_text(
                f"Error during exclusion search: {e.stderr.strip()}", Fore.RED))
    included_files = [
        file for file in all_files if file and file not in excluded_files]
    return included_files


def check_file(file, detailed):
    cmd = ["norminette", file]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=5)
        if ": OK!" in result.stdout:
            return (file, "ok", None)
        else:
            errors = [parse_output_line(line, detailed) for line in result.stdout.splitlines(
            ) if parse_output_line(line, detailed)]
            return (file, "error", errors)
    except subprocess.CalledProcessError as e:
        return (file, "fail", str(e))
    except subprocess.TimeoutExpired:
        return (file, "timeout", f"Checking timed out for {file}")
    except Exception as e:
        return (file, "crash", f"An error occurred: {str(e)}")


def parse_output_line(line, detailed=False):
    parts = line.split()
    file_path = parts[0].split(':')[0]
    if "Unexpected EOF" in line:
        return (line)
    elif "Error:" in line:
        error_description = " ".join(parts[1:])
        details = error_description.split('(')[1].split(')')[0]
        line_number, col_number = details.replace(
            'line: ', '').replace('col: ', '').split(',')
        error_name = error_description.split('(')[0].strip()
        detail_text = error_description.split(
            ')')[1].strip() if detailed else ''
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
        future_to_file = {executor.submit(
            check_file, file, detailed): file for file in files}
        for future in as_completed(future_to_file):
            file, status, error_lines = future.result()
            if status == "ok":
                files_ok.append(file)
            elif status == "error" and error_lines:
                errors_by_file.append((file, error_lines))
            elif status in ["fail", "timeout", "crash"]:
                files_failed.append((file, error_lines))
    print("\033[A                             \033[A")
    if not summary_only:
        if files_ok and not error_only:
            print(colorize_text(
                "══════════════[ PASS ]══════════════════", Fore.GREEN))
            files_ok.sort()
            wrapped_files_ok = textwrap.fill(colorize_text(
                ", ".join(files_ok), Fore.GREEN), width=shutil.get_terminal_size().columns, break_on_hyphens=False)
            print(wrapped_files_ok)
            if errors_by_file:
                print()
        if errors_by_file:
            print(colorize_text(
                "══════════════[ FAIL ]══════════════════", Fore.RED))
            print(colorize_text(
                "File    Line    Col    Error Description", Fore.YELLOW))
            errors_by_file.sort
            for file, errors in errors_by_file:
                display_errors(errors, detailed)
        if files_failed:
            print("══════════════[ FAILED ]════════════════")
            files_failed.sort(key=lambda x: x[0])
            for file, msg in files_failed:
                wrapped_failed_msg = textwrap.fill(colorize_text(
                    f"{file}: {msg}", Fore.YELLOW), width=shutil.get_terminal_size().columns, break_on_hyphens=False)
                print("\n".join(wrapped_failed_msg.split("\n")))
    if summary_only or errors_by_file or files_failed:
        print("════════════════════════════════════════")
        unique_files_with_errors = set(file for file, _ in errors_by_file)
        print(colorize_text(
            f"Correct files: {len(files_ok)}", Fore.GREEN))
        print(colorize_text(
            f"Files with errors: {len(unique_files_with_errors)}", Fore.RED))
        crashnum = len(files_failed)
        if crashnum != 0:
            print(colorize_text(
                f"Files that crashed norminette: {crashnum}", Fore.RED))
    end_time = time.time()
    execution_time = end_time - start_time
    print(colorize_text(
        f"Execution time: {execution_time:.2f} seconds", Fore.BLUE))


def main():
    parser = argparse.ArgumentParser(description="Run norminette but better!")
    parser.add_argument("paths", nargs="*", default=["."],
                        help="Space-separated directory paths or shell patterns like '*.c'. Default is current directory.")
    parser.add_argument("-x", "--exclude", nargs="*", default=[],
                    help="Space-separated list of file patterns to exclude. Example usage: --exclude '*.tmp' 'test/*'")
    parser.add_argument("-e", "--error_only", action="store_true",
                        help="Display only errors.")
    parser.add_argument("-s", "--summary_only", action="store_true",
                        help="Display only the summary.")
    parser.add_argument("-d", "--detailed", action="store_true",
                        help="Display detailed error messages.")
    parser.add_argument("-l", "--list_files", action="store_true",
                        help="List all found .c and .h files and exit.")
    args = parser.parse_args()
    all_files = []
    for path in args.paths:
        all_files.extend(find_c_and_h_files(path, args.exclude))
    if args.list_files:
        for file in all_files:
            print(file)
    else:
        run_norminette(all_files, args.error_only,
                       args.summary_only, args.detailed)


if __name__ == "__main__":
    main()
