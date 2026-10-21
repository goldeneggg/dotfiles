# モノレポへの Dev Containers 導入プラクティス

複数の Docker 稼働アプリを内包するモノレポに Dev Containers を導入し、開発環境を Docker 化するための構成・ベストプラクティスをまとめる。

---

## 1. 基本方針

複数の Docker 稼働アプリを持つモノレポでは、**単一の `docker-compose.yml` を用意し、各サービス用に分割した `devcontainer.json` をそれぞれ作成して共通の compose を参照させる**のが VS Code 公式の推奨構成。

- VS Code は 1 ウィンドウから 1 コンテナにしか接続できないが、複数ウィンドウを立ち上げて別々のコンテナにアタッチできる。単一ウィンドウ内でも `Dev Containers: Switch Container` でコンテナを切り替えられる。
- モノレポの利点（同一リポ内の複数プロダクトにアクセスできること）を活かすため、リポジトリ全体がコンテナ内で利用可能であることが重要。ルートを `/workspace` にマウントしつつ `workspaceFolder` で各アプリを指す構成でこれを実現する。

---

## 2. 標準構成（各アプリに専用 compose が無い場合）

### ディレクトリ構成

```
📁 repo-root
  📁 .git
  📁 .devcontainer
    📁 app-a
      📄 devcontainer.json
    📁 app-b
      📄 devcontainer.json
  📁 apps
    📁 app-a
      📄 Dockerfile        ← アプリのソースと同じ場所
    📁 app-b
      📄 Dockerfile
  📁 packages              ← 共有ライブラリ
  📄 docker-compose.yml    ← ルートに統合用を 1 つ
```

`.git` フォルダの位置が重要。ソース管理が正しく動作するよう、コンテナがこのパスを参照できる必要がある。

### docker-compose.yml（ルート）

ポイントは 2 つ。

1. **全サービスのビルドコンテキストをリポジトリのルートにする** → 共有パッケージ（`packages/`）をビルド時に `COPY` で参照できる。コンテキストをアプリ配下にすると外側の `packages/` を `COPY` できない。
2. **各サービスで `.git` を含むルートフォルダを `/workspace` にマウントする**。

```yaml
services:
  app-a:
    build:
      context: .                      # ルート（共有パッケージ参照のため）
      dockerfile: apps/app-a/Dockerfile
    volumes:
      - .:/workspace
    command: sleep infinity

  app-b:
    build:
      context: .
      dockerfile: apps/app-b/Dockerfile
    volumes:
      - .:/workspace
    command: sleep infinity
```

### devcontainer.json（サービスごと）

共通 compose を指しつつ、`service` と `workspaceFolder` だけを変える。

```jsonc
{
  "name": "App A Container",
  "dockerComposeFile": ["../../docker-compose.yml"],
  "service": "app-a",
  "workspaceFolder": "/workspace/apps/app-a",
  "shutdownAction": "none"
}
```

- `shutdownAction: "none"` は任意だが、VS Code を閉じてもコンテナを起動したまま残し、片方のウィンドウを閉じて両コンテナを誤って停止させる事故を防ぐ。
- 複数 compose を列挙する場合は、**すべての `devcontainer.json` で参照ファイルのリストを揃える**こと。devcontainer ごとに違うファイルを参照すると予期しない結果になる。

### ファイル置き場所の対応

| ファイル | 置き場所 |
|---|---|
| `devcontainer.json` | `.devcontainer/<app>/` |
| `Dockerfile` | `apps/<app>/`（アプリのソースと同じ場所） |
| `docker-compose.yml` | リポジトリのルート |

> 技術スタックが全アプリで統一されているなら、単一 Dockerfile をルートに置きエントリポイントだけ変える手もある（Nx 等）。アプリごとに言語やランタイムが違うならアプリ別 Dockerfile が素直。

---

## 3. 各アプリが自前 compose を持つ場合（本命：`include`）

「アプリ単体でも `docker compose up` で動かしたい」という要求から、各アプリが自前 compose を持つケースは現実によくある。この場合は **ルート compose で各アプリ compose を `include` する**。

### なぜ `include` なのか

Compose はビルドコンテキスト・env ファイルの場所・バインドマウントのパスなど多くのリソースで相対パスを使う。このため、別ディレクトリの compose を素朴に `-f` でマージすると、相対パスが作者の意図ではなくローカルの作業ディレクトリから解決され、アプリが期待どおり動かない。

`include` はこれを解決するために導入された。include された compose ファイルを丸ごとコピー&ペーストしたかのように取り込みつつ、**相対パス参照を管理し、元の場所を基準に解釈する**。これにより各アプリの compose を一切書き換えずに束ねられる。

- 依存が明示的になり、フラグ追加なしに `docker compose up` だけで全体起動できる。
- `extends`（単一サービスの共有・内部詳細の把握が前提）と違い、他チームの設定を「ブラックボックス」として再利用できる。

### 構成

```
📁 repo-root
  📁 .devcontainer
    📁 app-a/devcontainer.json
    📁 app-b/devcontainer.json
  📁 apps
    📁 app-a
      📄 compose.yaml      ← 単体起動用。書き換えない
      📄 Dockerfile
    📁 app-b
      📄 compose.yaml
      📄 Dockerfile
  📄 compose.yaml          ← 統合用
```

```yaml
# ルート compose.yaml
include:
  - apps/app-a/compose.yaml
  - apps/app-b/compose.yaml
```

これで「`cd apps/app-a && docker compose up`（単体開発）」と「ルートでの全体起動」が両立する。アプリ開発者の単体起動体験を壊さないのが、モノレポで最も重要な性質。

---

## 4. 落とし穴と対策

### サービス名・プロジェクト名の衝突

複数アプリが同じサービス名（典型的には `db` / `web` / `redis`）を持つと、`include` で束ねた際に衝突する。Compose のバージョンによっては公式例どおりの構成でも `... conflicts with imported resource` が出ることがある。

**対策:** 各アプリ内のサービス名をアプリ名でプレフィックスして名前空間化する（`app-a-db`, `app-b-db` など）。

### プロジェクト名によるリソース分離

Compose はプロジェクト名（デフォルトはディレクトリ名）を全リソースのプレフィックスにする。似た構造や同じフォルダ名のプロジェクトが複数あると、同名リソースが作られ、誤った DB への接続・無関係なアプリ間のボリューム共有・追跡困難なポート衝突が起きる。

**対策:** 各アプリ compose のトップレベルに `name:` を明示するか、devcontainer 側でプロジェクト名を固定する（VS Code の "Set Docker Compose project name" 設定）。

### include される側はポータブルに保つ

再利用される側の compose は環境非依存に保つほど堅牢。ホスト固有の開発設定（バインドマウント等）は include する側で重ねる、という分離意識を持つ。

### 開発専用の差分は override で重ねる

本番ビルド定義（各アプリ compose）と、開発時のバインドマウントや dev コマンドは分離する。開発設定は `compose.override.yaml` / `compose.devcontainer.yaml` に切り出し、`devcontainer.json` の `dockerComposeFile` 配列で重ねる。

```jsonc
{
  "dockerComposeFile": [
    "../../compose.yaml",
    "../../compose.devcontainer.yaml"
  ],
  "service": "app-a",
  "workspaceFolder": "/workspace/apps/app-a"
}
```

```yaml
# compose.override.yaml（開発オーバーライドの例）
services:
  app-a:
    build:
      target: base
    command: npm run dev --workspace=apps/app-a
    volumes:
      - ./apps/app-a/src:/workspace/apps/app-a/src
      - ./packages:/workspace/packages
```

---

## 5. アンチパターン

- **素朴な `-f` マージ**: `docker compose -f apps/app-a/compose.yaml -f apps/app-b/compose.yaml` のように別ディレクトリの compose を直接重ねると、相対パスが破綻する。各アプリが自前 compose を持つケースでは原則 `include` を使う。
- **ビルドコンテキストをアプリ配下に限定**: 共有パッケージを `COPY` できなくなる。コンテキストはルート、`dockerfile` でパス指定が基本。
- **同名サービスを放置**: 名前空間化せずに `include` すると衝突する。

---

## 6. 判断早見表

### 構成パターン

| 状況 | 推奨 |
|---|---|
| サービス間連携・共有パッケージがある | 単一 compose + サービス別 devcontainer |
| アプリ間が疎結合で別々に開発 | アプリ別に完全独立した `.devcontainer` |
| 技術スタックが揃っている | 単一 Dockerfile でエントリポイントだけ変える |
| 各アプリが自前 compose を持つ | ルート compose で `include`（本命） |

### compose 合成手段

| 状況 | 推奨 |
|---|---|
| 各アプリ compose を単体でも動かす・内部を知らず再利用 | `include` |
| 単一サービスだけ共有・内部も把握 | `extends` |
| 開発専用の差分（マウント・dev コマンド）を重ねる | `-f` で override ファイル追加 |
| 複数アプリで同名サービスがある | サービス名をアプリ名でプレフィックス + `name:` 明示 |

---

## 7. チェックリスト

- [ ] `.git` がコンテナから見える位置にあり、ルートを `/workspace` にマウントしている
- [ ] ビルドコンテキストはルート、`dockerfile` でパス指定している
- [ ] 各アプリ compose を `include` で束ねている（自前 compose を持つ場合）
- [ ] サービス名を名前空間化し、衝突を回避している
- [ ] プロジェクト名（`name:`）を明示し、リソースを分離している
- [ ] 開発差分は override に切り出し、`dockerComposeFile` 配列で重ねている
- [ ] 全 `devcontainer.json` で `dockerComposeFile` のリストが揃っている
- [ ] `shutdownAction` を必要に応じて設定している
