---
name: browser-ext-creator
description: Chrome Manifest V3とFirefox向けブラウザ拡張を設計・実装する。content script、background、popup、ページ埋め込みUI、外部API連携、Tampermonkeyからの変換を扱う。Safari、MV2移行、ストア公開は対象外。
---

# Browser Extension Creator

## 対象と完了条件

機能要件を受け取り、指定ブラウザ向けの拡張ファイルを作成・修正する。
実装、要件・権限・構文の検証、利用可能な環境での動作確認まで進める。
テスト基盤の新設、CI/CD構築、ストア公開・審査は対象外とする。

## 手順

1. 会話と既存プロジェクトから、機能、対象ブラウザ、対象サイト、UI、API・保存要件、配置先を整理する。既知情報は再質問しない。対象ブラウザや権限範囲など結果を大きく変える不足だけ確認する。
2. `references/manifest-v3.md` の対象ブラウザに関係する節を読む。外部通信・ユーザー入力・保存を扱う場合は `references/security.md` も読む。
3. 既存構成を優先し、必要なmanifest、content script、background、popup、options、style、iconだけを用意する。新規両ブラウザ構成はchrome/とfirefox/を基本とする。
4. `assets/chrome-template/` または `assets/firefox-template/` を基に、要件に合わせて実装する。既存ファイルを読む。無関係なファイルを上書きしない。
5. 以下の検証を実施し、対象内の不備は再承認を待たず修正する。
6. 生成物、導入方法、検証結果、ブラウザごとの未確認事項を報告する。

## 実装基準

- permissions、host_permissions、content_scripts.matchesを必要範囲に限定する。
- backgroundの方式とAPI対応は対象ブラウザの仕様で判断し、共通チェックを無条件に適用しない。
- 動的コード実行を避け、DOM挿入・入力・メッセージ・外部通信の信頼境界を確認する。
- SPA対応やMutationObserverは必要な場合だけ実装し、監視範囲・重複初期化・解放を検討する。
- ファイル名はkebab-case、変数・関数はcamelCaseを基本とし、既存規約を尊重する。

## 検証

manifestの構文、参照ファイルの存在、対象URL、権限、ブラウザ別background、入力検証、CSP、外部通信、資源解放を確認する。
既存のlint・build・テストがあれば変更に応じて実行する。
実ブラウザで確認可能なら主要機能を確認し、不能なら静的確認と区別する。
自己評価で見つけた要件内の不備は修正して該当項目を再検証する。

## 保守と例外

descriptionを変更する場合は `references/trigger-tests.md` の正常・対象外・境界例と照合する。
テンプレートが合わなければ必要な部分だけ利用する。
非対応の依頼や要件変更が必要な場合は、対象外の理由と必要な判断を示す。
