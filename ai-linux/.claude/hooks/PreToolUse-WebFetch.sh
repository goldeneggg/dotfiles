#!/bin/bash

set -euo pipefail

# output history log
THIS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
"${THIS_DIR}/history-logger.sh" "WebFetch pre-execution" "$(cat)"
