---
name: task-artifact-fixer
description: |
  task-starter のタスク要件を基準に、PRレビューコメントの妥当性検証と必要な修正、またはPRに紐づくCI失敗の原因調査と必要な修正を行う。タスクファイルとレビューコメントURL・GitHub Actions失敗URLを指定して、指摘が正しいか確認してから最小修正したい時、CI失敗がPR変更による回帰か外部要因かを切り分けて直したい時、task-artifact-reviewer後の指摘対応を依頼された時に使用する。一般的なタスク実装はtask-performer、修正を伴わない成果物レビューはtask-artifact-reviewer、タスク要件を伴わないCI修正はgh-action-error-fixerを優先する。
---

# Task Artifact Fixer

タスク要件を判断基準として外部指摘の正しさを検証し、根拠が確認できた問題だけを修正・検証する。

## 呼び出し

```text
$task-artifact-fixer <対象タスクファイルパス> <PRレビューコメントURL or PRのCI失敗URL> [--commit | --commit-push | --commit-push-reply] [--request-review] [--no-agent]
```

2つの位置引数を必須とし、順序を固定する。

- `<対象タスクファイルパス>`: task-starter 形式の `todos/NNN-{task}/README.md`、または独立したタスクMarkdown
- `<PRレビューコメントURL>`: PR上の `discussion_r...`、`issuecomment-...`、`pullrequestreview-...` のいずれかを含むURL
- `<PRのCI失敗URL>`: GitHub Actions の run/job URL、または失敗checkを一意に特定できるPR checks URL

PRトップURLだけでコメントまたは失敗checkを一意に特定できない場合は、候補を提示してユーザーに選択を求める。URLと現在のリポジトリが異なる場合は、対象を推測せず確認する。

### オプション

- `--commit`: 最終レビュー承認後、変更ファイルをステージし、コミットログファイルを出力して `git commit -F` を実行する。task-performer の `--commit` と同じ挙動にする。
- `--commit-push`: `--commit` を暗黙に有効化し、コミット成功後に対象PRのheadブランチへ通常の `git push` を実行する。force pushは行わない。
- `--commit-push-reply`: レビューコメントURL専用。`--commit-push` を暗黙に有効化し、push成功後に検証結果と修正・検証内容をコメント投稿する。`discussion_r<ID>` のURLは、対象が返信ならその `in_reply_to`、それ以外なら `ID` をスレッド先頭コメントIDとして `in_reply_to` に渡し、同じレビューthreadへ返信する。`issuecomment-<ID>` と `pullrequestreview-<ID>` のURLはPRへ次の新規コメントを投稿する。

  ```text
  > {レビューコメントURL}

  {返信コメント}
  ```

- `--request-review`: `--commit-push-reply` との併用時だけ有効。返信投稿成功後、元コメントのユーザーがbotではなく、当該PRの既存review（`GET /pulls/{PR}/reviews`）のauthor集合に含まれる場合だけ、そのユーザーをreview requestする。
- `--no-agent`: task-starter 関連ドキュメントの読み込みだけをメインスレッド内で行う。調査・テスト等の他工程の委譲方針は変えない。

`--commit-push-reply` と他のcommit系オプションが併記された場合は `--commit-push-reply` として扱う。`--commit-push-reply` をCI失敗URLと併用した場合、および `--request-review` を `--commit-push-reply` なしで指定した場合は、外部操作を行わず入力エラーとして扱う。オプションなしの場合は、最終レビュー承認後に対象ファイルのステージングとコミットログファイルの出力まで行い、commit・push・返信・review requestは行わない。

## スコープ

### 含むもの

- タスク本文・仕様・進捗正本を基準にしたレビューコメントの妥当性検証
- PR差分・失敗ログ・対象コードを根拠にしたCI失敗の原因特定
- 妥当と判定した問題への最小修正、回帰テスト、Lint・型チェック
- task-starter 形式での `PROGRESS.md` と進捗一覧への結果反映
- オプションに応じたコミット・push
- `--commit-push-reply` によるレビューthread返信または引用付きPRコメント
- `--request-review` 指定時の、条件を満たすコメント投稿者へのreview request

### 含まないもの

- PR全体の新規レビュー（task-artifact-reviewer または pr-reviewer を使う）
- 指定URL以外のレビュー指摘・CI失敗の便乗修正
- conversationのresolve、workflowの再実行
- PR説明の更新、approve、merge、close、rebase、force push
- タスク要件外のリファクタリングやフォールバック追加

## 実行原則

1. **外部指摘を事実として扱わない。** コメントや失敗ログを調査開始点とし、タスク要件・PR差分・現在コード・再現結果で独立検証する。
2. **根本原因へ直接対応する。** 症状を隠すskip、retry、条件緩和、エラー握り潰しを、要件なしに追加しない。
3. **変更を指定対象へ限定する。** 別の問題は「気づきメモ」として報告し、その場で修正しない。
4. **ユーザー変更を保持する。** dirty working treeを確認し、重なる未コミット変更がある場合は編集前に相談する。stash・reset・checkoutを無断実行しない。
5. **証跡と正本を分離する。** 生ログは `logs/{task-id}/`、状態と要約は `PROGRESS.md` に置き、TODO本文は変更しない。

## Degrees of Freedom

- **対象URLの解決: Low freedom** — URLから特定できたコメントまたはcheckだけを扱う。曖昧なら確認する。
- **指摘の判定: Medium freedom** — 指定の分類と必要な反証確認を行い、根拠を明示する。
- **修正方法: High freedom** — タスク要件と既存実装に合う最小の方法を選ぶ。
- **編集開始: Low freedom** — 判定結果と修正計画を提示し、ユーザー承認後に編集する。
- **重いテスト: Low freedom** — DB・コンテナ・外部サービスを使うテストは無断実行しない。
- **commit・push: Low freedom** — 指定オプションと最終レビュー承認の両方がある場合だけ実行する。
- **返信: Low freedom** — `--commit-push-reply`、最終レビュー承認、commitとpushの成功がすべて揃う場合だけ、指定コメントだけへ投稿する。
- **review request: Low freedom** — `--request-review`、最終レビュー承認、commit・push・返信投稿の成功がすべて揃う場合だけ、条件を満たす元コメント投稿者へ依頼する。

## ワークフロー

### Phase 1: 入力と作業状態を確定する

1. 最初に `../_shared/references/task-management-contract.md` を読み、以降のタスク文書更新へ適用する。
2. 引数からタスクファイル、対象URL、5オプションを解析する。不足・不明・競合があれば推測せず確認する。`--commit-push-reply` ではレビューコメントURLであること、`--request-review` が指定される場合は `--commit-push-reply` も指定されることを確認する。
3. `git rev-parse --show-toplevel`、`git status --short --branch`、`gh auth status` を確認する。
4. URLから `owner/repo`、PR番号、対象ID（comment / review / run / job / check）を抽出する。
5. `gh pr view` でPRのstate、head/baseブランチ、head SHA、head repositoryを取得し、ローカルのbranch・HEAD・remoteと照合する。`--request-review` 指定時は既存reviewのauthor集合も取得し、元コメント投稿者がこの集合に含まれるかだけを判定する。
6. ローカルがPR headと一致しない場合は編集せず、安全な切替・更新方法を提示してユーザーに確認する。
7. PRが `CLOSED` または `MERGED` の場合は既定で読み取り専用の検証に留める。別ブランチでの追補修正を求められた場合だけ、対象ブランチとスコープを確認して続行する。

### Phase 2: タスクコンテキストを取得する

タスクファイルが `todos/NNN-{task}/README.md` 形式なら、次の方式を選ぶ。

- **既定**: `task-reader` エージェントへ `タスクファイルパス: {task_path}` を渡す。`--with-log` は付けず、返されたタスク本文全文、specs、references、ロードマップ、進捗一覧、個別 `PROGRESS.md`、留意事項を使用する。
- **`--no-agent`**: タスクファイルから `todos/` の親をproject rootとして特定し、タスク本文、project README、`todos/README.md`、`specs/**/*.md`、`references/**/*.md`、`progresses/README.md`、該当 `PROGRESS.md` をメインスレッドで読む。500行超の補助文書は内容検索後に250行以下へ分割するが、タスク本文は全文を保持する。

独立したタスクMarkdownは直接全文を読む。いずれの場合も、受け入れ条件、作業項目、明示された非機能要件、スコープ外事項、既存の検証状態を抽出する。

### Phase 3: 対象の一次証拠を収集する

#### レビューコメントモード

1. URLアンカーに応じてコメント本文とメタデータを取得する。
   - `discussion_r<ID>`: `gh api repos/{owner}/{repo}/pulls/comments/{ID}`
   - `issuecomment-<ID>`: `gh api repos/{owner}/{repo}/issues/comments/{ID}`
   - `pullrequestreview-<ID>`: `gh api repos/{owner}/{repo}/pulls/{PR}/reviews/{ID}`
2. コメントのauthor login/type、作成時刻、対象path/line、commit ID、in_reply_to、outdated/resolved相当の状態を保持する。bot判定にはAPIの `user.type == "Bot"` とlogin末尾の `[bot]` の両方を使う。
3. 同じthreadの前後コメント、PR差分、コメント対象ファイルのPR head版とローカル版を読む。
4. サマリコメントの場合は、本文中の各主張を列挙するが、指定コメント外のthreadへ対象を広げない。

#### CI失敗モード

1. PR checks URLなら `gh pr checks` から失敗checkと実行URLを解決する。run URLならjob一覧、job URLなら対象jobを取得する。
2. 失敗jobが複数ある場合は独立原因か連鎖失敗かを切り分け、先行する根本原因を優先する。
3. GitHub Actionsログを次の順で調べる。
   - エラー語、失敗テスト名、例外名の前後を抽出する。
   - ログ末尾で終了コード、失敗件数、timeout、OOM、cancelを確認する。
   - 情報が一致しない、または原因チェーンが不足する場合だけ完全な失敗ログを段階的に読む。
4. matrix jobでは全環境共通か、OS・ランタイム版固有かを比較する。
5. GitHub Actions以外のcheckでログを取得できない場合は、提供元URLと不足情報を報告し、ログ提供を依頼する。推測で編集しない。

巨大ログを一度に会話へ展開しない。一時保存が必要ならセッション固有の一時ディレクトリを使い、必要行だけ読み、永続化する証跡だけを `logs/{task-id}/` へ置く。

### Phase 4: 妥当性と根本原因を判定する

#### レビューコメントの分類

コメントの各主張を、次のいずれかへ分類する。

- **妥当**: タスク要件または既存契約に反し、現在のPR headでも問題が再現する。
- **部分的に妥当**: 問題はあるが、提案された範囲・修正方法の一部が過剰または要件外である。
- **対応済み・outdated**: 後続commitで問題が解消されている。
- **不当**: コメントの前提がコード・仕様・テスト事実と一致しない。
- **仕様判断が必要**: 複数の解釈が成立し、タスク文書だけでは決められない。

判定前に、コメントが要求する期待動作を一文で言い換え、対象コードと呼び出し元、関連テスト、タスクの受け入れ条件を突き合わせる。提案コードはそのまま採用せず、反証となるケースも確認する。

#### CI失敗の分類

失敗を次のいずれかへ分類する。

- **PR変更による回帰**
- **リポジトリ内のworkflow・依存・設定不備**
- **flaky・並列干渉**
- **runner・権限・secret・外部サービス等の環境要因**
- **PRと無関係な既存障害**
- **原因未確定**

ログ、PR差分、対象コード、同一checkの他matrix結果で因果関係を説明する。再実行だけで消えそうという理由でflakyと断定しない。リポジトリ内修正で解決でき、かつタスクスコープ内の場合だけ編集対象とする。

#### 判定後の分岐

- `妥当`、`部分的に妥当`、`PR変更による回帰`、`リポジトリ内の不備`: 根拠と最小修正計画を提示し、ユーザー承認を得てPhase 5へ進む。
- `対応済み・outdated`、`不当`、環境要因、無関係な既存障害: コードを変更せず、根拠と推奨アクションを報告する。
- `仕様判断が必要`、`原因未確定`: 不足情報と推奨案を示してユーザーに確認する。推測で修正しない。

修正計画には変更対象、変更理由、追加・更新するテスト、実行する検証、影響する `AC-ID`、スコープ外の発見を含める。

### Phase 5: 最小修正を実装する

1. 承認後、task-starter形式では `PROGRESS.md` を `進行中` にし、最終更新を更新して進捗一覧を同期する。既に `進行中` なら不要な書き換えをしない。
2. 編集対象ファイルを直前に読み直す。
3. 原因へ直接対応する最小差分を実装する。本番コードを変更する場合は、問題を再現して修正後に通る回帰テストを可能な範囲で追加する。
4. 自動生成物は所定の生成コマンドで更新し、直接編集しない。
5. 指定対象と無関係な発見は変更せず、結果報告の気づきメモへ残す。

### Phase 6: 修正を検証する

1. 指摘またはCI失敗を再現する最小のテストを最初に実行する。
2. 変更対象に近い軽量テスト、リポジトリ所定のLint・型チェック・format check、`git diff --check` を実行する。
3. CI固有条件をローカルで完全再現できない場合は、ローカルで確認できた範囲と未検証条件を分離する。
4. DB、コンテナ、外部API等を使う重いテストは既定でskipし、ローカル実行が必要なら事前にユーザー承認を得る。
5. 失敗した検証はエラーメッセージを正確に読み、原因特定後に修正して再実行する。3回修正しても解決しない場合は続行判断を求める。
6. `git diff` と `git status --short` で依頼外変更の混入とユーザー変更との重複がないことを確認する。

### Phase 7: タスク進捗と作業結果をレビューする

task-starter形式では、影響する全 `AC-ID` を修正後の証跡で再評価する。他の `AC-ID` は既存根拠を無断で置き換えない。今回の問題により既存の充足判定が崩れた場合は `未充足` に戻す。

- 全 `AC-ID` が `充足` で、ユーザーが作業結果を承認した場合だけ `完了` とする。
- 未確認・未充足が残る場合は `進行中` または `ブロック中` とし、残作業・ブロッカーを具体化する。
- 状態または最終更新を変えたら `sync_progress_index.py` で一覧を同期し、不一致を残さない。
- 生ログは `logs/{task-id}/`、要約と相対証跡パスは `PROGRESS.md` の成果へ記録する。

次の形式で結論から報告し、コード変更がある場合は最終承認を求める。

```markdown
## 判定
- 対象: {コメント / check名}
- 分類: {分類}
- 根拠: {タスク要件・コード・ログ・テストの対応}

## 修正内容
- `{path}`: {最小修正の概要}

## 検証結果
- 対象テスト: `{command}` → {PASS/FAIL}
- Lint・型・format: `{command}` → {PASS/FAIL/SKIP}
- 重いテスト・CI固有条件: {SKIPまたは結果と理由}

## 受け入れ条件
- `AC-01`: {充足/未充足/未確認} — {根拠}

## 気づきメモ
- {スコープ外の発見、または「なし」}

## 外部操作
- PRコメント返信・review request・resolve・workflow再実行: 未実施
```

コード変更がない判定ではcommit・pushを行わず、調査結果だけを報告して終了する。

### Phase 8: ステージング・commit・pushを行う

Phase 7 の最終承認後、コード変更がある場合だけ次を実行する。

1. `.git/hooks/pre-commit` と `.githooks/pre-commit` を確認する。存在する場合は内容を読み、定義されたformat・Lint等を `git add` 前に直接実行して成功させる。
2. 今回変更したコード・テスト・設定だけを `git add` する。`todos/`、`progresses/`、`logs/` のタスク管理ファイルはステージしない。
3. task-starter形式なら `logs/{task-id}/commit-{YYYYmmddHHMMSS}-{title}.txt` に、それ以外はユーザーが承認した場所に、Conventional Commits形式・各行72文字以内のコミットログを出力する。メッセージへタスクパス、タスクID、ローカルログパスを含めない。
4. オプションに従う。
   - オプションなし: ステージングとログ出力で終了する。
   - `--commit`: `git commit -F {log_path}` を実行し、commit SHAを報告する。
   - `--commit-push`: commit成功後、URLから確認したPR head repository・branchとpush先が一致することを再確認し、通常の `git push` を実行する。upstream未設定時だけ `git push -u {remote} {branch}` を使う。
   - `--commit-push-reply`: `--commit-push` の全手順を実行する。push成功後、Phase 7の判定・修正・検証結果だけに基づく簡潔な返信本文を作成する。`discussion_r<ID>` なら、対象コメントが返信の場合は `in_reply_to`、それ以外は `ID` をスレッド先頭コメントIDとして `gh api repos/{owner}/{repo}/pulls/{PR}/comments -f body={reply} -F in_reply_to={thread_root_id}` で同じthreadへ投稿する。それ以外なら `gh pr comment {PR} --body {quoted_reply}` で引用付き新規コメントを投稿する。
   - `--request-review`: `--commit-push-reply` による返信投稿の成功後に限り、元コメント投稿者がbotでなく、Phase 1で取得した既存reviewのauthor集合に含まれる場合は `gh pr edit {PR} --add-reviewer {login}` でreview requestする。ユーザーが集合に含まれない場合とbotの場合はrequestを行わず、その理由を報告する。
5. pushまたは返信投稿が失敗した場合は、その時点で後続の外部操作を行わず正確なエラーを報告する。review requestだけが失敗した場合は、返信済みであることとエラーを分けて報告する。force push、別remoteへのpush、認証変更で回避しない。

## エラーハンドリング

| 状況 | 対応 |
|---|---|
| タスクファイル不在 | `**/todos/*/README.md` を検索して候補を提示する |
| URLから対象を特定不能 | PR内の候補URL・check名を提示して選択を求める |
| コメントが削除済み・権限不足 | APIエラーを提示し、本文またはアクセス権の確認を依頼する |
| PRがclosed・merged | 読み取り専用で判定し、追補修正が必要なら別ブランチで続けるか確認する |
| ローカルHEADとPR head不一致 | 編集を停止し、安全なbranch切替・更新方法を確認する |
| dirty working tree | 重複の有無を調べ、重なる場合だけstash・commit・中断の判断を求める |
| CIログ取得不能 | check提供元とURLを提示し、ログ提供を依頼する |
| `--commit-push-reply` とCI失敗URLの併用 | 入力エラーとして、レビューコメントURLを指定するよう案内する |
| `--request-review` の単独指定 | 入力エラーとして、`--commit-push-reply` との併用を案内する |
| 返信投稿失敗 | review requestを行わず、投稿先・エラー・commit/pushの成否を分けて報告する |
| review request失敗 | 返信済みの状態を保持し、エラーと手動で依頼する対象ユーザーを報告する |
| diffが想定より大きい | 原因仮説を見直し、500行超なら続行前に再承認を得る |
| ローカル検証失敗 | commit・pushせず、原因調査へ戻る |

## 禁止事項

- 検証前にレビュー提案コードを適用しない。
- CIを通すためだけにテスト削除、skip追加、閾値緩和を行わない。
- 機密情報をログへ保存またはコードへハードコードしない。
- オプションなしでcommit、`--commit-push` または `--commit-push-reply` なしでpushを行わない。
- `--commit-push-reply` と最終レビュー承認なしにPRコメント返信を行わない。
- `--request-review`、`--commit-push-reply`、最終レビュー承認、commit・push・返信投稿の成功がすべて揃わない限りreview requestを行わない。
- ユーザー承認なしにconversationのresolve・workflow再実行を行わない。
- `git reset --hard`、無断stash、無断checkout、force pushを行わない。
