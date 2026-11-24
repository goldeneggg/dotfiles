# PRスレッド投稿手順

`--output` に `pr-thread`、`pr-thread-summary`、`pr-thread-summary-after` のいずれかが指定された場合に、この手順を使用する。

## 投稿前の準備

1. 各指摘を `path`、`line`、`side`、`body` のオブジェクトへ変換する。`line` は対象 hunk の実ファイル行番号、`side` は追加・変更後の行なら `RIGHT`、削除前の行なら `LEFT` にする。複数行を対象にする場合だけ、連続した同一 side の `startLine` と `startSide` を加える。
2. `path` はリポジトリルートからの相対パスにし、行位置は取得済み PR diff の hunk に存在することを再確認する。本文とパスをシェル文字列連結で JSON に埋め込まず、JSON エンコーダーを使用する。
3. 投稿直前に PR の node ID と現在の head commit OID を GitHub GraphQL API で取得する。head がレビュー対象と一致することを確認してから送信する。

## Review の提出

投稿対象のスレッドがある場合、`--submit` が指定された場合、または `pr-thread-summary` の場合に、`addPullRequestReview` mutation を1回実行する。`AddPullRequestReviewInput` に `pullRequestId`、レビュー対象の `commitOID`、`event` を設定し、投稿対象のスレッドがあれば `threads` に含める。`--submit` を指定した場合は [Review種別の表](../SKILL.md#prへの投稿レビュー提出) の `event` を使い、省略時は `COMMENT` を使う。`gh api graphql --input <JSONファイル>` で送信する。

- `pr-thread` と `pr-thread-summary-after` では、`--submit` で `COMMENT` または `REQUEST_CHANGES` を選んだ場合に限り、判定理由を簡潔に `body` に入れる。
- `pr-thread-summary` では、総合判定、重要度別件数、主要な指摘、推奨アクション、未確認事項を `body` に要約する。PR説明の検証結果や修正案があれば、その要点も含める。

```graphql
mutation AddPullRequestReview($input: AddPullRequestReviewInput!) {
  addPullRequestReview(input: $input) {
    pullRequestReview {
      url
      state
      submittedAt
    }
  }
}
```

`--output pr-thread --submit` で、任意対応の指摘を投稿しつつ承認するリクエスト例。

```json
{
  "query": "mutation AddPullRequestReview($input: AddPullRequestReviewInput!) { addPullRequestReview(input: $input) { pullRequestReview { url state submittedAt } } }",
  "variables": {
    "input": {
      "pullRequestId": "PR node ID",
      "commitOID": "レビュー対象の head commit OID",
      "event": "APPROVE",
      "threads": [
        {"path": "src/example.ts", "line": 42, "side": "RIGHT", "body": "指摘本文"}
      ]
    }
  }
}
```

レスポンスの `pullRequestReview.state` が `event` に対応し、`submittedAt` があることを確認する。`pullRequestReview.url`、Review種別、投稿済みスレッド数を報告する。`pr-thread-summary` では要約を投稿したことも報告する。

## `pr-thread-summary-after` の要約投稿

1. スレッドの提出時は、mutation の返却項目に `pullRequestReview.id` を加える。Review を提出する場合は、上記の手順で成功を確認してから要約の投稿に進む。スレッドが0件で `--submit` も未指定なら、要約コメントだけを投稿する。
2. スレッドを提出した場合は、取得した ID で今回の Review の `comments` をページングして取得する。コメントの `path`、`originalLine`、`body` で指摘と照合し、対応を確認できたコメントの `url` を要約に添える。URLを取得できない場合や対応を確認できない場合は、指摘を要約に残したうえで、リンクを省略した理由をチャットで報告する。`--blind` でも取得対象は今回提出した Review のスレッドに限る。
3. 要約に含める項目は `pr-thread-summary` と共通とする。投稿直前に PR の head を再照合し、一致していれば `gh pr comment <PR URL> --body-file <本文ファイル>` で通常の PR コメントとして一件投稿する。投稿結果の URL を報告する。

## 失敗時

- mutation 実行前に発見した位置不整合は、該当指摘を投稿対象から外してチャットで報告する。
- mutation が明確な GraphQL エラーを返した場合は、そのエラーを報告し、入力を修正しない限り再試行しない。
- タイムアウト・接続断などで投稿の成否が不明な場合は再試行しない。既に投稿されている可能性があるため、ユーザーに PR で確認を依頼する。
- `pr-thread-summary-after` で Review 提出後に要約を投稿できなかった場合は、提出済みの Review URL と要約の投稿状況を報告する。スレッド付き Review の再提出は行わない。
