---
name: md-converter
description: |
  テキストコンテンツや各種フォーマット（HTML, RST, AsciiDoc, プレーンテキスト等）をMarkdown形式に変換するスキル。
  以下の状況で使用:
    (1) ユーザーが「このテキストをmarkdownに変換して」「HTMLをmdに変換して」と依頼した時
    (2) ユーザーが「このファイルをmarkdownにして」とファイルパスを提示した時
    (3) ユーザーが明示的に「/md-converter」を実行した時
    (4) RST, AsciiDoc, HTMLなどからmarkdownへの変換が必要な時
    (5) 形式が不明なテキストをmarkdownとして整形したい時
---

# md-converter

HTML, RST, AsciiDoc, プレーンテキストをGitHub Flavored Markdown (GFM) に変換する。

## ワークフロー

### Step 1: 入力を確認する

- ファイルパスが提供された場合 → ファイルを読み込む
- テキストコンテンツが直接提供された場合 → そのまま利用

### Step 2: フォーマットを判定する

| 判定方法 | 優先度 |
|---------|--------|
| ユーザーが明示指定 | 最高 |
| ファイル拡張子 (.html/.htm, .rst, .adoc/.asciidoc) | 高 |
| コンテンツのパターン解析 | 中 |

**コンテンツからの判定ヒント:**
- `<html>`, `<p>`, `<div>` タグ → HTML
- `.. ` ディレクティブ, `====` アンダーライン見出し → RST
- `=====` タイトル区切り, `[source,lang]` ブロック → AsciiDoc
- 判定不能 → プレーンテキストとして処理

### Step 3: 変換を実行する

**HTMLまたは構造化フォーマット（RST/AsciiDoc）の場合**

`scripts/convert.py` を使用してpandocで変換する:

```bash
# ファイルの場合（拡張子で自動判定）
python3 scripts/convert.py <input_file>

# フォーマットを明示指定
python3 scripts/convert.py <input_file> --from html
python3 scripts/convert.py <input_file> --from rst
python3 scripts/convert.py <input_file> --from asciidoc

# stdin から変換
echo "content" | python3 scripts/convert.py - --from html

# ファイルに保存
python3 scripts/convert.py <input_file> --output output.md
```

**スクリプトパス:** `scripts/convert.py`

**プレーンテキストの場合**

pandocではなくClaudeが直接解析・変換する:
1. 見出し候補（短い行、大文字、数字付き）を `#` 見出しに変換
2. 箇条書き（`-`, `*`, `・`, 数字）を適切なリスト記法に統一
3. コードブロックのような等幅テキストをバッククォートで囲む
4. 表形式のデータをMarkdownテーブルに変換

### Step 4: 結果を返す

- 変換済みmarkdownをチャットで返す（デフォルト）
- ユーザーがファイル保存を希望する場合は `--output` オプションを使用
- 出力ファイル名が未指定の場合は入力ファイル名の拡張子を `.md` に変更して提案
