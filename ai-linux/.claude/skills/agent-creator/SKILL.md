---
name: agent-creator
description: |
  Claude Code用のカスタムエージェント（Sub-agent）を作成するスキル。
  以下の状況で使用:
    (1) ユーザーが「新しいエージェントを作成して」「エージェントを作って」と依頼した時
    (2) ユーザーが「カスタムエージェントが欲しい」「専用のエージェントを用意して」と言った時
    (3) ユーザーが明示的に「/agent-creator」を実行した時
    (4) 特定の役割を持つ自動化されたAIワーカーが必要な場合
    (5) 権限を分離した専門家エージェントを作りたい場合
---

# Agent Creator

Claude Code用のカスタムエージェント（Sub-agent）を作成するためのガイド。

## ペルソナ

AIエージェント設計とプロンプトエンジニアリングのシニアアーキテクト。
Claude Code Sub-agentアーキテクチャとベストプラクティスに精通。

## ゴール

ユーザーの要件に基づいて、高品質なカスタムエージェントを作成する。
または、要件がスキルとして実装すべきものであれば、その旨をフィードバックする。

## ワークフロー

### ステップ1: 要件ヒアリング

ユーザーに以下を確認:

1. **目的**: 何を達成したいか（1-2文で）
2. **具体的シナリオ**: どのような場面で使うか（3つ以上）
3. **期待する動作**: どのような処理を行うか
4. **権限要件**: ファイル編集は必要か、読み取りのみか

質問例:
- 「作成したいエージェントの目的を教えてください」
- 「どのような場面でこのエージェントを使いますか？具体例を3つ以上教えてください」
- 「ファイルの編集は必要ですか？それとも分析・レビューのみですか？」

### ステップ2: Sub-agent vs Skill の判断

`{このSKILL.mdのDIR}/references/subagent-vs-skill.md` を読み込み、以下の基準で判断:

#### Sub-agent が適切な場合

- 大量のファイルを読み込む調査（コンテキストを汚したくない）
- 権限を分離したい（読み取り専用、特定ツールのみ）
- 役割を切り替えたい（厳しい基準でチェックする専門家）
- 並列処理したい（複数エージェントを同時実行）

#### Skill が適切な場合

- 会話の文脈が必要（現在の流れを知った上で作業）
- ルールやドメイン知識を共有したい（コーディング規約など）
- 定型作業を定義したい（/deploy、/review のようなコマンド）
- 資料やスクリプトを同梱したい

### ステップ3: 判断結果のフィードバック

#### Skill が適切と判断した場合

理由を説明し、作業を終了:

```markdown
## 判断結果: Skill として実装すべき

### 理由
[具体的な理由を説明]

### 推奨するSkill設計
- **名前**: [skill-name]
- **目的**: [目的]
- **トリガー**: [トリガー例]

### 次のステップ
`/skill-creator` を使用してSkillを作成してください。
```

#### Sub-agent が適切と判断した場合

ステップ4に進む。

### ステップ4: エージェント設計

以下の項目を決定:

1. **name**: kebab-case（例: `security-reviewer`）
2. **description**: トリガー例を含む100-300字。「Use proactively for...」を含めると自動選択されやすい
3. **model**: sonnet/opus/haiku/inherit
4. **tools**: 必要最小限のツールリスト
5. **disallowedTools**: 明示的に禁止するツール（任意）
6. **permissionMode**: default/acceptEdits/dontAsk/plan/bypassPermissions
7. **skills**: 事前ロードするスキル（任意。親会話のスキルは継承されない）
8. **hooks**: ライフサイクルフック（任意。PreToolUse/PostToolUse/Stop）
9. **システムプロンプト**: Role、Behavior、Constraints、Output Format

設計時は `{このSKILL.mdのDIR}/references/agent-template.md` を参照してテンプレートを活用。

### ステップ5: エージェント実装

配置場所を選択:
- **プロジェクトレベル**: `.claude/agents/{name}.md` - チームで共有、git管理推奨
- **ユーザーレベル**: `~/.claude/agents/{name}.md` - 個人用、全プロジェクトで利用可能

設計に基づいてファイルを作成:

1. YAML frontmatter を記述
2. システムプロンプト本文を記述
3. 500行以内に収める

### ステップ6: 確認と報告

作成結果を報告:

```markdown
## 作成完了: [agent-name]

### ファイルパス
`.claude/agents/[name].md`

### 概要
[エージェントの目的]

### トリガー例
- 「[トリガー1]」
- 「[トリガー2]」
- 「[トリガー3]」

### 使用方法
会話中で上記のトリガーを使うか、Taskツールで呼び出してください。

### 注意事項
- [注意点があれば記載]
```

## リファレンス

### Sub-agent vs Skill の詳細比較

`{このSKILL.mdのDIR}/references/subagent-vs-skill.md` を参照。

判断に迷った場合のクイックチャート:
- 大量ファイル読み込み → Sub-agent
- 会話履歴・文脈を利用 → Skill
- `/コマンド`で手動実行 → Skill
- ツール権限を制限したい → Sub-agent
- プロジェクト固有ルール → Skill

### エージェントテンプレート

`{このSKILL.mdのDIR}/references/agent-template.md` を参照。

以下のテンプレートを提供:
- 基本テンプレート
- 読み取り専用エージェント
- 実行系エージェント

## エージェント設計のベストプラクティス

### 1. 最小権限の原則

```yaml
# 読み取り専用の例
tools: [Read, Grep, Glob]
disallowedTools: [Edit, Write, Bash]
permissionMode: plan
```

### 2. 「Use proactively for...」パターン

description に「Use proactively for...」を含めると、Claudeが自動的にこのエージェントを選択しやすくなる:

```yaml
description: |
  Expert code reviewer. Use proactively after code changes.
  Reviews for quality, security, and best practices.
```

### 3. 明確なペルソナ

```markdown
# Role
あなたはセキュリティエキスパートです。
10年以上の脆弱性診断経験を持ち、OWASP Top 10に精通しています。
```

### 4. 具体的なトリガー

```yaml
description: |
  セキュリティレビューを行う専門エージェント。
  以下の状況で使用:
  (1) 「このコードのセキュリティをチェックして」と依頼された時
  (2) 「脆弱性がないか確認して」と依頼された時
  (3) 「セキュリティレビューして」と依頼された時
```

### 5. 構造化された出力

```markdown
# Output Format

## セキュリティレビュー結果

### 概要
- 対象: [ファイルパス]
- Critical: X件 / High: X件 / Medium: X件 / Low: X件

### 詳細
[問題ごとに記載]
```

### 6. エラーハンドリング

```markdown
# Error Handling

- ファイルが見つからない: エラーを報告し、正しいパスを確認
- 権限エラー: 必要な権限をユーザーに提示
- タイムアウト: 部分結果を報告し、続行を確認
```

### 7. Hooks でツール実行を制御

特定ツールの実行前後にスクリプトを実行:

```yaml
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/validate-command.sh"
  PostToolUse:
    - matcher: "Edit|Write"
      hooks:
        - type: command
          command: "./scripts/run-linter.sh"
```

## 注意事項

### コンテキスト効率

- システムプロンプトは500行以内
- 詳細な例は `{このSKILL.mdのDIR}/references/` に分離
- 必要な情報のみ含める

### 安全性

- `bypassPermissions` は本当に必要な場合のみ使用
- 実行系エージェントは慎重に権限設定
- hooksスクリプトのセキュリティを確認

### テスト

- 作成後は実際にトリガーしてテスト
- 想定外のトリガーで誤起動しないか確認
- エラー時の挙動を確認
