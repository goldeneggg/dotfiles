# Verification Patterns

コード変更後の検証パターン（言語非依存）

## コミット前の検証

### 1. テスト実行

以下の場所からテストコマンドを探す:
- `package.json` の "scripts.test"
- `Makefile` の test ターゲット
- `go.mod` があれば `go test`
- `tox.ini` があれば `tox`
- `pytest.ini` または `pyproject.toml`
- `Cargo.toml` があれば `cargo test`

**実行手順**:
1. テストコマンドを実行
2. すべてのテストがPASSすることを確認
3. テストが存在しない場合はユーザーに報告

### 2. Linter実行

以下の設定ファイルから自動検出:
- `.eslintrc*` → `eslint`
- `.golangci.yml` → `golangci-lint`
- `pyproject.toml` → `ruff` or `flake8`
- `.rubocop.yml` → `rubocop`
- `rustfmt.toml` → `cargo fmt`

**実行手順**:
1. Linter設定ファイルを確認
2. Linterを実行
3. 自動修正可能な問題は修正
4. 残った問題をユーザーに報告

### 3. 差分レビュー

`git diff` で以下を確認:
- 意図しない変更がないか
- デバッグコードの混入（console.log、debugger、print等）
- コメントアウトされたコード
- TODO/FIXMEコメント（新規追加の場合は担当者・期限を記載）
- シークレット情報の混入（APIキー、トークン等）

## テスト成功の判定基準

### 終了コード
- 0であること
- 非ゼロの場合は失敗

### 出力チェック
- "FAIL" が含まれない
- "Error" が含まれない（テスト内の期待エラーメッセージを除く）
- "✓" や "PASS" が期待される数だけある

### カバレッジ
- カバレッジが測定されている場合、低下していないこと
- 新規コードに対してテストが追加されていること

## Linter成功の判定基準

### 警告レベル
- Error: 必ず修正
- Warning: 可能な限り修正（自動修正できない場合はユーザーに確認）
- Info: 必要に応じて修正

### 自動修正
以下のツールは自動修正をサポート:
- `eslint --fix`
- `prettier --write`
- `black` (Python)
- `gofmt -w` (Go)
- `rubocop -a` (Ruby)
- `cargo fmt` (Rust)

## よくある失敗パターン

### テストの誤判定
❌ 「一部のテストがスキップされたが全体はPASS」→ 実際は未検証
✅ スキップされたテストがある場合はユーザーに報告

### Linterの過信
❌ 「Linterがエラーなし」→ ロジックの正しさは保証されない
✅ Linterはスタイル・構文チェックのみ、ロジックは別途レビュー

### 差分の見落とし
❌ 「git diff が大量すぎて確認できず」→ 不要な変更が混入
✅ 差分が大きい場合はファイル単位で確認、または分割コミット推奨

## 言語別の特記事項

### Go
- `go test -v ./...` で全パッケージテスト
- `golangci-lint run` でlint
- `go mod tidy` で依存関係整理

### TypeScript/JavaScript
- `npm test` または `yarn test`
- `eslint` + `prettier` の組み合わせが一般的
- `tsc --noEmit` で型チェック

### Python
- `pytest` が標準的
- `ruff` (高速) または `flake8` + `black`
- `mypy` で型チェック（型ヒントがある場合）

### Shell Script
- `shellcheck` で構文・ベストプラクティスチェック
- `shfmt` でフォーマット
- `bats` でテスト（存在する場合）

### Rust
- `cargo test` でテスト
- `cargo clippy` でlint
- `cargo fmt` でフォーマット
