#!/usr/bin/env python3
"""
Claude Code会話セッションをSQLiteにエクスポートするスクリプト。

Usage:
    python3 export.py --project-path /path/to/project
    python3 export.py --project-path /path/to/project --session-id <uuid>
    python3 export.py --project-path /path/to/project --output /path/to/output.db
"""

import argparse
import hashlib
import json
import os
import re
import sqlite3
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path


# --- Constants ---

CLAUDE_DIR = Path.home() / ".claude"
PROJECTS_DIR = CLAUDE_DIR / "projects"
EXPORTS_DIR = CLAUDE_DIR / "exports"
FILE_HISTORY_DIR = CLAUDE_DIR / "file-history"
DEFAULT_DB_PATH = EXPORTS_DIR / "conversations.db"


# --- Schema ---

SCHEMA_SQL = """
-- プロジェクト（正規化テーブル）
CREATE TABLE IF NOT EXISTS projects (
    project_path TEXT PRIMARY KEY,
    claude_dir_name TEXT,
    first_seen_at TEXT,
    last_exported_at TEXT
);

-- セッション（プロジェクトに紐づく）
CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    project_path TEXT NOT NULL,
    cwd TEXT,
    git_branch TEXT,
    claude_version TEXT,
    slug TEXT,
    first_prompt TEXT,
    summary TEXT,
    message_count INTEGER,
    created_at TEXT,
    modified_at TEXT,
    exported_at TEXT,
    FOREIGN KEY (project_path) REFERENCES projects(project_path)
);

-- メッセージ（セッションに紐づく）
CREATE TABLE IF NOT EXISTS messages (
    uuid TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    parent_uuid TEXT,
    type TEXT,
    role TEXT,
    content TEXT,
    model TEXT,
    timestamp TEXT,
    cwd TEXT,
    git_branch TEXT,
    is_sidechain INTEGER DEFAULT 0,
    is_meta INTEGER DEFAULT 0,
    user_type TEXT,
    subtype TEXT,
    entrypoint TEXT,
    claude_version TEXT,
    slug TEXT,
    prompt_id TEXT,
    permission_mode TEXT,
    source_tool_assistant_uuid TEXT,
    source_tool_use_id TEXT,
    interrupted_message_id TEXT,
    attribution_plugin TEXT,
    attribution_skill TEXT,
    attribution_mcp_server TEXT,
    attribution_mcp_tool TEXT,
    message_api_id TEXT,
    request_id TEXT,
    stop_reason TEXT,
    stop_sequence TEXT,
    stop_details TEXT,
    service_tier TEXT,
    diagnostics TEXT,
    context_management TEXT,
    is_api_error_message INTEGER,
    api_error_status INTEGER,
    usage_input_tokens INTEGER,
    usage_output_tokens INTEGER,
    usage_cache_creation_input_tokens INTEGER,
    usage_cache_read_input_tokens INTEGER,
    usage_cache_creation_5m INTEGER,
    usage_cache_creation_1h INTEGER,
    usage_web_search_requests INTEGER,
    usage_web_fetch_requests INTEGER,
    usage_speed TEXT,
    usage_inference_geo TEXT,
    usage_iterations TEXT,
    -- system タイプ用（hook 実行サマリ・ローカルコマンド出力など）
    level TEXT,
    duration_ms INTEGER,
    has_output INTEGER,
    hook_count INTEGER,
    hook_infos TEXT,
    hook_errors TEXT,
    prevented_continuation INTEGER,
    tool_use_id TEXT,
    message_count INTEGER,
    -- system api_error サブタイプ用
    error_data TEXT,
    retry_in_ms REAL,
    retry_attempt INTEGER,
    max_retries INTEGER,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);

-- ツール使用（メッセージから抽出）
CREATE TABLE IF NOT EXISTS tool_uses (
    id TEXT PRIMARY KEY,
    message_uuid TEXT NOT NULL,
    session_id TEXT NOT NULL,
    tool_name TEXT,
    tool_input TEXT,
    timestamp TEXT,
    FOREIGN KEY (message_uuid) REFERENCES messages(uuid),
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);

-- サブエージェント（セッションに紐づく）
CREATE TABLE IF NOT EXISTS subagents (
    agent_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    agent_type TEXT,
    message_count INTEGER DEFAULT 0,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);

-- サブエージェントメッセージ
CREATE TABLE IF NOT EXISTS subagent_messages (
    uuid TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    parent_uuid TEXT,
    type TEXT,
    role TEXT,
    content TEXT,
    model TEXT,
    timestamp TEXT,
    cwd TEXT,
    git_branch TEXT,
    is_sidechain INTEGER DEFAULT 0,
    is_meta INTEGER DEFAULT 0,
    user_type TEXT,
    subtype TEXT,
    entrypoint TEXT,
    claude_version TEXT,
    prompt_id TEXT,
    permission_mode TEXT,
    source_tool_assistant_uuid TEXT,
    attribution_plugin TEXT,
    attribution_skill TEXT,
    attribution_mcp_server TEXT,
    attribution_mcp_tool TEXT,
    message_api_id TEXT,
    request_id TEXT,
    stop_reason TEXT,
    stop_sequence TEXT,
    stop_details TEXT,
    service_tier TEXT,
    diagnostics TEXT,
    context_management TEXT,
    usage_input_tokens INTEGER,
    usage_output_tokens INTEGER,
    usage_cache_creation_input_tokens INTEGER,
    usage_cache_read_input_tokens INTEGER,
    usage_cache_creation_5m INTEGER,
    usage_cache_creation_1h INTEGER,
    usage_web_search_requests INTEGER,
    usage_web_fetch_requests INTEGER,
    usage_speed TEXT,
    usage_inference_geo TEXT,
    usage_iterations TEXT,
    FOREIGN KEY (agent_id) REFERENCES subagents(agent_id),
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);

-- ツール実行結果（user メッセージ内 tool_result の構造化メタ）
CREATE TABLE IF NOT EXISTS tool_results (
    tool_use_id TEXT PRIMARY KEY,
    message_uuid TEXT,
    session_id TEXT NOT NULL,
    result_type TEXT,
    file_path TEXT,
    user_modified INTEGER,
    stdout TEXT,
    stderr TEXT,
    interrupted INTEGER,
    is_image INTEGER,
    no_output_expected INTEGER,
    is_error INTEGER,
    raw_result TEXT,
    timestamp TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);

-- 添付情報（skill_listing, deferred_tools_delta など）
CREATE TABLE IF NOT EXISTS attachments (
    uuid TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    parent_uuid TEXT,
    attachment_type TEXT,
    attachment_data TEXT,
    timestamp TEXT,
    cwd TEXT,
    git_branch TEXT,
    user_type TEXT,
    entrypoint TEXT,
    claude_version TEXT,
    is_sidechain INTEGER DEFAULT 0,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);

-- パーミッションモード変更履歴
CREATE TABLE IF NOT EXISTS permission_modes (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    permission_mode TEXT,
    sequence INTEGER,
    exported_at TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);

-- 最終プロンプト記録
CREATE TABLE IF NOT EXISTS last_prompts (
    leaf_uuid TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    last_prompt TEXT,
    exported_at TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);

-- ファイル履歴スナップショット（trackedFileBackups）
CREATE TABLE IF NOT EXISTS file_history_snapshots (
    message_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    is_snapshot_update INTEGER,
    snapshot_timestamp TEXT,
    tracked_file_backups TEXT,
    raw_snapshot TEXT,
    exported_at TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);

-- AIタイトル（セッションごとの最新値）
CREATE TABLE IF NOT EXISTS ai_titles (
    session_id TEXT PRIMARY KEY,
    ai_title TEXT,
    exported_at TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);

-- バックグラウンドタスクのキュー操作
CREATE TABLE IF NOT EXISTS queue_operations (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    operation TEXT,
    content TEXT,
    timestamp TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);

-- セッション動作モード変更履歴（mode レコード。permission-mode とは別系統）
CREATE TABLE IF NOT EXISTS modes (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    mode TEXT,
    sequence INTEGER,
    exported_at TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);

-- クラウド/Webセッション連携（bridge-session レコード）
CREATE TABLE IF NOT EXISTS bridge_sessions (
    bridge_session_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    last_sequence_num INTEGER,
    exported_at TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);

-- 作成したPRへのリンク（pr-link レコード）
CREATE TABLE IF NOT EXISTS pr_links (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    pr_number INTEGER,
    pr_url TEXT,
    pr_repository TEXT,
    timestamp TEXT,
    exported_at TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);

-- メモリファイル（プロジェクトに紐づく）
CREATE TABLE IF NOT EXISTS memory_files (
    file_path TEXT PRIMARY KEY,
    project_path TEXT NOT NULL,
    file_name TEXT,
    memory_type TEXT,
    name TEXT,
    description TEXT,
    content TEXT,
    exported_at TEXT,
    FOREIGN KEY (project_path) REFERENCES projects(project_path)
);

-- ファイル編集履歴（セッションに紐づく）
CREATE TABLE IF NOT EXISTS file_history (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    file_hash TEXT,
    version INTEGER,
    file_size INTEGER,
    content BLOB,
    exported_at TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);

"""

# インデックスは migrate_schema() で新カラムを追加した後に実行する
# （旧スキーマDBに対して新カラムへのCREATE INDEXが走るとエラーになるため分離）
INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_sessions_project ON sessions(project_path);
CREATE INDEX IF NOT EXISTS idx_sessions_created ON sessions(created_at);
CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id);
CREATE INDEX IF NOT EXISTS idx_messages_type ON messages(type);
CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp);
CREATE INDEX IF NOT EXISTS idx_messages_prompt_id ON messages(prompt_id);
CREATE INDEX IF NOT EXISTS idx_tool_uses_session ON tool_uses(session_id);
CREATE INDEX IF NOT EXISTS idx_tool_uses_tool_name ON tool_uses(tool_name);
CREATE INDEX IF NOT EXISTS idx_tool_results_session ON tool_results(session_id);
CREATE INDEX IF NOT EXISTS idx_subagent_messages_agent ON subagent_messages(agent_id);
CREATE INDEX IF NOT EXISTS idx_subagent_messages_session ON subagent_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_memory_files_project ON memory_files(project_path);
CREATE INDEX IF NOT EXISTS idx_attachments_session ON attachments(session_id);
CREATE INDEX IF NOT EXISTS idx_attachments_type ON attachments(attachment_type);
CREATE INDEX IF NOT EXISTS idx_permission_modes_session ON permission_modes(session_id);
CREATE INDEX IF NOT EXISTS idx_last_prompts_session ON last_prompts(session_id);
CREATE INDEX IF NOT EXISTS idx_file_history_snapshots_session ON file_history_snapshots(session_id);
CREATE INDEX IF NOT EXISTS idx_queue_operations_session ON queue_operations(session_id);
CREATE INDEX IF NOT EXISTS idx_modes_session ON modes(session_id);
CREATE INDEX IF NOT EXISTS idx_bridge_sessions_session ON bridge_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_pr_links_session ON pr_links(session_id);
CREATE INDEX IF NOT EXISTS idx_messages_mcp_server ON messages(attribution_mcp_server);
CREATE INDEX IF NOT EXISTS idx_tool_results_result_type ON tool_results(result_type);
"""


def encode_project_path(project_path: str) -> str:
    """プロジェクトパスをClaude Codeのディレクトリ名形式にエンコード."""
    return project_path.replace("/", "-").replace("_", "-")


def find_project_dir(project_path: str) -> Path | None:
    """プロジェクトパスからClaude Codeのプロジェクトディレクトリを検索."""
    encoded = encode_project_path(project_path)
    candidate = PROJECTS_DIR / encoded
    if candidate.is_dir():
        return candidate

    # フォールバック: 部分一致で検索
    if PROJECTS_DIR.is_dir():
        for d in PROJECTS_DIR.iterdir():
            if d.is_dir() and encoded in d.name:
                return d
    return None


def find_current_session(project_dir: Path) -> tuple[str, Path] | None:
    """プロジェクトディレクトリから最新のセッションを特定.

    sessions-index.jsonは非同期更新のため最新セッションを含まないことがある。
    そのため、ディスク上のファイルのmtimeを最優先で使用する。
    """
    # ディスク上の最新.jsonlファイルを検索（最も信頼性が高い）
    jsonl_files = sorted(
        project_dir.glob("*.jsonl"),
        key=lambda f: f.stat().st_mtime,
        reverse=True,
    )
    if jsonl_files:
        session_id = jsonl_files[0].stem
        return (session_id, jsonl_files[0])

    return None


def find_session_by_id(project_dir: Path, session_id: str) -> Path | None:
    """セッションIDからトランスクリプトファイルを検索."""
    jsonl_path = project_dir / f"{session_id}.jsonl"
    if jsonl_path.exists():
        return jsonl_path
    return None


def parse_jsonl(file_path: Path) -> list[dict]:
    """JSONLファイルをパースしてレコードのリストを返す."""
    records = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                print(f"  Warning: Line {line_num} in {file_path.name} is not valid JSON, skipping", file=sys.stderr)
    return records


def extract_content_text(content) -> str:
    """メッセージのcontentからテキストを抽出（表示用）."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        texts = []
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "text":
                    texts.append(block.get("text", ""))
            elif isinstance(block, str):
                texts.append(block)
        return "\n".join(texts) if texts else json.dumps(content, ensure_ascii=False)
    return json.dumps(content, ensure_ascii=False)


def extract_tool_uses(message_record: dict) -> list[dict]:
    """assistantメッセージからtool_useブロックを抽出."""
    tool_uses = []
    msg = message_record.get("message", {})
    content = msg.get("content", [])

    if not isinstance(content, list):
        return tool_uses

    for block in content:
        if isinstance(block, dict) and block.get("type") == "tool_use":
            tool_uses.append({
                "id": block.get("id", str(uuid.uuid4())),
                "tool_name": block.get("name", "unknown"),
                "tool_input": json.dumps(block.get("input", {}), ensure_ascii=False),
            })

    return tool_uses


def parse_memory_frontmatter(content: str) -> dict:
    """メモリファイルのYAMLフロントマターをパース."""
    result = {"name": "", "description": "", "type": "", "body": content}

    match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)", content, re.DOTALL)
    if not match:
        return result

    frontmatter = match.group(1)
    result["body"] = match.group(2).strip()

    for line in frontmatter.split("\n"):
        line = line.strip()
        if line.startswith("name:"):
            result["name"] = line[5:].strip().strip('"\'')
        elif line.startswith("description:"):
            result["description"] = line[12:].strip().strip('"\'')
        elif line.startswith("type:"):
            result["type"] = line[5:].strip().strip('"\'')

    return result


def serialize_content(content) -> str:
    """メッセージのcontentをJSON文字列にシリアライズ."""
    if isinstance(content, str):
        return content
    return json.dumps(content, ensure_ascii=False)


# --- Database Operations ---

def _add_column_if_missing(conn: sqlite3.Connection, table: str, column: str, coltype: str):
    """既存テーブルにカラムを追加（存在しない場合のみ）."""
    existing = {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
    if column not in existing:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {coltype}")


def migrate_schema(conn: sqlite3.Connection):
    """既存DBのスキーマを最新版に移行（非破壊）."""
    extra_cols_messages = [
        ("is_meta", "INTEGER DEFAULT 0"),
        ("message_api_id", "TEXT"),
        ("request_id", "TEXT"),
        ("stop_reason", "TEXT"),
        ("service_tier", "TEXT"),
        ("usage_cache_creation_input_tokens", "INTEGER"),
        ("usage_cache_read_input_tokens", "INTEGER"),
        ("usage_cache_creation_5m", "INTEGER"),
        ("usage_cache_creation_1h", "INTEGER"),
        # Claude Code 2.1 系で追加されたフィールド
        ("entrypoint", "TEXT"),
        ("claude_version", "TEXT"),
        ("prompt_id", "TEXT"),
        ("permission_mode", "TEXT"),
        ("source_tool_assistant_uuid", "TEXT"),
        ("attribution_plugin", "TEXT"),
        ("attribution_skill", "TEXT"),
        ("usage_web_search_requests", "INTEGER"),
        ("usage_web_fetch_requests", "INTEGER"),
        ("usage_speed", "TEXT"),
        ("usage_inference_geo", "TEXT"),
        ("usage_iterations", "TEXT"),
        # system タイプ用
        ("level", "TEXT"),
        ("duration_ms", "INTEGER"),
        ("has_output", "INTEGER"),
        ("hook_count", "INTEGER"),
        ("hook_infos", "TEXT"),
        ("hook_errors", "TEXT"),
        ("prevented_continuation", "INTEGER"),
        ("tool_use_id", "TEXT"),
        ("message_count", "INTEGER"),
        # Claude Code 2.1.150+ で追加されたフィールド
        ("slug", "TEXT"),
        ("source_tool_use_id", "TEXT"),
        ("interrupted_message_id", "TEXT"),
        ("attribution_mcp_server", "TEXT"),
        ("attribution_mcp_tool", "TEXT"),
        ("stop_sequence", "TEXT"),
        ("stop_details", "TEXT"),
        ("diagnostics", "TEXT"),
        ("context_management", "TEXT"),
        ("is_api_error_message", "INTEGER"),
        ("api_error_status", "INTEGER"),
        # system api_error サブタイプ用
        ("error_data", "TEXT"),
        ("retry_in_ms", "REAL"),
        ("retry_attempt", "INTEGER"),
        ("max_retries", "INTEGER"),
    ]
    extra_cols_subagent = [
        ("message_api_id", "TEXT"),
        ("request_id", "TEXT"),
        ("stop_reason", "TEXT"),
        ("service_tier", "TEXT"),
        ("usage_cache_creation_input_tokens", "INTEGER"),
        ("usage_cache_read_input_tokens", "INTEGER"),
        ("usage_cache_creation_5m", "INTEGER"),
        ("usage_cache_creation_1h", "INTEGER"),
        ("cwd", "TEXT"),
        ("git_branch", "TEXT"),
        ("is_meta", "INTEGER DEFAULT 0"),
        ("user_type", "TEXT"),
        ("subtype", "TEXT"),
        ("entrypoint", "TEXT"),
        ("claude_version", "TEXT"),
        ("prompt_id", "TEXT"),
        ("permission_mode", "TEXT"),
        ("source_tool_assistant_uuid", "TEXT"),
        ("attribution_plugin", "TEXT"),
        ("attribution_skill", "TEXT"),
        ("usage_web_search_requests", "INTEGER"),
        ("usage_web_fetch_requests", "INTEGER"),
        ("usage_speed", "TEXT"),
        ("usage_inference_geo", "TEXT"),
        ("usage_iterations", "TEXT"),
        # Claude Code 2.1.150+ で追加されたフィールド
        ("attribution_mcp_server", "TEXT"),
        ("attribution_mcp_tool", "TEXT"),
        ("stop_sequence", "TEXT"),
        ("stop_details", "TEXT"),
        ("diagnostics", "TEXT"),
        ("context_management", "TEXT"),
    ]
    extra_cols_sessions = [
        ("slug", "TEXT"),
    ]
    extra_cols_tool_results = [
        ("result_type", "TEXT"),
        ("file_path", "TEXT"),
        ("user_modified", "INTEGER"),
    ]
    for col, typ in extra_cols_messages:
        _add_column_if_missing(conn, "messages", col, typ)
    for col, typ in extra_cols_subagent:
        _add_column_if_missing(conn, "subagent_messages", col, typ)
    for col, typ in extra_cols_sessions:
        _add_column_if_missing(conn, "sessions", col, typ)
    for col, typ in extra_cols_tool_results:
        _add_column_if_missing(conn, "tool_results", col, typ)


def init_db(db_path: Path) -> sqlite3.Connection:
    """SQLiteデータベースを初期化."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL")
    # インポート中はFK制約を無効化（挿入順序の依存を回避）
    conn.execute("PRAGMA foreign_keys=OFF")
    # 1. テーブル作成（CREATE TABLE IF NOT EXISTS なので既存テーブルは温存）
    conn.executescript(SCHEMA_SQL)
    # 2. 既存テーブルへの非破壊カラム追加
    migrate_schema(conn)
    # 3. インデックス作成（新カラム上のインデックスを含むため migrate 後）
    conn.executescript(INDEX_SQL)
    return conn


def upsert_project(conn: sqlite3.Connection, project_path: str, claude_dir_name: str):
    """プロジェクトをUpsert."""
    now = datetime.now(timezone.utc).isoformat()
    conn.execute("""
        INSERT INTO projects (project_path, claude_dir_name, first_seen_at, last_exported_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(project_path) DO UPDATE SET
            last_exported_at = excluded.last_exported_at
    """, (project_path, claude_dir_name, now, now))


def upsert_session(conn: sqlite3.Connection, session_data: dict):
    """セッションメタデータをUpsert."""
    conn.execute("""
        INSERT INTO sessions (session_id, project_path, cwd, git_branch, claude_version, slug,
                              first_prompt, summary, message_count, created_at, modified_at, exported_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(session_id) DO UPDATE SET
            project_path = COALESCE(NULLIF(excluded.project_path, ''), sessions.project_path),
            cwd = COALESCE(NULLIF(excluded.cwd, ''), sessions.cwd),
            git_branch = COALESCE(NULLIF(excluded.git_branch, ''), sessions.git_branch),
            claude_version = COALESCE(NULLIF(excluded.claude_version, ''), sessions.claude_version),
            slug = COALESCE(NULLIF(excluded.slug, ''), sessions.slug),
            first_prompt = COALESCE(NULLIF(excluded.first_prompt, ''), sessions.first_prompt),
            summary = COALESCE(NULLIF(excluded.summary, ''), sessions.summary),
            message_count = MAX(excluded.message_count, sessions.message_count),
            created_at = COALESCE(NULLIF(excluded.created_at, ''), sessions.created_at),
            modified_at = COALESCE(NULLIF(excluded.modified_at, ''), sessions.modified_at),
            exported_at = excluded.exported_at
    """, (
        session_data["session_id"],
        session_data.get("project_path", ""),
        session_data.get("cwd", ""),
        session_data.get("git_branch", ""),
        session_data.get("claude_version", ""),
        session_data.get("slug", ""),
        session_data.get("first_prompt", ""),
        session_data.get("summary", ""),
        session_data.get("message_count", 0),
        session_data.get("created_at", ""),
        session_data.get("modified_at", ""),
        datetime.now(timezone.utc).isoformat(),
    ))


def upsert_message(conn: sqlite3.Connection, msg: dict):
    """メッセージをUpsert."""
    conn.execute("""
        INSERT INTO messages (
            uuid, session_id, parent_uuid, type, role, content, model,
            timestamp, cwd, git_branch, is_sidechain, is_meta, user_type, subtype,
            entrypoint, claude_version, slug, prompt_id, permission_mode,
            source_tool_assistant_uuid, source_tool_use_id, interrupted_message_id,
            attribution_plugin, attribution_skill, attribution_mcp_server, attribution_mcp_tool,
            message_api_id, request_id, stop_reason, stop_sequence, stop_details, service_tier,
            diagnostics, context_management, is_api_error_message, api_error_status,
            usage_input_tokens, usage_output_tokens,
            usage_cache_creation_input_tokens, usage_cache_read_input_tokens,
            usage_cache_creation_5m, usage_cache_creation_1h,
            usage_web_search_requests, usage_web_fetch_requests,
            usage_speed, usage_inference_geo, usage_iterations,
            level, duration_ms, has_output, hook_count, hook_infos, hook_errors,
            prevented_continuation, tool_use_id, message_count,
            error_data, retry_in_ms, retry_attempt, max_retries
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?, ?)
        ON CONFLICT(uuid) DO UPDATE SET
            content = excluded.content,
            stop_reason = excluded.stop_reason,
            stop_sequence = excluded.stop_sequence,
            stop_details = excluded.stop_details,
            service_tier = excluded.service_tier,
            diagnostics = excluded.diagnostics,
            context_management = excluded.context_management,
            is_api_error_message = excluded.is_api_error_message,
            api_error_status = excluded.api_error_status,
            usage_input_tokens = excluded.usage_input_tokens,
            usage_output_tokens = excluded.usage_output_tokens,
            usage_cache_creation_input_tokens = excluded.usage_cache_creation_input_tokens,
            usage_cache_read_input_tokens = excluded.usage_cache_read_input_tokens,
            usage_cache_creation_5m = excluded.usage_cache_creation_5m,
            usage_cache_creation_1h = excluded.usage_cache_creation_1h,
            usage_web_search_requests = excluded.usage_web_search_requests,
            usage_web_fetch_requests = excluded.usage_web_fetch_requests,
            usage_speed = excluded.usage_speed,
            usage_inference_geo = excluded.usage_inference_geo,
            usage_iterations = excluded.usage_iterations,
            slug = COALESCE(excluded.slug, messages.slug),
            attribution_plugin = COALESCE(excluded.attribution_plugin, messages.attribution_plugin),
            attribution_skill = COALESCE(excluded.attribution_skill, messages.attribution_skill),
            attribution_mcp_server = COALESCE(excluded.attribution_mcp_server, messages.attribution_mcp_server),
            attribution_mcp_tool = COALESCE(excluded.attribution_mcp_tool, messages.attribution_mcp_tool),
            permission_mode = COALESCE(excluded.permission_mode, messages.permission_mode),
            hook_infos = excluded.hook_infos,
            hook_errors = excluded.hook_errors,
            hook_count = excluded.hook_count,
            error_data = excluded.error_data,
            retry_in_ms = excluded.retry_in_ms,
            retry_attempt = excluded.retry_attempt,
            max_retries = excluded.max_retries
    """, (
        msg["uuid"],
        msg["session_id"],
        msg.get("parent_uuid"),
        msg["type"],
        msg.get("role"),
        msg["content"],
        msg.get("model"),
        msg.get("timestamp"),
        msg.get("cwd"),
        msg.get("git_branch"),
        1 if msg.get("is_sidechain") else 0,
        1 if msg.get("is_meta") else 0,
        msg.get("user_type"),
        msg.get("subtype"),
        msg.get("entrypoint"),
        msg.get("claude_version"),
        msg.get("slug"),
        msg.get("prompt_id"),
        msg.get("permission_mode"),
        msg.get("source_tool_assistant_uuid"),
        msg.get("source_tool_use_id"),
        msg.get("interrupted_message_id"),
        msg.get("attribution_plugin"),
        msg.get("attribution_skill"),
        msg.get("attribution_mcp_server"),
        msg.get("attribution_mcp_tool"),
        msg.get("message_api_id"),
        msg.get("request_id"),
        msg.get("stop_reason"),
        msg.get("stop_sequence"),
        msg.get("stop_details"),
        msg.get("service_tier"),
        msg.get("diagnostics"),
        msg.get("context_management"),
        1 if msg.get("is_api_error_message") else (0 if msg.get("is_api_error_message") is False else None),
        msg.get("api_error_status"),
        msg.get("usage_input_tokens"),
        msg.get("usage_output_tokens"),
        msg.get("usage_cache_creation_input_tokens"),
        msg.get("usage_cache_read_input_tokens"),
        msg.get("usage_cache_creation_5m"),
        msg.get("usage_cache_creation_1h"),
        msg.get("usage_web_search_requests"),
        msg.get("usage_web_fetch_requests"),
        msg.get("usage_speed"),
        msg.get("usage_inference_geo"),
        msg.get("usage_iterations"),
        msg.get("level"),
        msg.get("duration_ms"),
        1 if msg.get("has_output") else (0 if msg.get("has_output") is False else None),
        msg.get("hook_count"),
        msg.get("hook_infos"),
        msg.get("hook_errors"),
        1 if msg.get("prevented_continuation") else (0 if msg.get("prevented_continuation") is False else None),
        msg.get("tool_use_id"),
        msg.get("message_count"),
        msg.get("error_data"),
        msg.get("retry_in_ms"),
        msg.get("retry_attempt"),
        msg.get("max_retries"),
    ))


def upsert_tool_use(conn: sqlite3.Connection, tool: dict):
    """ツール使用をUpsert."""
    conn.execute("""
        INSERT INTO tool_uses (id, message_uuid, session_id, tool_name, tool_input, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO NOTHING
    """, (
        tool["id"],
        tool["message_uuid"],
        tool["session_id"],
        tool["tool_name"],
        tool["tool_input"],
        tool.get("timestamp"),
    ))


def upsert_subagent(conn: sqlite3.Connection, agent: dict):
    """サブエージェントをUpsert."""
    conn.execute("""
        INSERT INTO subagents (agent_id, session_id, agent_type, message_count)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(agent_id) DO UPDATE SET
            message_count = excluded.message_count
    """, (
        agent["agent_id"],
        agent["session_id"],
        agent.get("agent_type", ""),
        agent.get("message_count", 0),
    ))


def upsert_subagent_message(conn: sqlite3.Connection, msg: dict):
    """サブエージェントメッセージをUpsert."""
    conn.execute("""
        INSERT INTO subagent_messages (
            uuid, agent_id, session_id, parent_uuid, type, role,
            content, model, timestamp, cwd, git_branch, is_sidechain, is_meta,
            user_type, subtype, entrypoint, claude_version, prompt_id, permission_mode,
            source_tool_assistant_uuid, attribution_plugin, attribution_skill,
            attribution_mcp_server, attribution_mcp_tool,
            message_api_id, request_id, stop_reason, stop_sequence, stop_details, service_tier,
            diagnostics, context_management,
            usage_input_tokens, usage_output_tokens,
            usage_cache_creation_input_tokens, usage_cache_read_input_tokens,
            usage_cache_creation_5m, usage_cache_creation_1h,
            usage_web_search_requests, usage_web_fetch_requests,
            usage_speed, usage_inference_geo, usage_iterations
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?,
                ?, ?, ?,
                ?, ?,
                ?, ?, ?, ?, ?, ?,
                ?, ?,
                ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?)
        ON CONFLICT(uuid) DO UPDATE SET
            content = excluded.content,
            usage_cache_creation_input_tokens = excluded.usage_cache_creation_input_tokens,
            usage_cache_read_input_tokens = excluded.usage_cache_read_input_tokens,
            usage_web_search_requests = excluded.usage_web_search_requests,
            usage_web_fetch_requests = excluded.usage_web_fetch_requests,
            usage_speed = excluded.usage_speed,
            usage_inference_geo = excluded.usage_inference_geo,
            usage_iterations = excluded.usage_iterations,
            stop_sequence = excluded.stop_sequence,
            stop_details = excluded.stop_details,
            diagnostics = excluded.diagnostics,
            context_management = excluded.context_management,
            attribution_plugin = COALESCE(excluded.attribution_plugin, subagent_messages.attribution_plugin),
            attribution_skill = COALESCE(excluded.attribution_skill, subagent_messages.attribution_skill),
            attribution_mcp_server = COALESCE(excluded.attribution_mcp_server, subagent_messages.attribution_mcp_server),
            attribution_mcp_tool = COALESCE(excluded.attribution_mcp_tool, subagent_messages.attribution_mcp_tool)
    """, (
        msg["uuid"],
        msg["agent_id"],
        msg["session_id"],
        msg.get("parent_uuid"),
        msg["type"],
        msg.get("role"),
        msg["content"],
        msg.get("model"),
        msg.get("timestamp"),
        msg.get("cwd"),
        msg.get("git_branch"),
        1 if msg.get("is_sidechain") else 0,
        1 if msg.get("is_meta") else 0,
        msg.get("user_type"),
        msg.get("subtype"),
        msg.get("entrypoint"),
        msg.get("claude_version"),
        msg.get("prompt_id"),
        msg.get("permission_mode"),
        msg.get("source_tool_assistant_uuid"),
        msg.get("attribution_plugin"),
        msg.get("attribution_skill"),
        msg.get("attribution_mcp_server"),
        msg.get("attribution_mcp_tool"),
        msg.get("message_api_id"),
        msg.get("request_id"),
        msg.get("stop_reason"),
        msg.get("stop_sequence"),
        msg.get("stop_details"),
        msg.get("service_tier"),
        msg.get("diagnostics"),
        msg.get("context_management"),
        msg.get("usage_input_tokens"),
        msg.get("usage_output_tokens"),
        msg.get("usage_cache_creation_input_tokens"),
        msg.get("usage_cache_read_input_tokens"),
        msg.get("usage_cache_creation_5m"),
        msg.get("usage_cache_creation_1h"),
        msg.get("usage_web_search_requests"),
        msg.get("usage_web_fetch_requests"),
        msg.get("usage_speed"),
        msg.get("usage_inference_geo"),
        msg.get("usage_iterations"),
    ))


def upsert_memory_file(conn: sqlite3.Connection, mem: dict):
    """メモリファイルをUpsert."""
    conn.execute("""
        INSERT INTO memory_files (file_path, project_path, file_name, memory_type,
                                   name, description, content, exported_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(file_path) DO UPDATE SET
            content = excluded.content,
            exported_at = excluded.exported_at
    """, (
        mem["file_path"],
        mem["project_path"],
        mem["file_name"],
        mem.get("memory_type", ""),
        mem.get("name", ""),
        mem.get("description", ""),
        mem["content"],
        datetime.now(timezone.utc).isoformat(),
    ))


def upsert_file_history(conn: sqlite3.Connection, fh: dict):
    """ファイル履歴をUpsert."""
    conn.execute("""
        INSERT INTO file_history (id, session_id, file_hash, version, file_size, content, exported_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO NOTHING
    """, (
        fh["id"],
        fh["session_id"],
        fh["file_hash"],
        fh["version"],
        fh["file_size"],
        fh.get("content"),
        datetime.now(timezone.utc).isoformat(),
    ))


def upsert_tool_result(conn: sqlite3.Connection, tr: dict):
    """ツール実行結果をUpsert (user メッセージ内の tool_result)."""
    conn.execute("""
        INSERT INTO tool_results (
            tool_use_id, message_uuid, session_id,
            result_type, file_path, user_modified,
            stdout, stderr, interrupted, is_image, no_output_expected, is_error,
            raw_result, timestamp
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(tool_use_id) DO UPDATE SET
            result_type = excluded.result_type,
            file_path = excluded.file_path,
            user_modified = excluded.user_modified,
            stdout = excluded.stdout,
            stderr = excluded.stderr,
            interrupted = excluded.interrupted,
            is_image = excluded.is_image,
            no_output_expected = excluded.no_output_expected,
            is_error = excluded.is_error,
            raw_result = excluded.raw_result
    """, (
        tr["tool_use_id"],
        tr.get("message_uuid"),
        tr["session_id"],
        tr.get("result_type"),
        tr.get("file_path"),
        _bool_to_int(tr.get("user_modified")),
        tr.get("stdout"),
        tr.get("stderr"),
        _bool_to_int(tr.get("interrupted")),
        _bool_to_int(tr.get("is_image")),
        _bool_to_int(tr.get("no_output_expected")),
        _bool_to_int(tr.get("is_error")),
        tr.get("raw_result"),
        tr.get("timestamp"),
    ))


def upsert_attachment(conn: sqlite3.Connection, att: dict):
    """添付情報をUpsert."""
    conn.execute("""
        INSERT INTO attachments (
            uuid, session_id, parent_uuid, attachment_type, attachment_data,
            timestamp, cwd, git_branch, user_type, entrypoint, claude_version, is_sidechain
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(uuid) DO UPDATE SET
            attachment_data = excluded.attachment_data
    """, (
        att["uuid"],
        att["session_id"],
        att.get("parent_uuid"),
        att.get("attachment_type"),
        att.get("attachment_data"),
        att.get("timestamp"),
        att.get("cwd"),
        att.get("git_branch"),
        att.get("user_type"),
        att.get("entrypoint"),
        att.get("claude_version"),
        1 if att.get("is_sidechain") else 0,
    ))


def upsert_permission_mode(conn: sqlite3.Connection, pm: dict):
    """パーミッションモード変更履歴をUpsert."""
    conn.execute("""
        INSERT INTO permission_modes (id, session_id, permission_mode, sequence, exported_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            permission_mode = excluded.permission_mode,
            exported_at = excluded.exported_at
    """, (
        pm["id"],
        pm["session_id"],
        pm.get("permission_mode"),
        pm.get("sequence"),
        datetime.now(timezone.utc).isoformat(),
    ))


def upsert_last_prompt(conn: sqlite3.Connection, lp: dict):
    """最終プロンプトをUpsert."""
    conn.execute("""
        INSERT INTO last_prompts (leaf_uuid, session_id, last_prompt, exported_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(leaf_uuid) DO UPDATE SET
            last_prompt = excluded.last_prompt,
            exported_at = excluded.exported_at
    """, (
        lp["leaf_uuid"],
        lp["session_id"],
        lp.get("last_prompt"),
        datetime.now(timezone.utc).isoformat(),
    ))


def upsert_file_history_snapshot(conn: sqlite3.Connection, fhs: dict):
    """ファイル履歴スナップショットをUpsert."""
    conn.execute("""
        INSERT INTO file_history_snapshots (
            message_id, session_id, is_snapshot_update,
            snapshot_timestamp, tracked_file_backups, raw_snapshot, exported_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(message_id) DO UPDATE SET
            is_snapshot_update = excluded.is_snapshot_update,
            tracked_file_backups = excluded.tracked_file_backups,
            raw_snapshot = excluded.raw_snapshot,
            exported_at = excluded.exported_at
    """, (
        fhs["message_id"],
        fhs["session_id"],
        1 if fhs.get("is_snapshot_update") else 0,
        fhs.get("snapshot_timestamp"),
        fhs.get("tracked_file_backups"),
        fhs.get("raw_snapshot"),
        datetime.now(timezone.utc).isoformat(),
    ))


def upsert_ai_title(conn: sqlite3.Connection, at: dict):
    """AIタイトルをUpsert（セッションごと最新値）."""
    conn.execute("""
        INSERT INTO ai_titles (session_id, ai_title, exported_at)
        VALUES (?, ?, ?)
        ON CONFLICT(session_id) DO UPDATE SET
            ai_title = excluded.ai_title,
            exported_at = excluded.exported_at
    """, (
        at["session_id"],
        at.get("ai_title"),
        datetime.now(timezone.utc).isoformat(),
    ))


def upsert_queue_operation(conn: sqlite3.Connection, qo: dict):
    """キュー操作をUpsert."""
    conn.execute("""
        INSERT INTO queue_operations (id, session_id, operation, content, timestamp)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(id) DO NOTHING
    """, (
        qo["id"],
        qo["session_id"],
        qo.get("operation"),
        qo.get("content"),
        qo.get("timestamp"),
    ))


def upsert_mode(conn: sqlite3.Connection, m: dict):
    """セッション動作モード変更履歴をUpsert."""
    conn.execute("""
        INSERT INTO modes (id, session_id, mode, sequence, exported_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            mode = excluded.mode,
            exported_at = excluded.exported_at
    """, (
        m["id"],
        m["session_id"],
        m.get("mode"),
        m.get("sequence"),
        datetime.now(timezone.utc).isoformat(),
    ))


def upsert_bridge_session(conn: sqlite3.Connection, bs: dict):
    """クラウド/Webセッション連携情報をUpsert."""
    conn.execute("""
        INSERT INTO bridge_sessions (bridge_session_id, session_id, last_sequence_num, exported_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(bridge_session_id) DO UPDATE SET
            last_sequence_num = excluded.last_sequence_num,
            exported_at = excluded.exported_at
    """, (
        bs["bridge_session_id"],
        bs["session_id"],
        bs.get("last_sequence_num"),
        datetime.now(timezone.utc).isoformat(),
    ))


def upsert_pr_link(conn: sqlite3.Connection, pl: dict):
    """PRリンクをUpsert."""
    conn.execute("""
        INSERT INTO pr_links (id, session_id, pr_number, pr_url, pr_repository, timestamp, exported_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            pr_url = excluded.pr_url,
            pr_repository = excluded.pr_repository,
            timestamp = excluded.timestamp,
            exported_at = excluded.exported_at
    """, (
        pl["id"],
        pl["session_id"],
        pl.get("pr_number"),
        pl.get("pr_url"),
        pl.get("pr_repository"),
        pl.get("timestamp"),
        datetime.now(timezone.utc).isoformat(),
    ))


def _bool_to_int(v):
    """True/False/Noneを1/0/Noneに変換."""
    if v is None:
        return None
    return 1 if v else 0


# --- Export Logic ---

def export_session(
    project_path: str,
    session_id: str,
    jsonl_path: Path,
    project_dir: Path,
    conn: sqlite3.Connection,
    include_memory: bool = True,
    include_file_history: bool = True,
) -> dict:
    """セッションデータをSQLiteにエクスポート. 統計情報を返す."""

    stats = {
        "messages": 0,
        "tool_uses": 0,
        "tool_results": 0,
        "subagents": 0,
        "subagent_messages": 0,
        "memory_files": 0,
        "file_history": 0,
        "attachments": 0,
        "permission_modes": 0,
        "last_prompts": 0,
        "file_history_snapshots": 0,
        "ai_titles": 0,
        "queue_operations": 0,
        "modes": 0,
        "bridge_sessions": 0,
        "pr_links": 0,
    }

    # プロジェクトをUpsert
    upsert_project(conn, project_path, project_dir.name)

    print(f"Parsing transcript: {jsonl_path.name}")
    records = parse_jsonl(jsonl_path)

    # --- セッションメタデータ ---
    session_meta = {
        "session_id": session_id,
        "project_path": project_path,
        "cwd": "",
        "git_branch": "",
        "claude_version": "",
        "slug": "",
        "first_prompt": "",
        "summary": "",
        "message_count": 0,
        "created_at": "",
        "modified_at": "",
    }

    # sessions-index.json からメタデータを補完
    index_file = project_dir / "sessions-index.json"
    if index_file.exists():
        try:
            with open(index_file, "r") as f:
                index = json.load(f)
            for entry in index.get("entries", []):
                if entry.get("sessionId") == session_id:
                    session_meta["first_prompt"] = entry.get("firstPrompt", "")
                    session_meta["summary"] = entry.get("summary", "")
                    session_meta["message_count"] = entry.get("messageCount", 0)
                    session_meta["created_at"] = entry.get("created", "")
                    session_meta["modified_at"] = entry.get("modified", "")
                    session_meta["git_branch"] = entry.get("gitBranch", "")
                    session_meta["project_path"] = entry.get("projectPath", project_path)
                    break
        except (json.JSONDecodeError, KeyError):
            pass

    # セッションを先にUpsert（外部キー制約のため）
    upsert_session(conn, session_meta)

    # --- メッセージ・新規レコードタイプ処理 ---
    permission_mode_seq = 0
    mode_seq = 0

    for rec in records:
        rec_type = rec.get("type")

        # セッションメタデータの補完（あらゆるレコードから）
        if not session_meta["cwd"] and rec.get("cwd"):
            session_meta["cwd"] = rec["cwd"]
        if not session_meta["git_branch"] and rec.get("gitBranch"):
            session_meta["git_branch"] = rec["gitBranch"]
        if not session_meta["claude_version"] and rec.get("version"):
            session_meta["claude_version"] = rec["version"]
        # slug はセッション単位で一定の人間可読エイリアス（任意レコードに付随）
        if not session_meta["slug"] and rec.get("slug"):
            session_meta["slug"] = rec["slug"]

        # --- 新規レコードタイプの処理 ---
        if rec_type == "mode":
            mode_seq += 1
            mode_id = f"{session_id}:{mode_seq}:{rec.get('mode','')}"
            upsert_mode(conn, {
                "id": mode_id,
                "session_id": session_id,
                "mode": rec.get("mode"),
                "sequence": mode_seq,
            })
            stats["modes"] += 1
            continue

        if rec_type == "bridge-session":
            bsid = rec.get("bridgeSessionId")
            if bsid:
                upsert_bridge_session(conn, {
                    "bridge_session_id": bsid,
                    "session_id": session_id,
                    "last_sequence_num": rec.get("lastSequenceNum"),
                })
                stats["bridge_sessions"] += 1
            continue

        if rec_type == "pr-link":
            pr_number = rec.get("prNumber")
            pl_id = f"{session_id}:{pr_number}" if pr_number is not None else f"{session_id}:{uuid.uuid4()}"
            upsert_pr_link(conn, {
                "id": pl_id,
                "session_id": session_id,
                "pr_number": pr_number,
                "pr_url": rec.get("prUrl"),
                "pr_repository": rec.get("prRepository"),
                "timestamp": rec.get("timestamp"),
            })
            stats["pr_links"] += 1
            continue

        if rec_type == "permission-mode":
            permission_mode_seq += 1
            pm_id = f"{session_id}:{permission_mode_seq}:{rec.get('permissionMode','')}"
            upsert_permission_mode(conn, {
                "id": pm_id,
                "session_id": session_id,
                "permission_mode": rec.get("permissionMode"),
                "sequence": permission_mode_seq,
            })
            stats["permission_modes"] += 1
            continue

        if rec_type == "last-prompt":
            upsert_last_prompt(conn, {
                "leaf_uuid": rec.get("leafUuid") or str(uuid.uuid4()),
                "session_id": session_id,
                "last_prompt": rec.get("lastPrompt"),
            })
            stats["last_prompts"] += 1
            continue

        if rec_type == "ai-title":
            upsert_ai_title(conn, {
                "session_id": session_id,
                "ai_title": rec.get("aiTitle"),
            })
            stats["ai_titles"] += 1
            continue

        if rec_type == "file-history-snapshot":
            snap = rec.get("snapshot") or {}
            msg_id = rec.get("messageId") or snap.get("messageId") or str(uuid.uuid4())
            upsert_file_history_snapshot(conn, {
                "message_id": msg_id,
                "session_id": session_id,
                "is_snapshot_update": rec.get("isSnapshotUpdate", False),
                "snapshot_timestamp": snap.get("timestamp"),
                "tracked_file_backups": json.dumps(
                    snap.get("trackedFileBackups", {}), ensure_ascii=False
                ),
                "raw_snapshot": json.dumps(snap, ensure_ascii=False),
            })
            stats["file_history_snapshots"] += 1
            continue

        if rec_type == "queue-operation":
            # idは timestamp+content のhashで安定化
            qo_key = f"{rec.get('timestamp','')}|{rec.get('operation','')}|{rec.get('content','')}"
            qo_id = hashlib.sha256(qo_key.encode("utf-8")).hexdigest()[:24]
            upsert_queue_operation(conn, {
                "id": f"{session_id}:{qo_id}",
                "session_id": session_id,
                "operation": rec.get("operation"),
                "content": rec.get("content"),
                "timestamp": rec.get("timestamp"),
            })
            stats["queue_operations"] += 1
            continue

        if rec_type == "attachment":
            attachment = rec.get("attachment") or {}
            upsert_attachment(conn, {
                "uuid": rec.get("uuid") or str(uuid.uuid4()),
                "session_id": session_id,
                "parent_uuid": rec.get("parentUuid"),
                "attachment_type": attachment.get("type"),
                "attachment_data": json.dumps(attachment, ensure_ascii=False),
                "timestamp": rec.get("timestamp"),
                "cwd": rec.get("cwd"),
                "git_branch": rec.get("gitBranch"),
                "user_type": rec.get("userType"),
                "entrypoint": rec.get("entrypoint"),
                "claude_version": rec.get("version"),
                "is_sidechain": rec.get("isSidechain", False),
            })
            stats["attachments"] += 1
            continue

        # --- メッセージ系（user / assistant / system） ---
        if rec_type not in ("user", "assistant", "system"):
            continue

        msg_data = rec.get("message", {})
        msg_content = msg_data.get("content", rec.get("content", ""))
        usage = msg_data.get("usage", {}) or {}
        cache_creation = usage.get("cache_creation") or {}
        server_tool = usage.get("server_tool_use") or {}
        iterations = usage.get("iterations")
        diagnostics = msg_data.get("diagnostics")
        context_management = msg_data.get("context_management")
        stop_details = msg_data.get("stop_details")
        # system api_error サブタイプの error は dict 構造
        error_obj = rec.get("error")

        msg_uuid = rec.get("uuid") or str(uuid.uuid4())

        msg = {
            "uuid": msg_uuid,
            "session_id": session_id,
            "parent_uuid": rec.get("parentUuid"),
            "type": rec_type,
            "role": msg_data.get("role", rec_type),
            "content": serialize_content(msg_content),
            "model": msg_data.get("model"),
            "timestamp": rec.get("timestamp"),
            "cwd": rec.get("cwd"),
            "git_branch": rec.get("gitBranch"),
            "is_sidechain": rec.get("isSidechain", False),
            "is_meta": rec.get("isMeta", False),
            "user_type": rec.get("userType"),
            "subtype": rec.get("subtype"),
            "entrypoint": rec.get("entrypoint"),
            "claude_version": rec.get("version"),
            "slug": rec.get("slug"),
            "prompt_id": rec.get("promptId"),
            "permission_mode": rec.get("permissionMode"),
            "source_tool_assistant_uuid": rec.get("sourceToolAssistantUUID"),
            "source_tool_use_id": rec.get("sourceToolUseID"),
            "interrupted_message_id": rec.get("interruptedMessageId"),
            "attribution_plugin": rec.get("attributionPlugin"),
            "attribution_skill": rec.get("attributionSkill"),
            "attribution_mcp_server": rec.get("attributionMcpServer"),
            "attribution_mcp_tool": rec.get("attributionMcpTool"),
            "message_api_id": msg_data.get("id"),
            "request_id": rec.get("requestId"),
            "stop_reason": msg_data.get("stop_reason") or rec.get("stopReason"),
            "stop_sequence": msg_data.get("stop_sequence"),
            "stop_details": json.dumps(stop_details, ensure_ascii=False) if stop_details is not None else None,
            "service_tier": usage.get("service_tier"),
            "diagnostics": json.dumps(diagnostics, ensure_ascii=False) if diagnostics is not None else None,
            "context_management": json.dumps(context_management, ensure_ascii=False) if context_management is not None else None,
            "is_api_error_message": rec.get("isApiErrorMessage"),
            "api_error_status": rec.get("apiErrorStatus"),
            "usage_input_tokens": usage.get("input_tokens"),
            "usage_output_tokens": usage.get("output_tokens"),
            "usage_cache_creation_input_tokens": usage.get("cache_creation_input_tokens"),
            "usage_cache_read_input_tokens": usage.get("cache_read_input_tokens"),
            "usage_cache_creation_5m": cache_creation.get("ephemeral_5m_input_tokens"),
            "usage_cache_creation_1h": cache_creation.get("ephemeral_1h_input_tokens"),
            "usage_web_search_requests": server_tool.get("web_search_requests"),
            "usage_web_fetch_requests": server_tool.get("web_fetch_requests"),
            "usage_speed": usage.get("speed"),
            "usage_inference_geo": usage.get("inference_geo"),
            "usage_iterations": json.dumps(iterations, ensure_ascii=False) if iterations is not None else None,
            # system タイプ用フィールド
            "level": rec.get("level"),
            "duration_ms": rec.get("durationMs"),
            "has_output": rec.get("hasOutput"),
            "hook_count": rec.get("hookCount"),
            "hook_infos": json.dumps(rec.get("hookInfos"), ensure_ascii=False) if rec.get("hookInfos") is not None else None,
            "hook_errors": json.dumps(rec.get("hookErrors"), ensure_ascii=False) if rec.get("hookErrors") is not None else None,
            "prevented_continuation": rec.get("preventedContinuation"),
            "tool_use_id": rec.get("toolUseID"),
            "message_count": rec.get("messageCount"),
            # system api_error サブタイプ用
            "error_data": json.dumps(error_obj, ensure_ascii=False) if error_obj is not None else None,
            "retry_in_ms": rec.get("retryInMs"),
            "retry_attempt": rec.get("retryAttempt"),
            "max_retries": rec.get("maxRetries"),
        }

        upsert_message(conn, msg)
        stats["messages"] += 1

        # assistant: ツール使用の抽出
        if rec_type == "assistant":
            tool_uses = extract_tool_uses(rec)
            for tu in tool_uses:
                tu["message_uuid"] = msg_uuid
                tu["session_id"] = session_id
                tu["timestamp"] = rec.get("timestamp")
                upsert_tool_use(conn, tu)
                stats["tool_uses"] += 1

        # user: tool_result の抽出（messageのcontentブロック + toolUseResultメタ）
        if rec_type == "user":
            tu_result_raw = rec.get("toolUseResult")
            # toolUseResult は dict (構造化) または str (シンプル出力) の両形態がある
            if isinstance(tu_result_raw, dict):
                tu_result_meta = tu_result_raw
                raw_result_json = json.dumps(tu_result_raw, ensure_ascii=False)
            elif isinstance(tu_result_raw, str):
                tu_result_meta = {"stdout": tu_result_raw}
                raw_result_json = tu_result_raw
            else:
                tu_result_meta = {}
                raw_result_json = None

            # filePath は直下、または file オブジェクト配下（Read結果など）に存在しうる
            file_obj = tu_result_meta.get("file")
            file_path = tu_result_meta.get("filePath")
            if not file_path and isinstance(file_obj, dict):
                file_path = file_obj.get("filePath")

            content = msg_data.get("content") if isinstance(msg_data, dict) else None
            if isinstance(content, list):
                for block in content:
                    if not isinstance(block, dict):
                        continue
                    if block.get("type") != "tool_result":
                        continue
                    tu_id = block.get("tool_use_id") or block.get("id")
                    if not tu_id:
                        continue
                    upsert_tool_result(conn, {
                        "tool_use_id": tu_id,
                        "message_uuid": msg_uuid,
                        "session_id": session_id,
                        "result_type": tu_result_meta.get("type"),
                        "file_path": file_path,
                        "user_modified": tu_result_meta.get("userModified"),
                        "stdout": tu_result_meta.get("stdout"),
                        "stderr": tu_result_meta.get("stderr"),
                        "interrupted": tu_result_meta.get("interrupted"),
                        "is_image": tu_result_meta.get("isImage"),
                        "no_output_expected": tu_result_meta.get("noOutputExpected"),
                        "is_error": block.get("is_error"),
                        "raw_result": raw_result_json,
                        "timestamp": rec.get("timestamp"),
                    })
                    stats["tool_results"] += 1

    # メッセージ数を更新
    if not session_meta["message_count"]:
        session_meta["message_count"] = stats["messages"]

    upsert_session(conn, session_meta)

    # --- サブエージェント処理 ---
    subagents_dir = project_dir / session_id / "subagents"
    if subagents_dir.is_dir():
        print(f"Processing subagents: {subagents_dir}")
        meta_files = sorted(subagents_dir.glob("agent-*.meta.json"))

        for meta_file in meta_files:
            agent_id = meta_file.stem.replace(".meta", "")
            agent_jsonl = subagents_dir / f"{agent_id}.jsonl"

            # メタデータ読み取り
            agent_type = ""
            try:
                with open(meta_file, "r") as f:
                    meta = json.load(f)
                    agent_type = meta.get("agentType", "")
            except (json.JSONDecodeError, KeyError):
                pass

            # サブエージェントのトランスクリプト
            agent_msg_count = 0
            if agent_jsonl.exists():
                agent_records = parse_jsonl(agent_jsonl)
                agent_messages = [r for r in agent_records if r.get("type") in ("user", "assistant", "system")]

                for rec in agent_messages:
                    msg_data = rec.get("message", {})
                    msg_content = msg_data.get("content", rec.get("content", ""))
                    usage = msg_data.get("usage", {}) or {}
                    cache_creation = usage.get("cache_creation") or {}
                    server_tool = usage.get("server_tool_use") or {}
                    iterations = usage.get("iterations")
                    diagnostics = msg_data.get("diagnostics")
                    context_management = msg_data.get("context_management")
                    stop_details = msg_data.get("stop_details")

                    sa_msg = {
                        "uuid": rec.get("uuid", str(uuid.uuid4())),
                        "agent_id": agent_id,
                        "session_id": session_id,
                        "parent_uuid": rec.get("parentUuid"),
                        "type": rec["type"],
                        "role": msg_data.get("role", rec["type"]),
                        "content": serialize_content(msg_content),
                        "model": msg_data.get("model"),
                        "timestamp": rec.get("timestamp"),
                        "cwd": rec.get("cwd"),
                        "git_branch": rec.get("gitBranch"),
                        "is_sidechain": rec.get("isSidechain", False),
                        "is_meta": rec.get("isMeta", False),
                        "user_type": rec.get("userType"),
                        "subtype": rec.get("subtype"),
                        "entrypoint": rec.get("entrypoint"),
                        "claude_version": rec.get("version"),
                        "prompt_id": rec.get("promptId"),
                        "permission_mode": rec.get("permissionMode"),
                        "source_tool_assistant_uuid": rec.get("sourceToolAssistantUUID"),
                        "attribution_plugin": rec.get("attributionPlugin"),
                        "attribution_skill": rec.get("attributionSkill"),
                        "attribution_mcp_server": rec.get("attributionMcpServer"),
                        "attribution_mcp_tool": rec.get("attributionMcpTool"),
                        "message_api_id": msg_data.get("id"),
                        "request_id": rec.get("requestId"),
                        "stop_reason": msg_data.get("stop_reason"),
                        "stop_sequence": msg_data.get("stop_sequence"),
                        "stop_details": json.dumps(stop_details, ensure_ascii=False) if stop_details is not None else None,
                        "service_tier": usage.get("service_tier"),
                        "diagnostics": json.dumps(diagnostics, ensure_ascii=False) if diagnostics is not None else None,
                        "context_management": json.dumps(context_management, ensure_ascii=False) if context_management is not None else None,
                        "usage_input_tokens": usage.get("input_tokens"),
                        "usage_output_tokens": usage.get("output_tokens"),
                        "usage_cache_creation_input_tokens": usage.get("cache_creation_input_tokens"),
                        "usage_cache_read_input_tokens": usage.get("cache_read_input_tokens"),
                        "usage_cache_creation_5m": cache_creation.get("ephemeral_5m_input_tokens"),
                        "usage_cache_creation_1h": cache_creation.get("ephemeral_1h_input_tokens"),
                        "usage_web_search_requests": server_tool.get("web_search_requests"),
                        "usage_web_fetch_requests": server_tool.get("web_fetch_requests"),
                        "usage_speed": usage.get("speed"),
                        "usage_inference_geo": usage.get("inference_geo"),
                        "usage_iterations": json.dumps(iterations, ensure_ascii=False) if iterations is not None else None,
                    }
                    upsert_subagent_message(conn, sa_msg)
                    agent_msg_count += 1
                    stats["subagent_messages"] += 1

            upsert_subagent(conn, {
                "agent_id": agent_id,
                "session_id": session_id,
                "agent_type": agent_type,
                "message_count": agent_msg_count,
            })
            stats["subagents"] += 1

    # --- メモリファイル ---
    if include_memory:
        memory_dir = project_dir / "memory"
        if memory_dir.is_dir():
            print(f"Processing memory files: {memory_dir}")
            for md_file in sorted(memory_dir.glob("*.md")):
                if md_file.name == "MEMORY.md":
                    # MEMORY.mdはインデックスファイルなので、そのまま保存
                    content = md_file.read_text(encoding="utf-8")
                    upsert_memory_file(conn, {
                        "file_path": str(md_file),
                        "project_path": project_path,
                        "file_name": md_file.name,
                        "memory_type": "index",
                        "name": "MEMORY",
                        "description": "Memory index file",
                        "content": content,
                    })
                else:
                    content = md_file.read_text(encoding="utf-8")
                    parsed = parse_memory_frontmatter(content)
                    upsert_memory_file(conn, {
                        "file_path": str(md_file),
                        "project_path": project_path,
                        "file_name": md_file.name,
                        "memory_type": parsed["type"],
                        "name": parsed["name"],
                        "description": parsed["description"],
                        "content": content,
                    })
                stats["memory_files"] += 1

    # --- ファイル編集履歴 ---
    if include_file_history:
        fh_dir = FILE_HISTORY_DIR / session_id
        if fh_dir.is_dir():
            print(f"Processing file history: {fh_dir}")
            for fh_file in sorted(fh_dir.iterdir()):
                if fh_file.is_file():
                    # ファイル名形式: <hash>@v<version>
                    match = re.match(r"^(.+)@v(\d+)$", fh_file.name)
                    if match:
                        file_hash = match.group(1)
                        version = int(match.group(2))
                        file_size = fh_file.stat().st_size

                        # テキストファイルの場合はcontentも保存、バイナリの場合はスキップ
                        content = None
                        try:
                            content = fh_file.read_bytes()
                            # テキストとしてデコード可能か確認
                            content.decode("utf-8")
                        except (UnicodeDecodeError, OSError):
                            pass  # バイナリファイルはBLOBとして保存

                        upsert_file_history(conn, {
                            "id": f"{session_id}/{fh_file.name}",
                            "session_id": session_id,
                            "file_hash": file_hash,
                            "version": version,
                            "file_size": file_size,
                            "content": content,
                        })
                        stats["file_history"] += 1

    conn.commit()
    return stats


def main():
    parser = argparse.ArgumentParser(
        description="Claude Code会話セッションをSQLiteにエクスポート"
    )
    parser.add_argument(
        "--project-path",
        required=True,
        help="プロジェクトのパス（cwd）",
    )
    parser.add_argument(
        "--session-id",
        default=None,
        help="エクスポートするセッションID（省略時は最新セッション）",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="SQLiteファイルの出力パス（省略時は ~/.claude/exports/ に保存）",
    )
    parser.add_argument(
        "--no-memory",
        action="store_true",
        help="メモリファイルを含めない",
    )
    parser.add_argument(
        "--no-file-history",
        action="store_true",
        help="ファイル編集履歴を含めない",
    )
    args = parser.parse_args()

    project_path = os.path.abspath(args.project_path)
    print(f"Project: {project_path}")

    # プロジェクトディレクトリの検索
    project_dir = find_project_dir(project_path)
    if not project_dir:
        print(f"Error: Project directory not found for {project_path}", file=sys.stderr)
        print(f"  Searched in: {PROJECTS_DIR}", file=sys.stderr)
        sys.exit(1)
    print(f"Project dir: {project_dir}")

    # セッションの特定
    if args.session_id:
        session_id = args.session_id
        jsonl_path = find_session_by_id(project_dir, session_id)
        if not jsonl_path:
            print(f"Error: Session {session_id} not found in {project_dir}", file=sys.stderr)
            sys.exit(1)
    else:
        result = find_current_session(project_dir)
        if not result:
            print(f"Error: No sessions found in {project_dir}", file=sys.stderr)
            sys.exit(1)
        session_id, jsonl_path = result

    print(f"Session ID: {session_id}")
    print(f"Transcript: {jsonl_path}")

    # 出力パスの決定
    if args.output:
        db_path = Path(args.output)
    else:
        db_path = DEFAULT_DB_PATH

    print(f"Output: {db_path}")

    # エクスポート実行
    conn = init_db(db_path)
    try:
        stats = export_session(
            project_path=project_path,
            session_id=session_id,
            jsonl_path=jsonl_path,
            project_dir=project_dir,
            conn=conn,
            include_memory=not args.no_memory,
            include_file_history=not args.no_file_history,
        )
    finally:
        conn.close()

    # 結果の表示
    print("\n--- Export Complete ---")
    print(f"Database: {db_path}")
    print(f"Session:  {session_id}")
    print(f"Records:")
    for table, count in stats.items():
        print(f"  {table}: {count}")

    db_size = db_path.stat().st_size
    if db_size >= 1024 * 1024:
        print(f"File size: {db_size / 1024 / 1024:.1f} MB")
    else:
        print(f"File size: {db_size / 1024:.1f} KB")


if __name__ == "__main__":
    main()
