#!/bin/bash
# Stop Notification Hook
# Claude Code の作業が完了したときに通知を表示

set -euo pipefail

# terminal-notifier の存在チェック
if ! command -v terminal-notifier >/dev/null 2>&1; then
    exit 0
fi

terminal-notifier \
    -title 'Claude Code' \
    -subtitle 'Stop' \
    -message 'Claude Codeの作業が完了したっぽいで'
