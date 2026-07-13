## 1. PROGRESS.md テンプレート（初期状態）

自律ループを開始する前に、リポジトリ内の `goals/<タスク名>/PROGRESS.md` に配置しておくべき初期スケルトン（骨組み）です。

~~~markdown
# PROGRESS: [ここにタスクのタイトルを記述]

## 1. Goal Status (現在のゴールステータス)
*   **Active Goal**: [GOAL.md](./GOAL.md)
*   **Current State**: `not_started` (pursuing | paused | achieved | unmet | budget-limited)
*   **Token Budget**: [例: 1,000,000 / 1M]
*   **Tokens Consumed**: 0
*   **Last Updated**: [YYYY-MM-DD HH:MM:SS]

## 2. Completion Audit Table (完了受入条件 監査テーブル)
自律エージェントは、実装および検証コマンドを実行した後、各受入基準（AC-ID）に対する「エビデンス（検証可能な事実）」をこのテーブルに直接記録しなければならない。すべてのセルが埋まるまで完了（achieved）への遷移は認められない。

| Requirement ID | Acceptance Criterion / Description | Status (PASS/FAIL/PENDING) | Evidence (File path, test logs, or screenshot) |
| :--- | :--- | :--- | :--- |
| **AC-001** | [例: 開発環境以外の外部リクエストをブロックする環境ゲート] | PENDING | *Not verified yet. Execute verification scripts.* |
| **AC-002** | [例: ログイン完了後のwp-adminへのリダイレクトとセッション保持] | PENDING | *Not verified yet. Check Playwright artifacts.* |
| **AC-003** | [例: 静的解析（Linter）および型チェックエラー of ゼロ] | PENDING | *Not verified yet. Run verification checks.* |

## 3. Command Execution & Verification Log (検証コマンド実行履歴)
エージェントが [VERIFY.md](./VERIFY.md) に基づいて自律実行した、または自己修復ループ内で実行したすべての検証コマンドと結果のサマリー。

| Timestamp | Executed Command | Exit Code | Result Summary & Artifact Path |
| :--- | :--- | :--- | :--- |
| [YYYY-MM-DD] | `[コマンド]` (例: `npm run typecheck`) | - | [未実行] |

## 4. Blocks & Key Decisions (ブロック要因および重要な意思決定)
*   *If status is 'unmet' or 'paused', record the exact blockers, missing credentials, or API limitations here.*
*   [ ]
~~~

---

## 2. PROGRESS.md の具体的な記録完了例（WordPress自動ログイン機能の場合）

ループ実行中に、GPT-5.6 Solが自律検証を重ね、自己監査を完了した後の `PROGRESS.md` の最終状態（いわゆる領収書/Receiptsの回収完了状態）の具体例です。

~~~markdown
# PROGRESS: Auto-login Link Handler for AI Agent

## 1. Goal Status
*   **Active Goal**: [GOAL.md](./GOAL.md)
*   **Current State**: `achieved`
*   **Token Budget**: 1,500,000
*   **Tokens Consumed**: 428,500 (28 minutes runtime)
*   **Last Updated**: 2026-07-13 07:01:00

## 2. Completion Audit Table
| Requirement ID | Acceptance Criterion / Description | Status | Evidence |
| :--- | :--- | :--- | :--- |
| **AC-001** | Environment gate blocks external requests (WP_ENV check). | **PASS** | Evaluated via `npx wp-env run cli phpunit --filter test_environment_gate`. Output verified in `.logs/phpunit-gate-pass.log`. |
| **AC-002** | Successful redirect to wp-admin & multi-role cookie instantiation. | **PASS** | Verified via Playwright automation. Screenshots saved to: `goals/wp-login-for-ai/test-artifacts/B-001_admin_success.png` and `B-003_editor_success.png`. |
| **AC-003** | Critical lint and quality checks passed (PHP_CodeSniffer, PHPUnit). | **PASS** | Executed `npm run lint` and `npm run test` inside the wp-env environment. 100% tests passed. Zero coding standard violations. |

## 3. Command Execution & Verification Log
| Timestamp | Executed Command | Exit Code | Result Summary & Artifact Path |
| :--- | :--- | :--- | :--- |
| 2026-07-13 06:35:12 | `npx wp-env run cli phpunit --filter test_environment_gate` | 0 | Unit test passed. Verified that mock external IP requests return WP_Error. |
| 2026-07-13 06:42:22 | `npx playwright test` | 0 | Interactive browser test completed. Generated 4 screenshots in `goals/wp-login-for-ai/test-artifacts/`. |
| 2026-07-13 06:55:04 | `npm run lint` | 0 | Checked PHP_CodeSniffer, zero style errors. |

## 4. Blocks & Key Decisions
*   **Resolved [2026-07-13 06:32:00]**: The host machine lacked native PHP 8.2 execution. Under instructions from `AGENTS.md` and `VERIFY.md`, all PHP and Composer invocations were successfully routed through `npx wp-env run cli` container wrapper to ensure deterministic execution .
~~~

---

## シニア開発者としての推論と実務アドバイス

以上を踏まえると、`/goal` コマンドでエージェントを完全に自律（Black Box）で走らせる場合、この `PROGRESS.md` はエージェント自身に「**作業ログの記録と完了のエビデンスを示すことを義務付ける、動的なレポートカード**」として機能させることが極めて効果的と考えられます。

エージェント自身に `PROGRESS.md` のテーブルを更新するよう `GOAL.md` の完了定義（DoD）で指示しておくことで、コンテキストの圧縮（Compaction）が発生した際にも、過去の検証ステップや収集された証拠（Evidence）が失われず、トークン消費のオーバーヘッドを最小限に抑えられます。人間が28分後に席に戻ったとき、このファイルを Git 差分（`git diff`）で確認するだけで、エージェントが一切の手抜き（Proxy-signal collapse）をせずに、本当に完璧な検証を通したかを「 receipts（領収書）」を読むように非同期で監査できるようになります。

---

### 情報源の信頼度: High
*   **根拠**: 本テンプレートおよびプラクティスは、公式の `continuation.md` に組み込まれている自己監査（Audit-first completion）のプロトコル、および WordPress/CLI開発での `/goal` コマンド実証記（Nathan Onn氏 / Ralphable Blog 2026年6月版、Developers Digest 2026年6月版）に完全に準拠しています。

📊 もし、現在構築しようとしている「特定の機能、テスト、あるいはリポジトリの受入要件」を投げていただければ、この PROGRESS テンプレートの「Acceptance Criterion」のテーブル部分を、即座にコピペして `/goal` に渡せる形に私がパーソナライズしてマッピング・ドラフトを作成しますが、いかがでしょうか？
