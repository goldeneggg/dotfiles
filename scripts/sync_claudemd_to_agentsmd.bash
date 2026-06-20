#!/bin/bash
set -euo pipefail

SEARCH_DIR="${1:-.}"

find "${SEARCH_DIR}" -name "CLAUDE.md" -not -path "*/.git/*" -not -path "*/node_modules/*" | while read -r f; do
  dir=$(dirname "${f}")
  ln -sf CLAUDE.md "${dir}/AGENTS.md"
  echo "Created: ${dir}/AGENTS.md -> CLAUDE.md"
done
