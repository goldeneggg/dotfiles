#!/usr/bin/env bash
# repo-snapshot.sh — リポジトリの構造スナップショットを取得する
# 使い方: bash repo-snapshot.sh /path/to/repo
#
# プロジェクトの技術スタック、構造、主要な設定を簡潔にまとめて出力する。
# tech-fit-analyzer スキルのリポジトリ分析フェーズで使用。

set -euo pipefail

REPO_PATH="${1:?使い方: repo-snapshot.sh /path/to/repo}"

if [ ! -d "$REPO_PATH" ]; then
  echo "エラー: ディレクトリが見つかりません: $REPO_PATH"
  exit 1
fi

echo "=== リポジトリスナップショット ==="
echo "パス: $REPO_PATH"
echo "スキャン日時: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo ""

# --- ディレクトリ構造（2階層、隠しディレクトリとnode_modules除外） ---
echo "=== ディレクトリ構造 ==="
find "$REPO_PATH" -maxdepth 2 \
  -not -path '*/\.*' \
  -not -path '*/node_modules/*' \
  -not -path '*/__pycache__/*' \
  -not -path '*/target/*' \
  -not -path '*/dist/*' \
  -not -path '*/build/*' \
  -not -path '*/.git/*' \
  | head -80 \
  | sed "s|^$REPO_PATH|.|"
echo ""

# --- 検出された設定ファイル ---
echo "=== 設定ファイル ==="
CONFIG_FILES=(
  "package.json" "tsconfig.json" "Cargo.toml" "go.mod" "go.sum"
  "pyproject.toml" "requirements.txt" "Pipfile" "setup.py" "setup.cfg"
  "Gemfile" "build.gradle" "build.gradle.kts" "pom.xml"
  "composer.json" "mix.exs" "pubspec.yaml" "deno.json" "bun.lockb"
  ".eslintrc.json" ".eslintrc.js" ".prettierrc" "biome.json"
  "vite.config.ts" "vite.config.js" "webpack.config.js" "rollup.config.js"
  "turbo.json" "nx.json" ".swcrc"
  "Dockerfile" "docker-compose.yml" "docker-compose.yaml" "compose.yml" "compose.yaml"
  "Makefile" "justfile" "Taskfile.yml"
)

for f in "${CONFIG_FILES[@]}"; do
  if [ -f "$REPO_PATH/$f" ]; then
    echo "  検出: $f"
  fi
done
echo ""

# --- CI/CD 設定 ---
echo "=== CI/CD ==="
[ -d "$REPO_PATH/.github/workflows" ] && echo "  GitHub Actions:" && ls "$REPO_PATH/.github/workflows/" 2>/dev/null | sed 's/^/    /'
[ -f "$REPO_PATH/.gitlab-ci.yml" ] && echo "  GitLab CI: .gitlab-ci.yml"
[ -f "$REPO_PATH/Jenkinsfile" ] && echo "  Jenkins: Jenkinsfile"
[ -f "$REPO_PATH/.circleci/config.yml" ] && echo "  CircleCI: .circleci/config.yml"
echo ""

# --- 依存管理ファイルの内容（先頭60行） ---
echo "=== 主要な依存管理ファイル ==="
for f in package.json Cargo.toml go.mod pyproject.toml requirements.txt Gemfile pom.xml composer.json; do
  if [ -f "$REPO_PATH/$f" ]; then
    echo "--- $f（先頭60行）---"
    head -60 "$REPO_PATH/$f"
    echo ""
    echo "--- $f ここまで ---"
    echo ""
  fi
done

# --- 拡張子別ファイル数（上位10） ---
echo "=== ファイル分布（上位10拡張子）==="
find "$REPO_PATH" -type f \
  -not -path '*/\.*' \
  -not -path '*/node_modules/*' \
  -not -path '*/__pycache__/*' \
  -not -path '*/target/*' \
  -not -path '*/dist/*' \
  -not -path '*/build/*' \
  -not -path '*/.git/*' \
  | sed 's/.*\.//' | sort | uniq -c | sort -rn | head -10
echo ""

# --- コード量の概算 ---
echo "=== コード量 ==="
TOTAL_FILES=$(find "$REPO_PATH" -type f \
  -not -path '*/\.*' \
  -not -path '*/node_modules/*' \
  -not -path '*/__pycache__/*' \
  -not -path '*/target/*' \
  -not -path '*/dist/*' \
  -not -path '*/build/*' \
  -not -path '*/.git/*' \
  | wc -l)
echo "総ファイル数（生成物・隠しファイル除外）: $TOTAL_FILES"

# 主要なソースコード拡張子ごとの行数
for ext in ts tsx js jsx py rs go rb java kt php ex exs vue svelte; do
  COUNT=$(find "$REPO_PATH" -name "*.$ext" \
    -not -path '*/node_modules/*' \
    -not -path '*/target/*' \
    -not -path '*/dist/*' \
    -not -path '*/.git/*' \
    -exec cat {} + 2>/dev/null | wc -l)
  if [ "$COUNT" -gt 0 ]; then
    echo "  .$ext: $COUNT 行"
  fi
done
echo ""

echo "=== スナップショット完了 ==="
