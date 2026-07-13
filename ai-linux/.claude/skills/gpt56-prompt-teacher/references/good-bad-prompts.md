# GPT-5.6プロンプト最適化ガイド：シニア・デベロッパー向け比較分析

GPT-5.6（特にフラグシップモデルのSol）は、以前のモデル（GPT-5.5や5.4など）と比較して、コンテキストやユーザーの潜在的な「意図（Intent）」をより深く推論・理解する能力が向上しています。そのため、プロンプトに細かな手順（ステップ）を過剰に書き連ねるよりも、**「期待する最終結果（Outcome）」と「厳格な制約条件（Constraints）」を明確に定義し、エージェント自身に最適な実行経路を選択させる**アプローチが最も効果を発揮します。

また、不要なプロンプトの記述や冗長な例示、無関係なツール定義を削減して「プロンプトのスリム化（Simplify prompts first）」を行うことで、タスクの実行成功率（評価スコア）が約10〜15%向上し、消費トークン数を41〜66%、コストを33〜67%削減できることが評価から実証されています。

以下に、実務で頻出する開発・自動化ワークフローを対象として、GPT-5.6の特性を最大限に活かす「良いプロンプト（Prefer）」と、非効率な「良くないプロンプト（Avoid）」の対比をカテゴリ別に紹介します。

---

## 1. タスクの方向性と自律性（アウトカムファースト）

GPT-5.6は自律的に効率的な検索やツール実行のパスを判断できます。マイクロマネジメントのような手順の指示はトークンを無駄にし、エージェントの柔軟性を奪います。

### 良くないプロンプト（Avoid）
~~~
Step 1: Open research.md.
Step 2: Extract key claims.
Step 3: Run search on custom database.
Step 4: Write draft based on the template.
~~~

### 良いプロンプト（Prefer）
~~~
Write a launch brief from the attached research, using the standard template in this repo. Verify every product claim against our source docs and flag missing information.
~~~

* **解説**: 目的地（ローンチブリーフの作成、リポジトリ内の標準テンプレート使用）と検証基準（ソース文書との整合性検証、欠落情報のフラグ立て）のみを指定し、途中の自律的な調査や抽出プロセスの組み立てはモデルの推論に委ねています。

---

## 2. 成果物の長さ、詳細度、スタイルの制御

GPT-5.6はGPT-5.5よりもデフォルトで簡潔な回答を出力する傾向があります。そのため、単に「簡潔に」「短く」と指示すると、必要な情報まで削ぎ落とされてしまうリスクがあります。詳細度の制御には、APIレベルの設定（`text.verbosity`など）を組み合わせつつ、プロンプトで「何を優先して残し、何を削ってよいか」の優先順位（Priority order）を指示することが重要です 。

### 良くないプロンプト（Avoid）
~~~
Rewrite the draft. Make it professional and concise.
~~~

### 良いプロンプト（Prefer）
~~~
Rewrite the draft for [audience]. Preserve the three main themes from the source text, but simplify the terminology and keep the length within 400 words.
~~~

* **解説**: どのような優先順位で情報を整理すべきか（主要な3つのテーマは維持し、用語を簡略化して400語以内に収める）が具体的に定義されているため、コンテキスト崩壊を起こさずに洗練された要約・編集が行われます。

---

## 3. 自律実行と承認（アクション・セキュリティ）の境界定義

GPT-5.6は非常に能動的に複数のツールをループ実行できます。不要な確認プロンプトによる中断（承認疲れ）を防ぎつつ、破壊的なアクションを確実に防止するために、ローカルの安全なアクションと、人間の事前承認が必須となるアクションの境界線を1箇所にまとめて提示する必要があります。

### 良くないプロンプト（Avoid）
~~~
Identify the slow query and fix it. Ask before you do anything.
~~~
*(または「Always ask before running commands.」のような過剰に絶対的な禁止命令)*

### 良いプロンプト（Prefer）
~~~
Identify the slow query, fix the cause, and rerun the benchmark. You may read the database logs and run select queries. Ask for approval before you perform any inserts, updates, or configuration changes.
~~~

* **解説**: 読み取りやベンチマーク実行などの安全なローカルアクションは自律実行を許可し、データの挿入・更新・設定変更などの破壊的な変更が加わる境界線でのみ明示的な承認（Ask for approval）を求めています。これによって、開発プロセスを阻害せずにセキュリティ境界を守ることができます。

---

## 4. 終了前の検証（Definition of Done / DoD）

「正常に動くはず」という憶測でタスクを完了させず、エージェント自身にテストスイートや検証コマンド、コードの静的解析を実行させ、確実なエビデンス（証拠）に基づいて自己監査を行わせる終了条件（DoD）を指定します。

### 良くないプロンプト（Avoid）
~~~
Implement the payment handler. Make sure it works.
~~~

### 良いプロンプト（Prefer）
~~~
Implement the payment handler, run the unit tests, and fix any failures. Before you report completion, verify that the handler catches checkout errors and logs them with traceId.
~~~

* **解説**: 単に「機能の実装」を求めるのではなく、ユニットテストの実行とエラー修正、そして完了報告の前に「エラーキャッチとtraceIdのログ出力」という具体的な検証パスまでをプロンプト内で要求しています。これによって、モデルが表面的なシグナル（「ファイルを書き換えた」など）だけで勝手に完了を宣言するのを防ぎます。

---

## 5. 自動的な反復修復・目標追跡（`/goal` コマンド用プロンプト）

Codex CLI 0.128.0以降に実装された `/goal` コマンドは、あらかじめ設定されたトークン予算（Token budget）の範囲内で、テストやコンパイルが通過するまで自律的に「コード修正 → テスト実行 → 修正」をループさせる機能です。`/goal` で指定する「目標オブジェクト」は、具体的な契約（Behavior contract）のように記述する必要があります。

### 良くないプロンプト（Avoid）
~~~
Refactor the auth code
~~~

### 良いプロンプト（Prefer）
~~~
Refactor src/auth/login.ts and src/auth/session.ts to async/await. Do not change the JavaScript runtime behavior, do not modify src/api/. Done means: npm run typecheck passes with zero errors, npm run test passes the new tests in src/utils/tests/
~~~

* **解説**: 良くないプロンプトではリファクタリングの範囲が曖昧なため、エージェントが自己監査（Audit-first completion）を行う際に何を基準に完了（achieved）と判断してよいか分からず、ループが無限に回るか、不完全な状態で勝手に終了します。良いプロンプトでは、変更対象の限定、非目標（変更してはならない範囲）、そして成功を定義するための具体的な検証コマンド（`npm run typecheck` などのパス）が契約書のように網羅されています。

---

## 6. ドキュメントやスライド、成果物生成タスク（Workモード用）

ChatGPT WorkモードやCodexでスライドデッキやスプレッドシート、決定メモなどのファイル生成（Artifacts）を行う場合、ソースデータを指定するだけでなく、全体の枚数制限や成果物の構成要件を明示します。

### 良くないプロンプト（Avoid）
~~~
Make me a presentation about our customer research.
~~~

### 良いプロンプト（Prefer）
~~~
Review the attached interview notes and survey results. Create an eight-slide presentation for the product leadership meeting. Focus on the three most common customer problems, include supporting evidence, separate findings from recommendations, and flag any claims that are not well supported. Use @Google Drive for the source docs. Return a draft for my review before treating it as final.
~~~

* **解説**: 生成するスライドの枚数（8枚）、ターゲット層（製品リーダーシップ会議）、核となるテーマ（最も多い3つの課題）、ソースの指定、そして「最終決定の前にドラフトを人間に提出する」というレビュー境界が精緻に指定されているため、実用に耐えうる精度の成果物が1発で生成されます。

---

## プロンプト設計におけるシニア開発者としての推論

以上を踏まえると、GPT-5.6 Solおよびそのファミリーをデプロイする際、従来のLLMで必要だった「思考のステップを1から10まで細かく制御するプロンプトエンジニアリング（過剰なチェーン・オブ・ソートの強制）」をそのまま移植するのは、かえってトークンの競合や推論効率の低下を招くため推奨されません。

GPT-5.6を自律エージェントや開発のループ（特に `/goal` などのコンティニュエーション）に組み込む場合、開発者はプロンプトを「**成果物の検証可能な仕様書（DoD）**」および「**実行のセーフティ境界（制約条件）**」として再設計することにリソースを集中させ、実装経路そのものは Sol 本体の高い推論力と自律ツール呼び出し能力に委ねることが、最もコスト対効果（ROI）を高める最適解であると考えられます。

---

### 情報源の信頼度
* **High（高）**: 提示した「良いプロンプト vs 良くないプロンプト」の対比、およびGPT-5.6 Solの特性やトークン/コスト効率データは、すべてOpenAI APIの公式移行・プロンプトガイド（Prompting guidance for GPT-5.6 Sol / Model guidance）、および公式ドキュメント（Codex 2026/06/11更新時点）の記述に基づいています。
