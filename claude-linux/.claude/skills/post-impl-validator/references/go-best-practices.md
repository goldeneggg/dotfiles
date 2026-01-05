# Go ベストプラクティス

## はじめに
この指示ファイルは、AIコーディング支援ツールがGo言語のコードをレビューし、ベストプラクティスに沿った修正案を提示するためのガイドラインです。各項目には、レビューの観点、修正を推奨する理由の例、そして具体的な修正前後のコード例を含んでいます。

## 対象Goバージョン

1.24以上

---

## 1. 命名規則 (Naming Conventions)

### 概要
Go言語のコードは、一貫性があり、意図が明確に伝わる命名規則に従うべきです。これにより、コードの可読性と保守性が向上します。

### レビュー観点
- パッケージ名が短く、小文字で、内容を表しているか。
- エクスポートされる識別子 (変数、定数、関数、型、メソッド) が大文字で始まっているか。
- エクスポートされない識別子が小文字で始まっているか。
- `mixedCaps` (ローワーキャメルケース) または `MixedCaps` (アッパーキャメルケース) が適切に使用されているか (アンダースコアは通常避ける)。
  - ただし、structのフィールドに `json:` などのタグを設定する場合の項目名については `snake_case` 形式で統一されているか
- 変数名や関数名が、その役割や動作を的確に表しているか。
- 略語を使用する場合、一貫性があり、一般的に理解されるものか (例: `HTTP`, `URL` は大文字)。
- インターフェース名は、メソッドセットを表す場合 `-er` で終わることが多い (例: `Reader`, `Writer`)。
- Goのキーワードや予約語と衝突していないか。

### 修正すべき理由の例
- **理由1:** エクスポートされるべき関数名が小文字で始まっているため、他のパッケージから利用できません。
- **理由2:** 変数名が曖昧で、その変数が何を表しているのか理解しにくいです。
- **理由3:** パッケージ名が一般的すぎ、他の標準パッケージや有名なサードパーティパッケージと混同する可能性があります。

### 修正例

#### 例1: エクスポートされる関数名
    ```go
    // Before
    package mypkg

    func calculateValue() int {
        // ...
        return 0
    }
    ```

    ```go
    // After
    package mypkg

    // CalculateValue は値を計算します。
    func CalculateValue() int { // 関数名を大文字に変更
        // ...
        return 0
    }
    ```

#### 例2: 曖昧な変数名
    ```go
    // Before
    func processData(d []string) {
        for _, val := range d {
            // ... valを使った処理 ...
        }
    }
    ```

    ```go
    // After
    func processData(lines []string) { // 変数名をより具体的に変更
        for _, line := range lines { // ループ変数名も具体的に
            // ... lineを使った処理 ...
        }
    }
    ```

---

## 2. エラーハンドリング (Error Handling)

### 概要
Go言語では、エラーは値として扱われ、明示的に処理されるべきです。適切なエラーハンドリングは、プログラムの堅牢性とデバッグの容易性を高めます。

### レビュー観点
- 関数がエラーを返す可能性がある場合、最後の戻り値として `error` 型を返しているか。
- エラーが無視されていないか (例: `_` への代入)。
- エラーを受け取った後、適切にチェックし、処理しているか。
- エラーをラップしてコンテキスト情報を追加しているか (Go 1.13以降の `%w` 、`fmt.Errorf`、`errors.Is`、`errors.As` の適切な使用)。
- エラーメッセージが明確で、問題の原因特定に役立つ情報を含んでいるか。
- `panic` の使用が、真に回復不可能な状況に限定されているか。
- `defer` を使ったリソース解放処理で発生したエラーが適切に処理されているか。
- `log.Fatalf`, `log.Fatalln` ではなく、代わりに `log.Panicf`, `log.Panicln` が使用されているか。
  - `log.Fatalf`, `log.Fatalln` はdeferブロックが実行されないため、非推奨

### 修正すべき理由の例
- **理由1:** 関数呼び出しで返されたエラーがチェックされておらず、潜在的な問題を見逃す可能性があります。
- **理由2:** エラーメッセージに具体的なコンテキストが含まれていないため、エラーの原因特定が困難です。
- **理由3:** エラーをラップせずに新たなエラーを返しているため、元のエラー情報が失われています。

### 修正例

#### 例1: エラーの無視
    ```go
    // Before
    func writeToFile(filename string, data []byte) {
        os.WriteFile(filename, data, 0644) // エラーを無視
    }
    ```

    ```go
    // After
    func writeToFile(filename string, data []byte) error {
        err := os.WriteFile(filename, data, 0644)
        if err != nil {
            return fmt.Errorf("writeToFile: ファイル '%s' への書き込みに失敗しました: %w", filename, err) // エラーをラップして返す
        }
        return nil
    }
    ```

#### 例2: エラーのラップ
    ```go
    // Before
    func queryDatabase() error {
        _, err := db.Query("SELECT * FROM users")
        if err != nil {
            return errors.New("データベースクエリ失敗") // 元のエラー情報が欠落
        }
        return nil
    }
    ```

    ```go
    // After
    func queryDatabase() error {
        _, err := db.Query("SELECT * FROM users")
        if err != nil {
            return fmt.Errorf("データベースクエリ失敗: %w", err) // %w を使ってエラーをラップ
        }
        return nil
    }
    ```

---

## 3. コードのフォーマット (Code Formatting)

### 概要
Go言語の標準フォーマッタである `gofmt` (または `goimports`) を使用し、一貫性のあるコードスタイルを維持します。

### レビュー観点
- コードが `gofmt` または `goimports` によってフォーマットされているか。
- インデント、スペース、括弧の位置などが標準スタイルに従っているか。
- import文が `goimports` によって整理されているか (標準パッケージ、サードパーティパッケージの順など)。

### 修正すべき理由の例
- **理由1:** コードのインデントが統一されておらず、可読性が低いです。`gofmt` を実行してください。
- **理由2:** import文が整理されていません。`goimports` を実行して、標準的な順序に並べ替えてください。

### 修正例
(修正例はフォーマッタの実行結果となるため、ここでは省略します。AIは `gofmt` や `goimports` の実行を促すコメントを生成します。)

    AIコメント例: "このファイルのフォーマットがGoの標準スタイルに準拠していません。`gofmt -w <ファイル名>` を実行してフォーマットを修正してください。"

---

## 4. コメント (Comments)

### 概要
コメントは、コードの意図、複雑なロジック、または重要な決定事項を説明するために使用されます。Godocコメントは、エクスポートされるAPIのドキュメントを生成するために不可欠です。

### レビュー観点
- エクスポートされるパッケージ、関数、型、変数、定数にGodoc形式のコメントが付与されているか。
  - 且つ、Godoc形式のコメントに限り言語は全て英語で統一されているか
- コメントがコードの動作ではなく「なぜ」そうなっているのかを説明しているか。
- 不要なコメント (自明な処理を説明するコメントなど) や古いコメントが残っていないか。
- 複雑なアルゴリズムやトリッキーなコード部分に説明コメントがあるか。
- TODOコメントには、対応すべき内容と、可能であれば担当者や期日が記載されているか。
- コメントが簡潔かつ明確か。

### 修正すべき理由の例
- **理由1:** エクスポートされる関数にGodocコメントがないため、APIの利用者が関数の目的や使用方法を理解しにくいです。
- **理由2:** このコードブロックのロジックが複雑であるにも関わらず、説明コメントがありません。
- **理由3:** コメントが現在のコードの実装と一致しておらず、誤解を招く可能性があります。

### 修正例

#### 例1: Godocコメント
    ```go
    // Before
    func Add(a, b int) int {
        return a + b
    }
    ```

    ```go
    // After
    // Add adds two integers and returns the result.
    func Add(a, b int) int {
        return a + b
    }
    ```

#### 例2: 複雑なロジックへのコメント
    ```go
    // Before
    func complexCalculation(data []int) int {
        // ... 多くのステップからなる複雑な計算 ...
        result := 0
        for i := 0; i < len(data); i++ {
            if data[i]%2 == 0 {
                result += data[i] * (i + 1) // 謎の重み付け
            } else {
                result -= data[i]
            }
        }
        return result
    }
    ```

    ```go
    // After
    func complexCalculation(data []int) int {
        // この関数は、特定のビジネスルールに基づいてスコアを計算します。
        // 偶数の要素にはインデックスに応じた重みを乗算し、奇数の要素は減算します。
        result := 0
        for i := 0; i < len(data); i++ {
            if data[i]%2 == 0 {
                // 偶数の場合: 要素の値に (インデックス + 1) を乗算して加算
                result += data[i] * (i + 1)
            } else {
                // 奇数の場合: 要素の値を減算
                result -= data[i]
            }
        }
        return result
    }
    ```

---

## 5. 関数の設計 (Function Design)

### 概要
関数は短く、単一の責務を持ち、明確なインターフェースを持つべきです。これにより、テスト、理解、再利用が容易になります。

### レビュー観点
- 関数が一つの明確なタスクを実行しているか (単一責任の原則)。
- 関数名がその処理内容を正確に反映しているか。
- 関数の行数が適切か (長すぎる場合は分割を検討)。
- 引数の数が適切か (目安として3つ程度まで、多い場合は構造体やオプションパターンを検討)。
- ポインタレシーバと値レシーバの使い分けが適切か。
- 名前付き戻り値が適切に使用されているか (多用しすぎると可読性が低下する場合がある)。
- 副作用がある場合、それが明確にドキュメント化されているか、または関数名から推測できるか。
- グローバル変数の変更を極力避けているか。

### 修正すべき理由の例
- **理由1:** この関数は複数の異なる責務を担っており、単一責任の原則に反しています。分割を検討してください。
- **理由2:** 関数の引数が多すぎます。引数を構造体にまとめるか、オプションパターンを検討してください。
- **理由3:** この関数の名前 (`handleData`) が処理内容を具体的に表していません。より説明的な名前に変更してください。

### 修正例

#### 例1: 長すぎる関数、複数の責務
    ```go
    // Before
    func processOrder(orderID string, customerID string, items []string, paymentType string) error {
        // 1. 注文情報をデータベースから取得
        // 2. 在庫を確認・引き当て
        // 3. 支払い処理を実行
        // 4. 注文ステータスを更新
        // 5. 顧客に通知メールを送信
        // ... 長大な処理 ...
        return nil
    }
    ```

    ```go
    // After
    // processOrder は注文処理の主要な流れを制御します。
    func processOrder(orderID string, customerID string, items []string, paymentType string) error {
        order, err := fetchOrderDetails(orderID)
        if err != nil {
            return fmt.Errorf("注文詳細の取得に失敗: %w", err)
        }

        if err := checkAndUpdateInventory(items); err != nil {
            return fmt.Errorf("在庫処理に失敗: %w", err)
        }

        if err := processPayment(order, paymentType); err != nil {
            return fmt.Errorf("支払い処理に失敗: %w", err)
        }

        if err := updateOrderStatus(orderID, "processed"); err != nil {
            return fmt.Errorf("注文ステータス更新に失敗: %w", err)
        }

        if err := sendOrderConfirmationEmail(customerID, order); err != nil {
            // メール送信失敗は致命的ではない場合、ログに記録するなどの対応も検討
            log.Printf("顧客 %s への注文確認メール送信に失敗: %v", customerID, err)
        }
        return nil
    }

    // (fetchOrderDetails, checkAndUpdateInventory, processPayment, updateOrderStatus, sendOrderConfirmationEmail は別途定義)
    ```

---

## 6. 並行処理 (Concurrency)

### 概要
Goの強力な機能であるgoroutineとchannelは、正しく使用しないと競合状態、デッドロック、goroutineリークなどの問題を引き起こす可能性があります。

### レビュー観点
- goroutineの起動と終了が適切に管理されているか (`sync.WaitGroup` の使用など)。
- channelのバッファサイズが適切に設定されているか、または非バッファチャネルが意図通りに使われているか。
- channelの送信側と受信側のどちらがchannelをクローズするかの規約が守られているか (通常は送信側)。
- `select` 文がタイムアウトやキャンセル処理 (`context` パッケージ) を考慮しているか。
- 共有リソースへのアクセスが `sync.Mutex` や `sync.RWMutex` などで適切に保護されているか。
- `go test -race` を実行し、競合状態がないことを確認しているか (またはその推奨)。
- デッドロックが発生する可能性のあるパターンがないか。
- goroutineが意図せずリークする可能性がないか。

### 修正すべき理由の例
- **理由1:** `sync.WaitGroup` を使用せずに複数のgoroutineを起動しており、全てのgoroutineの完了を待たずに処理が続行されるため、意図しない動作をする可能性があります。
- **理由2:** 複数のgoroutineからマップへの書き込みアクセスが保護されておらず、競合状態が発生する可能性があります。`sync.Mutex` で保護してください。
- **理由3:** channelのクローズ処理が受信側で行われており、送信側がクローズされたchannelに送信しようとしてパニックが発生する可能性があります。

### 修正例

#### 例1: WaitGroupなしでのgoroutine起動
    ```go
    // Before
    func processTasks(tasks []func()) {
        for _, task := range tasks {
            go task() // WaitGroupなしでgoroutineを起動
        }
        // ここで全てのタスクが完了している保証はない
    }
    ```

    ```go
    // After
    func processTasks(tasks []func()) {
        var wg sync.WaitGroup
        for _, task := range tasks {
            wg.Add(1)
            go func(t func()) {
                defer wg.Done()
                t()
            }(task)
        }
        wg.Wait() // 全てのgoroutineの完了を待つ
    }
    ```

#### 例2: マップへの競合アクセス
    ```go
    // Before
    func countWords(words []string) map[string]int {
        counts := make(map[string]int)
        for _, word := range words {
            go func(w string) {
                counts[w]++ // 競合状態が発生する可能性
            }(word)
        }
        // 結果が不正確になる可能性がある
        time.Sleep(100 * time.Millisecond) // 不確実な待機
        return counts
    }
    ```

    ```go
    // After
    func countWords(words []string) map[string]int {
        counts := make(map[string]int)
        var mu sync.Mutex
        var wg sync.WaitGroup

        for _, word := range words {
            wg.Add(1)
            go func(w string) {
                defer wg.Done()
                mu.Lock()
                counts[w]++
                mu.Unlock()
            }(word)
        }
        wg.Wait()
        return counts
    }
    ```

---

## 7. テスト (Testing)

### 概要
Goは強力な標準テストライブラリを提供しています。効果的なテストは、コードの品質と信頼性を保証し、リファクタリングを容易にします。

### レビュー観点
- `TestXxx` という命名規則に従ったテスト関数が記述されているか。
- テストパターンをテーブル駆動テストを活用して網羅出来ているか。
- テストケースが、正常系だけでなく、エラーケースや境界値もカバーしているか。
- 各テストが独立しており、他のテストの結果に影響を与えないか。
- テスト関数と各テストパターンを `t.Parallel()` を適切に使用して並列化し、実行時間を短縮しているか。
- ヘルパー関数 (`t.Helper()`) が適切に使用されているか。
- テストカバレッジが適切に確保されているか (`go test -cover` の活用を推奨)。
- モックやスタブが適切に使用され、外部依存性を排除しているか。
- ベンチマークテスト (`BenchmarkXxx`) が必要な箇所に記述されているか。

### 修正すべき理由の例
- **理由1:** テストケースが正常系のみを対象としており、エラー処理や境界値の振る舞いが未検証です。
- **理由2:** 複数のテストケースで類似のロジックが繰り返されています。テーブル駆動テストを導入して可読性と保守性を向上させてください。
- **理由3:** このテストは外部APIに依存しており、ネットワーク状態によって結果が不安定になる可能性があります。モックを使用してください。

### 修正例

#### 例1: テーブル駆動テストの導入
    ```go
    // Before
    func TestAdd(t *testing.T) {
        if Add(1, 2) != 3 {
            t.Error("Add(1, 2) should be 3")
        }
        if Add(-1, -1) != -2 {
            t.Error("Add(-1, -1) should be -2")
        }
        if Add(0, 0) != 0 {
            t.Error("Add(0, 0) should be 0")
        }
    }
    ```

    ```go
    // After
    func TestAdd(t *testing.T) {
        testCases := []struct {
            name string
            a, b int
            want int
        }{
            {"positive numbers", 1, 2, 3},
            {"negative numbers", -1, -1, -2},
            {"zero values", 0, 0, 0},
            {"mixed values", -5, 10, 5},
        }

        for _, tc := range testCases {
            t.Run(tc.name, func(t *testing.T) {
                got := Add(tc.a, tc.b)
                if got != tc.want {
                    t.Errorf("Add(%d, %d) = %d; want %d", tc.a, tc.b, got, tc.want)
                }
            })
        }
    }
    ```

### ※補足: biz リポジトリ固有の情報
- ${pkg_name} というpackageに ${filename}.go というファイルで機能を追加した場合は、同じディレクトリ下に `${pkg_name}_test` というpackageで `${filename}_test.go` というファイルにテストを実装する
  - 全テストで共通する事前処理・事後処理は、 testing.M と TestMain 関数を使って main_test.go というファイルに集約実装し、`${pkg_name}_test` package内に唯一つだけ存在することを保証する
- テストパターンはtable-driven tests形式で網羅する
- テスト関数と各テストパターンは `t.Parallel()` を使って並列化する
- インターネットにアクセスするテストは極力控えて、必要ならテストサーバーを起動して代替する
  - 外部APIやクラウドサービスへのアクセスも、極力モックする
- ポート番号を指定・使用する実装を行う場合、`3000` や `8080` など他アプリケーションと競合する可能性が高い番号は避けて、`13000` や `28080` のように +10000, +20000 した競合可能性が低いポート番号を使用する
- `go test` 実行時は `-shuffle on -race -cover` オプションを付けて実行し、テストの順序をランダム化し、競合状態を検出し、カバレッジを確認する

---

## 8. パッケージ構成と依存関係 (Package Organization and Dependencies)

### 概要
適切に設計されたパッケージは、コードのモジュール性、再利用性、保守性を向上させます。Go Modulesは依存関係管理の標準的な方法です。

### レビュー観点
- パッケージが単一の目的や関連する機能セットに焦点を当てているか。
- パッケージ間の依存関係が明確で、循環依存がないか。
- `internal` パッケージが適切に使用され、意図しない外部利用を防いでいるか。
- `go.mod` ファイルが適切に管理され、依存ライブラリのバージョンが指定されているか。
- 未使用の依存関係が `go.mod` に残っていないか (`go mod tidy` の実行推奨)。
- 巨大なパッケージ (god package) になっていないか。適切な粒度で分割されているか。

### 修正すべき理由の例
- **理由1:** このパッケージは複数の無関係な機能を含んでおり、凝集度が低いです。責務に基づいてパッケージを分割してください。
- **理由2:** パッケージAとパッケージBの間で循環依存が発生しており、ビルドできません。依存関係を見直してください。
- **理由3:** `go.mod` に記載されているいくつかの依存ライブラリは、プロジェクト内で実際には使用されていません。`go mod tidy` を実行して整理してください。

### 修正例
(パッケージ構成の修正はコードスニペットだけでは示しにくいため、AIは具体的なアドバイスや設計指針を提示します。)

    AIコメント例: "パッケージ `utils` が多くの異なる種類のヘルパー関数を含んでおり、責務が広範すぎます。例えば、文字列操作に関する関数は `stringutils` パッケージ、ファイル操作に関する関数は `fileutils` パッケージのように、より具体的なパッケージに分割することを検討してください。"

---

## 9. パフォーマンス (Performance)

### 概要
Goはパフォーマンスの高い言語ですが、非効率なコードは依然としてボトルネックとなり得ます。一般的なパフォーマンスアンチパターンを避けることが重要です。

### レビュー観点
- ループ内での不要なメモリアロケーション (例: `append` の事前キャパシティ指定不足、ループごとのスライスやマップの再作成)。
- 文字列結合の効率 (多数の文字列を結合する場合、`+`演算子ではなく `strings.Builder` や `bytes.Buffer` を使用しているか)。
- `defer` の使用がパフォーマンスに影響を与える箇所 (頻繁に呼び出されるループ内など) でないか。
- channelの不必要なブロッキングや過度なバッファリング。
- 不必要なポインタの間接参照。
- `sync.Mutex` のロック範囲が広すぎないか、または細かすぎないか。
- `pprof` ツールを使用したプロファイリングが推奨される箇所がないか。

### 修正すべき理由の例
- **理由1:** ループ内で `append` を繰り返し呼び出しており、スライスの再割り当てが頻繁に発生するため非効率です。事前にスライスのキャパシティを確保するか、`make` で適切なサイズを指定してください。
- **理由2:** 大量の文字列を `+` 演算子で結合しており、パフォーマンスが低下します。`strings.Builder` の使用を検討してください。
- **理由3:** 頻繁に呼び出されるこのループ内で `defer` を使用すると、リソース解放が遅延し、パフォーマンスに影響を与える可能性があります。

### 修正例

#### 例1: ループ内での効率の悪い `append`
    ```go
    // Before
    func buildStringList(n int) []string {
        var result []string // キャパシティ指定なし
        for i := 0; i < n; i++ {
            result = append(result, fmt.Sprintf("item-%d", i)) // 頻繁な再割り当て
        }
        return result
    }
    ```

    ```go
    // After
    func buildStringList(n int) []string {
        result := make([]string, 0, n) // 事前にキャパシティを指定
        for i := 0; i < n; i++ {
            result = append(result, fmt.Sprintf("item-%d", i))
        }
        return result
    }
    ```

#### 例2: 効率の悪い文字列結合
    ```go
    // Before
    func concatenateStrings(parts []string) string {
        var s string
        for _, part := range parts {
            s += part // ループ内で + 演算子による文字列結合
        }
        return s
    }
    ```

    ```go
    // After
    func concatenateStrings(parts []string) string {
        var sb strings.Builder
        // おおよその最終的な文字列長がわかる場合は、Growでバッファを確保するとさらに効率的
        // totalLen := 0
        // for _, part := range parts {
        //    totalLen += len(part)
        // }
        // sb.Grow(totalLen)

        for _, part := range parts {
            sb.WriteString(part) // strings.Builder を使用
        }
        return sb.String()
    }
    ```

---

## 10. セキュリティ (Security)

### 概要
安全でないコードは、脆弱性を引き起こし、悪意のある攻撃を可能にする可能性があります。一般的なセキュリティのベストプラクティスに従うことが重要です。

### レビュー観点
- ユーザーからの入力値を検証・サニタイズしているか (SQLインジェクション、XSS、コマンドインジェクション対策)。
- 安全でない標準ライブラリ関数の使用 (例: `os/exec` で外部入力を直接コマンドとして実行)。
- ハードコードされた認証情報 (APIキー、パスワードなど) がないか。
- `math/rand` をセキュリティが重要な乱数生成に使用していないか (`crypto/rand` を使用すべき)。
- エラーメッセージが内部情報を過度に漏洩していないか。
- ファイルパスの操作において、パストラバーサルの脆弱性がないか。
- `html/template` や `text/template` を使用する際に、適切にエスケープ処理が行われているか。
- `gosec` ツールを使用して、セキュリティ上の問題が検知されないことを確認しているか。
  - ただし、テスト用のダミーな値など明らかに問題が無い箇所についてのみ `// #nosec ${エラーコード}` 形式の検知除外用コメントの使用を許可する

### 修正すべき理由の例
- **理由1:** ユーザー入力を検証せずにSQLクエリに直接埋め込んでおり、SQLインジェクションの脆弱性があります。
- **理由2:** APIキーがソースコード内にハードコードされています。環境変数や設定ファイルから読み込むように変更してください。
- **理由3:** エラーメッセージに詳細なスタックトレースや内部パス情報が含まれており、攻撃者に有用な情報を提供する可能性があります。

### 修正例

#### 例1: SQLインジェクションの可能性
    ```go
    // Before
    func getUser(db *sql.DB, username string) (*User, error) {
        // username は外部からの入力
        query := "SELECT id, name, email FROM users WHERE username = '" + username + "'"
        row := db.QueryRow(query) // SQLインジェクションの危険性
        // ...
        return nil, nil
    }
    ```

    ```go
    // After
    func getUser(db *sql.DB, username string) (*User, error) {
        // username は外部からの入力
        query := "SELECT id, name, email FROM users WHERE username = ?" // プレースホルダを使用
        row := db.QueryRow(query, username) // パラメータとして渡す
        // ...
        var u User
        if err := row.Scan(&u.ID, &u.Name, &u.Email); err != nil {
            if errors.Is(err, sql.ErrNoRows) {
                return nil, fmt.Errorf("ユーザー '%s' が見つかりません", username)
            }
            return nil, fmt.Errorf("ユーザー '%s' の取得に失敗: %w", username, err)
        }
        return &u, nil
    }
    ```

#### 例2: ハードコードされたAPIキー
    ```go
    // Before
    func callExternalAPI() {
        apiKey := "THIS_IS_A_SECRET_API_KEY" // ハードコードされたAPIキー
        // ... apiKey を使ってAPI呼び出し ...
    }
    ```

    ```go
    // After
    func callExternalAPI() {
        apiKey := os.Getenv("MY_APP_API_KEY") // 環境変数からAPIキーを読み込む
        if apiKey == "" {
            log.Panicln("環境変数 MY_APP_API_KEY が設定されていません")
        }
        // ... apiKey を使ってAPI呼び出し ...
    }
    ```

---

## 11. Go 1.24 ループ変数に関する注意 (Go 1.24 Loop Variable Semantics)

### 概要
Go 1.22以降、`for` ループにおけるループ変数のセマンティクスが変更され、各イテレーションで変数が再宣言されるようになりました。これにより、クロージャ内でのループ変数のキャプチャに関する一般的なバグが修正されました。Go 1.24ではこの新しいセマンティクスがデフォルトですが、古いコードや古い挙動を期待しているコードでは注意が必要です。

### レビュー観点
- `for` ループ内でgoroutineを起動し、ループ変数をクロージャでキャプチャしている箇所で、古いセマンティクスを前提としたコードになっていないか。
- Go 1.21以前のコードをGo 1.22以降でビルドする際に、`GOEXPERIMENT=loopvar` の設定に依存した挙動をしていないか。
- 新しいセマンティクスを理解し、それに沿ったコードが書かれているか。

### 修正すべき理由の例
- **理由1:** (Go 1.21以前のコードの場合) ループ内でgoroutineを起動し、ループ変数を直接参照しています。これにより、全てのgoroutineが最後のループ変数の値を参照してしまう可能性があります。ループ変数をgoroutineの引数として渡すか、ループ内でローカルコピーを作成してください。
- **理由2:** (Go 1.22以降のコードで、意図的に古い挙動に依存している場合) このコードはループ変数の古いセマンティクスに依存しているように見えます。Go 1.22以降では、ループ変数は各イテレーションで再宣言されるため、意図した動作と異なる可能性があります。新しいセマンティクスに基づいたコードに修正することを推奨します。

### 修正例 (Go 1.21以前の一般的な問題と修正)

    ```go
    // Before (Go 1.21以前で問題が発生する可能性のあるコード)
    package main

    import (
    	"fmt"
    	"sync"
    )

    func main() {
    	var wg sync.WaitGroup
    	s := []string{"a", "b", "c"}

    	for _, v := range s {
    		wg.Add(1)
    		go func() {
    			defer wg.Done()
    			fmt.Println(v) // 全てのgoroutineが最後の "c" を表示する可能性が高い
    		}()
    	}
    	wg.Wait()
    }
    ```

    ```go
    // After (Go 1.21以前の一般的な修正方法、Go 1.22以降では不要)
    package main

    import (
    	"fmt"
    	"sync"
    )

    func main() {
    	var wg sync.WaitGroup
    	s := []string{"a", "b", "c"}

    	for _, v := range s {
    		wg.Add(1)
    		v := v // ループ変数のローカルコピーを作成 (Go 1.21以前の対策)
    		// または、goroutineの引数として渡す: go func(val string) { ... }(v)
    		go func() {
    			defer wg.Done()
    			fmt.Println(v)
    		}()
    	}
    	wg.Wait()
    }
    // 注意: Go 1.22以降では、上記のローカルコピー (v := v) は不要であり、
    // 元の Before のコードでも各goroutineは期待通りに "a", "b", "c" を (順不同で) 表示します。
    // この項目は、古いコードベースとの互換性や、過去のイディオムを理解する上で重要です。
    ```
    AIコメント例 (Go 1.22以降のコードで、上記のようなローカルコピーを見つけた場合):
    "Go 1.22以降では、forループ変数は各イテレーションで再宣言されるため、クロージャで安全にキャプチャできます。この行の `v := v` というローカルコピーは不要であり、削除できます。"

---
