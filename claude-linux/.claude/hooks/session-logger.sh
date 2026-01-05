#!/bin/bash
# Session Logger Hook
# Claude Code セッションの開始をログに記録

set -euo pipefail

LOG_FILE="${HOME}/.claude/logs/session.log"
LOG_DIR="$(dirname "${LOG_FILE}")"

# ログディレクトリが存在しない場合は作成
if [[ ! -d "${LOG_DIR}" ]]; then
    mkdir -p "${LOG_DIR}"
fi

# タイムスタンプ付きでログを記録
timestamp=$(date '+%Y-%m-%d %H:%M:%S')
cwd="${PWD:-unknown}"

echo "[${timestamp}] Session started in ${cwd}" >> "${LOG_FILE}"
