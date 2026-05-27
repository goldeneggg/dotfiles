# TypeSpec による API スキーマ設計のベストプラクティス

> **バージョン情報（執筆時点）**
>
> TypeSpec は 2025-05-06 に 1.0 GA。コアおよび主要拡張は 1.x 系で進化中で、プロダクション利用が公式にサポートされている。具体的な最新版は `npm view @typespec/<pkg> version` で確認すること。
>
> **パッケージ番号体系の注意**: TypeSpec は「コア / 安定拡張」と「プレビュー拡張」で番号体系が分かれている。`package.json` を書く際はこの違いを意識する。
>
> | カテゴリ | パッケージ | 番号体系 | ステータス |
> |---|---|---|---|
> | コア | `@typespec/compiler` | 1.x | 安定（Stable） |
> | 安定拡張 | `@typespec/openapi`, `@typespec/openapi3`, `@typespec/json-schema` | 1.x | 安定（Stable） |
> | HTTP プロトコル | `@typespec/http` | 1.x | 安定（1.0 はコア 1.0 GA と同時に到達） |
> | プレビュー拡張 | `@typespec/versioning`, `@typespec/rest`, `@typespec/xml`, `@typespec/streams`, `@typespec/sse`, `@typespec/protobuf` | 0.x | プレビュー（API 変更の可能性あり） |
> | コード生成 | `@typespec/http-client-*`, `@typespec/http-server-*`（.NET / JS / Java / Python） | 0.x | プレビュー |
>
> 各パッケージの最新バージョンは `npm view <pkg> version` で確認すること。プレビュー拡張は独自の 0.x サイクルでリリースされるため、`package.json` に書く際は実バージョンを必ず確認する。

TypeSpec を利用して API スキーマを実装する際は、単一のコードベースを「信頼できる情報源（Single Source of Truth）」とし、一貫性のある API 定義・クライアントコード・ドキュメントを生成できるように設計する。

---

## 1. 名前空間（Namespace）のネストによる論理的な構造化

API のモデルや操作（Operation）は、名前空間を使用して論理的にグループ化する。特にネストされた名前空間を活用することで、以下の利点が得られる。

- **整理と管理の向上**: 関連する操作（例: CRUD 操作など）をまとめることで、API の全体構造が把握しやすくなる
- **Operation ID の明確化**: OpenAPI などの仕様を出力する際、TypeSpec は名前空間をプレフィックスとして `operationId` に自動付与する（例: `Pets_listPets`）。どのリソースに対する操作であるかが明確になる
- **名前の衝突回避**: 異なるリソース間で同名の操作やモデルが存在した場合の衝突を防ぐ

### `@tag` デコレータによる操作グルーピング

名前空間による構造化に加え、`@tag` デコレータで OpenAPI ドキュメント上の操作グループをさらに細かく制御できる。名前空間とタグは別軸の整理方法であり、組み合わせるとより読みやすい API ドキュメントが生成される。

`@tag` は **interface 全体に 1 回付ければ配下の全操作に伝搬する**。各 op に同じタグを繰り返し付けるのは冗長であり、メンテナンスの負担も増えるため避ける。

```typespec
@tag("Search")
@route("/search")
interface SearchRoutes {
  @get list(): SearchModel.Search[];

  @get
  @route("/byName/{name}")
  byName(@path name: string): SearchModel.Search;
}
```

特定の op のみ別タグを当てたい場合は op 単位で `@tag` を併記すれば上書きできる。

---

## 2. 共通パラメータとモデルの再利用

複数の API 操作で共通して使用されるパラメータ（例: リクエスト ID、ロケール情報、クライアントバージョンなど）は、個別の操作にハードコードしない。

代わりに、共通パラメータを一つのモデルとして定義し、**スプレッド演算子（`...`）** で各操作の引数に展開する。これにより、API 全体でパラメータの適用が一貫し、冗長性とエラーの発生を減らせる。

```typespec
model CommonHeaders {
  @header("X-Request-ID") requestId?: string;
  @header("Accept-Language") locale?: string;
}

op listUsers(...CommonHeaders): User[];
op getUser(...CommonHeaders, @path id: string): User;
```

---

## 3. カスタムレスポンスと構造化されたエラーモデルの定義

- **カスタムレスポンスモデル**: TypeSpec の HTTP ライブラリに組み込まれた標準レスポンス（`OkResponse (200)` や `CreatedResponse (201)` など）を `extends` で拡張し、ドメインに特化した名前付きレスポンスモデルを定義する。これにより API の意図が明確になり、コードの重複を防げる。
- **エラーモデルの共通化**: 生のステータスコードをそのまま返すのではなく、`@error` デコレータで `ValidationError` や `NotFoundError` といった構造化されたエラーモデルを定義する。各操作の戻り値には `|` 演算子で正常系とエラー系のモデルを併記し、クライアント側でのエラーハンドリングが予測しやすいようにする。

### ジェネリックなレスポンスラッパーパターン

ジェネリック型を活用した共通レスポンスラッパーを定義することで、成功・エラーの構造を API 全体で統一できる。

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

各エンドポイントではこのラッパーを使い回す。

```typespec
op getSearch(): DefaultResponse.Response<SearchModel.Search[]>;
op getUser(@path id: string): DefaultResponse.Response<User>;
```

### PATCH 操作と部分更新（1.0 以降の変更点）

TypeSpec 1.0 以降、`@patch` はデフォルトで「implicit optionality」（暗黙的な省略可能化）変換を適用しなくなった。部分更新（JSON Merge-Patch）を実装するには、**`@typespec/http` が提供する `MergePatchUpdate<T>` テンプレート** を明示的に使用する。

```typespec
import "@typespec/http";

using TypeSpec.Http;

// 推奨: JSON Merge-Patch による部分更新
@patch op update(@body pet: MergePatchUpdate<Pet>): void;

// 旧来の挙動を維持したい場合（非推奨・段階的移行用）
@patch(#{ implicitOptionality: true }) op updateLegacy(@body pet: Pet): void;
```

`MergePatchUpdate<T>` は `T` のすべてのプロパティを optional にしつつ、merge-patch のセマンティクス（明示的 `null` で削除、未指定で据え置き）を型レベルで表現する。`import "@typespec/http"` と `using TypeSpec.Http` の宣言が必要なことに注意。

---

## 4. ライフサイクル・ビジビリティ（Visibility）の活用

TypeSpec の強力な機能である「Visibility（可視性）」を利用すると、リクエスト時とレスポンス時などの「文脈」に応じてモデルの構造（ビュー）を動的に変化させられる。

組み込みのライフサイクル修飾子をプロパティに適用することで、以下の制御が可能。

| 修飾子 | 適用文脈 | 典型的用途 |
|---|---|---|
| `Lifecycle.Read` | GET レスポンス | 自動採番 ID、サーバー算出フィールド |
| `Lifecycle.Create` | POST リクエスト | パスワード等の作成時のみ受け取る入力 |
| `Lifecycle.Update` | PUT/PATCH リクエスト | 更新可能だが作成時は不要なフィールド |
| `Lifecycle.Delete` | DELETE リクエスト | 削除時の追加パラメータ |
| `Lifecycle.Query` | GET クエリパラメータ | 検索フィルタ・ソート条件 |

```typespec
model TodoItem {
  @visibility(Lifecycle.Read)
  id: string;          // レスポンスのみに含まれる

  content: string;
  dueDate: utcDateTime;

  @visibility(Lifecycle.Create)
  initialTag?: string; // 作成時のみ指定可能

  @visibility(Lifecycle.Read, Lifecycle.Update)
  lastModifiedAt?: utcDateTime; // 読み取りと更新で見える
}

// クエリパラメータ専用 Visibility の例
model TodoQueryParams {
  @query
  @visibility(Lifecycle.Query)
  status?: "open" | "done";

  @query
  @visibility(Lifecycle.Query)
  dueBefore?: utcDateTime;
}
```

これにより POST 用・GET 用といった似たようなモデルを複数作成する（型の増殖）必要がなくなり、単一の論理モデルを維持したままシンプルに管理できる。

### `FilterVisibility` の活用（1.11.0 以降推奨）

TypeSpec 1.11.0 から、`@withVisibilityFilter` デコレータは **非推奨** となった。代わりに `FilterVisibility` テンプレートを使用する。`FilterVisibility` はデコレータメタデータの保持に関するバグが修正されており、より正確なビジビリティ変換を提供する。

```typespec
// 推奨（1.11.0 以降）
model CreateAndReadExample is FilterVisibility<
  Example,
  #{ all: #[Lifecycle.Create, Lifecycle.Read] },
  "CreateAndRead{name}"
>;

// 非推奨: @withVisibilityFilter
// @withVisibilityFilter(#{ all: #[Lifecycle.Create] })
// model CreateExample is Example {}
```

第 1 引数は対象モデル、第 2 引数はフィルタ条件（`all` で全マッチ、`any` でいずれかマッチ）、第 3 引数は派生モデルの命名テンプレート。

---

## 5. 堅牢なルーティング定義

エンドポイントのパス定義には、`@route` デコレータで明示的に記述する方法と、`@autoRoute` と `@segment` を組み合わせる方法がある。

リソース指向の設計では、モデル側に `@segment` でパスのセグメント（例: `pets`）を定義し、インターフェースや操作に `@autoRoute` を適用することで、パラメータから URL ルートを自動かつ一貫して生成できる。

選択指針:
- **小〜中規模・直感的なパス重視** → `@route` で明示
- **CRUD が定型化された大規模リソース** → `@autoRoute` + `@segment`

混在は避け、プロジェクト内で一貫させる。

---

## 6. API のバージョン管理（Versioning）の統合

`@typespec/versioning` ライブラリを使うと、API の変更を既存クライアントに影響を与えずに進化させられる。

詳細は **[`versioning-guide.md`](./versioning-guide.md)** を参照。要点のみ:

- ライブラリは現在 **プレビュー**。番号体系は 0.x（コアの 1.x とは独立）
- `@versioned` を namespace に付け、`enum Versions` でバージョンを列挙
- 進化系デコレータ: `@added` / `@removed` / `@renamedFrom` / `@madeOptional` / `@madeRequired` / `@typeChangedFrom`
- 採用判断は「公開 API か」「互換性が重要か」で決める。プレビュー API の変更追従コストはバージョニング欠如による破壊的変更コストより通常小さい

---

## 7. 認証・認可ポリシーの明示

API のセキュリティ要件は `@useAuth` で明示的に定義する。`BearerAuth`、`BasicAuth`、`OAuth2Auth` などの標準認証方式を、Namespace 全体・Interface・個別 Operation のレベルで適用する。

これにより、生成される OpenAPI 上で「どのエンドポイントがどのような認証を要求するか」がセキュリティ定義として正確に出力される。

```typespec
@useAuth(BearerAuth)
interface ProtectedRoutes {
  @get getProfile(): UserProfile;

  // 一部のエンドポイントは認証不要
  @useAuth(NoAuth)
  @get
  getPublicInfo(): PublicInfo;
}
```

複数の認証方式を許可する場合は union で並べる:

```typespec
@useAuth(BearerAuth | OAuth2Auth<["read", "write"]>)
namespace MyApi;
```

---

## 8. 命名規則（Naming Convention）とドキュメンテーション

### 命名規則

TypeSpec の公式スタイルガイドに従い、以下のケースを使用する。

| 対象 | ケース |
|---|---|
| モデル、名前空間、インターフェース、ユニオン、Enum 名 | `PascalCase` |
| 操作（Operation）、プロパティ、スカラー、Enum メンバ | `camelCase` |

### ドキュメンテーション

API を利用する開発者向けに、ドキュメンテーションコメント（`/** */`）または `@doc` デコレータで、各モデル・操作の目的や詳細を記述する。Markdown が使えるため、生成ドキュメントの品質向上に直結する。

```typespec
/**
 * ユーザーリソースを表すモデル。
 * 管理 API およびプロフィール API で共通して使用される。
 */
model User {
  /** システムが自動採番するユーザー ID */
  @visibility(Lifecycle.Read)
  id: string;

  /** ユーザーの表示名（1〜100 文字） */
  @minLength(1)
  @maxLength(100)
  displayName: string;
}
```

`/** */` と `@doc` は等価だが、コメント形式の方が IDE 表示で扱いやすい場合が多い。

### 開発環境のセットアップ

- **VS Code 拡張（TypeSpec for VS Code）**: シンタックスハイライト、バリデーション、オートコンプリート、ナビゲーションを提供。Visual Studio Marketplace から導入可能
- **`tsp compile . --watch`**: ファイル保存のたびに自動コンパイル。開発中は常時有効を推奨
- **`tsp format`**: TypeSpec 1.0 以降、`tspconfig.yaml` を含む全ファイルをフォーマット可能。CI に組み込めばコードスタイルを統一できる
- **`tspconfig.yaml`**: エミッターの出力先・フォーマット・オプションを一元管理。詳細は [`tspconfig-cookbook.md`](./tspconfig-cookbook.md) を参照

---

## 9. プロジェクト構造とファイル分割

規模が大きくなると、すべての定義を `main.tsp` 一枚に書き続けるのはスケールしない。早期にファイルを分割し、モジュール化された構造を採用する。

```
├── main.tsp                # エントリポイント・サービス定義
├── models/                 # 再利用可能なデータモデル群
│   ├── users.tsp
│   ├── orders.tsp
│   └── common.tsp          # 共通モデル（エラー型・ページネーション等）
└── routes/                 # リソースごとのルート・操作定義
    ├── users.tsp
    └── orders.tsp
```

`main.tsp` はエントリポイントとして各ファイルをインポートし、サービスメタデータとルートのバインディングのみを担当する。

```typespec
import "@typespec/http";
import "./routes/users.tsp";
import "./routes/orders.tsp";

using TypeSpec.Http;

@service(#{ title: "My API" })
@server("https://api.example.com", "API endpoint")
namespace MyApi;
```

`@service` の引数は **object value literal `#{ ... }`**（TypeSpec 1.0 以降の正規構文）。旧来の object literal `({ ... })` は非推奨。

この構成により得られるメリット:

- **スケーラビリティ**: 新しいリソース追加時の既存ファイルへの影響を最小化
- **再利用性**: 共通モデルを `models/common.tsp` に集約し、複数ルートから参照
- **可読性**: 担当領域ごとにファイルが分かれ、目的のコードをすばやく見つけられる

分割の目安: リソース数が 5 を超える、または `main.tsp` が 200 行を超えたら検討する。

---

## 10. Linter による品質ゲート

TypeSpec には組み込み Linter フレームワークがあり、アンチパターン検出やベストプラクティスへの準拠を自動的に強制できる。Linter はコンパイルエラーとは異なり「動作はするが改善の余地がある」コードを検出する（例: 全型にドキュメントを要求するルール）。

`tspconfig.yaml` に組み込み、CI パイプラインで実行することで、レビュープロセスに依存せず品質基準を機械的に担保できる。

```yaml
linter:
  extends:
    - "@typespec/http/all"
```

ルールセットの選び方:

| ルールセット | 想定運用 |
|---|---|
| `@typespec/http/all` | 新規プロジェクト・厳しめの規約 |
| `@typespec/http/recommended` | 既存プロジェクトの段階導入 |

詳細は [`tspconfig-cookbook.md`](./tspconfig-cookbook.md) を参照。

`tsp compile . --stats`（1.1.0 以降）でパフォーマンスや複雑度の統計情報を確認できる。リポジトリの成長に伴うコンパイル時間劣化の検知に有用。

---

## 11. 下流ツールチェーンとの統合（コード生成パイプライン）

TypeSpec の最大のメリットの一つは、単一スキーマからバックエンド・フロントエンド・ドキュメントのすべてを自動生成できる点。TypeSpec をパイプラインの起点に置くことで、スタック全体の一貫性を担保できる。

```
TypeSpec (.tsp)
    |
    | tsp compile .
    v
OpenAPI (openapi.yaml)
    |
    +--> バックエンド: oapi-codegen (Go) / http-server-csharp / http-server-js
    |        型安全なサーバースタブ・バリデーションを自動生成
    |
    +--> フロントエンド: openapi-typescript / http-client-js
    |        型付き API クライアントを自動生成
    |
    +--> ドキュメント: Redocly CLI / Swagger UI
             インタラクティブな API ドキュメントを自動生成
```

### 主な統合ツール

| 用途 | ツール例 | ステータス |
|---|---|---|
| OpenAPI 3.0/3.1 出力 | `@typespec/openapi3` | 安定（1.x） |
| JSON Schema 出力 | `@typespec/json-schema` | 安定（1.x） |
| Go サーバーコード生成 | `oapi-codegen` | 外部ツール |
| TypeScript クライアント生成 | `@typespec/http-client-js` | プレビュー（0.x） |
| C# クライアント/サーバー生成 | `@typespec/http-client-csharp` / `@typespec/http-server-csharp` | プレビュー（0.x） |
| Java / Python クライアント生成 | `@typespec/http-client-java` / `@typespec/http-client-python` | プレビュー（0.x） |
| ドキュメント生成 | `@redocly/cli`, Swagger UI | 外部ツール |

このアプローチにより、バックエンドとフロントエンドが同じ OpenAPI ファイルから生成されるため、スキーマから乖離した実装が生まれにくくなる。TypeSpec のスキーマを更新して再コンパイルするだけで、コンパイルエラーとして不整合を即座に検出できる。

OpenAPI/JSON Schema からの移行については [`migration-openapi.md`](./migration-openapi.md) を参照。

---

これらのベストプラクティスを遵守することで、API の可読性・再利用性・保守性が向上し、TypeSpec のポテンシャルを最大限に活用した堅牢なシステム設計が可能になる。

---

> **参考情報源**
>
> - [TypeSpec 公式ドキュメント](https://typespec.io/docs/)
> - [TypeSpec 1.0 GA リリースブログ](https://typespec.io/blog/typespec-1-0-GA-release/)（2025 年 5 月）
> - [TypeSpec リリース一覧（GitHub）](https://github.com/microsoft/typespec/releases)（最新版は実環境で `npm view @typespec/compiler version` を確認）
> - [Microsoft Learn — TypeSpec Overview](https://learn.microsoft.com/en-us/azure/developer/typespec/overview)
> - [microsoft/typespec リポジトリ](https://github.com/microsoft/typespec)
> - [microsoft/typespec petstore サンプル](https://github.com/microsoft/typespec/blob/main/packages/samples/specs/rest/petstore/petstore.tsp)（`@service(#{ title: ... })` 構文の正規例）
