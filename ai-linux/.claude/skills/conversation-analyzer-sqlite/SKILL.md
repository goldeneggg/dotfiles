---
name: conversation-analyzer-sqlite
description: |
  Claude Codeの会話データ（SQLiteエクスポート）を分析し、使い方の傾向・生産性・コスト・ツール利用パターンなどのレポートを生成するスキル。
  conversation-exporter-sqliteでエクスポート済みのconversations.dbを対象とする。

  以下の状況で使用:
  (1) ユーザーが「会話データを分析して」「使い方の傾向を見て」「Claude Codeの利用状況を確認して」と依頼した時
  (2) ユーザーが明示的に「/conversation-analyzer-sqlite」を実行した時
  (3) ユーザーが「トークン消費量を確認して」「どのツールをよく使ってる？」「プロジェクト別の利用状況は？」と聞いた時
  (4) ユーザーが「セッション履歴を振り返りたい」「生産性を分析して」と依頼した時
  (5) ユーザーが「会話のサマリーを出して」「最近の作業傾向を教えて」と依頼した時
  (6) 会話エクスポートデータに基づく任意の統計・分析・可視化の依頼があった時
  「分析」「傾向」「統計」「レポート」「利用状況」「トークン」「コスト」といったキーワードと
  Claude Code/会話/セッションが組み合わさった依頼なら積極的にトリガーすべき。
---

# Conversation Analyzer SQLite

Claude Codeの会話エクスポートデータ（SQLite）を分析し、構造化レポートを生成する。

## データベースの場所

デフォルト: `~/.claude/exports/conversations.db`

ユーザーが別のパスを指定した場合はそちらを使う。

## データベーススキーマ

### テーブル構成

| テーブル | 内容 | 主要カラム |
|---------|------|-----------|
| `projects` | プロジェクト情報 | project_path, first_seen_at, last_exported_at |
| `sessions` | セッション情報 | session_id, project_path, git_branch, message_count, created_at, modified_at |
| `messages` | 全メッセージ | uuid, session_id, type(user/assistant/system), content(JSON), model, timestamp, usage_input_tokens, usage_output_tokens |
| `tool_uses` | ツール使用履歴 | id, session_id, tool_name, tool_input(JSON), timestamp |
| `subagents` | サブエージェント情報 | agent_id, session_id, agent_type, message_count |
| `subagent_messages` | サブエージェントメッセージ | uuid, agent_id, session_id, type, content(JSON) |
| `memory_files` | メモリファイル | file_path, project_path, name, description, type |
| `file_history` | ファイル編集履歴 | id, session_id, file_hash, version, file_size, content |

### 重要な注意点

- `sessions.created_at`/`modified_at` は空の場合がある。日付解析にはmessages.timestampを使う
- `messages.content` はJSON文字列。テキストブロックやtool_useブロックの配列が格納される
- `messages.type` は `user`, `assistant`, `system` のいずれか
- `usage_input_tokens`, `usage_output_tokens` はNULLの場合がある
- タイムスタンプはISO8601 UTC形式

## 分析レポートの種類

ユーザーの依頼に応じて以下の分析を組み合わせる。特に指定がない場合は「総合レポート」を生成する。

### 1. 総合サマリー（デフォルト）

全体の概況を把握するダッシュボード的レポート。

```sql
-- 基本統計
SELECT COUNT(DISTINCT project_path) as projects,
       COUNT(*) as sessions,
       SUM(message_count) as total_messages
FROM sessions;

-- 期間
SELECT MIN(created_at) as first_session, MAX(modified_at) as last_session FROM sessions;

-- トークン消費
SELECT SUM(usage_input_tokens) as total_input,
       SUM(usage_output_tokens) as total_output
FROM messages WHERE usage_input_tokens IS NOT NULL;

-- ツール使用トップ5
SELECT tool_name, COUNT(*) as count
FROM tool_uses GROUP BY tool_name ORDER BY count DESC LIMIT 5;

-- プロジェクト別セッション数
SELECT project_path, COUNT(*) as sessions, SUM(message_count) as messages
FROM sessions GROUP BY project_path ORDER BY sessions DESC;
```

出力フォーマット:
```
## Claude Code 利用状況レポート

### 概要
- 分析期間: YYYY-MM-DD ～ YYYY-MM-DD
- プロジェクト数: N
- 総セッション数: N
- 総メッセージ数: N（ユーザー: N / アシスタント: N / システム: N）
- 総トークン消費: 入力 N / 出力 N

### プロジェクト別
| プロジェクト | セッション | メッセージ | 最終利用 |
|...

### ツール利用
| ツール | 使用回数 | 割合 |
|...

### サブエージェント利用
| タイプ | 起動回数 |
|...
```

### 2. トークン・コスト分析

トークン消費の傾向とコスト推定を行う。

```sql
-- 日別トークン消費
SELECT DATE(timestamp) as day,
       SUM(usage_input_tokens) as input_tokens,
       SUM(usage_output_tokens) as output_tokens
FROM messages
WHERE usage_input_tokens IS NOT NULL
GROUP BY day ORDER BY day;

-- セッション別トークン消費（重いセッション特定）
SELECT s.session_id, s.project_path,
       SUM(m.usage_input_tokens) as input_tokens,
       SUM(m.usage_output_tokens) as output_tokens,
       s.message_count
FROM sessions s JOIN messages m ON s.session_id = m.session_id
WHERE m.usage_input_tokens IS NOT NULL
GROUP BY s.session_id ORDER BY input_tokens DESC LIMIT 10;
```

コスト推定ルール（概算）:
- Claude Sonnet: 入力 $3/MTok, 出力 $15/MTok
- Claude Opus: 入力 $15/MTok, 出力 $75/MTok
- モデル名が不明な場合はSonnetベースで概算

### 3. ツール利用パターン分析

どのツールをどのように使っているかの詳細分析。

```sql
-- ツール使用頻度
SELECT tool_name, COUNT(*) as count,
       ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM tool_uses), 1) as pct
FROM tool_uses GROUP BY tool_name ORDER BY count DESC;

-- プロジェクト×ツールのクロス集計
SELECT s.project_path, tu.tool_name, COUNT(*) as count
FROM tool_uses tu JOIN sessions s ON tu.session_id = s.session_id
GROUP BY s.project_path, tu.tool_name
ORDER BY s.project_path, count DESC;

-- 日別ツール使用推移
SELECT DATE(timestamp) as day, tool_name, COUNT(*) as count
FROM tool_uses GROUP BY day, tool_name ORDER BY day;
```

### 4. セッション分析

セッションの特徴と作業パターンを分析。

```sql
-- セッション長分布
SELECT
  CASE
    WHEN message_count <= 10 THEN '短い (1-10)'
    WHEN message_count <= 50 THEN '中程度 (11-50)'
    WHEN message_count <= 100 THEN '長い (51-100)'
    ELSE '非常に長い (100+)'
  END as category,
  COUNT(*) as count
FROM sessions GROUP BY category;

-- 曜日別・時間帯別セッション数
SELECT
  CASE CAST(strftime('%w', created_at) AS INTEGER)
    WHEN 0 THEN '日' WHEN 1 THEN '月' WHEN 2 THEN '火'
    WHEN 3 THEN '水' WHEN 4 THEN '木' WHEN 5 THEN '金' WHEN 6 THEN '土'
  END as weekday,
  COUNT(*) as sessions
FROM sessions GROUP BY weekday;

-- ブランチ別作業量
SELECT git_branch, COUNT(*) as sessions, SUM(message_count) as messages
FROM sessions WHERE git_branch IS NOT NULL
GROUP BY git_branch ORDER BY messages DESC LIMIT 10;
```

### 5. ファイル編集分析

どのファイルがどれだけ編集されたかの分析。

```sql
-- よく編集されるファイル（tool_usesのEditやWriteから抽出）
SELECT json_extract(tool_input, '$.file_path') as file_path, COUNT(*) as edits
FROM tool_uses
WHERE tool_name IN ('Edit', 'Write')
  AND json_extract(tool_input, '$.file_path') IS NOT NULL
GROUP BY file_path ORDER BY edits DESC LIMIT 15;

-- file_historyからの編集量
SELECT file_hash, COUNT(*) as versions, MAX(file_size) as max_size
FROM file_history GROUP BY file_hash ORDER BY versions DESC LIMIT 10;
```

### 6. サブエージェント分析

サブエージェントの利用傾向。

```sql
-- タイプ別サブエージェント使用
SELECT subagent_type, COUNT(*) as count,
       AVG(msg_count) as avg_messages
FROM (
  SELECT sa.subagent_type, sa.agent_id,
         COUNT(sm.uuid) as msg_count
  FROM subagents sa
  LEFT JOIN subagent_messages sm ON sa.agent_id = sm.agent_id
  GROUP BY sa.agent_id
) GROUP BY subagent_type ORDER BY count DESC;
```

### 7. 時系列トレンド分析

週次・月次の利用トレンド。

```sql
-- 週次トレンド
SELECT strftime('%Y-W%W', created_at) as week,
       COUNT(*) as sessions,
       SUM(message_count) as messages
FROM sessions GROUP BY week ORDER BY week;
```

## 分析の実行方法

1. `scripts/analyze.py` を使ってSQLクエリを実行し、結果を取得する
2. 結果をマークダウンテーブルやリストとして整形する
3. 数値には適切な単位をつける（トークンはK/M単位、割合は%表示）
4. 大きな数値にはカンマ区切りを使う

## 引数の解釈

ユーザーの依頼から以下を判断する:

- **期間指定**: 「先週」「今月」「直近30日」→ WHERE句で日付フィルタ
- **プロジェクト指定**: プロジェクト名やパスの部分一致 → WHERE句でLIKEフィルタ
- **分析種別**: 上記1-7のどれか、または複合。指定なしなら「総合サマリー」
- **出力形式**: デフォルトはマークダウン。CSV出力を求められたらファイル保存

## 実装上の注意

- SQLiteへのアクセスはBashツールで `sqlite3` コマンドを使用する
- クエリ結果が大きい場合はLIMITで制限する
- NULLデータ（特にトークン数）を適切にハンドルする（COALESCEやIS NOT NULL）
- JSONフィールドの抽出には `json_extract()` を使用する
- レポートの冒頭に分析日時とデータベースパスを記載する

## 改善提案（Insights）

レポート出力後、分析データに基づいてClaude Codeの活用改善案を提案する。
以下の観点でデータを読み取り、具体的かつ実行可能なアドバイスを3〜5個に絞って提示する。

### 観点

#### ツール利用の最適化
- Bash で `grep`/`find`/`cat` を多用 → Grep/Glob/Read の専用ツール活用を推奨
- Edit/Write の比率が極端 → 既存ファイル編集にはEditを優先すべき
- ToolSearch の使用が少ない → 利用可能なツールの発見機会を逃している可能性

#### セッション設計
- 100+メッセージの長大セッションが多い → タスク分割で精度・コスト両面で改善
- 短すぎるセッション（1-10）が多い → セッション起動のオーバーヘッド
- 特定曜日に集中 → 作業分散やバッチ処理の検討

#### サブエージェント活用
- Agent利用が少ない → 並列サブエージェントで調査・テスト等の時短が可能
- 特定タイプに偏っている → 他のエージェントタイプ（Explore, Plan等）の活用余地
- カスタムエージェントが未活用 → プロジェクト固有の定型作業を自動化できる

#### コスト効率
- 特定セッションのトークン消費が突出 → コンテキスト肥大化の兆候、適切なタイミングでの新セッション開始
- 入力トークンが出力に比べ極端に大きい → 不要なファイル読み込みやコンテキストの見直し
- 日別コスト推移の急増 → 原因セッションの特定と作業方法の振り返り

#### ファイル操作パターン
- 同一ファイルへの編集回数が極端に多い → 設計段階での検討不足、またはファイル分割の検討
- Readが多くEditが少ないファイル → 参照専用ならreferencesディレクトリへの整理を検討

### 提案のフォーマット

レポート末尾に「💡 改善提案」セクションとして以下の形式で出力する:

```
## 改善提案

データに基づく活用改善のヒント:

1. **[カテゴリ]**: [具体的な提案] — [根拠データ]
2. ...
```

- 根拠となる数値を必ず添える（「Bashでgrep系コマンドが推定N回」等）
- 該当しない観点は無理に出さない
- ユーザーの利用スタイルを否定せず、選択肢として提示する
