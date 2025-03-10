#!/usr/bin/env python
import argparse

def get_args():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Block environment, database, dump, log and cache files in commits.")

    parser.add_argument(
        '--type', 
        type=str, 
        required=True, 
        choices=['env', 'dump', 'log', 'cache'],
        help='Which type of files to check ( env|dump|log|cache )'
    )

    # Capture the staged files passed by pre-commit
    parser.add_argument(
        'files',
        nargs='*',
        help='List of staged files to check'
    )

    #### Extensions
    parser.add_argument(
        '--extra-extensions',
        type=str,
        default='',
        help='Pipe-separated list of additional file extensions to block (e.g., .bak|.tar|.gz)'
    )

    parser.add_argument(
        '--exclude-extensions',
        type=str,
        default='',
        help='Pipe-separated list of file extensions to exclude (e.g., .log|.txt)'
    )

    #### Names
    parser.add_argument(
        '--extra-names',
        type=str,
        default='',
        help='Pipe-separated list of additional file names to block (e.g., file1.bak|file2.tar|file3.gz)'
    )

    parser.add_argument(
        '--exclude-names',
        type=str,
        default='',
        help='Pipe-separated list of file names to exclude (e.g., filename.txt)'
    )

    #### Prefixes
    parser.add_argument(
        '--extra-prefixes',
        type=str,
        default='',
        help='Pipe-separated list of additional file name prefixes to block (e.g., env|env.)'
    )

    parser.add_argument(
        '--exclude-prefixes',
        type=str,
        default='',
        help='Pipe-separated list of file name prefixes to exclude (e.g., pre|prefix)'
    )

    args = parser.parse_args()
    return args

def get_defaults(type: str):
    if type == "dump":
        default_extensions = (
            '.sql',
            '.dump',
            '.sqlite',
            '.db',
            '.sql.gz',
            '.sql.zip',
            '.dump.gz',
            '.dump.zip',
            '.sql.tar.gz',
            '.dump.tar.gz',
        )
        default_names = ()
        default_prefixes = ()
    elif type == "log":
        default_extensions = (
            '.log',
            '.err',
        )
        default_names = (
            'error_log',
        )
        default_prefixes = ()
    elif type == "env":
        default_extensions = ()
        default_names = ()
        default_prefixes = (
            '.env',
            'env.',
        )
    elif type == "cache":
        default_extensions = (
            '.cache',
        )
        default_names = ()
        default_prefixes = ()
    else:
        default_extensions = ()
        default_names = ()
        default_prefixes = ()

    defaults = {
        "extensions" : default_extensions,
        "names" : default_names,
        "prefixes" : default_prefixes,
    }
    return defaults

def split(str, separator='|'):
    return tuple(item.strip() for item in str.split(separator) if item.strip())

def get_extras(args):
    extras = {
        'extensions': split(args.extra_extensions),
        'names' : split(args.extra_names),
        'prefixes' : split(args.extra_prefixes)
    }
    return extras

def get_excludes(args):
    excludes = {
        'extensions' : split(args.exclude_extensions),
        'names' : split(args.exclude_names),
        'prefixes' : split(args.exclude_prefixes),
    }
    return excludes

def get_blocks(args):
    blocks = {}
    defaults = get_defaults(args.type)
    extras = get_extras(args)
    excludes = get_excludes(args)

    for item in ('extensions', 'names', 'prefixes'):
        blocks[item] = tuple(set(defaults[item] + extras[item]) - set(excludes[item]))

    return blocks

def main():
    args = get_args()
    staged_files = args.files
    type = args.type
    types = {
        'env': 'environment variable',
        'dump': 'database dump',
        'log': 'log',
        'cache': 'cache'
    }
    blocks = get_blocks(args)

    blocked_files = []
    for file in staged_files:
        filename = file.lower()
        if filename not in get_excludes(args)['names']:
            if filename.endswith(blocks['extensions']) or file in blocks['names'] or filename.startswith(blocks['prefixes']):
                blocked_files.append(file)

    if blocked_files:
        s = 's' if len(blocked_files) > 1 else ''
        a = 'an' if type == 'env' else 'a'
        x = '' if s == 's' else a + " "
        print(f"Found {x}{types[type]} file{s} in commit : ")

        for file in blocked_files:
            print(f"    - '{file}'")
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())