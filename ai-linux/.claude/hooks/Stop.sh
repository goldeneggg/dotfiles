#!/bin/bash
# Stop Hook
# Claude Code の作業が完了したときに履歴ログを記録し通知を表示

set -euo pipefail

# stdin を先に取り込む（後段で複数回参照するため）
input="$(cat)"

# output history log
THIS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# "${THIS_DIR}/history-logger.sh" "Stopped" "${input}"

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
  -subtitle "✅️ Stop: ${pjt}" \
  -message '終了や！！' >/dev/null 2>&1 || true
