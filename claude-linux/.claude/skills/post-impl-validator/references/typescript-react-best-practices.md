# TypeScript/React ベストプラクティス

## はじめに

この指示ファイルは、AIコーディング支援ツールがTypeScript/Reactのコードをレビューし、ベストプラクティスに沿った修正案を提示するためのガイドラインです。各項目には、レビューの観点、修正を推奨する理由の例、そして具体的な修正前後のコード例を含んでいます。

## 対象バージョン

- TypeScript 5.x以上
- React 19以上

---

## 1. 型定義 (Type Definitions)

### 概要

TypeScriptの強力な型システムを活用することで、コンパイル時にエラーを検出し、コードの信頼性と保守性を向上させます。

### レビュー観点

- コンポーネントのPropsとStateに適切な型が定義されているか。
- `any` 型の使用を避け、具体的な型を定義しているか。
- Union型やLiteral型を適切に活用しているか。
- 型推論を活用しつつ、必要な箇所では明示的な型注釈を付けているか。
- 再利用可能な型は別ファイルに切り出しているか。
- Genericsを適切に活用しているか。
- `unknown` 型を `any` の代わりに使用し、型安全性を確保しているか。
- 関数の戻り値型が明示されているか（特にパブリックAPI）。

### 修正すべき理由の例

- **理由1:** Props型が定義されておらず、コンポーネントの使用方法が不明確です。
- **理由2:** `any` 型が使用されており、型安全性が損なわれています。
- **理由3:** 同じ型定義が複数箇所で重複しており、保守性が低下しています。

### 修正例

#### 例1: Props型の定義

```typescript
// Before
function UserCard(props) {
  return <div>{props.name}</div>;
}
```

```typescript
// After
interface UserCardProps {
  name: string;
  email: string;
  avatar?: string;
}

function UserCard({ name, email, avatar }: UserCardProps) {
  return (
    <div>
      <span>{name}</span>
      <span>{email}</span>
      {avatar && <img src={avatar} alt={name} />}
    </div>
  );
}
```

#### 例2: any型の排除

```typescript
// Before
function processData(data: any) {
  return data.map((item: any) => item.value);
}
```

```typescript
// After
interface DataItem {
  id: string;
  value: number;
}

function processData(data: DataItem[]): number[] {
  return data.map((item) => item.value);
}
```

#### 例3: Union型とLiteral型

```typescript
// Before
interface Button {
  size: string;
  variant: string;
}
```

```typescript
// After
type ButtonSize = 'small' | 'medium' | 'large';
type ButtonVariant = 'primary' | 'secondary' | 'danger';

interface ButtonProps {
  size: ButtonSize;
  variant: ButtonVariant;
}
```

---

## 2. コンポーネント設計 (Component Design)

### 概要

Reactコンポーネントは、再利用性、テスト容易性、保守性を考慮して設計されるべきです。単一責任の原則に従い、適切なサイズに保つことが重要です。

### レビュー観点

- 関数コンポーネントを使用しているか（クラスコンポーネントは非推奨）。
- 単一責任の原則に従っているか。
- コンポーネントのサイズが適切か（目安として50-100行）。
- Propsドリリングを避け、Context APIやステート管理ライブラリを活用しているか。
- Presentational ComponentとContainer Componentの分離ができているか。
- コンポーネントの命名が適切か（PascalCase、内容を表す名前）。
- ファイル1つにつき1コンポーネントを原則としているか。

### 修正すべき理由の例

- **理由1:** このコンポーネントは複数の責務を持っており、テストと保守が困難です。
- **理由2:** Propsが5階層以上にわたってドリリングされており、可読性が低下しています。
- **理由3:** コンポーネントが300行を超えており、分割を検討してください。

### 修正例

#### 例1: 単一責任の原則

```typescript
// Before - 複数の責務を持つコンポーネント
function UserDashboard({ userId }: { userId: string }) {
  const [user, setUser] = useState<User | null>(null);
  const [posts, setPosts] = useState<Post[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // ユーザー情報の取得
    fetchUser(userId).then(setUser);
    // 投稿の取得
    fetchPosts(userId).then(setPosts);
    setLoading(false);
  }, [userId]);

  if (loading) return <Spinner />;

  return (
    <div>
      <div>{user?.name}</div>
      <div>{user?.email}</div>
      <ul>
        {posts.map(post => (
          <li key={post.id}>{post.title}</li>
        ))}
      </ul>
    </div>
  );
}
```

```typescript
// After - 責務を分離したコンポーネント
function UserDashboard({ userId }: { userId: string }) {
  return (
    <div>
      <UserProfile userId={userId} />
      <UserPosts userId={userId} />
    </div>
  );
}

function UserProfile({ userId }: { userId: string }) {
  const { data: user, isLoading } = useUser(userId);

  if (isLoading) return <Spinner />;

  return (
    <div>
      <span>{user?.name}</span>
      <span>{user?.email}</span>
    </div>
  );
}

function UserPosts({ userId }: { userId: string }) {
  const { data: posts, isLoading } = usePosts(userId);

  if (isLoading) return <Spinner />;

  return (
    <ul>
      {posts?.map(post => (
        <PostItem key={post.id} post={post} />
      ))}
    </ul>
  );
}
```

#### 例2: Propsドリリングの回避

```typescript
// Before - 深いPropsドリリング
function App() {
  const [theme, setTheme] = useState('light');
  return <Layout theme={theme} setTheme={setTheme} />;
}

function Layout({ theme, setTheme }) {
  return <Sidebar theme={theme} setTheme={setTheme} />;
}

function Sidebar({ theme, setTheme }) {
  return <ThemeToggle theme={theme} setTheme={setTheme} />;
}
```

```typescript
// After - Context APIを使用
const ThemeContext = createContext<{
  theme: string;
  setTheme: (theme: string) => void;
} | null>(null);

function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within ThemeProvider');
  }
  return context;
}

function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = useState('light');
  return (
    <ThemeContext.Provider value={{ theme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

function App() {
  return (
    <ThemeProvider>
      <Layout />
    </ThemeProvider>
  );
}

function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  return (
    <button onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}>
      Toggle Theme
    </button>
  );
}
```

---

## 3. Hooks使用法 (Hooks Usage)

### 概要

React Hooksは、関数コンポーネントで状態管理や副作用を扱うための強力な機能です。正しく使用することで、コードの再利用性と可読性が向上します。

### レビュー観点

- `useState` の初期値が適切に設定されているか。
- `useEffect` の依存配列が正しく設定されているか。
- `useCallback` と `useMemo` が適切に使用されているか（過度な使用は避ける）。
- カスタムHooksへの抽出が適切に行われているか。
- React 19の新Hooks（`useActionState`, `useFormStatus`, `useOptimistic`）を適切に活用しているか。
- Hooksのルールを守っているか（トップレベルでのみ呼び出し、条件分岐内で使用しない）。
- `useRef` と `useState` の使い分けが適切か。

### 修正すべき理由の例

- **理由1:** `useEffect` の依存配列に必要な値が含まれておらず、stale closureが発生する可能性があります。
- **理由2:** 単純な値に `useMemo` を使用しており、不要なオーバーヘッドが生じています。
- **理由3:** 複数のコンポーネントで同じロジックが重複しており、カスタムHooksへの抽出を検討してください。

### 修正例

#### 例1: useEffectの依存配列

```typescript
// Before - 依存配列の問題
function SearchComponent({ query }: { query: string }) {
  const [results, setResults] = useState<string[]>([]);

  useEffect(() => {
    fetchResults(query).then(setResults);
  }, []); // queryが依存配列に含まれていない

  return <ResultList results={results} />;
}
```

```typescript
// After - 正しい依存配列
function SearchComponent({ query }: { query: string }) {
  const [results, setResults] = useState<string[]>([]);

  useEffect(() => {
    const controller = new AbortController();

    fetchResults(query, { signal: controller.signal })
      .then(setResults)
      .catch((error) => {
        if (error.name !== 'AbortError') {
          console.error(error);
        }
      });

    return () => controller.abort();
  }, [query]); // queryを依存配列に追加

  return <ResultList results={results} />;
}
```

#### 例2: カスタムHooksへの抽出

```typescript
// Before - 重複したロジック
function UserProfile() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    setLoading(true);
    fetchUser()
      .then(setUser)
      .catch(setError)
      .finally(() => setLoading(false));
  }, []);

  // ...
}

function PostList() {
  const [posts, setPosts] = useState<Post[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    setLoading(true);
    fetchPosts()
      .then(setPosts)
      .catch(setError)
      .finally(() => setLoading(false));
  }, []);

  // ...
}
```

```typescript
// After - カスタムHooksで共通化
function useFetch<T>(fetchFn: () => Promise<T>) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    setLoading(true);
    fetchFn()
      .then(setData)
      .catch(setError)
      .finally(() => setLoading(false));
  }, [fetchFn]);

  return { data, loading, error };
}

function UserProfile() {
  const { data: user, loading, error } = useFetch(fetchUser);
  // ...
}

function PostList() {
  const { data: posts, loading, error } = useFetch(fetchPosts);
  // ...
}
```

#### 例3: React 19のuseActionState

```typescript
// Before - 従来のフォーム状態管理
function LoginForm() {
  const [isPending, setIsPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setIsPending(true);
    setError(null);

    const formData = new FormData(e.currentTarget);
    try {
      await login(formData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setIsPending(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      {error && <p>{error}</p>}
      <input name="email" type="email" disabled={isPending} />
      <input name="password" type="password" disabled={isPending} />
      <button type="submit" disabled={isPending}>
        {isPending ? 'Logging in...' : 'Login'}
      </button>
    </form>
  );
}
```

```typescript
// After - React 19のuseActionState
import { useActionState } from 'react';

async function loginAction(
  prevState: { error: string | null },
  formData: FormData
) {
  try {
    await login(formData);
    return { error: null };
  } catch (err) {
    return { error: err instanceof Error ? err.message : 'Login failed' };
  }
}

function LoginForm() {
  const [state, formAction, isPending] = useActionState(loginAction, {
    error: null,
  });

  return (
    <form action={formAction}>
      {state.error && <p>{state.error}</p>}
      <input name="email" type="email" disabled={isPending} />
      <input name="password" type="password" disabled={isPending} />
      <button type="submit" disabled={isPending}>
        {isPending ? 'Logging in...' : 'Login'}
      </button>
    </form>
  );
}
```

---

## 4. 状態管理 (State Management)

### 概要

効果的な状態管理は、アプリケーションの複雑さを軽減し、予測可能な動作を保証します。ローカル状態とグローバル状態を適切に使い分けることが重要です。

### レビュー観点

- ローカル状態とグローバル状態が適切に使い分けられているか。
- Context APIの適切な使用（頻繁に更新される状態には不向き）。
- 状態の正規化が行われているか（ネストされたデータの平坦化）。
- 不変性が維持されているか。
- 派生状態を `useMemo` で計算しているか（状態として保持しない）。
- 状態の更新が適切にバッチ処理されているか。

### 修正すべき理由の例

- **理由1:** このコンポーネント内でのみ使用される状態がグローバルに管理されており、不必要な複雑さが生じています。
- **理由2:** 状態を直接変更しており、予期しない動作の原因となる可能性があります。
- **理由3:** 派生状態を `useState` で管理しており、同期の問題が発生する可能性があります。

### 修正例

#### 例1: 状態の不変性

```typescript
// Before - 状態の直接変更
function TodoList() {
  const [todos, setTodos] = useState<Todo[]>([]);

  const toggleTodo = (id: string) => {
    const todo = todos.find(t => t.id === id);
    if (todo) {
      todo.completed = !todo.completed; // 直接変更
      setTodos([...todos]);
    }
  };

  // ...
}
```

```typescript
// After - 不変性を維持
function TodoList() {
  const [todos, setTodos] = useState<Todo[]>([]);

  const toggleTodo = (id: string) => {
    setTodos(prevTodos =>
      prevTodos.map(todo =>
        todo.id === id ? { ...todo, completed: !todo.completed } : todo
      )
    );
  };

  // ...
}
```

#### 例2: 派生状態の計算

```typescript
// Before - 派生状態をuseStateで管理
function ProductList({ products }: { products: Product[] }) {
  const [filteredProducts, setFilteredProducts] = useState<Product[]>(products);
  const [filter, setFilter] = useState('');

  useEffect(() => {
    setFilteredProducts(
      products.filter(p => p.name.includes(filter))
    );
  }, [products, filter]);

  // ...
}
```

```typescript
// After - useMemoで派生状態を計算
function ProductList({ products }: { products: Product[] }) {
  const [filter, setFilter] = useState('');

  const filteredProducts = useMemo(
    () => products.filter(p => p.name.toLowerCase().includes(filter.toLowerCase())),
    [products, filter]
  );

  // ...
}
```

---

## 5. パフォーマンス最適化 (Performance Optimization)

### 概要

Reactアプリケーションのパフォーマンスは、不要な再レンダリングの防止と効率的なリソース管理によって向上します。

### レビュー観点

- 不要な再レンダリングが防止されているか。
- `React.memo` が適切に使用されているか。
- コード分割とレイジーローディングが実装されているか。
- `key` 属性が適切に設定されているか（インデックスの使用を避ける）。
- 大きなリストに仮想化（virtualization）が適用されているか。
- イベントハンドラがレンダリングごとに再生成されていないか。

### 修正すべき理由の例

- **理由1:** 親コンポーネントの再レンダリングにより、変更のない子コンポーネントも再レンダリングされています。
- **理由2:** リストの `key` にインデックスを使用しており、リストの順序変更時に問題が発生する可能性があります。
- **理由3:** 大きなコンポーネントが初期ロード時に全て読み込まれており、パフォーマンスに影響しています。

### 修正例

#### 例1: React.memoの適切な使用

```typescript
// Before - 不要な再レンダリング
function ParentComponent() {
  const [count, setCount] = useState(0);

  return (
    <div>
      <button onClick={() => setCount(c => c + 1)}>Count: {count}</button>
      <ExpensiveChild data={staticData} />
    </div>
  );
}

function ExpensiveChild({ data }: { data: Data }) {
  // 重い計算処理
  return <div>{/* ... */}</div>;
}
```

```typescript
// After - React.memoで最適化
function ParentComponent() {
  const [count, setCount] = useState(0);

  return (
    <div>
      <button onClick={() => setCount(c => c + 1)}>Count: {count}</button>
      <MemoizedExpensiveChild data={staticData} />
    </div>
  );
}

const MemoizedExpensiveChild = React.memo(function ExpensiveChild({
  data,
}: {
  data: Data;
}) {
  // 重い計算処理
  return <div>{/* ... */}</div>;
});
```

#### 例2: key属性の適切な使用

```typescript
// Before - インデックスをkeyとして使用
function TodoList({ todos }: { todos: Todo[] }) {
  return (
    <ul>
      {todos.map((todo, index) => (
        <li key={index}>{todo.text}</li>
      ))}
    </ul>
  );
}
```

```typescript
// After - 一意のIDをkeyとして使用
function TodoList({ todos }: { todos: Todo[] }) {
  return (
    <ul>
      {todos.map((todo) => (
        <li key={todo.id}>{todo.text}</li>
      ))}
    </ul>
  );
}
```

#### 例3: コード分割とレイジーローディング

```typescript
// Before - 全てのコンポーネントを同期的にインポート
import { Dashboard } from './Dashboard';
import { Settings } from './Settings';
import { Profile } from './Profile';

function App() {
  return (
    <Routes>
      <Route path="/" element={<Dashboard />} />
      <Route path="/settings" element={<Settings />} />
      <Route path="/profile" element={<Profile />} />
    </Routes>
  );
}
```

```typescript
// After - React.lazyでコード分割
import { lazy, Suspense } from 'react';

const Dashboard = lazy(() => import('./Dashboard'));
const Settings = lazy(() => import('./Settings'));
const Profile = lazy(() => import('./Profile'));

function App() {
  return (
    <Suspense fallback={<Loading />}>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="/profile" element={<Profile />} />
      </Routes>
    </Suspense>
  );
}
```

---

## 6. エラーハンドリング (Error Handling)

### 概要

適切なエラーハンドリングは、ユーザー体験を向上させ、デバッグを容易にします。Error Boundariesとtry-catchを適切に使用することが重要です。

### レビュー観点

- Error Boundariesが適切に配置されているか。
- 非同期処理でのtry-catchが適切に使用されているか。
- ユーザーフレンドリーなエラーメッセージが表示されているか。
- エラーログが適切に記録されているか。
- フォールバックUIが用意されているか。

### 修正すべき理由の例

- **理由1:** Error Boundaryが設定されておらず、コンポーネントのエラーがアプリ全体をクラッシュさせる可能性があります。
- **理由2:** 非同期処理のエラーが適切にハンドリングされておらず、ユーザーにフィードバックがありません。
- **理由3:** エラーメッセージが技術的すぎて、ユーザーが理解できません。

### 修正例

#### 例1: Error Boundary

```typescript
// Before - Error Boundaryなし
function App() {
  return (
    <div>
      <Header />
      <MainContent />
      <Footer />
    </div>
  );
}
```

```typescript
// After - Error Boundaryを追加
import { Component, ReactNode } from 'react';

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

class ErrorBoundary extends Component<
  { children: ReactNode; fallback?: ReactNode },
  ErrorBoundaryState
> {
  state: ErrorBoundaryState = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
    // エラーログサービスに送信
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback || <ErrorFallback error={this.state.error} />;
    }
    return this.props.children;
  }
}

function App() {
  return (
    <ErrorBoundary>
      <Header />
      <ErrorBoundary fallback={<ContentError />}>
        <MainContent />
      </ErrorBoundary>
      <Footer />
    </ErrorBoundary>
  );
}
```

#### 例2: 非同期エラーハンドリング

```typescript
// Before - エラーハンドリングなし
async function fetchData() {
  const response = await fetch('/api/data');
  return response.json();
}

function DataComponent() {
  const [data, setData] = useState(null);

  useEffect(() => {
    fetchData().then(setData);
  }, []);

  return <div>{/* ... */}</div>;
}
```

```typescript
// After - 適切なエラーハンドリング
async function fetchData(): Promise<Data> {
  const response = await fetch('/api/data');

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return response.json();
}

function DataComponent() {
  const [data, setData] = useState<Data | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const controller = new AbortController();

    fetchData()
      .then(setData)
      .catch((err) => {
        if (err.name !== 'AbortError') {
          setError('データの取得に失敗しました。後でもう一度お試しください。');
          console.error('Fetch error:', err);
        }
      })
      .finally(() => setLoading(false));

    return () => controller.abort();
  }, []);

  if (loading) return <Loading />;
  if (error) return <ErrorMessage message={error} />;
  if (!data) return null;

  return <div>{/* データを表示 */}</div>;
}
```

---

## 7. テスト (Testing)

### 概要

効果的なテストは、コードの品質を保証し、リファクタリングを容易にします。React Testing Libraryを使用してユーザー中心のテストを書くことが推奨されます。

### レビュー観点

- Testing Libraryのベストプラクティスに従っているか。
- ユーザー操作をシミュレートしたテストになっているか。
- モックが適切に使用され、外部依存が排除されているか。
- テストカバレッジが適切に確保されているか。
- 実装詳細ではなく、振る舞いをテストしているか。

### 修正すべき理由の例

- **理由1:** 実装詳細（内部状態やメソッド）をテストしており、リファクタリング時に壊れやすいテストになっています。
- **理由2:** 外部APIへの実際のリクエストを行っており、テストが不安定です。
- **理由3:** `getByTestId` を多用しており、アクセシビリティを考慮したクエリを使用してください。

### 修正例

#### 例1: ユーザー操作ベースのテスト

```typescript
// Before - 実装詳細に依存したテスト
import { render, screen } from '@testing-library/react';

test('counter increments', () => {
  const { container } = render(<Counter />);
  const button = container.querySelector('button');
  const display = container.querySelector('.count-display');

  fireEvent.click(button!);

  expect(display?.textContent).toBe('1');
});
```

```typescript
// After - ユーザー視点のテスト
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

test('counter increments when user clicks the button', async () => {
  const user = userEvent.setup();
  render(<Counter />);

  const button = screen.getByRole('button', { name: /increment/i });

  await user.click(button);

  expect(screen.getByText('Count: 1')).toBeInTheDocument();
});
```

#### 例2: APIモック

```typescript
// Before - 実際のAPIを呼び出す
test('displays user data', async () => {
  render(<UserProfile userId="1" />);

  // 実際のAPIレスポンスを待つ
  await screen.findByText('John Doe');
});
```

```typescript
// After - APIをモック
import { rest } from 'msw';
import { setupServer } from 'msw/node';

const server = setupServer(
  rest.get('/api/users/:id', (req, res, ctx) => {
    return res(
      ctx.json({
        id: req.params.id,
        name: 'John Doe',
        email: 'john@example.com',
      })
    );
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

test('displays user data', async () => {
  render(<UserProfile userId="1" />);

  expect(await screen.findByText('John Doe')).toBeInTheDocument();
  expect(screen.getByText('john@example.com')).toBeInTheDocument();
});

test('displays error message when API fails', async () => {
  server.use(
    rest.get('/api/users/:id', (req, res, ctx) => {
      return res(ctx.status(500));
    })
  );

  render(<UserProfile userId="1" />);

  expect(await screen.findByText(/error/i)).toBeInTheDocument();
});
```

---

## 8. アクセシビリティ (Accessibility)

### 概要

アクセシビリティは、すべてのユーザーがアプリケーションを利用できるようにするために重要です。WCAG（Web Content Accessibility Guidelines）に準拠することを目指します。

### レビュー観点

- セマンティックHTMLが使用されているか。
- ARIA属性が適切に使用されているか。
- キーボードナビゲーションが可能か。
- スクリーンリーダーに対応しているか。
- カラーコントラストが十分か。
- フォーカス管理が適切か。

### 修正すべき理由の例

- **理由1:** `div` でボタンを実装しており、キーボードでの操作ができません。
- **理由2:** 画像に `alt` 属性がなく、スクリーンリーダーユーザーが内容を理解できません。
- **理由3:** フォーム入力にラベルが関連付けられていません。

### 修正例

#### 例1: セマンティックHTML

```typescript
// Before - セマンティックでないHTML
function Navigation() {
  return (
    <div className="nav">
      <div className="nav-item" onClick={() => navigate('/')}>Home</div>
      <div className="nav-item" onClick={() => navigate('/about')}>About</div>
    </div>
  );
}
```

```typescript
// After - セマンティックなHTML
function Navigation() {
  return (
    <nav aria-label="Main navigation">
      <ul>
        <li>
          <a href="/">Home</a>
        </li>
        <li>
          <a href="/about">About</a>
        </li>
      </ul>
    </nav>
  );
}
```

#### 例2: フォームのアクセシビリティ

```typescript
// Before - ラベルなし
function LoginForm() {
  return (
    <form>
      <input type="email" placeholder="Email" />
      <input type="password" placeholder="Password" />
      <div onClick={handleSubmit}>Login</div>
    </form>
  );
}
```

```typescript
// After - 適切なラベルとセマンティクス
function LoginForm() {
  return (
    <form onSubmit={handleSubmit}>
      <div>
        <label htmlFor="email">Email</label>
        <input
          id="email"
          type="email"
          autoComplete="email"
          required
          aria-describedby="email-hint"
        />
        <span id="email-hint" className="hint">
          Enter your registered email address
        </span>
      </div>

      <div>
        <label htmlFor="password">Password</label>
        <input
          id="password"
          type="password"
          autoComplete="current-password"
          required
        />
      </div>

      <button type="submit">Login</button>
    </form>
  );
}
```

#### 例3: カスタムボタンのアクセシビリティ

```typescript
// Before - アクセシブルでないカスタムボタン
function IconButton({ icon, onClick }) {
  return (
    <div className="icon-button" onClick={onClick}>
      <Icon name={icon} />
    </div>
  );
}
```

```typescript
// After - アクセシブルなカスタムボタン
function IconButton({
  icon,
  onClick,
  label,
}: {
  icon: string;
  onClick: () => void;
  label: string;
}) {
  return (
    <button
      type="button"
      className="icon-button"
      onClick={onClick}
      aria-label={label}
    >
      <Icon name={icon} aria-hidden="true" />
    </button>
  );
}
```

---

## 9. セキュリティ (Security)

### 概要

フロントエンドのセキュリティは、ユーザーデータの保護とアプリケーションの信頼性を確保するために重要です。

### レビュー観点

- XSS（クロスサイトスクリプティング）対策が行われているか。
- `dangerouslySetInnerHTML` の使用が最小限かつ安全か。
- ユーザー入力のサニタイズが行われているか。
- 認証情報が安全に取り扱われているか。
- 機密情報がクライアントサイドに露出していないか。

### 修正すべき理由の例

- **理由1:** ユーザー入力を直接 `dangerouslySetInnerHTML` で出力しており、XSS攻撃のリスクがあります。
- **理由2:** APIキーがクライアントサイドのコードにハードコードされています。
- **理由3:** 認証トークンがlocalStorageに保存されており、XSS攻撃に対して脆弱です。

### 修正例

#### 例1: XSS対策

```typescript
// Before - XSS脆弱性
function Comment({ content }: { content: string }) {
  return <div dangerouslySetInnerHTML={{ __html: content }} />;
}
```

```typescript
// After - 安全な実装
import DOMPurify from 'dompurify';

function Comment({ content }: { content: string }) {
  // HTMLを許可する場合はサニタイズ
  const sanitizedContent = DOMPurify.sanitize(content, {
    ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'a'],
    ALLOWED_ATTR: ['href'],
  });

  return <div dangerouslySetInnerHTML={{ __html: sanitizedContent }} />;
}

// または、HTMLを許可しない場合
function SafeComment({ content }: { content: string }) {
  return <div>{content}</div>; // Reactが自動的にエスケープ
}
```

#### 例2: 認証情報の安全な取り扱い

```typescript
// Before - 安全でない認証情報の保存
function login(token: string) {
  localStorage.setItem('authToken', token);
}

function getAuthToken() {
  return localStorage.getItem('authToken');
}
```

```typescript
// After - HttpOnly Cookieを使用
// サーバーサイドでHttpOnly Cookieを設定

// クライアントサイドでは、認証状態を別の方法で管理
function useAuth() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    // 認証状態をAPIで確認
    fetch('/api/auth/status', { credentials: 'include' })
      .then(res => res.json())
      .then(data => setIsAuthenticated(data.isAuthenticated))
      .catch(() => setIsAuthenticated(false));
  }, []);

  return { isAuthenticated };
}
```

#### 例3: 環境変数の適切な使用

```typescript
// Before - APIキーのハードコード
const API_KEY = 'sk-1234567890abcdef';

async function fetchData() {
  const response = await fetch('/api/data', {
    headers: {
      'X-API-Key': API_KEY,
    },
  });
  return response.json();
}
```

```typescript
// After - 環境変数を使用（サーバーサイドプロキシ推奨）
// フロントエンドではAPIキーを直接使用しない

// バックエンドプロキシを経由してAPIを呼び出す
async function fetchData() {
  const response = await fetch('/api/proxy/data', {
    credentials: 'include', // 認証はCookieで
  });
  return response.json();
}

// または、公開可能な設定のみ環境変数で使用
const config = {
  apiUrl: process.env.NEXT_PUBLIC_API_URL,
  // 注意: NEXT_PUBLIC_ プレフィックスの変数はクライアントに露出する
};
```

---

## 10. コードスタイル (Code Style)

### 概要

一貫したコードスタイルは、コードの可読性と保守性を向上させます。チーム全体で統一されたスタイルガイドに従うことが重要です。

### レビュー観点

- 命名規則が守られているか（コンポーネント: PascalCase、関数/変数: camelCase）。
- ファイル構成が適切か。
- インポート順序が統一されているか。
- ESLint/Prettierの設定に従っているか。
- コメントが適切に書かれているか。

### 修正すべき理由の例

- **理由1:** コンポーネント名がcamelCaseで書かれており、命名規則に違反しています。
- **理由2:** インポート順序がバラバラで、一貫性がありません。
- **理由3:** 不要なコメントやコメントアウトされたコードが残っています。

### 修正例

#### 例1: 命名規則

```typescript
// Before - 不適切な命名
const userProfile = () => {
  const USER_NAME = 'John';
  const Handle_Click = () => {};

  return <div onClick={Handle_Click}>{USER_NAME}</div>;
};
```

```typescript
// After - 適切な命名
const UserProfile = () => {
  const userName = 'John';
  const handleClick = () => {};

  return <div onClick={handleClick}>{userName}</div>;
};
```

#### 例2: インポート順序

```typescript
// Before - 順序がバラバラ
import { Button } from './components/Button';
import React, { useState } from 'react';
import axios from 'axios';
import { useAuth } from '../hooks/useAuth';
import type { User } from './types';
import styles from './styles.module.css';
```

```typescript
// After - 整理されたインポート順序
// 1. 外部ライブラリ
import React, { useState } from 'react';
import axios from 'axios';

// 2. 内部モジュール（絶対パス）
import { useAuth } from '@/hooks/useAuth';

// 3. 相対パス
import { Button } from './components/Button';

// 4. 型定義
import type { User } from './types';

// 5. スタイル
import styles from './styles.module.css';
```

---

## 11. フォーム処理 (Form Handling)

### 概要

フォームはユーザーとのインタラクションの重要な部分です。適切なバリデーション、エラー処理、ユーザーフィードバックを実装することが重要です。

### レビュー観点

- 制御コンポーネント vs 非制御コンポーネントの使い分けが適切か。
- バリデーションが適切に実装されているか。
- React 19のform actionsを活用しているか。
- エラーメッセージが明確でユーザーフレンドリーか。
- 送信中の状態が適切に管理されているか。

### 修正すべき理由の例

- **理由1:** フォームのバリデーションがサブミット時のみで、リアルタイムフィードバックがありません。
- **理由2:** 送信中のボタン状態が管理されておらず、重複送信の可能性があります。
- **理由3:** エラーメッセージが不明確で、ユーザーが問題を修正できません。

### 修正例

#### 例1: React 19のフォームアクション

```typescript
// Before - 従来のフォーム処理
function ContactForm() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const validate = () => {
    const newErrors: Record<string, string> = {};
    if (!name) newErrors.name = 'Name is required';
    if (!email) newErrors.email = 'Email is required';
    if (!message) newErrors.message = 'Message is required';
    return newErrors;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const newErrors = validate();
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }
    setIsSubmitting(true);
    try {
      await submitForm({ name, email, message });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      {/* フォームフィールド */}
    </form>
  );
}
```

```typescript
// After - React 19のアプローチ
import { useActionState } from 'react';

interface FormState {
  errors: Record<string, string>;
  success: boolean;
}

async function submitAction(
  prevState: FormState,
  formData: FormData
): Promise<FormState> {
  const name = formData.get('name') as string;
  const email = formData.get('email') as string;
  const message = formData.get('message') as string;

  const errors: Record<string, string> = {};

  if (!name) errors.name = 'Name is required';
  if (!email) errors.email = 'Email is required';
  else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    errors.email = 'Invalid email format';
  }
  if (!message) errors.message = 'Message is required';

  if (Object.keys(errors).length > 0) {
    return { errors, success: false };
  }

  await submitForm({ name, email, message });
  return { errors: {}, success: true };
}

function ContactForm() {
  const [state, formAction, isPending] = useActionState(submitAction, {
    errors: {},
    success: false,
  });

  if (state.success) {
    return <p>Thank you for your message!</p>;
  }

  return (
    <form action={formAction}>
      <div>
        <label htmlFor="name">Name</label>
        <input id="name" name="name" type="text" disabled={isPending} />
        {state.errors.name && (
          <span className="error">{state.errors.name}</span>
        )}
      </div>

      <div>
        <label htmlFor="email">Email</label>
        <input id="email" name="email" type="email" disabled={isPending} />
        {state.errors.email && (
          <span className="error">{state.errors.email}</span>
        )}
      </div>

      <div>
        <label htmlFor="message">Message</label>
        <textarea id="message" name="message" disabled={isPending} />
        {state.errors.message && (
          <span className="error">{state.errors.message}</span>
        )}
      </div>

      <button type="submit" disabled={isPending}>
        {isPending ? 'Sending...' : 'Send Message'}
      </button>
    </form>
  );
}
```

#### 例2: useOptimisticの活用

```typescript
// React 19のuseOptimisticを使用した楽観的更新
import { useOptimistic } from 'react';

interface Todo {
  id: string;
  text: string;
  completed: boolean;
}

function TodoList({ todos }: { todos: Todo[] }) {
  const [optimisticTodos, addOptimisticTodo] = useOptimistic(
    todos,
    (state, newTodo: Todo) => [...state, newTodo]
  );

  async function addTodo(formData: FormData) {
    const text = formData.get('text') as string;
    const optimisticTodo: Todo = {
      id: `temp-${Date.now()}`,
      text,
      completed: false,
    };

    addOptimisticTodo(optimisticTodo);

    // サーバーに送信
    await createTodo(text);
  }

  return (
    <div>
      <form action={addTodo}>
        <input name="text" type="text" placeholder="Add todo..." />
        <button type="submit">Add</button>
      </form>

      <ul>
        {optimisticTodos.map((todo) => (
          <li key={todo.id}>{todo.text}</li>
        ))}
      </ul>
    </div>
  );
}
```

---

## まとめ

このガイドラインは、TypeScript/Reactプロジェクトのコードレビューにおける主要な観点を網羅しています。以下の点を常に意識してください：

1. **型安全性**: TypeScriptの型システムを最大限活用する
2. **コンポーネント設計**: 単一責任の原則に従い、適切なサイズを維持する
3. **Hooks**: 正しい依存配列、カスタムHooksへの抽出
4. **状態管理**: ローカル/グローバル状態の適切な使い分け
5. **パフォーマンス**: 不要な再レンダリングの防止
6. **エラーハンドリング**: Error BoundariesとAsync/Awaitの適切な使用
7. **テスト**: ユーザー視点での振る舞いテスト
8. **アクセシビリティ**: セマンティックHTML、キーボードナビゲーション
9. **セキュリティ**: XSS対策、認証情報の安全な取り扱い
10. **コードスタイル**: 一貫した命名規則とフォーマット
11. **フォーム処理**: React 19の新機能を活用した効率的なフォーム実装

コードレビュー時は、これらの観点を参考に、具体的な改善提案を行ってください。
