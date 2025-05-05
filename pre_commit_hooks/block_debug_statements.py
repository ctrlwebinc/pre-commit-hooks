#!/usr/bin/env python
import argparse
import subprocess
import re
import sys
import os

def get_args():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Block debug statements in commits.")
    
    parser.add_argument(
        '--file-types',
        type=str,
        default='php|js',
        help='Pipe-separated list of file types to check (e.g., php|js)'
    )
    
    parser.add_argument(
        '--extra-patterns',
        type=str,
        default='',
        help='Pipe-separated list of additional debug patterns to block (e.g., die|exit)'
    )
    
    parser.add_argument(
        '--exclude-patterns',
        type=str,
        default='',
        help='Pipe-separated list of debug patterns to exclude (e.g., console.info)'
    )

    parser.add_argument(
        '--check-mode',
        type=str,
        default='full',
        choices=['full', 'diff'],
        help='Check mode: "full" to check entire file, "diff" to check only modified lines (default: full)'
    )
    
    # Capture the staged files passed by pre-commit
    parser.add_argument(
        'files',
        nargs='*',
        help='List of staged files to check'
    )
    
    args = parser.parse_args()
    return args

def get_defaults(file_type: str):
    if file_type == "php":
        default_patterns = (
            'var_dump',
            'print_r',
            'dd',
        )
        default_comment_markers = (
            '//',
            '#',
        )
    elif file_type == "js":
        default_patterns = (
            'console.log',
        )
        default_comment_markers = (
            '//',
        )
    else:
        default_patterns = ()
        default_comment_markers = ()
    
    defaults = {
        "patterns": default_patterns,
        "comment_markers": default_comment_markers,
    }
    return defaults

def split(str, separator='|'):
    return tuple(item.strip() for item in str.split(separator) if item.strip())

def get_extras(args):
    extras = {
        'patterns': split(args.extra_patterns),
    }
    return extras

def get_excludes(args):
    excludes = {
        'patterns': split(args.exclude_patterns),
    }
    return excludes

def get_blocks(args):
    blocks = {}
    file_types = split(args.file_types)
    extras = get_extras(args)
    excludes = get_excludes(args)
    
    for file_type in file_types:
        defaults = get_defaults(file_type)
        patterns = tuple(set(defaults['patterns'] + extras['patterns']) - set(excludes['patterns']))

        filtered_patterns = [r'{}\s*\('.format(func) for func in patterns]

        # Combine patterns
        blocks[file_type] = {
            'patterns': filtered_patterns,
            'comment_markers': defaults['comment_markers'],
        }
    
    return blocks

def has_debug_statement(line, patterns, comment_markers):
    # Find the position of the first comment marker, or end of line if none
    comment_pos = min([line.find(marker) for marker in comment_markers if marker in line] + [len(line)])
    for pattern in patterns:
        match = re.search(pattern, line)
        if match and match.start() < comment_pos:
            return True
    return False

def get_modified_lines(file):
    # Retrieve modified lines from the staged diff of the file
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--", file],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            encoding='utf-8',
            check=True,
        )
        diff_output = result.stdout
    except subprocess.CalledProcessError:
        print(f"Warning: Could not retrieve diff for {file}. Skipping.")
        return []
    
    modified_lines = []
    line_num = 0
    in_hunk = False
    for line in diff_output.splitlines():
        if line.startswith('@@'):
            # Parse hunk header, e.g., @@ -10,5 +12,7 @@
            hunk_info = line.split()[2]  # +12,7
            line_num = int(hunk_info.split(',')[0][1:]) - 1  # Start at line 12
            in_hunk = True
        elif in_hunk:
            if line.startswith('+'):
                modified_lines.append((line_num, line[1:].strip()))  # Added line
                line_num += 1
            elif not line.startswith('-'):
                line_num += 1  # Unchanged line
    return modified_lines

def get_all_lines(file):
    file_lines = []
    try:
        content = subprocess.run(
            ["git", "show", f":{file}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            encoding='utf-8',
            check=True,
        )
        lines = content.stdout
    except subprocess.CalledProcessError:
        print(f"Warning: Could not retrieve file {file}. Skipping.")
        return []
    
    line_num = 1
    for line in lines.splitlines():
        file_lines.append((line_num, line.strip()))
        line_num += 1
    return file_lines

def main():
    args = get_args()
    staged_files = args.files
    blocks = get_blocks(args)
    check_mode = args.check_mode

    # Map file types to their extensions
    file_extensions = {
        'php': ('.php', '.blade.php'),
        'js': ('.js', '.jsx', '.ts'),
    }
    
    # Determine which extensions to check based on file_types
    extensions_to_check = []
    for file_type in split(args.file_types):
        if file_type in file_extensions:
            extensions_to_check.extend(file_extensions[file_type])
    
    blocked_files = []
    for file in staged_files:
        ext = os.path.splitext(file)[1].lower()
        if ext in extensions_to_check:
            file_type = next(ft for ft, exts in file_extensions.items() if ext in exts)
            patterns = blocks[file_type]['patterns']
            comment_markers = blocks[file_type]['comment_markers']
            
            lines = []
            if check_mode == 'full': # Check the entire file
                lines = get_all_lines(file)
            elif check_mode == 'diff': # Check only modified lines
                lines = get_modified_lines(file)

            for line_num, line in lines:
                if has_debug_statement(line, patterns, comment_markers):
                    blocked_files.append((file, line_num, line))
    
    if blocked_files:
        s = 's' if len(blocked_files) > 1 else ''
        print(f"Found debug statement{s} in the following file{s}:")
        for file, line_num, line in blocked_files:
            print(f"    - '{file}:{line_num}' - {line}")
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())