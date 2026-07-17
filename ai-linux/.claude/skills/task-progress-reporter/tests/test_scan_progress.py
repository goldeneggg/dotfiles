import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "scan_progress.py"
SPEC = importlib.util.spec_from_file_location("scan_progress", SCRIPT_PATH)
scan_progress = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(scan_progress)


class ScanProgressTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_root = Path(self.temp_dir.name)
        self.todos_dir = self.project_root / "todos"
        self.progresses_dir = self.project_root / "progresses"
        self.logs_dir = self.project_root / "logs"
        self.todos_dir.mkdir()
        self.progresses_dir.mkdir()
        self.logs_dir.mkdir()

    def tearDown(self):
        self.temp_dir.cleanup()

    def write_markdown_task(self, task_id, acceptance_checked=False):
        task_dir = self.todos_dir / task_id
        task_dir.mkdir()
        marker = "x" if acceptance_checked else " "
        (task_dir / "README.md").write_text(
            f"""---
id: "{task_id}"
depends_on: []
---

# TODO

## 作業内容

- [{marker}] 実装する

## 受け入れ条件

- [{marker}] 条件を満たす
""",
            encoding="utf-8",
        )
        return task_dir

    def write_html_task(self, task_id):
        task_dir = self.todos_dir / task_id
        task_dir.mkdir()
        (task_dir / "README.html").write_text(
            "<html><body><h1>TODO</h1></body></html>",
            encoding="utf-8",
        )
        return task_dir

    def write_progress(self, task_id, status, include_outcome=True):
        progress_dir = self.progresses_dir / task_id
        progress_dir.mkdir(parents=True, exist_ok=True)
        outcome = "\n## 成果\n\n- 結果" if include_outcome else ""
        (progress_dir / "PROGRESS.md").write_text(
            f"""# タスク進捗: {task_id}

## 進捗

- **状態**: {status}
- **最終更新**: 2026-07-16T12:00:00+09:00
- **完了した作業**:
  - なし
- **残作業**:
  - 実装
- **ブロッカー**:
  - なし
{outcome}
""",
            encoding="utf-8",
        )

    def scan_task(self, task_dir):
        return scan_progress.scan_task(
            task_dir,
            self.progresses_dir,
            self.logs_dir,
        )

    def test_canonical_statuses_are_parsed(self):
        cases = (
            ("001-not-started", "未着手", "not_started"),
            ("002-in-progress", "進行中", "in_progress"),
            ("003-blocked", "ブロック中", "in_progress"),
        )
        for task_id, declared_status, expected_status in cases:
            with self.subTest(task_id=task_id):
                task_dir = self.write_markdown_task(task_id)
                self.write_progress(task_id, declared_status)

                result = self.scan_task(task_dir)

                self.assertTrue(result["progresses"]["schema_valid"])
                self.assertEqual(result["status"], expected_status)

    def test_done_requires_consistent_acceptance(self):
        task_id = "004-done"
        task_dir = self.write_markdown_task(task_id, acceptance_checked=True)
        self.write_progress(task_id, "完了")

        result = self.scan_task(task_dir)

        self.assertEqual(result["progresses"]["declared_status"], "done")
        self.assertEqual(result["status"], "done")

    def test_progress_acceptance_conflict_stays_in_progress(self):
        task_id = "005-conflict"
        task_dir = self.write_markdown_task(task_id)
        self.write_progress(task_id, "完了")

        result = self.scan_task(task_dir)

        self.assertEqual(result["status"], "in_progress")
        self.assertTrue(any("未チェック" in note for note in result["notes"]))

    def test_invalid_progress_schema_is_reported(self):
        task_id = "006-invalid"
        task_dir = self.write_markdown_task(task_id)
        self.write_progress(task_id, "未着手", include_outcome=False)

        result = self.scan_task(task_dir)

        self.assertFalse(result["progresses"]["schema_valid"])
        self.assertIn("成果セクション", result["progresses"]["missing_fields"])
        self.assertTrue(any("必須形式が不正" in note for note in result["notes"]))

    def test_invalid_status_and_timestamp_are_reported(self):
        task_id = "006-invalid-values"
        task_dir = self.write_markdown_task(task_id)
        self.write_progress(task_id, "保留")
        progress_path = self.progresses_dir / task_id / "PROGRESS.md"
        progress_path.write_text(
            progress_path.read_text(encoding="utf-8").replace(
                "2026-07-16T12:00:00+09:00",
                "2026-07-16T12:00:00",
            ),
            encoding="utf-8",
        )

        result = self.scan_task(task_dir)

        self.assertFalse(result["progresses"]["schema_valid"])
        self.assertIn(
            "未対応の状態値: 保留",
            result["progresses"]["validation_errors"],
        )
        self.assertIn(
            "最終更新にタイムゾーンがありません",
            result["progresses"]["validation_errors"],
        )

    def test_nonstandard_progress_files_and_general_logs_do_not_start_task(self):
        task_id = "007-artifacts"
        task_dir = self.write_markdown_task(task_id)
        self.write_progress(task_id, "未着手")
        (self.progresses_dir / task_id / "ta-review-20260716-deadbeef.md").write_text(
            "review",
            encoding="utf-8",
        )
        screenshot_dir = self.logs_dir / task_id / "screenshots"
        screenshot_dir.mkdir(parents=True)
        (screenshot_dir / "result.png").write_bytes(b"png")

        result = self.scan_task(task_dir)

        self.assertEqual(result["status"], "not_started")
        self.assertEqual(
            result["progresses"]["unexpected_files"],
            ["ta-review-20260716-deadbeef.md"],
        )
        self.assertEqual(result["logs"]["other_file_count"], 1)

    def test_valid_progress_can_classify_html_task(self):
        task_id = "008-html"
        task_dir = self.write_html_task(task_id)
        self.write_progress(task_id, "完了")

        result = self.scan_task(task_dir)

        self.assertTrue(result["needs_manual_review"])
        self.assertTrue(result["progresses"]["schema_valid"])
        self.assertEqual(result["status"], "done")


if __name__ == "__main__":
    unittest.main()
