# Pre-Commit Hooks

This repository contains custom pre-commit hooks designed to prevent accidental commits of specific file types in your Git repository. These hooks help maintain a clean and secure codebase by blocking sensitive, large, or temporary files such as environment files, database dumps, logs, and cache files.

## Hooks

The following hooks are available:

- **`block-env-files`**: Blocks environment files.
- **`block-dump-files`**: Blocks database dump files.
- **`block-log-files`**: Blocks log files.
- **`block-cache-files`**: Blocks cache files.
- **`block-debug-statements`**: Blocks cache files.
- **`block-insecure-code`**: Blocks insecure code.

Each hook can be customized with optional arguments to adjust its behavior (see [Arguments](#arguments) below).

## Installation

To use these hooks in your project, add the following to your `.pre-commit-config.yaml` file:

```yaml
- repo: https://github.com/ctrlwebinc/pre-commit-hooks
  rev: v1.2.0  # Replace with the desired tag or commit hash
  hooks:
    - id: block-env-files
    - id: block-dump-files
    - id: block-log-files
    - id: block-cache-files
    - id: block-debug-statements
    - id: block-insecure-code
```

## Hook Details

### `block-env-files`
- **Default Behavior**: Blocks files that start with `.env` (e.g., `.env`, `.env.local`, `.env.development`).

### `block-dump-files`
- **Default Behavior**: Blocks files with extensions like `.sql`, `.dump`, `.sqlite`, `.db`, and compressed variants (e.g., `.sql.gz`).

### `block-log-files`
- **Default Behavior**: Blocks files with `.log` or `.err` extensions and the exact name `error_log`.

### `block-cache-files`
- **Default Behavior**: Blocks files with the `.cache` extension.

### `block-debug-statements`
- **Default Behavior**: Blocks commits that contains debug statements for PHP and JS files.

### `block-insecure-code`
- **Default Behavior**: Blocks  risky function `eval()` for PHP and JS files.

## Arguments

Each hook supports the following optional arguments for customization:

### For 'block-*-files' hooks:
- **`--extra-extensions`**: A pipe-separated list of additional file extensions to block (e.g., `.bak|.tar|.gz`).
- **`--exclude-extensions`**: A pipe-separated list of file extensions to exclude from blocking (e.g., `.log|.txt`).
- **`--extra-names`**: A pipe-separated list of additional full file names to block (e.g., `file1.bak|file2.tar`).
- **`--exclude-names`**: A pipe-separated list of full file names to exclude from blocking (e.g., `.env.example`).
- **`--extra-prefixes`**: A pipe-separated list of additional file name prefixes to block (e.g., `env|secrets`).
- **`--exclude-prefixes`**: A pipe-separated list of file name prefixes to exclude from blocking (e.g., `test_|dev_`).

### For 'block-debug-statements' hook:
- **`--file-types`**: A pipe-separated list of file extensions to block (e.g., `php`, `js`, `php|js`).
- **`--extra-patterns`**: A pipe-separated list of additional debug patterns to block (e.g., `die|exit`).
- **`--exclude-patterns`**: A pipe-separated list of debug patterns to exclude (e.g., `console.info`).
- **`--check-mode`**: `full` for a full check on the committed file, `diff` for a check on the modified lines only. (default is `full`)

### For 'block-insecure-code' hook:
- **`--extra-patterns`**: A pipe-separated list of additional patterns to block.
- **`--exclude-patterns`**: A pipe-separated list of patterns to exclude.

## Example Usage

To customize the `block-dump-files` hook to block `.txt` and `.exe` files while excluding `.sql` files and to allow `.env.example` for the `block-env-files` hook,
and block debug statements from `php` files, add this to your `.pre-commit-config.yaml`:

```yaml
- repo: https://github.com/ctrlwebinc/pre-commit-hooks
  rev: v1.2.0
  hooks:
    - id: block-dump-files
      args: [--extra-extensions=.txt|.exe, --exclude-extensions=.sql]
    - id: block-env-files
      args: [--exclude-names=.env.example]
    - id: block-debug-statements
      args: [--file-types=php, --check-mode=diff]
```