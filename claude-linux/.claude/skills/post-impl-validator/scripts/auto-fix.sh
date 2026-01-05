#!/usr/bin/env bash
#
# auto-fix.sh - 自動修正を試行（最大3回リトライ）
#
# 使用方法:
#   ./auto-fix.sh <project_type> <workdir>
#
# 引数:
#   project_type  プロジェクトタイプ (go | typescript-react | terraform)
#   workdir       作業ディレクトリ
#
# 戻り値:
#   0: 修正成功
#   1: 修正失敗（リトライ上限到達）
#   2: 自動修正非対応またはコマンド実行エラー

set -uo pipefail

# 定数
readonly SCRIPT_NAME="$(basename "$0")"
readonly MAX_RETRIES=3
readonly SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# 色定義
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[0;33m'
readonly BLUE='\033[0;34m'
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

log_retry() {
    echo -e "${BLUE}[RETRY]${NC} $*" >&2
}

# 使用方法を表示
usage() {
    cat << EOF >&2
Usage: ${SCRIPT_NAME} <project_type> <workdir>

プロジェクトタイプ別に自動修正を試行します。
修正後にLintを再実行し、成功するまで最大${MAX_RETRIES}回リトライします。

Arguments:
  project_type  プロジェクトタイプ (go | typescript-react | terraform)
  workdir       作業ディレクトリ

Environment Variables:
  GO_FIX_CMD    Go用の自動修正コマンド（デフォルト: なし - 手動修正）
  GO_LINT_CMD   Go用のLintコマンド（デフォルト: go vet ./...）
  TS_FIX_CMD    TypeScript/React用の自動修正コマンド（デフォルト: npm run lint -- --fix）
  TS_LINT_CMD   TypeScript/React用のLintコマンド（デフォルト: npm run lint）
  TF_FIX_CMD    Terraform用の自動修正コマンド（デフォルト: terraform fmt -recursive）
  TF_LINT_CMD   Terraform用のLintコマンド（デフォルト: terraform fmt -check -recursive）

Exit codes:
  0: 修正成功
  1: 修正失敗（リトライ上限到達）
  2: 自動修正非対応またはコマンド実行エラー
EOF
}

# コマンドの存在確認
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Go用自動修正
fix_go() {
    local workdir="$1"
    local fix_cmd="${GO_FIX_CMD:-}"
    local lint_cmd="${GO_LINT_CMD:-go vet ./...}"

    # GO_FIX_CMD が指定されていない場合は手動修正を案内
    if [[ -z "$fix_cmd" ]]; then
        log_warn "Go は自動修正に非対応です"
        log_info "手動で以下のコマンドを実行してください:"
        log_info "  gofmt -w ."
        log_info "  goimports -w ."
        log_info "または GO_FIX_CMD 環境変数でカスタムコマンドを指定できます"
        return 2
    fi

    cd "$workdir" || return 2

    log_info "Go 自動修正を実行しています: $fix_cmd"

    local retry=0
    while [[ $retry -lt $MAX_RETRIES ]]; do
        retry=$((retry + 1))

        # 自動修正を実行
        log_info "自動修正を実行中... (試行 ${retry}/${MAX_RETRIES})"
        if ! eval "$fix_cmd" 2>&1; then
            log_warn "自動修正コマンドが非ゼロで終了しました"
        fi

        # Lintを再実行して検証
        log_info "修正を検証中..."
        if eval "$lint_cmd" >/dev/null 2>&1; then
            log_success "自動修正が成功しました (試行 ${retry}/${MAX_RETRIES})"
            return 0
        fi

        if [[ $retry -lt $MAX_RETRIES ]]; then
            log_retry "まだエラーが残っています。再試行します..."
        fi
    done

    log_error "自動修正に失敗しました。リトライ上限 (${MAX_RETRIES}) に到達しました"
    log_info "手動での修正が必要です"
    return 1
}

# TypeScript/React用自動修正
fix_typescript() {
    local workdir="$1"
    local fix_cmd="${TS_FIX_CMD:-}"
    local lint_cmd="${TS_LINT_CMD:-}"

    cd "$workdir" || return 2

    # package.json の存在確認
    if [[ ! -f "package.json" ]]; then
        log_error "package.json が見つかりません: $workdir"
        return 2
    fi

    # パッケージマネージャーの検出
    local pkg_manager="npm"
    if command_exists pnpm && [[ -f "pnpm-lock.yaml" ]]; then
        pkg_manager="pnpm"
    elif command_exists yarn && [[ -f "yarn.lock" ]]; then
        pkg_manager="yarn"
    fi

    # 自動修正コマンドの決定
    if [[ -z "$fix_cmd" ]]; then
        if grep -q '"lint:fix"' package.json 2>/dev/null; then
            fix_cmd="$pkg_manager run lint:fix"
        elif grep -q '"lint"' package.json 2>/dev/null; then
            case "$pkg_manager" in
                pnpm)
                    fix_cmd="pnpm run lint -- --fix"
                    ;;
                yarn)
                    fix_cmd="yarn lint --fix"
                    ;;
                *)
                    fix_cmd="npm run lint -- --fix"
                    ;;
            esac
        else
            log_error "package.json に lint スクリプトが定義されていません"
            return 2
        fi
    fi

    # Lintコマンドの決定
    if [[ -z "$lint_cmd" ]]; then
        if grep -q '"lint"' package.json 2>/dev/null; then
            lint_cmd="$pkg_manager run lint"
        else
            log_error "package.json に lint スクリプトが定義されていません"
            return 2
        fi
    fi

    log_info "TypeScript/React 自動修正を実行しています: $fix_cmd"

    local retry=0
    while [[ $retry -lt $MAX_RETRIES ]]; do
        retry=$((retry + 1))

        # 自動修正を実行
        log_info "自動修正を実行中... (試行 ${retry}/${MAX_RETRIES})"
        if ! eval "$fix_cmd" 2>&1; then
            log_warn "自動修正コマンドが非ゼロで終了しました"
        fi

        # Lintを再実行して検証
        log_info "修正を検証中..."
        if eval "$lint_cmd" >/dev/null 2>&1; then
            log_success "自動修正が成功しました (試行 ${retry}/${MAX_RETRIES})"
            return 0
        fi

        if [[ $retry -lt $MAX_RETRIES ]]; then
            log_retry "まだエラーが残っています。再試行します..."
        fi
    done

    log_error "自動修正に失敗しました。リトライ上限 (${MAX_RETRIES}) に到達しました"
    log_info "手動での修正が必要です"
    return 1
}

# Terraform用自動修正
fix_terraform() {
    local workdir="$1"
    local fix_cmd="${TF_FIX_CMD:-terraform fmt -recursive}"
    local lint_cmd="${TF_LINT_CMD:-terraform fmt -check -recursive}"

    log_info "Terraform 自動修正を実行しています: $fix_cmd"

    # デフォルトコマンドの場合は terraform コマンドの存在確認
    if [[ -z "${TF_FIX_CMD:-}" ]] && ! command_exists terraform; then
        log_error "terraform コマンドが見つかりません"
        return 2
    fi

    cd "$workdir" || return 2

    # デフォルトコマンドの場合のみ .tf ファイルの存在確認
    if [[ -z "${TF_FIX_CMD:-}" ]]; then
        if ! ls ./*.tf >/dev/null 2>&1 && ! ls ./**/*.tf >/dev/null 2>&1; then
            log_error "Terraform ファイル (.tf) が見つかりません: $workdir"
            return 2
        fi
    fi

    local retry=0
    while [[ $retry -lt $MAX_RETRIES ]]; do
        retry=$((retry + 1))

        # 自動フォーマットを実行
        log_info "自動修正を実行中... (試行 ${retry}/${MAX_RETRIES})"
        if ! eval "$fix_cmd" 2>&1; then
            log_warn "自動修正コマンドが非ゼロで終了しました"
        fi

        # Lintで検証
        log_info "修正を検証中..."
        if eval "$lint_cmd" >/dev/null 2>&1; then
            log_success "自動修正が成功しました (試行 ${retry}/${MAX_RETRIES})"
            return 0
        fi

        if [[ $retry -lt $MAX_RETRIES ]]; then
            log_retry "まだエラーが残っています。再試行します..."
        fi
    done

    log_error "自動修正に失敗しました。リトライ上限 (${MAX_RETRIES}) に到達しました"
    log_info "手動での修正が必要です"
    return 1
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

    # プロジェクトタイプ別に自動修正実行
    case "$project_type" in
        go)
            fix_go "$workdir"
            ;;
        typescript-react|typescript|react|ts|tsx)
            fix_typescript "$workdir"
            ;;
        terraform|tf)
            fix_terraform "$workdir"
            ;;
        *)
            log_error "未対応のプロジェクトタイプです: $project_type"
            log_error "対応タイプ: go, typescript-react, terraform"
            exit 2
            ;;
    esac
}

main "$@"
