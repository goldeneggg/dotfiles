#!/bin/bash
# Bash Command Logger Hook
# 実行されたBashコマンドをログに記録

set -euo pipefail

LOG_FILE="${HOME}/.claude/logs/bash-commands.log"
LOG_DIR="$(dirname "${LOG_FILE}")"

# ログディレクトリが存在しない場合は作成
if [[ ! -d "${LOG_DIR}" ]]; then
    mkdir -p "${LOG_DIR}"
fi

# 標準入力からJSONを読み取り、コマンドと説明を抽出
# jq がインストールされている前提
if command -v jq &> /dev/null; then
    input=$(cat)
    command_str=$(echo "${input}" | jq -r '.tool_input.command // "unknown"')
    description=$(echo "${input}" | jq -r '.tool_input.description // "No description"')

    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[${timestamp}] ${command_str} - ${description}" >> "${LOG_FILE}"
fi
