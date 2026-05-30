---
name: gh-action-run-validator
description: |
  GitHub Actionsのworkflow実行ログを取得・分析し、workflowの実装が期待通り動作しているかを検証するスキル。
  実行ログからのエラー原因分析、workflow YAML定義との整合性チェック、改善提案を実施する。

  以下の状況で使用:
  (1) ユーザーが「GitHub Actionsの実行結果を検証して」「ワークフローの実行ログを確認して」と依頼した時
  (2) ユーザーがGitHub Actionsの実行URL（https://github.com/ORG/REPO/actions/runs/RUN_ID）を提示した時
  (3) ユーザーが「CIが失敗した原因を調べて」「ワークフローが期待通り動いているか確認して」と依頼した時
  (4) ユーザーが「actionsのログを分析して」「workflowのrunを検証して」と依頼した時
  (5) ユーザーが明示的に「/gh-action-run-validator」を実行した時
  (6) ユーザーがGitHub Actionsのrun IDやリポジトリ名を提示してworkflowの検証を求めた時
  (7) ユーザーが「デプロイが失敗した」「テストが落ちた」などCI/CDの問題調査を依頼した時
argument-hint: "{URL} or {owner/repo} {run_id}"
context: fork
agent: general-purpose
---

# gh-action-run-validator

GitHub Actionsのworkflow実行ログを取得・分析し、workflow定義との整合性検証、エラー原因分析、改善提案を行います。

**注意: このSkillを使用する際のユーザーとのやり取りはすべて日本語で行います。**

## Degrees of Freedom

- **引数の解析: Low freedom** — 以下の「引数の解析」セクションのパターンに厳密に従う。パターンに合致しない場合は必ずユーザーに確認する
- **ログ分析の深さ: Medium freedom** — 失敗したstepは詳細に分析し、成功したstepは概要のみ。ただしユーザーが特定stepの詳細を求めた場合は掘り下げる
- **改善提案: High freedom** — 検出した問題の性質に応じて、具体的な修正コード・設定変更・ベストプラクティスを自由に提案してよい

## 引数の解析

`$ARGUMENTS` を以下のパターンでパースする:

| パターン | 例 | 解釈 |
|---------|-----|------|
| `https://github.com/{owner}/{repo}/actions/runs/{run_id}` | `https://github.com/myorg/myrepo/actions/runs/12345` | URL形式 |
| `{owner/repo} {run_id}` | `myorg/myrepo 12345` | リポジトリ+RUN ID |
| 引数なし | （空） | ユーザーにURL or owner/repo + run_idを確認 |

**URL解析ルール**: URLからは `owner/repo` と `run_id` を抽出する。URLにクエリパラメータやフラグメントが付いていても正しく抽出すること。

## 前提条件

- `gh` CLI がインストール済みで認証済みであること
- 対象リポジトリへの読み取り権限があること

## 実行フロー

### Phase 1: データ収集

以下の情報を `gh` CLI で取得する。可能な限り並列で実行すること。

#### 1-1. Run概要の取得

```bash
gh run view {run_id} --repo {owner/repo}
```

取得する情報:
- workflow名、ブランチ、トリガーイベント、実行ステータス
- 各jobの名前・ステータス・所要時間

#### 1-2. 各Jobのログ取得

```bash
gh run view {run_id} --repo {owner/repo} --log
```

失敗したjobがある場合は `--log-failed` も活用してエラー箇所を効率的に特定する:

```bash
gh run view {run_id} --repo {owner/repo} --log-failed
```

ログが大量の場合は全量を読み込まず、失敗stepのログを優先的に分析すること。

#### 1-3. Workflow定義ファイルの取得

Runの概要から workflow ファイル名を特定し、リポジトリからYAMLを取得する:

```bash
gh api repos/{owner}/{repo}/actions/runs/{run_id} --jq '.path'
```

取得したパスを使ってファイル内容を取得:

```bash
gh api repos/{owner}/{repo}/contents/{workflow_path} --jq '.content' | base64 -d
```

`--jq '.head_branch'` でブランチを確認し、必要に応じて `?ref={branch}` パラメータを付与する。

### Phase 2: 整合性チェック

Workflow YAML定義と実際の実行結果を照合し、以下を確認する:

1. **Job実行順序の検証**
   - `needs` で定義された依存関係通りにjobが実行されたか
   - 条件付きjob（`if` 条件）が意図通りにスキップ/実行されたか

2. **Step実行の検証**
   - 各stepが定義通りの順序で実行されたか
   - `if` 条件付きstepが期待通りに動作したか
   - `continue-on-error: true` のstepが失敗しても後続が実行されているか

3. **環境・変数の検証**
   - `env` や `secrets` の参照エラーがないか（ログ中の "undefined" や空文字の警告を検出）
   - matrix strategyが期待通りに展開されているか

4. **Artifact/Cache検証**
   - upload/download artifactが正常に動作しているか
   - cacheのhit/miss状況

### Phase 3: エラー原因分析

失敗したstepがある場合、以下の観点で根本原因を特定する:

1. **エラーメッセージの分類**
   - コマンド実行エラー（exit code != 0）
   - 依存関係エラー（パッケージのインストール失敗等）
   - テスト失敗（テストフレームワークの出力をパース）
   - タイムアウト
   - 権限・認証エラー
   - リソース制限（ディスク、メモリ等）

2. **エラーの連鎖分析**
   - 最初に失敗したstep/jobを特定（根本原因と二次的失敗を区別）
   - `needs` 依存による連鎖的なjob失敗を追跡

3. **一時的な問題 vs 永続的な問題の判別**
   - ネットワークエラー、レート制限などの一時的問題か
   - コードや設定の問題で再実行しても解消しない永続的問題か

### Phase 4: レポート出力

以下の構造で検証レポートを出力する:

```
## 検証レポート: {workflow名}

### 実行概要
- **リポジトリ**: {owner/repo}
- **Run ID**: {run_id}
- **ブランチ**: {branch}
- **トリガー**: {event}
- **ステータス**: {status}
- **所要時間**: {duration}

### 実行結果サマリ

| Job | ステータス | 所要時間 | 備考 |
|-----|-----------|---------|------|
| ... | ...       | ...     | ...  |

### 整合性チェック結果
（workflow YAML定義と実行結果の照合結果。問題がなければ「問題なし」と明記）

### エラー分析（失敗時のみ）
#### 根本原因
（最初に失敗したstepとその原因）

#### エラー詳細
（関連するログ抜粋とその解釈）

#### 連鎖的影響
（根本原因から派生した二次的な失敗がある場合）

### 改善提案
（問題の修正方法、workflow最適化の提案。具体的なYAMLコード例を含める）
```

## 注意事項

- ログにsecretやトークンの値が含まれる場合があるため、レポートにそのまま引用しないこと。`***` でマスクされた値はそのまま表示して問題ない
- 大規模なログ（数万行）の場合は、失敗箇所周辺に絞って分析すること。全量読み込みはコンテキストを圧迫する
- `gh` コマンドが認証エラーを返した場合は、ユーザーに `gh auth login` の実行を案内する
