---
name: commit-message-suggester
description: |
  会話内容とgit diffからConventional Commits準拠のコミットメッセージを提案するスキル。
  shortモード（1行概要）とlongモード（複数行markdown詳細）を選択可能。

  以下の状況で使用:
  (1) ユーザーが「コミットメッセージを提案して」「コミットメッセージを考えて」と依頼した時
  (2) ユーザーが「この変更のコミットメッセージは？」と聞いた時
  (3) ユーザーが明示的に「/commit-message-suggester」を実行した時
  (4) ユーザーが「コミットメッセージを書いて」「commit messageを作って」と依頼した時
  (5) ユーザーが「何をコミットすればいい？」「どうコミットする？」と相談した時
  (6) 実装完了後にコミットメッセージの提案を求められた時

  コミットの実行自体はこのスキルの責務ではない。メッセージの提案のみを行う。
  コミット実行を求められた場合は通常のgitワークフローで対応すること。
---

# commit-message-suggester

会話コンテキストとgitの差分情報を分析し、Conventional Commits仕様に準拠したコミットメッセージを提案する。

**ユーザーとのやり取りはすべて日本語で行う。**

## 引数

```
/commit-message-suggester [--mode short|long] [--scope <scope>] [--lang <language>] [--export-dir <dir>]
```

- `--mode` (任意): `short`（デフォルト）または `long`
- `--scope` (任意): スコープを明示的に指定（省略時は差分から自動推定）
- `--lang` (任意): メッセージの記述言語（デフォルト: `en`）。`ja` で日本語、`en` で英語。type と scope は常に英語
- `--export-dir` (任意): 提案したメッセージをファイルに保存する場合のディレクトリパス。指定された場合、"commit-{`date +'%Y%m%d%H%M%S'` コマンドの実行結果}-{title}.txt" というファイル名でファイルに書き出す（`git commit -F` で使用する想定）。ディレクトリが未指定ならAskUserQuestionで確認（デフォルトは `./tmp/`

## 実行フロー

### Step 1: 差分情報の収集

以下の順序でgitの差分を取得する:

1. `git diff --cached --stat` でステージ済み変更のサマリを確認
2. ステージ済み変更がある場合 → `git diff --cached` で詳細を取得
3. ステージ済み変更がない場合 → `git diff --stat` と `git diff` で未ステージの変更を取得
4. どちらもない場合 → `git status` で未追跡ファイルを確認

差分が一切ない場合は「コミット対象の変更がありません」と報告して終了する。

### Step 2: 会話コンテキストの分析

現在の会話履歴から以下を抽出する:

- ユーザーが依頼した作業内容（「なぜ」この変更が必要だったか）
- 実装中に行った判断や設計上のトレードオフ
- 解決した問題やバグの内容

会話コンテキストが不十分な場合は差分内容のみから推定する。会話コンテキストがあると「なぜ」の部分がより正確になるため、可能な限り活用する。

### Step 3: Conventional Commitsの分類

差分と会話コンテキストから、以下の要素を決定する:

#### type（必須）

| type | 用途 |
|------|------|
| `feat` | 新機能の追加 |
| `fix` | バグ修正 |
| `docs` | ドキュメントのみの変更 |
| `style` | コードの意味に影響しない変更（フォーマット、セミコロン等） |
| `refactor` | バグ修正でも機能追加でもないコード変更 |
| `perf` | パフォーマンス改善 |
| `test` | テストの追加・修正 |
| `build` | ビルドシステムや外部依存の変更 |
| `ci` | CI設定ファイルやスクリプトの変更 |
| `chore` | その他（上記に当てはまらない保守作業） |

複数のtypeにまたがる変更の場合は、最も主要な変更のtypeを選択する。ただし、変更が明確に分離可能な場合は「複数のコミットに分けることを推奨する」旨をアドバイスとして付記する。

#### scope（任意）

変更の影響範囲を表す短い名詞。差分のファイルパスやディレクトリ構造から推定する。

推定ルール:
- 変更が単一のモジュール/ディレクトリに閉じている → そのディレクトリ名
- 複数にまたがるが共通の親がある → 親ディレクトリ名
- 広範囲 → 省略

`--scope` 引数で明示指定された場合はそれを優先する。

#### description（必須）

変更内容を簡潔に表す命令形フレーズ。先頭は小文字。末尾にピリオドは付けない。

`--lang en`（デフォルト）の場合は英語で記述する:
- 良い例: `add user authentication with JWT`
- 悪い例: `Added user authentication.` / `User authentication was added`

`--lang ja` の場合は日本語で記述する:
- 良い例: `JWTによるユーザー認証を追加`
- 悪い例: `JWTによるユーザー認証を追加しました。`

### Step 4: メッセージの生成

#### shortモード

1行で完結するメッセージを生成する:

```
type(scope): description
```

scopeがない場合:

```
type: description
```

**制約:**
- 全体で72文字以内を目指す（超える場合はdescriptionを短縮）
- Breaking changeがある場合は `type(scope)!: description` とする

**出力例:**

```
feat(auth): add JWT-based authentication
```

```
fix: resolve null pointer in user profile handler
```

#### longモード

ヘッダー行に加えて、本文とフッターを含むメッセージを生成する:

```
type(scope): description

本文（なぜこの変更が必要だったか、何を変えたかの詳細）

- 変更点1の説明
- 変更点2の説明
- 変更点3の説明

BREAKING CHANGE: (もしあれば)破壊的変更の説明
```

**本文の書き方:**
- 最初の段落で「なぜ」この変更が必要だったかを説明する（会話コンテキストから抽出）
- 箇条書きで主要な変更点を列挙する（差分から抽出）
- 72文字で折り返す
- `--lang` で指定された言語で記述する（デフォルト: 英語）

**出力例:**

```
feat(auth): add JWT-based authentication

User authentication was previously handled by session cookies,
which caused issues with mobile API clients. JWT tokens provide
a stateless authentication mechanism that works across all clients.

- add JWT token generation and validation middleware
- implement refresh token rotation
- add token expiry configuration via environment variables
- update user login endpoint to return JWT pair

BREAKING CHANGE: /api/login response format changed from
session cookie to JSON body with access_token and refresh_token
```

**`--lang ja` での出力例:**

```
feat(auth): JWTベースの認証を追加

セッションCookieによる認証はモバイルAPIクライアントで問題が
発生していた。JWTトークンにより、全クライアントで動作する
ステートレスな認証機構を実現する。

- JWTトークンの生成・検証ミドルウェアを追加
- リフレッシュトークンのローテーションを実装
- 環境変数によるトークン有効期限の設定を追加
- ユーザーログインエンドポイントをJWTペア返却に変更

BREAKING CHANGE: /api/login のレスポンス形式がセッションCookie
からaccess_tokenとrefresh_tokenを含むJSONボディに変更
```

### Step 5: 提案の提示

生成したメッセージを以下の形式でユーザーに提示する:

**shortモードの場合:**

提案するメッセージをコードブロックで表示する。

**longモードの場合:**

提案するメッセージをコードブロックで表示する。

**共通:**
- 複数のコミットに分割すべきと判断した場合は、分割案も併せて提示する
- typeの選択理由が微妙な場合は、代替案も提示する（例: 「`refactor` としましたが、`chore` も妥当です」）

## 注意事項

- このスキルはメッセージの**提案のみ**を行う。`git commit` の実行は行わない
- ユーザーが提案を採用するかどうかはユーザーの判断に委ねる
- `--lang` で言語を指定可能。デフォルトは英語（`en`）。日本語は `ja`。type と scope は常に英語で記述する
- `--lang` 未指定でもユーザーが会話中に「日本語で」等と指定した場合は `--lang ja` と同等に扱う
