#!/usr/bin/env bash
#
# run-lint.sh - プロジェクトタイプ別にLint実行
#
# 使用方法:
#   ./run-lint.sh <project_type> <workdir>
#
# 引数:
#   project_type  プロジェクトタイプ (go | typescript-react | terraform)
#   workdir       作業ディレクトリ
#
# 戻り値:
#   0: 成功（Lintエラーなし）
#   1: Lintエラー検出
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

プロジェクトタイプ別にLintを実行します。

Arguments:
  project_type  プロジェクトタイプ (go | typescript-react | terraform)
  workdir       作業ディレクトリ

Environment Variables:
  GO_LINT_CMD   Go用のLintコマンド（デフォルト: go vet ./...）
  TS_LINT_CMD   TypeScript/React用のLintコマンド（デフォルト: npm run lint）
  TF_LINT_CMD   Terraform用のLintコマンド（デフォルト: terraform fmt -check -recursive）

Exit codes:
  0: 成功（Lintエラーなし）
  1: Lintエラー検出
  2: コマンド実行エラー
EOF
}

# コマンドの存在確認
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Go用Lint実行
run_go_lint() {
    local workdir="$1"
    local lint_cmd="${GO_LINT_CMD:-go vet ./...}"

    log_info "Go Lint を実行しています: $lint_cmd"

    # デフォルトコマンドの場合は go コマンドの存在確認
    if [[ -z "${GO_LINT_CMD:-}" ]] && ! command_exists go; then
        log_error "go コマンドが見つかりません"
        return 2
    fi

    cd "$workdir" || return 2

    if eval "$lint_cmd" 2>&1; then
        log_success "Go Lint: エラーなし"
        return 0
    else
        log_error "Go Lint: エラーを検出しました"
        return 1
    fi
}

# TypeScript/React用Lint実行
run_typescript_lint() {
    local workdir="$1"
    local lint_cmd="${TS_LINT_CMD:-}"

    cd "$workdir" || return 2

    # package.json の存在確認
    if [[ ! -f "package.json" ]]; then
        log_error "package.json が見つかりません: $workdir"
        return 2
    fi

    # Lintコマンドの決定
    if [[ -z "$lint_cmd" ]]; then
        # package.json から lint スクリプトを検出
        if grep -q '"lint"' package.json 2>/dev/null; then
            if command_exists pnpm && [[ -f "pnpm-lock.yaml" ]]; then
                lint_cmd="pnpm run lint"
            elif command_exists yarn && [[ -f "yarn.lock" ]]; then
                lint_cmd="yarn lint"
            elif command_exists npm; then
                lint_cmd="npm run lint"
            else
                log_error "npm, yarn, pnpm のいずれも見つかりません"
                return 2
            fi
        else
            log_warn "package.json に lint スクリプトが定義されていません"
            log_warn "環境変数 TS_LINT_CMD でカスタムコマンドを指定できます"
            return 2
        fi
    fi

    log_info "TypeScript/React Lint を実行しています: $lint_cmd"

    if eval "$lint_cmd" 2>&1; then
        log_success "TypeScript/React Lint: エラーなし"
        return 0
    else
        log_error "TypeScript/React Lint: エラーを検出しました"
        return 1
    fi
}

# Terraform用Lint実行
run_terraform_lint() {
    local workdir="$1"
    local lint_cmd="${TF_LINT_CMD:-terraform fmt -check -recursive}"

    log_info "Terraform Lint を実行しています: $lint_cmd"

    # デフォルトコマンドの場合は terraform コマンドの存在確認
    if [[ -z "${TF_LINT_CMD:-}" ]] && ! command_exists terraform; then
        log_error "terraform コマンドが見つかりません"
        return 2
    fi

    cd "$workdir" || return 2

    # デフォルトコマンドの場合のみ .tf ファイルの存在確認
    if [[ -z "${TF_LINT_CMD:-}" ]]; then
        if ! ls ./*.tf >/dev/null 2>&1 && ! ls ./**/*.tf >/dev/null 2>&1; then
            log_error "Terraform ファイル (.tf) が見つかりません: $workdir"
            return 2
        fi
    fi

    if eval "$lint_cmd" 2>&1; then
        log_success "Terraform Lint: エラーなし"
        return 0
    else
        log_error "Terraform Lint: エラーを検出しました"
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

    # プロジェクトタイプ別にLint実行
    case "$project_type" in
        go)
            run_go_lint "$workdir"
            ;;
        typescript-react|typescript|react|ts|tsx)
            run_typescript_lint "$workdir"
            ;;
        terraform|tf)
            run_terraform_lint "$workdir"
            ;;
        *)
            log_error "未対応のプロジェクトタイプです: $project_type"
            log_error "対応タイプ: go, typescript-react, terraform"
            exit 2
            ;;
    esac
}

main "$@"
