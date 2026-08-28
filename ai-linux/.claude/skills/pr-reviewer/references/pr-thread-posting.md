# PRスレッド投稿手順

`--output pr-thread` が指定された場合だけ、この手順を使用する。

## 投稿前の準備

1. PR の node ID と現在の head commit OID を GitHub GraphQL API で取得する。レビュー中に head が変わった場合は、古い diff へ投稿しないため投稿を中止し、再レビューを促す。
2. 各指摘を `path`、`line`、`side`、`body` のオブジェクトへ変換する。`line` は対象 hunk の実ファイル行番号、`side` は追加・変更後の行なら `RIGHT`、削除前の行なら `LEFT` にする。複数行を対象にする場合だけ、連続した同一 side の `startLine` と `startSide` を加える。
3. `path` はリポジトリルートからの相対パスにし、行位置は取得済み PR diff の hunk に存在することを再確認する。本文とパスをシェル文字列連結で JSON に埋め込まず、JSON エンコーダーを使用する。

## 投稿

`AddPullRequestReviewInput` の `threads` を使い、すべてのスレッドを1回の `addPullRequestReview` mutation で送信する。`pullRequestId`、取得した `commitOID`、`event: COMMENT`、スレッド配列を含める。`gh api graphql --input {JSONファイル}` を使うと、本文に改行や引用符があっても安全に渡せる。

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

リクエストの JSON は、概ね次の構造にする。

```json
{
  "query": "mutation AddPullRequestReview($input: AddPullRequestReviewInput!) { addPullRequestReview(input: $input) { pullRequestReview { url state } } }",
  "variables": {
    "input": {
      "pullRequestId": "PR node ID",
      "commitOID": "現在の head commit OID",
      "event": "COMMENT",
      "threads": [
        {"path": "src/example.ts", "line": 42, "side": "RIGHT", "body": "指摘本文"}
      ]
    }
  }
}
```

成功レスポンスの `pullRequestReview.url` を取得し、投稿済みスレッド数とともに報告する。投稿結果の確認に PR の既存レビューコメントを読み込む必要はない。

## 失敗時

- mutation 実行前に発見した位置不整合は、該当指摘を投稿対象から外してチャットで報告する。
- mutation が明確な GraphQL エラーを返した場合は、そのエラーを報告し、入力を修正しない限り再試行しない。
- タイムアウト・接続断などで成否が不明な場合は再試行しない。既に投稿されている可能性があるため、ユーザーに PR で確認を依頼する。
