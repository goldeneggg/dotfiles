# タスクロードマップ: {プロジェクト名}

このドキュメントは `todos/` 配下のタスク群について、依存関係・並行実行可能性・推奨ワークロードをまとめた俯瞰ドキュメントです。各タスクの詳細は `todos/{連番}-{name}/README.md` を参照してください。

## タスク一覧

| ID | タスク名 | 概要 | 前提タスク | 並行グループ | 推定時間 | 並行実行推奨 |
| --- | --- | --- | --- | --- | --- | --- |
| 001-setup | 初期セットアップ | ... | - | - | 30m | - |
| 002-xxx | ... | ... | 001-setup | A | 1h | ✅ |
| 003-xxx | ... | ... | 001-setup | A | 1h | ✅ |
| 004-xxx | ... | ... | 002-xxx, 003-xxx | - | 2h | - |

## 依存DAG

```mermaid
graph TD
  001[001-setup]
  002[002-xxx]
  003[003-xxx]
  004[004-xxx]
  001 --> 002
  001 --> 003
  002 --> 004
  003 --> 004

  classDef parallel fill:#cfe8ff,stroke:#1e88e5;
  class 002,003 parallel;
```

> 凡例: 青塗りノード = 同じ並行グループ（同時実行可能）

## クリティカルパス

最長経路: `001-setup → 002-xxx → 004-xxx` (合計: **約3.5時間**)

このパス上のタスクが全体完了時間を決定する。最短化したい場合は、ここのタスクを優先的に実行・スリム化する。

## 並行実行可能なタスク群

### Group A
- 002-xxx
- 003-xxx
- **前提**: 001-setup 完了
- **非干渉性**: 編集対象ファイルが分離されている（具体的には `src/api/` と `src/ui/`）
- **推奨**: subagentで並列実行（後述「ステップ2」参照）

---

## 推奨ワークロード

最速完了のため、Claude Code の以下機能を組み合わせる。

### Step 1: 順次実行が必須なタスク

```
001-setup を task-performer で実行
```

完了を待ってから Step 2 へ。

### Step 2: 並行可能タスクを subagent で並列実行

1メッセージ内で複数の Agent ツール呼び出しを行うことで並列実行する。各タスクが同じファイルを編集する可能性がある場合は `isolation: worktree` を指定して隔離する。

```text
Group A の002-xxx と 003-xxx を以下の指示で並列実行:

Agent #1:
  subagent_type: general-purpose
  description: "002-xxx を実装"
  prompt: "todos/002-xxx/README.md の作業内容を完了させる。受け入れ条件をすべて満たすこと。"
  isolation: worktree   # 並行で他Agentと同じファイルを触る恐れがあるなら指定

Agent #2:
  subagent_type: general-purpose
  description: "003-xxx を実装"
  prompt: "todos/003-xxx/README.md の作業内容を完了させる。受け入れ条件をすべて満たすこと。"
  isolation: worktree
```

### Step 3: 統合タスクを実行

Group A の全Agent完了後、`004-xxx` を実行。両worktreeでの変更を統合する場合は事前にmergeまたはrebaseする。

### Step 4 (オプション): /goal で全体を自動完走させる

```text
/goal todos/ 配下のすべてのタスクの受け入れ条件が満たされており、`<プロジェクトのテストコマンド>` が成功している
```

`/goal` は完了条件を満たすまでターン継続するため、上記Step 1-3 の手動オーケストレーションを Claude 自身に委ねる選択肢として有効。条件が検証可能（テストコマンドの exit 0 など）であることが重要。

---

## ワークロード選択ガイド

| 状況 | 推奨アプローチ |
| --- | --- |
| 並行可能タスクが2-5個、ファイル独立 | **Subagents + worktree並列実行**（上記Step 2） |
| 5-30個の機械的に類似した変更 | `/batch` でworktree-isolated subagentに自動分散 |
| バックグラウンド長時間実行を複数走らせたい | `claude agents` (Agent View) で各タスクをバックグラウンドセッション化 |
| すべて完走させて結果だけ確認したい | `/goal` + auto mode で全自動 |
| タスク数が少なく依存が直線的 | `task-performer` で順次実行 |
| 完了通知が欲しい | Stop hook でデスクトップ通知 / Slack 通知 |

---

## 進捗管理

- 各タスク完了時に該当 `todos/{ID}/README.md` の受け入れ条件にチェックを入れる
- 全タスク完了時にこの README.md 末尾の「完了宣言」にサインオフ

## 完了宣言

- [ ] すべての TODO が完了
- [ ] 受け入れ条件すべて達成
- [ ] テスト/lint パス
- [ ] レビュー承認済み
