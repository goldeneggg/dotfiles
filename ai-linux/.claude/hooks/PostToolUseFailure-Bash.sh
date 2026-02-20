#!/bin/bash

set -euo pipefail

# output history log
THIS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
"${THIS_DIR}/history-logger.sh" "Bash failure" "$(cat)"

# output error log
"${THIS_DIR}/error-logger.sh" "Bash failure" "$(cat)"
