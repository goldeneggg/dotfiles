# 検証チェックリスト

skill-creator のベストプラクティスに基づく検証項目一覧。
各項目は Pass / Warn / Fail で判定する。

---

## 1. 構造検証 (Structure)

### 1-01: frontmatter の必須フィールド
- **基準**: `name` と `description` が存在すること
- **Fail**: いずれかが欠落
- **根拠**: name と description はスキルのメタデータ層であり、トリガーの基盤

### 1-02: name の形式
- **基準**: kebab-case であること（例: `my-skill`）
- **Warn**: kebab-case でない（動作はするが慣例から逸脱）
- **根拠**: skill-creator のドキュメントおよび例示で一貫して kebab-case が使用されている（例: `example-skill`, `cloud-deploy`）

### 1-03: SKILL.md の行数
- **基準**: 500行以内が理想
- **Pass**: 500行以内
- **Warn**: 500〜700行（内容密度が高ければ許容）
- **Fail**: 700行超（progressive disclosure の活用を検討すべき）
- **根拠**: skill-creator が推奨する progressive disclosure の3層構造。SKILL.md はトリガー時に全文コンテキストに入るため、長すぎるとトークン効率が悪化する

### 1-04: progressive disclosure の活用
- **基準**: 大量の詳細情報がある場合、references/ に分離されていること
- **Pass**: SKILL.md が簡潔で、詳細は references/ に適切に分離
- **Pass**: SKILL.md 単体で完結する程度のシンプルなスキル
- **Warn**: 長い SKILL.md に全情報が詰め込まれている
- **根拠**: 3層ローディングシステム（metadata → body → bundled resources）

### 1-05: ディレクトリ構成の慣例準拠
- **基準**: bundled resources が適切なサブディレクトリに配置されていること
  - 実行可能コード → `scripts/`
  - ドキュメント → `references/`
  - テンプレート・アセット → `assets/`
  - サブエージェント指示 → `agents/`
  - テストケース → `evals/`
- **Warn**: 役割が曖昧なファイルがルート直下にある
- **根拠**: skill-creator が定義する Anatomy of a Skill

---

## 2. 記述品質 (Writing Quality)

### 2-01: 指示形式
- **基準**: 命令形（imperative form）で書かれていること
- **Warn**: 「〜してください」「〜すると良いでしょう」など曖昧な表現が多い
- **根拠**: skill-creator の Writing Patterns — "Prefer using the imperative form in instructions"

### 2-02: why の説明
- **基準**: 重要な指示にはなぜそうすべきかの理由が添えられていること
- **Warn**: 指示の羅列のみで理由が不明
- **Fail**: ALWAYS/NEVER/MUST が多用され、理由の説明がない
- **根拠**: skill-creator の核心的教え — "explain the **why** behind everything". LLM は理由を理解すると、未知の状況でも適切に判断できる。大文字の強調に頼る指示は、モデルの推論力を活かせていないサイン

### 2-03: 具体例の提供
- **基準**: 出力フォーマットや判断基準に具体例があること
- **Warn**: 抽象的な説明のみで例がない
- **根拠**: skill-creator の Examples pattern。例があることでモデルの解釈ブレが減る

### 2-04: 出力フォーマットの定義
- **基準**: 期待される出力の形式が明確に定義されていること（該当する場合）
- **Warn**: 出力形式の説明が曖昧
- **根拠**: "Defining output formats" パターン。テンプレートを明示すると一貫した出力が得られる

### 2-05: スコープの明示
- **基準**: 何をするか（in-scope）と何をしないか（out-of-scope）が明確であること
- **Warn**: スコープが不明確で境界が曖昧
- **根拠**: スコープが曖昧だとモデルが意図しない方向に拡張してしまうリスクがある

---

## 3. description 品質 (Triggering)

### 3-01: トリガー条件の具体性
- **基準**: description にどんなユーザー発話でトリガーすべきかが具体的に書かれていること
- **Warn**: 機能説明のみでトリガー条件が不明確
- **根拠**: description はトリガーの主要メカニズム。"include both what the skill does AND specific contexts for when to use it"

### 3-02: pushy さの確保
- **基準**: description が積極的にトリガーを促す記述になっていること
- **Warn**: 控えめすぎてトリガーされにくい可能性
- **根拠**: skill-creator が指摘する undertrigger 問題への対策。"please make the skill descriptions a little bit 'pushy'"

### 3-03: キーワード・フレーズの網羅
- **基準**: ユーザーが使いそうな多様な表現が description に含まれていること
- **Warn**: 限定的な表現しかカバーしていない
- **根拠**: ユーザーは同じ意図を異なる言葉で表現する。多様なフレーズをカバーすることでトリガー精度が向上

### 3-04: description の長さ
- **基準**: メタデータ層として約100 words（日本語なら200〜400文字程度）が目安
- **Warn**: 極端に短い（30 words未満）または極端に長い（200 words超）
- **根拠**: description は常にコンテキストに入る。短すぎるとトリガー情報不足、長すぎると他スキルのメタデータを圧迫

---

## 4. リソース整合性 (Resource Integrity)

### 4-01: 参照先ファイルの存在
- **基準**: SKILL.md から参照されているファイルパスが実際に存在すること
- **Fail**: 参照先が存在しない（デッドリンク）
- **根拠**: 実行時にファイルが見つからずエラーになる

### 4-02: 未参照ファイルの検出
- **基準**: ディレクトリ内のファイルが SKILL.md または他のファイルから参照されていること
- **Warn**: どこからも参照されていないファイルがある（孤児ファイル）
- **根拠**: 不要ファイルはメンテナンスコストを増やし、スキルの理解を妨げる

### 4-03: references/ の大規模ファイル
- **基準**: 300行を超える reference ファイルには目次（TOC）があること
- **Warn**: 大規模ファイルに TOC がない
- **根拠**: skill-creator の推奨 — "For large reference files (>300 lines), include a table of contents"

### 4-04: scripts/ の実行可能性
- **基準**: scripts/ 内のファイルに適切な shebang やファイル拡張子があること
- **Warn**: 実行方法が不明確なスクリプトがある
- **根拠**: スクリプトは「ロードせずに実行できる」のが利点。実行方法が不明確だとその利点が失われる

### 4-05: evals/ の存在と品質（該当する場合）
- **基準**: evals/evals.json が存在し、有効な JSON 構造であること
- **Pass**: evals.json が存在し、prompt と expected_output が定義されている
- **Pass**: evals/ がない（必須ではない）
- **Warn**: evals.json が存在するが構造が不完全

---

## 5. 設計妥当性 (Design)

### 5-01: 汎用性と具体性のバランス
- **基準**: スキルが特定例にオーバーフィットせず、かつ十分に具体的であること
- **Warn**: 特定のケースに過度に特化した指示がある
- **Warn**: 抽象的すぎて実用的でない
- **根拠**: skill-creator の改善指針 — "Generalize from the feedback". スキルは多様なプロンプトで使われることを前提に設計すべき

### 5-02: 無駄の排除
- **基準**: スキル内に効果を発揮していない冗長な記述がないこと
- **Warn**: 同じ内容が複数箇所で繰り返されている
- **Warn**: 実質的に何も指示していない空虚な記述がある
- **根拠**: "Keep the prompt lean. Remove things that aren't pulling their weight."

### 5-03: 繰り返しパターンのスクリプト化
- **基準**: 決定論的・反復的な処理が scripts/ に抽出されていること（該当する場合）
- **Warn**: SKILL.md 内に複雑な手順が長々と記述されており、スクリプト化できそう
- **根拠**: "Look for repeated work across test cases" — スクリプト化により毎回の再発明を防ぐ

### 5-04: セキュリティ上の懸念
- **基準**: マルウェア、エクスプロイトコード、ミスリーディングな内容を含まないこと
- **Fail**: セキュリティ上の懸念がある内容を検出
- **根拠**: Principle of Lack of Surprise

### 5-05: ドメイン別整理（該当する場合）
- **基準**: 複数のドメイン/フレームワークをサポートする場合、variant ごとに reference を分離していること
- **Warn**: 複数ドメインの情報が SKILL.md 内に混在
- **根拠**: skill-creator の Domain organization パターン。関連する reference のみを読み込むことでトークン効率が向上
