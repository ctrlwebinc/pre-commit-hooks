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
        default_patterns = [
            'var_dump',
            'print_r',
            'dd',
        ]
        default_comment_markers = (
            '//',
            '#',
        )
    elif file_type == "js":
        default_patterns = [
            'console.log',
        ]
        default_comment_markers = (
            '//',
        )
    else:
        default_patterns = []
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

def main():
    args = get_args()
    staged_files = args.files
    blocks = get_blocks(args)
    
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
            try:
                content = subprocess.run(
                    ["git", "show", f":{file}"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    encoding='utf-8',
                    check=True,
                ).stdout
                lines = content.splitlines()
                for i, line in enumerate(lines, start=1):
                    if has_debug_statement(line, patterns, comment_markers):
                        blocked_files.append((file, i, line.strip()))
            except subprocess.CalledProcessError:
                print(f"Warning: Could not read staged content of {file}. Skipping.")
                continue
    
    if blocked_files:
        s = 's' if len(blocked_files) > 1 else ''
        print(f"Found debug statement{s} in the following file{s}:")
        for file, line_num, line in blocked_files:
            print(f"    - '{file}:{line_num}' - {line}")
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())