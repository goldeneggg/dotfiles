# Personal Instructions for GitHub Copilot CLI

## Language / 言語設定

- **Communication**: 日本語で応答してください
- **Code comments**: English preferred
- **Commit messages**: English

## Code Style Preferences

### General

- シンプルで読みやすいコードを優先
- 過度な抽象化を避ける
- 必要最小限の変更に留める

### Shell Scripts

- POSIX準拠を基本とする（bash拡張が必要な場合は明示）
- ShellCheck準拠
- 変数は `"${var}"` 形式でクォート

### Documentation

- READMEやドキュメントは日本語で記述（ただしOSSの場合は英語）
- コード内コメントは英語

## Workflow Preferences

### Before Implementation

- 不明点は実装前に確認
- 大きな変更は計画を立ててから実行

### After Implementation

- 変更内容を簡潔に報告
- テストが存在する場合は実行確認

## Personal Tooling

- Editor: Neovim
- Shell: Zsh
- Package Manager: Homebrew (macOS), apt (Linux)
- Version Manager: asdf

## Code Quality

### Readability

- 短いコードより読みやすいコードを優先
- マジックナンバーは定数化
- 変数名・関数名は意図が明確なものを使用

### Error Handling

- エラーは早期にチェックして早期リターン
- エラーメッセージは具体的に（何が、なぜ失敗したか）
- 必要に応じてログ出力を追加

### Comments

- 「なぜ」を説明するコメントを重視
- 自明なコードにはコメント不要
- TODOコメントには担当者と期限を記載

## Git Conventions

### Commit Messages

- 英語で記述
- Conventional Commitsの仕様に基づくprefixから始める（fix:, feat: 等）
- 1行目は50文字以内を目安

### Branch Names

- `feat/`, `fix/`, `refactor/` 等のプレフィックス使用
- ケバブケース（例: `feat/add-new-feature`）
