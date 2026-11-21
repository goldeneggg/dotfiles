# PRスレッド投稿手順

`--output` に `pr-thread` または `pr-thread-summary` が指定された場合に、この手順を使用する。

## 投稿前の準備

1. PR の node ID と現在の head commit OID を GitHub GraphQL API で取得する。レビュー中に head が変わった場合は、古い diff へ投稿しないため投稿を中止し、再レビューを促す。
2. 各指摘を `path`、`line`、`side`、`body` のオブジェクトへ変換する。`line` は対象 hunk の実ファイル行番号、`side` は追加・変更後の行なら `RIGHT`、削除前の行なら `LEFT` にする。複数行を対象にする場合だけ、連続した同一 side の `startLine` と `startSide` を加える。
3. `path` はリポジトリルートからの相対パスにし、行位置は取得済み PR diff の hunk に存在することを再確認する。本文とパスをシェル文字列連結で JSON に埋め込まず、JSON エンコーダーを使用する。

## 投稿

`addPullRequestReview` mutation を1回実行する。`AddPullRequestReviewInput` に `pullRequestId`、取得した `commitOID`、`event: COMMENT` を設定し、投稿対象のスレッドがあれば `threads` に含める。`gh api graphql --input {JSONファイル}` で送信する。

- `pr-thread` では `body` を省略し、スレッドの投稿対象が0件なら送信を省略する。
- `pr-thread-summary` では、レビュー全体の要約コメントを `body` に設定する。スレッドの投稿対象が0件でも、`threads` を省略して要約を投稿する。

```graphql
mutation AddPullRequestReview($input: AddPullRequestReviewInput!) {
  addPullRequestReview(input: $input) {
    pullRequestReview {
      url
      state
    }
  }
}
```

スレッドがある場合の `pr-thread-summary` のリクエスト例。

```json
{
  "query": "mutation AddPullRequestReview($input: AddPullRequestReviewInput!) { addPullRequestReview(input: $input) { pullRequestReview { url state } } }",
  "variables": {
    "input": {
      "pullRequestId": "PR node ID",
      "commitOID": "現在の head commit OID",
      "event": "COMMENT",
      "body": "レビュー全体の要約",
      "threads": [
        {"path": "src/example.ts", "line": 42, "side": "RIGHT", "body": "指摘本文"}
      ]
    }
  }
}
```

レスポンスの `pullRequestReview.state` が `COMMENTED` であることを確認し、`pullRequestReview.url` と投稿済みスレッド数を報告する。`pr-thread-summary` では要約を投稿したことも報告する。投稿結果の確認に PR の既存レビューコメントを読み込む必要はない。

## 失敗時

- mutation 実行前に発見した位置不整合は、該当指摘を投稿対象から外してチャットで報告する。
- mutation が明確な GraphQL エラーを返した場合は、そのエラーを報告し、入力を修正しない限り再試行しない。
- タイムアウト・接続断などで成否が不明な場合は再試行しない。既に投稿されている可能性があるため、ユーザーに PR で確認を依頼する。
