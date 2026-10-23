#!/usr/bin/env python3
"""Check local repository path spellings for common Windows portability issues."""
import argparse
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile

MAX_BYTES = 16 * 1024 * 1024
MAX_PATHS = 100_000
SKIP = {'.git', 'node_modules', '.venv', 'venv', '__pycache__', 'dist', 'build', '.next', '.tox'}
RESERVED = {'con','prn','aux','nul','conin$','conout$'} | {f'{p}{n}' for p in ('com','lpt') for n in '123456789\u00b9\u00b2\u00b3'}

class Invalid(ValueError):
    pass

class Parser(argparse.ArgumentParser):
    def error(self, message):
        self.exit(2, 'error: invalid arguments; use --help\n')

def pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise Invalid('duplicate JSON key')
        result[key] = value
    return result

def link(path):
    info = path.lstat()
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, 'st_file_attributes', 0) & 0x400)

def collect(root, directory=False, paths_file=None):
    if not root.is_dir() or link(root):
        raise Invalid('root must be an unlinked directory')
    if paths_file is not None:
        if paths_file.stat().st_size > MAX_BYTES:
            raise Invalid('paths file exceeds 16 MiB')
        with paths_file.open('rb') as stream:
            raw = stream.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise Invalid('paths file exceeds 16 MiB')
        paths = json.loads(raw.decode('utf-8'), object_pairs_hook=pairs,
                           parse_constant=lambda _: (_ for _ in ()).throw(Invalid('nonfinite JSON')))
        if not isinstance(paths, list):
            raise Invalid('paths file must contain an array')
        return paths
    if directory:
        paths = []
        def failed(_):
            raise Invalid('directory traversal failed')
        for current, dirs, files in os.walk(root, followlinks=False, onerror=failed):
            parent = Path(current)
            dirs[:] = sorted(d for d in dirs if d not in SKIP and not link(parent / d))
            for name in sorted(files):
                path = parent / name
                if not link(path):
                    paths.append(path.relative_to(root).as_posix())
                    if len(paths) > MAX_PATHS:
                        raise Invalid('too many paths')
        return paths
    # Spool stdout to avoid unbounded subprocess memory. Git stderr is never echoed.
    with tempfile.TemporaryFile() as output, tempfile.TemporaryFile() as errors:
        result = subprocess.run(['git','-C',str(root),'ls-files','-z'], stdout=output, stderr=errors, timeout=30)
        if result.returncode:
            raise Invalid('Git could not list tracked paths')
        output.seek(0)
        raw = output.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise Invalid('Git path output exceeds 16 MiB')
    if raw and not raw.endswith(b'\0'):
        raise Invalid('invalid Git path framing')
    return raw[:-1].decode('utf-8', errors='surrogateescape').split('\0') if raw else []

def analyze(paths, max_path=None):
    if len(paths) > MAX_PATHS:
        raise Invalid('too many paths')
    findings = []
    emitted = set()
    spellings = {}
    roles = {}
    seen = set()
    for path in paths:
        if not isinstance(path, str) or not path or len(path) > 32_768 or path.startswith(('/', '\\')) or re.match(r'^[a-zA-Z]:', path):
            raise Invalid('invalid relative path')
        parts = path.split('/')
        if any(p in ('','.', '..') for p in parts) or path in seen:
            raise Invalid('invalid or duplicate relative path')
        seen.add(path)
        if max_path is not None and len(path) > max_path:
            findings.append(dict(path=path, code='relative_length_advisory', length=len(path)))
        for index, part in enumerate(parts):
            prefix = '/'.join(parts[:index + 1])
            folded = prefix.casefold()
            spellings.setdefault(folded, set()).add(prefix)
            roles.setdefault(folded, set()).add('file' if index == len(parts) - 1 else 'directory')
            codes = []
            if any(ord(c) < 32 or c in '<>:"\\|?*' or 0xD800 <= ord(c) <= 0xDFFF for c in part):
                codes.append('invalid_character')
            if part.endswith(('.', ' ')):
                codes.append('trailing_dot_or_space')
            if part.rstrip(' .').split('.')[0].casefold() in RESERVED:
                codes.append('reserved_device')
            for code in codes:
                finding = dict(path=prefix, code=code)
                key = (prefix, code)
                if key not in emitted:
                    emitted.add(key)
                    findings.append(finding)
    for folded in sorted(spellings):
        variants = sorted(spellings[folded])
        if len(variants) > 1:
            findings.append(dict(code='case_collision', paths=variants))
        if len(roles[folded]) > 1:
            findings.append(dict(code='file_directory_collision', paths=variants))
    return dict(status='findings' if findings else 'clean', checked_paths=len(paths), findings=findings)

def main(argv=None):
    parser = Parser(description=__doc__)
    parser.add_argument('root', nargs='?', type=Path, default=Path('.'))
    source = parser.add_mutually_exclusive_group()
    source.add_argument('--directory', action='store_true', help='include untracked tree files; skip generated dependencies and links')
    source.add_argument('--paths-file', type=Path, help='JSON array of synthetic relative path spellings')
    parser.add_argument('--max-path', type=int, help='relative character-count advisory threshold')
    parser.add_argument('--format', choices=('json','text'), default='text')
    args = parser.parse_args(argv)
    try:
        if args.max_path is not None and not 1 <= args.max_path <= 32_768:
            raise Invalid('invalid max-path threshold')
        result = analyze(collect(args.root, args.directory, args.paths_file), args.max_path)
        result['source'] = 'paths-file' if args.paths_file else 'directory' if args.directory else 'git-index'
        print(json.dumps(result, ensure_ascii=True) if args.format == 'json' else result['status'] + ': ' + json.dumps(result, ensure_ascii=True))
        return int(result['status'] == 'findings')
    except (OSError, ValueError, TypeError, RecursionError, subprocess.SubprocessError):
        print('error: invalid paths, input bounds, directory access, or Git failure', file=sys.stderr)
        return 2

if __name__ == '__main__':
    sys.exit(main())
