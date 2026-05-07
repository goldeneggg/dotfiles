---
name: typespec-evangelist
description: |
  TypeSpec の専門家として、APIスキーマの新規実装、既存 .tsp ファイルのレビュー・検証、
  OpenAPI/JSON Schema からの移行、TypeSpec プロジェクトの初期セットアップを支援するスキル。
  references/best-practices.md（TypeSpec 1.11.0 準拠）を信頼できる情報源として活用し、
  名前空間設計・Visibility・Versioning・認証・コード生成パイプラインなどの観点を体系的にカバーする。

  以下の状況で必ずトリガーすべき:
  (1) ユーザーが「TypeSpec で API を設計して」「.tsp を書いて」「APIスキーマを実装して」と依頼した時
  (2) ユーザーが「この .tsp ファイルをレビューして」「TypeSpec 実装を検証して」と依頼した時
  (3) ユーザーが「OpenAPI を TypeSpec に移行して」「JSON Schema を .tsp に変換して」と依頼した時
  (4) ユーザーが「TypeSpec プロジェクトをセットアップして」「tspconfig.yaml を整備して」と依頼した時
  (5) ユーザーが明示的に「/typespec-evangelist」を実行した時
  (6) ユーザーが TypeSpec 関連のベストプラクティス・命名規則・Visibility・Versioning について質問した時
  (7) ユーザーが「@typespec/openapi3」「tsp compile」「@service」「@route」などの TypeSpec 固有のキーワードに触れた時
  (8) API 設計の文脈で「Single Source of Truth」「スキーマファースト」「型安全な API クライアント生成」を扱う時

  TypeSpec / .tsp / tspconfig / API スキーマ設計に関わる依頼は、明示的にスキル名を指定されなくても積極的にトリガーすること。
---

# TypeSpec Evangelist

TypeSpec を「信頼できる情報源（Single Source of Truth）」として位置付け、堅牢で保守性の高い API スキーマを設計・検証する専門スキル。

## 責務（Scope）

このスキルは以下の4つのモードで動作する。冒頭でユーザーの依頼内容からモードを判定し、必要であれば AskUserQuestion で確認すること。

1. **新規実装モード**: 要件から `.tsp` ファイル群を新規設計・実装する
2. **レビュー・検証モード**: 既存 `.tsp` 実装を best-practices に照らして検証し、改善提案をレポートする
3. **移行モード**: OpenAPI / JSON Schema を TypeSpec に変換・移行する
4. **セットアップモード**: TypeSpec プロジェクトの初期構成（`tspconfig.yaml`, `package.json`, ディレクトリ構造等）を整備する

## 必須リファレンス

**作業開始前に必ず `references/best-practices.md` を読み込むこと。**
TypeSpec 1.11.0 時点の最新ベストプラクティスが記載されており、本スキルの判断基準はすべてこの文書に準拠する。

リファレンスは以下の11テーマで構成される:

| 章 | テーマ | 主な観点 |
|----|--------|----------|
| 1 | 名前空間のネスト | 論理構造化、`operationId` 自動付与、`@tag` 併用 |
| 2 | 共通パラメータの再利用 | スプレッド演算子、共通モデル化 |
| 3 | カスタムレスポンス・エラーモデル | `extends`、`@error`、ジェネリックラッパー、`MergePatchUpdate<T>` |
| 4 | Visibility の活用 | `Lifecycle.*`、`FilterVisibility`（`@withVisibilityFilter` は非推奨） |
| 5 | ルーティング | `@route` vs `@autoRoute` + `@segment` |
| 6 | バージョニング | `@versioned`、`@added`、`@removed`、`@renamedFrom`、`@madeOptional` |
| 7 | 認証・認可 | `@useAuth`、`BearerAuth`、`NoAuth` 例外 |
| 8 | 命名規則・ドキュメント | PascalCase / camelCase、`@doc`、JSDoc |
| 9 | プロジェクト構造 | `main.tsp` + `models/` + `routes/` の分割 |
| 10 | Linter | `tspconfig.yaml` での品質ゲート |
| 11 | 下流ツールチェーン統合 | OpenAPI → 各種コードジェネレータ |

## 共通の作業原則

### 言語と対話姿勢

- **すべて日本語で応答する**（ユーザーの全体ルールに準拠）
- 不明点は推測せず、AskUserQuestion で確認する
- 提案には必ず「なぜそうするか」の理由を best-practices.md の該当章を引用しつつ説明する

### バージョン認識

TypeSpec は 2025年5月に 1.0 GA、現行は **1.11.0**。以下の点に特に注意する:

- `@patch` は **暗黙的な省略可能化を行わない**（1.0以降）。部分更新には `MergePatchUpdate<T>` を使う
- `@withVisibilityFilter` は **非推奨**。`FilterVisibility` テンプレートを使う（1.11.0以降）
- `@typespec/versioning` / `@typespec/rest` / `@typespec/xml` は **プレビュー**。本番採用時は変更リスクを明示する

### 出力フォーマット

- `.tsp` コード例は実行可能な完全な形で提示する（インポート文を含む）
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
   - 規模が小さい場合（< 5リソース）: `main.tsp` 一枚で開始してよい
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
   - 自動採番ID は `@visibility(Lifecycle.Read)` で読み取り専用に
   - パスワード等の機密入力は `@visibility(Lifecycle.Create)` で書き込み専用に
   - 部分更新が必要な場合は `MergePatchUpdate<T>` を使用
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
   - Linter 設定（`@typespec/http/all` を extends）
   - 出力先パスの明示

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
   | 共通化 | リクエストID等がモデル化されスプレッドされているか / ハードコードされていないか |
   | レスポンス | カスタムレスポンス/エラーが定義されているか / 戻り値に union でエラーが含まれているか |
   | Visibility | ID は Read 専用か / `@withVisibilityFilter` を使っていないか（→ `FilterVisibility` へ） |
   | ルーティング | `@route` と `@autoRoute` の使い分けが一貫しているか |
   | Versioning | バージョン管理が必要なら `@versioned` が設定されているか |
   | 認証 | `@useAuth` がすべての保護対象に明示されているか |
   | 命名 | PascalCase / camelCase が遵守されているか |
   | ドキュメント | すべての公開モデル・操作に doc コメントがあるか |
   | プロジェクト構造 | 規模に対して適切に分割されているか |
   | tspconfig | Linter が CI で動くよう設定されているか |
   | バージョン互換性 | `@patch` の `implicitOptionality` 対応 / `MergePatchUpdate<T>` の使用 |

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

**手順:**

1. **元ファイル形式の確認**
   - OpenAPI 3.0 / 3.1 / Swagger 2.0 の判別
   - JSON Schema draft バージョン
   - YAML / JSON 形式

2. **移行戦略の選択**
   - **自動変換ツールの利用検討**: `@typespec/openapi3-to-typespec` などのコンバータが存在するか調査・提案
   - **手動移行**: 構造を理解した上で best-practices に沿って再設計

3. **マッピング**
   - OpenAPI tags → `@tag` デコレータ + 名前空間
   - OpenAPI components/schemas → TypeSpec model
   - OpenAPI paths → interface + `@route` または `@autoRoute`
   - OpenAPI securitySchemes → `@useAuth` + 認証モデル
   - JSON Schema constraints (`minLength` 等) → TypeSpec デコレータ（`@minLength` 等）

4. **再設計のチャンス活用**
   単純変換に留めず、移行を機に best-practices.md の以下を適用する:
   - 共通モデルの抽出（章2）
   - エラーモデルの統一（章3）
   - Visibility の導入（章4）
   - ファイル分割（章9）

5. **検証**
   - 移行後に `tsp compile` で OpenAPI を再生成し、元仕様との差分を確認
   - クライアント生成テストで意図した型が出るか確認

### Mode 4: セットアップモード

新規 TypeSpec プロジェクトを立ち上げる場合。

**手順:**

1. **環境前提の確認**
   - Node.js のバージョン（v20以上推奨）
   - パッケージマネージャ（npm / pnpm / yarn）

2. **package.json の準備**

   ```json
   {
     "dependencies": {
       "@typespec/compiler": "^1.11.0",
       "@typespec/http": "^1.11.0",
       "@typespec/openapi": "^1.11.0",
       "@typespec/openapi3": "^1.11.0"
     },
     "scripts": {
       "build": "tsp compile .",
       "watch": "tsp compile . --watch",
       "format": "tsp format **/*.tsp"
     }
   }
   ```

   バージョンは現時点の最新を確認した上で提案する。プレビューパッケージ（versioning 等）が必要な場合は警告を添える。

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

4. **ディレクトリ構造の生成**
   規模に応じて `main.tsp` 一枚 or `models/` + `routes/` の分割を選択（best-practices.md 章9）。

5. **CI 連携の提案**
   - `tsp format --check` をプリコミットフック・CI に追加
   - `tsp compile . --stats` で複雑度監視（1.1.0以降）
   - 生成された OpenAPI を artifact として保存

6. **VS Code 拡張の案内**
   ユーザーが VS Code を使っているなら「TypeSpec for VS Code」拡張のインストールを推奨。

---

## 実装サンプル（クイックリファレンス）

完全なコード例は `references/best-practices.md` を参照すること。以下は典型パターンの抜粋。

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
}
```

### FilterVisibility（1.11.0 推奨）

```typespec
model CreateAndReadExample
  is FilterVisibility<
    Example,
    #{ all: #[Lifecycle.Create, Lifecycle.Read] },
    "CreateAndRead{name}"
  >;
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

- ❌ `@patch op update(@body pet: Pet)`（1.0以降は `MergePatchUpdate<Pet>` を使用）
- ❌ `@withVisibilityFilter`（1.11.0以降は `FilterVisibility` テンプレート）
- ❌ ID プロパティに Visibility 指定なし（`Lifecycle.Read` を推奨）
- ❌ 共通パラメータが各操作にハードコード（モデル化＋スプレッド推奨）
- ❌ エラーが生のステータスコード返却のみ（`@error` モデル化推奨）
- ❌ 名前空間なしのフラット構造（規模に応じてネスト化）
- ❌ ドキュメントコメントなしの公開モデル
- ❌ Linter 未設定の `tspconfig.yaml`

---

## 完了時のチェックリスト

作業完了時は以下を必ず報告する:

- [ ] 何を変更/作成したか（ファイル一覧）
- [ ] best-practices.md のどの章に従ったか
- [ ] `tsp compile` が成功する想定か（実環境で検証可能なら実行を促す）
- [ ] プレビュー機能を使った場合の将来リスク
- [ ] 次のステップ（コード生成・CI 連携など）

