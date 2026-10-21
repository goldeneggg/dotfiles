# 言語仕様の更新と互換性

確認日: 2026-10-21。確認版: `@typespec/compiler` 1.17.0。
ここでの導入版は機能を選ぶための下限であり、実プロジェクトの対応保証ではない。対象版の公式仕様とローカルCLIで再確認する。

## 1. 更新時の確認手順

1. package.json、lockfile、ローカルCLIで実際の版を特定する。npmの`latest`とインストール済みの版を混同しない。
2. 採用版までの公式リリースノートを読み、言語の意味、非推奨構文、生成結果の変更を分けて確認する。
3. `npm view <package> version engines peerDependencies --json` で採用候補の対応条件を確認する。既存環境を無断で最新版へ更新しない。
4. プロジェクトで使うCLIの `tsp info features` でfeature flagを確認し、必要な機能だけ有効にする。
5. 最小例をcompileし、OpenAPI・JSON Schemaの構造や下流の契約も確認する。コンパイル成功だけで意味の互換性を判断しない。

## 2. 安定機能と互換性に関わる変更

| 導入版 | 変更 | 適用時の判断 |
|---|---|---|
| 1.13 | `internal` が安定化 | ライブラリ実装用の宣言に使う。HTTP認可や生成仕様の非公開化の代わりにはしない |
| 1.14 | booleanへの `@encode(string)` | wire上の文字列化が必要な契約に使用する。任意の文字列ではなく、大文字小文字を区別しないtrue/falseの表現 |
| 1.14 | `.tsp` から `.ts` のデコレータ実装を直接import可能 | 実行環境と配布形態も確認する。既存ライブラリのビルド方法を一律変更しない |
| 1.15 | ファイル名前空間の前にある `using` の名前解決が変更 | 相対名に依存していた場合、完全修飾名へ直す |
| 1.15 | 診断・Linterルールの短縮名とライブラリalias | 対象ライブラリのロードが必要。短縮名が衝突する場合は完全名を使う |
| 1.16 | `file:` で共有Linterルールセットを参照 | 詳細は `tspconfig-cookbook.md`。各ファイルからの相対パスで解決する |

### `using` の解決（1.15の破壊的変更）

```typespec
import "@typespec/http";

using TypeSpec.Http;
namespace MyOrg.Service;

@route("/health")
@get
op health(): string;
```

ファイルレベルの `namespace MyOrg.Service;` より前の `using` はグローバルから解決する。
名前空間の後、または名前空間ブロック内の `using` は従来どおり相対名を解決する。宣言位置を機械的に移動すると意味が変わる場合がある。

## 3. 実験的な言語機能

compilerが安定版でも、以下の機能は1.17.0時点で実験的。feature flagによって利用可能・警告なしになっても、安定化を意味しない。
`features` はそのプロジェクトに属するソースへ適用される。ライブラリが自分の機能を有効化する場合は、ライブラリ側のtspconfigで宣言し、利用者へ一律に有効化を求めない。

### Functions（1.10〜、`function-declarations`）

`extern fn` は型や値を計算して返す。JavaScript実装を伴い、テンプレートやデコレータとは別の拡張手段である。
型と値を区別し、値の引数・戻り値には `valueof` を使う。副作用や高コスト処理はコンパイラ・言語サーバーに影響するため避ける。

```typespec
import "./functions.js";

extern fn defaultLabel(): valueof string;

model Settings {
  label: string = defaultLabel();
}
```

```javascript
// functions.js
export const $functions = {
  "": {
    defaultLabel: () => "default",
  },
};
```

実装は `$functions` の名前空間・関数名と宣言を対応させる。`valueof string` の戻り値にはJavaScriptの文字列を返す。型を返す関数とは受け渡し方法を区別する。

### Auto decorators（1.14〜、`auto-decorators`）

メタデータの保存だけを行うデコレータは `auto dec` で宣言でき、JavaScript実装は不要。
検証や計算が必要な場合は通常の `extern dec` を選ぶ。`auto` と `extern` は併用しない。

```typespec
using TypeSpec.Reflection;

auto dec label(target: Model, value: valueof string);

@label("widget")
model Widget {
  name: string;
}
```

メタデータは `hasAutoDecorator`、`getAutoDecoratorValue`、`getAutoDecoratorTargets` などで取得する。
任意のauto decoratorがOpenAPIの項目へ自動変換されるわけではなく、読み取るemitter・ツールが必要。

### Union extends（1.16〜、`union-extends`）

```typespec
model PetBase {
  name: string;
}

model Cat extends PetBase {
  toy: string;
}

model Dog extends PetBase {
  food: string;
}

union Pet extends PetBase {
  cat: Cat,
  dog: Dog,
}
```

全variantが基底型に代入可能であることを制約する。union自体のサブタイプ関係、拡張可能性、`@discriminator` の動作を追加する機能ではない。

### 宣言式（1.17〜、`declaration-expressions`）

```typespec
model Envelope {
  state: enum { active, inactive };
  unit: scalar extends string;
  inner: model Inner {
    value: string;
  };
}
```

`model`・`enum`・`union`・`scalar` 宣言を、プロパティ型、alias、デコレータやテンプレートの引数など式の位置に記述できる。デコレータ・docコメントも付与できる。
従来の `{ ... }` や `A | B` の式と、宣言キーワードを使う宣言式は区別する。
OpenAPI・JSON Schema emitterでは匿名宣言をinline化し、名前付き宣言を再利用可能なschema/componentへ出力する。生成名や参照の変化を確認する。

### IDE向け型情報（1.16〜、`type-info-provider`）

ライブラリ作者向けの `$provideTypeInfo` はhover等で遅延評価され、通常のcompileでは呼ばれない。
型グラフを変更せず、検証処理は `$onValidate` に置く。通常のAPI定義に必須の設定ではない。

## 4. Emitter側の変更も確認する

- 1.14: OpenAPI 3.1以上で `enum-strategy: annotated` を選べる。enumメンバーのdoc・summaryを `oneOf` / `const` に保持する。3.0では警告と従来形式への切り替えがある。
- 1.14: OpenAPI 3.1/3.2では `$ref` にdescription等を隣接でき、不要な `allOf` ラッパーがなくなる。意味と単純なテキスト差分を区別する。
- 1.16: spec由来の出力パス要素がサニタイズされる。バージョン名等にパス区切りを埋め込む運用に依存しない。
- 1.17: OpenAPI 3.1/3.2の `Record<T>` indexerは `additionalProperties` を出力する。継承モデルや封鎖されたモデルは引き続き `unevaluatedProperties` を使う。

OpenAPI仕様の版、サービスのAPI版、TypeSpecパッケージの版は別物として扱う。

## 5. 公式情報

- https://typespec.io/release-notes/typespec-1-14-0/
- https://typespec.io/release-notes/typespec-1-15-0/
- https://typespec.io/release-notes/typespec-1-16-0/
- https://typespec.io/release-notes/typespec-1-17-0/
- https://typespec.io/docs/language-basics/functions/
- https://typespec.io/docs/extending-typespec/implement-functions/
- https://typespec.io/docs/extending-typespec/create-decorators/
- https://typespec.io/docs/handbook/configuration/configuration/
- https://typespec.io/docs/emitters/openapi3/reference/emitter/
