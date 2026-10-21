# tspconfig.yaml クックブック

確認日: 2026-10-21。compiler・OpenAPI emitter 1.17.0を基準とする。既存プロジェクトではlockfileの版を優先する。

`tspconfig.yaml` は TypeSpec プロジェクトの設定ファイルであり、エミッター・Linter・出力先・コンパイラオプションを一元管理する。CI と開発環境で同じ設定が再現されることを担保するため、原則としてリポジトリにコミットする。

このドキュメントは `references/best-practices.md` の章 10「Linter による品質ゲート」と章 11「下流ツールチェーン統合」を補強するレシピ集である。

---

## 1. 基本構造

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

- `emit`: 実行するエミッターのリスト（複数可）
- `options.<emitter-name>`: エミッター固有の設定
- `linter.extends`: 適用する Linter ルールセット

`{output-dir}` などの組み込み変数を活用すると、出力先をエミッター単位で切り替えやすい。

### 1.1 プロジェクト設定（1.13.0 以降）

`kind: project` と `entrypoint` でプロジェクト境界とエントリポイントを明示できる:

```yaml
kind: project
entrypoint: src/service.tsp
emit:
  - "@typespec/openapi3"
options:
  "@typespec/openapi3":
    emitter-output-dir: "{output-dir}/schema"
```

- `kind: project`: このディレクトリが TypeSpec プロジェクトの境界であることを宣言
- `entrypoint`: コンパイルのエントリポイントファイルを明示指定

モノレポや複数サービスの構成で、コンパイラがどのファイルを起点にするかを一意に決定したい場合に有効。省略した場合は従来通りの解決ロジック。

### 1.2 Feature Flags（1.13.0 以降）

プロジェクトスコープのコンパイラ機能フラグを有効化できる:

```yaml
kind: project
features:
  - function-declarations
```

利用可能なフラグ一覧はローカルCLIの `tsp info features` で確認する。flagの追加は実験的機能を採用する判断であり、安定化ではない。

| 機能 | 1.17.0でのflag |
|---|---|
| 関数宣言 | `function-declarations` |
| メタデータ保存用デコレータ | `auto-decorators` |
| unionの共通基底型制約 | `union-extends` |
| 宣言式 | `declaration-expressions` |
| ライブラリのIDE型情報 | `type-info-provider` |

必要なflagだけを列挙し、機能を宣言するプロジェクト・ライブラリに設定する。導入版と例は [`language-updates.md`](./language-updates.md) を参照。

---

## 2. エミッター設定の典型レシピ

### 2.1 OpenAPI 3.1 を出力（推奨デフォルト）

```yaml
emit:
  - "@typespec/openapi3"
options:
  "@typespec/openapi3":
    emitter-output-dir: "{output-dir}/openapi"
    openapi-versions:
      - 3.1.0
    output-file: "openapi.{version}.yaml"
```

OpenAPI 3.1 は JSON Schema 2020-12 完全互換であり、`nullable` 等の差分が解消されている。新規プロジェクトでは原則 3.1 を選ぶ。
これはこの資料の選択指針であり、emitterの既定値は3.0.0。下流ツールが対応する版を明示する。1.17.0では `3.2.0` も指定可能。

### 2.2 OpenAPI 3.0 と 3.1 を併存出力

下流のツールチェーンが 3.0 にしか対応していない場合（一部の SDK ジェネレータで起こりうる）、両方を出力する:

```yaml
options:
  "@typespec/openapi3":
    openapi-versions:
      - 3.0.0
      - 3.1.0
```

両バージョン併存は「移行期間中」の運用。長期に持つほどメンテコストが増えるため、片方に寄せるロードマップを引くこと。

### 2.3 JSON Schema を併出力

```yaml
emit:
  - "@typespec/openapi3"
  - "@typespec/json-schema"
options:
  "@typespec/json-schema":
    emitter-output-dir: "{output-dir}/json-schema"
    file-type: "yaml"
```

API 仕様（OpenAPI）とイベント/メッセージスキーマ（JSON Schema 単体）を併用するシステムで有効。

### 2.4 注釈付きenum（1.14以降、OpenAPI 3.1以上）

```yaml
emit:
  - "@typespec/openapi3"
options:
  "@typespec/openapi3":
    openapi-versions:
      - 3.1.0
    enum-strategy: annotated
```

enumメンバーのdoc・summaryを `oneOf` / `const` のdescription・titleとして出力する。下流のenum処理に影響するため、生成物を確認して採用する。3.0出力では警告され、従来のenum形式になる。

`file-type: [yaml, json]` で両形式を出す場合は、`output-file: "openapi.{version}.{file-type}"` のように拡張子を分ける。

---

## 3. Linter 設定の選び方

1.17.0の `@typespec/http` は `all` と `op-reference-container-route` ルールを提供する。`recommended` ルールセットや `no-unused-routes` ルールは提供していない。段階導入では実在するルールを `enable` で選ぶ。

### 3.1 個別ルールの上書き

```yaml
linter:
  extends:
    - "@typespec/http/all"
  disable:
    "@typespec/http/op-reference-container-route": "プロジェクト固有のルーティング戦略のため除外"
```

`disable` には必ず除外理由を文字列で添える。後続のメンテナーが判断しやすい。

### 3.2 ルールオプションの設定（1.12.0 以降）

Linterルールが型付きオプションを受け付けるようになった。以下は独自ライブラリを導入済みで、そのルールが対応する場合の例:

```yaml
linter:
  enable:
    # デフォルト値で使う場合は、下のオブジェクトの代わりにtrueを指定
    # カスタムオプション付きで有効化
    "@typespec/my-lib/no-model-with-name":
      bannedName: "Bar"
```

### 3.3 カスタムルールセットの拡張

独自の検査ロジックはライブラリに実装する。既存ルールの選択・設定だけを共有する場合、1.16以降は単独のYAMLファイルを参照できる:

```yaml
# tspconfig.yaml
linter:
  extends:
    - "file:../common-rules.yaml"
```

```yaml
# ../common-rules.yaml
extends:
  - "@typespec/http/all"
```

`file:` の相対パスは、それを記述したconfig・rulesetファイルから解決する。ライブラリ内のruleset定義には `file:` を使えない。
1.15以降の短縮名（例: `http/op-reference-container-route`）はライブラリのロードが必要で、衝突した場合は完全名を使用する。

---

## 4. CI/CD 連携

### 4.1 フォーマット検証

`tsp format --check` は差分があると非ゼロ終了する。プリコミットフックと CI 双方に組み込むことで、フォーマット漂流を防げる。

```yaml
# GitHub Actions 例
- name: TypeSpec format check
  run: npx tsp format --check "**/*.tsp"
```

### 4.2 コンパイル + Linter 実行

```yaml
- name: TypeSpec compile
  run: npx tsp compile . --warn-as-error
```

`--warn-as-error` を付けることで Linter 警告も CI 失敗扱いとなり、品質基準を機械的に強制できる。

### 4.3 統計の記録（1.1.0 以降）

```yaml
- name: TypeSpec stats
  run: npx tsp compile . --stats
```

`--stats` はコンパイル時間・ノード数・テンプレート展開回数等を出力する。レポジトリの成長に伴うパフォーマンス劣化検知に有用。

### 4.4 生成成果物の保存

```yaml
- name: Upload OpenAPI
  uses: actions/upload-artifact@v4
  with:
    name: openapi-spec
    path: tsp-output/schema/
```

PR レビュー時に生成 OpenAPI を直接確認できるよう、artifact として保存しておく。

---

## 5. パスとファイル分割

`tspconfig.yaml` 自体の場所はコンパイル対象 `.tsp` のあるディレクトリに置く。モノレポの場合はサービス単位で配置する:

```
services/
├── billing/
│   ├── tspconfig.yaml
│   ├── main.tsp
│   └── ...
└── catalog/
    ├── tspconfig.yaml
    ├── main.tsp
    └── ...
```

共通設定はトップレベルの `extends: ../tspconfig.base.yaml` でファイルを参照できる。YAMLアンカーは同一ファイル内の再利用に限る。Linter専用の共有には3.3の `linter.extends` を使う。

---

## 6. よくあるトラブル

| 症状 | 原因 | 対処 |
|---|---|---|
| `Cannot find emitter "@typespec/openapi3"` | パッケージ未インストール | `npm install -D @typespec/openapi3` |
| `output-dir` が想定と違う | `{output-dir}` の解決順序の誤解 | `--output-dir` CLI オプションで上書き、または絶対パス指定 |
| Linter 警告が出ない | ルール名の誤り、ライブラリ未ロード、対象コードなし | 公式Linter一覧とconfig・import・通常のcompile診断を照合する |
| `tsp format` がファイルを書き換えない | 設定でフォーマット対象外 | `**/*.tsp` 等の glob を CLI で指定 |

## 7. 公式情報

- https://typespec.io/docs/handbook/configuration/configuration/
- https://typespec.io/docs/libraries/http/reference/linter/
- https://typespec.io/docs/emitters/openapi3/reference/emitter/
