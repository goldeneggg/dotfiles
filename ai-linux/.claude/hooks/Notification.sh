#!/bin/bash
# Notification Hook
# Claude Code が確認を待っているときに通知を表示

set -euo pipefail

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
