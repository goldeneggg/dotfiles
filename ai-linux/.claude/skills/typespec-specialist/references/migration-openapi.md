# OpenAPI / JSON Schema → TypeSpec 移行ガイド

既存の OpenAPI 仕様や JSON Schema を TypeSpec に移行するための実践ガイド。`references/best-practices.md` 全章を、移行作業の文脈で再構成したもの。

---

## 1. 全体方針

移行は「単純変換 → 後で整理」より「変換時に best-practices に沿って再設計」する方が長期的に得をする。理由:

- OpenAPI/JSON Schema はモデル指向で書かれていることが多く、ループバック展開された結果として共通化が崩れているケースが多い
- TypeSpec のスプレッド・ジェネリクス・Visibility といった抽象化機能は、移行時に整理する絶好のタイミングで適用できる
- 機械的な往復変換だけ行うと、TypeSpec 採用の主目的（保守性向上）が達成できない

ただし、規模が大きい場合は段階移行が現実的:

1. **Phase 1**: 自動変換ツールで叩き台を作る
2. **Phase 2**: コンパイルを通し、生成 OpenAPI が元仕様と概ね一致することを確認
3. **Phase 3**: best-practices に沿って手動でリファクタ（共通化・Visibility・エラー統一）

---

## 2. 元ファイル形式の判定

| 形式 | 識別ポイント | 移行優先度 |
|---|---|---|
| OpenAPI 3.1 | ルートに `openapi: 3.1.x`、`$schema` を含むことがある | 直接変換しやすい（JSON Schema 2020-12 互換） |
| OpenAPI 3.0 | `openapi: 3.0.x`、`nullable: true` の使用 | 3.1 化を兼ねた整理推奨 |
| Swagger 2.0 | `swagger: "2.0"`、`definitions` セクション | 一度 OpenAPI 3 に上げてから移行する方が安全 |
| JSON Schema 単体 | `$schema` URI で draft を判定 | データモデル部分のみ TypeSpec model に変換 |
| YAML / JSON | 拡張子と先頭文字 | 中身は同じスキーマなので形式は問わない |

---

## 3. 自動変換ツールの活用

### 3.1 公式コンバータ

OpenAPI 3.0 → TypeSpec の自動変換ツールは Microsoft が提供している。代表的なものは npm レジストリで `@typespec/openapi3-to-typespec` 等の名称で探せる（パッケージ名・ステータスは時期により変動するため要確認）。

```bash
npx @typespec/openapi3-to-typespec convert ./openapi.yaml --output ./tsp/
```

**強み**: モデル定義・パス・パラメータ・レスポンス構造を機械的に展開してくれる。
**弱み**: 名前空間ネスト・Visibility・エラーモデル統一などの「設計判断」は反映されない。

### 3.2 部分的な手動移行

ツールが古い OpenAPI 仕様を取り扱えない場合や、設計を抜本的に見直したい場合は手動移行を選ぶ。下記マッピング表を参照。

---

## 4. マッピング詳細

### 4.1 構造のマッピング

| OpenAPI / JSON Schema | TypeSpec | 補足 |
|---|---|---|
| `info.title` | `@service(#{ title: "..." })` | `#{}` は object value literal（1.0+） |
| `servers[]` | `@server("url", "description")` | 複数並べて宣言可能 |
| `tags[]` | `@tag("name")` | namespace/interface に付与 |
| `components/schemas/<Name>` | `model <Name> { ... }` | PascalCase 維持 |
| `paths/<path>` | `interface` + `@route("path")` | リソース単位でグルーピング |
| `paths.<path>.<method>` | `op <name>(): <Response>` | HTTP メソッドは `@get`/`@post`/`@put`/`@patch`/`@delete` |
| `parameters` (header/query/path) | `@header`, `@query`, `@path` | 各 op の引数で宣言 |
| `requestBody` | `@body` 引数 | content-type は `@header contentType` で個別指定可能 |
| `responses.<status>` | `model X { @statusCode statusCode: <N>; ... }` | 標準ヘルパー型（`OkResponse` 等）も活用 |
| `securitySchemes` | `BearerAuth`/`BasicAuth`/`OAuth2Auth` | `@useAuth` で適用 |

### 4.2 制約のマッピング

| JSON Schema 制約 | TypeSpec デコレータ |
|---|---|
| `minLength` / `maxLength` | `@minLength` / `@maxLength` |
| `minimum` / `maximum` | `@minValue` / `@maxValue` |
| `pattern` | `@pattern` |
| `format: "email"` | `@format("email")` または `string` の subtype |
| `enum` | `union` または `enum` 構造 |
| `nullable: true` (3.0) | `T \| null` の union（3.1 と同じ表現） |
| `default` | `= value` 構文 |

### 4.3 認証のマッピング例

OpenAPI:
```yaml
components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
security:
  - bearerAuth: []
```

TypeSpec:
```typespec
@useAuth(BearerAuth)
namespace MyApi;
```

---

## 5. 再設計のチャンスとして適用すべきベストプラクティス

単純変換に留めず、以下を移行と同時に適用する:

### 5.1 共通パラメータの抽出（章 2）

OpenAPI で各 path に重複展開されている `X-Request-ID` 等のヘッダーを TypeSpec の共通モデル化:

```typespec
model CommonHeaders {
  @header("X-Request-ID") requestId?: string;
  @header("Accept-Language") locale?: string;
}

op listUsers(...CommonHeaders): User[];
op getUser(...CommonHeaders, @path id: string): User;
```

### 5.2 エラーモデルの統一（章 3）

OpenAPI で散らばっているエラーレスポンスを `@error` モデルに集約:

```typespec
@error
model ApiError {
  code: string;
  message: string;
  details?: Record<unknown>;
}

@error
model ValidationError extends ApiError {
  @statusCode statusCode: 400;
}

@error
model NotFoundError extends ApiError {
  @statusCode statusCode: 404;
}
```

### 5.3 Visibility の導入（章 4）

OpenAPI で `UserCreate` / `UserUpdate` / `UserResponse` の 3 モデルに分かれているものを単一 `User` + Visibility に統合:

```typespec
model User {
  @visibility(Lifecycle.Read)
  id: string;

  @visibility(Lifecycle.Read, Lifecycle.Update)
  email: string;

  @visibility(Lifecycle.Create)
  password: string;
}
```

### 5.4 ファイル分割（章 9）

最初から `models/` と `routes/` に分けると後の拡張が楽。1 ファイルでスタートしても良いが、5 リソースを超えたら分割を検討する。

---

## 6. 検証ステップ

### 6.1 コンパイル → OpenAPI 再生成

```bash
npx tsp compile .
```

`tsp-output/schema/openapi.yaml` を元の `openapi.yaml` と diff し、意図しない変化がないかを確認する。

### 6.2 差分の典型カテゴリ

| 差分の種類 | 対処 |
|---|---|
| プロパティ順序の違い | 通常は無視可（OpenAPI 仕様上意味なし） |
| `additionalProperties: false` の有無 | TypeSpec のデフォルト挙動を確認し必要に応じて `@withSpread` 等を調整 |
| `nullable` 表現の違い | OpenAPI 3.1 では `type: [..., "null"]` 形式に変わる |
| `description` の脱落 | 元仕様に存在した `description` は `@doc` または `/** */` で復元 |

### 6.3 クライアント生成テスト

可能であれば下流の SDK ジェネレータ（`openapi-typescript`、`oapi-codegen` 等）に通し、移行前後で生成型が等価であることを確認する。これは仕様の「下流互換性」検証になる。

---

## 7. よくある落とし穴

| 落とし穴 | 説明 | 対処 |
|---|---|---|
| `discriminator` の表現差 | OpenAPI と TypeSpec の `discriminator` 解釈に微妙な差がある | `@discriminator` デコレータの公式ドキュメントを必ず確認 |
| `oneOf` / `anyOf` | TypeSpec の union と OpenAPI の `oneOf`/`anyOf` は厳密には別物 | union は `oneOf` に近い意味で出力される。意図と違う場合は手動調整 |
| `$ref` の循環参照 | TypeSpec は名前空間で解決するが、深い循環は警告対象 | フラットな共通モデル層を作って解消 |
| `allOf` の継承 | TypeSpec では `extends` または `is` で表現 | 多重継承相当が必要なら spread 演算子の併用 |
| `examples` の脱落 | `@example` デコレータで明示的に書き戻す必要がある | 重要な API は手動で例を再追加 |

---

## 8. 移行完了後のチェックリスト

- [ ] `tsp compile .` がエラーなしで通る
- [ ] `tsp format --check` が差分なしで通る
- [ ] 生成 OpenAPI の `info`, `paths`, `components.schemas` の主要エントリが元仕様と一致
- [ ] `@useAuth` が全保護対象に明示されている
- [ ] エラーモデルが共通化され `@error` 付きで定義されている
- [ ] Visibility が適切に導入され、Create/Read/Update の意図が型に表れている
- [ ] バージョニングが必要なら `@versioned` 設定済み（`references/versioning-guide.md` 参照）
- [ ] CI に `tsp compile`/`tsp format --check` が組み込まれている（`references/tspconfig-cookbook.md` 参照）
