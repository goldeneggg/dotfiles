---
name: typespec-specialist
description: |
  TypeSpec専門家として、APIスキーマ設計・実装、.tspファイルレビュー・検証、OpenAPI/JSON SchemaからのTypeSpec移行、TypeSpecプロジェクトセットアップを支援するスキル（TypeSpec 1.x 系準拠、最新版に追随）。

  以下の状況で積極的にトリガーすること:
  - 「TypeSpecでAPIを設計して」「.tspを書いて」「APIスキーマを実装して」
  - 「.tspファイルをレビューして」「TypeSpec実装を検証して」
  - 「OpenAPIをTypeSpecに移行して」「JSON Schemaを.tspに変換して」
  - 「TypeSpecプロジェクトをセットアップして」「tspconfig.yamlを整備して」
  - 「/typespec-specialist」の明示実行
  - TypeSpec関連のベストプラクティス・Visibility・Versioningの質問
  - 「@typespec/openapi3」「tsp compile」「@service」「@route」などのキーワード
  - 「スキーマファースト」「型安全なAPIクライアント生成」の文脈

  トリガーしないケース: OpenAPIの直接編集のみ / TypeScript typeやZodなど非TypeSpec型システム / Swagger UIなどドキュメントツール設定のみ
argument-hint: "[.tspファイルパス or OpenAPIファイルパス]"
---

# TypeSpec specialist

TypeSpec を「信頼できる情報源（Single Source of Truth）」として位置付け、堅牢で保守性の高い API スキーマを設計・検証する専門スキル。

## 責務（Scope）

このスキルは以下の 4 つのモードで動作する。冒頭でユーザーの依頼内容からモードを判定し、必要であれば AskUserQuestion で確認する。

**モード判定のヒント**: ユーザー発話に以下のキーワードが含まれていれば対応モードを優先候補とする。複数該当・あいまいな場合のみ AskUserQuestion で確認する。

| キーワード例 | モード |
|---|---|
| 新規 / 設計して / 実装して / ゼロから / 一から | Mode 1: 新規実装 |
| レビュー / 検証 / チェック / 監査 / 改善点 | Mode 2: レビュー・検証 |
| 移行 / 変換 / OpenAPI から / Swagger から / JSON Schema から | Mode 3: 移行 |
| セットアップ / 初期化 / プロジェクト立ち上げ / tspconfig / package.json | Mode 4: セットアップ |

1. **新規実装モード**: 要件から `.tsp` ファイル群を新規設計・実装する
2. **レビュー・検証モード**: 既存 `.tsp` 実装を best-practices に照らして検証し、改善提案をレポートする
3. **移行モード**: OpenAPI / JSON Schema を TypeSpec に変換・移行する
4. **セットアップモード**: TypeSpec プロジェクトの初期構成（`tspconfig.yaml`, `package.json`, ディレクトリ構造等）を整備する

## 必須リファレンス

**作業開始前に必ず `references/best-practices.md` を読み込むこと。** TypeSpec 1.11.0 時点の最新ベストプラクティスが記載されており、本スキルの判断基準はすべてこの文書に準拠する。

参照すべきリファレンス:

| ファイル | 主な用途 |
|---|---|
| `references/best-practices.md` | 全モードで必読の中核ガイド（11 章構成） |
| `references/versioning-guide.md` | バージョニングを扱う際の詳細ガイド |
| `references/migration-openapi.md` | 移行モードで参照する実践ガイド |
| `references/tspconfig-cookbook.md` | セットアップモード・CI 連携で参照するレシピ集 |

best-practices.md の章立て:

| 章 | テーマ |
|----|--------|
| 1 | 名前空間のネスト |
| 2 | 共通パラメータの再利用 |
| 3 | カスタムレスポンス・エラーモデル |
| 4 | Visibility の活用 |
| 5 | ルーティング |
| 6 | バージョニング（詳細は `versioning-guide.md`） |
| 7 | 認証・認可 |
| 8 | 命名規則・ドキュメント |
| 9 | プロジェクト構造 |
| 10 | Linter（詳細は `tspconfig-cookbook.md`） |
| 11 | 下流ツールチェーン統合（移行は `migration-openapi.md`） |

## 共通の作業原則

### バージョン認識

TypeSpec は 2025 年 5 月に 1.0 GA。コア・主要拡張は 1.x 系で安定運用中（執筆時点の最新バージョンは `npm view @typespec/compiler version` 等で確認すること）。以下の点に特に注意:

- **`@service` の構文は object value literal `#{ ... }`** が正規（1.0 以降）。旧来の `({ ... })` は非推奨
- **`@patch` は暗黙的な省略可能化を行わない**（1.0 以降）。部分更新には `@typespec/http` の `MergePatchUpdate<T>` を使う
- **`@withVisibilityFilter` は非推奨**（1.11.0 以降）。`FilterVisibility` テンプレートを使う
- **`@typespec/versioning` / `@typespec/rest` / `@typespec/xml` などはプレビュー**（番号体系は 0.x）。本番採用時は変更リスクを明示する
- **パッケージ番号体系の混在に注意**: コア・`@typespec/http`・`@typespec/openapi(3)`・`@typespec/json-schema` は 1.x stable、`@typespec/rest` および各種プレビュー拡張は 0.x。`package.json` を書く際は `npm view <pkg> version` で実バージョンを確認する

### 出力フォーマット

- `.tsp` コード例は実行可能な完全な形で提示する（必要なインポート文を含む）
- レビュー結果は表形式または箇条書きで構造化する
- ファイル分割を提案する場合はディレクトリツリーを示す

---

## モード別ワークフロー

### Mode 1: 新規実装モード

ユーザーが API 要件から `.tsp` ファイルを新規作成したい場合。

**手順:**

1. **要件ヒアリング**（AskUserQuestion を活用）
   - 対象ドメイン（リソース、操作）
   - 認証方式（Bearer / OAuth2 / なし）
   - バージョニング要否
   - エミッター対象（OpenAPI 3.0 / 3.1 / JSON Schema）
   - クライアント・サーバーコード生成の要否

2. **プロジェクト構造の決定**
   - 規模が小さい場合（< 5 リソース）: `main.tsp` 一枚で開始してよい
   - 規模が大きい場合: best-practices.md「9. プロジェクト構造」のディレクトリ構成を採用
     ```
     main.tsp
     models/
       common.tsp    # エラー型・ページネーション・ResponseWrapper 等
       <resource>.tsp
     routes/
       <resource>.tsp
     ```

3. **モデル設計**
   - 命名規則: モデル/Namespace/Interface = `PascalCase`、操作/プロパティ = `camelCase`
   - 自動採番 ID は `@visibility(Lifecycle.Read)` で読み取り専用に
   - パスワード等の機密入力は `@visibility(Lifecycle.Create)` で書き込み専用に
   - 検索フィルタは `@visibility(Lifecycle.Query)` でクエリ専用に
   - 部分更新が必要な場合は `MergePatchUpdate<T>` を使用（要 `import "@typespec/http"`）
   - すべてのモデル・操作に `/** */` または `@doc` でドキュメントコメントを付与

4. **エラー設計**
   - `@error` デコレータで `ValidationError` / `NotFoundError` / `ConflictError` 等を定義
   - 共通レスポンスラッパーを使う場合はジェネリック `Response<T>` パターンを採用
   - 操作の戻り値は `OkResponse | ValidationError | NotFoundError` のように union で列挙

5. **認証定義**
   - Namespace 全体に `@useAuth(BearerAuth)` 等を適用
   - 認証不要のエンドポイントは個別に `@useAuth(NoAuth)` で上書き

6. **tspconfig.yaml の生成**
   - エミッター指定（`@typespec/openapi3` 等）
   - Linter 設定（新規プロジェクトなら `@typespec/http/all`、既存組み込みなら `recommended`）
   - 出力先パスの明示
   - 詳細は `references/tspconfig-cookbook.md` を参照

7. **完成物の提示**
   - ディレクトリツリー
   - 各ファイルの内容
   - `tsp compile` の想定実行コマンド
   - 期待される OpenAPI 出力の概要

### Mode 2: レビュー・検証モード

既存の `.tsp` ファイル群を best-practices に照らして検証する場合。

**手順:**

1. **対象の特定**
   - レビュー対象ファイルパスを確認（複数の場合は全て）
   - レビューの観点（全章 / 特定章のみ / セキュリティ / パフォーマンス）を確認

2. **構造化チェック**
   各ファイルを読み込み、以下のチェックリストで検証する:

   | カテゴリ | チェック項目 |
   |----------|--------------|
   | 名前空間 | 論理的にネスト化されているか / `operationId` の衝突がないか |
   | 共通化 | リクエスト ID 等がモデル化されスプレッドされているか / ハードコードされていないか |
   | レスポンス | カスタムレスポンス/エラーが定義されているか / 戻り値に union でエラーが含まれているか |
   | Visibility | ID は Read 専用か / `@withVisibilityFilter` を使っていないか（→ `FilterVisibility` へ） |
   | ルーティング | `@route` と `@autoRoute` の使い分けが一貫しているか |
   | Versioning | バージョン管理が必要なら `@versioned` が設定されているか |
   | 認証 | `@useAuth` がすべての保護対象に明示されているか |
   | 命名 | PascalCase / camelCase が遵守されているか |
   | ドキュメント | すべての公開モデル・操作に doc コメントがあるか |
   | プロジェクト構造 | 規模に対して適切に分割されているか |
   | tspconfig | Linter が CI で動くよう設定されているか |
   | バージョン互換性 | `@service` の `#{}` 構文 / `@patch` の `MergePatchUpdate<T>` 使用 |
   | パッケージバージョン | `package.json` のバージョンが実 npm と整合しているか |

3. **レポート出力**

   以下のテンプレートで出力する:

   ```markdown
   # TypeSpec レビューレポート

   ## サマリ
   - 対象ファイル: <ファイル一覧>
   - 検出された問題: <件数>（致命的: N / 警告: M / 提案: L）

   ## 致命的（Critical）
   <コンパイルエラーや誤った API 契約に繋がる問題>

   ## 警告（Warning）
   <best-practices に明確に違反している問題>

   ## 提案（Suggestion）
   <改善余地のある設計>

   ## 良い点
   <既に best-practices に従えている部分>
   ```

   各指摘には以下を含めること:
   - **該当ファイル:行番号**
   - **問題の概要**
   - **best-practices.md の該当章**
   - **修正前 → 修正後のコード例**
   - **修正の根拠（なぜそうすべきか）**

### Mode 3: 移行モード（OpenAPI/JSON Schema → TypeSpec）

既存の OpenAPI 仕様や JSON Schema を TypeSpec に変換する場合。

**この作業は `references/migration-openapi.md` に詳細手順が記載されている。** 必ずこのファイルを参照しながら進める。

要点のみ:

1. 元ファイル形式（OpenAPI 3.0 / 3.1 / Swagger 2.0 / JSON Schema draft）を判定
2. 自動変換ツールの利用可否を検討（規模が大きい場合は叩き台として有効）
3. マッピング表に従って構造を変換
4. 単純変換に留めず、移行を機に共通化・Visibility 導入・エラー統一などの再設計を実施
5. 移行後に `tsp compile` で OpenAPI を再生成し、元仕様との差分を確認

### Mode 4: セットアップモード

新規 TypeSpec プロジェクトを立ち上げる場合。

**手順:**

1. **環境前提の確認**
   - Node.js のバージョン（v20 以上推奨）
   - パッケージマネージャ（npm / pnpm / yarn）

2. **package.json の準備**

   バージョンは `npm view <pkg> version` で実バージョンを確認した上で記述する。番号体系がパッケージごとに異なる点に注意:

   ```json
   {
     "devDependencies": {
       "@typespec/compiler": "^1.12.0",
       "@typespec/http": "^1.12.0",
       "@typespec/openapi": "^1.12.0",
       "@typespec/openapi3": "^1.12.0"
     },
     "scripts": {
       "build": "tsp compile .",
       "watch": "tsp compile . --watch",
       "format": "tsp format \"**/*.tsp\"",
       "format:check": "tsp format --check \"**/*.tsp\""
     }
   }
   ```

   オプション（必要に応じて追加）:
   - `@typespec/json-schema`（^1.x）: JSON Schema 出力
   - `@typespec/versioning`（^0.x、プレビュー）: バージョニング
   - `@typespec/rest`（^0.x、プレビュー扱い、リソース指向ルーティング）

   プレビューパッケージを使う場合は将来の API 変更リスクをユーザーに明示する。

3. **tspconfig.yaml の作成**

   ```yaml
   emit:
     - "@typespec/openapi3"
   options:
     "@typespec/openapi3":
       emitter-output-dir: "{output-dir}/schema"
       openapi-versions:
         - 3.1.0
   linter:
     extends:
       - "@typespec/http/all"
   ```

   既存プロジェクトに後付けする場合は `@typespec/http/recommended` から始めるのが現実的。詳細は `references/tspconfig-cookbook.md` を参照。

4. **ディレクトリ構造の生成**
   規模に応じて `main.tsp` 一枚 or `models/` + `routes/` の分割を選択（best-practices.md 章 9）。

5. **CI 連携の提案**
   - `tsp format --check` をプリコミットフック・CI に追加
   - `tsp compile . --warn-as-error` で Linter 警告も CI 失敗扱いに
   - `tsp compile . --stats` で複雑度監視（1.1.0 以降）
   - 生成された OpenAPI を artifact として保存

6. **VS Code 拡張の案内**
   ユーザーが VS Code を使っているなら「TypeSpec for VS Code」拡張のインストールを推奨。

---

## 実装サンプル（クイックリファレンス）

完全なコード例は `references/best-practices.md` を参照。以下は典型パターンの抜粋。

### サービス定義（@service の正規構文）

```typespec
import "@typespec/http";

using TypeSpec.Http;

@service(#{ title: "My API" })
@server("https://api.example.com", "Production endpoint")
namespace MyApi;
```

### 共通レスポンスラッパー

```typespec
namespace DefaultResponse;

model Response<T> {
  @statusCode statusCode: int32;
  data: T;
  error: ResponseError;
}

model ResponseError {
  message: string;
  code?: string;
}
```

### Visibility を使ったモデル定義

```typespec
model TodoItem {
  @visibility(Lifecycle.Read)
  id: string;

  content: string;

  @visibility(Lifecycle.Create)
  initialTag?: string;

  @visibility(Lifecycle.Read, Lifecycle.Update)
  lastModifiedAt?: utcDateTime;
}

// クエリパラメータ専用
model TodoQueryParams {
  @query
  @visibility(Lifecycle.Query)
  status?: "open" | "done";
}
```

### FilterVisibility（1.11.0 推奨）

```typespec
model CreateAndReadExample is FilterVisibility<
  Example,
  #{ all: #[Lifecycle.Create, Lifecycle.Read] },
  "CreateAndRead{name}"
>;
```

### 部分更新（MergePatchUpdate）

```typespec
import "@typespec/http";

using TypeSpec.Http;

@patch op update(@body pet: MergePatchUpdate<Pet>): void;
```

### 認証付きインターフェース

```typespec
@useAuth(BearerAuth)
interface ProtectedRoutes {
  @get getProfile(): UserProfile;

  @useAuth(NoAuth)
  @get getPublicInfo(): PublicInfo;
}
```

---

## アンチパターン警告

以下を検出したら必ず指摘する:

- `@service({ title: "..." })`（1.0 以降は object value literal `@service(#{ title: "..." })`）
- `@patch op update(@body pet: Pet)`（1.0 以降は `MergePatchUpdate<Pet>` を使用）
- `@withVisibilityFilter`（1.11.0 以降は `FilterVisibility` テンプレート）
- ID プロパティに Visibility 指定なし（`Lifecycle.Read` を推奨）
- 共通パラメータが各操作にハードコード（モデル化＋スプレッド推奨）
- エラーが生のステータスコード返却のみ（`@error` モデル化推奨）
- 名前空間なしのフラット構造（規模に応じてネスト化）
- ドキュメントコメントなしの公開モデル
- Linter 未設定の `tspconfig.yaml`
- `package.json` の TypeSpec パッケージバージョンが実 npm と乖離（特に `@typespec/http` を `^1.x` と書く誤り）
- 各 op に同一 `@tag` を繰り返し付与（interface に 1 回付ければ伝搬する）

---

## 完了時のチェックリスト

作業完了時は以下を必ず報告する:

- [ ] 何を変更/作成したか（ファイル一覧）
- [ ] best-practices.md のどの章に従ったか
- [ ] `tsp compile` が成功する想定か（実環境で検証可能なら実行を促す）
- [ ] プレビュー機能を使った場合の将来リスク
- [ ] 次のステップ（コード生成・CI 連携など）
