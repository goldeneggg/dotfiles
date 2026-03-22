# トリガーテストスイート

terraform-validation-enhancer スキルのトリガー判定を検証するためのテストケース集。

## ポジティブ（発動すべき）

| # | 入力例 | 期待動作 |
|---|--------|---------|
| P1 | "Terraformのバリデーションを見直して" | スキル発動 → ステップ0から開始 |
| P2 | "validation blockを追加して" | スキル発動 |
| P3 | "このTerraform構成のセキュリティをチェックして" | スキル発動 |
| P4 | "lifecycleの設定を確認して" | スキル発動（Terraform構成が存在する場合） |
| P5 | "precondition/postconditionを追加すべき箇所を教えて" | スキル発動 |
| P6 | "本番DBにprevent_destroyが設定されているか確認して" | スキル発動 |
| P7 | "/terraform-validation-enhancer ./infra" | スキル発動 → $ARGUMENTS=./infra |
| P8 | "/terraform-validation-enhancer" | スキル発動 → ステップ0でディレクトリ確認 |

## ネガティブ（発動すべきでない）

| # | 入力例 | 理由 |
|---|--------|------|
| N1 | "Terraformのインストール方法を教えて" | 一般的な質問であってバリデーション強化ではない |
| N2 | "terraform planの結果を見て" | plan結果の読解であって構成の評価ではない |
| N3 | "Terraformのモジュールを作って" | モジュール作成は別タスク |
| N4 | "tflintのルールを設定して" | 別ツールの設定 |
| N5 | "Terraform Cloudの設定を教えて" | プラットフォーム設定であって構成バリデーションではない |
| N6 | "Ansibleのバリデーションを確認して" | Terraform以外のツール |

## エッジケース（判断が分かれるケース）

| # | 入力例 | 推奨判定 | 理由 |
|---|--------|---------|------|
| E1 | "Terraformの変数にバリデーションが必要？" | 発動してよい | 教育的な文脈でもバリデーション知識を提供できる |
| E2 | "HCLのベストプラクティスを教えて" | 発動すべきでない | Terraform限定でなくHCL全般の質問 |
| E3 | "terraform validateがエラーになった" | 発動すべきでない | 既存エラーのデバッグであってバリデーション強化ではない |
| E4 | "Terraformのリソースを安全に削除したい" | 発動してよい | lifecycle/prevent_destroyの知識が関連する |
