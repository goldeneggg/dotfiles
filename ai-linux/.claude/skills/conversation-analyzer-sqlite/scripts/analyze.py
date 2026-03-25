#!/usr/bin/env python3
"""Claude Code会話データ分析スクリプト

SQLiteエクスポートデータに対して各種分析クエリを実行し、結果を出力する。

Usage:
    python3 scripts/analyze.py [--db PATH] [--report TYPE] [--project FILTER] [--days N] [--format FORMAT]

Options:
    --db PATH        データベースパス (default: ~/.claude/exports/conversations.db)
    --report TYPE    レポート種別: summary, tokens, tools, sessions, files, subagents, trends, all
                     (default: summary)
    --project FILTER プロジェクトパスのフィルタ (部分一致)
    --days N         直近N日間に限定
    --format FORMAT  出力形式: markdown, csv, json (default: markdown)
"""

import argparse
import json
import os
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path


def get_db_path(custom_path=None):
    if custom_path:
        return custom_path
    return os.path.expanduser("~/.claude/exports/conversations.db")


def connect(db_path):
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}", file=sys.stderr)
        sys.exit(1)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def date_filter(days=None):
    """日付フィルタのWHERE句を生成
    sessions.created_atが空の場合があるため、exported_atをフォールバックに使う
    """
    if days:
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        return f"AND COALESCE(created_at, exported_at) >= '{cutoff}'"
    return ""


def project_filter(project=None):
    """プロジェクトフィルタのWHERE句を生成"""
    if project:
        return f"AND project_path LIKE '%{project}%'"
    return ""


def report_summary(conn, days=None, project=None):
    """総合サマリーレポート"""
    df = date_filter(days)
    pf = project_filter(project)

    # 基本統計（created_at/modified_atが空の場合、messagesのtimestampから導出）
    row = conn.execute(f"""
        SELECT COUNT(DISTINCT s.project_path) as projects,
               COUNT(DISTINCT s.session_id) as sessions,
               SUM(s.message_count) as total_messages,
               MIN(m.min_ts) as first_session,
               MAX(m.max_ts) as last_session
        FROM sessions s
        LEFT JOIN (
            SELECT session_id, MIN(timestamp) as min_ts, MAX(timestamp) as max_ts
            FROM messages WHERE timestamp IS NOT NULL GROUP BY session_id
        ) m ON s.session_id = m.session_id
        WHERE 1=1 {df} {pf}
    """).fetchone()

    # メッセージ種別
    session_filter = f"session_id IN (SELECT session_id FROM sessions WHERE 1=1 {df} {pf})"
    msg_types = conn.execute(f"""
        SELECT type, COUNT(*) as count
        FROM messages WHERE {session_filter}
        GROUP BY type ORDER BY count DESC
    """).fetchall()

    # トークン消費
    tokens = conn.execute(f"""
        SELECT COALESCE(SUM(usage_input_tokens), 0) as total_input,
               COALESCE(SUM(usage_output_tokens), 0) as total_output
        FROM messages WHERE {session_filter} AND usage_input_tokens IS NOT NULL
    """).fetchone()

    # ツール使用トップ
    tools = conn.execute(f"""
        SELECT tool_name, COUNT(*) as count
        FROM tool_uses WHERE {session_filter}
        GROUP BY tool_name ORDER BY count DESC LIMIT 10
    """).fetchall()

    # プロジェクト別（最終利用日はmessagesのtimestampから導出）
    projects = conn.execute(f"""
        SELECT s.project_path, COUNT(DISTINCT s.session_id) as sessions,
               SUM(s.message_count) as messages,
               MAX(m.max_ts) as last_used
        FROM sessions s
        LEFT JOIN (
            SELECT session_id, MAX(timestamp) as max_ts
            FROM messages WHERE timestamp IS NOT NULL GROUP BY session_id
        ) m ON s.session_id = m.session_id
        WHERE 1=1 {df} {pf}
        GROUP BY s.project_path ORDER BY sessions DESC
    """).fetchall()

    # サブエージェント
    subagents = conn.execute(f"""
        SELECT agent_type, COUNT(*) as count
        FROM subagents WHERE {session_filter}
        GROUP BY agent_type ORDER BY count DESC
    """).fetchall()

    # 出力
    print("## Claude Code 利用状況レポート")
    print(f"\n分析日時: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    if days:
        print(f"期間: 直近{days}日間")
    if project:
        print(f"フィルタ: {project}")

    print("\n### 概要")
    print(f"- 分析期間: {row['first_session'][:10] if row['first_session'] else 'N/A'} ～ {row['last_session'][:10] if row['last_session'] else 'N/A'}")
    print(f"- プロジェクト数: {row['projects']}")
    print(f"- 総セッション数: {row['sessions']}")
    print(f"- 総メッセージ数: {row['total_messages'] or 0:,}")
    for mt in msg_types:
        print(f"  - {mt['type']}: {mt['count']:,}")
    total_input = tokens['total_input']
    total_output = tokens['total_output']
    print(f"- トークン消費: 入力 {total_input:,} ({total_input/1_000_000:.2f}M) / 出力 {total_output:,} ({total_output/1_000_000:.2f}M)")

    # コスト概算（Sonnetベース）
    cost_input = total_input / 1_000_000 * 3
    cost_output = total_output / 1_000_000 * 15
    print(f"- コスト概算 (Sonnet基準): ${cost_input + cost_output:.2f} (入力: ${cost_input:.2f} / 出力: ${cost_output:.2f})")

    print("\n### プロジェクト別")
    print("| プロジェクト | セッション | メッセージ | 最終利用 |")
    print("|---|---|---|---|")
    for p in projects:
        name = p['project_path'].split('/')[-1] if p['project_path'] else 'N/A'
        print(f"| {name} | {p['sessions']} | {p['messages'] or 0:,} | {p['last_used'][:10] if p['last_used'] else 'N/A'} |")

    print("\n### ツール利用 Top 10")
    total_tools = sum(t['count'] for t in tools)
    print("| ツール | 使用回数 | 割合 |")
    print("|---|---|---|")
    for t in tools:
        pct = t['count'] / total_tools * 100 if total_tools else 0
        print(f"| {t['tool_name']} | {t['count']:,} | {pct:.1f}% |")

    if subagents:
        print("\n### サブエージェント利用")
        print("| タイプ | 起動回数 |")
        print("|---|---|")
        for sa in subagents:
            print(f"| {sa['agent_type']} | {sa['count']} |")


def report_tokens(conn, days=None, project=None):
    """トークン・コスト分析"""
    df = date_filter(days)
    pf = project_filter(project)
    session_filter = f"session_id IN (SELECT session_id FROM sessions WHERE 1=1 {df} {pf})"

    # 日別トークン消費
    daily = conn.execute(f"""
        SELECT DATE(timestamp) as day,
               SUM(usage_input_tokens) as input_tokens,
               SUM(usage_output_tokens) as output_tokens
        FROM messages
        WHERE {session_filter} AND usage_input_tokens IS NOT NULL
        GROUP BY day ORDER BY day
    """).fetchall()

    # セッション別トークン消費トップ10
    heavy = conn.execute(f"""
        SELECT s.session_id, s.project_path,
               COALESCE(SUM(m.usage_input_tokens), 0) as input_tokens,
               COALESCE(SUM(m.usage_output_tokens), 0) as output_tokens,
               s.message_count
        FROM sessions s JOIN messages m ON s.session_id = m.session_id
        WHERE m.usage_input_tokens IS NOT NULL {df} {pf}
        GROUP BY s.session_id ORDER BY input_tokens DESC LIMIT 10
    """).fetchall()

    print("## トークン・コスト分析")

    print("\n### 日別トークン消費")
    print("| 日付 | 入力トークン | 出力トークン | 概算コスト |")
    print("|---|---|---|---|")
    for d in daily:
        inp = d['input_tokens'] or 0
        out = d['output_tokens'] or 0
        cost = inp / 1_000_000 * 3 + out / 1_000_000 * 15
        print(f"| {d['day']} | {inp:,} | {out:,} | ${cost:.2f} |")

    print("\n### トークン消費量トップ10セッション")
    print("| プロジェクト | メッセージ数 | 入力トークン | 出力トークン | 概算コスト |")
    print("|---|---|---|---|---|")
    for h in heavy:
        name = h['project_path'].split('/')[-1] if h['project_path'] else 'N/A'
        inp = h['input_tokens']
        out = h['output_tokens']
        cost = inp / 1_000_000 * 3 + out / 1_000_000 * 15
        print(f"| {name} | {h['message_count']} | {inp:,} | {out:,} | ${cost:.2f} |")


def report_tools(conn, days=None, project=None):
    """ツール利用パターン分析"""
    df = date_filter(days)
    pf = project_filter(project)
    session_filter = f"session_id IN (SELECT session_id FROM sessions WHERE 1=1 {df} {pf})"

    # ツール使用頻度
    tools = conn.execute(f"""
        SELECT tool_name, COUNT(*) as count,
               ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM tool_uses WHERE {session_filter}), 1) as pct
        FROM tool_uses WHERE {session_filter}
        GROUP BY tool_name ORDER BY count DESC
    """).fetchall()

    # プロジェクト×ツール
    cross = conn.execute(f"""
        SELECT s.project_path, tu.tool_name, COUNT(*) as count
        FROM tool_uses tu JOIN sessions s ON tu.session_id = s.session_id
        WHERE tu.session_id IN (SELECT session_id FROM sessions WHERE 1=1 {df} {pf})
        GROUP BY s.project_path, tu.tool_name
        ORDER BY s.project_path, count DESC
    """).fetchall()

    print("## ツール利用パターン分析")

    print("\n### ツール使用頻度")
    print("| ツール | 使用回数 | 割合 |")
    print("|---|---|---|")
    for t in tools:
        print(f"| {t['tool_name']} | {t['count']:,} | {t['pct']}% |")

    print("\n### プロジェクト別ツール利用")
    current_project = None
    for c in cross:
        name = c['project_path'].split('/')[-1] if c['project_path'] else 'N/A'
        if name != current_project:
            current_project = name
            print(f"\n**{name}**")
            print("| ツール | 使用回数 |")
            print("|---|---|")
        print(f"| {c['tool_name']} | {c['count']} |")


def report_sessions(conn, days=None, project=None):
    """セッション分析"""
    df = date_filter(days)
    pf = project_filter(project)

    # セッション長分布
    distribution = conn.execute(f"""
        SELECT
          CASE
            WHEN message_count <= 10 THEN '短い (1-10)'
            WHEN message_count <= 50 THEN '中程度 (11-50)'
            WHEN message_count <= 100 THEN '長い (51-100)'
            ELSE '非常に長い (100+)'
          END as category,
          COUNT(*) as count
        FROM sessions WHERE 1=1 {df} {pf}
        GROUP BY category ORDER BY MIN(message_count)
    """).fetchall()

    # 曜日別（messagesの最初のtimestampからセッション開始日を導出）
    weekdays = conn.execute(f"""
        SELECT
          CASE CAST(strftime('%w', min_ts) AS INTEGER)
            WHEN 0 THEN '日' WHEN 1 THEN '月' WHEN 2 THEN '火'
            WHEN 3 THEN '水' WHEN 4 THEN '木' WHEN 5 THEN '金' WHEN 6 THEN '土'
          END as weekday,
          CAST(strftime('%w', min_ts) AS INTEGER) as day_num,
          COUNT(*) as sessions
        FROM (
            SELECT s.session_id, MIN(m.timestamp) as min_ts
            FROM sessions s
            JOIN messages m ON s.session_id = m.session_id
            WHERE m.timestamp IS NOT NULL {df} {pf}
            GROUP BY s.session_id
        )
        WHERE min_ts IS NOT NULL
        GROUP BY day_num ORDER BY day_num
    """).fetchall()

    # ブランチ別
    branches = conn.execute(f"""
        SELECT git_branch, COUNT(*) as sessions, SUM(message_count) as messages
        FROM sessions WHERE git_branch IS NOT NULL {df} {pf}
        GROUP BY git_branch ORDER BY messages DESC LIMIT 10
    """).fetchall()

    print("## セッション分析")

    print("\n### セッション長分布")
    print("| カテゴリ | セッション数 |")
    print("|---|---|")
    for d in distribution:
        print(f"| {d['category']} | {d['count']} |")

    print("\n### 曜日別セッション数")
    print("| 曜日 | セッション数 |")
    print("|---|---|")
    for w in weekdays:
        print(f"| {w['weekday']} | {w['sessions']} |")

    if branches:
        print("\n### ブランチ別作業量 Top 10")
        print("| ブランチ | セッション数 | メッセージ数 |")
        print("|---|---|---|")
        for b in branches:
            print(f"| {b['git_branch']} | {b['sessions']} | {b['messages'] or 0:,} |")


def report_files(conn, days=None, project=None):
    """ファイル編集分析"""
    df = date_filter(days)
    pf = project_filter(project)
    session_filter = f"session_id IN (SELECT session_id FROM sessions WHERE 1=1 {df} {pf})"

    # よく編集されるファイル
    edits = conn.execute(f"""
        SELECT json_extract(tool_input, '$.file_path') as file_path, COUNT(*) as edits
        FROM tool_uses
        WHERE tool_name IN ('Edit', 'Write')
          AND json_extract(tool_input, '$.file_path') IS NOT NULL
          AND {session_filter}
        GROUP BY file_path ORDER BY edits DESC LIMIT 20
    """).fetchall()

    # よく読まれるファイル
    reads = conn.execute(f"""
        SELECT json_extract(tool_input, '$.file_path') as file_path, COUNT(*) as reads
        FROM tool_uses
        WHERE tool_name = 'Read'
          AND json_extract(tool_input, '$.file_path') IS NOT NULL
          AND {session_filter}
        GROUP BY file_path ORDER BY reads DESC LIMIT 20
    """).fetchall()

    print("## ファイル編集分析")

    print("\n### よく編集されるファイル Top 20")
    print("| ファイル | 編集回数 |")
    print("|---|---|")
    for e in edits:
        print(f"| {e['file_path']} | {e['edits']} |")

    print("\n### よく読まれるファイル Top 20")
    print("| ファイル | 読取回数 |")
    print("|---|---|")
    for r in reads:
        print(f"| {r['file_path']} | {r['reads']} |")


def report_subagents(conn, days=None, project=None):
    """サブエージェント分析"""
    df = date_filter(days)
    pf = project_filter(project)
    session_filter = f"session_id IN (SELECT session_id FROM sessions WHERE 1=1 {df} {pf})"

    # タイプ別
    types = conn.execute(f"""
        SELECT sa.agent_type, COUNT(DISTINCT sa.agent_id) as agents,
               COUNT(sm.uuid) as messages
        FROM subagents sa
        LEFT JOIN subagent_messages sm ON sa.agent_id = sm.agent_id
        WHERE sa.{session_filter}
        GROUP BY sa.agent_type ORDER BY agents DESC
    """).fetchall()

    print("## サブエージェント分析")
    print("| タイプ | 起動回数 | 総メッセージ数 |")
    print("|---|---|---|")
    for t in types:
        print(f"| {t['agent_type']} | {t['agents']} | {t['messages']} |")


def report_trends(conn, days=None, project=None):
    """時系列トレンド"""
    df = date_filter(days)
    pf = project_filter(project)

    # 週次トレンド（messagesのtimestampから導出）
    weekly = conn.execute(f"""
        SELECT strftime('%Y-W%W', min_ts) as week,
               COUNT(*) as sessions,
               SUM(message_count) as messages
        FROM (
            SELECT s.session_id, s.message_count, MIN(m.timestamp) as min_ts
            FROM sessions s
            JOIN messages m ON s.session_id = m.session_id
            WHERE m.timestamp IS NOT NULL {df} {pf}
            GROUP BY s.session_id
        )
        WHERE min_ts IS NOT NULL
        GROUP BY week ORDER BY week
    """).fetchall()

    print("## 時系列トレンド")

    print("\n### 週次トレンド")
    print("| 週 | セッション数 | メッセージ数 |")
    print("|---|---|---|")
    for w in weekly:
        print(f"| {w['week']} | {w['sessions']} | {w['messages'] or 0:,} |")


def main():
    parser = argparse.ArgumentParser(description="Claude Code会話データ分析")
    parser.add_argument("--db", help="データベースパス")
    parser.add_argument("--report", default="summary",
                        choices=["summary", "tokens", "tools", "sessions", "files", "subagents", "trends", "all"],
                        help="レポート種別")
    parser.add_argument("--project", help="プロジェクトフィルタ (部分一致)")
    parser.add_argument("--days", type=int, help="直近N日間に限定")
    parser.add_argument("--format", default="markdown", choices=["markdown", "json"],
                        help="出力形式")
    args = parser.parse_args()

    db_path = get_db_path(args.db)
    conn = connect(db_path)

    reports = {
        "summary": report_summary,
        "tokens": report_tokens,
        "tools": report_tools,
        "sessions": report_sessions,
        "files": report_files,
        "subagents": report_subagents,
        "trends": report_trends,
    }

    if args.report == "all":
        for name, func in reports.items():
            func(conn, days=args.days, project=args.project)
            print("\n---\n")
    else:
        reports[args.report](conn, days=args.days, project=args.project)

    conn.close()


if __name__ == "__main__":
    main()
