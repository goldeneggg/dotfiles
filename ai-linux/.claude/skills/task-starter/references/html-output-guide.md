# HTML出力ガイド

Phase 1 でユーザーが **HTML形式** を選んだ場合のドキュメント生成ルール。Markdown 形式（既定）を選んだ場合はこのガイドは不要で、従来どおり `.md` を生成する。

なぜ自己完結HTMLか: ビルドや外部CSSなしで、ブラウザで開くだけで体裁が整い Mermaid 図も描画されるため。配布・共有がファイル1枚で完結する。

## 適用範囲と拡張子

HTML選択時は、進捗正本を除くドキュメントを `.html` で生成する。`progresses/{ID}/PROGRESS.md` だけは、`../../_shared/references/task-management-contract.md` に従ってMarkdownへ固定する。

| ドキュメント | Markdown時 | HTML時 |
| --- | --- | --- |
| プロジェクトREADME | `README.md` | `README.html` |
| ロードマップ | `todos/README.md` | `todos/README.html` |
| 仕様書 | `specs/{name}.md` | `specs/{name}.html` |
| TODO | `todos/{ID}/README.md` | `todos/{ID}/README.html` |
| 現状分析 | `references/{name}.md` | `references/{name}.html` |
| 進捗正本 | `progresses/{ID}/PROGRESS.md` | `progresses/{ID}/PROGRESS.md` |

`README.html` と `todos/README.html` は `init_project.py --format html` が雛形を生成する。`specs/` `todos/{ID}/` `references/` は Claude がテンプレートを元に生成する。

## 共有HTMLシェルの使い方

全HTMLは `references/templates/html-shell.html` を単一ソースとして使う。スクリプトもこのシェルを使うので、Claude が手書きする際も同じシェルに揃えることで体裁が統一される。

手順:
1. `references/templates/html-shell.html` を読む
2. `{{TITLE}}` を `<title>` 用文字列に置換
3. `{{BODY}}` を本文HTML（`<h1>` 以降）に置換
4. 対象パスに `.html` で書き出す

シェルには埋め込みCSS（GitHub風・ダークモード対応）と Mermaid の CDN 読込（`startOnLoad`）が含まれる。**`<head>` やCSSを再発明しないこと**。

## Markdownテンプレート → HTML本文への変換規約

`references/templates/*.md` の構造を、意味の同じHTMLに移す:

| Markdown | HTML |
| --- | --- |
| `# 見出し` / `## 見出し` | `<h1>` / `<h2>` / `<h3>` |
| `- 項目` | `<ul><li>項目</li></ul>` |
| `- [ ] 項目` | `<li><input type="checkbox" disabled> 項目</li>` |
| `> 引用` | `<blockquote>...</blockquote>` |
| 表（パイプ記法） | `<table><tr><th>...</th></tr>...</table>` |
| `` `code` `` / コードブロック | `<code>` / `<pre><code>` |
| `<!-- コメント -->` | `<!-- コメント -->`（HTMLでもそのまま使える） |

ユーザー入力（プロジェクト名・概要等）を本文へ差し込む際は `&` `<` `>` をエスケープする。

TODOの「作業内容」と「受け入れ条件」はチェックボックスへ変換しない。`W-01` / `AC-01` のIDを `<strong>` で保持した静的なリストにし、状態と検証根拠は `PROGRESS.md` だけに記録する。

## Mermaid 図（ロードマップの依存DAG）

Markdownの ` ```mermaid ... ``` ` ブロックは、HTMLでは **`<pre class="mermaid">`** に置く。シェルが `startOnLoad` で自動描画する。

```html
<pre class="mermaid">
graph TD
  001[001-setup]
  002[002-xxx]
  001 --> 002

  classDef parallel fill:#cfe8ff,stroke:#1e88e5;
  class 002 parallel;
</pre>
```

注意: `<pre>` 内では `>` を含む矢印 `-->` をそのまま書ける（属性値ではないため）。ただしノードラベルに `<` `>` を含める場合は実体参照にする。

## TODO の依存メタデータ（Phase 4 が読む）

Markdownでは YAML フロントマターで持つ依存メタを、HTMLでは **`<script type="application/x-task-meta">`** に YAML で埋め込む。ブラウザはこの type を実行・表示しないため、レイアウトを壊さずに機械可読データを1ファイルに同梱できる。

`todos/{ID}/README.html` の `<body>` 先頭に置く:

```html
<script type="application/x-task-meta">
id: "001-setup"
estimated_time: "30m"
depends_on: []
parallel_group: null
priority: "high"
parallelizable: false
</script>

<h1>TODO: 初期セットアップ</h1>
...
```

任意で、人にも見えるメタ表示を `<div class="task-meta-view">` で併記してよい（machine-readable な `<script>` とは別に用意する。両方置く場合は値を一致させる）。

### Phase 4 でのメタ読み取り

- **Markdown時**: 各 `todos/{ID}/README.md` 冒頭の YAML フロントマターを読む
- **HTML時**: 各 `todos/{ID}/README.html` の `<script type="application/x-task-meta">` ブロックを Read で取得し、内部のYAMLをパースする

いずれも `id` / `depends_on` / `parallel_group` を集約して依存DAG・クリティカルパスを算出する。

## task-performer との互換に関する注意

`task-performer` スキルは `todos/{ID}/README.md`（Markdown）を前提に動く。HTML形式を選ぶと TODO は `README.html` になるため、HTMLで生成したプロジェクトを task-performer でそのまま実行する場合は、ユーザーにこの差異を伝えること。閲覧・共有重視で HTML、実行自動化重視なら Markdown が無難である旨を案内する。
