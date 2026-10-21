# Go 1.27 固有ガイド

対象: `go`ディレクティブまたは実行toolchainが1.27以上のモジュール、Go 1.27への移行、または1.27固有機能の相談。

この資料は1.27系列の機能と互換性判断を補助する。利用可能な機能を無条件に採用する一覧ではない。
同一minor系列の最新patchは公式Release Historyで確認し、現行指定または実行環境が古い場合は更新を提案する。`go`または`toolchain`ディレクティブは依頼範囲に含まれる場合だけ変更する。

最終確認日: 2026-10-21

## 適用軸

- 言語仕様とGo 1.27で追加された標準ライブラリsymbolは、`go`ディレクティブとfileのbuild constraintsが定める言語版で判断する。実行toolchainが新しいだけでは導入しない。
- toolchain、compiler、runtime、linker、既存標準ライブラリの実装変更は、古い`go`ディレクティブのモジュールをGo 1.27 toolchainでbuild・testする場合にも影響する。特に3〜6章の該当項目を確認する。
- `go mod tidy`のrequire block統合のように`go`ディレクティブを条件とするtoolchain挙動は、各項目の条件を優先する。

## 1. 言語仕様

### Generic methods

concrete methodは、receiver型の型パラメータとは別に、メソッド自身の型パラメータを宣言できる。

```go
func (list List[E]) Map[R any](transform func(E) R) List[R] {
    // ...
}
```

- 型に属する変換をpackage-level generic functionより自然に整理できる場合に使う。
- 呼び出し、method value、method expressionでは、型引数を明示または推論して具体化する。
- interface methodは型パラメータを宣言できない。
- generic concrete methodは、同じ具体化後signatureに見えてもnon-generic interface methodを実装しない。
- interface polymorphismが必要なら、non-generic adapterまたはpackage-level generic functionを検討する。
- genericsでAPIが単純になる場合に採用し、抽象化のためだけに既存APIを置き換えない。

### Struct literalのfield selector key

struct literalのkeyには、そのstruct型で有効なfield selectorを使用できる。promotedされた埋め込みfieldも直接初期化できる。

```go
type Habitat struct {
    Burrow string
}

type Gopher struct {
    Name string
    Habitat
}

gopher := Gopher{Name: "Gopher", Burrow: "Burrow #42"}
```

- 安定した自前型で簡潔になる場合に使う。
- 埋め込み先に同名fieldが追加されるとselectorが曖昧になる可能性がある。境界や所有構造を明示したい場合はnested literalを維持する。
- AST・lint・generatorは、`CompositeLit`のkeyがtop-level field nameだけとは仮定しない。

### Generic functionの型推論

generic functionをmatching function typeへ代入または変換する全contextで、型引数を推論できる。composite literal、type conversion、channel sendを含む。

```go
func format[T any](value T) string { return fmt.Sprint(value) }

type IntFormatter func(int) string

formatters := []IntFormatter{format}
converted := IntFormatter(format)
ch <- format
```

冗長な明示的instantiationは省略できるが、複数候補があり意図が不明瞭になる場合は明示してよい。

## 2. バージョン互換性

- `go 1.26`以下のモジュールへ上記構文を導入しない。新しいtoolchainを指定していても、`go`ディレクティブの言語版とは別に判断する。
- 最低Go版の引き上げは公開互換性と利用者のtoolchainへ影響するため、明示的な移行として扱う。
- `go test`は`stdversion` vet checkを既定実行し、`go`ディレクティブやfileのbuild tagより新しい標準ライブラリsymbolを検出する。診断を回避せず、最低Go版または使用APIを整合させる。
- `go.mod`の`godebug`とsourceの`//go:debug`で、削除済みの`asynctimerchan`、`tlsunsafeekm`、`tlsrsakex`、`tls3des`、`tls10server`、`x509keypairleaf`、`gotypesalias`を設定していないか確認する。削除前の旧値では`go`コマンドが失敗し、削除時点の最終既定値だけが受理される。

## 3. Toolchainと解析

- `go fix`には`atomictypes`、`embedlit`、`slicesbackward`、`unsafefuncs` modernizerがある。まずdiffを確認し、コメント、API互換性、性能特性をレビューしてから採用する。
- `go fix`の`fmtappendf` analyzerは削除され、`waitgroup`は`waitgroupgo`へ改名された。CIやscriptでanalyzer名を指定している場合は更新する。
- `go mod tidy`は`go 1.27`以上のモジュールで`require` blockをdirect / indirectの最大2つへ統合する。生成形を手編集で戻さない。
- 1.27の`gofmt`はarchitecture間でalignmentを統一したため、以前整形済みのfileにも少量の空白差分が出る場合がある。
- vetのprintf analyzerは、`E`自身が`error`を実装する場合の`*E`を`%w`でwrapする疑わしいコードを診断する。実際のdynamic error型と`errors.Is` / `errors.As`契約を確認する。
- `go doc package@version`と`go doc -ex`を、版固有APIとexecutable exampleの確認に使える。
- compilerがclosure symbol nameやcodeを共有し得るため、function code pointerの比較やclosure symbol nameへ依存しない。

### go/types・解析tool

- `go/types.Signature`ではreceiver側の型parameterを`RecvTypeParams`、generic method固有の型parameterを`TypeParams`から取得する。generic typeのgeneric methodでは両方が非nilになり得るため、片方だけを前提にしない。
- alias宣言は常に`*types.Alias`として表現される。削除された`gotypesalias`切替を前提にしない。
- 型をhash key相当に扱う場合は`go/types.Hasher`または`HasherIgnoreTags`を使い、文字列化やpointer identityで代用しない。
- parser、type checker、lint、generatorが1.27構文を扱える版か確認する。

## 4. Runtime、並行処理、診断

- timer channelは常にunbufferedかつsynchronousであり、削除された`asynctimerchan`互換modeを提案しない。
- `runtime/pprof`の`goroutineleak` profileをleak調査に利用できる。ただしreachabilityに基づく補助診断であり、leakがないことの完全な証明ではない。
- traceback headerへpprof goroutine labelが表示され得るため、labelへsecretや個人情報を入れない。
- 80 byte未満のallocation高速化はruntime / compiler側の改善である。型やコードを不自然に変形せず、最適化はbenchmarkとprofileに基づく。

## 5. 標準ライブラリと移行判断

### JSON

- `encoding/json/v2`と`encoding/json/jsontext`が正式追加された。
- v2はinvalid UTF-8とduplicate object nameを既定で拒否する。新規の厳格な入力処理では検討し、移行時はbehavior差をテストする。
- `encoding/json` v1はv2実装をbackendに使うが、公開behaviorは互換を保つ。v1からの移行を強制しない。
- error textは変わり得るため、完全一致ではなくerror contractや構造を検証する。
- `GOEXPERIMENT=nojsonv2`は一時的な診断・回避策であり、恒久設計にしない。
- 試験提供中の`GOEXPERIMENT=jsonv2`を使っていたコードでは、`inline` tagの`embed`への改名、`format`・`unknown` tag、`DiscardUnknownMembers`、`SkipFunc`の削除を確認する。`jsontext.Token`の数値accessorはerrorも返すため、呼び出し側を更新する。

### Testとnetwork

- `net/http/httptest.NewTestServer`は`testing/synctest`向けのin-memory fake networkを作れる。
- `testing/synctest.Sleep`はfake timeの進行と待機を組み合わせる。並行・時間依存testでは、実時間の`time.Sleep`や固定portより決定的な同期を優先する。
- 通常のnetwork testでも`httptest`またはOS割当portを使い、固定portを避ける。

### HTTPとsecurity

- HTTP/1 `Response.Body.Close`は未読contentを保守的な上限までdrainしてconnection reuseを改善する。bodyをcloseする責務は変わらない。
- `http.Client`と`Transport`をrequestごとに作らず、再利用する。
- serverの`MaxHeaderValueCount`で受理するheader value数を制限できる。既定値とproxy境界を確認して調整する。
- `crypto/tls.Config.Rand`はdeprecated。決定的なcrypto testでは`testing/cryptotest.SetGlobalRandom`を使う。

### その他

- 標準ライブラリの`uuid` package（import path `uuid`）をbasic UUID生成・解析の候補にする。既存third-party API、DB表現、version選択を確認せず機械的に置換しない。
- `bytes.CutLast` / `strings.CutLast`、`net/url.URL.Clone` / `Values.Clone`で手書き処理を簡潔かつ安全にできる場合がある。
- flate、gzip、zlib、zip、pngは同じ意味でもencoded bytesが変わり得る。byte列自体が契約でない限り、decode後の意味を検証する。
- Unicode tableはUnicode 17へ更新された。文字分類や正規表現のgolden差分を移行時に確認する。
- `simd`と`simd/archsimd`はexperimentalで、`GOEXPERIMENT=simd`が必要である。明示された性能要件、benchmark、対応architecture、fallbackがない限り一般解として推奨しない。

## 6. Platform

- macOSの最低対応版は13 Ventura。
- linux/ppc64はELFv2 ABIへ移行した。cgo、外部link、配布binaryでは実行環境との互換性を確認する。

## 7. 公式資料

- Release Notes: https://go.dev/doc/go1.27
- Language Specification: https://go.dev/ref/spec
- Go 1.27 announcement: https://go.dev/blog/go1.27
- Generic Methods: https://go.dev/blog/generic-methods
- Release History: https://go.dev/doc/devel/release
- Standard library: https://pkg.go.dev/std
