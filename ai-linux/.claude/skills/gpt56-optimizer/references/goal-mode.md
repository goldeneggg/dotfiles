# Codex `/goal` 最適化ガイド

## 公式に確認できる動作

- ChatGPTデスクトップアプリ、Codex CLI、IDE拡張で `/goal` を開始できる。
- 目標文は最初のプロンプトであると同時に完了条件になる。
- 目標が曖昧なら、先に `/plan` で制約と測定可能な成功条件を明確にする。
- 目標にはOutcome、Constraints、Verificationを必要に応じて含める。
- CLIでは `/goal edit`、`/goal pause`、`/goal resume`、`/goal clear` を使用できる。
- 目標は空でなく4,000文字以内にする。長い詳細はファイルに置き、目標文から参照する。
- `/goal` はサンドボックスや承認境界を拡張しない。必要な判断では停止する。

## 2雛形を使う条件

`GOAL.md` と `PROGRESS.md` はこのスキルの長時間作業パターンであり、Codexの必須ファイルではない。

次のいずれかに当てはまる場合、2つを対で使用する。

- 目標の詳細が4,000文字に収まらない。
- 複数の受入基準やマイルストーンがある。
- コンテキスト圧縮後も決定、進捗、検証証拠を残す必要がある。
- 非同期で成果を監査する必要がある。

短く明確で、単一の検証だけで完了を判断できる作業には、インラインの `/goal <objective>` を使う。

## 雛形の適用手順

1. ユーザー指定またはリポジトリ既存のgoal文書管理ディレクトリを使う。規約がなく、配置が成果に影響する場合は候補を示して確認する。
2. `templates/goal-md-template-for-sol.md` を `GOAL.md` として具体化する。Outcome、Scope、Constraints、Acceptance Criteria、Verificationを実在する要件だけで埋める。
3. `templates/progress-md-template.md` を `PROGRESS.md` として具体化する。`GOAL.md` のAC-IDと監査表の行を一致させる。
4. `GOAL.md` に、主要マイルストーンと完了前に `PROGRESS.md` を更新する要件を含める。Codexが自動更新すると仮定しない。
5. プレースホルダー、架空のコマンド、存在しないファイル、ユーザー未指定のトークン予算を残さない。
6. 4,000文字以内の目標文から両ファイルを参照する。

例:

```text
/goal <path>/GOAL.md の目標を達成する。主要マイルストーンと完了前に
<path>/PROGRESS.md を更新し、各受入基準を検証証拠に結び付ける。
```

## 実行中の扱い

- 制約や成果が変わる場合は目標を編集する。説明や状況確認だけならサイド会話を使い、主作業を不要に中断しない。
- 接続を失う見込みがある場合はpauseし、再開可能になってからresumeする。
- 並行するgoalに同じファイルを編集させない。コーディング作業は別worktreeを使う。
- 根拠が不足している項目を完了扱いしない。ブロッカーと次に必要な入力を `PROGRESS.md` に残す。

## 公式資料

- [Long-running work](https://learn.chatgpt.com/docs/long-running-work.md)
- [Slash commands in Codex CLI](https://developers.openai.com/codex/cli/slash-commands.md)
