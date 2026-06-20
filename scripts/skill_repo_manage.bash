#!/bin/bash
set -euo pipefail

ACTION="${1:?Usage: $0 <add-all|update-all> <dest_dir> <repo|dir|name> [...]}"
DEST_DIR="${2:?Usage: $0 <add-all|update-all> <dest_dir> <repo|dir|name> [...]}"
shift 2

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

for entry in "$@"; do
  IFS='|' read -r REPO REPO_DIR SKILL_NAME <<< "${entry}"

  case "${ACTION}" in
    add-all)
      if [ -d "${DEST_DIR}/${SKILL_NAME}" ]; then
        echo "SKIP: ${SKILL_NAME} already exists"
      else
        echo "ADD: ${SKILL_NAME} from ${REPO}..."
        "${SCRIPT_DIR}/skill_sparse_checkout.bash" "${REPO}" "${REPO_DIR}" "${SKILL_NAME}" "${DEST_DIR}"
      fi
      ;;
    update-all)
      echo "UPDATE: ${SKILL_NAME} from ${REPO}..."
      rm -rf "${DEST_DIR:?}/${SKILL_NAME}"
      "${SCRIPT_DIR}/skill_sparse_checkout.bash" "${REPO}" "${REPO_DIR}" "${SKILL_NAME}" "${DEST_DIR}"
      ;;
    *)
      echo "Error: unknown action '${ACTION}' (expected: add-all|update-all)" >&2
      exit 1
      ;;
  esac
done
