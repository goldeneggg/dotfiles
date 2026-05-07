# Versioning ガイド

`@typespec/versioning` は API のバージョン進化を単一コードベースで管理するためのライブラリ。`references/best-practices.md` の章 6 を補強する詳細ガイド。

---

## 1. ステータスと採用判断

`@typespec/versioning` は **プレビュー（preview）** ライブラリである（npm 上のバージョンも 0.x 系で、コアパッケージの 1.x とは独立した番号体系）。これは以下を意味する:

- API（デコレータ名・引数仕様）が将来変更される可能性がある
- アップグレード時にマイグレーションが必要となる場合がある
- 一方、Microsoft 内の Azure REST API specs では既に広範に採用されており、実用上の安定度は高い

**採用判断の指針**:
- 公開 API でバージョン互換性が重要 → 採用推奨。プレビュー API の追従コストはバージョニングが無いことによる破壊的変更コストより小さい
- 内部 API・短命なプロトタイプ → 採用しないか、バージョン列挙の最低限のみ使う

---

## 2. 基本構文

```typespec
import "@typespec/versioning";

using TypeSpec.Versioning;

@versioned(Versions)
@service(#{ title: "Pet Store" })
namespace PetStore;

enum Versions {
  v1: "2024-01-01",
  v2: "2024-06-01",
  v3: "2025-01-01",
}
```

- `enum Versions` の各メンバはバージョン識別子。値（文字列）はリリース日や semver など、外部に公開する文字列形式に合わせる
- `@versioned` を namespace に付けることで、その配下の全てのモデル・操作にバージョンデコレータを適用可能になる

---

## 3. 進化系デコレータ

| デコレータ | 用途 | 典型的な使用文脈 |
|---|---|---|
| `@added(Versions.v2)` | このバージョン以降に追加された型・プロパティ・操作 | 新エンドポイント・新フィールド |
| `@removed(Versions.v3)` | このバージョン以降に削除 | 廃止機能 |
| `@renamedFrom(Versions.v2, "oldName")` | このバージョンで名称変更 | フィールド名整理 |
| `@madeOptional(Versions.v2)` | このバージョンで必須から任意へ | バリデーション緩和 |
| `@madeRequired(Versions.v2)` | 任意から必須へ（破壊的変更） | 強制マイグレーション |
| `@typeChangedFrom(Versions.v2, OldType)` | 型変更 | スキーマ進化 |
| `@returnTypeChangedFrom(Versions.v2, OldType)` | 操作の戻り値型変更 | レスポンス進化 |

### 3.1 プロパティの追加

```typespec
model User {
  id: string;
  name: string;

  @added(Versions.v2)
  email: string;
}
```

v1 ではプロパティが存在せず、v2 で追加される。v2 以降のクライアントは `email` を期待でき、v1 クライアントは送信しない。

### 3.2 名前変更（後方互換）

```typespec
model User {
  id: string;

  @renamedFrom(Versions.v2, "userName")
  name: string;
}
```

v1 では `userName`、v2 以降は `name`。生成される OpenAPI は両バージョンで適切な名前になる。

### 3.3 必須から任意へ

```typespec
model CreateUserRequest {
  name: string;

  @madeOptional(Versions.v2)
  email?: string;
}
```

v1 では `email` が必須、v2 以降は任意。意外と頻発するパターン。

---

## 4. 複数バージョンを同時に出力

```yaml
# tspconfig.yaml
emit:
  - "@typespec/openapi3"
options:
  "@typespec/openapi3":
    emitter-output-dir: "{output-dir}/openapi/{version}"
    output-file: "openapi.yaml"
```

`{version}` 変数を使うことで、`enum Versions` の各メンバごとに OpenAPI ファイルが生成される。クライアント SDK 生成パイプラインでは、各バージョンを独立した出力ディレクトリで管理することが多い。

---

## 5. アンチパターン

### 5.1 全フィールドに無闇に `@added` を付ける

```typespec
// BAD: 全部に付けると初期バージョン v1 から既に存在するものまで追加扱いになる
model User {
  @added(Versions.v1)  // 不要
  id: string;
  @added(Versions.v1)  // 不要
  name: string;
}
```

`@added` は「あるバージョンで追加された」ことを示すデコレータ。最初のバージョンに含まれる要素には不要。

### 5.2 enum の値を後から変更する

`enum Versions` のメンバ値（バージョン文字列）は OpenAPI 出力の `info.version` などに反映される。リリース後に変更すると下流のクライアント識別が狂うため、原則として一度確定したら不変。

### 5.3 バージョン分岐の濫用

`@added`/`@removed` を多用しすぎると一つのモデルが「歴史の堆積層」になり、可読性が下がる。**メジャーな仕様変更は名前空間ごと分ける**（例: `PetStore.V1`, `PetStore.V2`）方が現実的なケースもある。

---

## 6. 移行戦略

新規プロジェクトでバージョニングを後付けする場合の手順:

1. 現状の API を `Versions.v1` として固定
2. `@versioned(Versions)` を namespace に追加
3. 既存モデル・操作にはデコレータを付けない（v1 から存在するため）
4. 新機能は `@added(Versions.v2)` で導入
5. CI で `tsp compile . --emit @typespec/openapi3` を全バージョンに対して実行し、互換性を確認

---

## 7. プレビュー追従の指針

`@typespec/versioning` のメジャーアップデートでデコレータ名や引数が変わる可能性に備えて:

- **バージョン管理コードの集約**: 進化系デコレータは可能な限り 1 ファイル（例: `models/versions.tsp`）に集めると、ライブラリ更新時の差し替え範囲が局所化できる
- **CI でリリースノート確認**: `npm outdated @typespec/versioning` を定期的に実行し、メジャー更新時はリリースノートを必読する
- **生成 OpenAPI の差分監視**: バージョン文字列を含む OpenAPI を Git にコミットしておけば、デコレータ仕様変更による出力差分を PR で検知できる
