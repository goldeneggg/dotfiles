#!/usr/bin/env python3
"""task-starter プロジェクトの todos/ を走査し、各タスクの進捗シグナルをJSONで出力する。

進捗の最終的な分類・グルーピング・推奨順序付けはモデル側の判断に委ねる。
このスクリプトの役割は「判定に必要な定義・状態・互換シグナルを機械的に集める」こと。

集める情報:
- frontmatter: id / estimated_time / depends_on / parallel_group / priority / parallelizable
- TODOに定義された W-ID / AC-ID（新形式）
- progresses/NNN-{task}/PROGRESS.md のスキーマ・宣言状態・AC検証状態・非標準ファイル
- 受け入れ条件・作業内容のチェックボックス進捗（旧形式の読取互換だけ）
- logs/NNN-{task}/ 配下の commit ログ有無・その他ファイル有無
- 上記から導出した暫定ステータス（done / in_progress / not_started / unknown）と注記

Markdown(.md) タスクを主対象とする。HTML(.html) プロジェクトはベストエフォートで検出し、
frontmatter 相当が取れない場合は needs_manual_review=true を立てて呼び出し側に直接確認を促す。
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

# 番号帯の境界。0xx=メインタスク、1xx=申し送り（task-starter/performer の番号規約）
HANDOVER_BAND_START = 100

TASK_DIR_RE = re.compile(r"^(\d{3})-(.+)$")
CHECKBOX_RE = re.compile(r"^\s*[-*]\s+\[( |x|X)\]")
SECTION_RE = re.compile(r"^#{1,6}\s+(.+?)\s*$")
DEFINITION_ID_RE = re.compile(r"^\s*[-*]\s+\*\*((?:W|AC)-\d+)\*\*\s*:")
ACCEPTANCE_ID_RE = re.compile(r"^AC-\d+$")
# logs 配下のコミットログ命名: commit-YYYYmmddHHMMSS-title.txt
COMMIT_LOG_RE = re.compile(r"^commit-.*\.txt$")
PROGRESS_FILE_NAME = "PROGRESS.md"
PROGRESS_SECTION_RE = re.compile(r"^##\s+進捗\s*$", re.MULTILINE)
OUTCOME_SECTION_RE = re.compile(r"^##\s+成果\s*$", re.MULTILINE)
ACCEPTANCE_VERIFICATION_SECTION_RE = re.compile(
    r"^##\s+受け入れ条件の検証\s*$", re.MULTILINE
)
PROGRESS_FIELD_NAMES = (
    "状態",
    "最終更新",
    "完了した作業",
    "残作業",
    "ブロッカー",
)
PROGRESS_STATUS_MAP = {
    "未着手": "not_started",
    "進行中": "in_progress",
    "ブロック中": "blocked",
    "完了": "done",
}
ACCEPTANCE_STATUS_VALUES = {"未確認", "充足", "未充足"}
IGNORED_TRACKING_FILES = {".gitkeep"}


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


def extract_definition_ids(
    text: str,
    section_names: list[str],
    prefix: str,
) -> tuple[list[str], list[str]]:
    """指定セクションから順序を保ってIDを抽出し、重複IDも返す。"""
    ids: list[str] = []
    active = False
    section_level = 0
    for line in text.splitlines():
        heading_match = SECTION_RE.match(line)
        if heading_match:
            level = len(heading_match.group(0)) - len(
                heading_match.group(0).lstrip("#")
            )
            heading = heading_match.group(1)
            if active and level <= section_level:
                active = False
            if any(name in heading for name in section_names):
                active = True
                section_level = level
            continue
        if not active:
            continue
        id_match = DEFINITION_ID_RE.match(line)
        if id_match and id_match.group(1).startswith(f"{prefix}-"):
            ids.append(id_match.group(1))

    duplicates = sorted({item_id for item_id in ids if ids.count(item_id) > 1})
    return ids, duplicates


def scan_logs(logs_dir: Path, task_id: str) -> dict:
    """logs/NNN-{task}/ の中身を調べ、コミットログ有無と他ファイル有無を返す。"""
    info = {"commit_log_count": 0, "other_file_count": 0, "exists": False}
    if not logs_dir or not logs_dir.is_dir():
        return info
    task_log_dir = logs_dir / task_id
    if not task_log_dir.is_dir():
        return info
    info["exists"] = True
    for f in task_log_dir.rglob("*"):
        if not f.is_file() or f.name in IGNORED_TRACKING_FILES:
            continue
        if COMMIT_LOG_RE.match(f.name):
            info["commit_log_count"] += 1
        else:
            info["other_file_count"] += 1
    return info


def scan_progresses(
    progresses_dir: Path,
    task_id: str,
    expected_acceptance_ids: list[str] | None = None,
    require_acceptance_verification: bool = False,
) -> dict:
    """正本のPROGRESS.mdを検証し、非標準ファイルを進捗判定から分離する。"""
    info = {
        "exists": False,
        "canonical_file": None,
        "canonical_exists": False,
        "schema_valid": False,
        "declared_status": None,
        "missing_fields": [],
        "validation_errors": [],
        "unexpected_files": [],
        "schema_version": None,
        "acceptance_verification": {
            "present": False,
            "items": [],
            "counts": {"未確認": 0, "充足": 0, "未充足": 0},
            "missing_ids": [],
            "unexpected_ids": [],
            "duplicate_ids": [],
        },
    }
    if not progresses_dir or not progresses_dir.is_dir():
        return info
    task_progress_dir = progresses_dir / task_id
    if not task_progress_dir.is_dir():
        return info
    info["exists"] = True
    canonical_file = task_progress_dir / PROGRESS_FILE_NAME
    for file_path in sorted(task_progress_dir.iterdir(), key=lambda path: path.name):
        if file_path.name in IGNORED_TRACKING_FILES:
            continue
        if file_path == canonical_file and file_path.is_file():
            continue
        suffix = "/" if file_path.is_dir() else ""
        info["unexpected_files"].append(f"{file_path.name}{suffix}")

    if not canonical_file.is_file():
        return info

    info["canonical_file"] = str(canonical_file)
    info["canonical_exists"] = True
    text = canonical_file.read_text(encoding="utf-8", errors="replace")

    missing_fields = []
    if not PROGRESS_SECTION_RE.search(text):
        missing_fields.append("進捗セクション")
    if not OUTCOME_SECTION_RE.search(text):
        missing_fields.append("成果セクション")

    acceptance = _parse_acceptance_verification(text)
    info["acceptance_verification"] = acceptance
    if require_acceptance_verification and not acceptance["present"]:
        missing_fields.append("受け入れ条件の検証セクション")
    info["schema_version"] = "current" if acceptance["present"] else "legacy"

    field_values = {}
    for field_name in PROGRESS_FIELD_NAMES:
        value = _extract_progress_field(text, field_name)
        if value is None:
            missing_fields.append(field_name)
        else:
            field_values[field_name] = value

    validation_errors = []
    status_label = field_values.get("状態", "")
    if status_label:
        info["declared_status"] = PROGRESS_STATUS_MAP.get(status_label)
        if info["declared_status"] is None:
            validation_errors.append(f"未対応の状態値: {status_label}")
    elif "状態" in field_values:
        validation_errors.append("状態が空です")

    updated_at = field_values.get("最終更新", "")
    if updated_at:
        try:
            parsed_updated_at = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
            if parsed_updated_at.tzinfo is None:
                validation_errors.append("最終更新にタイムゾーンがありません")
        except ValueError:
            validation_errors.append(f"最終更新がISO 8601形式ではありません: {updated_at}")
    elif "最終更新" in field_values:
        validation_errors.append("最終更新が空です")

    validation_errors.extend(acceptance["validation_errors"])
    if acceptance["present"] and expected_acceptance_ids is not None:
        actual_ids = [item["id"] for item in acceptance["items"]]
        expected_set = set(expected_acceptance_ids)
        actual_set = set(actual_ids)
        acceptance["missing_ids"] = [
            item_id for item_id in expected_acceptance_ids if item_id not in actual_set
        ]
        acceptance["unexpected_ids"] = [
            item_id for item_id in actual_ids if item_id not in expected_set
        ]
        if acceptance["missing_ids"]:
            validation_errors.append(
                "AC-IDが欠落: " + ", ".join(acceptance["missing_ids"])
            )
        if acceptance["unexpected_ids"]:
            validation_errors.append(
                "TODOに存在しないAC-ID: "
                + ", ".join(acceptance["unexpected_ids"])
            )

    info["missing_fields"] = missing_fields
    info["validation_errors"] = validation_errors
    info["schema_valid"] = not missing_fields and not validation_errors
    return info


def _parse_acceptance_verification(text: str) -> dict:
    result = {
        "present": False,
        "items": [],
        "counts": {"未確認": 0, "充足": 0, "未充足": 0},
        "missing_ids": [],
        "unexpected_ids": [],
        "duplicate_ids": [],
        "validation_errors": [],
    }
    section_match = ACCEPTANCE_VERIFICATION_SECTION_RE.search(text)
    if not section_match:
        return result

    result["present"] = True
    section_text = text[section_match.end() :]
    next_section = re.search(r"^##\s+", section_text, re.MULTILINE)
    if next_section:
        section_text = section_text[: next_section.start()]

    seen_ids: set[str] = set()
    for line in section_text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if len(cells) < 3 or cells[0] == "ID" or set(cells[0]) <= {"-", ":"}:
            continue
        acceptance_id, status, evidence = cells[:3]
        if not ACCEPTANCE_ID_RE.fullmatch(acceptance_id):
            result["validation_errors"].append(
                f"不正なAC-ID: {acceptance_id or '(空)'}"
            )
            continue
        if acceptance_id in seen_ids:
            result["duplicate_ids"].append(acceptance_id)
            continue
        seen_ids.add(acceptance_id)
        if status not in ACCEPTANCE_STATUS_VALUES:
            result["validation_errors"].append(
                f"{acceptance_id}の未対応の検証状態: {status or '(空)'}"
            )
            continue
        result["items"].append(
            {"id": acceptance_id, "status": status, "evidence": evidence}
        )
        result["counts"][status] += 1

    if result["duplicate_ids"]:
        result["duplicate_ids"] = sorted(set(result["duplicate_ids"]))
        result["validation_errors"].append(
            "重複AC-ID: " + ", ".join(result["duplicate_ids"])
        )
    if not result["items"]:
        result["validation_errors"].append("AC検証行がありません")
    return result


def _extract_progress_field(text: str, field_name: str) -> str | None:
    pattern = re.compile(
        rf"^\s*[-*]\s+\*\*{re.escape(field_name)}\*\*:\s*(.*?)\s*$",
        re.MULTILINE,
    )
    match = pattern.search(text)
    return match.group(1).strip() if match else None


def derive_status(
    definition_format: str,
    accept: tuple[int, int],
    work: tuple[int, int],
    progresses: dict,
    logs: dict,
) -> tuple[str, list[str]]:
    """契約バージョンに応じて暫定ステータスと注記を導出する。

    判定ルール:
    - 新形式はPROGRESS.mdの宣言状態とAC検証状態だけで判定する
    - 旧形式は有効なPROGRESS.mdを優先し、正本が無効・欠落した場合だけチェックボックスとコミットログで補助判定する
    - 一般ログとprogresses内の非標準ファイルは着手シグナルにしない
    """
    a_checked, a_total = accept
    w_checked, w_total = work
    has_commit = logs["commit_log_count"] > 0
    declared_status = (
        progresses["declared_status"] if progresses["schema_valid"] else None
    )
    notes: list[str] = []

    acceptance = progresses["acceptance_verification"]
    acceptance_total = len(acceptance["items"])
    acceptance_complete = (
        acceptance_total > 0 and acceptance["counts"]["充足"] == acceptance_total
    )

    if definition_format == "current" or progresses["schema_version"] == "current":
        if progresses["schema_valid"]:
            if declared_status == "done" and not acceptance_complete:
                status = "in_progress"
                notes.append(
                    "PROGRESS.mdは完了だが未確認または未充足のAC-IDあり（要確認）"
                )
            elif declared_status == "done":
                status = "done"
            elif acceptance_complete:
                status = "in_progress"
                notes.append(
                    "全AC-IDは充足済みだがPROGRESS.mdの状態が完了ではない（要確認）"
                )
            elif declared_status in {"in_progress", "blocked"}:
                status = "in_progress"
                if declared_status == "blocked":
                    notes.append("PROGRESS.mdでブロック中と宣言")
            elif declared_status == "not_started":
                status = "not_started"
            else:
                status = "unknown"
        else:
            status = "unknown"
    elif declared_status is not None:
        status = "in_progress" if declared_status == "blocked" else declared_status
        notes.append("旧形式を読取互換モードで判定。新形式への移行を推奨")
        if declared_status == "blocked":
            notes.append("PROGRESS.mdでブロック中と宣言")
    else:
        accept_complete = a_total > 0 and a_checked == a_total
        accept_has_unchecked = a_total > 0 and a_checked < a_total
        if accept_complete or (has_commit and not accept_has_unchecked):
            status = "done"
            if has_commit and a_total == 0:
                notes.append("旧形式の進捗正本と受け入れ条件が無いためコミットログを根拠に完了と推定")
        elif a_checked == 0 and w_checked == 0 and not has_commit:
            status = "not_started"
        else:
            status = "in_progress"
        notes.append("旧形式のチェックボックスを読取専用の補助情報として判定。新形式への移行を推奨")

    if progresses["canonical_exists"] is False:
        notes.append("PROGRESS.mdが見つからない")
    elif progresses["schema_valid"] is False:
        details = progresses["missing_fields"] + progresses["validation_errors"]
        notes.append(f"PROGRESS.mdの必須形式が不正: {', '.join(details)}")
    if progresses["unexpected_files"]:
        notes.append(
            "progresses内の非標準ファイル（進捗判定から除外）: "
            + ", ".join(progresses["unexpected_files"])
        )

    return status, notes


def scan_task(task_dir: Path, progresses_dir: Path, logs_dir: Path) -> dict | None:
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
        acceptance_ids, duplicate_acceptance_ids = extract_definition_ids(
            text, ["受け入れ条件", "Acceptance"], "AC"
        )
        work_ids, duplicate_work_ids = extract_definition_ids(
            text, ["作業内容", "Tasks", "Checklist"], "W"
        )
        accept = count_section_checkboxes(text, ["受け入れ条件", "Acceptance"])
        work = count_section_checkboxes(text, ["作業内容", "Tasks", "Checklist"])
        if acceptance_ids or work_ids:
            definition_format = "current"
        elif accept[1] > 0 or work[1] > 0:
            definition_format = "legacy"
        else:
            definition_format = "unknown"
    elif readme_html.is_file():
        # HTMLはベストエフォート。確実な定義抽出が難しいので手動確認フラグを立てる
        result["needs_manual_review"] = True
        result["notes"].append("HTML形式タスクのため frontmatter/W-ID/AC-IDは未解析。直接確認が必要")
        meta, accept, work = {}, (0, 0), (0, 0)
        acceptance_ids, work_ids = [], []
        duplicate_acceptance_ids, duplicate_work_ids = [], []
        definition_format = "unknown"
    else:
        result["needs_manual_review"] = True
        result["notes"].append("README.md/README.html が見つからない")
        meta, accept, work = {}, (0, 0), (0, 0)
        acceptance_ids, work_ids = [], []
        duplicate_acceptance_ids, duplicate_work_ids = [], []
        definition_format = "unknown"

    if duplicate_acceptance_ids:
        result["notes"].append(
            "TODOの重複AC-ID: " + ", ".join(duplicate_acceptance_ids)
        )
        result["needs_manual_review"] = True
    if duplicate_work_ids:
        result["notes"].append(
            "TODOの重複W-ID: " + ", ".join(duplicate_work_ids)
        )
        result["needs_manual_review"] = True
    if definition_format == "current" and not acceptance_ids:
        result["notes"].append("新形式のTODOにAC-IDがない")
        result["needs_manual_review"] = True

    progresses = scan_progresses(
        progresses_dir,
        task_dir.name,
        acceptance_ids if definition_format == "current" else None,
        require_acceptance_verification=definition_format == "current",
    )
    if duplicate_acceptance_ids:
        progresses["validation_errors"].append(
            "TODOの重複AC-ID: " + ", ".join(duplicate_acceptance_ids)
        )
        progresses["schema_valid"] = False
    logs = scan_logs(logs_dir, task_dir.name)
    status, status_notes = derive_status(
        definition_format, accept, work, progresses, logs
    )
    result["notes"].extend(status_notes)

    result.update(
        {
            "frontmatter": meta,
            "depends_on": meta.get("depends_on", []),
            "estimated_time": meta.get("estimated_time"),
            "parallel_group": meta.get("parallel_group"),
            "priority": meta.get("priority"),
            "parallelizable": meta.get("parallelizable"),
            "definition_format": definition_format,
            "acceptance": {
                "ids": acceptance_ids,
                "checked": accept[0] if definition_format == "legacy" else None,
                "total": len(acceptance_ids) if acceptance_ids else accept[1],
            },
            "work_items": {
                "ids": work_ids,
                "checked": work[0] if definition_format == "legacy" else None,
                "total": len(work_ids) if work_ids else work[1],
            },
            "progresses": progresses,
            "logs": logs,
            "status": (
                status
                if not result["needs_manual_review"] or progresses["schema_valid"]
                else "unknown"
            ),
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
    progresses_dir = project_root / "progresses"
    logs_dir = project_root / "logs"

    tasks = []
    for child in sorted(todos_dir.iterdir(), key=lambda p: p.name):
        if not child.is_dir():
            continue
        task = scan_task(child, progresses_dir, logs_dir)
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
        "progresses_dir": str(progresses_dir) if progresses_dir.is_dir() else None,
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
