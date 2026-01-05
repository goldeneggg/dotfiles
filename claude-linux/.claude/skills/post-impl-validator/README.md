# Post-Implementation Validator Skill

実装完了後の検証、具体的にはテスト、lint、ベストプラクティスレビューを自動実行するClaude Code Skill。

## 概要

このSkillは、コード変更後に以下を自動で実行します：

1. **変更ファイルの検出** - gitの差分から変更ファイルを特定
2. **プロジェクト判定** - パスパターンから適用するツールを決定
3. **Lint実行** - エラー時は自動修正を試行（最大3回）
4. **テスト実行** - 失敗時は修正を提案
5. **ベストプラクティスレビュー** - CLAUDE.mdの規約に基づくチェック

## 使用例

### 例1: 実装完了後に自動起動

```
ユーザー: xxxxxの実装が完了しました

Claude: 実装が完了したようです。以下のプロジェクトで変更を検出しました:
        - xxx (Go): 3ファイル

        Post-Implementation Validatorを実行しますか？

ユーザー: はい

Claude: ## Post-Implementation Validator 結果

        ### Lint: PASS
        - エラーなし

        ### テスト: PASS
        - 全 42 テストがパス

        ### ベストプラクティス: PASS
        - テストが書かれている ✓
```

### 例2: 手動でSkillを起動

```
ユーザー: /post-impl-validator

Claude: 変更ファイルを検出しています...

        検出結果:
        - xxx/frontend/ (TypeScript/React): 5ファイル

        ## Post-Implementation Validator 結果

        ### xxx/frontend/

        #### Lint: FAIL (自動修正済み)
        - 修正ファイル: 2件
        - xxx を実行して修正しました

        #### テスト: PASS
        - 全テストがパス

        ### ベストプラクティス: WARNING
        - [ ] プレフィックスが不足: Xxxx.tsx (line 15)
```

### 例3: コミット依頼時に自動起動

```
ユーザー: この変更をコミットして

Claude: コミット前にPost-Implementation Validatorを実行しますか？

        検出された変更:
        - xxx/terraform/ (Terraform): 2ファイル

ユーザー: お願いします

Claude: ## Post-Implementation Validator 結果

        ### Lint: FAIL
        - terraform fmt -check が失敗

        自動修正を試みます...
        - terraform fmt を実行

        ### Lint: PASS (自動修正後)

        ### バリデーション: PASS
        - terraform validate 成功

        ### ベストプラクティス: PASS
        - シークレットのハードコードなし ✓

        レビュー完了。コミットを作成しますか？
```

### 例4: 複数プロジェクトの変更

```
ユーザー: フロントエンドとバックエンドの実装ができた

Claude: 複数プロジェクトの変更を検出しました:
        - xxx (Go): 4ファイル
        - xxx/react (React): 6ファイル

        Post-Implementation Validatorを実行しますか？

ユーザー: はい

Claude: 依存関係順に処理します: Go → React

        ## Post-Implementation Validator 結果

        ### xxx (Go)

        #### Lint: FAIL
        - xxxxx

        自動修正非対応です。以下を手動で修正してください:
        ```go
        // 修正前
        xxx

        // 修正後
        xxx
        ```

        #### テスト: PASS

        ### xxx/react (React)

        #### Lint: PASS
        #### テスト: PASS

        ### 推奨アクション
        1. xxx
        2. 修正後、再度 /post-impl-validator を実行
```

### 例5: エラー時の自動修正ループ

```
ユーザー: /post-impl-validator

Claude: 変更ファイルを検出しています...

        検出結果:
        - xxx/frontend/ (TypeScript/React): 3ファイル

        ## Post-Implementation Validator 結果

        ### xxx/frontend/

        #### Lint: FAIL
        - ESLint エラー: 5件
          - Component.tsx:15 - 'useEffect' の依存配列に 'userId' が不足
          - Component.tsx:28 - 未使用変数 'oldData'
          - utils.ts:42 - any型の使用

        自動修正を試行します... (1/3回目)
        - `npm run lint -- --fix` を実行

        #### Lint: FAIL (一部エラー残存)
        - ESLint エラー: 1件
          - Component.tsx:15 - 'useEffect' の依存配列に 'userId' が不足

        自動修正を試行します... (2/3回目)
        - この問題は自動修正では解決できません

        #### 推奨アクション
        以下を手動で修正してください:

        ```tsx
        // 修正前 (Component.tsx:15)
        useEffect(() => {
          fetchUserData(userId);
        }, []); // userId が依存配列に含まれていない

        // 修正後
        useEffect(() => {
          fetchUserData(userId);
        }, [userId]); // userId を依存配列に追加
        ```

        修正後、再度 `/post-impl-validator` を実行してください。
```

## 自動起動トリガー

以下のキーワードを検知すると、Skill実行を提案します：

- 「実装完了」「完成」「できた」「終わった」「実装した」
- 「コミットして」「PRを作成」「プルリクエスト」

## ファイル構成

```
post-impl-validator/
├── SKILL.md                              # メインSkillファイル
├── README.md                             # このファイル
├── scripts/
│   ├── detect-changes.sh                 # 変更ファイル検出
│   ├── run-tests.sh                      # テスト実行
│   ├── run-lint.sh                       # Lint実行
│   └── auto-fix.sh                       # 自動修正（最大3回リトライ）
└── references/
    ├── go-best-practices.md          # Go規約
    ├── typescript-react-best-practices.md # TypeScript/React規約
    └── terraform-best-practices.md       # Terraform規約
```

## スクリプト使用方法

### detect-changes.sh

```bash
# 変更ファイルを検出してJSON形式で出力
./scripts/detect-changes.sh /path/to/repo
```

### run-lint.sh

```bash
# プロジェクト別にLint実行
./scripts/run-lint.sh go /path/to/repo
./scripts/run-lint.sh react /path/to/repo

# カスタムコマンドを指定して実行
GO_LINT_CMD="golangci-lint run" ./scripts/run-lint.sh go /path/to/repo
TF_LINT_CMD="tflint" ./scripts/run-lint.sh terraform /path/to/repo
```

### run-tests.sh

```bash
# プロジェクト別にテスト実行
./scripts/run-tests.sh go /path/to/repo

# カスタムコマンドを指定して実行
GO_TEST_CMD="make test" ./scripts/run-tests.sh go /path/to/repo
TF_TEST_CMD="terratest" ./scripts/run-tests.sh terraform /path/to/repo
```

### auto-fix.sh

```bash
# 自動修正を試行（最大3回リトライ）
./scripts/auto-fix.sh react /path/to/repo

# カスタムコマンドを指定して実行
GO_FIX_CMD="gofmt -w . && goimports -w ." ./scripts/auto-fix.sh go /path/to/repo
```

## 環境変数によるカスタムコマンド指定

各スクリプトは環境変数でコマンドをカスタマイズできます。

### Go

| 環境変数 | 用途 | デフォルト |
|---------|------|-----------|
| `GO_LINT_CMD` | Lint コマンド | `go vet ./...` |
| `GO_TEST_CMD` | テストコマンド | `go test -shuffle on -race -cover ./...` |
| `GO_TEST_FLAGS` | テストフラグ（`GO_TEST_CMD` 未指定時のみ） | `-shuffle on -race -cover` |
| `GO_FIX_CMD` | 自動修正コマンド | なし（手動修正） |

### TypeScript/React

| 環境変数 | 用途 | デフォルト |
|---------|------|-----------|
| `TS_LINT_CMD` | Lint コマンド | package.json から自動検出 |
| `TS_TEST_CMD` | テストコマンド | package.json から自動検出 |
| `TS_FIX_CMD` | 自動修正コマンド | package.json から自動検出 |

### Terraform

| 環境変数 | 用途 | デフォルト |
|---------|------|-----------|
| `TF_LINT_CMD` | Lint コマンド | `terraform fmt -check -recursive` |
| `TF_TEST_CMD` | テストコマンド | `terraform validate` |
| `TF_FIX_CMD` | 自動修正コマンド | `terraform fmt -recursive` |

## ベストプラクティスチェック内容

### Go

以下の観点でレビューを実施します：

- **命名規則**: エクスポート可否、キャメルケース、インターフェース名
- **エラーハンドリング**: `%w` によるラップ、panic回避、`log.Panicf` の使用
- **コードフォーマット**: gofmt/goimports準拠
- **コメント**: Godoc形式（英語）、複雑なロジックへの説明
- **関数設計**: 単一責任、引数数制限、名前付き戻り値
- **並行処理**: WaitGroup、Mutex、競合検出（`-race`）
- **テスト**: テーブル駆動テスト、`t.Parallel()`、カバレッジ
- **パッケージ構成**: 循環依存回避、internal活用
- **パフォーマンス**: append事前確保、`strings.Builder`
- **セキュリティ**: SQLインジェクション対策、シークレット管理、gosec

詳細は `references/go-best-practices.md` を参照してください。

### TypeScript/React

以下の観点でレビューを実施します：

- **型定義**: any禁止、Props/State型、Union/Literal型
- **コンポーネント設計**: 関数コンポーネント、単一責任、50-100行目安
- **Hooks使用法**: 依存配列、カスタムHooks、React 19新機能
- **状態管理**: ローカル vs グローバル、不変性維持
- **パフォーマンス**: React.memo、key属性、コード分割
- **エラーハンドリング**: Error Boundaries、非同期エラー処理
- **テスト**: Testing Library、ユーザー視点テスト
- **アクセシビリティ**: セマンティックHTML、ARIA、キーボード操作
- **セキュリティ**: XSS対策、dangerouslySetInnerHTML
- **コードスタイル**: PascalCase/camelCase、インポート順序

詳細は `references/typescript-react-best-practices.md` を参照してください。

### Terraform

以下の観点でレビューを実施します：

- **コード構成**: ファイル分割、モジュール構造、環境分離
- **変数管理**: 型指定、バリデーション、sensitive属性
- **状態管理**: リモートバックエンド、暗号化、ロック機構
- **セキュリティ**: シークレット管理、最小権限IAM、tfsec/Checkov
- **プロバイダー管理**: バージョン固定、required_providers
- **モジュール設計**: 粒度、入出力定義、ドキュメント
- **リソース定義**: 命名規則、タグ付け、for_each優先
- **データソース**: 動的データ取得、ハードコード回避
- **出力値**: 必要情報の公開、センシティブ属性
- **CI/CD統合**: plan自動化、承認フロー、ドリフト検出

詳細は `references/terraform-best-practices.md` を参照してください。
