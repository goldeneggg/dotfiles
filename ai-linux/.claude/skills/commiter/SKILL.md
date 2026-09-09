---
name: commiter
description: 会話とgit差分からConventional Commits形式のメッセージを生成し、commit・必要ならpushを行う。--suggestは提案のみ、--autoはステージ済み変更のみを確認なしでcommit、--pushはcommit後にpushする。
---

# Commiter

ユーザーとのやり取りは日本語で行う。

## 引数

`[--suggest] [--auto] [--push] [--mode short|long] [--scope scope] [--lang en|ja] [--export-dir dir]`

- `--suggest`: 提案のみ。autoとpushは無効。
- `--auto`: 既にステージ済みの変更だけをcommitする。git addは行わない。対象がなければ終了する。
- `--push`: commit成功後にpushする。
- modeはshort、langはenが既定。ユーザーの明示した言語を優先する。type・scopeは英語。
- export-dirは提案モード専用。実行モードでは無視した旨を伝える。

## 差分と対象

git status、cached diff、必要なら未ステージ差分・未追跡ファイルを確認する。
既存のステージ状態と部分ステージを保持する。
会話から変更理由を把握し、実際の対象差分で内容を裏付ける。

通常モードでは、対象とメッセージを具体化してから確認する。
対象範囲が既にユーザーから指定されていれば再質問しない。
新たに未ステージ・未追跡ファイルを含める場合は、対象を明示して許可を得る。
承認されていないファイルを自動追加しない。

<!-- 要確認: 通常モードの最終commit確認は維持する。--autoだけが既定の確認省略モード。 -->

## メッセージ

Conventional Commitsのtype、必要なscope、簡潔なsubjectを使う。
shortは件名のみ。longは以下の規則で変更理由と必要な詳細を本文へ記載する。
件名は72文字以内を目安とし、long本文も72文字を目安に折り返す。URLや参照IDは分断しない。
破壊的変更は `!` と必要なBREAKING CHANGE説明を付ける。
Co-Authored-By行は付与しない。

### longのフォーマット

提案・エクスポート・commitで同じフォーマットを使う。ユーザーが今回明示した形式を優先し、それ以外は次の順で選ぶ。

1. `git rev-parse --show-toplevel` で取得した対象リポジトリのルートにある `.gitmessage`
2. `~/.gitmessage`
3. 下記の既定フォーマット

これは本スキルの選択規則であり、Gitの `commit.template` の探索規則ではない。
存在しない候補は次へ進む。存在するファイルは全文を読み、空または案内コメントのみで構成を指定していなければ次へ進む。読込エラーは黙って無視せず報告する。
選んだテンプレートの見出し・順序・必須項目を採用し、案内コメントとプレースホルダーは完成メッセージに残さない。
件名のConventional Commits形式、言語指定、Co-Authored-By禁止は維持する。両立できないテンプレートは競合点を示して確認する。

既定フォーマット（`[scope]` と `[!]` は任意要素の説明で、角括弧は出力しない）:

```text
<type>[(<scope>)][!]: <summary>

Why is this change necessary?

  <problem / motivation / previous behavior, and what changes>

Why this approach?

  <reasoning / constraints / trade-offs, if non-obvious>

BREAKING CHANGE: <impact and migration>
Refs: <issue or URL>
```

既定フォーマットでは、見出しの後に空行を置き、各節の本文は折り返した行も含めて半角2スペースでインデントする。件名・見出し・フッターはインデントしない。空行にスペースは入れず、折り返し幅はインデントを含めて72文字を目安とする。
変更理由は必須とし、会話・差分で裏付けられる内容を書く。採用理由に非自明な説明がなければ `Why this approach?` ごと省略する。
`BREAKING CHANGE` は破壊的変更時のみ、`Refs` は実在する関連参照が分かる場合のみ付ける。空の項目や `Optional trailers` 見出しは出力せず、末尾のフッター群を本文から空行で分離する。
見出しと説明文はlangに合わせる。`BREAKING CHANGE`・`Refs` は翻訳しない。
既定の見出しに `#` は付けない。Gitのcleanupによるコメント削除を避けるため。

## 実行

1. 通常モードでは対象とメッセージへの必要な確認を終える。autoでは生成内容を共有して続行する。
2. 許可された対象だけをステージし、cached diffが意図した内容か確認する。
3. メッセージを安全に渡してcommitする。longは選択した形式で完成メッセージをファイルに書き、`git commit --cleanup=whitespace -F <file>` で渡す。`-F` ではGitのテンプレート機構は働かないため、テンプレートの読込・反映は事前に行う。案内コメントは事前に除去し、テンプレートが指定した本文の見出しは保持する。
4. pre-commit hookを省略しない。失敗時は原因を確認し、依頼内の修正許可がある場合だけ修正・再検証する。許可がなければ失敗と必要な修正を報告する。
5. commit成功後、SHA・件名・残る変更を確認する。longは保存された本文も確認し、hook等によって提示した内容から変更されていれば報告する。

## Push

push指定がある場合だけ実行する。
先に現在ブランチ、remote、追跡先を確認する。
main/masterへの直接pushは、実行前に追加確認する。autoでも省略しない。
追跡先がなければ確認したremoteとbranchでupstreamを設定する。
force pushや別remoteへの変更で失敗を回避しない。

## 提案モード

メッセージと必要なら分割案を提示する。
export-dir指定時だけ `commit-{YYYYMMDDHHMMSS}-{title}.txt` へ保存する。
保存未指定を理由に追加質問しない。
タイトルのパス文字を安全化し、既存ファイルを無断で置換しない。

## 完了報告

提案、commit、pushそれぞれの成否を区別し、SHA、残る変更、失敗理由を簡潔に報告する。
