#!/bin/bash
#
# clipboard_copy.sh - 入力（ファイル or 標準入力）を整形してクリップボードへコピーする
#
# 整形仕様:
#   1. 行末空白を全て削除
#   2. 共通先頭空白を削除（dedent）
#      - 空行以外の各行の先頭空白数を調べ、その最小値を全行から一律に削除
#
# クリップボードコマンドの選択:
#   - macOS(Darwin): pbcopy
#   - Linux:         xsel --clipboard --input
#   - OS判定不可:     pbcopy（フォールバック）
#
# 使い方:
#   clipboard_copy.sh <FILE>     # ファイル内容をコピー
#   ... | clipboard_copy.sh      # 標準入力の内容をコピー

set -euo pipefail

# クリップボードコマンドを決定する。
# uname が利用できない等で判定不能な場合は pbcopy にフォールバックする。
detect_clipboard_cmd() {
  local os
  if ! os="$(\uname -s 2>/dev/null)"; then
    \printf '%s' "pbcopy"
    return
  fi

  case "${os}" in
    Darwin) \printf '%s' "pbcopy" ;;
    Linux)  \printf '%s' "xsel --clipboard --input" ;;
    *)      \printf '%s' "pbcopy" ;;  # 未知のOS（判定不可）は pbcopy
  esac
}

# 入力を取得する。
# 引数があればファイルとして読み込み、無ければ標準入力を使用する。
read_input() {
  if [[ $# -ge 1 ]]; then
    local file="$1"
    if [[ ! -f "${file}" ]]; then
      \printf 'エラー: ファイルが見つかりません: %s\n' "${file}" >&2
      exit 1
    fi
    \cat -- "${file}"
  else
    \cat
  fi
}

# 整形処理: 行末空白削除 + 共通先頭空白削除(dedent)
#
# 「空白」には半角スペース・タブ等(ASCII空白)に加え、全角空白(U+3000)も含める。
# [[:space:]] が U+3000 にマッチするかは awk 実装・ロケール依存(macOSの awk は
# 非マッチ、Linuxの gawk はマッチ)で挙動が割れるため、正規表現に U+3000 を
# 明示追加して OS 間の差異を吸収する。
#
# 先頭空白の除去は「文字単位で1個ずつ」行う。これは substr のバイト数指定だと
# 全角空白(マルチバイト)を途中で分断し不正なバイト列を生む恐れがあるため。
# 各行から共通の最小空白数 min 個ぶんの先頭空白文字を取り除く。
format_text() {
  \awk '
  # 文字列 s の先頭にある空白文字の個数を数える(全角空白も1個として数える)
  function count_leading_ws(s,    n) {
      n = 0
      while (match(s, /^([[:space:]]|　)/)) {
          s = substr(s, RLENGTH + 1)   # マッチした1文字ぶんを取り除く
          n++
      }
      return n
  }
  {
      sub(/([[:space:]]|　)+$/, "")     # 行末空白(全角含む)を削除
      if ($0 ~ /[^[:space:]　]/) {      # 空白のみでない行(空行扱いの行を除く)を集計対象
          n = count_leading_ws($0)
          if (min == "" || n < min)
              min = n
      }
      lines[NR] = $0
  }
  END {
      if (min == "") min = 0            # 全行が空白のみ 等で min 未確定の場合
      for (i = 1; i <= NR; i++) {
          line = lines[i]
          removed = 0
          # 先頭空白を min 個だけ文字単位で除去(マルチバイトを分断しない)
          while (removed < min && match(line, /^([[:space:]]|　)/)) {
              line = substr(line, RLENGTH + 1)
              removed++
          }
          print line
      }
  }
  '
}

main() {
  local clip_cmd
  clip_cmd="$(detect_clipboard_cmd)"

  read_input "$@" | format_text | ${clip_cmd}

  \printf 'クリップボードにコピーしました (使用コマンド: %s)\n' "${clip_cmd}" >&2
}

main "$@"
