# conversation-analyzer-sqlite 活用法ガイド

このドキュメントは、conversation-exporter-sqlite で蓄積された `~/.claude/exports/conversations.db` を、
単なる「会話ログ」ではなく**自分の Claude Code 利用の observability データレイク**として活用するための
詳細レシピ集である。

ユーザーから「活用法を教えて」「どんな分析ができる？」「効果的なレポートの出し方は？」と
質問された時に、AI はこのファイルを Read して参照する。通常の分析依頼時にはロード不要。

## 目次

- [0. 前提：保存されている観測データの全体像](#0-前提保存されている観測データの全体像)
- [1. 活用シナリオ別レシピ集（12種）](#1-活用シナリオ別レシピ集12種)
- [2. レポートとして組み立てる3つの型](#2-レポートとして組み立てる3つの型)
- [3. 実行のコツとハマりどころ](#3-実行のコツとハマりどころ)
- [4. すぐ試せるベスト3クエリ](#4-すぐ試せるベスト3クエリ)
- [5. 運用サイクル](#5-運用サイクル)

---

## 0. 前提：保存されている観測データの全体像

エクスポータが保存しているのは「単なる会話ログ」ではなく、Claude Code を
**観測可能(observable)なシステム**として扱える計装データである。
SKILL.md のサンプル分析（7種）は入り口に過ぎず、以下のカラム群を使うと
「働き方の改善ループ」を回せる。

| データ層 | 代表カラム | これで何がわかるか |
|---|---|---|
| トークン詳細 | `usage_cache_read_input_tokens` / `usage_cache_creation_input_tokens` / `usage_input_tokens` / `usage_output_tokens` | キャッシュ効率、コスト構造、コンテキスト肥大化 |
| スキル/プラグイン帰属 | `attribution_skill` / `attribution_plugin` | どのスキルが本当に効いているか（ROI） |
| Hook実行 | `hook_count` / `hook_errors` / `duration_ms` / `prevented_continuation` | 自作hookの失敗率、ブロック頻度 |
| 権限モード | `permission_modes` テーブル | acceptEdits/bypass 切替の頻度 |
| サブエージェント | `subagents` / `subagent_messages` | 並列化できているか、特定タイプ偏重 |
| ツール結果 | `tool_results` (interrupted / stderr) | 中断・失敗の発生箇所 |
| AIタイトル | `ai_titles` | セッションの「内容ラベル」での集計 |
| 添付 | `attachments`（skill_listing / deferred_tools_delta） | 利用可能スキルの認知範囲 |

2か月分以上のデータがあれば、統計的に意味のあるトレンドが出る。
1回限りの分析より「定例レビュー（週次・月次）」として回すのが本命。

---

## 1. 活用シナリオ別レシピ集（12種）

### レシピA. 「自分の働き方ダッシュボード」（月次レビュー向け）

**目的**: 直近30日の自分の Claude Code の使い方を1枚で振り返る。

**問いかけ方の例**:
> 「直近30日のClaude Code利用について、時間帯分布・プロジェクト集中度・ツール上位・サブエージェント活用率・キャッシュヒット率を出して、改善ポイントを3つ提案して」

**鍵となる集計軸**:
- 時間帯（`strftime('%H', timestamp)`）→ 集中タイムを可視化
- 曜日（`strftime('%w', timestamp)`）→ 平日/休日傾向
- セッション長分布 → 短すぎ/長すぎを把握
- **キャッシュヒット率** = `cache_read / (cache_read + cache_creation + input)`

サンプルクエリ:
```sql
SELECT
  ROUND(100.0 * SUM(usage_cache_read_input_tokens) /
        NULLIF(SUM(usage_cache_read_input_tokens
                 + usage_cache_creation_input_tokens
                 + usage_input_tokens), 0), 1) AS cache_hit_pct
FROM messages
WHERE timestamp >= date('now','-30 day');
```

キャッシュヒット率が低い日はコンテキスト切替が多すぎる兆候。

---

### レシピB. 「コスト・スパイク検出」

**目的**: 「今月たくさん使ったな…どこで？」の犯人特定。

**問いかけ方**:
> 「直近60日でトークン消費が突出しているセッションTop10と、その共通点を分析して」

**ポイント**:
- セッション別総トークン → 上位を抽出
- そのセッションの `ai_titles.title` を引いてラベル化
- そのセッションでよく呼ばれた tool_name 上位 → 何で重くなったか推測
- セッション長 vs トークン量 → コンテキスト肥大化型 / 並列大量実行型 を分類

```sql
SELECT s.session_id, t.title,
       SUM(m.usage_input_tokens + m.usage_cache_creation_input_tokens) AS heavy_input,
       SUM(m.usage_output_tokens) AS output,
       COUNT(*) AS msgs
FROM sessions s
LEFT JOIN ai_titles t USING(session_id)
JOIN messages m USING(session_id)
WHERE m.timestamp >= date('now','-60 day')
GROUP BY s.session_id
ORDER BY heavy_input DESC LIMIT 10;
```

→ アクション例: 「重いセッションはどれも特定のmake target系だった → 別セッションに分けるべき」

---

### レシピC. 「スキルROI測定」

**目的**: 自作 / 導入したスキルのうち、**実際に発火して結果が良かったもの**を選別。

**問いかけ方**:
> 「`attribution_skill` 別の発火回数、平均セッション長、エラー発生率、平均トークン消費を出して、ROIが高い/低いスキルをランキングして」

**メトリクス**:
- 発火回数（messages where attribution_skill IS NOT NULL）
- 同セッション内の hook_errors 発生有無
- スキル発火後 N メッセージで終了したか（≒ 解決した）
- そのスキル経由の tool_uses 数

```sql
SELECT attribution_skill,
       COUNT(*) AS fires,
       COUNT(DISTINCT session_id) AS sessions,
       AVG(usage_output_tokens) AS avg_out
FROM messages
WHERE attribution_skill IS NOT NULL
  AND timestamp >= date('now','-60 day')
GROUP BY attribution_skill
ORDER BY fires DESC;
```

→ アクション例: 「`pr-reviewer` は10回中9回別エージェント追加実行 → スキル単体で完結しないので統合検討」「`commiter --suggest` は1回呼ばれて即解決 → 優秀、description をもう少し pushy にして発火増を狙う」

自作スキル多数の場合に最も刺さる分析。

---

### レシピD. 「スキル発火漏れ検出」

**目的**: 「このスキル、もっと発火していいはずなのに発火してない」を炙り出す。

**手法**:
- `attachments` の `attachment_type = 'skill_listing'` で「セッションに提示されたスキル」を取得
- 一方、`messages.attribution_skill` で「実際に発火したスキル」を取得
- **提示はされたが発火しなかったスキル**を時系列で集計

これは description 最適化（skill-creator の `run_loop.py`）を回すべきスキルの候補リストになる。

---

### レシピE. 「hookヘルスチェック」

**目的**: 自作hookのエラー率と所要時間を計測。

```sql
SELECT subtype,
       COUNT(*) AS calls,
       SUM(CASE WHEN hook_errors IS NOT NULL AND hook_errors != '[]' THEN 1 ELSE 0 END) AS errors,
       AVG(duration_ms) AS avg_ms,
       MAX(duration_ms) AS max_ms
FROM messages
WHERE type='system' AND subtype IS NOT NULL
GROUP BY subtype
ORDER BY calls DESC;
```

`prevented_continuation = 1` が多い hook は作業を阻害している兆候。
`avg_ms` が大きい hook は体感を悪化させている。

hook整備の前後で before/after 比較を取ると効果測定として有意義。

---

### レシピF. 「サブエージェント並列化スコア」

**目的**: 並列で Subagent を起動できているか診断。

**指標**:
- セッションあたりの平均 Subagent 数
- 同一セッション内で「同時刻帯（±10秒）」に複数起動しているか
- Agent種別の偏り（Explore / Plan / 専門系の比率）

```sql
SELECT agent_type, COUNT(*) AS launches,
       AVG((SELECT COUNT(*) FROM subagent_messages sm WHERE sm.agent_id = sa.agent_id)) AS avg_msgs
FROM subagents sa
GROUP BY agent_type ORDER BY launches DESC;
```

→ アクション例: 「Explore起動が90%、Plan/専門系がほぼゼロ → 設計フェーズで Plan を使う癖をつけるべき」

---

### レシピG. 「権限モード変遷」

**目的**: bypass / acceptEdits をどれくらい使っているか、どこで切り替えたか。

```sql
SELECT mode, COUNT(*) AS switches
FROM permission_modes
GROUP BY mode
ORDER BY switches DESC;
```

セッションごとの遷移を時系列で見ると、「危険操作前に plan へ落とす」運用ができているかが診断できる。

---

### レシピH. 「ファイル編集ホットスポット & 再編集率」

**目的**: 同じファイルを何度も触り直していないか（設計不足の兆候）。

```sql
SELECT json_extract(tool_input,'$.file_path') AS f,
       COUNT(*) AS edits,
       COUNT(DISTINCT session_id) AS distinct_sessions
FROM tool_uses
WHERE tool_name IN ('Edit','Write','NotebookEdit')
  AND f IS NOT NULL
GROUP BY f
HAVING distinct_sessions >= 3
ORDER BY edits DESC LIMIT 20;
```

複数セッションで何度も編集されているファイル = リファクタ or 分割候補。
CLAUDE.md / SKILL.md / shell rc が上位に来やすい。

---

### レシピI. 「読書傾向（Read偏重）」

**目的**: Read（ファイル参照）で消費しているトークンが多すぎないか。

- Read のtool_uses数 vs Edit/Write数の比率
- セッションあたりの累計読込ファイル数
- 同一ファイルを同一セッション内で再Readしているケース（記憶忘れ）

コンテキスト肥大化の最大原因になりがち。比率が10:1以上だと過剰参照の可能性。

---

### レシピJ. 「曜日×時間帯ヒートマップ（テキスト版）」

```sql
SELECT strftime('%w', timestamp) AS dow,
       strftime('%H', timestamp) AS hr,
       COUNT(*) AS msgs
FROM messages
WHERE timestamp >= date('now','-60 day')
GROUP BY dow, hr
ORDER BY dow, hr;
```

レポート整形時にマークダウンの12×7テーブルにすると視認性が良い。深夜帯偏重なら睡眠コストを推定できる。

---

### レシピK. 「失敗・中断シグナル」

**目的**: 「うまくいかなかった会話」を炙り出す。

ヒント:
- `tool_results.interrupted = 1`
- `tool_results.stderr IS NOT NULL`
- `messages.stop_reason = 'refusal'` または `'max_tokens'`
- `prevented_continuation = 1`

```sql
SELECT s.project_path, COUNT(*) AS interruptions
FROM tool_results tr JOIN sessions s USING(session_id)
WHERE tr.interrupted = 1
GROUP BY s.project_path ORDER BY interruptions DESC;
```

中断が多発するプロジェクト = ツールチェーン or 環境変数の問題候補。

---

### レシピL. 「last_prompts の質的レビュー」

**目的**: ユーザー自身のプロンプティング傾向の自己診断。

- 1セッション内のプロンプト平均長
- 「やり直し」「再度」「もう一度」など修正系キーワードの出現率
- AskUserQuestion が発生したセッション率

```sql
SELECT COUNT(*) AS total,
       SUM(CASE WHEN content LIKE '%やり直%' OR content LIKE '%再度%'
                  OR content LIKE '%もう一度%' THEN 1 ELSE 0 END) AS redo_prompts
FROM messages WHERE type='user';
```

redo率が下がっていれば、自分の指示精度の学習曲線として可視化できる。

---

## 2. レポートとして組み立てる3つの型

単発クエリを並べるだけでは「何が言いたいか」がぼやける。以下のレポート型を使い分ける。

### 型1：定例週次レビュー（毎週月曜の儀式向け）

構成:
1. 今週の数値サマリー（セッション/メッセージ/トークン/コスト推定）
2. 先週比デルタ（↑↓％）
3. Top3 プロジェクト & Top3 スキル発火
4. ハイライト（最重セッション / エラー多発hook / 中断件数）
5. **改善提案 上位3つ**（SKILL.md の「💡 改善提案」セクション活用）

毎週同フォーマットで蓄積すると「個人開発KPI」になる。

### 型2：プロジェクト棚卸しレポート

ブランチ別・プロジェクト別の作業バランス確認向け。

- `git_branch` 別の累計メッセージ
- ブランチ別の Edit/Write 比率
- ブランチ別の最終アクセス日

長期間触らないブランチや、メンテ漏れプロジェクトの検出に使える。

### 型3：スキル/プラグイン健全性レポート（重要）

自作スキル多数の場合の本命。

- スキル発火数 × 平均解決メッセージ数 × エラー発生率の三項マトリクス
- 「提示されたが発火していないスキル」リスト
- description の最適化候補（skill-creator の `run_loop.py` への入力）

このレポートを月1で回せば、スキル群のメンテループが完成する。

---

## 3. 実行のコツとハマりどころ

1. **スキーマ確認を最初にやる**: `sqlite3 ~/.claude/exports/conversations.db ".schema messages"` を最初に流して、カラム名のドリフトを潰す。エクスポータ側のスキーマ更新に追従するため。
2. **NULL対応必須**: `usage_*` は assistant メッセージのみ、system メッセージは NULL。`WHERE usage_input_tokens IS NOT NULL` を癖にする。
3. **タイムゾーン**: timestamp は UTC。日本時間表示する場合は `datetime(timestamp,'+9 hours')`。
4. **JSON抽出は `json_extract`**: `tool_input` / `hook_infos` / `attachment_data` などは全部 JSON 文字列。
5. **重いクエリは CTE で段階化**: 数か月分だと数百万行になりうるので、まずサブセットを WITH 句で絞ってから集計。
6. **キャッシュトークンを忘れない**: 「コスト」を計算する時 `usage_input_tokens` だけ見ると過小評価。必ず `cache_read` / `cache_creation` も合算する。

---

## 4. すぐ試せるベスト3クエリ

### (1) 今月のキャッシュ効率

```bash
sqlite3 ~/.claude/exports/conversations.db <<'SQL'
SELECT DATE(timestamp) day,
  SUM(usage_cache_read_input_tokens) read,
  SUM(usage_cache_creation_input_tokens) write,
  SUM(usage_input_tokens) fresh,
  ROUND(100.0*SUM(usage_cache_read_input_tokens)/NULLIF(SUM(usage_cache_read_input_tokens+usage_cache_creation_input_tokens+usage_input_tokens),0),1) hit_pct
FROM messages
WHERE timestamp >= date('now','-30 day') AND type='assistant'
GROUP BY day ORDER BY day;
SQL
```

### (2) スキル別ROIスコア

```bash
sqlite3 ~/.claude/exports/conversations.db <<'SQL'
SELECT attribution_skill,
  COUNT(*) fires,
  COUNT(DISTINCT session_id) sessions,
  ROUND(AVG(usage_output_tokens),0) avg_out
FROM messages
WHERE attribution_skill IS NOT NULL
  AND timestamp >= date('now','-60 day')
GROUP BY attribution_skill
ORDER BY fires DESC;
SQL
```

### (3) hookヘルス

```bash
sqlite3 ~/.claude/exports/conversations.db <<'SQL'
SELECT subtype,
  COUNT(*) calls,
  SUM(CASE WHEN hook_errors NOT IN ('','[]') AND hook_errors IS NOT NULL THEN 1 ELSE 0 END) errs,
  ROUND(AVG(duration_ms),0) avg_ms
FROM messages
WHERE type='system' AND subtype IS NOT NULL
GROUP BY subtype ORDER BY calls DESC;
SQL
```

---

## 5. 運用サイクル

1. **まず1回フルレポートを回す**: 「直近60日の総合レポート + スキルROI + hookヘルス を出して」と analyzer に依頼。
2. **週次レビューを定例化**: schedule スキル経由で毎週月曜にレポート生成を仕込む（routine化）。
3. **発見を skill-creator に還流**: 発火していないスキルの description を `run_loop.py` で最適化。
4. **CLAUDE.md / hook の調整**: 中断・hookエラーの多い箇所を修正 → 次月レポートで効果測定。

このサイクルが回り始めると、`conversations.db` は自分専用の observability データレイクとして機能する。
2か月分以上のデータが溜まっていれば、すでに統計的な意味のある差分が見える段階である。
