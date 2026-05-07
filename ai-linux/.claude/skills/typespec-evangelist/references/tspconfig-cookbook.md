# tspconfig.yaml クックブック

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

---

## 3. Linter 設定の選び方

`@typespec/http` には複数のルールセットが用意されている。現場運用では「厳格度」と「ノイズ量」のトレードオフを踏まえて選択する。

| ルールセット | 想定運用 | 特徴 |
|---|---|---|
| `@typespec/http/all` | 新規プロジェクト・厳しめの規約を敷きたい場合 | 全ルール有効。指摘数は多いが、ベストプラクティス徹底に最適 |
| `@typespec/http/recommended` | 既存プロジェクトの段階導入 | 重要ルールに絞られる。CI 通過率が現実的 |

選択指針:
- 新規開発で white-box から書く場合は `all` から始め、不要ルールを `disable` で除く方が後悔しにくい。
- 既存大型プロジェクトに後付けする場合は `recommended` から導入し、段階的に強化する。

### 3.1 個別ルールの上書き

```yaml
linter:
  extends:
    - "@typespec/http/all"
  disable:
    "@typespec/http/op-reference-container-route": "プロジェクト固有のルーティング戦略のため除外"
  enable:
    "@typespec/http/no-unused-routes": true
```

`disable` には必ず除外理由を文字列で添える。後続のメンテナーが判断しやすい。

### 3.2 カスタムルールセットの拡張

組織独自のガイドライン（例: `displayName` フィールド必須化）は、社内パッケージとして Linter プラグインを公開し `extends` で読み込ませると複数リポジトリで再利用できる。

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

共通設定を抽出したい場合、YAML アンカー機能か、組織共通の base config を npm パッケージとして配り `extends` させる運用が現実的。

---

## 6. よくあるトラブル

| 症状 | 原因 | 対処 |
|---|---|---|
| `Cannot find emitter "@typespec/openapi3"` | パッケージ未インストール | `npm install -D @typespec/openapi3` |
| `output-dir` が想定と違う | `{output-dir}` の解決順序の誤解 | `--output-dir` CLI オプションで上書き、または絶対パス指定 |
| Linter 警告が出ない | `extends` のパッケージ名タイポ | `npx tsp compile . --diagnostics-level verbose` で確認 |
| `tsp format` がファイルを書き換えない | 設定でフォーマット対象外 | `**/*.tsp` 等の glob を CLI で指定 |
