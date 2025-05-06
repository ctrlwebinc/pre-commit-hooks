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
        '--extra-functions',
        type=str,
        default='',
        help='Pipe-separated list of additional functions to block'
    )
    
    parser.add_argument(
        '--exclude-functions',
        type=str,
        default='',
        help='Pipe-separated list of functions to exclude'
    )
    
    # Capture the staged files passed by pre-commit
    parser.add_argument(
        'files',
        nargs='*',
        help='List of staged files to check'
    )
    
    args = parser.parse_args()
    return args

def get_defaults():
    default_functions = (
        'eval'
    )
    default_comment_markers = (
        '//',
        '#',
    )

    defaults = {
        "functions": default_functions,
        "comment_markers": default_comment_markers,
    }
    return defaults

def split(str, separator='|'):
    return tuple(item.strip() for item in str.split(separator) if item.strip())

def get_extras(args):
    extras = {
        'functions': split(args.extra_functions),
    }
    return extras

def get_excludes(args):
    excludes = {
        'functions': split(args.exclude_functions),
    }
    return excludes

def get_blocks(args):
    blocks = {}
    extras = get_extras(args)
    excludes = get_excludes(args)
    
    defaults = get_defaults()
    functions = tuple(set(defaults['functions'] + extras['functions']) - set(excludes['functions']))

    filtered_functions = [r'{}\s*\('.format(func) for func in functions]

    blocks = {
        'functions': filtered_functions,
        'comment_markers': defaults['comment_markers'],
    }
    
    return blocks

def has_insecure_functions(line, functions, comment_markers):
    # Find the position of the first comment marker, or end of line if none
    comment_pos = min([line.find(marker) for marker in comment_markers if marker in line] + [len(line)])
    for functions in functions:
        match = re.search(functions, line)
        if match and match.start() < comment_pos:
            return True
    return False

def get_lines(file):
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
    
    blocked_files = []
    for file in staged_files:
        functions = blocks['functions']
        comment_markers = blocks['comment_markers']
            
        lines = get_lines(file)

        for line_num, line in lines:
            if has_insecure_functions(line, functions, comment_markers):
                blocked_files.append((file, line_num, line))
    
    if blocked_files:
        s = 's' if len(blocked_files) > 1 else ''
        print(f"Found insecure function{s} in the following file{s}:")
        for file, line_num, line in blocked_files:
            print(f"    - '{file}:{line_num}' - {line}")
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())