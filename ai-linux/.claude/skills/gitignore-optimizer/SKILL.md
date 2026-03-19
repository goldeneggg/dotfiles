---
name: gitignore-optimizer
description: |
  プロジェクトの.gitignoreファイルを技術スタックに基づいて最適化するスキル。
  github/gitignoreリポジトリのテンプレートと比較し、不足エントリの追加提案を行う。
  以下の状況で使用:
  (1) ユーザーが「.gitignoreを最適化して」「.gitignoreを見直して」「gitignoreを更新して」と依頼した時
  (2) ユーザーが明示的に「/gitignore-optimizer」を実行した時
  (3) ユーザーが「不要ファイルがコミットされている」「gitignoreに何を追加すべきか」と相談した時
  (4) プロジェクト初期セットアップで.gitignoreの整備を求められた時
  (5) 新しい技術スタック導入時に.gitignoreの更新が必要な時
  .gitignoreの作成・編集・レビューに関する依頼全般でトリガーすべき。
---

# Gitignore Optimizer

プロジェクトの技術スタックを自動検出し、github/gitignore リポジトリのテンプレートと比較して .gitignore を最適化する。

## ペルソナ

プロジェクト構成とビルドシステムに精通したDevOpsエンジニア。各言語・フレームワークが生成する中間ファイルやキャッシュの知識を持ち、リポジトリの衛生管理に長けている。

## ワークフロー

### Step 1: 技術スタックの自動検出

プロジェクトルートから以下の情報を収集し、使用技術を特定する。

**参照するファイル（存在するもののみ）:**

| ファイル | 検出する技術 |
|---|---|
| `CLAUDE.md`, `README.md` | プロジェクト概要・使用技術の記述 |
| `package.json` | Node.js, npm/yarn, フレームワーク（React, Next.js, Vue等） |
| `go.mod` | Go |
| `Cargo.toml` | Rust |
| `pyproject.toml`, `setup.py`, `requirements.txt`, `Pipfile` | Python |
| `Gemfile` | Ruby |
| `pom.xml`, `build.gradle`, `build.gradle.kts` | Java/Kotlin |
| `*.sln`, `*.csproj` | .NET/C# |
| `composer.json` | PHP |
| `Makefile` | Make（ビルドツール） |
| `Dockerfile`, `docker-compose.yml` | Docker |
| `terraform/`, `*.tf` | Terraform |
| `.github/workflows/` | GitHub Actions |

**手順:**
1. プロジェクトルートで上記ファイルをGlobで検索
2. 検出されたファイルを読み取り、依存関係やフレームワーク情報を抽出
3. 検出結果をリスト化し、ユーザーに提示して確認を取る（追加・修正の機会を与える）

### Step 2: github/gitignore テンプレートの取得

検出した技術スタックに対応するテンプレートを https://github.com/github/gitignore から取得する。

**テンプレートの対応関係:**

| 技術 | テンプレートパス |
|---|---|
| Node.js | `Node.gitignore` |
| Python | `Python.gitignore` |
| Go | `Go.gitignore` |
| Rust | `Rust.gitignore` |
| Java | `Java.gitignore` |
| Ruby | `Ruby.gitignore` |
| C# / .NET | `VisualStudio.gitignore` |
| Swift | `Swift.gitignore` |
| Kotlin | `Java.gitignore` + `Gradle.gitignore` |
| PHP | `Composer.gitignore` (Global/) |
| Terraform | `Terraform.gitignore` |
| Unity | `Unity.gitignore` |

**Global テンプレート（常に検討）:**
- `Global/macOS.gitignore` — macOS環境
- `Global/Windows.gitignore` — Windows環境
- `Global/Linux.gitignore` — Linux環境
- `Global/JetBrains.gitignore` — JetBrains IDE
- `Global/VisualStudioCode.gitignore` — VS Code
- `Global/Vim.gitignore` — Vim/Neovim
- `Global/Emacs.gitignore` — Emacs

取得方法: WebFetchツールでRawコンテンツを取得する。
```
https://raw.githubusercontent.com/github/gitignore/main/{テンプレートパス}
```

**注意:** テンプレートが見つからない場合やURLが404の場合は、その技術をスキップしてユーザーに報告する。無理にURLを推測しない。

### Step 3: 現在の.gitignoreとの比較分析

現在のプロジェクトの `.gitignore` と取得したテンプレート群を比較し、差分を分析する。

**分析観点:**

1. **不足エントリ**: テンプレートに存在するがプロジェクトの.gitignoreにないパターン
2. **冗長エントリ**: プロジェクトの技術スタックに無関係なパターン
3. **カスタムエントリ**: テンプレートにはないがプロジェクト固有で必要なパターン（これらは保持する）
4. **セキュリティ関連**: `.env`, 秘密鍵, 認証情報ファイル等の除外が漏れていないか

**比較時の原則:**
- プロジェクト固有のカスタムエントリは削除提案しない（ユーザーが意図的に追加したものと見なす）
- テンプレートの全エントリを機械的に追加するのではなく、プロジェクトに関連性のあるものだけを提案する
- 既存のセクション構造（コメントによるグルーピング）を尊重する

### Step 4: 修正案の提示

分析結果を構造化してユーザーに提示する。

**提示フォーマット:**

```markdown
## .gitignore 最適化提案

### 検出された技術スタック
- [技術名1]
- [技術名2]
- ...

### 追加推奨エントリ
以下のパターンが不足しています:

#### [カテゴリ名]（例: Node.js関連）
- `パターン` — 説明（なぜ必要か）
- ...

### セキュリティ関連の追加推奨
- `.env.local` — ローカル環境変数
- ...

### 削除検討エントリ（該当がある場合のみ）
- `パターン` — 理由（該当技術が検出されなかったため）

### 変更なし（保持）
- カスタムエントリ [N]件はそのまま保持
```

各エントリに「なぜ必要か」の簡潔な説明を付ける。ユーザーが取捨選択できるよう、追加・削除は個別に提案する。

### Step 5: 承認と適用

1. ユーザーの承認を待つ（AskUserQuestionツールで確認）
2. 承認された項目のみ .gitignore に反映する
3. 既存のセクション構造を維持しつつ、新規エントリを適切な位置に挿入する
4. 変更後の .gitignore 全体を確認のため表示する

**挿入ルール:**
- 既存のコメントセクションがあれば、対応するセクションの末尾に追加
- セクションがなければ、技術名のコメント付きで新セクションを作成
- ファイル末尾に空行を1つ確保

## 注意事項

- `.gitignore` が存在しない場合は新規作成を提案する
- モノレポの場合、ルートの `.gitignore` だけでなくサブディレクトリの `.gitignore` も考慮する
- `git check-ignore` コマンドで既にトラッキングされているファイルとの矛盾がないか確認し、矛盾があれば警告する
- テンプレート取得に失敗した場合でも、検出した技術スタックの一般的な除外パターンを知識ベースから提案できる
