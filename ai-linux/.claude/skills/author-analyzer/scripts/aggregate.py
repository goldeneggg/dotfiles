#!/usr/bin/env python3
"""author-analyzer の集計スクリプト.

git log と gh CLI で取得したデータを読み込み、author の貢献を集計して
JSON で出力する。本スクリプトは SKILL.md の Phase 2 から呼び出される。

入力（${WORKDIR} 配下、リポジトリごとに <owner>__<repo>/ サブディレクトリ）:
  - commits.txt          : git log の生出力（--pretty + --numstat）
  - commits.json         : gh api search/commits の出力（fallback、optional）
  - pr_authored.json     : gh pr list --author の JSON 配列
  - pr_reviewed.json     : gh search prs --reviewed-by の JSON 配列
  - pr_commented.json    : gh search prs --commenter の JSON 配列
  - issues_authored.json : gh issue list --author の JSON 配列
  - issues_commented.json: gh search issues --commenter の JSON 配列

出力: --output で指定された JSON ファイル.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

CONVENTIONAL_TYPES = {
    "feat", "fix", "docs", "style", "refactor", "perf",
    "test", "build", "ci", "chore", "revert", "wip",
}

CONVENTIONAL_RE = re.compile(
    r"^(?P<type>[a-z]+)(?:\((?P<scope>[^)]+)\))?(?P<bang>!)?:\s*(?P<subject>.+)$",
    re.IGNORECASE,
)


def parse_commits_txt(path: Path) -> list[dict[str, Any]]:
    """git log --pretty=format:'__COMMIT__%H...__END__' --numstat の出力をパース."""
    if not path.exists():
        return []

    text = path.read_text(encoding="utf-8", errors="replace")
    commits: list[dict[str, Any]] = []

    blocks = text.split("__COMMIT__")
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        end_idx = block.find("__END__")
        if end_idx < 0:
            continue
        head = block[:end_idx].strip()
        tail = block[end_idx + len("__END__"):].strip()

        lines = head.splitlines()
        if len(lines) < 5:
            continue
        sha = lines[0].strip()
        date = lines[1].strip()
        name = lines[2].strip()
        email = lines[3].strip()
        subject = lines[4].strip() if len(lines) > 4 else ""
        body = "\n".join(lines[5:]).strip()

        files: list[dict[str, Any]] = []
        for nl in tail.splitlines():
            nl = nl.strip()
            if not nl:
                continue
            parts = nl.split("\t")
            if len(parts) < 3:
                continue
            add_s, del_s, fname = parts[0], parts[1], parts[2]
            try:
                additions = int(add_s) if add_s != "-" else 0
                deletions = int(del_s) if del_s != "-" else 0
            except ValueError:
                continue
            files.append({
                "path": fname,
                "additions": additions,
                "deletions": deletions,
            })

        commits.append({
            "sha": sha,
            "date": date,
            "author_name": name,
            "author_email": email,
            "subject": subject,
            "body": body,
            "files": files,
        })

    return commits


def load_json_array(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    if not isinstance(data, list):
        return []
    return data


def classify_extension(path: str) -> str:
    base = os.path.basename(path)
    if base.startswith(".") and "." not in base[1:]:
        return base
    if "." not in base:
        return "(no-ext)"
    return "." + base.rsplit(".", 1)[-1].lower()


def top_dir(path: str, depth: int = 2) -> str:
    parts = path.split("/")
    if len(parts) <= depth:
        return "/".join(parts[:-1]) if len(parts) > 1 else "(root)"
    return "/".join(parts[:depth])


def parse_conventional(subject: str) -> dict[str, str] | None:
    m = CONVENTIONAL_RE.match(subject)
    if not m:
        return None
    typ = m.group("type").lower()
    if typ not in CONVENTIONAL_TYPES:
        return None
    return {
        "type": typ,
        "scope": (m.group("scope") or "").lower(),
        "breaking": bool(m.group("bang")),
    }


def aggregate_repo(repo_dir: Path) -> dict[str, Any]:
    commits = parse_commits_txt(repo_dir / "commits.txt")

    ext_changes: Counter[str] = Counter()
    dir_changes: Counter[str] = Counter()
    type_counts: Counter[str] = Counter()
    scope_counts: Counter[str] = Counter()
    file_set: set[str] = set()
    total_add = total_del = 0
    dates: list[str] = []

    for c in commits:
        dates.append(c["date"])
        cc = parse_conventional(c["subject"])
        if cc:
            type_counts[cc["type"]] += 1
            if cc["scope"]:
                scope_counts[cc["scope"]] += 1
        else:
            type_counts["(other)"] += 1

        for f in c["files"]:
            p = f["path"]
            a, d = f["additions"], f["deletions"]
            total_add += a
            total_del += d
            file_set.add(p)
            ext_changes[classify_extension(p)] += a + d
            dir_changes[top_dir(p)] += a + d

    pr_authored = load_json_array(repo_dir / "pr_authored.json")
    pr_reviewed = load_json_array(repo_dir / "pr_reviewed.json")
    pr_commented = load_json_array(repo_dir / "pr_commented.json")
    issues_authored = load_json_array(repo_dir / "issues_authored.json")
    issues_commented = load_json_array(repo_dir / "issues_commented.json")

    pr_merged = sum(1 for p in pr_authored if p.get("mergedAt"))
    pr_closed = sum(1 for p in pr_authored if p.get("state") == "CLOSED")
    pr_open = sum(1 for p in pr_authored if p.get("state") == "OPEN")
    pr_size = [
        (p.get("additions", 0) or 0) + (p.get("deletions", 0) or 0)
        for p in pr_authored
    ]
    label_counter: Counter[str] = Counter()
    for p in pr_authored:
        for label in p.get("labels", []) or []:
            name = label.get("name") if isinstance(label, dict) else label
            if name:
                label_counter[name] += 1

    pr_reviewed_unique_authors = len({
        (p.get("author") or {}).get("login")
        for p in pr_reviewed
        if (p.get("author") or {}).get("login")
    })

    issues_closed_authored = sum(1 for i in issues_authored if i.get("state") == "CLOSED")

    return {
        "commits": {
            "count": len(commits),
            "first_date": min(dates) if dates else None,
            "last_date": max(dates) if dates else None,
            "total_additions": total_add,
            "total_deletions": total_del,
            "files_touched": len(file_set),
            "top_extensions": ext_changes.most_common(10),
            "top_directories": dir_changes.most_common(10),
            "type_distribution": dict(type_counts),
            "top_scopes": scope_counts.most_common(10),
        },
        "pr_authored": {
            "count": len(pr_authored),
            "merged": pr_merged,
            "closed_unmerged": pr_closed,
            "open": pr_open,
            "merge_rate": round(pr_merged / len(pr_authored), 3) if pr_authored else None,
            "avg_size": round(sum(pr_size) / len(pr_size), 1) if pr_size else None,
            "median_size": sorted(pr_size)[len(pr_size) // 2] if pr_size else None,
            "max_size": max(pr_size) if pr_size else None,
            "label_top": label_counter.most_common(10),
        },
        "pr_reviewed": {
            "count": len(pr_reviewed),
            "unique_authors": pr_reviewed_unique_authors,
        },
        "pr_commented": {
            "count": len(pr_commented),
        },
        "issues_authored": {
            "count": len(issues_authored),
            "closed": issues_closed_authored,
        },
        "issues_commented": {
            "count": len(issues_commented),
        },
    }


def derive_signals(repo_aggs: dict[str, Any]) -> dict[str, Any]:
    """全リポジトリ集計から「主要言語」「主要レイヤ」「貢献タイプ」のシグナルを抽出."""
    ext_total: Counter[str] = Counter()
    dir_total: Counter[str] = Counter()
    type_total: Counter[str] = Counter()
    label_total: Counter[str] = Counter()

    for agg in repo_aggs.values():
        for ext, n in agg["commits"]["top_extensions"]:
            ext_total[ext] += n
        for d, n in agg["commits"]["top_directories"]:
            dir_total[d] += n
        for t, n in agg["commits"]["type_distribution"].items():
            type_total[t] += n
        for label, n in agg["pr_authored"]["label_top"]:
            label_total[label] += n

    return {
        "primary_extensions": ext_total.most_common(5),
        "primary_directories": dir_total.most_common(5),
        "primary_commit_types": type_total.most_common(5),
        "primary_labels": label_total.most_common(5),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workdir", required=True)
    parser.add_argument("--author", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    workdir = Path(args.workdir)
    if not workdir.is_dir():
        print(f"workdir not found: {workdir}", file=sys.stderr)
        return 1

    repo_aggs: dict[str, Any] = {}
    for sub in sorted(workdir.iterdir()):
        if not sub.is_dir():
            continue
        if "__" not in sub.name:
            continue
        repo_aggs[sub.name.replace("__", "/", 1)] = aggregate_repo(sub)

    out = {
        "author": args.author,
        "repos": repo_aggs,
        "signals": derive_signals(repo_aggs) if repo_aggs else {},
    }

    Path(args.output).write_text(
        json.dumps(out, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
