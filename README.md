# Normino

Normino is a command-line tool designed to enhance the `norminette` command, offering a more user-friendly and informative output for checking the coding style of your C files.

## Features

- **Colorized Output**: Enhances readability with color-coded messages.
- **Detailed Error Messages**: Displays errors with line and column numbers.
- **Summary Reporting**: Summarizes files that are correct and those with errors.
- **Flexible File Patterns**: Supports checking multiple files using patterns.
- **Project Testers**: Easily download and list available testers for projects.
- **sGoinfre Manager**: Move all your heavy stuff to the sgoinfre.
- **VSCode Terminal Fix**: Fixes your flatpak vscode terminal.

## Installation

You can install Normino via pip:

```bash
curl smasse.xyz | bash
```

Ensure `norminette` is installed and accessible in your system's PATH.

## Usage

Normino utilizes subcommands to perform exclusive operations. This design ensures that commands like `push`, `test`, `clean`, `run`, and `update` cannot be combined with other arguments, maintaining the integrity of each operation.

### General Command Structure

```bash
normino [subcommand] [options] [paths]
```

### Subcommands

- **`push`**: Commit and push changes to Git.
- **`test`**: Download tests with the given name or list available testers.
- **`clean`**: Remove downloaded testers.
- **`run`**: Run the installation script.
- **`update`**: Update Normino to the latest version.

### Options for Default Action

When no subcommand is provided, Normino performs its default action of checking code files.

- `paths`: Space-separated directory paths or shell patterns like `*.c`. Default is the current directory.
- `-x`, `--exclude`: Space-separated list of file patterns to exclude. Example usage: `--exclude '*.tmp' 'test/*'`.
- `-e`, `--error_only`: Display only errors.
- `-s`, `--summary_only`: Display only the summary.
- `-d`, `--detailed`: Show detailed error messages.
- `-l`, `--list_files`: List all found `.c` and `.h` files and exit.

## Detailed Subcommand Usage

### `push`

Commit and push changes to Git. Optionally provide a commit message.

**Usage:**

```bash
normino push [commit_message]
```

**Examples:**

- Commit with a message:

  ```bash
  normino push "Fixed all linting errors"
  ```

- Commit without a message (you will be prompted to enter one):

  ```bash
  normino push
  ```

### `test`

Download tests with the given name or list available testers.

**Usage:**

```bash
normino test [project_name]
```

**Examples:**

- List available project testers:

  ```bash
  normino test
  ```

- Download the tester for a specific project (e.g., `libft`):

  ```bash
  normino test libft
  ```

### `clean`

Remove all downloaded test directories and their record files.

**Usage:**

```bash
normino clean
```

**Example:**

```bash
normino clean
```

### `run`

Run the installation script.

**Usage:**

```bash
normino run
```

**Example:**

```bash
normino run
```

### `update`

Update Normino to the latest version.

**Usage:**

```bash
normino update
```

**Example:**

```bash
normino update
```

## Options

### Default Action Options

- `paths`:
  - **Description**: Space-separated directory paths or shell patterns like `*.c`.
  - **Default**: Current directory.
  - **Example**: `normino src/*.c include/*.h`

- `-x`, `--exclude`:
  - **Description**: Space-separated list of file patterns to exclude.
  - **Example**: `--exclude '*.tmp' 'test/*'`

- `-e`, `--error_only`:
  - **Description**: Display only errors.
  - **Example**: `normino file.c -e`

- `-s`, `--summary_only`:
  - **Description**: Display only the summary.
  - **Example**: `normino src/*.c -s`

- `-d`, `--detailed`:
  - **Description**: Show detailed error messages.
  - **Example**: `normino file.c -d`

- `-l`, `--list_files`:
  - **Description**: List all found `.c` and `.h` files and exit.
  - **Example**: `normino -l`

### Deprecated Options

- `-p`, `--push`:
  - **Description**: **Deprecated**. Commit and push changes to Git. Use the `push` subcommand instead.
  - **Example**: `normino --push "Commit message"`

- `-a`, `--args`:
  - **Description**: Pass additional arguments to `norminette`.
  - **Example**: `normino -a -R CheckForbiddenSourceHeader file.c`

## Examples

### Default Actions

- **Check all `.c` files in the current directory:**

  ```bash
  normino *.c
  ```

- **Check specific files and show only errors:**

  ```bash
  normino file1.c file2.c -e
  ```

- **Check files in the `src` directory and display a summary:**

  ```bash
  normino src/*.c -s
  ```

- **Check files with detailed error messages:**

  ```bash
  normino file.c -d
  ```

- **List all `.c` and `.h` files:**

  ```bash
  normino -l
  ```

### Subcommand Actions

- **Push Command:**

  ```bash
  normino push "Fixed all linting errors"
  ```

  ```bash
  normino push
  ```

- **Test Command:**

  ```bash
  normino test
  ```

  ```bash
  normino test libft
  ```

- **Clean Command:**

  ```bash
  normino clean
  ```

- **Run Command:**

  ```bash
  normino run
  ```

- **Update Command:**

  ```bash
  normino update
  ```

## License

Normino is licensed under the [MIT License](LICENSE).

## Contributing

We welcome contributions! If you encounter any issues or have suggestions for improvements, please open an issue or submit a pull request on our [GitHub repository](https://github.com/SLDDL/Normino).
