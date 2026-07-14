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
    overview = description if description else "<!-- プロジェクトの概要を記載 -->"
    return f"""# {project_name}

## 概要

{overview}

## 目的

<!-- プロジェクトの目的を記載 -->

## ステータス

- [ ] 計画中
- [ ] 開発中
- [ ] レビュー中
- [ ] 完了
"""


def readme_html(project_name: str, description: str) -> str:
    """README.html の内容を返す（自己完結HTML）。"""
    esc_name = html.escape(project_name)
    overview = (
        f"<p>{html.escape(description)}</p>"
        if description
        else "<p><!-- プロジェクトの概要を記載 --></p>"
    )
    body = f"""<h1>{esc_name}</h1>

<h2>概要</h2>
{overview}

<h2>目的</h2>
<p><!-- プロジェクトの目的を記載 --></p>

<h2>ステータス</h2>
<ul>
  <li><input type="checkbox" disabled> 計画中</li>
  <li><input type="checkbox" disabled> 開発中</li>
  <li><input type="checkbox" disabled> レビュー中</li>
  <li><input type="checkbox" disabled> 完了</li>
</ul>
"""
    return render_html(esc_name, body)


def todos_readme_markdown(project_name: str) -> str:
    """todos/README.md（ロードマップ雛形）の内容を返す（Markdown）。"""
    return f"""# タスクロードマップ: {project_name}

> このファイルは雛形です。タスク分割完了後（Phase 4）に
> `references/templates/roadmap-template.md` をベースに以下を埋めてください:
>
> - タスク一覧表（前提・並行グループ・推定時間）
> - Mermaid 依存DAG
> - クリティカルパス
> - 並行可能タスク群と非干渉性の根拠
> - 推奨ワークロード（Subagents並列 / /goal / worktree など Claude Code 機能の活用法）

## タスク一覧

<!-- ここにタスク表を記載 -->

## 依存DAG

<!-- ここに Mermaid graph TD を記載 -->

## クリティカルパス

<!-- 最長経路と合計推定時間 -->

## 並行可能タスク群

<!-- Group A, B... と所属タスク -->

## 推奨ワークロード

<!-- Step 1, 2, 3 ... の具体的な実行手順 -->
"""


def todos_readme_html(project_name: str) -> str:
    """todos/README.html（ロードマップ雛形）の内容を返す（自己完結HTML）。

    HTMLでは Mermaid 依存DAG を <pre class="mermaid"> に書くと自動描画される。
    """
    esc_name = html.escape(project_name)
    title = f"タスクロードマップ: {esc_name}"
    body = f"""<h1>タスクロードマップ: {esc_name}</h1>

<blockquote>
  <p>このファイルは雛形です。タスク分割完了後（Phase 4）に
  <code>references/templates/roadmap-template.md</code> をベースに以下を埋めてください:</p>
  <ul>
    <li>タスク一覧表（前提・並行グループ・推定時間）</li>
    <li>Mermaid 依存DAG（<code>&lt;pre class="mermaid"&gt;graph TD ...&lt;/pre&gt;</code> で記述すると自動描画）</li>
    <li>クリティカルパス</li>
    <li>並行可能タスク群と非干渉性の根拠</li>
    <li>推奨ワークロード（Subagents並列 / /goal / worktree など Claude Code 機能の活用法）</li>
  </ul>
</blockquote>

<h2>タスク一覧</h2>
<!-- ここにタスク表を記載 -->

<h2>依存DAG</h2>
<!-- ここに <pre class="mermaid">graph TD ...</pre> を記載 -->

<h2>クリティカルパス</h2>
<!-- 最長経路と合計推定時間 -->

<h2>並行可能タスク群</h2>
<!-- Group A, B... と所属タスク -->

<h2>推奨ワークロード</h2>
<!-- Step 1, 2, 3 ... の具体的な実行手順 -->
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
