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
| `messages` | user/assistant/systemメッセージ（hook実行サマリ含む） | `uuid` | `sessions` |
| `tool_uses` | ツール呼び出し（assistantメッセージから抽出） | `id` | `messages`, `sessions` |
| `tool_results` | ツール実行結果（stdout/stderr/interrupted/isImage等） | `tool_use_id` | `messages`, `sessions` |
| `subagents` | サブエージェント情報 | `agent_id` | `sessions` |
| `subagent_messages` | サブエージェントの会話履歴 | `uuid` | `subagents`, `sessions` |
| `memory_files` | メモリファイル（frontmatter解析済み） | `file_path` | `projects` |
| `file_history` | ファイル編集スナップショットの実体 | `id` | `sessions` |
| `file_history_snapshots` | `file-history-snapshot`レコード（trackedFileBackups） | `message_id` | `sessions` |
| `attachments` | `attachment`レコード（skill_listing/hook_success/output_style/deferred_tools_delta等） | `uuid` | `sessions` |
| `permission_modes` | `permission-mode`レコード（モード変更履歴） | `id` | `sessions` |
| `last_prompts` | `last-prompt`レコード（最終プロンプトのスナップ） | `leaf_uuid` | `sessions` |
| `ai_titles` | `ai-title`レコード（セッションごと最新値） | `session_id` | `sessions` |
| `queue_operations` | `queue-operation`レコード（バックグラウンドタスクのキュー操作） | `id` | `sessions` |

### messages / subagent_messages の主要カラム

基本メタ:
- `uuid`, `session_id`, `parent_uuid`, `type` (user/assistant/system), `role`, `model`, `timestamp`, `cwd`, `git_branch`
- `is_sidechain`, `is_meta`, `user_type`, `subtype`
- `entrypoint`, `claude_version`, `prompt_id`, `permission_mode`, `source_tool_assistant_uuid`

帰属情報（プラグイン/スキル起動の追跡）:
- `attribution_plugin`, `attribution_skill`

API識別子:
- `message_api_id` (Anthropic APIのmessage ID), `request_id`, `stop_reason`, `service_tier`

トークン使用量（usage 配下）:
- `usage_input_tokens`: 非キャッシュのfresh入力
- `usage_output_tokens`: 出力
- `usage_cache_creation_input_tokens`: キャッシュ書込（新規キャッシュ化）
- `usage_cache_read_input_tokens`: キャッシュヒット（再利用）
- `usage_cache_creation_5m`: 5分TTLキャッシュ書込内訳
- `usage_cache_creation_1h`: 1時間TTLキャッシュ書込内訳
- `usage_web_search_requests` / `usage_web_fetch_requests`: server_tool_use 内訳
- `usage_speed`, `usage_inference_geo`: モデル速度ティアと推論リージョン
- `usage_iterations`: メッセージ生成のイテレーション履歴（JSON文字列）

systemメッセージ専用（hookやローカルコマンドの実行サマリ）:
- `level` (info/suggestion等), `subtype` (stop_hook_summary/local_command等), `tool_use_id`
- `duration_ms`, `has_output`, `hook_count`, `hook_infos` (JSON配列), `hook_errors` (JSON配列)
- `prevented_continuation`, `message_count`

> **スキーマ自動マイグレーション**: 既存DBは初回実行時に `ALTER TABLE ADD COLUMN` で非破壊的に新カラムが追加される。過去メッセージの新フィールド値はNULLのまま（再エクスポートで埋まる）。新規テーブルは `CREATE TABLE IF NOT EXISTS` で安全に追加される。

### ER構造

```
projects 1──N sessions 1──N messages 1──N tool_uses
                                     1──N tool_results
                       1──N subagents 1──N subagent_messages
                       1──N file_history
                       1──N file_history_snapshots
                       1──N attachments
                       1──N permission_modes
                       1──N last_prompts
                       1──N ai_titles
                       1──N queue_operations
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
3. **トランスクリプト解析**: JSONL形式のトランスクリプトをパース（`type`フィールドで分岐）
4. **メッセージ抽出**: `user`/`assistant`/`system` をmessagesに保存
5. **ツール使用抽出**: assistantメッセージのcontent blocksから`tool_use`を抽出
6. **ツール結果抽出**: userメッセージの`tool_result`ブロック＋`toolUseResult`メタをtool_resultsに保存
7. **新規レコード抽出**: `attachment`/`permission-mode`/`last-prompt`/`file-history-snapshot`/`ai-title`/`queue-operation` を各テーブルに保存
8. **サブエージェント解析**: サブエージェントのメタデータとトランスクリプトをパース
9. **メモリ収集**: プロジェクトのmemoryディレクトリからファイルを読み取り
10. **ファイル履歴収集**: file-historyディレクトリからセッション中の編集履歴を収集
11. **SQLiteにUpsert**: 全データを書き込み

## 対応するJSONLレコードタイプ

Claude Code (v2.1.x系) の `~/.claude/projects/<encoded>/<session>.jsonl` に出現する以下のタイプを処理する:

| `type` | 格納先テーブル | 備考 |
|--------|---------------|------|
| `user` | messages (+ tool_results) | `toolUseResult`メタを別テーブル化 |
| `assistant` | messages (+ tool_uses) | `attributionPlugin/Skill`, `usage.iterations`等を保存 |
| `system` | messages | `hookInfos`/`hookErrors`/`durationMs`等hookサマリを保存 |
| `attachment` | attachments | `skill_listing`/`hook_success`/`output_style`/`deferred_tools_delta`等 |
| `permission-mode` | permission_modes | モード変更履歴（タイムスタンプ無いため出現順を sequence で保存） |
| `last-prompt` | last_prompts | `leafUuid`をキーに最終プロンプトを保存 |
| `file-history-snapshot` | file_history_snapshots | `trackedFileBackups`を構造化保存 |
| `ai-title` | ai_titles | セッションごと最新値で上書き |
| `queue-operation` | queue_operations | バックグラウンドタスクのキュー操作 |

未知のタイプは警告無くスキップされる（破壊的でない）。

## 出力

エクスポート完了後、以下を報告する:
- SQLiteファイルのパス
- 保存されたレコード数（テーブルごと）
- セッションID

## 注意事項

- 現在実行中のセッションのトランスクリプトはリアルタイムで書き込まれているため、エクスポート時点までのデータが保存される
- assistantメッセージのcontentはJSON配列として保存される（テキスト、ツール呼び出し、ツール結果などの複合構造）
- `attachments.attachment_data` / `messages.hook_infos` / `messages.usage_iterations` などはJSON文字列として保存。SQLiteの`json_*`関数で展開可能
- 大きなセッションの場合、ファイルサイズが数十MBになることがある
- プロジェクト横断のクエリが可能（例: `SELECT tool_name, COUNT(*) FROM tool_uses JOIN sessions USING(session_id) GROUP BY tool_name`）
- スキル/プラグイン起動の追跡: `SELECT attribution_skill, COUNT(*) FROM messages WHERE attribution_skill IS NOT NULL GROUP BY attribution_skill`
