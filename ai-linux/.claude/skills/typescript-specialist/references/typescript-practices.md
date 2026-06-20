# TypeScript 5 コーディング規約

## 目次

1. [型安全性](#1-型安全性)
2. [命名規則](#2-命名規則)
3. [型定義](#3-型定義)
4. [モジュール](#4-モジュール)
5. [エラーハンドリング](#5-エラーハンドリング)
6. [非同期処理](#6-非同期処理)
7. [テスト](#7-テスト)
8. [tsconfig.json](#8-tsconfigjson)
9. [パフォーマンス](#9-パフォーマンス)
10. [セキュリティ](#10-セキュリティ)

---

## 1. 型安全性

### レビュー観点
- `any` を使っていないか（`unknown` + 型ガードで代替すべき）
- `!`（Non-null assertion）の使用が本当に安全か
- 関数の戻り値の型が明示されているか
- `strictNullChecks` を前提とした null/undefined ハンドリングか
- 型ガード（`typeof`, `instanceof`, カスタム型ガード）が正しく絞り込めているか
- `as` による型アサーションが型安全性を損なっていないか

### 修正例

```typescript
// Before: any で型チェック無効化
function parse(input: any): string {
  return input.name.toUpperCase();
}

// After: unknown + 型ガード
function parse(input: unknown): string {
  if (typeof input === 'object' && input !== null && 'name' in input) {
    const { name } = input as { name: unknown };
    if (typeof name === 'string') {
      return name.toUpperCase();
    }
  }
  throw new Error('Invalid input: expected object with string "name" property');
}
```

```typescript
// Before: Non-null assertion で実行時エラーのリスク
const el = document.getElementById('app')!;
el.textContent = 'Hello';

// After: null チェック
const el = document.getElementById('app');
if (!el) {
  throw new Error('Element #app not found');
}
el.textContent = 'Hello';
```

---

## 2. 命名規則

### レビュー観点
- 変数・関数が `camelCase` か
- クラス・インターフェース・型エイリアス・Enum が `PascalCase` か
- 定数が `UPPER_CASE_SNAKE_CASE` か
- ファイル名が `kebab-case`（一般）または `PascalCase`（Reactコンポーネント）で一貫しているか
- 変数名・関数名が意図を正確に表しているか

### 修正例

```typescript
// Before: 命名規則の不統一
const Max_Retries = 3;
type user_role = 'admin' | 'editor';
function GetUserName() { /* ... */ }

// After
const MAX_RETRIES = 3;
type UserRole = 'admin' | 'editor';
function getUserName() { /* ... */ }
```

---

## 3. 型定義

### レビュー観点
- `type` と `interface` を適切に使い分けているか
  - Union型・交差型・タプル型・プリミティブエイリアス → `type`
  - クラスの形状定義・`implements` 用途 → `interface`
- `enum` の代わりに文字列リテラルの Union型を使っているか — `enum` はトランスパイル後にランタイムオブジェクトが生成され、バンドルサイズが増加する
- ユーティリティ型（`Partial<T>`, `Readonly<T>`, `Pick<T, K>`, `Omit<T, K>`）を活用しているか
- 型の粒度が適切か（大きな型より小さな型を合成する設計が望ましい）
- Discriminated Union で分岐処理を型安全にしているか
- `satisfies` 演算子で型推論を保持しつつ型適合を検証しているか
- `as const` で不変リテラル型を活用しているか
- Branded Types で意味的に異なるプリミティブを区別しているか

### 修正例

```typescript
// Before: enum
enum Status {
  Active = 'active',
  Inactive = 'inactive',
}

// After: Union型 — バンドルサイズが小さく、Tree Shakingも効く
type Status = 'active' | 'inactive';
```

```typescript
// Before: 条件分岐で型が曖昧
type Shape = { kind: string; radius?: number; width?: number; height?: number };

function area(shape: Shape): number {
  if (shape.kind === 'circle') return Math.PI * shape.radius! ** 2;
  return shape.width! * shape.height!;
}

// After: Discriminated Union で網羅性チェック
type Shape =
  | { kind: 'circle'; radius: number }
  | { kind: 'rectangle'; width: number; height: number };

function area(shape: Shape): number {
  switch (shape.kind) {
    case 'circle':
      return Math.PI * shape.radius ** 2;
    case 'rectangle':
      return shape.width * shape.height;
  }
}
```

```typescript
// satisfies: 型推論を保持しつつ型適合を検証
const config = {
  port: 3000,
  host: 'localhost',
} satisfies Record<string, string | number>;
// config.port は number 型のまま（Record<string, string | number> にキャストされない）
```

```typescript
// as const: リテラル型として推論させる
const ROLES = ['admin', 'editor', 'viewer'] as const;
type Role = typeof ROLES[number]; // 'admin' | 'editor' | 'viewer'
```

```typescript
// Branded Types: 意味的に異なる string/number を型レベルで区別
type UserId = string & { readonly __brand: 'UserId' };
type OrderId = string & { readonly __brand: 'OrderId' };

function getUser(id: UserId): void { /* ... */ }

const orderId = 'order-123' as OrderId;
// getUser(orderId); // コンパイルエラー — UserId と OrderId を取り違えない
```

---

## 4. モジュール

### レビュー観点
- ESモジュール（`import`/`export`）を使用しているか
- `export default` より名前付きエクスポートを優先しているか — インポート時の名前の揺れを防ぎ、リファクタリングを容易にするため
- `import type` / `export type` で型のみのインポート・エクスポートを明示しているか — ランタイムに不要なインポートを排除し、バンドルサイズを削減する
- パスエイリアス（tsconfig.json の `paths`）で相対パスの深いネストを避けているか
- 循環依存がないか
- バレルファイル（`index.ts` での再エクスポート）が肥大化していないか

### 修正例

```typescript
// Before: default export
export default class UserService { /* ... */ }

// After: 名前付きエクスポート
export class UserService { /* ... */ }
```

```typescript
// Before: 型とランタイム値のインポートが混在
import { User, getUserById } from './user';

// After: 型は import type で分離
import type { User } from './user';
import { getUserById } from './user';
```

```json
// tsconfig.json のパスエイリアス設定
{
  "compilerOptions": {
    "baseUrl": "./src",
    "paths": {
      "@components/*": ["components/*"],
      "@services/*": ["services/*"]
    }
  }
}
```

---

## 5. エラーハンドリング

### レビュー観点
- カスタムエラークラスでエラー種別を区別しているか
- `try...catch` で具体的なエラー型をハンドリングしているか
- Promise の reject が適切に処理されているか
- エラーメッセージが原因特定に十分な具体性を持っているか
- エラーを握りつぶしていないか（catch で何もせずに return する等）

### 修正例

```typescript
// Before: 汎用 Error のみ
async function fetchUser(id: string): Promise<User> {
  const res = await fetch(`/api/users/${id}`);
  if (!res.ok) throw new Error('Failed');
  return res.json();
}

// After: カスタムエラーで種別を区別
class NotFoundError extends Error {
  constructor(resource: string, id: string) {
    super(`${resource} not found: ${id}`);
    this.name = 'NotFoundError';
  }
}

class NetworkError extends Error {
  constructor(message: string, public readonly statusCode: number) {
    super(message);
    this.name = 'NetworkError';
  }
}

async function fetchUser(id: string): Promise<User> {
  const res = await fetch(`/api/users/${id}`);
  if (res.status === 404) throw new NotFoundError('User', id);
  if (!res.ok) throw new NetworkError(`Failed to fetch user: ${res.statusText}`, res.status);
  return res.json();
}
```

---

## 6. 非同期処理

### レビュー観点
- `async/await` を使用しているか（Promise チェーンより読みやすく、スタックトレースも明確になる）
- Promise コンストラクタ内で `async` 関数を使用していないか — reject されない例外が発生するリスクがある
- 並行実行可能な処理に `Promise.all` / `Promise.allSettled` を活用しているか
- `await` の直列化で不要なウォーターフォールが発生していないか

### 修正例

```typescript
// Before: 直列 await で不要に遅い
const user = await fetchUser(id);
const orders = await fetchOrders(id);
const reviews = await fetchReviews(id);

// After: 独立した処理は並行実行
const [user, orders, reviews] = await Promise.all([
  fetchUser(id),
  fetchOrders(id),
  fetchReviews(id),
]);
```

```typescript
// Before: Promise コンストラクタ内の async（アンチパターン）
const result = new Promise(async (resolve, reject) => {
  const data = await fetchData();
  resolve(data);
});

// After: async 関数を直接使用
const result = fetchData();
```

---

## 7. テスト

### レビュー観点
- テーブル駆動テスト（`it.each` / `test.each`）でパターンを網羅しているか
- 型定義のテストがあるか — 複雑な型ロジックが期待通りに動作することを検証する
- モック・スタブで外部依存を分離しているか
- 正常系だけでなくエラーケースや境界値もカバーしているか
- テスト名が「何を」「どうすると」「どうなるか」を表しているか

### 修正例

```typescript
// テーブル駆動テスト（Vitest / Jest）
describe('add', () => {
  it.each([
    { a: 1, b: 2, expected: 3 },
    { a: -1, b: -1, expected: -2 },
    { a: 0, b: 0, expected: 0 },
  ])('add($a, $b) returns $expected', ({ a, b, expected }) => {
    expect(add(a, b)).toBe(expected);
  });
});
```

```typescript
// 型テスト: コンパイル時に型が期待通りかを検証
// @ts-expect-error — string は UserId に代入できない
const id: UserId = 'raw-string';

// expectTypeOf（vitest）
import { expectTypeOf } from 'vitest';
expectTypeOf(getUser).parameter(0).toMatchTypeOf<UserId>();
```

---

## 8. tsconfig.json

### 推奨設定

```json
{
  "compilerOptions": {
    "strict": true,
    "noImplicitReturns": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "esModuleInterop": true,
    "forceConsistentCasingInFileNames": true,
    "skipLibCheck": true
  }
}
```

### レビュー観点
- `"strict": true` が有効か — `strictNullChecks`, `strictFunctionTypes`, `noImplicitAny` 等を一括有効化
- `"noImplicitReturns": true` で全コードパスの戻り値を保証しているか
- `"noUnusedLocals"` / `"noUnusedParameters"` で未使用コードを検出しているか
- `target` がプロジェクトの実行環境に合っているか（Node.js → `ES2022`+、ブラウザ → `ES2020`+ 等）
- `module` が適切か（`ESNext` または `Node16`/`NodeNext`）

---

## 9. パフォーマンス

### レビュー観点
- 過度に複雑な条件付き型やMapped Typesがビルド時間を圧迫していないか
- イベントリスナーやタイマーのクリーンアップが適切か — メモリリーク防止
- 動的インポート（`import()`）で必要なモジュールのみを遅延読み込みしているか
- ループ内で高コストな操作（オブジェクトの深いコピー等）を繰り返していないか

---

## 10. セキュリティ

### レビュー観点
- ユーザー入力をサニタイズ・バリデーションしているか
- `eval()` や `innerHTML` に信頼できないデータを渡していないか — XSS の原因
- 機密情報（APIキー、トークン）がコードにハードコードされていないか
- 依存ライブラリの脆弱性をチェックしているか（`npm audit`）
- テンプレートリテラルをSQLクエリやHTMLに直接埋め込んでいないか（パラメータ化クエリやサニタイズ関数を使用する）
