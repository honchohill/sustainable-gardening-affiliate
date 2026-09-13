#!/usr/bin/env bash
set -euo pipefail
# Relative path works on POSIX and Git Bash without a hard-coded checkout.
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
if [[ -n "${PYTHON:-}" ]]; then
    exec "$PYTHON" publish.py "$@"
elif command -v python >/dev/null 2>&1; then
    exec python publish.py "$@"
else
    exec python3 publish.py "$@"
fi
