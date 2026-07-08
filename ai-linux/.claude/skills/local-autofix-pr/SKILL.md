---
name: local-autofix-pr
description: |
  PRに紐づくCI失敗（lint/型/テスト失敗）と未解決レビューコメント（suggestion・CHANGES_REQUESTED）をローカルで対話的に修正・コミット・pushする日本語スキル。built-in /autofix-pr と異なりpush前のdiff確認・各ステップの選択肢提示確認・ブロッカー無し時の早期終了が特徴。

  以下の状況で積極的にトリガーすること:
  - "local-autofix-pr スキルを実行して" "local-autofix-pr 実行して"
  - "PRのCI失敗を対話的に直してpush" "checks赤いとこ直してdiff見せて"
  - "lint/型エラー/mypy/eslintの指摘を直してコミット・push"
  - "レビューコメントへの対応コミット、push前にdiff確認"
  - "suggestion/行コメント/unresolved threadに対応してpush前確認"
  - "built-in /autofix-prじゃなくてローカル対話型でCI直して"
  - "/loopと組み合わせてノーオペ早期終了で回したい"

  別スキル優先: PRレビュー→pr-reviewer / PR説明文→pr-description / Actions分析→gh-action-run-validator
argument-hint: "[prompt] [--pr <番号>] [--ci-only] [--reviews-only] [--no-push]"
---

# local-autofix-pr

現在のブランチに紐づくPRに対して、CI失敗ログと未解決レビューコメントを収集し、
それらを解消する修正をローカルで行い、コミット・pushする。

**ユーザーとのやり取りはすべて日本語で行う。**

## スコープの境界

**対象:**
- 現ブランチ（または `--pr` で指定したPR）のCI失敗の解析と修正
- 未解決レビューコメント（行コメント・サマリレビュー）への対応修正
- 修正のコミットとpush（push前にdiff確認を必ず取る）

**対象外:**
- 永続監視（watch）。本スキルは単発実行型。継続的に走らせたい場合は `/loop` スキルとの併用を案内する
- PR本体のレビュー実施（pr-reviewer の領域）
- PR説明文の生成（pr-description の領域）
- PR の merge / close / approve 操作

## Web版との差分（なぜ移植したか）

Web版 `/autofix-pr` は Claude Code on the Web のクラウドエージェントを起動し、
PRをwatchして CI失敗・新着レビューコメントに自動反応する。
本スキルは「クラウドエージェントへ依存しない」ことを目的とした移植版であり、
ローカルClaude Code内で完結させるため以下の方針を取る:

- **watch廃止**: 呼び出された時点で「現在の」CI失敗と未解決レビューコメントを収集して修正
- **push前にdiff確認**: ノンストップ自動pushはせず、必ずユーザーに修正内容を見せて承認を取る
- **修正可否の判断はユーザーに委ねる**: 自動修正不可能な指摘（仕様変更が必要等）は分類して報告

## Degrees of Freedom

- **指摘事項の収集: Low freedom** — gh CLIから機械的に集める。情報源は固定（後述）
- **修正対象の優先度付け: Medium freedom** — Critical/High/Medium/Lowに分類し、修正計画を組む判断はエージェントに委ねる
- **修正アプローチ: High freedom** — 指摘ごとの修正方法は文脈に応じてエージェントが判断する
- **push判断: Low freedom** — 必ずユーザー確認後にpush。`--no-push` 指定時はpushしない

## 引数の解析

`$ARGUMENTS` を以下のパターンでパースする:

| 形式 | 例 | 意味 |
|---|---|---|
| 引数なし | `local-autofix-pr` スキル | 現ブランチPRをデフォルト挙動で修正 |
| 自由文prompt | `local-autofix-pr` スキル（例: 「lintエラーだけ直して」） | 修正対象を絞り込む追加指示 |
| `--pr <番号>` | `local-autofix-pr` スキル --pr 123 | 別のPRを対象にする（要ブランチ切替確認） |
| `--ci-only` | `local-autofix-pr` スキル --ci-only | CI失敗のみ修正、レビューコメントは無視 |
| `--reviews-only` | `local-autofix-pr` スキル --reviews-only | レビューコメントのみ修正、CIは無視 |
| `--no-push` | `local-autofix-pr` スキル --no-push | コミットまでで止め、pushはユーザーに任せる |

複数フラグは併用可能。自由文promptは他フラグと併用可能で「追加指示」として扱う。

## 前提条件

スキル実行の最初に以下を確認する。一つでも満たさなければ作業に入らずユーザーに通知:

1. **gitリポジトリ内である** — `git rev-parse --is-inside-work-tree`
2. **gh CLIで認証済み** — `gh auth status`（失敗時は `gh auth login` を案内）
3. **working treeがクリーン** — `git status --porcelain` が空。dirtyなら以下を確認:
   - 「コミット済みで未pushの変更がある」のか「未コミット変更がある」のか
   - 未コミット変更がある場合は、stash/commit/abortのいずれを取るかユーザーに確認
4. **現ブランチPRが存在する** — `gh pr view --json number,state,headRefName,baseRefName,url`
   - 失敗時: 「現ブランチに紐づくPRが見つかりません」と報告し、`--pr` 指定を促す

## 実行フロー

### Step 1: 引数のパースと前提確認

`$ARGUMENTS` を上記表に従ってパース。前提条件をすべてチェック。

`--pr <番号>` 指定時の追加挙動:
- 指定PRの headRefName を取得
- 現ブランチと異なる場合、選択肢提示で「ブランチを切り替えますか？」を確認
- 切り替える場合は `git fetch origin && git checkout <headRefName> && git pull --ff-only`

### Step 2: PRメタ情報の取得

```bash
gh pr view --json number,state,title,url,headRefName,baseRefName,headRepository,headRepositoryOwner,isDraft,mergeable,reviewDecision
```

stateが `OPEN` 以外（CLOSED / MERGED）の場合は警告し、続行可否をユーザーに確認。

### Step 2.5: 早期終了判定（ブロッカー検査）

**このステップが本スキルの「無駄実行を避ける」ための要。** `/loop` で定期実行されても、対応すべき指摘が無ければここで即座に終了する。

以下のいずれにも該当しない場合は「修正対象なし」として即終了する:

| 判定項目 | 取得方法 | ブロッカー条件 |
|---|---|---|
| 失敗中のCI checks | `gh pr checks --json name,state` | `state` が `FAILURE` / `ERROR` / `TIMED_OUT` / `CANCELLED` のものが1件以上 |
| 実行中のCI checks | `gh pr checks --json name,state` | `state` が `PENDING` / `IN_PROGRESS` / `QUEUED` のものが1件以上（結果未確定のため一旦待つ） |
| レビュー判定 | Step 2の `reviewDecision` | `CHANGES_REQUESTED` |
| 未解決review thread | GraphQL `reviewThreads { isResolved }` | `isResolved == false` のスレッドが1件以上（自分が書いたものは除外） |
| マージ可否 | Step 2の `mergeable` | `CONFLICTING`（コンフリクトは別途報告） |

**判定結果別の挙動:**

1. **すべて該当なし（ブロッカー無し）** → 以下を報告して即終了。Step 3以降は実行しない:
   ```
   ✅ PR #<num> は現時点でブロッカー無し
   - reviewDecision: APPROVED (または REVIEW_REQUIRED で未レビュー)
   - checks: ALL_GREEN
   - 未解決スレッド: 0
   - mergeable: MERGEABLE
   何もせず終了します。
   ```

2. **CI実行中のみ該当（失敗・未解決コメントなし）** → 結果未確定として「待ち」扱いで終了:
   ```
   ⏳ PR #<num> はCI実行中
   - 実行中: <ジョブ名一覧>
   - 失敗中: なし
   - 未解決コメント: なし
   結果が確定するまで何もしません。次回 /loop 周回まで待機を推奨。
   ```

3. **コンフリクトのみ該当** → 自動修正対象外として報告:
   ```
   ⚠️ PR #<num> は base ブランチとコンフリクト
   - mergeable: CONFLICTING
   コンフリクト解消は本スキルの対象外です。手動で rebase / merge してください。
   ```

4. **CI失敗 or レビュー指摘あり** → Step 3に進み通常フローを継続

**ユーザーがprompt引数で「対象を絞り込む指示」を出している場合**:
- 例えば `--ci-only` 指定で「失敗CIが無いがレビューコメントだけある」状態は、絞り込み対象が空なので早期終了扱い
- `--reviews-only` 指定で「未解決コメントが無いがCIだけ落ちている」状態も同様

### Step 3: 指摘事項の収集

`--reviews-only` 指定時はStep 3aをスキップ、`--ci-only` 指定時はStep 3bをスキップ。
それ以外は両方を**並列実行**で収集する。

#### Step 3a: CI失敗の収集

```bash
# 失敗中のchecks一覧
gh pr checks --json name,state,link,description
```

`state` が `FAILURE` / `ERROR` / `TIMED_OUT` / `CANCELLED` のものを抽出。
各失敗チェックについて、GitHub Actions であれば実行ログを取得:

```bash
# linkからrun_idを抽出して
gh run view <run_id> --log-failed
```

ログが巨大（10,000行超）な場合は `--log-failed | tail -200` 等で末尾を中心に読む。
失敗ジョブ名・失敗ステップ・エラーメッセージを抽出して整理する。

#### Step 3b: レビューコメントの収集

```bash
# サマリレビュー（COMMENTED/CHANGES_REQUESTED）
gh pr view --json reviews

# 行コメント（diff上のインラインコメント）
gh api "repos/{owner}/{repo}/pulls/{pr}/comments" --paginate
```

各コメントの**未解決判定**:
- レビューサマリ: `state == CHANGES_REQUESTED` で、その後同レビュアーからのapproveが無いものを未解決とみなす
- 行コメント: GraphQL APIで `isResolved` を取得できる場合はそれを利用。
  - 必要に応じて以下のクエリを使用:
    ```bash
    gh api graphql -f query='
      query($owner:String!,$repo:String!,$pr:Int!){
        repository(owner:$owner,name:$repo){
          pullRequest(number:$pr){
            reviewThreads(first:100){
              nodes{ isResolved comments(first:10){ nodes{ body path line author{login} } } }
            }
          }
        }
      }' -f owner=OWNER -f repo=REPO -F pr=PR
    ```
- 自分（current user）が書いたコメントは原則対象外（自己コメントへの修正は不要）

### Step 4: 指摘事項の整理と優先度付け

収集した指摘を以下の構造でまとめる:

```markdown
## 検出した指摘事項

### 🔴 CI失敗 (N件)
- [ジョブ名] エラー概要（ファイル:行）
  - 失敗ログ抜粋:
    ```
    ...
    ```
  - 推定原因: ...
  - 修正方針案: ...

### 🟠 未解決レビューコメント (M件)
- [@reviewer] path:line
  - 指摘内容: "..."
  - 修正方針案: ...
  - 自動修正可否: ✅ 可 / ⚠️ 要相談 / ❌ 不可
```

優先度の目安:
- 🔴 **Critical**: ビルド/テスト失敗、セキュリティ指摘、CHANGES_REQUESTED
- 🟠 **High**: lint/型エラー、明確なバグ指摘
- 🟡 **Medium**: リファクタ提案、命名・可読性指摘
- 🟢 **Low**: スタイル統一、コメント文言

自動修正不可能な指摘（仕様判断が必要・大規模設計変更等）はその旨を明示する。

prompt引数（自由文）が指定されている場合、その意図に合わせて対象を絞る:
- 例: `lintエラーだけ` → lint/format系の指摘のみ抽出
- 例: `@alice の指摘だけ` → 特定レビュアーのみ抽出
- 例: `securityの観点だけ` → セキュリティ指摘のみ抽出

### Step 5: 修正計画の提示とユーザー確認

整理した指摘事項と修正方針案をユーザーに提示し、推奨案を含む複数の選択肢を提示して以下を確認:

1. すべて修正してよいか / 一部のみか
2. 自動修正不可と判定した指摘の扱い（スキップ・別途相談）

ユーザーが「進めて」と承認したら次へ。

### Step 6: 修正の実行

指摘ごとに修正を実装する。複数ファイル横断の修正でも、関連する論理単位ごとにまとめる。

修正中の原則（CLAUDE.md / 個人ルール準拠）:
- **依頼された内容に集中**: 「ついでに」のリファクタは入れない
- **フォールバックは追加しない**: 指摘が「フォールバック追加」でない限り
- **既存テストがあれば実行**: 修正後に該当テストをローカル実行できる場合、実行自体はサブエージェントに委譲し、メインには合否と失敗時の要点だけを戻させる。単一ファイルの軽微な修正で実行が一瞬で終わる場合は、委譲せずメインで直接実行してよい
- **エラーは具体的に**: エラーハンドリングを追加する場合は、何がなぜ失敗したか明記

### Step 7: diffの提示とpush前確認

```bash
git diff
```

を実行し、修正内容をユーザーに見せる。選択肢提示で以下を確認:

1. このdiffでコミット・pushしてよいか
2. コミットメッセージはこちらで提案してよいか / ユーザーが指定するか

承認後、コミットメッセージを生成（**commit-message-suggester スキルの流儀に準拠したConventional Commits形式**を推奨）。
代表例:

```
fix(ci): resolve lint and type errors flagged by review

- fix unused import in src/foo.ts (review by @alice)
- correct type annotation in src/bar.ts (eslint no-explicit-any)

Refs: #123
```

### Step 8: コミット & push

```bash
git add <修正したファイル>
git commit -m "$(cat <<'EOF'
<メッセージ>
EOF
)"
```

`--no-push` 指定が**ない**場合のみpush:

```bash
git push
```

upstream未設定の場合は `git push -u origin <branch>` で初回push。

### Step 9: 完了報告

```markdown
## ✅ autofix-pr 完了

**PR**: <URL>
**ブランチ**: <branch>
**コミット**: <sha>

### 修正した指摘 (X件)
- ✅ [CI:ジョブ名] 修正概要
- ✅ [@reviewer] path:line 修正概要

### スキップした指摘 (Y件)
- ⚠️ [@reviewer] path:line 理由: 仕様変更が必要なため要相談

### 推奨される次のアクション
- CI再実行を待ち、グリーンになるか確認
- レビュアーへの返信（GitHub上で対応コメント記載を推奨）
- 解決済みコメントの「Resolve conversation」操作
```

watchが必要な場合の案内を末尾に追加:

> 継続的に監視したい場合は `/loop 10m` で `local-autofix-pr` スキルを実行する形で併用可能です。
> 本スキルは Step 2.5 の早期終了判定により「ブロッカー無し」状態では即座にノーオペで終了するため、
> approve済み・マージ可能になった後も安全に回し続けられます（gh API 呼び出しのみで副作用なし）。
> 監視を止めるタイミング（PRマージ後など）はユーザーが判断してください。

## エラーハンドリング

### gh CLI 未認証
`gh auth status` 失敗。`gh auth login` を案内し、必要なら `gh auth refresh -s repo,read:org` を提案。

### 現ブランチPRなし
「現在のブランチ `<branch>` に紐づくOpen PRが見つかりません。`--pr <番号>` で対象PRを指定するか、PRを作成してください」と報告。

### dirty working tree
未コミット変更がある場合は、選択肢提示で「stash / commit / 中断」を確認。
勝手にstashやresetを行わない。

### push権限なし
`git push` が `403` で失敗した場合、フォークPRの可能性を疑い、ユーザーに対応方法（fork側のブランチへの push 権限取得 等）を確認。

### CI失敗ログの取得失敗
`gh run view` がエラーになる場合、GitHub Actions以外のCIプロバイダ（CircleCI等）の可能性あり。
その場合は `gh pr checks` の `link` をユーザーに提示し、ログURLから手動で内容を貼り付けてもらう旨を依頼。

### 修正の影響範囲が大きい
diff が500行を超える等の大規模修正になった場合、Step 7のdiff提示前に「修正が大規模になりました。本当にこのまま進めますか」と再確認する。

### 修正後にローカルテストが失敗
コミット前にローカルテスト失敗を検知した場合、push せず原因調査に切り替え、ユーザーに報告する。

## ガイドライン

- **必ず日本語で対話**（コード・コマンド・コミットメッセージは原語のまま）
- **push前のdiff確認は省略しない** — 自動pushの誘惑を断つ
- **修正不可能な指摘は誠実に報告** — 推測で書き換えない
- **既存のコミットメッセージスタイルを尊重** — `git log --oneline -20` で確認
- **巨大ログは要約して提示** — ユーザーの可読性を優先
- **fork先PRや巨大モノレポ等の特殊状況では一旦止まって確認** — 自動で押し進めない
