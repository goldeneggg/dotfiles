---
name: author-analyzer
description: |
  指定したGitHubリポジトリにおける特定authorのコミット履歴・PR（作成分・レビュー参加分）・Issueを横断分析し、
  「実績」「評価ポイント/セールスポイント」「得意分野」を構造化レポートとして出力するスキル。
  実績データはgit logとgh CLIから取得し、ファイル拡張子・パスパターン・コミットメッセージ（Conventional Commits）から
  得意分野を推定する。レポートは事実ベースの「データセクション」と前向き解釈の「評価セクション」を併記する。

  以下の状況で必ずトリガーすべき:
  (1) ユーザーが「<author>の実績を分析して」「<author>のセールスポイントを教えて」と依頼した時
  (2) ユーザーが「このリポジトリでの<author>の貢献を可視化して」「<author>の得意分野は？」と依頼した時
  (3) ユーザーが「<author>のコミット/PR/Issueをまとめて評価レポートを作って」と依頼した時
  (4) ユーザーが明示的に「author-analyzer スキル」の実行を指示された時
  (5) ユーザーが特定のGitHub username（@付き含む）と「分析」「評価」「貢献」「実績」「ポートフォリオ」を組み合わせて依頼した時
  (6) ユーザーが「自分（あるいは同僚）のアウトプットを振り返りたい」「キャリア棚卸しをしたい」と依頼した時
  (7) 採用・評価・1on1・キャリア相談などの文脈で「特定人物のGitHub上の働き」を要約する必要がある時

  GitHub username（gh CLIクエリ用）と対象リポジトリ（デフォルト: cwd、オプションで複数owner/repo指定可）を入力とする。
  期間はデフォルト全期間、--since/--untilで絞り込み可。出力はMarkdownファイル＋会話内サマリの両方。

  ただし、以下のケースでは別スキルを優先する:
  - PR単体のコードレビュー → pr-reviewer
  - コミットメッセージの提案 → commit-message-suggester
  - GitHub Actions実行ログの分析 → gh-action-run-validator
argument-hint: "<author> [owner/repo ...] [--since YYYY-MM-DD] [--until YYYY-MM-DD]"
context: fork
---

# author-analyzer

GitHubリポジトリにおける特定authorのコミット・PR・Issueを横断分析し、「実績」「評価ポイント」「得意分野」を構造化レポートとして出力します。

**注意: このSkillを使用する際のユーザーとのやり取りはすべて日本語で行います。**

## このスキルの設計思想

- **事実と解釈を分離**: 「データセクション」（数値・一覧）と「評価セクション」（前向きな解釈）を別建てにし、読み手が一次情報と二次解釈を区別できるようにする
- **過大評価の回避**: 評価セクションでも、数値の根拠を必ず添える。盛り上げる言葉だけのレポートは作らない
- **得意分野は複数シグナルの合成**: 「拡張子・パスのウェイト」と「Conventional Commitsのtype分布」と「PRラベル」を組み合わせて推定する。単一指標で断定しない

## Degrees of Freedom

- **引数の解析: Low freedom** — 後述の「引数の解析」セクションのパターンに厳密に従う。曖昧な場合は必ず確認する
- **データ収集: Low freedom** — gh / git の取得コマンドは本SKILLで指定する形に揃え、不要な情報を取り過ぎない（コンテキスト圧迫の回避）
- **得意分野の推定: Medium freedom** — シグナルの解釈はモデルの判断に任せるが、必ず根拠（拡張子別行数、上位ディレクトリ、commit type分布）を添える
- **評価ポイントの言語化: High freedom** — データから読み取れる強みを自然言語で表現してよい。ただし数値根拠を必ず併記する

## 引数の解析

`$ARGUMENTS` を以下のルールでパースする:

| パターン | 例 | 解釈 |
|---------|-----|------|
| `<author>` | `goldeneggg` | author（必須）。`@` プレフィクスは除去 |
| `<author> <owner/repo>` | `goldeneggg goldeneggg/dotfiles` | 単一リポジトリを明示指定 |
| `<author> <owner/repo> <owner/repo> ...` | `goldeneggg org/a org/b` | 複数リポジトリを横断分析 |
| `--since YYYY-MM-DD` | `--since 2024-01-01` | 期間下限 |
| `--until YYYY-MM-DD` | `--until 2024-12-31` | 期間上限 |
| 引数なし or authorなし | （空） | 選択肢提示で author を確認 |

**リポジトリ未指定時の挙動**:
1. cwd が git リポジトリかつ `gh repo view --json nameWithOwner` が成功する → そのリポジトリを対象にする
2. それ以外 → ユーザーに `owner/repo` を確認

**期間未指定時の挙動**: 全期間を対象とする（最初のコミット〜今日）。

## 前提条件

- `gh` CLI がインストール済み・認証済み（`gh auth status` で確認）
- 対象リポジトリへの読み取り権限
- ローカル分析の場合: 対象 git リポジトリで `git log` が実行できる
- Python 3 がインストール済み（集計スクリプト用）

`gh auth status` が失敗する場合は `gh auth login` を案内して中断する。

## 実行フロー

### Phase 0: 事前確認

1. 引数を解析し、author / repos / since / until を決定
2. `gh auth status` で認証確認
3. 作業ディレクトリ作成: `./.author-analyzer/<author>-<YYYYMMDDHHmmss>/`
   - 以降このディレクトリを `${WORKDIR}` と呼ぶ
   - 一時データ（JSONL等）は全てここに置く
4. 対象が複数リポジトリの場合、リポジトリごとにサブディレクトリを切る: `${WORKDIR}/<owner>__<repo>/`

### Phase 1: データ収集

リポジトリごとに以下を実行する。**各 gh コマンドは可能な限り並列で実行**してよい（独立な取得のため）。複数リポジトリを横断する場合や取得件数が多い場合は、リポジトリ単位でサブエージェントに委譲し `${WORKDIR}/<owner>__<repo>/` への書き出しまで任せて、メインには完了報告だけ戻させる。単一リポジトリ・短期間のような軽量なケースでは、委譲せずメインで直接進めてよい。

#### 1-1. コミット履歴

ローカル git リポジトリ（cwd の場合）:

```bash
git log --author="<author>" \
  ${SINCE:+--since=$SINCE} ${UNTIL:+--until=$UNTIL} \
  --pretty=format:'__COMMIT__%H%n%aI%n%an%n%ae%n%s%n%b%n__END__' \
  --numstat \
  > "${WORKDIR}/<owner>__<repo>/commits.txt"
```

`--author` には GitHub username だけでなく email/表示名も渡してよい。`<author>` で取りきれない場合は `git log --all --author="<author>"` で再試行し、それでも0件なら以下のフォールバック:

```bash
# author 検索の失敗時: GitHub username から noreply email を試す
git log --author="${AUTHOR}@users.noreply.github.com" ...
# それでも0件なら gh API search/commits を使う（後述）
```

リモートのみのリポジトリ（owner/repo 指定で未cloneのケース）:

```bash
gh api -X GET search/commits \
  -f q="author:<author> repo:<owner>/<repo>${SINCE:+ author-date:>=$SINCE}${UNTIL:+ author-date:<=$UNTIL}" \
  --paginate \
  -H "Accept: application/vnd.github.cloak-preview+json" \
  > "${WORKDIR}/<owner>__<repo>/commits.json"
```

注: GitHub commit search は変更ファイル一覧を返さない。詳細な拡張子別集計をしたい場合は対象リポジトリを `gh repo clone` してから git log を使うのが確実。デフォルトでは clone せず、リモートAPIで取得した summary だけ使う運用とし、ユーザーに「より詳細な得意分野推定にはローカル clone が必要」と提案する。

#### 1-2. PR（authorが作成したもの）

```bash
gh pr list --repo <owner>/<repo> \
  --author "<author>" --state all --limit 1000 \
  --json number,title,state,createdAt,updatedAt,mergedAt,closedAt,additions,deletions,changedFiles,labels,baseRefName,headRefName,url,reviewDecision \
  > "${WORKDIR}/<owner>__<repo>/pr_authored.json"
```

期間絞り込みは取得後にフィルタする（gh pr list の `--search` でも可だが、JSONフィールド化の方が後段で扱いやすい）。

#### 1-3. PR（authorがレビュー参加したもの）

レビュアー指定:

```bash
gh search prs --repo <owner>/<repo> --reviewed-by "<author>" --limit 1000 \
  --json number,title,author,state,createdAt,updatedAt,url \
  > "${WORKDIR}/<owner>__<repo>/pr_reviewed.json"
```

コメント参加:

```bash
gh search prs --repo <owner>/<repo> --commenter "<author>" --limit 1000 \
  --json number,title,author,state,createdAt,updatedAt,url \
  > "${WORKDIR}/<owner>__<repo>/pr_commented.json"
```

レビュアーかつauthorのケース（自身のPR）は後段で除外する。

#### 1-4. Issue

作成分:

```bash
gh issue list --repo <owner>/<repo> \
  --author "<author>" --state all --limit 1000 \
  --json number,title,state,createdAt,updatedAt,closedAt,labels,url \
  > "${WORKDIR}/<owner>__<repo>/issues_authored.json"
```

参加分（コメント）:

```bash
gh search issues --repo <owner>/<repo> --commenter "<author>" --limit 1000 \
  --json number,title,author,state,createdAt,updatedAt,url \
  > "${WORKDIR}/<owner>__<repo>/issues_commented.json"
```

#### 1-5. プロフィール（任意）

```bash
gh api users/<author> > "${WORKDIR}/profile.json"
```

公開プロフィールから「所属」「自己紹介」「公開リポジトリ数」などをレポート冒頭で軽く触れる材料に使う。取得失敗時は無視する。

### Phase 2: 集計

`scripts/aggregate.py` に各データを渡し、集計済みJSONを得る（Phase 1の生データを読み込んで小さな集計JSONを出力するだけの処理のため、委譲せずメインで直接実行してよい）:

```bash
python3 "${SKILL_DIR}/scripts/aggregate.py" \
  --workdir "${WORKDIR}" \
  --author "<author>" \
  --output "${WORKDIR}/aggregate.json"
```

`SKILL_DIR` はこの SKILL.md が置かれたディレクトリの絶対パス。
スキル発動時は当該パスを把握できるよう、最初に `SKILL_DIR=$(dirname <SKILL.md の絶対パス>)` を解決してから使うこと。スクリプトは以下を出力する:

- `commit_count`, `commit_period`（最古〜最新）
- `total_additions`, `total_deletions`, `total_files_changed`
- `top_extensions`: 拡張子別の合計変更行数 上位N（デフォルト10）
- `top_directories`: トップレベル/2階層目ディレクトリ別の合計変更行数 上位N
- `commit_type_distribution`: Conventional Commits の type 集計（feat/fix/docs/refactor/perf/test/chore/...）
- `pr_authored_stats`: 件数、マージ数、マージ率、平均PR Size（additions+deletions）、ラベル分布
- `pr_reviewed_stats`: 件数、ユニークauthor数
- `issue_stats`: 作成件数、参加件数、closeへの寄与
- `signals`: 上記から導出した「主要言語」「主要レイヤ」「貢献タイプ」のラベル列

スクリプト詳細は `scripts/aggregate.py` を参照。

### Phase 3: 分析と解釈

集計結果を読み、以下の3視点で解釈する:

#### 3-1. 実績（事実ベース）

- 期間とリポジトリ
- コミット数、PR作成数（マージ率）、PRレビュー参加数、Issue作成・参加数
- 変更行数（additions/deletions）、変更ファイル数
- 代表的なPRをタイトル＋URLで5件程度ピックアップ（マージ済みかつサイズ・コメント数が多いもの）

#### 3-2. 評価ポイント / セールスポイント（前向きな解釈）

数値根拠を必ず添える。以下の観点で抽出:

- **継続性**: 期間に対するコミット頻度の安定さ
- **完遂力**: PRマージ率の高さ、issue close への寄与
- **協調性**: 他者PRへのレビュー参加件数とコメント濃度
- **影響範囲**: 変更ファイル数、跨いだ上位ディレクトリ数（横断的に貢献しているか）
- **品質志向**: test/refactor/docs 系コミットの比率、CI関連ファイル変更

「テンプレ的に褒める」のではなく、具体データを引用しながら言語化する。例:

```text
バックエンドコア層の変更が大きく、`internal/server/**` のディレクトリで全体の38%を占める。
このディレクトリは他コントリビューターの変更も多くハブ的な領域であり、
そこに継続的にコミットしている点は中核的な信頼を得ている証左と読み取れる。
```

#### 3-3. 得意分野（推定）

複数シグナルから推定する:

| シグナル | 重み付け方針 |
|---------|-------------|
| 拡張子別変更行数（上位） | 主要言語の推定 |
| 上位ディレクトリ | レイヤ・ドメインの推定（frontend / server / infra / docs / tests など） |
| Conventional Commits type 分布 | 貢献タイプ（feature開発寄り / 修正寄り / refactor寄り / docs寄り） |
| PRラベル分布 | チームが付与した分類 |
| レビュアーロール頻度 | 設計レビュー寄り or 実装レビュー寄り |

推定にはばらつきがあるため、「<分野>に強い可能性が高い（X%の根拠：...）」のように確度を添える。

### Phase 4: レポート出力

`references/report_template.md` をベースにMarkdownを組み立て、以下に保存する:

```text
./author-analysis-<author>-<YYYYMMDD>.md
```

ファイル名は author と日付（実行日 YYYY-MM-DD）から決める。複数リポジトリを跨いだ場合は `./author-analysis-<author>-multi-<YYYYMMDD>.md`。

保存後、**会話内サマリ**として以下を出力する:

- 出力ファイルパス
- 期間 / 対象リポジトリ / コミット数・PR数・Issue数の概要1行
- 評価ポイントの top 3（短く）
- 得意分野の top 3（短く）
- 「詳細はファイルを参照」の旨

### Phase 5: 後片付け

- ${WORKDIR} 内の中間ファイル（commits.txt 等）は残す（再実行・差分確認しやすいように）
- ユーザーが不要と明言した場合のみ削除する

## 注意事項

- **GitHub username と git author の不一致**: GitHubアカウントの noreply メールでコミットしている場合、git log の `--author=<username>` でヒットしない。1-1 のフォールバック（noreply email、gh search/commits）を必ず備える
- **rate limit**: gh API は認証済みでも 5000req/h の制限がある。`--limit 1000` を超える件数でなければ通常問題ないが、複数リポジトリ × 大量PRの場合は警告し、必要なら ETA を提示
- **個人情報**: profile.json から取得した email は「公開プロフィールに掲載されている場合のみ」レポートに含める。`gh api users/<author>` のレスポンスで email が `null` なら触れない
- **盛らない**: 評価セクションで根拠のない誇張は避ける。データから読み取れない「リーダーシップ」「コミュニケーション能力」のような文化的評価は記述しない
- **大量出力対策**: コミット数が1000件を超える場合、レポートの「代表的PR」抜粋は10件程度までにし、それ以上は集計値だけ示す

## 実行例

```text
# 引数: alice-dev myorg/myrepo --since 2024-01-01
→ alice-dev の 2024-01-01 以降の myorg/myrepo における貢献を分析

# 引数: bob-eng myorg/repo-a myorg/repo-b
→ bob-eng の repo-a / repo-b 横断分析

# 引数: charlie （cwd が git リポジトリ）
→ cwd の owner/repo を自動検出して charlie の全期間貢献を分析
```
