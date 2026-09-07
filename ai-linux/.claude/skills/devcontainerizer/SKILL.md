---
name: devcontainerizer
description: リポジトリと既存Docker資産を調べ、Dev Containers構成の設計・生成または導入計画を作成する。導入価値の評価はtech-fit-analyzer、リポジトリ理解はrepos-onboarderを使う。
---

# Devcontainerizer

## モード

構成の作成・導入依頼は実施モード、計画のみの依頼は計画モードとする。
会話から明確なモードや対象範囲を再確認しない。

## 調査

Dockerfile、Compose、.dockerignore、既存.devcontainer、README、開発コマンド、CI、マニフェストを読む。
本番と開発でのDocker利用、および単一アプリ・モノレポとDocker/Compose配置を整理する。
広い独立調査は必要に応じて委譲し、分類・根拠・不明点を受け取る。

## 設計

既存の開発Composeは再利用し、開発差分はoverrideまたはdevcontainer側に置く。
本番Dockerfileの流用は開発に適したstageがあるか確認して判断する。
Docker未使用でミドルウェア不要ならimage＋Featuresを基本とし、必要なサービスがある場合にComposeを使う。

モノレポの複数Docker/Compose構成は `references/monorepo-devcontainerize-practice.md` を読む。
フィールド、Features、雛形、検証は `references/devcontainer-building-blocks.md` の関連節を読む。
対象サービスや接続先など、設計を大きく変える未確定事項だけ確認する。

## 生成

実施モードでは、必要なdevcontainer.json、開発用override、必要ならDockerfileを生成する。
既存ファイルを読み、通常の開発起動とユーザー変更を保持する。
非自明なmount、context、targetには理由を記す。

計画モードではDEVCONTAINER_PLAN.mdへ現状、方針、構成、導入手順、注意点、検証方法、未決事項を記載する。
指定された出力先を優先する。

## 検証と報告

実施モードでは、利用可能な構文検査、参照パス確認、Composeの構成解決を実行する。
コンテナ起動はlifecycle処理、mount、接続先を確認し、依頼で許可された環境・操作の範囲で行う。
起動できない場合は理由と未検証事項を明示し、具体的な起動・接続確認手順を示す。

計画モードでは計画と参照先の整合性を確認し、起動しない。
生成物または計画、実施した検証、残課題を報告する。
