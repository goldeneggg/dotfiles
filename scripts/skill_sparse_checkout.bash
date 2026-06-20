#!/bin/bash
set -euo pipefail

REPO="${1:?Usage: $0 <repo> <repo_dir> <skill_name> <dest_dir>}"
REPO_DIR="${2:?Usage: $0 <repo> <repo_dir> <skill_name> <dest_dir>}"
SKILL_NAME="${3:?Usage: $0 <repo> <repo_dir> <skill_name> <dest_dir>}"
DEST_DIR="${4:?Usage: $0 <repo> <repo_dir> <skill_name> <dest_dir>}"

TEMP_DIR=$(mktemp -d)
trap 'rm -rf "${TEMP_DIR}"' EXIT
git clone --depth 1 --filter=blob:none --sparse "https://github.com/${REPO}.git" "${TEMP_DIR}"
(cd "${TEMP_DIR}" && git sparse-checkout set "${REPO_DIR}/${SKILL_NAME}")
mkdir -p "${DEST_DIR}"
cp -r "${TEMP_DIR}/${REPO_DIR}/${SKILL_NAME}" "${DEST_DIR}/"
