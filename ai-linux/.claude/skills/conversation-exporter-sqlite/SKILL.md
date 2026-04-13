---
name: conversation-exporter-sqlite
description: |
  Claude Codeの会話セッションデータをSQLiteデータベースにエクスポートするスキル。
  現在のセッションのトランスクリプト（ユーザー入力・AI応答・ツール使用）、
  サブエージェントの会話履歴、メモリファイル、ファイル編集履歴を構造化して保存する。
  全プロジェクト・全セッションが単一のDBファイル（conversations.db）に蓄積される。
  以下の状況で使用:
  (1) ユーザーが「会話をエクスポートして」「セッションを保存して」「会話をSQLiteに出力して」と依頼した時
  (2) ユーザーが明示的に「/conversation-exporter-sqlite」を実行した時
  (3) ユーザーが「セッションデータをDBに保存して」「会話ログをデータベース化して」と依頼した時
  (4) 会話の記録・分析・アーカイブが必要な時
---

# Conversation Exporter (SQLite)

Claude Codeの会話セッションデータをSQLiteにエクスポートする。

## 概要

全プロジェクト・全セッションのデータを単一のSQLiteファイル `~/.claude/exports/conversations.db` に蓄積する。
Upsert方式により、同じセッションを複数回エクスポートしても重複せず差分のみが追加・更新される。

### テーブル構成

| テーブル | 内容 | 主キー | 親テーブル |
|---------|------|--------|-----------|
| `projects` | プロジェクト情報 | `project_path` | - |
| `sessions` | セッションメタデータ | `session_id` | `projects` |
| `messages` | ユーザー入力・AI応答・システムメッセージ | `uuid` | `sessions` |
| `tool_uses` | ツール呼び出し（assistantメッセージから抽出） | `id` | `messages`, `sessions` |
| `subagents` | サブエージェント情報 | `agent_id` | `sessions` |
| `subagent_messages` | サブエージェントの会話履歴 | `uuid` | `subagents`, `sessions` |
| `memory_files` | メモリファイル（frontmatter解析済み） | `file_path` | `projects` |
| `file_history` | ファイル編集履歴 | `id` | `sessions` |

### messages / subagent_messages の主要カラム

基本メタ:
- `uuid`, `session_id`, `parent_uuid`, `type` (user/assistant/system), `role`, `model`, `timestamp`, `cwd`, `git_branch`
- `is_sidechain`, `is_meta`, `user_type`, `subtype`

API識別子:
- `message_api_id` (Anthropic APIのmessage ID), `request_id`, `stop_reason`, `service_tier`

トークン使用量:
- `usage_input_tokens`: 非キャッシュのfresh入力
- `usage_output_tokens`: 出力
- `usage_cache_creation_input_tokens`: キャッシュ書込（新規キャッシュ化）
- `usage_cache_read_input_tokens`: キャッシュヒット（再利用）
- `usage_cache_creation_5m`: 5分TTLキャッシュ書込内訳
- `usage_cache_creation_1h`: 1時間TTLキャッシュ書込内訳

> **スキーマ自動マイグレーション**: 既存DBは初回実行時に `ALTER TABLE ADD COLUMN` で非破壊的に新カラムが追加される。過去メッセージのcache値はNULLのまま（再エクスポートで埋まる）。

### ER構造

```
projects 1──N sessions 1──N messages 1──N tool_uses
                       1──N subagents 1──N subagent_messages
                       1──N file_history
         1──N memory_files
```

## 実行方法

エクスポートスクリプトを実行する:

```bash
python3 scripts/export.py --project-path <cwd>
```

### オプション

| フラグ | 説明 | デフォルト |
|--------|------|----------|
| `--project-path` | プロジェクトのパス（cwdを渡す） | 必須 |
| `--session-id` | 特定のセッションIDを指定 | 最新セッションを自動検出 |
| `--output` | SQLiteファイルの出力パス | `~/.claude/exports/conversations.db` |
| `--no-memory` | メモリファイルを含めない | false |
| `--no-file-history` | ファイル編集履歴を含めない | false |

## ワークフロー

1. **セッション特定**: ディスク上の最新の.jsonlファイルから現在のセッションを特定
2. **プロジェクト登録**: projectsテーブルにUpsert
3. **トランスクリプト解析**: JSONL形式のトランスクリプトをパース
4. **ツール使用抽出**: assistantメッセージのcontent blocksからtool_useを抽出
5. **サブエージェント解析**: サブエージェントのメタデータとトランスクリプトをパース
6. **メモリ収集**: プロジェクトのmemoryディレクトリからファイルを読み取り
7. **ファイル履歴収集**: file-historyディレクトリからセッション中の編集履歴を収集
8. **SQLiteにUpsert**: 全データを書き込み

## 出力

エクスポート完了後、以下を報告する:
- SQLiteファイルのパス
- 保存されたレコード数（テーブルごと）
- セッションID

## 注意事項

- 現在実行中のセッションのトランスクリプトはリアルタイムで書き込まれているため、エクスポート時点までのデータが保存される
- assistantメッセージのcontentはJSON配列として保存される（テキスト、ツール呼び出し、ツール結果などの複合構造）
- 大きなセッションの場合、ファイルサイズが数十MBになることがある
- プロジェクト横断のクエリが可能（例: `SELECT tool_name, COUNT(*) FROM tool_uses JOIN sessions USING(session_id) GROUP BY tool_name`）
