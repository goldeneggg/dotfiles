#!/usr/bin/env bash
#
# detect-changes.sh - Git差分から変更ファイルを検出しJSON形式で出力
#
# 使用方法:
#   ./detect-changes.sh [repo_path]
#
# 出力形式:
#   JSON形式で変更ファイルを出力
#   {
#     "projects": [
#       {"type": "go", "workdir": "/path/to/project", "files": ["main.go"], "count": 1}
#     ],
#     "total_files": 1
#   }
#
# 戻り値:
#   0: 成功
#   1: Gitリポジトリではない
#   2: 引数エラー

set -euo pipefail

# 定数
readonly SCRIPT_NAME="$(basename "$0")"

# 色定義（ログ出力用）
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

# 使用方法を表示
usage() {
    cat << EOF >&2
Usage: ${SCRIPT_NAME} [repo_path]

Git差分から変更ファイルを検出しJSON形式で出力します。

Arguments:
  repo_path   検出対象のリポジトリパス（省略時はカレントディレクトリ）

Exit codes:
  0: 成功
  1: Gitリポジトリではない
  2: 引数エラー
EOF
}

# JSONをエスケープ
json_escape() {
    local str="$1"
    str="${str//\\/\\\\}"
    str="${str//\"/\\\"}"
    str="${str//$'\n'/\\n}"
    str="${str//$'\r'/\\r}"
    str="${str//$'\t'/\\t}"
    echo "$str"
}

# ファイル拡張子からプロジェクトタイプを判定
get_project_type() {
    local file="$1"
    case "$file" in
        *.go)
            echo "go"
            ;;
        *.ts|*.tsx)
            echo "typescript-react"
            ;;
        *.tf)
            echo "terraform"
            ;;
        *)
            echo ""
            ;;
    esac
}

# ファイルからプロジェクトルートを推定
get_project_root() {
    local file="$1"
    local repo_root="$2"
    local dir

    dir="$(dirname "$file")"

    # go.mod, package.json, main.tf などを探す
    while [[ "$dir" != "." && "$dir" != "/" && "$dir" != "$repo_root" ]]; do
        if [[ -f "${repo_root}/${dir}/go.mod" ]] || \
           [[ -f "${repo_root}/${dir}/package.json" ]] || \
           [[ -f "${repo_root}/${dir}/main.tf" ]]; then
            echo "${repo_root}/${dir}"
            return
        fi
        dir="$(dirname "$dir")"
    done

    # プロジェクトルートが見つからない場合はリポジトリルート
    echo "$repo_root"
}

# メイン処理
main() {
    local repo_path="${1:-.}"

    # ヘルプオプション
    if [[ "$repo_path" == "-h" || "$repo_path" == "--help" ]]; then
        usage
        exit 0
    fi

    # 絶対パスに変換
    repo_path="$(cd "$repo_path" 2>/dev/null && pwd)" || {
        log_error "指定されたパスが存在しません: $1"
        exit 2
    }

    # Gitリポジトリか確認
    if ! git -C "$repo_path" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
        log_error "Gitリポジトリではありません: $repo_path"
        exit 1
    fi

    # 変更ファイルを取得（staged + unstaged + untracked）
    local changed_files=()
    local file

    # staged files
    while IFS= read -r file; do
        [[ -n "$file" ]] && changed_files+=("$file")
    done < <(git -C "$repo_path" diff --cached --name-only 2>/dev/null)

    # unstaged files
    while IFS= read -r file; do
        [[ -n "$file" ]] && changed_files+=("$file")
    done < <(git -C "$repo_path" diff --name-only 2>/dev/null)

    # untracked files
    while IFS= read -r file; do
        [[ -n "$file" ]] && changed_files+=("$file")
    done < <(git -C "$repo_path" ls-files --others --exclude-standard 2>/dev/null)

    # 重複を除去
    local unique_files=()
    local -A seen=()
    for file in "${changed_files[@]}"; do
        if [[ -z "${seen[$file]:-}" ]]; then
            seen[$file]=1
            unique_files+=("$file")
        fi
    done

    # プロジェクトタイプごとにファイルを分類
    declare -A project_files
    declare -A project_workdirs

    for file in "${unique_files[@]}"; do
        local project_type
        project_type="$(get_project_type "$file")"

        if [[ -n "$project_type" ]]; then
            local workdir
            workdir="$(get_project_root "$file" "$repo_path")"
            local key="${project_type}:${workdir}"

            if [[ -z "${project_files[$key]:-}" ]]; then
                project_files[$key]="$file"
                project_workdirs[$key]="$workdir"
            else
                project_files[$key]="${project_files[$key]}|$file"
            fi
        fi
    done

    # JSON出力を構築
    local json_projects=""
    local total_files=0
    local first=true

    # プロジェクトタイプの優先順位（Terraform, Go, TypeScript/React）
    local -a sorted_keys=()
    for key in "${!project_files[@]}"; do
        sorted_keys+=("$key")
    done

    # ソート（terraform, go, typescript-react の順）
    IFS=$'\n' sorted_keys=($(printf '%s\n' "${sorted_keys[@]}" | sort -t: -k1,1))
    unset IFS

    for key in "${sorted_keys[@]}"; do
        local project_type="${key%%:*}"
        local workdir="${project_workdirs[$key]}"
        local files_str="${project_files[$key]}"

        # ファイルリストを配列に分割
        IFS='|' read -ra files_array <<< "$files_str"
        local count=${#files_array[@]}
        total_files=$((total_files + count))

        # JSON配列を構築
        local json_files=""
        local first_file=true
        for f in "${files_array[@]}"; do
            if $first_file; then
                json_files="\"$(json_escape "$f")\""
                first_file=false
            else
                json_files="${json_files},\"$(json_escape "$f")\""
            fi
        done

        local project_json
        project_json=$(cat << EOF
{"type":"${project_type}","workdir":"$(json_escape "$workdir")","files":[${json_files}],"count":${count}}
EOF
)

        if $first; then
            json_projects="$project_json"
            first=false
        else
            json_projects="${json_projects},${project_json}"
        fi
    done

    # 最終JSON出力
    cat << EOF
{"projects":[${json_projects}],"total_files":${total_files}}
EOF
}

main "$@"
