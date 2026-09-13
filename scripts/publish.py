#!/usr/bin/env python3
"""Build/test locally; --push explicitly stages safe paths, commits, and pushes.

A Git push only triggers deployment if the remote is connected to a hosting
provider. This script does not configure Netlify or claim the site is live.
Start with an empty Git index; unrelated staged work is never committed.
"""
import argparse
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SAFE_FILES = {
    '.gitignore', 'README.md', 'EDITORIAL.md', 'requirements.txt', 'netlify.toml',
    'scripts/build_site.py', 'scripts/check_deploy.py', 'scripts/publish.py',
    'scripts/publish.sh', 'tests/test_build_site.py', 'tests/test_operations.py',
    'tests/test_security.py', 'site/index.html', 'site/robots.txt', 'site/sitemap.xml',
}


def safe_path(path):
    """Allow specific source files and flat article paths, never whole trees."""
    if any(part.startswith('.') or part.lower().split('.')[0] in {'env', 'logs', 'metrics'}
           for part in path.split('/')):
        return path == '.gitignore'
    allowed = path in SAFE_FILES or bool(re.fullmatch(r'(?:content/[a-zA-Z0-9_-]+\.md|site/posts/[a-zA-Z0-9_-]+\.html)', path))
    target = ROOT / path
    return allowed and not target.is_symlink() and all(not parent.is_symlink() for parent in target.parents if parent != ROOT.parent)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--push', action='store_true', help='Explicitly stage, commit and push validated files')
    args = parser.parse_args(argv)

    def run(command, check=True):
        return subprocess.run(command, cwd=ROOT, check=check, capture_output=True, text=True, timeout=300)

    try:
        for command in ([sys.executable, 'scripts/build_site.py'],
                        [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v']):
            run(command)
        if not args.push:
            print('Local validation passed. No Git state changed; nothing published.')
            return 0
        if run(['git', 'diff', '--cached', '--name-only', '-z']).stdout:
            print('Publish refused: index already contains staged changes. Commit or unstage them explicitly first.')
            return 1
        candidates = run(['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z']).stdout.split('\0')
        paths = sorted({path for path in candidates if path and safe_path(path)})
        if paths:
            run(['git', 'add', '--', *paths])
        diff = run(['git', 'diff', '--cached', '--quiet'], check=False)
        if diff.returncode == 1:
            run(['git', 'commit', '-m', 'Publish validated Verdant site'])
        elif diff.returncode != 0:
            print('Publish failed: unable to inspect staged changes.')
            return 1
        run(['git', 'push'])
        print('Git push completed. Hosting deployment is separate; verify with check_deploy.py --url URL.')
        return 0
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
        # Commands/remote URLs may contain credentials: do not echo exceptions.
        print('Validation or publish command failed. Nothing further was run; inspect the local build/tests or Git status.')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
