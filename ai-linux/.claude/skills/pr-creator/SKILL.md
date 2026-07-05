---
name: pr-creator
description: |
  現在のブランチからGitHub PRを作成するスキル。PR説明文の生成は pr-description スキルに委譲し、
  タイトル選定・ブランチpush・gh pr createによるPR作成・ラベル/レビュアー設定までを一気通貫で行う。
  ドラフトPR作成にも対応。

  以下の状況で必ず使用すること:
  (1) ユーザーが「PRを作成して」「PR作って」「pull request作って」「PRを出して」と依頼した時
  (2) ユーザーが「このブランチでPR作成して」「PRを開いて」と依頼した時
  (3) ユーザーが明示的に「pr-creator スキル」の実行を指示された時
  (4) ユーザーが「PR作ってpushして」「PRを出しておいて」と依頼した時
  (5) ユーザーが「ドラフトPR作って」「draft PRを出して」と依頼した時
  (6) ユーザーが「PRを作成してレビュアーを設定して」と依頼した時
  (7) ユーザーが「実装が終わったのでPRにしたい」「PRにまとめて」と依頼した時

  別スキルを優先するケース:
  - PR説明文だけ欲しい（PR作成不要） → pr-description
  - PRのレビューをしたい → pr-reviewer
  - 既存PRのCI失敗・レビュー指摘を修正したい → local-autofix-pr
  - コミットだけしたい → commiter
argument-hint: "[--base ブランチ] [--draft] [--reviewer ユーザー] [--label ラベル] [--template テンプレートパス]"
---

# pr-creator

現在のブランチの変更からGitHub PRを作成する。
PR説明文の生成は `pr-description` スキルに委譲し、その出力をPR本文として使用する。

**ユーザーとのやり取りはすべて日本語で行う。**

## スコープの境界

- PR説明文の**生成ロジック**はこのスキルに含まない。`pr-description` スキルを呼び出して委譲する
- PRの**作成**（`gh pr create`）、ブランチの**push**、メタデータ（ラベル・レビュアー）の**設定**がこのスキルの責務
- PR作成後のレビュー・CI修正は対象外（pr-reviewer / local-autofix-pr の領域）

## Degrees of Freedom

- **PR説明文: No freedom** — `pr-description` スキルの出力をそのまま使用する
- **タイトル選定: Low freedom** — `pr-description` が提示するタイトル候補から選択。ユーザーが別案を指定した場合はそれに従う
- **ブランチ操作: Low freedom** — push先・ベースブランチの判断。必ずユーザーに確認
- **メタデータ設定: Medium freedom** — ラベル・レビュアーの提案。引数で指定されたものは必ず設定、追加提案はユーザー確認

## 引数

`pr-creator` スキル（`--base <ブランチ>` `--draft` `--reviewer <ユーザー,...>` `--label <ラベル,...>` `--template <テンプレートパス>` `--format <フォーマット指示>` の各オプション指定可）

- `--base <ブランチ>` (任意): マージ先のベースブランチ。省略時は main → master の順で自動検出
- `--draft` (任意): ドラフトPRとして作成
- `--reviewer <ユーザー,...>` (任意): レビュアーをカンマ区切りで指定
- `--label <ラベル,...>` (任意): ラベルをカンマ区切りで指定
- `--template <パス>` (任意): PR説明文テンプレートのパス（`pr-description` に渡す）
- `--format <指示>` (任意): PR説明文のフォーマット指示（`pr-description` に渡す）

## 実行フロー

### Step 1: 前提条件の確認

以下を順に確認し、一つでも失敗したら作業に入らずユーザーに通知する。

1. **gitリポジトリ内** — `git rev-parse --is-inside-work-tree`
2. **gh CLIで認証済み** — `gh auth status`
3. **現ブランチがmain/masterではない** — main/masterから直接PRを作ろうとしている場合は警告し、ブランチ作成を提案
4. **コミット済みの変更がある** — ベースブランチとの差分が存在すること（`git log <base>..HEAD --oneline` が空でないこと）
5. **同一ブランチの既存PRがない** — `gh pr view --json number,state,url` で確認。既にOpen PRがあれば、そのURLを提示して「既存PRを更新しますか？ 新規PRを作りますか？」と確認

### Step 2: 未コミット変更の確認

`git status --porcelain` で未コミット・未追跡ファイルを確認する。

- **未コミット変更がある場合**: 変更内容を一覧表示し、推奨案を含む複数の選択肢を提示してユーザーに確認:
  - **コミットしてからPR作成**: `commiter` スキルに委譲してコミットし、その後Step 3に進む
  - **現状のコミット済み内容でPR作成**: 未コミット変更は無視してPR作成を進める
  - **中止**: PR作成を取りやめ
- **クリーンな場合**: そのままStep 3に進む

### Step 3: ベースブランチの決定

`--base` 引数が指定されている場合はそれを使用。未指定の場合:

1. リモートに `main` が存在するか確認: `git ls-remote --heads origin main`
2. 存在しなければ `master` を確認: `git ls-remote --heads origin master`
3. どちらもなければユーザーにベースブランチを確認

### Step 4: リモートへのpush

現ブランチがリモートに追跡ブランチを持つか確認し、pushする。

1. `git rev-parse --abbrev-ref --symbolic-full-name @{u}` でリモート追跡ブランチを確認
2. 追跡ブランチが**ない**場合: `git push -u origin <branch>` で初回push
3. 追跡ブランチが**ある**場合: ローカルがリモートより先行しているか確認し、先行分があれば `git push`
4. push失敗時はエラー内容をそのまま報告し、ユーザーに対応を委ねる

### Step 5: PR説明文の生成

`pr-description` スキルを呼び出してPR説明文を生成する。

呼び出し時の引数構成（Skillツールの `args` に渡す文字列）:
```
/tmp/pr-body-<branch-name>.md --base <ベースブランチ> [--template <パス>] [--format <指示>]
```

- 先頭の positional argument（出力先パス）は必須。必ず `/tmp/pr-body-<branch-name>.md` を渡す
- `--base`: Step 3で決定したベースブランチ
- `--template`: 引数で指定されていれば転送
- `--format`: 引数で指定されていれば転送

`pr-description` の出力からPRタイトル候補も得られるので、以降のStep 6で使用する。

**⚠️ フロー継続の注意**: `pr-description` の出力（ファイル生成 + タイトル候補提示）が完了したら、ユーザーの追加入力を待たず、**同一ターン内で即座に Step 6 に進む**こと。`pr-description` の出力はこのスキルの中間成果物であり、ユーザーへの最終報告ではない。

### Step 6: PRタイトルの選定

`pr-description` スキルが提示するPRタイトル候補（Conventional Commits形式・72文字以内）をユーザーに提示し、推奨案を含む複数の選択肢を提示してユーザーに選定してもらう。

選択肢:
- 推奨案（第1候補）
- 第2候補
- 第3候補
- 自由入力（ユーザーが独自のタイトルを指定）

### Step 7: PR作成前の最終確認

以下の情報をまとめて提示し、「作成」「修正」「中止」の選択肢を提示してユーザーに確認する。

```
## PR作成確認

- タイトル: <選択されたタイトル>
- ベースブランチ: <base> ← <head>
- ドラフト: はい / いいえ
- レビュアー: <指定されていれば表示>
- ラベル: <指定されていれば表示>
- 説明文: <pr-descriptionが生成した概要の冒頭数行>
```

「修正」が選択された場合、修正したい箇所をユーザーから受け取り該当Stepに戻る。

### Step 8: PRの作成

`gh pr create` でPRを作成する。

```bash
gh pr create \
  --title "<タイトル>" \
  --body-file /tmp/pr-body-<branch-name>.md \
  --base <ベースブランチ> \
  [--draft] \
  [--reviewer <ユーザー>] \
  [--label <ラベル>]
```

引数の構成:
- `--title`: Step 6で選定したタイトル
- `--body-file`: Step 5で生成したPR説明文ファイル
- `--base`: Step 3で決定したベースブランチ
- `--draft`: `--draft` 引数が指定されている場合のみ付与
- `--reviewer`: `--reviewer` 引数が指定されている場合のみ付与（カンマ区切りの場合は複数回 `--reviewer` を指定）
- `--label`: `--label` 引数が指定されている場合のみ付与

### Step 9: 完了報告

PR作成成功後、以下を報告する。

```
## PR作成完了

**URL**: <PR URL>
**タイトル**: <タイトル>
**ベースブランチ**: <base> ← <head>
**状態**: Open / Draft

### 次のアクション
- CIの実行結果を確認
- レビュアーへの依頼（未設定の場合）
```

一時ファイル `/tmp/pr-body-<branch-name>.md` はPR作成後も残す（ユーザーが参照・再利用できるように）。

## エラーハンドリング

### gh CLI 未認証
`gh auth status` 失敗時は `gh auth login` を案内。

### リモートリポジトリなし
`git remote -v` が空の場合、リモート設定を案内。

### push権限なし
`git push` が `403` や `denied` で失敗した場合、フォークリポジトリの可能性を確認し、ユーザーに対応方法を提示。

### PR作成失敗
`gh pr create` がエラーの場合、エラーメッセージをそのまま報告。よくある原因:
- リポジトリの権限不足 → コラボレータ追加 or フォークPRを案内
- ベースブランチが存在しない → 正しいブランチ名を確認
- 同名PRが既に存在 → 既存PRのURLを提示

### pr-description スキルの呼び出し失敗
PR説明文の生成に失敗した場合、手動でのPR説明文入力へのフォールバックは行わず、エラー内容を報告して原因の解消を促す。

## ガイドライン

- **すべてのやり取りは日本語**（コード・コマンド・タイトルは原語のまま）
- **push前にユーザー確認を省略しない** — 特にmain/masterへの直接pushは追加警告
- **PR説明文の生成は必ず `pr-description` スキルに委譲** — このスキル内で独自にPR説明文を組み立てない
- **一時ファイルのパスは固定パターン** — `/tmp/pr-body-<branch-name>.md` で予測可能にする
- **PRタイトルはConventional Commits形式** — `pr-description` スキルの出力を尊重
- **既存PRの検出を怠らない** — 重複PR作成を防ぐ
