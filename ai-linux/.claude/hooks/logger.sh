#!/bin/bash

set -euo pipefail

# 指定されたフィールドを先頭N文字にカットする関数
truncate_field() {
  local json="$1"
  local field_path="$2"
  local max_length="${3:-20}"

  # フィールドが存在しない場合はスキップ
  if ! echo "${json}" | jq -e "${field_path}" > /dev/null 2>&1; then
    echo "${json}"
    return 0
  fi

  # 値を取得してカット
  local field_value
  field_value=$(echo "${json}" | jq -r "${field_path}")
  local truncated
  truncated=$(echo "${field_value}" | head -c "${max_length}")

  echo "${json}" | jq --arg snippet "${truncated}" "${field_path} = \$snippet + \"...\""
}

timestamp=$(date '+%Y-%m-%d %H:%M:%S')

log_dir="${HOME}/.claude/logs"
if [[ ! -d "${log_dir}" ]]; then
  mkdir -p "${log_dir}"
fi

log_file="${log_dir}/${1}"
msg="${2}"
input_json="${3}"

# カット対象のフィールドパス一覧
readonly TRUNCATE_FIELDS=(
  ".prompt"
  ".content"
  ".message"
  ".tool_response.stdout"
)

# 各フィールドに対してカット処理を適用
for field in "${TRUNCATE_FIELDS[@]}"; do
  input_json=$(truncate_field "${input_json}" "${field}" 20)
done

# input_jsonが改行やインデント含みの場合、削除して1行のJSONにする
input_json=$(echo "${input_json}" | jq -c '.')

echo "{\"timestamp\":\"${timestamp}\",\"msg\":\"${msg}\",\"input\":${input_json}}" >> "${log_file}"
