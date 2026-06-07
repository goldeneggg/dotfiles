#!/bin/bash

if ! command -v jq >/dev/null 2>&1; then
  echo "enforce-builtin-tools: jq not found (brew install jq)" >&2
  exit 0
fi

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')
[ -z "$COMMAND" ] && exit 0

# 第1トークンを正規化して素のコマンド名を返す
normalize_cmd() {
  local tok="$1"
  # 引用符を除去（'grep' "grep" g"r"ep などに対応）
  tok=${tok//\"/}
  tok=${tok//\'/}
  # 先頭のバックスラッシュ（\grep）を除去
  tok=${tok#\\}
  # パス（/usr/bin/grep）を basename で落とす
  tok=$(basename "$tok" 2>/dev/null)
  printf '%s' "$tok"
}

SEGMENTS=$(printf '%s' "$COMMAND" \
  | awk '{gsub(/&&|\|\||;|\||&/, "\n"); print}')

while IFS= read -r segment; do
  [ -z "$segment" ] && continue
  cmd=$(printf '%s' "$segment" \
    | awk '{sub(/^[[:space:]]+/, ""); sub(/^[A-Za-z_][A-Za-z_0-9]*=[^ ]* /, ""); print}')

  # ラッパー語（command / builtin / exec / env）を剥がして実コマンドに辿り着く
  first=$(printf '%s' "$cmd" | awk '{print $1}')
  base=$(normalize_cmd "$first")
  while [ "$base" = "command" ] || [ "$base" = "builtin" ] || [ "$base" = "exec" ] || [ "$base" = "env" ]; do
    cmd=$(printf '%s' "$cmd" | awk '{$1=""; sub(/^[[:space:]]+/, ""); print}')
    first=$(printf '%s' "$cmd" | awk '{print $1}')
    base=$(normalize_cmd "$first")
  done

  case "$base" in
    cat)       msg="Use Read to read files, or Write to create them" ;;
    head|tail) msg="Use Read with offset/limit parameters" ;;
    sed)       msg="Use Edit for modifications, Read for line ranges" ;;
    grep|egrep|fgrep|rg) msg="Use the built-in Grep tool" ;;
    find)      msg="Use the built-in Glob tool" ;;
    *)         continue ;;
  esac

  # shellcheck disable=SC2016
  printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"Do not use `%s`. %s"}}\n' "$base" "$msg"

  exit 0
done <<EOF
$SEGMENTS
EOF
exit 0
