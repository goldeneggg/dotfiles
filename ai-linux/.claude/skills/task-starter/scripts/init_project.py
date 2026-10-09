#!/usr/bin/env python3
"""
Project structure initializer for task-starter skill.
Creates the standard folder structure for Web development projects.

ドキュメント形式は --format で切り替える:
  - md   : Markdown（既定）
  - html : 自己完結HTML（references/templates/html-shell.html を利用）
"""

import argparse
import html
import re
from datetime import datetime
from pathlib import Path

# 出力形式の選択肢。SKILL.md / ガイドと表記を揃える。
FORMAT_MD = "md"
FORMAT_HTML = "html"

# 自己完結HTMLシェルの単一ソース。スクリプトと Claude の HTML 生成が同じ体裁を共有するため、
# スクリプト位置からの相対で参照する（skills/task-starter/ 配下のレイアウトに依存）。
HTML_SHELL_PATH = (
    Path(__file__).resolve().parent.parent
    / "references" / "templates" / "html-shell.html"
)


def to_kebab_case(name: str) -> str:
    """Convert a string to kebab-case."""
    # Replace spaces and underscores with hyphens
    name = re.sub(r'[\s_]+', '-', name)
    # Insert hyphen before uppercase letters and convert to lowercase
    name = re.sub(r'([a-z])([A-Z])', r'\1-\2', name)
    # Remove non-alphanumeric characters except hyphens
    name = re.sub(r'[^a-zA-Z0-9-]', '', name)
    # Convert to lowercase and remove consecutive hyphens
    name = re.sub(r'-+', '-', name.lower())
    result = name.strip('-')
    if not result:
        raise ValueError(
            "Project name must contain at least one alphanumeric character."
        )
    return result


def render_html(title: str, body: str) -> str:
    """共有HTMLシェルに title/body を埋め込んで自己完結HTMLを返す。

    シェルが見つからない場合は、原因が一目で分かるよう明示的に失敗させる
    （体裁の壊れたHTMLを黙って生成しないため）。
    """
    if not HTML_SHELL_PATH.exists():
        raise FileNotFoundError(
            f"HTML shell template not found: {HTML_SHELL_PATH}. "
            "skills/task-starter/references/templates/html-shell.html を確認してください。"
        )
    shell = HTML_SHELL_PATH.read_text(encoding="utf-8")
    return shell.replace("{{TITLE}}", title).replace("{{BODY}}", body)


def readme_markdown(project_name: str, description: str) -> str:
    """README.md の内容を返す（Markdown）。"""
    overview = description if description else "<!-- 誰のどの問題を解決し、何を実現するか -->"
    return f"""# {project_name}

## 概要

{overview}

## なぜ必要か

<!-- 現在の困りごとと原因。実施しない場合に残る問題 -->

## 何を変えるか

<!-- 主要な変更について、現在と完成後の違いを説明する -->

## どう進めるか

<!-- 意味のある段階ごとに、作業・必要な理由・成果と、対応するTODOへのリンクを書く -->

## 今回の範囲

<!-- 対象と対象外を区別する -->

## 完了の判断

<!-- 期待する結果と確認方法の要点。詳細な条件は仕様へリンクする -->

## 未決事項

<!-- 計画を左右する不明点と決め方。なければこの節は削除する -->

## 詳細資料

<!-- 仕様と調査根拠へのリンクを、文書の生成後に追加する -->

- [作業の順序と個別タスク](todos/README.md)
- [現在の進捗](progresses/README.md)
"""


def readme_html(project_name: str, description: str) -> str:
    """README.html の内容を返す（自己完結HTML）。"""
    esc_name = html.escape(project_name)
    overview = (
        f"<p>{html.escape(description)}</p>"
        if description
        else "<p><!-- 誰のどの問題を解決し、何を実現するか --></p>"
    )
    body = f"""<h1>{esc_name}</h1>

<h2>概要</h2>
{overview}

<h2>なぜ必要か</h2>
<!-- 現在の困りごとと原因。実施しない場合に残る問題 -->

<h2>何を変えるか</h2>
<!-- 主要な変更について、現在と完成後の違いを説明する -->

<h2>どう進めるか</h2>
<!-- 意味のある段階ごとに、作業・必要な理由・成果と、対応するTODOへのリンクを書く -->

<h2>今回の範囲</h2>
<!-- 対象と対象外を区別する -->

<h2>完了の判断</h2>
<!-- 期待する結果と確認方法の要点。詳細な条件は仕様へリンクする -->

<h2>未決事項</h2>
<!-- 計画を左右する不明点と決め方。なければこの節は削除する -->

<h2>詳細資料</h2>
<!-- 仕様と調査根拠へのリンクを、文書の生成後に追加する -->
<ul>
  <li><a href="todos/README.html">作業の順序と個別タスク</a></li>
  <li><a href="progresses/README.md">現在の進捗</a></li>
</ul>
"""
    return render_html(esc_name, body)


def todos_readme_markdown(project_name: str) -> str:
    """todos/README.md（ロードマップ雛形）の内容を返す（Markdown）。"""
    return f"""# タスクロードマップ: {project_name}

目的と完成後の姿は[全体説明](../README.md)、現在の状態は[進捗一覧](../progresses/README.md)を参照する。この文書では、着手する順序と待つ必要がある作業を説明する。

> このファイルは雛形です。タスク分割完了後（Phase 4）に
> `references/templates/roadmap-template.md` をベースに以下を埋めてください:
>
> - タスク一覧表（前提・並行グループ・推定時間）
> - 作業の依存関係図（Mermaid）
> - 完了までの見通し（全体の所要時間を決める経路・合計時間・待ち時間）
> - 並行できる作業と、同時に進めても衝突しない理由
> - 作業の進め方（実行順と待ち条件）
> - 完了の判断と進捗の記録先。必要ならAIへの実行指示を付録に記載

## タスク一覧

<!-- ここにタスク表を記載 -->

## 作業の依存関係

<!-- ここに Mermaid graph TD を記載 -->

## 完了までの見通し

<!-- 最長経路・合計作業時間・外部の待ち時間 -->

## 並行できる作業

<!-- 同時に行う作業が分かるグループ名、所属タスク、前提、分担・統合方法 -->

## 作業の進め方（実行順と待ち条件）

<!-- 作業順・着手条件・受け渡す成果 -->

## 完了の判断と進捗

<!-- 完了条件の要点と定義元の仕様へのリンク。進捗は progresses/README.md と各 PROGRESS.md へ案内する -->

## 付録: AIへの実行指示（必要な場合のみ）

<!-- 採用する実行手段の指示だけを記載し、必要がなければ節ごと削除する -->
"""


def todos_readme_html(project_name: str) -> str:
    """todos/README.html（ロードマップ雛形）の内容を返す（自己完結HTML）。

    HTMLでは作業の依存関係図を <pre class="mermaid"> に書くと自動描画される。
    """
    esc_name = html.escape(project_name)
    title = f"タスクロードマップ: {esc_name}"
    body = f"""<h1>タスクロードマップ: {esc_name}</h1>

<p>目的と完成後の姿は<a href="../README.html">全体説明</a>、現在の状態は<a href="../progresses/README.md">進捗一覧</a>を参照する。この文書では、着手する順序と待つ必要がある作業を説明する。</p>

<blockquote>
  <p>このファイルは雛形です。タスク分割完了後（Phase 4）に
  <code>references/templates/roadmap-template.md</code> をベースに以下を埋めてください:</p>
  <ul>
    <li>タスク一覧表（前提・並行グループ・推定時間）</li>
    <li>作業の依存関係図（Mermaid。<code>&lt;pre class="mermaid"&gt;graph TD ...&lt;/pre&gt;</code> で記述すると自動描画）</li>
    <li>完了までの見通し（全体の所要時間を決める経路・合計時間・待ち時間）</li>
    <li>並行できる作業と、同時に進めても衝突しない理由</li>
    <li>作業の進め方（実行順と待ち条件）</li>
    <li>完了の判断と進捗の記録先。必要ならAIへの実行指示を付録に記載</li>
  </ul>
</blockquote>

<h2>タスク一覧</h2>
<!-- ここにタスク表を記載 -->

<h2>作業の依存関係</h2>
<!-- ここに <pre class="mermaid">graph TD ...</pre> を記載 -->

<h2>完了までの見通し</h2>
<!-- 最長経路・合計作業時間・外部の待ち時間 -->

<h2>並行できる作業</h2>
<!-- 同時に行う作業が分かるグループ名、所属タスク、前提、分担・統合方法 -->

<h2>作業の進め方（実行順と待ち条件）</h2>
<!-- 作業順・着手条件・受け渡す成果 -->

<h2>完了の判断と進捗</h2>
<!-- 完了条件の要点と定義元の仕様へのリンク。進捗は progresses/README.md と各 PROGRESS.md へ案内する -->

<h2>付録: AIへの実行指示（必要な場合のみ）</h2>
<!-- 採用する実行手段の指示だけを記載し、必要がなければ節ごと削除する -->
"""
    return render_html(title, body)


def create_readme(
    project_path: Path, project_name: str, description: str, fmt: str
) -> None:
    """Create initial README in the requested format."""
    if fmt == FORMAT_HTML:
        (project_path / "README.html").write_text(
            readme_html(project_name, description), encoding="utf-8"
        )
    else:
        (project_path / "README.md").write_text(
            readme_markdown(project_name, description), encoding="utf-8"
        )


def create_directories(project_path: Path) -> None:
    """Create the standard directory structure."""
    dirs = [
        "references",
        "files",
        "specs",
        "drafts/doubt",
        "todos",
        "progresses",
        "logs",
    ]
    for dir_name in dirs:
        (project_path / dir_name).mkdir(parents=True, exist_ok=True)
        # Ensure .gitkeep exists so the directory is tracked by git
        gitkeep = project_path / dir_name / ".gitkeep"
        gitkeep.touch()


def create_todos_readme(project_path: Path, project_name: str, fmt: str) -> None:
    """Create a placeholder todos/README for the roadmap.

    Phase 4 (依存分析とロードマップ生成) でこのファイルを書き換える。
    最初は雛形のみを置いておき、タスク分割完了後に内容が埋まる前提。
    """
    if fmt == FORMAT_HTML:
        (project_path / "todos" / "README.html").write_text(
            todos_readme_html(project_name), encoding="utf-8"
        )
    else:
        (project_path / "todos" / "README.md").write_text(
            todos_readme_markdown(project_name), encoding="utf-8"
        )


def create_progresses_readme(project_path: Path) -> None:
    """Create the task progress index in Markdown for every document format."""
    content = """# タスク進捗一覧

> この一覧は各タスクの `PROGRESS.md` から生成する集約ビューです。
> 状態判定では個別の `PROGRESS.md` を正本として参照してください。

| タスク | 状態 | 最終更新 | 個別進捗 |
|---|---|---|---|
"""
    (project_path / "progresses" / "README.md").write_text(
        content, encoding="utf-8"
    )


def create_doubt_status(project_path: Path) -> None:
    """Create the independent adversarial review state in Markdown."""
    updated_at = datetime.now().astimezone().isoformat(timespec="seconds")
    content = f"""# Doubt Review Status

- **state**: not_started
- **active_cycle**: none
- **completed_cycles**: 0
- **maximum_cycles**: 3
- **checkpoint**: none
- **reviewer_input**: none
- **result**: none
- **reader_check**: pending
- **reader_check_result**: none
- **reader_check_reason**: 対象未生成
- **updated_at**: {updated_at}
- **note**: none
"""
    (project_path / "drafts" / "doubt" / "STATUS.md").write_text(
        content, encoding="utf-8"
    )


def init_project(
    base_dir: str,
    project_name: str,
    description: str = "",
    fmt: str = FORMAT_MD,
) -> Path:
    """
    Initialize a new project structure.

    Args:
        base_dir: Base directory where the project folder will be created
        project_name: Name of the project
        description: Optional project description
        fmt: Document format ("md" or "html")

    Returns:
        Path to the created project directory
    """
    # Generate folder name with date prefix
    date_prefix = datetime.now().strftime("%Y%m%d")
    kebab_name = to_kebab_case(project_name)
    folder_name = f"{date_prefix}-{kebab_name}"

    project_path = Path(base_dir) / folder_name

    # Create project directory (race-safe)
    try:
        project_path.mkdir(parents=True)
    except FileExistsError:
        raise FileExistsError(f"Project directory already exists: {project_path}")

    # Create structure
    create_directories(project_path)
    create_readme(project_path, project_name, description, fmt)
    create_todos_readme(project_path, project_name, fmt)
    create_progresses_readme(project_path)
    create_doubt_status(project_path)

    return project_path


def main():
    parser = argparse.ArgumentParser(
        description="Initialize a new project structure for Web development tasks"
    )
    parser.add_argument(
        "project_name",
        help="Name of the project"
    )
    parser.add_argument(
        "--path",
        default=".",
        help="Base directory where the project will be created (default: current directory)"
    )
    parser.add_argument(
        "--description",
        default="",
        help="Project description"
    )
    parser.add_argument(
        "--format",
        choices=[FORMAT_MD, FORMAT_HTML],
        default=FORMAT_MD,
        help="Document format: 'md' (Markdown, default) or 'html' (self-contained HTML)"
    )

    args = parser.parse_args()

    try:
        project_path = init_project(
            args.path,
            args.project_name,
            args.description,
            args.format,
        )
        print(f"✅ Project initialized at: {project_path}")
        print(f"   Format: {args.format}")
        print(f"\nCreated structure:")
        for item in sorted(project_path.rglob("*")):
            rel_path = item.relative_to(project_path)
            indent = "  " * (len(rel_path.parts) - 1)
            if item.is_dir():
                print(f"{indent}📁 {item.name}/")
            else:
                print(f"{indent}📄 {item.name}")
    except FileExistsError as e:
        print(f"❌ Error: {e}")
        exit(1)
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        exit(1)


if __name__ == "__main__":
    main()
