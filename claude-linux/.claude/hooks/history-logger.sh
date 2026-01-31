#!/bin/bash

set -euo pipefail

THIS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
"${THIS_DIR}/logger.sh" "history.jsonl" "$@"
