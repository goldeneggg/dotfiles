# TypeSpecによるAPIスキーマ設計のベストプラクティス

> **📌 バージョン情報（2026年5月時点）**
> TypeSpec は **1.11.0** が最新リリースです。2025年5月に 1.0 GA（一般提供）となり、プロダクション利用が公式にサポートされています。
>
> | コンポーネント | ステータス |
> |---|---|
> | `@typespec/compiler` / `@typespec/http` / `@typespec/openapi` | ✅ 安定版（Stable） |
> | `@typespec/openapi3` / `@typespec/json-schema` | ✅ 安定版（Stable） |
> | `@typespec/versioning` / `@typespec/rest` / `@typespec/xml` | 🔶 プレビュー（Preview） |
> | クライアント・サーバーコード生成（.NET / JS / Java / Python） | 🔶 プレビュー（Preview） |

TypeSpecを利用してAPIスキーマを実装する際は、単一のコードベースを「信頼できる情報源（Single Source of Truth）」とし、一貫性のあるAPI定義やクライアントコード、ドキュメントを生成できるように設計することが重要です。

---

## 1. 名前空間（Namespace）のネストによる論理的な構造化

APIのモデルや操作（Operation）は、名前空間を使用して論理的にグループ化します。特にネストされた名前空間を活用することで、以下の利点が得られます。

- **整理と管理の向上**: 関連する操作（例: CRUD操作など）をまとめることで、APIの全体構造が把握しやすくなります。
- **Operation IDの明確化**: OpenAPIなどの仕様を出力する際、TypeSpecは名前空間をプレフィックスとして `operationId` に自動付与するため（例: `Pets_listPets`）、どのリソースに対する操作であるかが明確になります。
- **名前の衝突回避**: 異なるリソース間で同名の操作やモデルが存在した場合の衝突を防ぎます。

### `@tag` デコレータによる操作グルーピング

名前空間による構造化に加え、`@tag` デコレータを使うことでOpenAPIドキュメント上での操作グループをさらに細かく制御できます。名前空間とタグは別軸の整理方法であり、組み合わせることでより読みやすいAPIドキュメントが生成されます。

```typescript
interface Routes {
  @tag("Search")
  @route("")
  @get
  getSearch(): SearchModel.Search[];

  @tag("Search")
  @route("/byName/{name}")
  @get
  getSearchByName(@path name: string): SearchModel.Search;
}
```

---

## 2. 共通パラメータとモデルの再利用

複数のAPI操作で共通して使用されるパラメータ（例: リクエストID、ロケール情報、クライアントバージョンなど）は、個別の操作にハードコードするべきではありません。

代わりに、共通パラメータを一つのモデルとして定義し、**スプレッド演算子（`...`）**を使用して各操作の引数に展開します。これにより、API全体でパラメータの適用が一貫し、冗長性とエラーの発生を減らすことができます。

---

## 3. カスタムレスポンスと構造化されたエラーモデルの定義

- **カスタムレスポンスモデル**: TypeSpecのHTTPライブラリに組み込まれた標準レスポンス（`OkResponse (200)` や `CreatedResponse (201)` など）を拡張（`extends`）して、ドメインに特化した名前付きレスポンスモデルを定義します。これによりAPIの意図が明確になり、コードの重複を防ぐことができます。
- **エラーモデルの共通化**: 生のステータスコードをそのまま返すのではなく、`@error` デコレータを用いて `ValidationError` や `NotFoundError` といった構造化されたエラーモデルを定義します。各操作の戻り値には、`|` 演算子を用いて正常系とエラー系のモデルを併記することで、クライアント側でのエラーハンドリングが予測しやすくなります。

### ジェネリックなレスポンスラッパーパターン

ジェネリック型を活用した共通レスポンスラッパーを定義することで、成功・エラーの構造をAPI全体で統一できます。

```typescript
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

各エンドポイントではこのラッパーを使い回します。

```typescript
op getSearch(): DefaultResponse.Response<SearchModel.Search[]>;
op getUser(@path id: string): DefaultResponse.Response<User>;
```

### PATCH操作と部分更新（1.0以降の変更点）

TypeSpec 1.0 以降、`@patch` はデフォルトで "implicit optionality"（暗黙的な省略可能化）変換を適用しなくなりました。部分更新（JSON Merge-Patch）を実装するには、`MergePatchUpdate<T>` テンプレートを明示的に使用します。

```typescript
// ✅ 推奨: JSON Merge-Patch による部分更新
@patch op update(@body pet: MergePatchUpdate<Pet>): void;

// 旧来の挙動を維持したい場合（非推奨）
@patch(#{ implicitOptionality: true }) op update(@body pet: Pet): void;
```

---

## 4. ライフサイクル・ビジビリティ（Visibility）の活用

TypeSpecの強力な機能である「Visibility（可視性）」を利用することで、リクエスト時とレスポンス時などの「文脈」に応じてモデルの構造（ビュー）を動的に変化させることができます。

組み込みのライフサイクル修飾子（`Lifecycle.Create`, `Lifecycle.Read`, `Lifecycle.Update`, `Lifecycle.Delete`, `Lifecycle.Query`）をプロパティに適用することで、以下の制御が可能です。

- **レスポンス専用**: 自動生成される `id` のように、`Lifecycle.Read`（GETレスポンスなど）でのみ表示させる。
- **リクエスト専用**: `password` のように、`Lifecycle.Create` や `Lifecycle.Update`（POST/PUTリクエスト）でのみ入力を許可する。

```typescript
model TodoItem {
  @visibility(Lifecycle.Read)
  id: string;          // レスポンスのみに含まれる

  content: string;
  dueDate: utcDateTime;

  @visibility(Lifecycle.Create)
  initialTag?: string; // 作成時のみ指定可能
}
```

これにより、POST用・GET用といった似たようなモデルを複数作成する（型の増殖）必要がなくなり、単一の論理モデルを維持したままシンプルに管理できます。

### `FilterVisibility` の活用（1.11.0以降推奨）

TypeSpec 1.11.0 から、`@withVisibilityFilter` デコレータは**非推奨**となりました。代わりに `FilterVisibility` テンプレートを使用します。`FilterVisibility` はデコレータメタデータの保持に関するバグが修正されており、より正確なビジビリティ変換を提供します。

```typescript
// ✅ 推奨（1.11.0以降）
model CreateAndReadExample
  is FilterVisibility
    Example,
    #{ all: #[Lifecycle.Create, Lifecycle.Read] },
    "CreateAndRead{name}"
  >;

// ❌ 非推奨（@withVisibilityFilter）
// @withVisibilityFilter(#{ all: #[Lifecycle.Create] })
// model CreateExample is Example {}
```

---

## 5. 堅牢なルーティング定義

エンドポイントのパス定義には、`@route` デコレータを使用して明示的に記述する方法のほかに、`@autoRoute` と `@segment` デコレータを組み合わせる方法があります。

リソース指向の設計においては、モデル側に `@segment` でパスのセグメント（例: `pets`）を定義し、インターフェースや操作に `@autoRoute` を適用することで、パラメータからURLルートを自動かつ一貫して生成できるため、保守性が高まります。

---

## 6. APIのバージョン管理（Versioning）の統合

> ⚠️ **`@typespec/versioning` は現在プレビューライブラリ**です。本番環境での採用にあたっては、将来的なAPIの変更に注意してください。

APIの変更を既存クライアントに影響を与えずに安全に進めるため、初期段階から `@typespec/versioning` ライブラリを使用することが推奨されます。

列挙型（`enum`）でサポートするバージョンを定義し、APIのNamespaceに `@versioned` デコレータを設定します。APIの変更箇所に以下のようなデコレータを付与することで、同一のコードベースから各バージョンごとのAPI仕様を独立して生成できます。

| デコレータ | 用途 |
|---|---|
| `@added` | 特定のバージョンから追加 |
| `@removed` | 削除 |
| `@renamedFrom` | プロパティ名の変更 |
| `@madeOptional` | 必須から任意への変更 |

---

## 7. 認証・認可ポリシーの明示

APIのセキュリティ要件は、`@useAuth` デコレータを使用して明示的に定義します。`BearerAuth`、`BasicAuth`、`OAuth2` などの標準的な認証方式を利用し、Namespace全体・Interface・個別のOperationレベルに適用します。

これを適用することで、生成されるOpenAPIドキュメント上で「どのエンドポイントがどのような認証を要求するか」がセキュリティ定義として正確に出力されます。

```typescript
@useAuth(BearerAuth)
interface ProtectedRoutes {
  @get getProfile(): UserProfile;

  // 一部のエンドポイントは認証不要にする場合
  @useAuth(NoAuth)
  @get
  getPublicInfo(): PublicInfo;
}
```

---

## 8. 命名規則（Naming Convention）とドキュメンテーション

### 命名規則

TypeSpecの公式スタイルガイドに従い、以下のケースを使用します。

| 対象 | ケース |
|---|---|
| モデル、名前空間、インターフェース、ユニオン | `PascalCase` |
| 操作（Operation）、プロパティ、スカラー | `camelCase` |

### ドキュメンテーション

APIを利用する開発者向けに、ドキュメンテーションコメント（`/** */`）または `@doc` デコレータを使用して、各モデルや操作の目的・詳細を記述します。ドキュメントにはMarkdownフォーマットが使用でき、生成されるドキュメントの品質向上に直接繋がります。

```typescript
/**
 * ユーザーリソースを表すモデル。
 * 管理APIおよびプロフィールAPIで共通して使用される。
 */
model User {
  /** システムが自動採番するユーザーID */
  @visibility(Lifecycle.Read)
  id: string;

  /** ユーザーの表示名（1〜100文字） */
  @minLength(1)
  @maxLength(100)
  displayName: string;
}
```

### 開発環境のセットアップ

快適な開発のために、以下のツールを活用します。

- **VS Code拡張（TypeSpec for VS Code）**: シンタックスハイライト、バリデーション、オートコンプリート、ナビゲーションを提供します。Visual Studio Marketplaceからインストール可能です。
- **`tsp compile . --watch`**: ファイル保存のたびに自動コンパイルするウォッチモード。開発中は常に有効にすることを推奨します。
- **`tsp format`**: TypeSpec 1.0 以降、`tspconfig.yaml` を含むすべての管理ファイルをフォーマット可能です。CIに組み込むことでコードスタイルを統一できます。
- **`tspconfig.yaml`**: エミッターの出力先・フォーマット・オプションを一元管理する設定ファイルです。

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

---

## 9. プロジェクト構造とファイル分割

規模が大きくなるにつれて、すべての定義を `main.tsp` 一枚に書き続けることはスケールしません。早期にファイルを分割し、モジュール化された構造を採用することを推奨します。

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

`main.tsp` はエントリポイントとして各ファイルをインポートし、サービスメタデータとルートのバインディングのみを担当します。

```typescript
import "@typespec/http";
import "./routes/users.tsp";
import "./routes/orders.tsp";

using TypeSpec.Http;

@service({ title: "My API" })
@server("https://api.example.com", "API endpoint")
namespace MyApi;

@route("/users")
interface Users extends global.Users.Routes {}

@route("/orders")
interface Orders extends global.Orders.Routes {}
```

この構成により、以下のメリットが得られます。

- **スケーラビリティ**: 新しいリソースを追加する際に、既存ファイルへの影響を最小化できます。
- **再利用性**: 共通モデルを `models/common.tsp` に集約し、複数のルートから参照できます。
- **可読性**: 担当領域ごとにファイルが分かれるため、目的のコードをすばやく見つけられます。

---

## 10. Linterによる品質ゲート

TypeSpecには組み込みのLinterフレームワークが搭載されており、アンチパターンの検出やベストプラクティスへの準拠を自動的に強制できます。Linterはコンパイルエラーとは異なり、「動作はするが改善の余地がある」コードを検出します（例: すべての型にドキュメントを要求するルールなど）。

`tspconfig.yaml` に組み込み、CIパイプラインで実行することで、レビュープロセスに依存せず品質基準を機械的に担保できます。

```yaml
linter:
  extends:
    - "@typespec/http/all"
```

チームのAPIガイドラインに合わせたカスタムルールセットの作成も可能です。また、`tsp compile` 実行時に `--stats` フラグを付けると（1.1.0以降）、パフォーマンスや複雑度の統計情報を確認できます。

```bash
tsp compile . --stats
```

---

## 11. 下流ツールチェーンとの統合（コード生成パイプライン）

TypeSpecの最大のメリットの一つは、単一のスキーマからバックエンド・フロントエンド・ドキュメントのすべてを自動生成できる点です。TypeSpecをパイプラインの起点として位置づけることで、スタック全体の一貫性を担保できます。

```
TypeSpec (.tsp)
    │
    ▼ tsp compile .
OpenAPI (openapi.yaml)
    │
    ├──▶ バックエンド: oapi-codegen（Go）/ http-server-csharp / http-server-js 等
    │         型安全なサーバースタブ・バリデーションを自動生成
    │
    ├──▶ フロントエンド: openapi-typescript（TypeScript）/ http-client-js 等
    │         型付きAPIクライアントを自動生成
    │
    └──▶ ドキュメント: Redocly CLI / Swagger UI 等
              インタラクティブなAPIドキュメントを自動生成
```

### 主な統合ツール

| 用途 | ツール例 | ステータス |
|---|---|---|
| OpenAPI 3.0/3.1 出力 | `@typespec/openapi3` | ✅ 安定版 |
| JSON Schema 出力 | `@typespec/json-schema` | ✅ 安定版 |
| Go サーバーコード生成 | `oapi-codegen` | 外部ツール |
| TypeScript クライアント生成 | `@typespec/http-client-js` | 🔶 プレビュー |
| C# クライアント/サーバー生成 | `@typespec/http-client-csharp` / `@typespec/http-server-csharp` | 🔶 プレビュー |
| Java / Python クライアント生成 | `@typespec/http-client-java` / `@typespec/http-client-python` | 🔶 プレビュー |
| ドキュメント生成 | `@redocly/cli`, Swagger UI | 外部ツール |

このアプローチにより、バックエンドとフロントエンドが同じOpenAPIファイルから生成されるため、スキーマから乖離した実装が生まれにくくなります。TypeSpecのスキーマを更新して再コンパイルするだけで、コンパイルエラーとして不整合を即座に検出できます。

---

これらのベストプラクティスを遵守することで、APIの可読性・再利用性・保守性が向上し、TypeSpecのポテンシャルを最大限に活用した堅牢なシステム設計が可能になります。

---

> **参考情報源**
> - [TypeSpec 公式ドキュメント](https://typespec.io/docs/)
> - [TypeSpec 1.0 GA リリースブログ](https://typespec.io/blog/typespec-1-0-GA-release/)（2025年5月）
> - [TypeSpec 1.11.0 リリースノート](https://typespec.io/release-notes/typespec-1-11-0/)（最新）
> - [Microsoft Learn — TypeSpec Overview](https://learn.microsoft.com/en-us/azure/developer/typespec/overview)（2026年3月更新）
> - [GitHub microsoft/typespec](https://github.com/microsoft/typespec)
