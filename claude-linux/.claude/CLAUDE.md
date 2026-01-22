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

## Verification Workflow

実装完了後は以下の手順で検証を実施:

1. **プロジェクトのテスト実行**
   - package.json, Makefile, go.mod等でテストコマンドを確認
   - すべてのテストがPASSすることを確認
   - テストがない場合はユーザーに報告

2. **Linter実行**
   - .eslintrc, .golangci.yml, pyproject.toml等で設定を確認
   - 自動修正可能な問題は修正
   - 残った問題をユーザーに報告

3. **変更差分の確認**
   - `git diff`で意図しない変更がないか確認
   - console.log、debugger、コメントアウトコード、TODOをチェック
   - シークレット情報の混入がないか確認

### テスト成功の判定基準

- 終了コード: 0
- 出力に"FAIL"、"Error"が含まれない（テスト内の期待エラーを除く）
- カバレッジが低下していない（測定されている場合）

## Context Management

効率的な作業のためのコンテキスト管理

### /clear を使うタイミング

- 無関係なタスク間（コミット完了 → 新機能開始時）
- 修正が2回以上失敗した場合（プロンプトを見直して再開）
- プロジェクト/リポジトリを切り替える時

### 委譲の活用

- **調査タスク**: Explore エージェントに委譲してメインコンテキストを保護
- **並行作業**: 無関係な変更は別セッションで実行
- **深い解析**: 専門エージェント（security-expert等）に委譲

### コンテキスト汚染を避ける

- コードベース全体を読み込まない（ターゲットを絞った検索）
- 「念のため」の調査を避ける（具体的な必要性が出てから）
- 上限に近づいたら `/compact` でヒストリーを圧縮

## Personal Tooling

- Editor: Neovim
- Shell: Zsh
- Package Manager: Homebrew (macOS), apt (Linux)
- Version Manager: asdf

## Import Additional Rules

- @~/.claude/rules/preferences.md
- @~/.claude/rules/workflows.md
- @~/.claude/rules/verification.md
