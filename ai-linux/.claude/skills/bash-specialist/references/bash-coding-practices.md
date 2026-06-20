# Bashスクリプト コーディング規約

## 目次

1. [規約](#1-規約) — 各セクションの設計意図と守るべきルール
2. [テンプレート](#2-テンプレート) — 規約を反映した完全なスクリプト雛形

規約セクションで「なぜそうすべきか」を理解し、テンプレートセクションで「具体的にどう書くか」を参照する。

---

## 1. 規約

### 1.1. 基本構造

- **Shebang**: `#!/bin/bash`
- **エラーハンドリング**: `set -euo pipefail` をスクリプト冒頭で宣言
  - `-e`: コマンド失敗時に即座にスクリプトを終了させる
  - `-u`: 未定義変数の参照をエラーにする（タイポによる事故を防ぐ）
  - `-o pipefail`: パイプライン途中のコマンド失敗を検出する（デフォルトでは最後のコマンドの終了ステータスしか見ない）
- **main関数 + 実行ガード**: 処理を `main` 関数にまとめ、末尾に `if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then main "$@"; fi` を配置。`source` で読み込んだ際に関数ライブラリとして再利用可能にするため

### 1.2. 引数解析

`_parse_arg` 関数で `while` + `case` パターンを使用する:

- `-h | --help` と `-V | --version` を必ず実装
- 値を取るオプション（例: `-c | --config`）は引数の存在を検証してから `shift 2`
- フラグオプション（`-v`, `-q`, `-n`, `-d`）は対応する変数を `true` にして `shift`
- 未知のオプション（`-*`）はエラーメッセージを出して終了
- オプション以外の残り引数は `args` 配列に格納

### 1.3. 関数と命名

- 論理的な処理単位で関数に分割
- private関数は `_` prefix（例: `_parse_arg`, `_load_config`）
- 関数内の変数は `local` で宣言し、グローバル変数の汚染を防ぐ

### 1.4. ログ出力

ログは `>&2`（stderr）に出力し、スクリプトの実行結果（stdout）と分離する。
パイプやリダイレクトでスクリプト出力を処理する際に、ログが混入しないようにするため。

- `_debug`: `--debug` 時のみ出力（内部変数の状態など）
- `_verbose`: `--verbose` 時のみ出力（処理の進行状況）
- `_info`: 通常時に出力（`--quiet` で抑制）
- `_warn` / `_error`: 常に出力（抑制しない）

### 1.5. ヘルプメッセージ

`_usage` 関数で `cat << EOU ... EOU`（Here Document）を使い、以下を記載:
目的、Options、Args、Examples。
stderr に出力する（`>&2`）。

### 1.6. メイン処理

- ビジネスロジックは `_process_args` 関数に実装
- `--dry-run` モード時は実際の処理を実行せず、何が行われるかの出力のみ
- 引数の数（`${#args[@]}`）に応じて処理を分岐

---

## 2. テンプレート

以下を基盤としてスクリプトを構築する。
構成順序: グローバル変数 → ログ関数 → _version/_usage → _parse_arg → ビジネスロジック → main → 実行ガード

```bash
#!/bin/bash

#--------------------
#
# テンプレートスクリプト
# コマンドラインオプションと引数をparseし、main functionを処理して結果をstdoutに出力する
#
#--------------------

set -euo pipefail

# グローバル変数の初期化
args=()
config_file=""
debug_mode=false
verbose_mode=false
quiet_mode=false
dry_run_mode=false
script_version="1.0.0"

# ログ出力関数
_debug() {
  if [[ "${debug_mode}" == "true" ]]; then
    echo "DEBUG: $*" >&2
  fi
}

_verbose() {
  if [[ "${verbose_mode}" == "true" && "${quiet_mode}" == "false" ]]; then
    echo "INFO: $*" >&2
  fi
}

_info() {
  if [[ "${quiet_mode}" == "false" ]]; then
    echo "INFO: $*" >&2
  fi
}

_warn() {
  echo "WARN: $*" >&2
}

_error() {
  echo "ERROR: $*" >&2
}

_version() {
  echo "${script_version}"
}

_usage (){
  cat << EOU >&2
Usage: $0 [Options] <Args...>

汎用bashスクリプトテンプレート
このテンプレートをベースに様々な用途のスクリプトを作成できます

Options:
  -c | --config <PATH>         設定ファイルのパス
  -v | --verbose               詳細出力モード（処理の進行状況を表示）
  -q | --quiet                 静寂モード（エラー以外出力しない）
  -n | --dry-run               実行せずに何を行うかだけ表示
  -d | --debug                 デバッグモード（内部変数や技術詳細を表示）
  -V | --version               バージョン情報を表示
  -h | --help                  このヘルプメッセージを表示

Args:
  args...                      任意の数の引数を指定可能

Examples:
  $0 arg1 arg2                               # 基本的な使用
  $0 --verbose --config ./config.txt arg1   # 設定ファイルと詳細出力
  $0 --debug arg1 arg2                       # デバッグ情報付きで実行
  $0 --dry-run --verbose arg1 arg2 arg3      # ドライランと詳細出力

Logging Levels:
  通常      : 結果のみ出力
  --verbose : + 処理の進行状況を表示
  --debug   : + 内部変数や技術詳細を表示

EOU
}

_parse_arg (){
  while true
  do
    if [[ $# == 0 ]]
    then
      break
    fi

    case "$1" in
      -h | --help)
        _usage
        exit 0
        ;;
      -V | --version)
        _version
        exit 0
        ;;
      -c | --config)
        if [[ -z "${2:-}" ]] || [[ "${2:-}" =~ ^-+ ]]
        then
          _error "$1 option requires an argument"
          _usage
          exit 1
        fi
        config_file="$2"
        shift 2
        ;;
      -v | --verbose)
        verbose_mode=true
        shift
        ;;
      -q | --quiet)
        quiet_mode=true
        shift
        ;;
      -n | --dry-run)
        dry_run_mode=true
        shift
        ;;
      -d | --debug)
        debug_mode=true
        shift
        ;;
      -*)
        _error "illegal option '${1}'"
        _usage
        exit 1
        ;;
      *)
        while [[ $# -gt 0 ]]; do
          args+=("$1")
          shift
        done
        break
        ;;
    esac
  done

  if [[ -n "${config_file}" && ! -f "${config_file}" ]]; then
    _error "Config file not found: ${config_file}"
    exit 1
  fi

  _debug "parsed options:"
  _debug "  config_file  = [${config_file:-}]"
  _debug "  verbose_mode = [${verbose_mode}]"
  _debug "  quiet_mode   = [${quiet_mode}]"
  _debug "  dry_run_mode = [${dry_run_mode}]"
  _debug "  debug_mode   = [${debug_mode}]"
  _debug "  args         = [${args[*]:-}]"
  _debug "  args count   = [${#args[@]}]"
}

_load_config() {
  if [[ -n "${config_file}" ]]; then
    _verbose "Loading config from: ${config_file}"
  fi
}

_process_args() {
  local result=""

  if [[ "${dry_run_mode}" == "true" ]]; then
    _info "DRY RUN MODE: Would process the following:"
  fi

  if [[ ${#args[@]} -eq 0 ]]; then
    _verbose "No arguments provided, using default action"
    if [[ "${dry_run_mode}" == "true" ]]; then
      result="[DRY RUN] Default action would be executed"
    else
      _verbose "Executing default action..."
      result="Default action executed"
    fi
  else
    _verbose "Processing ${#args[@]} arguments"
    _debug "Arguments received: ${args[*]}"

    if [[ "${dry_run_mode}" == "true" ]]; then
      result="[DRY RUN] Would process arguments: [${args[*]}]"
    else
      _verbose "Executing argument processing..."
      result="Processing arguments: [${args[*]}]"
    fi
  fi

  echo "${result}"
}

main() {
  local script_dir
  script_dir=$(cd "$(dirname "${0}")" && pwd)
  _debug "Script directory: ${script_dir}"

  _parse_arg "$@"

  _load_config

  local main_result
  main_result=$(_process_args)

  if [[ "${quiet_mode}" == "false" ]]; then
    echo "${main_result}"
  fi
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  main "$@"
fi
```
