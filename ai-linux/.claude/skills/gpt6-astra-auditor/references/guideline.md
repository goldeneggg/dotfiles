## GPT-6 Astra 適合性監査ガイドライン

このドキュメントは、AGENTS.md・CLAUDE.md と Agent Skill を、GPT-6 Astra / 現行の高性能 coding agent に適した状態になっているかを監査する際に使用する想定のガイドラインです。

目的は、単純に指示を短くすることではありません。
古いモデルの能力不足を補うために追加された scaffolding や handholding を減らしつつ、プロジェクト固有の制約、安全要件、品質基準、業務ルール、非自明なワークフローは維持してください。

以下の観点で監査してください。

1. 古いモデル向けの過剰な handholding
    - 毎回読む必要のないファイルやドキュメントを強制していないか
    - grep、ファイル閲覧、編集、テストなどの実行手順を不必要に固定していないか
    - モデル自身が判断できることを逐一指示していないか
    - 「必ず〜する」「常に〜する」など、単純な変更にも適用される過剰な一般ルールがないか
2. decision boundary
    - 過去のモデルが勝手に進みすぎることを防ぐ目的で、現在は厳しすぎる approval / stop / ask-first ルールが残っていないか
    - 本当に人間の承認が必要な操作と、agent が安全に自律実行できる操作が区別されているか
    - 安全なローカル操作について、不必要に確認を要求していないか
3. completion / persistence
    - 「どこまで進めば完了か」が明確か
    - 実装だけで止まらず、必要に応じて実行、検証、関連テスト、失敗修正まで進めることが分かるか
    - 逆に、不要な全件テストや過剰な検証を常に要求していないか
4. Skills の routing
    - 各 Skill の name / description が短く、発火条件が明確か
    - description が広すぎて、関係の薄いタスクでも Skill を選ばせる内容になっていないか
    - 複数 Skill の description が競合・重複していないか
    - 「この Skill を使え」という pick-me 的な記述がないか
    - 常時必要なルールを Skill に入れていないか
5. progressive disclosure
    - Skill の root SKILL.md が巨大な手順書になっていないか
    - 複数の workflow がある場合、root を minimal router にして必要な supporting docs / scripts のみ読む構成にできないか
    - タスクに無関係な情報まで毎回 context に入る構造になっていないか
6. モデル非依存性
    - 特定モデルの弱点や癖への workaround が、他の coding agent まで不必要に制約していないか
    - プロジェクト固有の事実・制約と、特定モデル向けの prompting hack が混在していないか

重要な制約:

- 「短いほど良い」という前提で削除しないでください。
- セキュリティ、データ保護、production 操作、破壊的変更、migration、リリース、外部 API、課金を伴う操作などの境界は、モデルが賢くなったという理由だけで削除しないでください。
- プロジェクト固有の convention や、コードから容易には推測できないルールは維持してください。
- 不明な指示については勝手に削除せず、「要確認」としてください。
- 現在のルールが何を防ぐために存在するか推測できる場合は、その意図と現在の必要性を分けて評価してください。

各 AGENTS.md と Agent Skill について、以下の形式で結果を出してください。

### 1. Executive summary

- 現状の主な問題
- Astra に特に不向きなパターン
- 維持すべき重要なルール
- 最も効果が大きい改善 5 件

### 2. Rule-by-rule audit

各指示について次のいずれかに分類してください。

- KEEP: 現状維持
- REWRITE: 意図は正しいが表現・強度・適用範囲を変更
- REMOVE: 古いモデル向け scaffolding で、現在は害が大きい
- MOVE_TO_SKILL: 常時適用ではなく特定 workflow のときだけ必要
- MOVE_TO_AGENTS: Skill ではなく repository-wide rule として常時必要
- SPLIT: 複数の目的が混在しているので分割
- NEEDS_HUMAN_DECISION: プロジェクト固有の判断が必要

各項目について、

- 現在の記述
- 分類
- 問題点
- なぜ Astra / 現行 coding agent で問題になり得るか
- 変更案

を示してください。

### 3. Skills audit

各 Skill について、

- 本当に Skill として存在すべきか
- trigger / description の適切さ
- 他 Skill との重複
- progressive disclosure の状態
- root document に残すべき内容
- supporting docs / scripts に移すべき内容

を評価してください。

### 4. Proposed rewrite

監査結果を反映した、

- AGENTS.md の完全な改訂案
- 各 Skill の SKILL.md の改訂案

を提示してください。

ただし、安全性やプロジェクト固有要件に関して判断材料が不足している箇所は、勝手に変更せず TODO または要確認コメントとして残してください。

### 5. Diff rationale

最後に、変更案について

- context 消費を減らす変更
- autonomy を高める変更
- premature stopping を防ぐ変更
- Skill routing を改善する変更
- safety / project invariants を維持する変更

に分けて要約してください。
