#!/usr/bin/env bash
#
# run-tests.sh - プロジェクトタイプ別にテスト実行
#
# 使用方法:
#   ./run-tests.sh <project_type> <workdir>
#
# 引数:
#   project_type  プロジェクトタイプ (go | typescript-react | terraform)
#   workdir       作業ディレクトリ
#
# 戻り値:
#   0: 成功（テストパス）
#   1: テスト失敗
#   2: コマンド実行エラー（コマンドが見つからない等）

set -uo pipefail

# 定数
readonly SCRIPT_NAME="$(basename "$0")"

# 色定義
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[0;33m'
readonly NC='\033[0m' # No Color

# ログ関数
log_error() {
    echo -e "${RED}[ERROR]${NC} $*" >&2
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $*" >&2
}

log_info() {
    echo -e "${GREEN}[INFO]${NC} $*" >&2
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*" >&2
}

# 使用方法を表示
usage() {
    cat << EOF >&2
Usage: ${SCRIPT_NAME} <project_type> <workdir>

プロジェクトタイプ別にテストを実行します。

Arguments:
  project_type  プロジェクトタイプ (go | typescript-react | terraform)
  workdir       作業ディレクトリ

Environment Variables:
  GO_TEST_CMD   Go用のテストコマンド（デフォルト: go test -shuffle on -race -cover ./...）
  GO_TEST_FLAGS 追加のGoテストフラグ（GO_TEST_CMD未指定時のみ有効）
  TS_TEST_CMD   TypeScript/React用のテストコマンド（デフォルト: npm test）
  TF_TEST_CMD   Terraform用のテストコマンド（デフォルト: terraform validate）

Exit codes:
  0: 成功（テストパス）
  1: テスト失敗
  2: コマンド実行エラー
EOF
}

# コマンドの存在確認
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Go用テスト実行
run_go_tests() {
    local workdir="$1"
    local test_cmd="${GO_TEST_CMD:-}"
    local test_flags="${GO_TEST_FLAGS:--shuffle on -race -cover}"

    # GO_TEST_CMD が指定されていなければデフォルトコマンドを構築
    if [[ -z "$test_cmd" ]]; then
        test_cmd="go test ${test_flags} ./..."
    fi

    log_info "Go テストを実行しています: $test_cmd"

    # デフォルトコマンドの場合は go コマンドの存在確認
    if [[ -z "${GO_TEST_CMD:-}" ]] && ! command_exists go; then
        log_error "go コマンドが見つかりません"
        return 2
    fi

    cd "$workdir" || return 2

    # デフォルトコマンドの場合のみ go.mod の存在確認
    if [[ -z "${GO_TEST_CMD:-}" ]] && [[ ! -f "go.mod" ]]; then
        log_warn "go.mod が見つかりません。モジュール外での実行となります"
    fi

    local output
    local exit_code

    output=$(eval "$test_cmd" 2>&1) || exit_code=$?
    exit_code=${exit_code:-0}

    echo "$output"

    if [[ $exit_code -eq 0 ]]; then
        log_success "Go テスト: 全テストパス"
        return 0
    else
        log_error "Go テスト: 一部のテストが失敗しました"
        return 1
    fi
}

# TypeScript/React用テスト実行
run_typescript_tests() {
    local workdir="$1"
    local test_cmd="${TS_TEST_CMD:-}"

    cd "$workdir" || return 2

    # package.json の存在確認
    if [[ ! -f "package.json" ]]; then
        log_error "package.json が見つかりません: $workdir"
        return 2
    fi

    # テストコマンドの決定
    if [[ -z "$test_cmd" ]]; then
        # package.json から test スクリプトを検出
        if grep -q '"test"' package.json 2>/dev/null; then
            if command_exists pnpm && [[ -f "pnpm-lock.yaml" ]]; then
                test_cmd="pnpm test"
            elif command_exists yarn && [[ -f "yarn.lock" ]]; then
                test_cmd="yarn test"
            elif command_exists npm; then
                test_cmd="npm test"
            else
                log_error "npm, yarn, pnpm のいずれも見つかりません"
                return 2
            fi
        else
            log_warn "package.json に test スクリプトが定義されていません"
            log_warn "環境変数 TS_TEST_CMD でカスタムコマンドを指定できます"
            return 2
        fi
    fi

    log_info "TypeScript/React テストを実行しています: $test_cmd"

    local output
    local exit_code

    output=$(eval "$test_cmd" 2>&1) || exit_code=$?
    exit_code=${exit_code:-0}

    echo "$output"

    if [[ $exit_code -eq 0 ]]; then
        log_success "TypeScript/React テスト: 全テストパス"
        return 0
    else
        log_error "TypeScript/React テスト: 一部のテストが失敗しました"
        return 1
    fi
}

# Terraform用バリデーション実行
run_terraform_validate() {
    local workdir="$1"
    local test_cmd="${TF_TEST_CMD:-terraform validate}"

    log_info "Terraform テストを実行しています: $test_cmd"

    # デフォルトコマンドの場合は terraform コマンドの存在確認
    if [[ -z "${TF_TEST_CMD:-}" ]] && ! command_exists terraform; then
        log_error "terraform コマンドが見つかりません"
        return 2
    fi

    cd "$workdir" || return 2

    # デフォルトコマンドの場合のみ .tf ファイルの存在確認と init 実行
    if [[ -z "${TF_TEST_CMD:-}" ]]; then
        if ! ls ./*.tf >/dev/null 2>&1 && ! ls ./**/*.tf >/dev/null 2>&1; then
            log_error "Terraform ファイル (.tf) が見つかりません: $workdir"
            return 2
        fi

        # terraform init が必要かチェック
        if [[ ! -d ".terraform" ]]; then
            log_info "terraform init を実行しています..."
            if ! terraform init -backend=false >/dev/null 2>&1; then
                log_warn "terraform init に失敗しました。バリデーションを続行します"
            fi
        fi
    fi

    local output
    local exit_code

    output=$(eval "$test_cmd" 2>&1) || exit_code=$?
    exit_code=${exit_code:-0}

    echo "$output"

    if [[ $exit_code -eq 0 ]]; then
        log_success "Terraform テスト: 成功"
        return 0
    else
        log_error "Terraform テスト: 失敗しました"
        return 1
    fi
}

# メイン処理
main() {
    # 引数チェック
    if [[ $# -lt 2 ]]; then
        log_error "引数が不足しています"
        usage
        exit 2
    fi

    local project_type="$1"
    local workdir="$2"

    # ヘルプオプション
    if [[ "$project_type" == "-h" || "$project_type" == "--help" ]]; then
        usage
        exit 0
    fi

    # 作業ディレクトリの存在確認
    if [[ ! -d "$workdir" ]]; then
        log_error "作業ディレクトリが存在しません: $workdir"
        exit 2
    fi

    # 絶対パスに変換
    workdir="$(cd "$workdir" && pwd)"

    # プロジェクトタイプ別にテスト実行
    case "$project_type" in
        go)
            run_go_tests "$workdir"
            ;;
        typescript-react|typescript|react|ts|tsx)
            run_typescript_tests "$workdir"
            ;;
        terraform|tf)
            run_terraform_validate "$workdir"
            ;;
        *)
            log_error "未対応のプロジェクトタイプです: $project_type"
            log_error "対応タイプ: go, typescript-react, terraform"
            exit 2
            ;;
    esac
}

main "$@"
