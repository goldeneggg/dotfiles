#!/bin/bash

set -euo pipefail

# stdin を先に取り込む（後段で複数回参照するため）
input="$(cat)"

THIS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# output history log
# "${THIS_DIR}/history-logger.sh" "WebFetch failure" "${input}"

# output error log
"${THIS_DIR}/error-logger.sh" "WebFetch failure" "${input}"
