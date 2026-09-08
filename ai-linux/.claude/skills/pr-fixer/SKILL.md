---
name: pr-fixer
description: 指定したGitHub PRの単一レビューコメントまたはCI失敗を、タスク文書に依存せず検証して最小修正する。コメント・CI URLを起点に妥当性、根本原因、修正、検証、指定時のcommit・push・返信まで扱う。task-starterのタスク要件を基準にする場合はtask-artifact-fixer、PR全体の未解決指摘・CIをまとめて扱う場合はlocal-autofix-prを使う。
---

# PR Fixer

指定された外部指摘を事実として扱わず、PRの目的、既存の公開契約、PR差分、現在のコード、テストと失敗ログで独立に検証する。根拠が確認できた問題だけを最小限に直す。

## 呼び出し

```text
$pr-fixer <PRレビューコメントURL or PRのCI失敗URL> [--commit | --commit-push | --commit-push-reply] [--request-review] [--no-agent]
```

位置引数は1つだけ必須とする。

- `<PRレビューコメントURL>`: PR上の `discussion_r...`、`issuecomment-...`、`pullrequestreview-...` のいずれかを含むURL
- `<PRのCI失敗URL>`: GitHub Actionsのrun/job URL、または失敗checkを一意に特定できるPR checks URL

PRトップURLだけでコメントまたは失敗checkを一意に特定できない場合は、候補を提示して選択を求める。URLと現在のリポジトリが異なる場合は、対象を推測しない。

### オプション

- `--commit`: 最終レビュー承認後、今回の変更だけをステージし、セッション固有の一時ファイルへConventional Commits形式のコミットログを出力して `git commit -F` を実行する。
- `--commit-push`: `--commit` を暗黙に有効化し、コミット成功後に対象PRのheadブランチへ通常の `git push` を実行する。force pushは行わない。
- `--commit-push-reply`: レビューコメントURL専用。`--commit-push` を暗黙に有効化し、push成功後に検証結果と修正・検証内容をコメント投稿する。`discussion_r<ID>` のURLは、対象が返信ならその `in_reply_to`、それ以外なら `ID` をスレッド先頭コメントIDとして同じレビューthreadへ返信する。`issuecomment-<ID>` と `pullrequestreview-<ID>` のURLは、次の形式でPRへ新規コメントを投稿する。

  ```text
  > {レビューコメントURL}

  {返信コメント}
  ```

- `--request-review`: `--commit-push-reply` との併用時だけ有効。返信投稿成功後、元コメントのユーザーがbotではなく、当該PRの既存reviewのauthor集合に含まれる場合だけreview requestする。
- `--no-agent`: `task-artifact-fixer` との呼び出し互換性のため受理する。タスク文書を読む工程がないため、処理は変えない。

`--commit-push-reply` と他のcommit系オプションが併記された場合は `--commit-push-reply` として扱う。`--commit-push-reply` をCI失敗URLと併用した場合、および `--request-review` を `--commit-push-reply` なしで指定した場合は、外部操作を行わず入力エラーとして扱う。オプションなしの場合は、最終レビュー承認後に対象ファイルのステージングとコミットログファイルの出力まで行い、commit・push・返信・review requestは行わない。

## スコープ

### 含むもの

- PRの目的・既存契約・現在コードを基準にした、指定レビューコメントの妥当性検証
- PR差分・失敗ログ・対象コードを根拠にした、指定CI失敗の原因特定
- 妥当と判定した問題への最小修正、回帰テスト、Lint・型チェック
- オプションに応じたcommit・push、指定コメントへの返信、条件付きreview request

### 含まないもの

- タスク文書、進捗正本、受け入れ条件の読込・更新
- PR全体の新規レビューや、指定URL以外のレビュー指摘・CI失敗の便乗修正
- conversationのresolve、workflowの再実行、PR説明の更新、approve、merge、close、rebase、force push
- 指定問題と無関係なリファクタリングやフォールバック追加

## 実行原則

1. **外部指摘を事実として扱わない。** コメントや失敗ログを調査開始点とし、PRの目的・既存契約・PR差分・現在コード・再現結果で独立検証する。
2. **根本原因へ直接対応する。** 症状を隠すskip、retry、条件緩和、エラー握り潰しを、要件なしに追加しない。
3. **変更を指定対象へ限定する。** 別の問題は「気づきメモ」として報告し、その場で修正しない。
4. **ユーザー変更を保持する。** dirty working treeを確認し、重なる未コミット変更がある場合は編集前に相談する。stash・reset・checkoutを無断実行しない。
5. **公開情報と作業証跡を分離する。** PR返信にはローカルパス、内部の作業管理情報、未確認の事実を含めない。

## ワークフロー

### Phase 1: 入力と作業状態を確定する

1. URLと5オプションを解析する。不足・不明・競合があれば推測せず確認する。`--commit-push-reply` ではレビューコメントURLであること、`--request-review` が指定される場合は `--commit-push-reply` も指定されることを確認する。
2. `git rev-parse --show-toplevel`、`git status --short --branch`、`gh auth status` を確認する。
3. URLから `owner/repo`、PR番号、対象ID（comment / review / run / job / check）を抽出する。
4. `gh pr view` でPRのstate、title、body、head/baseブランチ、head SHA、head repositoryを取得し、ローカルのbranch・HEAD・remoteと照合する。`--request-review` 指定時は既存reviewのauthor集合も取得し、元コメント投稿者がこの集合に含まれるかだけを判定する。
5. ローカルがPR headと一致しない場合は編集せず、安全な切替・更新方法を提示して確認する。
6. PRが `CLOSED` または `MERGED` の場合は既定で読み取り専用の検証に留める。別ブランチでの追補修正を求められた場合だけ、対象ブランチとスコープを確認して続行する。

### Phase 2: PRとプロジェクトの判断材料を取得する

1. リポジトリ直下から対象へ適用される `AGENTS.md`、`CLAUDE.md`、開発・テスト規約を読む。
2. PRのtitle・bodyと差分から変更目的を抽出する。目的の説明だけで正しさを判断しない。
3. 指摘箇所の現在コードと呼び出し元、関連テスト、公開仕様・設定・既存の契約を読む。期待動作を裏付ける資料が不足する場合は、仕様判断が必要な状態として扱う。

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

巨大ログを一度に会話へ展開しない。一時保存が必要ならセッション固有の一時ディレクトリを使い、必要行だけ読む。

### Phase 4: 妥当性と根本原因を判定する

#### レビューコメントの分類

コメントの各主張を、次のいずれかへ分類する。

- **妥当**: PRの目的または既存契約に反し、現在のPR headでも問題が再現する。
- **部分的に妥当**: 問題はあるが、提案された範囲・修正方法の一部が過剰または目的外である。
- **対応済み・outdated**: 後続commitで問題が解消されている。
- **不当**: コメントの前提がコード・仕様・テスト事実と一致しない。
- **仕様判断が必要**: 複数の解釈が成立し、既存契約・PRの目的・テストでは決められない。

判定前に、コメントが要求する期待動作を一文で言い換え、対象コードと呼び出し元、関連テスト、PRの目的、既存契約を突き合わせる。提案コードはそのまま採用せず、反証となるケースも確認する。

#### CI失敗の分類

失敗を次のいずれかへ分類する。

- **PR変更による回帰**
- **リポジトリ内のworkflow・依存・設定不備**
- **flaky・並列干渉**
- **runner・権限・secret・外部サービス等の環境要因**
- **PRと無関係な既存障害**
- **原因未確定**

ログ、PR差分、対象コード、同一checkの他matrix結果で因果関係を説明する。再実行だけで消えそうという理由でflakyと断定しない。指定問題の根本原因を直接解消するリポジトリ内修正だけを編集対象とする。

#### 判定後の分岐

- `妥当`、`部分的に妥当`、`PR変更による回帰`、`リポジトリ内の不備`: 根拠と最小修正計画を提示し、ユーザー承認を得てPhase 5へ進む。
- `対応済み・outdated`、`不当`、環境要因、無関係な既存障害: コードを変更せず、根拠と推奨アクションを報告する。
- `仕様判断が必要`、`原因未確定`: 不足情報と推奨案を示して確認する。推測で修正しない。

修正計画には、変更対象、変更理由、追加・更新するテスト、実行する検証、スコープ外の発見を含める。

### Phase 5: 最小修正を実装する

1. 承認後、編集対象ファイルを直前に読み直す。
2. 原因へ直接対応する最小差分を実装する。本番コードを変更する場合は、問題を再現して修正後に通る回帰テストを可能な範囲で追加する。
3. 自動生成物は所定の生成コマンドで更新し、直接編集しない。
4. 指定対象と無関係な発見は変更せず、結果報告の気づきメモへ残す。

### Phase 6: 修正を検証する

1. 指摘またはCI失敗を再現する最小のテストを最初に実行する。
2. 変更対象に近い軽量テスト、リポジトリ所定のLint・型チェック・format check、`git diff --check` を実行する。
3. CI固有条件をローカルで完全再現できない場合は、ローカルで確認できた範囲と未検証条件を分離する。
4. DB、コンテナ、外部API等を使う重いテストは既定でskipし、ローカル実行が必要なら事前に承認を得る。
5. 失敗した検証はエラーメッセージを正確に読み、原因特定後に修正して再実行する。3回修正しても解決しない場合は続行判断を求める。
6. `git diff` と `git status --short` で依頼外変更の混入とユーザー変更との重複がないことを確認する。

### Phase 7: 作業結果をレビューする

次の形式で結論から報告し、コード変更がある場合は最終承認を求める。

```markdown
## 判定
- 対象: {コメント / check名}
- 分類: {分類}
- 根拠: {PRの目的・コード・既存契約・ログ・テストの対応}

## 修正内容
- `{path}`: {最小修正の概要}

## 検証結果
- 対象テスト: `{command}` → {PASS/FAIL}
- Lint・型・format: `{command}` → {PASS/FAIL/SKIP}
- 重いテスト・CI固有条件: {SKIPまたは結果と理由}

## 気づきメモ
- {スコープ外の発見、または「なし」}

## 外部操作
- PRコメント返信・review request・resolve・workflow再実行: 未実施
```

コード変更がない判定ではcommit・pushを行わず、調査結果だけを報告して終了する。

### PRコメント返信の記述

PRコメント返信は、ローカル環境を知らないレビュアーが単独で読んでも理解できる公開文書として作成する。

- 結論、対応内容、検証結果をこの順で簡潔に書く。コードを変更しない場合は、結論と確認できた事実だけを示す。
- ローカルパス、内部の作業項目・受け入れ条件・進捗・ログ、未確認の事実を本文へ書かない。
- 読み手が確認できるPR差分内のファイルパスやコード識別子は、必要な場合だけ使う。専門用語や略語は初出時に短く説明し、主語・条件・結果を省略しない。

投稿直前に、記載した事実をPR差分・コード・検証結果で裏付けられることを確認する。満たさない場合は、投稿前に書き直す。

### Phase 8: ステージング・commit・pushを行う

Phase 7の最終承認後、コード変更がある場合だけ次を実行する。

1. `.git/hooks/pre-commit` と `.githooks/pre-commit` を確認する。存在する場合は内容を読み、定義されたformat・Lint等を `git add` 前に直接実行して成功させる。
2. 今回変更したコード・テスト・設定だけを `git add` する。ユーザーの未コミット変更や作業証跡はステージしない。
3. セッション固有の一時ファイルへ、Conventional Commits形式・各行72文字以内のコミットログを出力する。メッセージへローカル一時ファイルのパスを含めない。
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
