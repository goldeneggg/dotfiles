# プロジェクト概要

Go製のREST APIバックエンド。[サービスの説明] を [利用者: モバイルアプリ / Webフロントエンド / 他サービス] に提供する。
システム設計・サービス間連携の全体像は `.claude/rules/architecture.md` を参照。

# ディレクトリ構成

```text
.
├── cmd/
│   └── api/          # エントリーポイント（main.go のみ。ビジネスロジックは書かない）
├── internal/
│   ├── domain/       # 純粋なGoの構造体・インターフェース（外部依存なし）
│   ├── handler/      # HTTPレイヤー: リクエスト解析 → service呼び出し → レスポンス返却
│   ├── service/      # ビジネスロジック（domainインターフェースのみに依存）
│   ├── repository/   # DBアクセス（domainインターフェースを実装）
│   ├── middleware/   # 認証・ロギング・レートリミットなど
│   └── platform/     # DB接続・設定読み込み・ロガー初期化
├── pkg/              # 外部importを許可するコード（最小限に保つ）
├── api/              # OpenAPI / Swagger仕様書
├── migrations/       # SQLマイグレーションファイル（連番: 001_*.sql）
└── .claude/
    └── rules/        # AI向けドキュメント（必要時のみ読む。下記テーブル参照）
```

---

# 主要コマンド

```bash
# 起動
go run ./cmd/api

# ビルド
go build -o bin/api ./cmd/api

# テスト（./... は遅いので必ずパッケージ単位で実行する）
go test ./internal/service/...
go test ./internal/handler/...

# Lint（コミット前に必ずパス）
golangci-lint run ./...

# 型チェックのみ
go vet ./...

# DBマイグレーション（migrate CLI使用）
migrate -path ./migrations -database "$DATABASE_URL" up
migrate -path ./migrations -database "$DATABASE_URL" down 1

# モック生成（mockery）
go generate ./...
```

# 作業ルール

- **実装前**: 関連ファイルを読んでから計画を立てる。計画を確認するまでコードを書かない。
- **変更後**: 必ず `go vet ./...` と `golangci-lint run ./...` を実行し、全エラーを修正してから完了とする。
- **テスト**: テーブル駆動テストで書く。モックは `internal/domain` のインターフェース境界で行う。DBを直接モックしない。
- **マイグレーション**: 既存のマイグレーションファイルは絶対に編集しない。必ず新しい連番ファイルを追加する。
- **エラー処理**: `fmt.Errorf("context: %w", err)` でラップする。エラーをサイレントに握り潰さない。
- **コミット**: Conventional Commits形式（`feat:`, `fix:`, `chore:` など）、1コミット1論理変更。

# ハマりやすい注意点

- `DATABASE_URL` にローカル開発時は `?sslmode=disable` が必要。ないと接続が無音でハングする。
- Linterの `wrapcheck` ルールが有効。外部パッケージからのエラーは必ずラップすること。
- インテグレーションテストはDockerが必要（`testcontainers-go` 使用）。Dockerがない場合は `-short` フラグでスキップ。
- `go generate` は mockery v2 が必要。v1 だと互換性のない出力になる。

# Specific Rules（必要なときだけ読む）

| ファイル | 読むタイミング |
|---|---|
| `.claude/rules/architecture.md` | サービス構成・外部依存・認証フローの確認 |
| `.claude/rules/domain-model.md` | エンティティ定義・リレーション・バリデーションルール |
| `.claude/rules/api-conventions.md` | リクエスト/レスポンス形式・エラーフォーマット・ページネーション |
| `.claude/rules/testing-guide.md` | テストの書き方・インテグレーションテストの実行方法 |
| `.claude/rules/deployment.md` | 環境変数・Dockerビルド・CI/CDパイプライン |

非自明なタスクを開始する前に、関連するドキュメントだけを読む。すべてを最初から読まない。

---

# 補足: 上記サンプルの設計意図

全体の行数：約70行。「300行以下・短いほど良い」原則を守り、情報密度を最大化しています。

## 各セクションの判断根拠

- Project Overview（3行）: WHY・WHATを最小限で。プロジェクト固有の情報だけ書き、あとは .claude/rules/architecture.md へのポインターで済ませます。
- Directory Map（ディレクトリ構造）: Goの internal/ 構造はAIの知識にあるようで実際はプロジェクトごとに微妙に違うため、毎回明示する価値があります。コメントで各ディレクトリの責務を1行で示すことで、AIがどこを触るべきかを即座に判断できます。
- Key Commands: go run, go build, go test, go vet, lint, migrate を厳選。重要なのは**「テストは ./... でなく単一パッケージで回せ」という指示**です。これはコードを読んでも推測できないプロジェクト固有の判断であり、省略するとAIは毎回 go test ./... を実行して遅くなります。
- Workflow Rules: 「計画してから実装」「変更後は必ずlint」「モックの境界はdomainインターフェース」など、プロジェクトのGo特有の決め事だけに絞っています。一般的なGoスタイル（gofmt等）は書いていません——linterが機械的に保証するからです。
- Known Gotchas: これがメモリファイルの最も費用対効果が高い記述です。sslmode=disable のような「コードを読んでも絶対わからないが知らないとハマる」罠だけを4つ厳選しています。
- Specific Rules テーブル: Progressive Disclosure の実装です。メモリファイル本体を軽く保ちつつ、深い情報（ドメインモデル、APIの規約、テスト方法）は必要時だけ読むよう誘導します。「全部最初に読め」ではなく「関連するものだけ読め」と明示している点がポイントです。

## あえて書かなかったもの

- コードスタイル（gofmt/golangci-lintに任せる）
- エラーハンドリングの詳細パターン（.claude/rules/api-conventions.md に委譲）
- 依存ライブラリのバージョン（go.mod が正式情報源）
- テストの書き方の詳細（.claude/rules/testing-guide.md に委譲）
