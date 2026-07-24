#!/usr/bin/env python3
"""個別の PROGRESS.md から progresses/README.md を生成・検証する。"""

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

TASK_DIRECTORY_PATTERN = re.compile(r"^\d{3}-[a-z0-9][a-z0-9-]*$")
STATUS_PATTERN = re.compile(r"^- \*\*状態\*\*: (.+)$", re.MULTILINE)
UPDATED_AT_PATTERN = re.compile(r"^- \*\*最終更新\*\*: (.+)$", re.MULTILINE)
VALID_STATUSES = {"未着手", "進行中", "ブロック中", "完了"}
UNKNOWN_STATUS = "判定不能"
UNKNOWN_UPDATED_AT = "—"


def find_project_root(path: Path) -> Path:
    """プロジェクトルートまたは配下パスからルートを特定する。"""
    resolved = path.resolve()
    if resolved.name in {"todos", "progresses"}:
        return resolved.parent
    if (resolved / "todos").is_dir():
        return resolved
    raise ValueError(f"todos/ が見つかりません: {resolved}")


def read_progress_values(progress_file: Path) -> tuple[str, str]:
    """PROGRESS.md の状態と最終更新を返す。不正時は判定不能を返す。"""
    if not progress_file.is_file():
        return UNKNOWN_STATUS, UNKNOWN_UPDATED_AT

    content = progress_file.read_text(encoding="utf-8")
    status_match = STATUS_PATTERN.search(content)
    updated_at_match = UPDATED_AT_PATTERN.search(content)
    if status_match is None or updated_at_match is None:
        return UNKNOWN_STATUS, UNKNOWN_UPDATED_AT

    status = status_match.group(1).strip()
    updated_at = updated_at_match.group(1).strip()
    try:
        parsed_updated_at = datetime.fromisoformat(updated_at)
    except ValueError:
        return UNKNOWN_STATUS, UNKNOWN_UPDATED_AT
    if status not in VALID_STATUSES or parsed_updated_at.utcoffset() is None:
        return UNKNOWN_STATUS, UNKNOWN_UPDATED_AT

    return status, updated_at


def render_index(project_root: Path) -> str:
    """todos/ の全タスクを列挙して進捗一覧を生成する。"""
    todos_dir = project_root / "todos"
    task_ids = sorted(
        child.name
        for child in todos_dir.iterdir()
        if child.is_dir() and TASK_DIRECTORY_PATTERN.fullmatch(child.name)
    )

    lines = [
        "# タスク進捗一覧",
        "",
        "> この一覧は各タスクの `PROGRESS.md` から生成する集約ビューです。",
        "> 状態判定では個別の `PROGRESS.md` を正本として参照してください。",
        "",
        "| タスク | 状態 | 最終更新 | 個別進捗 |",
        "|---|---|---|---|",
    ]
    for task_id in task_ids:
        progress_file = project_root / "progresses" / task_id / "PROGRESS.md"
        status, updated_at = read_progress_values(progress_file)
        progress_link = f"[PROGRESS.md](./{task_id}/PROGRESS.md)"
        lines.append(
            f"| `{task_id}` | {status} | {updated_at} | {progress_link} |"
        )
    return "\n".join(lines) + "\n"


def sync_index(project_root: Path, check_only: bool) -> bool:
    """一覧を同期する。check_only の場合は書き込まず一致可否を返す。"""
    expected = render_index(project_root)
    index_path = project_root / "progresses" / "README.md"
    current = (
        index_path.read_text(encoding="utf-8") if index_path.is_file() else None
    )
    if current == expected:
        return True
    if check_only:
        return False

    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(expected, encoding="utf-8")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(
        description="個別の PROGRESS.md から progresses/README.md を同期する"
    )
    parser.add_argument("project_path", help="プロジェクトルートまたは todos/ のパス")
    parser.add_argument(
        "--check",
        action="store_true",
        help="ファイルを変更せず、同期済みかだけを確認する",
    )
    args = parser.parse_args()

    try:
        project_root = find_project_root(Path(args.project_path))
        synchronized = sync_index(project_root, args.check)
    except (OSError, UnicodeError, ValueError) as error:
        print(f"エラー: {error}", file=sys.stderr)
        return 2

    if not synchronized:
        print(
            "progresses/README.md が個別の PROGRESS.md と同期していません",
            file=sys.stderr,
        )
        return 1

    action = "確認" if args.check else "同期"
    print(f"progresses/README.md を{action}しました: {project_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
