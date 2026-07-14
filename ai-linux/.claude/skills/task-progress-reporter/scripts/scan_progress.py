#!/usr/bin/env python3
"""task-starter プロジェクトの todos/ を走査し、各タスクの進捗シグナルをJSONで出力する。

進捗の最終的な分類・グルーピング・推奨順序付けはモデル側の判断に委ねる。
このスクリプトの役割は「判定に必要な生シグナルを、複数ソースから漏れなく機械的に集める」こと。

集めるシグナル（複数シグナル統合の材料）:
- frontmatter: id / estimated_time / depends_on / parallel_group / priority / parallelizable
- 受け入れ条件・作業内容のチェックボックス進捗（checked / total）
- logs/NNN-{task}/ 配下の commit ログ有無・その他ファイル有無
- 上記から導出した暫定ステータス（done / in_progress / not_started）と、シグナル矛盾フラグ

Markdown(.md) タスクを主対象とする。HTML(.html) プロジェクトはベストエフォートで検出し、
frontmatter 相当が取れない場合は needs_manual_review=true を立てて呼び出し側に直接確認を促す。
"""

import argparse
import json
import re
import sys
from pathlib import Path

# 番号帯の境界。0xx=メインタスク、1xx=申し送り（task-starter/performer の番号規約）
HANDOVER_BAND_START = 100

TASK_DIR_RE = re.compile(r"^(\d{3})-(.+)$")
CHECKBOX_RE = re.compile(r"^\s*[-*]\s+\[( |x|X)\]")
SECTION_RE = re.compile(r"^#{1,6}\s+(.+?)\s*$")
# logs 配下のコミットログ命名: commit-YYYYmmddHHMMSS-title.txt
COMMIT_LOG_RE = re.compile(r"^commit-.*\.txt$")


def find_todos_dir(start: Path) -> Path | None:
    """指定パスから todos/ ディレクトリを特定する。

    優先順:
    1. start 自身が todos/ ならそれ
    2. start 直下に todos/ があればそれ（プロジェクトルート指定）
    3. start 配下を浅い順に探索して最初に見つかった todos/
    """
    if start.name == "todos" and start.is_dir():
        return start
    direct = start / "todos"
    if direct.is_dir():
        return direct
    candidates = sorted(start.glob("**/todos"), key=lambda p: len(p.parts))
    for c in candidates:
        if c.is_dir():
            return c
    return None


def parse_frontmatter(text: str) -> dict:
    """先頭の --- ... --- ブロックから既知キーを抽出する（PyYAML非依存）。"""
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    block = text[3:end]
    meta: dict = {}
    for line in block.splitlines():
        if ":" not in line:
            continue
        key, _, raw = line.partition(":")
        key = key.strip()
        val = raw.strip()
        if key not in {
            "id",
            "estimated_time",
            "depends_on",
            "parallel_group",
            "priority",
            "parallelizable",
        }:
            continue
        meta[key] = _coerce_value(key, val)
    return meta


def _coerce_value(key: str, val: str):
    # インラインコメント除去（リスト/クォート外の # 以降）
    val = _strip_inline_comment(val)
    if key == "depends_on":
        inner = val.strip().lstrip("[").rstrip("]").strip()
        if not inner:
            return []
        return [item.strip().strip("\"'") for item in inner.split(",") if item.strip()]
    if key == "parallelizable":
        return val.lower() in {"true", "yes", "1"}
    cleaned = val.strip().strip("\"'")
    # YAML の null 相当（null / ~ / 空）は None に正規化
    if cleaned.lower() in {"null", "~", ""}:
        return None
    return cleaned


def _strip_inline_comment(val: str) -> str:
    in_quote = None
    for i, ch in enumerate(val):
        if ch in "\"'":
            in_quote = None if in_quote == ch else (in_quote or ch)
        elif ch == "#" and in_quote is None:
            return val[:i].strip()
    return val.strip()


def count_section_checkboxes(text: str, section_names: list[str]) -> tuple[int, int]:
    """指定見出しセクション内のチェックボックス (checked, total) を数える。"""
    lines = text.splitlines()
    checked = total = 0
    active = False
    section_level = 0
    for line in lines:
        m = SECTION_RE.match(line)
        if m:
            level = len(m.group(0)) - len(m.group(0).lstrip("#"))
            heading = m.group(1)
            if active and level <= section_level:
                active = False
            if any(name in heading for name in section_names):
                active = True
                section_level = level
            continue
        if not active:
            continue
        cb = CHECKBOX_RE.match(line)
        if cb:
            total += 1
            if cb.group(1).lower() == "x":
                checked += 1
    return checked, total


def scan_logs(logs_dir: Path, task_id: str) -> dict:
    """logs/NNN-{task}/ の中身を調べ、コミットログ有無と他ファイル有無を返す。"""
    info = {"commit_log_count": 0, "other_file_count": 0, "exists": False}
    if not logs_dir or not logs_dir.is_dir():
        return info
    task_log_dir = logs_dir / task_id
    if not task_log_dir.is_dir():
        return info
    info["exists"] = True
    for f in task_log_dir.iterdir():
        if not f.is_file():
            continue
        if COMMIT_LOG_RE.match(f.name):
            info["commit_log_count"] += 1
        else:
            info["other_file_count"] += 1
    return info


def derive_status(accept: tuple[int, int], work: tuple[int, int], logs: dict) -> tuple[str, list[str]]:
    """複数シグナルを統合して暫定ステータスと注記（矛盾等）を導出する。

    判定ルール（堅牢性のため受け入れ条件を主、コミットログを補強シグナルとして扱う）:
    - done:        受け入れ条件が全て[x]、または（コミットログあり and 受け入れに未チェックが無い）
    - not_started: いかなる完了痕跡も無い（チェック0・コミットログ無し・ログdir空/不在）
    - in_progress: 上記以外（一部チェック済み、ログはあるが受け入れ未充足 等）
    """
    a_checked, a_total = accept
    w_checked, w_total = work
    has_commit = logs["commit_log_count"] > 0
    has_log_activity = logs["exists"] and (has_commit or logs["other_file_count"] > 0)
    notes: list[str] = []

    accept_complete = a_total > 0 and a_checked == a_total
    accept_has_unchecked = a_total > 0 and a_checked < a_total

    if accept_complete or (has_commit and not accept_has_unchecked):
        status = "done"
        if has_commit and a_total == 0:
            notes.append("受け入れ条件の記載が無いためコミットログを根拠に完了と推定")
    elif a_checked == 0 and w_checked == 0 and not has_log_activity:
        status = "not_started"
    else:
        status = "in_progress"

    # シグナル矛盾の明示（レポートの備考に転記させる）
    if has_commit and accept_has_unchecked:
        notes.append("コミットログありだが受け入れ条件に未チェックあり（要確認）")
    if accept_complete and not has_commit and logs["exists"] is False:
        notes.append("受け入れ条件は全チェックだがコミットログ未検出")

    return status, notes


def scan_task(task_dir: Path, logs_dir: Path) -> dict | None:
    m = TASK_DIR_RE.match(task_dir.name)
    if not m:
        return None
    number = int(m.group(1))
    slug = m.group(2)

    readme_md = task_dir / "README.md"
    readme_html = task_dir / "README.html"
    result: dict = {
        "task_id": task_dir.name,
        "number": number,
        "slug": slug,
        "band": "handover" if number >= HANDOVER_BAND_START else "main",
        "needs_manual_review": False,
        "notes": [],
    }

    if readme_md.is_file():
        text = readme_md.read_text(encoding="utf-8", errors="replace")
        meta = parse_frontmatter(text)
        accept = count_section_checkboxes(text, ["受け入れ条件", "Acceptance"])
        work = count_section_checkboxes(text, ["作業内容", "Tasks", "Checklist"])
    elif readme_html.is_file():
        # HTMLはベストエフォート。確実な機械判定が難しいので手動確認フラグを立てる
        result["needs_manual_review"] = True
        result["notes"].append("HTML形式タスクのため frontmatter/チェックボックスは未解析。直接確認が必要")
        meta, accept, work = {}, (0, 0), (0, 0)
    else:
        result["needs_manual_review"] = True
        result["notes"].append("README.md/README.html が見つからない")
        meta, accept, work = {}, (0, 0), (0, 0)

    logs = scan_logs(logs_dir, task_dir.name)
    status, status_notes = derive_status(accept, work, logs)
    result["notes"].extend(status_notes)

    result.update(
        {
            "frontmatter": meta,
            "depends_on": meta.get("depends_on", []),
            "estimated_time": meta.get("estimated_time"),
            "parallel_group": meta.get("parallel_group"),
            "priority": meta.get("priority"),
            "parallelizable": meta.get("parallelizable"),
            "acceptance": {"checked": accept[0], "total": accept[1]},
            "work_items": {"checked": work[0], "total": work[1]},
            "logs": logs,
            "status": status if not result["needs_manual_review"] else "unknown",
        }
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="プロジェクトルート / todos ディレクトリ / その親（既定: カレント）",
    )
    args = parser.parse_args()

    start = Path(args.path).expanduser().resolve()
    if not start.exists():
        print(json.dumps({"error": f"パスが存在しません: {start}"}, ensure_ascii=False))
        return 1

    todos_dir = find_todos_dir(start)
    if todos_dir is None:
        print(
            json.dumps(
                {"error": f"todos/ ディレクトリが見つかりません（探索起点: {start}）"},
                ensure_ascii=False,
            )
        )
        return 1

    project_root = todos_dir.parent
    logs_dir = project_root / "logs"

    tasks = []
    for child in sorted(todos_dir.iterdir(), key=lambda p: p.name):
        if not child.is_dir():
            continue
        task = scan_task(child, logs_dir)
        if task:
            tasks.append(task)

    # 依存先の完了状況から「着手可能か」を導出（推奨順序付けの材料）
    status_by_id = {t["task_id"]: t["status"] for t in tasks}
    for t in tasks:
        unmet = [d for d in t["depends_on"] if status_by_id.get(d) not in {"done"}]
        t["unmet_dependencies"] = unmet
        t["ready_to_start"] = (t["status"] == "not_started") and not unmet

    summary = _build_summary(tasks)

    output = {
        "project_root": str(project_root),
        "todos_dir": str(todos_dir),
        "logs_dir": str(logs_dir) if logs_dir.is_dir() else None,
        "roadmap_file": _detect_roadmap(todos_dir),
        "summary": summary,
        "tasks": tasks,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


def _detect_roadmap(todos_dir: Path) -> str | None:
    for name in ("README.md", "README.html"):
        f = todos_dir / name
        if f.is_file():
            return str(f)
    return None


def _build_summary(tasks: list[dict]) -> dict:
    def bucket(band: str) -> dict:
        sub = [t for t in tasks if t["band"] == band]
        return {
            "total": len(sub),
            "done": sum(1 for t in sub if t["status"] == "done"),
            "in_progress": sum(1 for t in sub if t["status"] == "in_progress"),
            "not_started": sum(1 for t in sub if t["status"] == "not_started"),
            "unknown": sum(1 for t in sub if t["status"] == "unknown"),
        }

    return {
        "main": bucket("main"),
        "handover": bucket("handover"),
        "ready_to_start": [t["task_id"] for t in tasks if t.get("ready_to_start")],
        "blocked": [
            t["task_id"]
            for t in tasks
            if t["status"] == "not_started" and t.get("unmet_dependencies")
        ],
    }


if __name__ == "__main__":
    sys.exit(main())
