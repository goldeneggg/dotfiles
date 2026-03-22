---
name: browser-ext-creator
description: |
  ブラウザ拡張機能の開発を支援するスキル。
  Chrome (Manifest V3) と Firefox に対応したブラウザ拡張を設計・実装する。
  以下の状況で使用:
    (1) ユーザーが「ブラウザ拡張を作って」「Chrome拡張を実装して」「Firefox拡張を開発して」と依頼した時
    (2) ユーザーが明示的に「/browser-ext-creator」を実行した時
    (3) 特定のウェブサイトの機能拡張や自動化を求められた時
    (4) content script、background script、popup UIなどの拡張機能コンポーネントの実装が必要な時
    (5) 「YouTubeの動画速度を変えるChrome拡張が欲しい」のようにサイト名+機能で拡張を依頼された時
    (6) 「GitHubのPRページにボタンを追加したい」のようにページ埋め込みUIを求められた時
    (7) 「ページ内のテキストを選択したらAPIに投げる拡張を作って」のように外部API連携を含む拡張を依頼された時
    (8) 「Tampermonkeyスクリプトを正式なChrome拡張にしたい」のように拡張への変換を求められた時
---

# Browser Extension Creator

ブラウザ拡張機能（Chrome Manifest V3 / Firefox）の設計・実装を支援するスキル。

### スコープ外

以下はこのスキルの対象外。依頼された場合はその旨を伝える:
- Chrome Web Store / Firefox Add-ons への公開手順・審査対応
- 拡張機能のユニットテスト・E2Eテスト構築
- CI/CD パイプライン構築
- Manifest V2 → V3 の移行作業（新規MV3実装は対応可）
- Safari Web Extensions（Xcode連携が必要なため）

## ワークフロー概要

```
1. 要件収集 → AskUserQuestion で機能仕様を確認
2. 設計     → プロジェクト構造とファイル構成を決定
3. 実装     → テンプレートをベースにコード生成
4. 自己評価 → セキュリティ・パフォーマンス観点で自己評価
```

## Degrees of Freedom

| ステップ | Freedom | 理由 |
|----------|---------|------|
| 要件収集 | **Low** | 確認項目は固定（機能概要・対象ブラウザ・動作対象サイト・UI要件・データ連携）。項目を飛ばさず順に確認する |
| 設計 | **Medium** | プロジェクト構造はテンプレートに準拠するが、不要コンポーネント（popup/options）の省略やディレクトリ追加はユーザー要件に応じて判断する |
| 実装 | **High** | ユーザーの機能要件に応じてコード内容を自由に設計する。テンプレートはベースとして利用するが、要件に合わせた大幅なカスタマイズを行ってよい |
| 自己評価 | **Low** | チェック項目は固定（要件準拠・MV3準拠・セキュリティ・パフォーマンスの4観点）。全項目を機械的に確認する |

## Step 1: 要件収集

AskUserQuestion ツールで以下を確認する：

### 必須項目

1. **機能概要**: 実装したい機能の全体像と目的
2. **機能要件リスト**: 実現したい機能を箇条書きで
3. **対象ブラウザ**: Chrome / Firefox / 両方
4. **動作対象サイト**: 機能が動作するURL（例: `https://www.youtube.com/watch*`）

### UI要件

- **ページ埋め込みUI**: 対象ページに追加するUI要素
- **ポップアップ**: 拡張アイコンクリックで表示するUI
- **設定ページ (Options)**: ユーザー設定用UI

### データ連携

- **外部API連携**: エンドポイント、リクエスト/レスポンス形式
- **データ保存**: `chrome.storage.sync` / `chrome.storage.local` の使用

## Step 2: 設計（プロジェクト構造の決定）

### 出力先ディレクトリ

ファイル生成前に、AskUserQuestion で出力先を確認する:

- **質問例**: 「拡張機能のファイルをどこに生成しますか？（例: `./my-extension/`）」
- **デフォルト**: カレントディレクトリ直下に `<拡張機能名のkebab-case>/` ディレクトリを作成
- **既存ディレクトリ指定時**: 空でなければ上書きリスクを警告し、承認を得てから生成する

両ブラウザ対応の場合は以下の構成:
```
<出力先>/
├── chrome/          # Chrome版
│   ├── manifest.json
│   └── ...
└── firefox/         # Firefox版
    ├── manifest.json
    └── ...
```

### Chrome (Manifest V3)

```
extension-name/
├── manifest.json           # 拡張機能の設定（Manifest V3）
├── content-script.js       # 対象ページに注入されるスクリプト
├── background.js           # Service Worker（バックグラウンド処理）
├── popup/
│   ├── popup.html          # ポップアップUI
│   ├── popup.css
│   └── popup.js
├── options/
│   ├── options.html        # 設定ページUI
│   ├── options.css
│   └── options.js
├── styles/
│   └── content.css         # ページ埋め込みスタイル
└── icons/
    ├── icon16.png
    ├── icon48.png
    └── icon128.png
```

### Firefox

Firefox はほぼ同じ構造だが、`manifest.json` に差異あり（`browser_specific_settings` が必要）。

## Step 3: 実装

### manifest.json

テンプレートをベースにユーザー要件に合わせてカスタマイズする:
- **Chrome**: `{このSKILL.mdのDIR}/assets/chrome-template/manifest.json` をコピーして編集
- **Firefox**: `{このSKILL.mdのDIR}/assets/firefox-template/manifest.json` をコピーして編集

カスタマイズ時の主なポイント:
- `name`, `description`: ユーザー指定の拡張名・説明に置換
- `permissions`: 要件に必要なもののみ（詳細は references/manifest-v3.md の permissions 一覧を参照）
- `host_permissions`: 動作対象サイトのURLパターンに変更
- `content_scripts.matches`: 同上
- 不要セクション（`action`, `options_ui` 等）は要件に応じて削除

### Content Script パターン

```javascript
// content-script.js
(() => {
  'use strict';

  // Wait for page load
  const init = () => {
    // Avoid duplicate initialization
    if (document.querySelector('#my-extension-container')) return;

    // Create UI element
    const container = document.createElement('div');
    container.id = 'my-extension-container';
    container.textContent = 'Extension Loaded';
    document.body.appendChild(container);
  };

  // Handle SPA navigation
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  // Observe URL changes for SPA
  let lastUrl = location.href;
  new MutationObserver(() => {
    if (location.href !== lastUrl) {
      lastUrl = location.href;
      init();
    }
  }).observe(document.body, { subtree: true, childList: true });
})();
```

### Background Script (Service Worker)

```javascript
// background.js
chrome.runtime.onInstalled.addListener(() => {
  console.log('Extension installed');
});

// Message handler
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'fetchData') {
    fetchData(request.url)
      .then(data => sendResponse({ success: true, data }))
      .catch(error => sendResponse({ success: false, error: error.message }));
    return true; // Keep message channel open for async response
  }
});

const fetchData = async (url) => {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
};
```

### Storage API

```javascript
// Save settings
const saveSettings = async (settings) => {
  await chrome.storage.sync.set(settings);
};

// Load settings
const loadSettings = async () => {
  return chrome.storage.sync.get({
    // Default values
    apiKey: '',
    enabled: true
  });
};
```

## Step 4: 自己評価

生成したコードを以下の観点で評価：

### 要件準拠

- [ ] すべての機能要件を満たしているか
- [ ] 指定されたサイトで正しく動作するか

### Manifest V3 準拠

- [ ] `manifest_version: 3` を使用
- [ ] Service Worker を background script として使用
- [ ] `host_permissions` で必要なドメインのみ許可
- [ ] 動的コード実行（`eval`, `new Function`）を使用していない

### セキュリティ

- [ ] XSS防止: `textContent` 使用 or DOMPurify でサニタイズ
- [ ] 最小権限の原則: 必要最小限の permissions のみ要求
- [ ] 外部通信: 必要最小限のエンドポイントのみ
- [ ] ユーザー入力のバリデーション実施

### パフォーマンス

- [ ] 不要な DOM 操作を避けている
- [ ] MutationObserver の監視範囲が適切
- [ ] メモリリークを防止している

## エラーハンドリング

### 要件不足・不明確な場合

ユーザーの回答が曖昧、または必須項目が不足している場合:
1. 不足している具体的な項目を明示して AskUserQuestion で再確認する
2. 推測で進めない。「対象ブラウザが未指定のためChromeのみで進めます」のような仮決定もユーザーの承認を得てから実行する

### 非対応パターンを要求された場合

以下のケースではスキルの対象外であることを伝え、代替案を提示する:
- **Manifest V2**: 「MV3のみ対応です。MV2→MV3移行ガイドを参照してください」と案内
- **Safari Web Extensions**: 「このスキルはChrome/Firefox対応です。Safari固有のXcode連携は対象外です」と案内
- **Electron / Tauri**: 「ブラウザ拡張ではなくデスクトップアプリの領域です」と案内

### 自己評価で問題が検出された場合

Step 4のチェックリストで ❌ が見つかった場合:
1. 問題箇所と理由をユーザーに報告する
2. 修正案を提示し、承認を得てからコードを修正する
3. 修正後、該当チェック項目を再評価する

### テンプレートが要件に合わない場合

テンプレートの構造がユーザー要件と大きく乖離する場合（例: popup不要、options不要、複数content script が必要）:
1. テンプレートから必要な部分のみ抽出して使用する
2. 不要ファイルは生成しない
3. manifest.json の該当セクション（`action`, `options_ui` 等）も省略する

## コーディング規約

| 項目 | 規約 |
|------|------|
| ファイル名 | ケバブケース（例: `content-script.js`） |
| 変数名 | キャメルケース（例: `selectedElement`） |
| 関数 | アロー関数を優先 |
| エラー処理 | try-catch で適切に例外処理 |

## リファレンス

| 資料 | パス | 用途 | 参照頻度 |
|------|------|------|----------|
| Manifest V3 詳細 | `{このSKILL.mdのDIR}/references/manifest-v3.md` | Chrome/Firefox差異の確認、permissions選定、Content Script/Background Scriptの実装パターン | **毎回** — Step 2-3で必ず参照 |
| セキュリティガイド | `{このSKILL.mdのDIR}/references/security.md` | XSS防止、CSP設定、API通信・ストレージのセキュリティ確認 | **時々** — 外部API連携やユーザー入力を扱う場合にStep 3-4で参照 |
| トリガーテスト | `{このSKILL.mdのDIR}/references/trigger-tests.md` | description改善時の回帰テスト用。正常系8例・異常系5例・境界3例 | **保守時のみ** — スキルのdescription変更時に参照 |

## テンプレート

プロジェクトテンプレート：

- **Chrome**: {このSKILL.mdのDIR}/assets/chrome-template
- **Firefox**: {このSKILL.mdのDIR}/assets/firefox-template
