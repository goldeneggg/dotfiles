---
name: terraform-validation-enhancer
description: |
  Terraform構成の依存関係管理とバリデーションを評価・強化するスキル。
  Terraform 1.14以上を対象に、variable validation、depends_on/lifecycle、precondition/postcondition、check blockの現状評価と改善提案を実施。
  以下の状況で使用:
  (1) ユーザーが「Terraformのバリデーションを見直して」「validation blockを追加して」と依頼した時
  (2) ユーザーが「このTerraform構成のセキュリティをチェックして」「lifecycleの設定を確認して」と依頼した時
  (3) ユーザーが「precondition/postconditionを追加すべき箇所を教えて」「check blockを追加して」と依頼した時
  (4) ユーザーが「Terraform構成をレビューしてバリデーション不足を検出して」と依頼した時
  (5) ユーザーが「本番DBにprevent_destroyが設定されているか確認して」のようにTerraformのライフサイクル管理を依頼した時
  (6) ユーザーが明示的に「/terraform-validation-enhancer」を実行した時
  (7) Terraform構成の新規作成・リファクタリング時にバリデーション強化が求められた時
argument-hint: "<terraform_directory>"
disable-model-invocation: true
---

# Terraform Validation Enhancer

Terraform構成の依存関係管理とバリデーションを体系的に評価・強化します。

## 対象バージョン

- **Terraform**: 1.14以上
- **Python**: 3.7以上（分析スクリプト用）

## 概要

このスキルはTerraform構成に対して以下を実施:

1. **現状評価**: variable validation、depends_on、lifecycle、precondition/postcondition、check blockの使用状況を分析
2. **問題検出**: 不足しているバリデーションや不適切な依存関係設定を特定
3. **修正提案**: 具体的な改善コードと実装ガイダンスを提供
4. **ベストプラクティス適用**: Terraformの機能を活用した推奨パターンを提案

## スキル境界

**対象:**
- Terraform HCL構成ファイル（.tf）のバリデーション・依存関係・ライフサイクル設定の評価と改善

**対象外:**
- tflint / Sentinel によるポリシーチェック（別ツールの責務）
- Terraform Cloud / Enterprise の設定・ワークスペース管理
- Terraformモジュールの新規設計・作成
- `terraform plan` 結果の読解・デバッグ（エラー解決は一般的なTerraform知識で対応）

## Degrees of Freedom

- **分析・検出: Low freedom** — analyze_terraform.pyの出力とパターン集に基づいて機械的に評価する
- **修正提案の内容: Medium freedom** — プロジェクト固有の要件（環境構成、命名規則、チームポリシー等）に応じて適用パターンと優先度を判断する
- **修正の実施: High freedom** — ユーザーの承認を得た上で、対象コードの文脈に合わせた具体的なHCLコードを実装する

## ワークフロー

### ステップ0: 対象ディレクトリの特定

1. `$ARGUMENTS` が指定されている場合はそれを対象ディレクトリとして使用
2. 未指定の場合、カレントディレクトリに `.tf` ファイルが存在するか確認
3. `.tf` ファイルが見つからない場合、AskUserQuestionツールで対象ディレクトリをユーザーに確認

### ステップ1: 構成の分析

analyze_terraform.pyスクリプトを使用してTerraform構成を分析します。

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/analyze_terraform.py $ARGUMENTS
```

このスクリプトは以下をJSON形式で出力:

- バリデーションが不足している変数
- lifecycleブロックが推奨されるリソース
- precondition/postconditionが有用なリソース
- check blockの追加候補

### ステップ2: 評価結果の確認

分析結果を確認し、以下の観点で優先度を判断:

1. **Critical (警告)**: セキュリティやデータ保護に関わる問題
   - センシティブな変数に`sensitive = true`が未設定
   - 本番DBリソースに`prevent_destroy`が未設定

2. **Important (推奨)**: 可用性や運用品質に関わる問題
   - 重要な変数にvalidationブロックが未設定
   - ダウンタイムリスクのあるリソースに`create_before_destroy`が未設定

3. **Nice to have (提案)**: コード品質向上に寄与
   - data sourceへのprecondition追加
   - check blockによる実行時検証

### ステップ3: 修正の実施

優先度に基づいて修正を実施します。具体的なBefore/Afterパターンは以下を参照:

- **Variable Validation** → `${CLAUDE_SKILL_DIR}/references/validation-patterns.md#variable-validation-patterns`
- **Lifecycle Block** → `${CLAUDE_SKILL_DIR}/references/validation-patterns.md#lifecycle-management`
- **Precondition/Postcondition** → `${CLAUDE_SKILL_DIR}/references/validation-patterns.md#preconditions-and-postconditions`
- **Check Block** → `${CLAUDE_SKILL_DIR}/references/validation-patterns.md#check-blocks`
- **Resource Dependencies** → `${CLAUDE_SKILL_DIR}/references/validation-patterns.md#resource-dependencies-depends_on`

### ステップ4: 検証

修正後、以下を実行して構成の妥当性を確認:

```bash
# 構成の検証
terraform init
terraform validate

# planで変更内容を確認
terraform plan

# 再度分析スクリプトを実行して改善を確認
python3 ${CLAUDE_SKILL_DIR}/scripts/analyze_terraform.py $ARGUMENTS
```

### ステップ5: 報告

分析・修正結果を以下のフォーマットでユーザーに報告:

```markdown
## 分析結果サマリー

- **対象**: [ディレクトリパス] ([N]ファイル)
- **検出数**: Critical [X]件 / Important [X]件 / Nice to have [X]件

## 実施した修正

| ファイル | カテゴリ | 修正内容 |
|---------|---------|---------|
| variables.tf | validation | variable 'xxx' にvalidation blockを追加 |
| main.tf | lifecycle | aws_db_instance に prevent_destroy を追加 |

## 未対応項目

- [項目と未対応の理由（チーム合意が必要、影響範囲が大きい等）]

## 再分析結果

- 修正前: [X]件 → 修正後: [Y]件（[Z]件改善）
```

## 評価観点の詳細

### Variable Validation

- 全ての公開変数に適切なvalidationが設定されているか
- センシティブな変数に`sensitive = true`が設定されているか
- error_messageが具体的で理解しやすいか

**詳細**: `${CLAUDE_SKILL_DIR}/references/validation-patterns.md#variable-validation-patterns`

### Resource Dependencies

- `depends_on`は本当に必要か（暗黙的依存で十分でないか）
- モジュール間の依存関係が明確に表現されているか
- 循環依存が発生していないか

**詳細**: `${CLAUDE_SKILL_DIR}/references/validation-patterns.md#resource-dependencies-depends_on`

### Lifecycle Management

- 本番環境リソースに`prevent_destroy`が設定されているか
- ダウンタイムを避けるため`create_before_destroy`が適切に使用されているか
- `ignore_changes`の使用が正当化されているか

**詳細**: `${CLAUDE_SKILL_DIR}/references/validation-patterns.md#lifecycle-management`

### Preconditions and Postconditions

- 重要なdata sourceにpreconditionが設定されているか
- リソース作成の前提条件がpreconditionで検証されているか
- リソースの重要な属性がpostconditionで検証されているか

**詳細**: `${CLAUDE_SKILL_DIR}/references/validation-patterns.md#preconditions-and-postconditions`

### Check Blocks

- インフラの稼働状態を検証するcheck blockが存在するか
- セキュリティ要件を検証するcheck blockが存在するか
- 環境別の要件がcheck blockで検証されているか

**詳細**: `${CLAUDE_SKILL_DIR}/references/validation-patterns.md#check-blocks`

## リファレンス

| ファイル | 参照頻度 | 用途 |
|---------|---------|------|
| `${CLAUDE_SKILL_DIR}/references/validation-patterns.md` | **毎回参照** | ステップ3の修正パターン。Before/Afterコード例を含む |
| `${CLAUDE_SKILL_DIR}/references/terraform-v1.14-docs.md` | **必要時のみ** | 構文やオプションの詳細確認時。セクション名でgrepして該当部分のみ読み込むこと |
| `${CLAUDE_SKILL_DIR}/references/trigger-test-suite.md` | **開発時のみ** | トリガー判定の検証用。通常のスキル実行では参照不要 |

## スクリプト

### analyze_terraform.py

Terraform構成ファイルを解析し、改善点を特定します。

**使用方法**:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/analyze_terraform.py $ARGUMENTS
```

**出力例**:

```json
{
  "summary": {
    "total_files": 5,
    "total_issues": 12,
    "by_severity": {
      "warning": 3,
      "suggestion": 6,
      "info": 3
    },
    "by_category": {
      "validation": 4,
      "lifecycle": 3,
      "condition": 3,
      "check": 2
    }
  },
  "issues": [
    {
      "file": "variables.tf",
      "line": 10,
      "severity": "warning",
      "category": "validation",
      "message": "Variable 'instance_count' lacks validation block",
      "suggestion": "Consider adding validation block to ensure input correctness"
    }
  ]
}
```

## 使用上の注意

1. **Terraform バージョン**: 「対象バージョン」セクションを参照
2. **段階的適用**: 一度に全ての修正を適用せず、優先度に基づいて段階的に実施してください
3. **テスト**: 修正後は必ず`terraform plan`で影響を確認してください
4. **チーム合意**: 大規模な変更はチームで合意を得てから実施してください

## トラブルシューティング

### analyze_terraform.py実行時のエラー

- **権限エラー**: スクリプトに実行権限を付与 (`chmod +x ${CLAUDE_SKILL_DIR}/scripts/analyze_terraform.py`)
- **Python バージョン**: Python 3.7以上が必要

### 誤検知への対処

スクリプトの検出は推奨事項です。プロジェクト固有の理由で適用しない判断も有効です。その場合は:

1. 理由をコメントで文書化
2. チーム内で合意を記録
3. 将来のレビューで再評価

## 関連ドキュメント

- [Terraform Language Documentation](https://developer.hashicorp.com/terraform/language)
- [Terraform Best Practices](https://www.terraform-best-practices.com/)
- トリガーテストスイート: `${CLAUDE_SKILL_DIR}/references/trigger-test-suite.md`
