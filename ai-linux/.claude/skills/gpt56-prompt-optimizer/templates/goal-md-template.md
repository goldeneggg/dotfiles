# GOAL.md 記述フォーマット設計書：GPT-5.6 Sol /goal 駆動開発向け

GPT-5.6 Solに長時間の自律的な開発（Ralphループ）を行わせる場合、ゴールは抽象的な指示ではなく、**「機械的に検証可能（Testable）な契約」**として記述する必要があります。
そのための仕様書である `GOAL.md` は、受入基準（Acceptance Criteria）の各項目にIDを付与し、完了定義（Definition of Done）と監査エビデンス（Evidence）を強固にマッピングできるフォーマットで記述することが、最も自律ループを安定させるアプローチです。

以下に、実務（Vibe Coding / 自律型CIなど）ですぐに使える `GOAL.md` の具体的な記述フォーマット（テンプレート）と実例を提示します。

---

## `GOAL.md` 設計テンプレート

~~~markdown
# GOAL: [ここにタスクの簡潔なタイトルを記述]

## 1. High-Level Objective (高レベル目標)
> [エージェントが最終的に達成すべきビジネス・機能的なゴールを1〜2文で記述する]

## 2. Scoped Targets (対象範囲の厳格な定義)
*   **Primary Files**:
    *   `[対象ファイルパス1]` (例: `src/auth/login.ts`)
    *   `[対象ファイルパス2]` (例: `src/auth/session.ts`)
*   **Output Directories**:
    *   `[成果物が生成されるディレクトリ]` (例: `dist/`, `goals/wp-login-for-ai/test-artifacts/`)

## 3. Explicit Non-Goals (変更禁止領域・制約条件)
*   [ ] [変更してはならないコードやファイル] (例: `Do not modify src/api/` )
*   [ ] [維持すべき既存の動作/仕様] (例: `Do not change the JavaScript runtime behavior`)
*   [ ] [依存関係やツールの制限] (例: `Do not install new icon packages or dependencies without approval`)

## 4. Acceptance Criteria (受入基準)
[重要] 各項目には必ず `AC-` から始まる一意のIDを付与してください。このIDは後述するDoDや `PROGRESS.md` での進捗監査テーブル（Audit Table）と完全に同期させます。

*   **[AC-001] Functional Contract (機能契約)**
    *   *Requirement*: [期待する振る舞い・インターフェースの契約]
    *   *Verification*: [動作を証明するために実行する具体的なコマンド]
*   **[AC-002] Error Handling & Telemetry (例外処理・ロギング)**
    *   *Requirement*: [エラーハンドリングと、追跡可能性のあるロギング]
    *   *Verification*: [ログの出力確認、または例外発生テスト]
*   **[AC-003] Lint & Quality Checks (静的解析契約)**
    *   *Requirement*: [型チェックやLinterの警告がゼロであること]
    *   *Verification*: `[型チェック/Linterの実行コマンド]` (例: `npm run typecheck` / `composer lint`)

## 5. Definition of Done (DoD / 完了定義)
自律エージェントが「自己監査」を完了したとみなし、`update_goal` ツールを `complete/achieved` に更新するための必須条件を定義します。

1. [ ] すべての変更コードに型エラーがなく、静的解析が警告なしでパスしていること
2. [ ] 新規または修正された単体テスト/結合テストがすべて `PASS` していること
3. [ ] 動作を確認するための検証シナリオを全て実行し、ログや成果物の存在を確認していること
4. [ ] `PROGRESS.md` に自動記録される **「Completion Audit Table (完了監査テーブル)」** に、各 `AC-` IDに対応するエビデンス（検証ファイルパス、Linter結果、テスト出力、またはスクリーンショット）が100%網羅して書き込まれていること
5. [ ] **「不確実なものは未完了として扱う（Treat uncertainty as incomplete）」**: テストが通った、ビルドできたという表層的なシグナル（プロキシシグナル）だけを理由に完了とせず、実際の要件が満たされていることを直接確認すること
~~~

---

## 具体的な作成例（WordPressプラグイン自動ログイン機能の例）

Nathan Onn氏のwp-spec-to-goalスキルが実際に出力する `GOAL.md` をベースにした、実践的な実装例です。

~~~markdown
# GOAL: Auto-login Link Handler for AI Agent

## 1. High-Level Objective
WordPressの開発用Docker環境（wp-env）内において、セキュリティゲート（IP制限、ホスト検証）を通過した上で、特定のユーザー（管理者または編集者）としてログインセッションを確率させる自動ログインURLハンドラーを新規実装する。

## 2. Scoped Targets
*   **Primary Files**:
    *   `src/handlers/class-autologin-handler.php`
    *   `tests/test-autologin-handler.php`
*   **Output Directories**:
    *   `goals/wp-login-for-ai/test-artifacts/` (Playwrightによるブラウザ動作検証のスクリーンショット)

## 3. Explicit Non-Goals
*   [ ] 開発環境（wp-env）以外の本番（production）環境で動作するコードを記述しない（セキュリティ保護のため環境ゲートを設けること）
*   [ ] 既存のWordPressコアの認証ロジックを破壊的に上書き・変更しない
*   [ ] ホストマシンに直接PHP環境を構築・要求しない（すべてのPHPコマンドは Docker 内で実行すること）

## 4. Acceptance Criteria
*   **[AC-001] Environment and Host Gate (環境制限)**
    *   *Requirement*: リクエストが `localhost` または `127.0.0.1` などの開発環境（WP_ENV = 'development'）から送信されている場合のみログインを許可し、それ以外は即座に拒否する。
    *   *Verification*: `npx wp-env run cli phpunit --filter test_environment_gate_blocks_external_request` の実行。
*   **[AC-002] Multi-role Session Instantiation (セッションの確率)**
    *   *Requirement*: 有効なクエリ（例: `?autologwp=admin` や `?autologwp=editor`）を検出した場合、既存のセッションクッキーをクリアした上で、対象ユーザーのログインセッションを確立させ、`wp-admin` へリダイレクトする。
    *   *Verification*: Playwrightを用いたブラウザ検証による `wp-admin` 表示時のスクリーンショット取得（`B-001`〜`B-003`）。
*   **[AC-003] Verification Commands Validation (テストの通過)**
    *   *Requirement*: 記述したすべてのPHPUnitテストが100%通過し、PHP Linter (PHP_CodeSniffer等) で重大な違反が検出されないこと。
    *   *Verification*: `npm run test` および `npm run lint` の実行。

## 5. Definition of Done (DoD)
1. [ ] PHP_CodeSnifferの静的解析警告が0件であること
2. [ ] 新規作成したPHPUnitのテストケースがすべて `PASS` していること
3. [ ] `PROGRESS.md` の「Completion Audit Table」に、`[AC-001]` から `[AC-003]` までのエビデンス（テスト結果のログ、Playwrightが `goals/wp-login-for-ai/test-artifacts/` に出力したブラウザのログイン確認スクリーンショットのパス）が記録されていること
4. [ ] **「Treat uncertainty as incomplete」**: テストの返り値が単に `true` になっているだけで安心せず、データベース内のセッションメタデータおよび実際のブラウザログイン完了を検証すること
~~~

---

## シニア開発者としての推論と実務アドバイス

以上を踏まえると、GPT-5.6 Solで `/goal` コマンドを使用する際、`GOAL.md` の中身をいかに**「エージェントが言い訳（Proxy Signalの悪用）できないレベルまで厳格に書くか」**が成否を分けると考えられます。

特に、テストの成功（Green）だけを信じて自律ループを終わらせてしまうエージェントの「 proxy-signal collapse（代理シグナル崩壊）」を防ぐために 、DoD（完了定義）の中に **「PROGRESS.mdに具体的なエビデンス（実行ログ、成果物ファイル、またはブラウザ自動操作のスクリーンショット等）へのパスを書き出すこと」** を義務付ける記述（上記DoDの4番と5番）を明記することが、/goal を実用レベルで自律動作させるための極めてスマートなハックとなります。
