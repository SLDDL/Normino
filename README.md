# Normino

Normino is a command-line tool that enhances the functionality of the `norminette` command, providing a more user-friendly and informative output for checking the coding style of your C files.

## Features

- Colorized output for better readability
- Detailed error messages with line and column numbers
- Summary of correct files and files with errors
- Support for file patterns and additional `norminette` arguments

## Installation

You can install Normino using pip:

``​`
pip install normino
``​`

Make sure you have `norminette` installed and accessible in your system's PATH.

## Usage

To run Normino, simply use the `normino` command followed by the filenames or file patterns you want to check:

``​`
normino file1.c file2.c
normino *.c
normino src/*.c include/*.h
``​`

You can also provide additional arguments for `norminette` using the `-a` or `--args` option:

``​`
normino -a -R CheckForbiddenSourceHeader file.c
``​`

### Options

- `-e`, `--error_only`: Display only errors
- `-s`, `--summary_only`: Display only the summary
- `-d`, `--detailed`: Display detailed error messages
- `-a`, `--args`: Additional arguments for `norminette`

## Examples

Check all `.c` files in the current directory:

``​`
normino *.c
``​`

Check specific files and display only errors:

``​`
normino file1.c file2.c -e
``​`

Check files in the `src` directory and display a summary:

``​`
normino src/*.c -s
``​`

Check files with detailed error messages:

``​`
normino file.c -d
``​`

## License

This project is licensed under the [MIT License](LICENSE).

## Contributing

Contributions are welcome! If you find any issues or have suggestions for improvements, please open an issue or submit a pull request.