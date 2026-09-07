# OpenAPI / JSON Schema → TypeSpec 移行ガイド

既存の OpenAPI 仕様や JSON Schema を TypeSpec に移行するための実践ガイド。`references/best-practices.md` 全章を、移行作業の文脈で再構成したもの。

---

## 1. 全体方針

移行は公開契約の互換性維持を既定とする。経路、型、必須性、認証、エラー、シリアライズを保持し、生成仕様と元仕様の意味を比較する。
共通化・Visibility導入・エラーモデル統一などの再設計は、依頼範囲に含まれる場合だけ行う。移行を理由に作業範囲を広げない。

1. 必要なら自動変換ツールで叩き台を作る。
2. コンパイルし、生成仕様を元仕様と比較して欠落・不一致を修正する。
3. 再設計も依頼されている場合だけ、合意された範囲を実施して互換性を再検証する。

作業範囲と完了条件はユーザーの依頼とSKILL.mdのモード別制約に従う。範囲外の再設計・CI追加を移行完了の条件にしない。

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

## 5. 再設計を依頼された場合のベストプラクティス

以下は再設計が依頼範囲に含まれる場合だけ検討する。形式変換だけの依頼では必須にせず、必要なら別タスクとして提案する。
適用時も公開契約への影響を確認し、契約変更が必要ならその扱いを確定してから進める。

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
| `@defaultResponse` の誤用 | `@statusCode` 付きモデルや `@error` モデルに `@defaultResponse` を付けると 1.13.0 で警告 | `@error` モデルは用途に応じて使い分ける |

---

## 8. 移行完了後のチェックリスト

- [ ] `tsp compile .` がエラーなしで通る
- [ ] `tsp format --check` が差分なしで通る
- [ ] 生成仕様の経路、型、必須性、認証、エラー、シリアライズが元仕様と一致するか、依頼された変更として説明できる
- [ ] 保護対象の認証要件が生成仕様で保持されている
- [ ] 変換できない要素、残る不一致、未検証事項が報告されている

次は依頼範囲に含まれる場合だけ確認し、範囲外なら適用外とする。未実施を移行未完了の理由にしない。

- [ ] エラーモデルの共通化と`@error`の使用が合意した設計・公開契約に適合する
- [ ] Visibilityが合意したCreate/Read/Updateの設計に適合する
- [ ] バージョニングが必要なら設定・生成結果を確認している（`references/versioning-guide.md`参照）
- [ ] CI追加が依頼されていればcompile・format checkを組み込んでいる（`references/tspconfig-cookbook.md`参照）

検証を実行できない場合は理由と未検証範囲を報告し、チェック済み・成功と扱わない。
