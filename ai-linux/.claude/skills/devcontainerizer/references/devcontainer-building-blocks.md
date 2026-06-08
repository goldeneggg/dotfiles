# Dev Container 構成部品リファレンス

単一アプリ・ゼロ構築（Docker 皆無）を中心に、`.devcontainer/` を組み立てる際の構成部品・雛形・判断材料をまとめる。モノレポ特有の論点は `monorepo-devcontainerize-practice.md` を参照。

## 目次

1. [起点の3択: image / Dockerfile / compose](#1-起点の3択-image--dockerfile--compose)
2. [devcontainer.json の主要フィールド](#2-devcontainerjson-の主要フィールド)
3. [Dev Container Features](#3-dev-container-features)
4. [雛形: パターン別](#4-雛形-パターン別)
5. [既存 Dockerfile の流用（A-2）](#5-既存-dockerfile-の流用a-2)
6. [検証コマンド](#6-検証コマンド)
7. [よくある落とし穴](#7-よくある落とし穴)

---

## 1. 起点の3択: image / Dockerfile / compose

devcontainer の土台は 3 通り。**シンプルな方から選ぶ**のが鉄則。

| 起点 | 使う場面 | 備考 |
|---|---|---|
| `image` | 単一コンテナで足り、依存も Features で賄える | 最速・最小。Docker 皆無の小規模はまずこれ |
| `build`(Dockerfile) | OS パッケージ等の独自セットアップが必要だが単一コンテナ | `image` で足りなければ昇格 |
| `dockerComposeFile` | DB/Redis 等の付随サービスが要る、または既存 compose がある | 複数サービス連携はこれ一択 |

判断の流れ: **付随サービス（DB等）が要る？ → Yes なら compose / No なら、独自 OS セットアップが要る？ → Yes なら Dockerfile / No なら image。**

---

## 2. devcontainer.json の主要フィールド

```jsonc
{
  // 起点（いずれか1つ）
  "image": "mcr.microsoft.com/devcontainers/javascript-node:20",
  // "build": { "dockerfile": "Dockerfile", "context": ".." },
  // "dockerComposeFile": ["../compose.yaml", "../compose.devcontainer.yaml"],

  "name": "My App Dev",

  // compose 起点の時に必須: 接続先サービスと作業ディレクトリ
  // "service": "app",
  // "workspaceFolder": "/workspace",

  // 追加ランタイム/CLI は Features で宣言的に
  "features": {
    "ghcr.io/devcontainers/features/github-cli:1": {}
  },

  // VS Code 拡張・設定（コンテナ内に適用）
  "customizations": {
    "vscode": {
      "extensions": ["dbaeumer.vscode-eslint"],
      "settings": {}
    }
  },

  // 公開ポート（フォワード）
  "forwardPorts": [3000],

  // セットアップフック（タイミング別）
  "onCreateCommand": "",        // コンテナ作成時に1回（イメージ非依存の準備）
  "postCreateCommand": "npm ci", // 作成後1回（依存インストール等）
  "postStartCommand": "",        // 起動ごと

  // 権限を持たない一般ユーザーで作業（推奨）
  "remoteUser": "node",

  // compose 利用時、VS Code を閉じてもコンテナを残す
  "shutdownAction": "none"
}
```

ポイント:
- `postCreateCommand` は依存インストールの定位置。イメージに焼かずここに置くと、依存変更時の差分が分かりやすい。
- `remoteUser` を非 root にしておくと、生成ファイルの所有権トラブルを避けやすい。
- compose 起点では `service` と `workspaceFolder` が要。`workspaceFolder` は compose のマウント先（例 `/workspace`）と整合させる。

---

## 3. Dev Container Features

Features は「言語ランタイム・CLI ツールを宣言的に追加する」再利用部品。Dockerfile に手で書く代わりに `features` で足すと、可搬性が高く保守しやすい。

よく使うもの（`ghcr.io/devcontainers/features/...`）:

| Feature | 用途 |
|---|---|
| `common-utils` | zsh/oh-my-zsh・非rootユーザー・基本ツール |
| `git` | 新しめの git |
| `github-cli` | `gh` |
| `node` / `python` / `go` / `ruby` / `rust` | 各言語ランタイム |
| `docker-in-docker` / `docker-outside-of-docker` | コンテナ内から docker を使う |

ベースイメージ（`mcr.microsoft.com/devcontainers/<lang>`）に主要ランタイムが入っているなら、Features は補助ツールだけに絞る。

---

## 4. 雛形: パターン別

### 4-1. 単一アプリ・image 起点（最小・Docker 皆無の出発点）

`.devcontainer/devcontainer.json`:

```jsonc
{
  "name": "App Dev",
  "image": "mcr.microsoft.com/devcontainers/javascript-node:20",
  "features": {
    "ghcr.io/devcontainers/features/github-cli:1": {}
  },
  "forwardPorts": [3000],
  "postCreateCommand": "npm ci",
  "customizations": {
    "vscode": { "extensions": ["dbaeumer.vscode-eslint"] }
  },
  "remoteUser": "node"
}
```

### 4-2. 単一アプリ・Dockerfile 起点

`.devcontainer/devcontainer.json`:

```jsonc
{
  "name": "App Dev",
  "build": { "dockerfile": "Dockerfile", "context": ".." },
  "postCreateCommand": "make setup",
  "remoteUser": "vscode"
}
```

`.devcontainer/Dockerfile`:

```dockerfile
FROM mcr.microsoft.com/devcontainers/base:ubuntu
# 独自の OS パッケージ等。言語ランタイムは Features 併用が楽
RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential \
    && rm -rf /var/lib/apt/lists/*
```

### 4-3. 単一アプリ・compose 起点（DB 等の付随サービスが必要）

`.devcontainer/devcontainer.json`:

```jsonc
{
  "name": "App Dev",
  "dockerComposeFile": ["../compose.yaml", "../compose.devcontainer.yaml"],
  "service": "app",
  "workspaceFolder": "/workspace",
  "forwardPorts": [3000, 5432],
  "postCreateCommand": "npm ci",
  "shutdownAction": "none"
}
```

`compose.yaml`（本番/標準。app と db）:

```yaml
services:
  app:
    build: .
    depends_on: [db]
  db:
    image: postgres:16
    environment:
      POSTGRES_PASSWORD: dev
```

`compose.devcontainer.yaml`（開発差分の override。ソースをマウントし常駐させる）:

```yaml
services:
  app:
    volumes:
      - .:/workspace:cached
    command: sleep infinity
```

> 既存 compose があるなら（A-1）、それを書き換えず `compose.devcontainer.yaml` に差分だけ足して配列で重ねるのが安全。

---

## 5. 既存 Dockerfile の流用（A-2）

本番用 `Dockerfile` がマルチステージなら、開発用ステージ（`target`）を流用して二重管理を避ける。

```dockerfile
# 本番 Dockerfile（抜粋）
FROM node:20 AS base
WORKDIR /app
COPY package*.json ./
RUN npm ci

FROM base AS dev          # ← 開発用ステージ
# devDependencies 込み・ソースは compose でマウント

FROM base AS prod
COPY . .
RUN npm run build
```

開発用 compose で `build.target: dev` を指定:

```yaml
services:
  app:
    build:
      context: .
      target: dev
    volumes:
      - .:/workspace:cached
    command: sleep infinity
```

本番 Dockerfile に dev ステージが無い場合は、まず dev ステージを足す（本番ステージは触らない）か、`.devcontainer/Dockerfile` を別途用意する。どちらにするかはユーザーに確認する。

---

## 6. 検証コマンド

```sh
# compose の妥当性（include 解決・相対パス・サービス名衝突を検出）
docker compose -f compose.yaml -f compose.devcontainer.yaml config

# devcontainer CLI があれば実起動まで検証
devcontainer up --workspace-folder .
devcontainer exec --workspace-folder . bash -lc 'echo OK && pwd'
```

VS Code 手動確認: コマンドパレット →「Dev Containers: Reopen in Container」。

---

## 7. よくある落とし穴

- **`workspaceFolder` と compose のマウント先の不一致** — `volumes: .:/workspace` なら `workspaceFolder` も `/workspace` 配下に揃える。
- **`postCreateCommand` の重さ** — ビルドまで入れると毎回遅い。重い処理はイメージ側 or `onCreateCommand` に寄せる。
- **root で作業して所有権が壊れる** — `remoteUser` を非 root に。
- **既存 compose の直接改変** — 開発差分は override ファイルに分離し、本番定義を汚さない。
- **ポートの閉じ込め** — アプリのリッスンポートを `forwardPorts` に入れ忘れるとブラウザから届かない。
