#!/bin/bash
# Notification Hook
# Claude Code が確認を待っているときに通知を表示

set -euo pipefail

# terminal-notifier の存在チェック
if ! command -v terminal-notifier >/dev/null 2>&1; then
    exit 0
fi

terminal-notifier \
    -title 'Claude Code' \
    -subtitle 'Notification' \
    -message 'Claude Codeが何かの確認を待っとるで'
