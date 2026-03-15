#!/usr/bin/env python3
"""
Claude Code会話セッションをSQLiteにエクスポートするスクリプト。

Usage:
    python3 export.py --project-path /path/to/project
    python3 export.py --project-path /path/to/project --session-id <uuid>
    python3 export.py --project-path /path/to/project --output /path/to/output.db
"""

import argparse
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
    user_type TEXT,
    subtype TEXT,
    usage_input_tokens INTEGER,
    usage_output_tokens INTEGER,
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
    is_sidechain INTEGER DEFAULT 0,
    usage_input_tokens INTEGER,
    usage_output_tokens INTEGER,
    FOREIGN KEY (agent_id) REFERENCES subagents(agent_id),
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

-- インデックス
CREATE INDEX IF NOT EXISTS idx_sessions_project ON sessions(project_path);
CREATE INDEX IF NOT EXISTS idx_sessions_created ON sessions(created_at);
CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id);
CREATE INDEX IF NOT EXISTS idx_messages_type ON messages(type);
CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp);
CREATE INDEX IF NOT EXISTS idx_tool_uses_session ON tool_uses(session_id);
CREATE INDEX IF NOT EXISTS idx_tool_uses_tool_name ON tool_uses(tool_name);
CREATE INDEX IF NOT EXISTS idx_subagent_messages_agent ON subagent_messages(agent_id);
CREATE INDEX IF NOT EXISTS idx_subagent_messages_session ON subagent_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_memory_files_project ON memory_files(project_path);
"""


def encode_project_path(project_path: str) -> str:
    """プロジェクトパスをClaude Codeのディレクトリ名形式にエンコード."""
    return project_path.replace("/", "-")


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

def init_db(db_path: Path) -> sqlite3.Connection:
    """SQLiteデータベースを初期化."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL")
    # インポート中はFK制約を無効化（挿入順序の依存を回避）
    conn.execute("PRAGMA foreign_keys=OFF")
    conn.executescript(SCHEMA_SQL)
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
        INSERT INTO sessions (session_id, project_path, cwd, git_branch, claude_version,
                              first_prompt, summary, message_count, created_at, modified_at, exported_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(session_id) DO UPDATE SET
            project_path = COALESCE(NULLIF(excluded.project_path, ''), sessions.project_path),
            cwd = COALESCE(NULLIF(excluded.cwd, ''), sessions.cwd),
            git_branch = COALESCE(NULLIF(excluded.git_branch, ''), sessions.git_branch),
            claude_version = COALESCE(NULLIF(excluded.claude_version, ''), sessions.claude_version),
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
        INSERT INTO messages (uuid, session_id, parent_uuid, type, role, content, model,
                              timestamp, cwd, git_branch, is_sidechain, user_type, subtype,
                              usage_input_tokens, usage_output_tokens)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(uuid) DO UPDATE SET
            content = excluded.content,
            usage_input_tokens = excluded.usage_input_tokens,
            usage_output_tokens = excluded.usage_output_tokens
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
        msg.get("user_type"),
        msg.get("subtype"),
        msg.get("usage_input_tokens"),
        msg.get("usage_output_tokens"),
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
        INSERT INTO subagent_messages (uuid, agent_id, session_id, parent_uuid, type, role,
                                        content, model, timestamp, is_sidechain,
                                        usage_input_tokens, usage_output_tokens)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(uuid) DO UPDATE SET
            content = excluded.content
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
        1 if msg.get("is_sidechain") else 0,
        msg.get("usage_input_tokens"),
        msg.get("usage_output_tokens"),
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
        "subagents": 0,
        "subagent_messages": 0,
        "memory_files": 0,
        "file_history": 0,
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

    # --- メッセージ処理 ---
    message_records = [r for r in records if r.get("type") in ("user", "assistant", "system")]

    for rec in message_records:
        # セッションメタデータの補完（最初のレコードから）
        if not session_meta["cwd"] and rec.get("cwd"):
            session_meta["cwd"] = rec["cwd"]
        if not session_meta["git_branch"] and rec.get("gitBranch"):
            session_meta["git_branch"] = rec["gitBranch"]
        if not session_meta["claude_version"] and rec.get("version"):
            session_meta["claude_version"] = rec["version"]

        msg_data = rec.get("message", {})
        msg_content = msg_data.get("content", rec.get("content", ""))
        usage = msg_data.get("usage", {})

        msg = {
            "uuid": rec.get("uuid", str(uuid.uuid4())),
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
            "user_type": rec.get("userType"),
            "subtype": rec.get("subtype"),
            "usage_input_tokens": usage.get("input_tokens"),
            "usage_output_tokens": usage.get("output_tokens"),
        }

        upsert_message(conn, msg)
        stats["messages"] += 1

        # ツール使用の抽出
        if rec["type"] == "assistant":
            tool_uses = extract_tool_uses(rec)
            for tu in tool_uses:
                tu["message_uuid"] = msg["uuid"]
                tu["session_id"] = session_id
                tu["timestamp"] = rec.get("timestamp")
                upsert_tool_use(conn, tu)
                stats["tool_uses"] += 1

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
                    usage = msg_data.get("usage", {})

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
                        "is_sidechain": rec.get("isSidechain", False),
                        "usage_input_tokens": usage.get("input_tokens"),
                        "usage_output_tokens": usage.get("output_tokens"),
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
