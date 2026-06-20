#!/bin/bash
set -euo pipefail

if [ $# -eq 0 ]; then
  echo "Usage: $0 <lang1> [lang2 ...]" >&2
  exit 1
fi

for lang in "$@"; do
  asdf list "${lang}" | fzf -m | awk '{print $1}' | xargs -I {} sh -c "echo \"uninstall ${lang} {}...\" && asdf uninstall ${lang} {}"
done
