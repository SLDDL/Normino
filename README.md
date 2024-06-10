# Normino

Normino is a command-line tool designed to enhance the `norminette` command, offering a more user-friendly and informative output for checking the coding style of your C files.

## Features

- **Colorized Output**: Enhances readability with color-coded messages.
- **Detailed Error Messages**: Displays errors with line and column numbers.
- **Summary Reporting**: Summarizes files that are correct and those with errors.
- **Flexible File Patterns**: Supports checking multiple files using patterns.
- **Extended `norminette` Support**: Allows passing additional arguments to `norminette`.
- **Project Testers**: Easily download and list available testers for projects.

## Installation

You can install Normino via pip:

``pip install normino``

Ensure `norminette` is installed and accessible in your system's PATH.

## Usage

To run Normino, use the `normino` command followed by the filenames or patterns to check:

``normino file1.c file2.c``
``normino *.c``
``normino src/*.c include/*.h``

Add additional arguments for `norminette` with the `-a` or `--args` option:

``normino -a -R CheckForbiddenSourceHeader file.c``

### Options

- `-e`, `--error_only`: Display only errors
- `-s`, `--summary_only`: Display only the summary
- `-d`, `--detailed`: Show detailed error messages
- `-a`, `--args`: Pass additional arguments to `norminette`
- `-t`, `--test [project_name]`: Show available testers or download the tester for the specified project

## Examples

Check all `.c` files in the current directory:

``normino *.c``

Check specific files and show only errors:

``normino file1.c file2.c -e``

Check files in the `src` directory and display a summary:

``normino src/*.c -s``

Check files with detailed error messages:

``normino file.c -d``

List available project testers:

``normino -t``

Download the tester for a specific project (e.g., `libft`):

``normino -t libft``

## License

Normino is licensed under the [MIT License](LICENSE).

## Contributing

We welcome contributions! If you encounter any issues or have suggestions for improvements, please open an issue or submit a pull request on our [GitHub repository](https://github.com/SLDDL/Normino).