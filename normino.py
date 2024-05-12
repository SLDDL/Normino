import subprocess
import argparse
from pathlib import Path
from colorama import init, Fore, Style
init(autoreset=True)


def colorize_text(text, color):
    return f"{color}{text}{Style.RESET_ALL}"


def parse_output_line(line, detailed=False):
    parts = line.split()
    file_path = parts[0].split(':')[0]
    if "Error:" in line:
        error_description = " ".join(parts[1:])
        details = error_description.split('(')[1].split(')')[0]
        line_number, col_number = details.replace(
            'line: ', '').replace('col: ', '').split(',')
        error_name = error_description.split('(')[0].strip()
        detail_text = error_description.split(
            ')')[1].strip() if detailed else ''
        error_info = f"\t{colorize_text(line_number, Fore.YELLOW)}\t{colorize_text(col_number, Fore.YELLOW)}     {colorize_text(error_name, Fore.RED)}"
        return error_info + f" {detail_text}" if detailed else error_info
    if ": Error!" in line:
        return f"{colorize_text(file_path, Fore.CYAN)}\t---\t---    {colorize_text('---', Fore.CYAN)}"
    return None


def display_errors(errors):
    print(colorize_text("File    Line    Col    Error Description", Fore.YELLOW))
    for error in errors:
        print(error)


def run_norminette(cmd, error_only, summary_only, detailed):
    print(colorize_text("Processing...", Fore.CYAN))
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        print("\033[A                             \033[A")
    except subprocess.CalledProcessError as e:
        print("\033[A                             \033[A")
        print(colorize_text(
            f"Failed to execute '{' '.join(cmd)}'. Make sure 'norminette' is installed and accessible.", Fore.RED))
        print(colorize_text(f"Error details: {e}", Fore.YELLOW))
        return
    files_ok, errors = [], []
    for line in result.stdout.splitlines():
        if ": OK!" in line:
            files_ok.append(line.split(":")[0])
        else:
            error_line = parse_output_line(line, detailed)
            if error_line:
                errors.append(error_line)
    if not summary_only:
        if files_ok and not error_only:
            print(colorize_text(
                "══════════════[ PASS ]══════════════════", Fore.GREEN))
            print(colorize_text(", ".join(files_ok), Fore.GREEN))
            if errors:
                print()
        if errors:
            print(colorize_text(
                "══════════════[ FAIL ]══════════════════", Fore.RED))
            display_errors(errors)
    if (summary_only or errors) and not error_only:
        if files_ok or errors:
            print()
        print(colorize_text("════════════════════════════════════════", Fore.CYAN))
        unique_files_with_errors = set(err.split('\t')[0] for err in errors)
        print(colorize_text(
            f"Correct files: {sum(1 for item in files_ok if item != '')}", Fore.GREEN))
        print(colorize_text(
            f"Files with errors: {sum(1 for item in unique_files_with_errors if item != '')}", Fore.RED))


def main():
    parser = argparse.ArgumentParser(
        description="Run norminette but better!")
    parser.add_argument("filenames", nargs="*",
                        help="Space-separated filenames or shell pattern expansions like '*.c'. Supports all shell patterns.")
    parser.add_argument("-a", "--args", nargs=argparse.REMAINDER,
                        help="Additional arguments for norminette.")
    parser.add_argument("-e", "--error_only",
                        action="store_true", help="Display only errors.")
    parser.add_argument("-s", "--summary_only",
                        action="store_true", help="Display only the summary.")
    parser.add_argument("-d", "--detailed", action="store_true",
                        help="Display detailed error messages.")
    args = parser.parse_args()
    cmd = ["norminette"]
    if args.filenames:
        cmd.extend(args.filenames)
    if args.args:
        cmd.extend(args.args)
    run_norminette(cmd, args.error_only, args.summary_only, args.detailed)


if __name__ == "__main__":
    main()
