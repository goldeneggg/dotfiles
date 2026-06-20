#!/bin/bash
set -euo pipefail

if [ $# -eq 0 ]; then
  echo "Usage: $0 <lang1> [lang2 ...]" >&2
  exit 1
fi

for lang in "$@"; do
  for oldver in $(asdf list "${lang}" | \grep -v ' \*'); do
    echo "uninstall ${lang} old version ${oldver}"
    asdf uninstall "${lang}" "${oldver}"
  done
done
