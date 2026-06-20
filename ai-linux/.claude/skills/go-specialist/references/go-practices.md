# Go言語 コーディング規約 (Go 1.24+)

## 目次

1. [命名規則](#1-命名規則)
2. [エラーハンドリング](#2-エラーハンドリング)
3. [コードフォーマット](#3-コードフォーマット)
4. [コメント](#4-コメント)
5. [関数の設計](#5-関数の設計)
6. [並行処理](#6-並行処理)
7. [テスト](#7-テスト)
8. [パッケージ構成と依存関係](#8-パッケージ構成と依存関係)
9. [パフォーマンス](#9-パフォーマンス)
10. [セキュリティ](#10-セキュリティ)

---

## 1. 命名規則

### レビュー観点
- パッケージ名が短く、小文字で、内容を表しているか
- エクスポートされる識別子が大文字で始まり、されない識別子が小文字で始まっているか
- `mixedCaps` / `MixedCaps` が適切に使用されているか（アンダースコアは通常避ける）
  - ただしstructのjsonタグの項目名は `snake_case` で統一
- 変数名・関数名が役割や動作を的確に表しているか
- 略語は一貫性を保ち、一般的なもの（`HTTP`, `URL`）は全大文字
- インターフェース名は `-er` 接尾辞が慣例（`Reader`, `Writer`）

### 修正例

```go
// Before: エクスポートすべき関数が小文字
func calculateValue() int { return 0 }

// After
// CalculateValue computes and returns the value.
func CalculateValue() int { return 0 }
```

```go
// Before: 曖昧な変数名
func processData(d []string) {
    for _, val := range d { /* ... */ }
}

// After
func processData(lines []string) {
    for _, line := range lines { /* ... */ }
}
```

---

## 2. エラーハンドリング

### レビュー観点
- エラーを返す関数は最後の戻り値として `error` 型を返しているか
- エラーが `_` に捨てられていないか
- エラーを `%w` でラップしてコンテキスト情報を追加しているか（`errors.Is`/`errors.As` での判定を維持するため）
- エラーメッセージが問題の原因特定に役立つ具体性を持っているか
- `panic` の使用が真に回復不可能な状況に限定されているか
- `defer` でのリソース解放時に発生したエラーを適切に処理しているか
- `log.Fatalf`/`log.Fatalln` ではなく `log.Panicf`/`log.Panicln` を使用しているか
  - `log.Fatal*` は `os.Exit(1)` を呼ぶためdeferブロックが実行されない

### 修正例

```go
// Before: エラー無視
func writeToFile(filename string, data []byte) {
    os.WriteFile(filename, data, 0644)
}

// After: エラーをラップして返す
func writeToFile(filename string, data []byte) error {
    if err := os.WriteFile(filename, data, 0644); err != nil {
        return fmt.Errorf("writeToFile: ファイル '%s' への書き込みに失敗: %w", filename, err)
    }
    return nil
}
```

```go
// Before: 元のエラー情報が欠落
return errors.New("データベースクエリ失敗")

// After: %w でラップ
return fmt.Errorf("データベースクエリ失敗: %w", err)
```

---

## 3. コードフォーマット

### レビュー観点
- `gofmt` または `goimports` でフォーマット済みか
- import文が整理されているか（標準パッケージ → サードパーティの順）

フォーマット違反を検出したら `gofmt -w <ファイル名>` の実行を促す。

---

## 4. コメント

### レビュー観点
- エクスポートされるパッケージ・関数・型・変数・定数にGodoc形式のコメントがあるか
  - Godocコメントは全て英語で統一
- コメントが「なぜ」を説明しているか（「何を」ではなく）
- 自明な処理や古くなったコメントが残っていないか
- 複雑なアルゴリズムやトリッキーなコードに説明があるか
- TODOコメントに対応内容と可能なら担当者・期日があるか

### 修正例

```go
// Before: Godocコメントなし
func Add(a, b int) int { return a + b }

// After
// Add adds two integers and returns the result.
func Add(a, b int) int { return a + b }
```

---

## 5. 関数の設計

### レビュー観点
- 関数が単一の責務を持っているか
- 関数名が処理内容を正確に反映しているか
- 引数は3つ程度まで（多い場合は構造体やオプションパターンを検討）
- ポインタレシーバと値レシーバの使い分けが適切か
- 名前付き戻り値を多用しすぎていないか
- 副作用がドキュメント化されているか、関数名から推測できるか
- グローバル変数の変更を極力避けているか

### 修正例

```go
// Before: 複数の責務が混在した長大な関数
func processOrder(orderID, customerID string, items []string, paymentType string) error {
    // 注文取得 → 在庫確認 → 支払い → ステータス更新 → メール送信が全て1関数に...
    return nil
}

// After: 各責務を分離し、メイン関数は制御フローのみ
func processOrder(orderID, customerID string, items []string, paymentType string) error {
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
        log.Printf("顧客 %s への注文確認メール送信に失敗: %v", customerID, err)
    }
    return nil
}
```

---

## 6. 並行処理

### レビュー観点
- goroutineの起動と終了が適切に管理されているか（`sync.WaitGroup` の使用など）
- channelのバッファサイズが適切か
- channelのクローズは送信側が行っているか
- `select` 文がタイムアウトやキャンセル処理（`context` パッケージ）を考慮しているか
- 共有リソースへのアクセスが `sync.Mutex` / `sync.RWMutex` で保護されているか
- デッドロックやgoroutineリークのリスクがないか
- Go 1.22+ではループ変数が各イテレーションで再宣言されるため、不要な `v := v` コピーが残っていれば削除を推奨

### 修正例

```go
// Before: WaitGroupなし
func processTasks(tasks []func()) {
    for _, task := range tasks {
        go task()
    }
}

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
    wg.Wait()
}
```

```go
// Before: mapへの並行書き込み（ランタイムpanic）
func countWords(words []string) map[string]int {
    counts := make(map[string]int)
    for _, word := range words {
        go func(w string) {
            counts[w]++
        }(word)
    }
    time.Sleep(100 * time.Millisecond)
    return counts
}

// After: Mutex + WaitGroup で保護
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

## 7. テスト

### レビュー観点
- `TestXxx` 命名規則に従っているか
- テーブル駆動テストを活用してパターンを網羅しているか
- 正常系だけでなくエラーケースや境界値もカバーしているか
- 各テストが独立しており、他のテスト結果に影響を与えないか
- `t.Parallel()` で並列化し実行時間を短縮しているか
- ヘルパー関数に `t.Helper()` を付与しているか
- モック・スタブで外部依存性を排除しているか（インターネットアクセスは極力避け、テストサーバーで代替）
- ポート番号は `13000`, `28080` のように競合しにくい番号を使用（`3000`, `8080` は避ける）
- `go test` 実行時は `-shuffle on -race -cover` を付ける

### 修正例

```go
// Before: 個別のアサーション
func TestAdd(t *testing.T) {
    if Add(1, 2) != 3 { t.Error("Add(1, 2) should be 3") }
    if Add(-1, -1) != -2 { t.Error("Add(-1, -1) should be -2") }
}

// After: テーブル駆動テスト
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
            if got := Add(tc.a, tc.b); got != tc.want {
                t.Errorf("Add(%d, %d) = %d; want %d", tc.a, tc.b, got, tc.want)
            }
        })
    }
}
```

---

## 8. パッケージ構成と依存関係

### レビュー観点
- パッケージが単一の目的や関連する機能セットに焦点を当てているか
- パッケージ間に循環依存がないか
- `internal` パッケージで意図しない外部利用を防いでいるか
- `go.mod` が適切に管理され、未使用の依存が残っていないか（`go mod tidy` で整理）
- 巨大なパッケージ（god package）になっていないか（`utils` のような汎用パッケージは責務ごとに分割）

---

## 9. パフォーマンス

### レビュー観点
- ループ内で不要なメモリアロケーションがないか（`append` の事前キャパシティ指定不足など）
- 多数の文字列結合に `+` ではなく `strings.Builder` を使用しているか
- 頻繁に呼ばれるループ内で `defer` を使っていないか
- channelの不必要なブロッキングや過度なバッファリングがないか
- `sync.Mutex` のロック範囲が適切か

### 修正例

```go
// Before: キャパシティ未指定で頻繁な再割り当て
var result []string
for i := 0; i < n; i++ {
    result = append(result, fmt.Sprintf("item-%d", i))
}

// After: 事前にキャパシティを指定
result := make([]string, 0, n)
for i := 0; i < n; i++ {
    result = append(result, fmt.Sprintf("item-%d", i))
}
```

```go
// Before: ループ内で + 演算子（O(n²)）
var s string
for _, part := range parts {
    s += part
}

// After: strings.Builder を使用
var sb strings.Builder
for _, part := range parts {
    sb.WriteString(part)
}
return sb.String()
```

---

## 10. セキュリティ

### レビュー観点
- ユーザー入力を検証・サニタイズしているか（SQLインジェクション、XSS、コマンドインジェクション対策）
- `os/exec` で外部入力を直接コマンドとして実行していないか
- ハードコードされた認証情報（APIキー、パスワード）がないか
- セキュリティ用途の乱数に `math/rand` ではなく `crypto/rand` を使用しているか
- エラーメッセージが内部情報を過度に漏洩していないか
- ファイルパス操作でパストラバーサルの脆弱性がないか
- `html/template` / `text/template` で適切にエスケープしているか
- `gosec` で問題が検知されないか
  - テスト用ダミー値など明らかに問題ない箇所のみ `// #nosec ${エラーコード}` を許可

### 修正例

```go
// Before: SQLインジェクション
query := "SELECT id, name, email FROM users WHERE username = '" + username + "'"
row := db.QueryRow(query)

// After: プレースホルダを使用
query := "SELECT id, name, email FROM users WHERE username = ?"
row := db.QueryRow(query, username)
```

```go
// Before: ハードコードされたAPIキー
apiKey := "THIS_IS_A_SECRET_API_KEY"

// After: 環境変数から読み込む
apiKey := os.Getenv("MY_APP_API_KEY")
if apiKey == "" {
    log.Panicln("環境変数 MY_APP_API_KEY が設定されていません")
}
```
