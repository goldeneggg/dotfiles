# 技術スタック検出リファレンス

設定ファイルからプロジェクトの技術スタックを素早く特定するための対応表。
リポジトリ分析時に参照する。

## 設定ファイル → スタック対応表

| ファイル                 | スタック / エコシステム          | 確認すべきフィールド                     |
|------------------------|---------------------------------|----------------------------------------|
| `package.json`         | Node.js / JavaScript / TS       | dependencies, devDependencies, engines |
| `tsconfig.json`        | TypeScript                      | compilerOptions.target, lib, strict    |
| `Cargo.toml`           | Rust                            | dependencies, edition, features        |
| `go.mod`               | Go                              | go version, require ブロック            |
| `pyproject.toml`       | Python（モダン）                 | project.dependencies, tool.* セクション |
| `requirements.txt`     | Python（レガシー）               | ピン留めされたバージョン                 |
| `Pipfile`              | Python（pipenv）                | packages, dev-packages                 |
| `Gemfile`              | Ruby                            | gem 宣言, ruby バージョン               |
| `build.gradle(.kts)`   | Java / Kotlin（Gradle）         | dependencies, plugins                  |
| `pom.xml`              | Java（Maven）                   | dependencies, parent, modules          |
| `composer.json`        | PHP                             | require, autoload                      |
| `mix.exs`              | Elixir                          | deps 関数                              |
| `pubspec.yaml`         | Dart / Flutter                  | dependencies, environment              |
| `.csproj`              | C# / .NET                       | PackageReference, TargetFramework      |
| `CMakeLists.txt`       | C / C++                         | cmake_minimum_required, find_package   |
| `deno.json`            | Deno                            | imports, tasks                         |
| `bun.lockb`            | Bun                             | 存在自体がBunランタイムを示す            |

## フレームワーク検出（JavaScript/TypeScript）

| 依存パッケージ名          | フレームワーク      |
|--------------------------|-------------------|
| `react`, `react-dom`    | React             |
| `next`                   | Next.js           |
| `vue`                    | Vue.js            |
| `nuxt`                   | Nuxt              |
| `@angular/core`         | Angular           |
| `svelte`                 | Svelte            |
| `astro`                  | Astro             |
| `express`                | Express.js        |
| `fastify`                | Fastify           |
| `hono`                   | Hono              |
| `@nestjs/core`          | NestJS            |

## ビルドツール検出

| 手がかり                           | ビルドツール       |
|-----------------------------------|-------------------|
| `vite.config.*`                   | Vite              |
| `webpack.config.*`                | Webpack           |
| `rollup.config.*`                 | Rollup            |
| `esbuild`（deps/scripts内）       | esbuild           |
| `turbo.json`                      | Turborepo         |
| `nx.json`                         | Nx                |
| `.swcrc`                          | SWC               |
| `tsup`（deps内）                  | tsup              |

## CI/CD 検出

| ファイル / ディレクトリ             | CIシステム                |
|-----------------------------------|--------------------------|
| `.github/workflows/*.yml`         | GitHub Actions           |
| `.gitlab-ci.yml`                  | GitLab CI                |
| `Jenkinsfile`                     | Jenkins                  |
| `.circleci/config.yml`            | CircleCI                 |
| `.travis.yml`                     | Travis CI                |
| `bitbucket-pipelines.yml`         | Bitbucket Pipelines      |
| `.buildkite/pipeline.yml`         | Buildkite                |

## テストフレームワーク検出

| 手がかり                           | テストフレームワーク  |
|-----------------------------------|---------------------|
| `jest.config.*`, `jest`（deps内） | Jest                |
| `vitest`（deps内）                | Vitest              |
| `@playwright/test`                | Playwright          |
| `cypress`（deps内）               | Cypress             |
| `pytest`（deps内）, `conftest.py` | pytest              |
| `rspec`（Gemfile内）              | RSpec               |
| `#[cfg(test)]`（.rsファイル内）    | Rust組み込みテスト    |
| `_test.go` ファイル接尾辞          | Go組み込みテスト      |
