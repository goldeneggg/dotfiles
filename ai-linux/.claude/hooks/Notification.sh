#!/bin/bash
# Notification Hook
# Claude Code が確認を待っているときに履歴ログを記録し通知を表示

set -euo pipefail

# stdin を先に取り込む
input="$(cat)"

# output history log
THIS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
"${THIS_DIR}/history-logger.sh" "Notification" "${input}"

# terminal-notifier の存在チェック
if ! command -v terminal-notifier >/dev/null 2>&1; then
  exit 0
fi

pjt='unknown'
if [[ -n "${PWD}" ]]
then
  pjt="$(basename "${PWD}")"
fi

terminal-notifier \
  -title 'Claude Code' \
  -subtitle "ℹ️ Notification: ${pjt}" \
  -message '通知やで'
