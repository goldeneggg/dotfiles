#!/bin/bash

set -euo pipefail

# stdin を先に取り込む
input="$(cat)"

THIS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# output history log
"${THIS_DIR}/history-logger.sh" "Bash permission denied" "${input}"

# output error log
"${THIS_DIR}/error-logger.sh" "Bash permission denied" "${input}"
