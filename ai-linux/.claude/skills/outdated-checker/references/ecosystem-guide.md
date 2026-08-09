# エコシステム別調査ガイド

対象プロジェクトで検出したセクションだけを使う。コマンドを実行する前に、リポジトリの指示、利用中のパッケージマネージャー、workspace構成を確認する。コマンド名や挙動は現行の公式ドキュメントで確認する。

## JavaScript / TypeScript

- 検出: `package.json`、npm・Yarn・pnpm・Bunのlockfile、workspace定義、`engines`、`packageManager`
- 照会: 利用中マネージャーのoutdated/info系コマンドとnpm registry
- 更新: 利用中マネージャーのlatest更新機能を使い、manifestとlockfileを同期
- 注意: peer dependencies、Node.js要件、workspace間依存、lockfile形式、ESM/CJS移行、postinstallを確認

## Go

- 検出: `go.mod`、`go.work`、`go.sum`、`toolchain`、`replace`、tool依存
- 照会: `go list -m -u all`、Go module proxy、pkg.go.dev、公式リポジトリ
- 更新: 対象moduleを `go get <module>@latest` で更新し、`go mod tidy` を実行
- 注意: `/v2` 以降のmodule path、`replace`、撤回済みversion、Go最小version、生成コードを確認

## Python

- 検出: `pyproject.toml`、requirements系ファイル、`Pipfile.lock`、`poetry.lock`、`uv.lock`、環境・Python version定義
- 照会: 利用中マネージャーのoutdated機能、PyPI、公式リリース
- 更新: uv、Poetry、Pipenv、pip-toolsなど、検出した管理方式で制約とlockを同期
- 注意: Python要件、extras、環境marker、ビルドbackend、ABI、依存解決の競合を確認

## Ruby

- 検出: `Gemfile`、`Gemfile.lock`、gemspec、Ruby version定義
- 照会: `bundle outdated`、RubyGems、公式リリース
- 更新: Bundlerでmanifest制約とlockfileを同期
- 注意: Ruby/Rails要件、native extension、Bundler version、複数sourceを確認

## Rust

- 検出: `Cargo.toml`、`Cargo.lock`、workspace、`rust-toolchain.toml`
- 照会: crates.io、公式リポジトリ。利用可能ならcargoのoutdated系ツールも使用
- 更新: manifestの制約を最新安定版に更新してからlockfileを再解決
- 注意: Cargo feature、MSRV、edition、build script、yanked releaseを確認。`cargo update` だけではmanifest制約を更新できない場合がある

## JVM / Kotlin

- 検出: Mavenの`pom.xml`、Gradle build、version catalog、wrapper、plugin定義、JDK version
- 照会: Maven Central、Gradle Plugin Portal、公式リリース、利用可能なdependency update task
- 更新: property、catalog、plugin、wrapperをそれぞれの管理元で更新
- 注意: Java toolchain、Gradle/Maven plugin互換性、Jakarta移行、Kotlin compiler/plugin整合を確認

## .NET

- 検出: `*.csproj`、`*.fsproj`、`Directory.Packages.props`、`packages.lock.json`、`global.json`、tool manifest
- 照会: `dotnet list package --outdated` 相当の現行コマンド、NuGet、公式リリース
- 更新: `dotnet` CLIで中央管理とlockfileを含めて同期
- 注意: target framework、SDK workload、analyzer、source generator、中央package管理を確認

## PHP

- 検出: `composer.json`、`composer.lock`、PHP version制約
- 照会: `composer outdated`、Packagist、公式リリース
- 更新: Composerで制約とlockfileを同期
- 注意: PHP extension、platform設定、framework major、Composer plugin互換性を確認

## Terraform

- 検出: `required_version`、`required_providers`、module source/version、`.terraform.lock.hcl`
- 照会: Terraform Registry、provider/moduleの公式リリース
- 更新: 制約を更新し、`terraform init -upgrade` でlockfileを同期
- 注意: provider schema、state migration、module入力・出力、Terraform CLI互換性を確認。planなしで互換と断定しない

## Docker / コンテナ

- 検出: Dockerfileの`FROM`、Compose・Kubernetes・Helm内のimage、devcontainer、CI service image
- 照会: 公式registry、Official Images、vendorの公式リリース
- 更新: tagまたはdigestと、必要なOS package・設定・healthcheckを更新
- 注意: `latest`など可変tagは固定版とみなさない。OS、ランタイム、DBのmajor更新ではデータ形式、初期化、volume、アーキテクチャを確認

## GitHub Actions / CI

- 検出: `.github/workflows/**/*.{yml,yaml}`、composite action、reusable workflow内の `uses:`。ローカルactionとDocker参照を区別
- 照会: action公式リポジトリのrelease、Marketplace、公式移行ガイド
- 更新: リポジトリのpin方針に従い、major tag、完全tag、commit SHAを更新。SHA pinでは対応するreleaseを注記
- 注意: Node runtimeの移行、入力名・権限・出力の変更、runner image、廃止commandを確認

## ランタイムとその他のCLI

- 検出: `.tool-versions`、mise/asdf設定、`.node-version`、`.python-version`、`.ruby-version`、Go/Rust/JDK設定、Makefile、Taskfile、CI setup action、インストールスクリプト
- 照会: vendorの公式リリース、version manager pluginの公式情報、公式サポート表
- 更新: 同一versionを参照する設定をまとめて更新し、生成ファイルやtool cache定義も同期
- 注意: major更新ではEOL、plugin/API互換性、標準ライブラリ、コンパイラ警告、出力形式を確認

## 共通の除外と例外

- ローカルpath、workspace内package、プロジェクト自身のversionは外部最新版比較から除外する。
- Git branch、commit、可変tagを使う依存は、対応する公式releaseを特定できる場合だけ比較する。
- fork、private registry、社内mirrorは公開upstreamと同一視しない。アクセス可能な正規sourceを確認する。
- DependabotやRenovateの設定は検出範囲と更新方針の補助情報として使い、それ自体を依存versionとして数えない。
- lockfile内の推移的依存は、パッケージマネージャーのoutdated判定で直接更新可能な対象と区別する。
