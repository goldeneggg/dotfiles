import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1] / "scripts" / "sync_progress_index.py"
)
SPEC = importlib.util.spec_from_file_location("sync_progress_index", SCRIPT_PATH)
sync_progress_index = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(sync_progress_index)

INIT_SCRIPT_PATH = (
    Path(__file__).resolve().parents[2]
    / "task-starter"
    / "scripts"
    / "init_project.py"
)
INIT_SPEC = importlib.util.spec_from_file_location(
    "task_starter_init_project", INIT_SCRIPT_PATH
)
task_starter_init_project = importlib.util.module_from_spec(INIT_SPEC)
assert INIT_SPEC.loader is not None
INIT_SPEC.loader.exec_module(task_starter_init_project)


class SyncProgressIndexTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_root = Path(self.temp_dir.name)
        (self.project_root / "todos").mkdir()
        (self.project_root / "progresses").mkdir()

    def tearDown(self):
        self.temp_dir.cleanup()

    def create_task(
        self,
        task_id: str,
        status: str = "未着手",
        updated_at: str = "2026-07-24T10:00:00+09:00",
    ) -> None:
        (self.project_root / "todos" / task_id).mkdir()
        progress_dir = self.project_root / "progresses" / task_id
        progress_dir.mkdir()
        (progress_dir / "PROGRESS.md").write_text(
            "\n".join(
                [
                    f"# タスク進捗: {task_id}",
                    "",
                    "## 進捗",
                    "",
                    f"- **状態**: {status}",
                    f"- **最終更新**: {updated_at}",
                    "",
                ]
            ),
            encoding="utf-8",
        )

    def test_render_index_sorts_tasks_and_uses_canonical_values(self):
        self.create_task("002-second", "完了", "2026-07-24T12:00:00+09:00")
        self.create_task("001-first", "進行中", "2026-07-24T11:00:00+09:00")

        result = sync_progress_index.render_index(self.project_root)

        first_position = result.index("`001-first`")
        second_position = result.index("`002-second`")
        self.assertLess(first_position, second_position)
        self.assertIn(
            "| `001-first` | 進行中 | 2026-07-24T11:00:00+09:00 |",
            result,
        )
        self.assertIn(
            "| `002-second` | 完了 | 2026-07-24T12:00:00+09:00 |",
            result,
        )

    def test_missing_progress_is_visible_as_unknown(self):
        (self.project_root / "todos" / "001-missing").mkdir()

        result = sync_progress_index.render_index(self.project_root)

        self.assertIn("| `001-missing` | 判定不能 | — |", result)

    def test_invalid_status_or_timestamp_is_visible_as_unknown(self):
        self.create_task("001-invalid-status", "レビュー中")
        self.create_task("002-invalid-time", updated_at="2026-07-24 10:00:00")

        result = sync_progress_index.render_index(self.project_root)

        self.assertIn("| `001-invalid-status` | 判定不能 | — |", result)
        self.assertIn("| `002-invalid-time` | 判定不能 | — |", result)

    def test_check_only_detects_drift_without_overwriting(self):
        self.create_task("001-first")
        index_path = self.project_root / "progresses" / "README.md"
        index_path.write_text("古い一覧\n", encoding="utf-8")

        synchronized = sync_progress_index.sync_index(
            self.project_root, check_only=True
        )

        self.assertFalse(synchronized)
        self.assertEqual(index_path.read_text(encoding="utf-8"), "古い一覧\n")

    def test_sync_writes_index_and_then_check_succeeds(self):
        self.create_task("001-first")

        self.assertTrue(
            sync_progress_index.sync_index(
                self.project_root, check_only=False
            )
        )
        self.assertTrue(
            sync_progress_index.sync_index(self.project_root, check_only=True)
        )

    def test_task_starter_initial_index_matches_synchronizer(self):
        project_root = task_starter_init_project.init_project(
            self.temp_dir.name, "progress-index-test"
        )

        index_path = project_root / "progresses" / "README.md"
        self.assertTrue(index_path.is_file())
        self.assertEqual(
            index_path.read_text(encoding="utf-8"),
            sync_progress_index.render_index(project_root),
        )


if __name__ == "__main__":
    unittest.main()
