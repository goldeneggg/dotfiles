#!/bin/bash

set -euo pipefail

# output history log
THIS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
"${THIS_DIR}/history-logger.sh" "WebSearch failure" "$(cat)"

# output error log
"${THIS_DIR}/error-logger.sh" "WebSearch failure" "$(cat)"
