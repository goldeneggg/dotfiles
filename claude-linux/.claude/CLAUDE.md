# User Memory - Personal Preferences

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

## Import Additional Rules

- @~/.claude/rules/preferences.md
- @~/.claude/rules/workflows.md
