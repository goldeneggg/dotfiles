# Codex設定診断チェックリスト

## プロジェクトとタスク

- 適用される `AGENTS.md` / `CLAUDE.md` と、スキルの役割を混同していないか。
- build、test、lint、format、generate、install、releaseの実コマンドを把握したか。
- ソース以外の書込先として、build成果物、cache、temp、lockfile、DB、socketを把握したか。
- network、Docker、GUI、クラウドCLI、MCP、秘密情報が必要な操作を把握したか。
- 対象外の運用・本番操作を、通常の開発タスクから分離したか。

## 設定レイヤーと実効性

- `CODEX_HOME` を考慮し、ユーザー設定の実パスを確認したか。
- ユーザー設定、選択profile、プロジェクト設定、CLI override、管理者要件の適用順を確認したか。
- プロジェクトのtrust状態により `.codex/` が無効化されていないか。
- プロジェクト設定では有効にならないキーを置いていないか。
- 現行バージョンで未対応・非推奨・名称変更されたキーがないか。
- 設定ファイルの記述値と、実行時に表示されるsandbox、approval、writable rootsが一致するか。

## Filesystemとsandbox

- 通常の開発に必要な読取ルートと書込ルートが揃っているか。
- workspace外のcache、temp、toolchain、module cacheへの書込要否を確認したか。
- symlink先やworktreeが意図せず権限外になっていないか。
- secrets、SSH鍵、credential store、他プロジェクトへの読取・書込を必要以上に許可していないか。
- full accessを、より狭いsandboxや追加rootで置き換えられないか。
- read-onlyタスクに書込権限を付け過ぎていないか。

## Networkと外部機能

- 依存取得、API検証、Git hosting、package registryに必要な通信を把握したか。
- network許可が広過ぎず、対象や目的を限定できるか。
- localhost、Unix socket、Docker socketを通常の外部通信と区別したか。
- MCPや外部CLIのwrite・destructive操作に適切な承認境界があるか。
- 秘密値を設定ファイルや診断レポートへ直接露出していないか。

## Approvalとrules

- 対象ルールが実際のargv prefixに一致するか。
- shell wrapperや複合コマンドがルール評価へ与える影響を確認したか。
- 頻出する安全なread-only操作で、承認が不必要に反復しないか。
- write、destructive、外部状態変更を広いprefixで自動許可していないか。
- 競合ルールのうち最も制限的な決定が適用される前提で評価したか。
- ruleの検証コマンドまたは同等機能で代表例と反例を確認したか。

## 判定カテゴリ

- **適切**: 必要能力を最小権限で満たし、通常タスクを妨げない。
- **過剰**: タスクに不要な権限や許可範囲を含む。
- **不足**: 必須操作が失敗する、または合理性のない承認を反復する。
- **無効**: 設定レイヤー、trust、構文、version差により意図が反映されない。
- **不明**: 証拠不足のため断定できない。必要な確認方法を示す。

## 優先度

- **High**: 開発タスクを完遂できない、重要な保護を迂回する、秘密・本番・広範囲な破壊操作に現実的なリスクがある。
- **Medium**: 頻出タスクで失敗や承認が反復する、設定が部分的に無効、権限範囲が必要以上に広い。
- **Low**: 現時点で実害は小さいが、保守性、説明、テスト例、将来互換性を改善できる。

## 公式仕様の確認先

仕様が更新され得るため、まずインストール済みCodexのhelp、schema、config診断を確認し、不明点だけOpenAI公式ドキュメントで確認する。

- Configuration Reference: <https://learn.chatgpt.com/docs/config-file/config-reference>
- Rules: <https://learn.chatgpt.com/docs/agent-configuration/rules>
- Sandbox and approvals: <https://learn.chatgpt.com/docs/agent-approvals-security>

公式仕様と現在の実行環境が異なる場合は差異を明示し、その環境で検証できた挙動を診断の根拠にする。
