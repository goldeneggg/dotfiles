#!/bin/bash

BASE_DIR="${1:?Usage: $0 <base_dir> <command> <repo1> [repo2 ...]}"
COMMAND="${2:?Usage: $0 <base_dir> <command> <repo1> [repo2 ...]}"
shift 2

if [ $# -eq 0 ]; then
  echo "Error: at least one repo name required" >&2
  exit 1
fi

for repo in "$@"; do
  (cd "${BASE_DIR}/watch-${repo}" && echo "---------- ${repo}" && eval "${COMMAND}") || { echo "NG!"; true; }
done
