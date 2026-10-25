# Manifest V3 リファレンス

仕様確認日: 2026-10-25。以下のバージョンは機能の対応開始を示す。実装時は末尾の公式資料で採用機能の現状を確認する。

## 目次

1. [Chrome と Firefox の違い](#chrome-と-firefox-の違い)
2. [permissions 一覧](#permissions-一覧)
3. [Content Scripts](#content-scripts)
4. [Background Scripts](#background-scripts)
5. [メッセージング](#メッセージング)
6. [Firefox のデータ収集・送信宣言](#firefox-のデータ収集送信宣言)
7. [公式資料](#公式資料)

## Chrome と Firefox の違い

### manifest.json 比較

```json
{
  "manifest_version": 3,
  "name": "Extension",
  "version": "1.0.0",
  "background": {
    "service_worker": "background.js"
  },
  "action": {
    "default_popup": "popup.html"
  }
}
```

```json
{
  "manifest_version": 3,
  "name": "Extension",
  "version": "1.0.0",
  "browser_specific_settings": {
    "gecko": {
      "id": "extension@example.com",
      "strict_min_version": "140.0",
      "data_collection_permissions": {
        "required": ["none"]
      }
    }
  },
  "background": {
    "scripts": ["background.js"]
  },
  "action": {
    "default_popup": "popup.html"
  }
}
```

上のFirefox例は外部へのデータ収集・送信がない場合。外部API連携を含む同梱テンプレートとは宣言が異なるため、後述のデータ収集・送信宣言を参照する。

### 主な差異

| 項目 | Chrome | Firefox |
| ---- | ------ | ------- |
| Background | `service_worker` | 非永続の `scripts` / `page`。`service_worker` は未対応 |
| 固有設定 | 必要に応じて `minimum_chrome_version` | MV3の署名には `browser_specific_settings.gecko.id` が必要 |
| API namespace | `chrome.*`、Chrome 148以降は `browser.*` も利用可能 | `browser.*` (Promise対応) |

Chromeの `browser` は `chrome` と同じAPIオブジェクトを指す。名前空間が共通でもAPIの対応・挙動まで同一とは限らない。`devtools_page` を持つ拡張ではChrome 152以降が必要（それ以前は拡張全体で `browser` が無効）。既存の `chrome.*` は引き続き利用できる。

Chrome 121以降とFirefox 121以降では `background.scripts` と `service_worker` を同じmanifestに併記できる。既存構成が共通manifestなら維持できるが、実行環境の違いは残る。

## permissions 一覧

### よく使う permissions

| Permission | 説明 |
| ---------- | ---- |
| `storage` | `chrome.storage` API の使用 |
| `tabs` | タブ情報へのアクセス |
| `activeTab` | クリック時にアクティブタブへの一時的アクセス |
| `scripting` | `chrome.scripting` API（動的スクリプト注入） |
| `alarms` | `chrome.alarms` API（タイマー機能） |
| `notifications` | 通知の表示 |
| `contextMenus` | 右クリックメニューの追加 |
| `clipboardRead` | クリップボード読み取り |
| `clipboardWrite` | クリップボード書き込み |

### host_permissions

特定ドメインへのアクセス権限：

```json
{
  "host_permissions": [
    "https://example.com/*",
    "https://*.example.org/*"
  ]
}
```

`host_permissions` の宣言だけで常にアクセスできるとは限らない。Firefox 127以降では `host_permissions` と `content_scripts` のホスト権限がインストール時に表示される。ユーザーによる取消も考慮し、必要に応じて `permissions.contains()` で確認し、ユーザー操作から `permissions.request()` で要求する。任意機能には `optional_host_permissions` を検討する。

`file://` を対象にする場合、Firefox 153以降ではホスト権限とは別にローカルファイルアクセスの許可が必要で、既存拡張も初期状態は無効になる。`browser.extension.isAllowedFileSchemeAccess()` で確認し、未許可なら設定方法を案内する。

## Content Scripts

### 宣言的注入（manifest.json）

```json
{
  "content_scripts": [
    {
      "matches": ["https://example.com/*"],
      "js": ["content-script.js"],
      "css": ["content.css"],
      "run_at": "document_idle"
    }
  ]
}
```

### `run_at` オプション

| 値 | タイミング |
| -- | ---------- |
| `document_start` | DOM構築前 |
| `document_end` | DOM構築後、リソース読み込み前 |
| `document_idle` | DOM構築後（デフォルト）。Chromeでは全リソースの読み込み完了は保証しない |

### 動的注入（chrome.scripting）

```javascript
// background.js
chrome.scripting.executeScript({
  target: { tabId: tabId },
  files: ['content-script.js']
});
```

## Background Scripts

### Service Worker の制約（Chrome）

- 永続的な状態を持てない（アイドル後に停止）
- DOM アクセス不可
- `setTimeout` / `setInterval` 非推奨（`chrome.alarms` を使用）

FirefoxのMV3 backgroundも停止・再起動されるイベントページであり、グローバル変数だけに状態を置かない。両ブラウザでイベントリスナーはトップレベルで同期的に登録する。

### 状態の永続化

```javascript
// 状態を storage に保存
chrome.storage.local.set({ state: currentState });

// Service Worker 起動時に復元
chrome.storage.local.get(['state'], (result) => {
  if (result.state) {
    currentState = result.state;
  }
});
```

## メッセージング

### 非同期応答とシリアライズ

- FirefoxとChrome 148以降では `runtime.onMessage` のリスナーからPromiseを返して非同期応答できる。Chromeで `devtools_page` がある場合は152以降が必要。旧版も対象なら下の `return true` + `sendResponse` を使う。応答対象外のメッセージまで `async` リスナーで引き受けない。
- Chromeの既定はJSONシリアライズ、Firefoxはstructured clone。共通コードでは両方で扱えるデータ型を使う。
- Chrome 148以降はmanifestに `"message_serialization": "structured_clone"` を指定できる。省略時・148未満はJSONのままなので、採用時は最低対応バージョンも合わせる。拡張間通信では双方の形式を揃える必要があり、native messagingは引き続きJSONとなる。
- structured cloneは `toJSON()` を呼ばない。送信項目の制限を `toJSON()` に依存させず、必要な項目だけをメッセージに含める。

### Content Script ↔ Background

```javascript
// Content Script から送信
chrome.runtime.sendMessage({ action: 'getData', id: 123 }, (response) => {
  console.log(response);
});

// Background で受信
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'getData') {
    fetchData(request.id).then(sendResponse);
    return true; // 非同期レスポンスを有効化
  }
});
```

### Tab へのメッセージ送信

```javascript
// Background から特定タブに送信
chrome.tabs.sendMessage(tabId, { action: 'update' }, (response) => {
  console.log(response);
});

// Content Script で受信
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'update') {
    updateUI();
    sendResponse({ success: true });
  }
});
```

## Firefox のデータ収集・送信宣言

- `browser_specific_settings.gecko.data_collection_permissions` に外部へ収集・送信するデータを宣言する。2025-11-03以降のAMOへの新規提出では、送信しない拡張も `required: ["none"]` が必要。既存拡張への適用時期は公式案内を確認する。公開作業は本スキルの対象外だが、生成するmanifestと実装の整合は確認する。
- 組み込み同意画面はデスクトップ140以降、Android142以降。既存の最低対応バージョンを勝手に引き上げない。旧版対応が必要なら、送信停止か独自の同意UIかを要件に照らして判断する。
- 同梱のFirefoxテンプレートはデスクトップ140以降向け。`background.js` がページURLとBearer APIキーを外部APIへ送るため、`required` に `browsingActivity` と `authenticationInfo` を宣言する。生成時に外部通信を削除するなら `none` に、送信データを変更するなら該当カテゴリに変更する。APIのホスト権限も送信先に合わせる。
- 任意の収集は `optional` に宣言し、ユーザー操作から `permissions.request({ data_collection: [...] })` で同意を得る。送信前に許可を確認し、取消後は送信しない。`technicalAndInteraction` は必須収集にはできない。

## 公式資料

採用する機能に関係する資料だけを参照する。

- Chromeの更新情報: https://developer.chrome.com/docs/extensions/whats-new
- ChromeのAPI名前空間・Promise応答: https://developer.chrome.com/docs/extensions/develop/concepts/browser-namespace
- ChromeのDevTools拡張の対応条件: https://developer.chrome.com/docs/extensions/how-to/devtools/extend-devtools
- Chromeのメッセージ形式: https://developer.chrome.com/blog/structured-clone-messaging
- Chromeのcontent scripts: https://developer.chrome.com/docs/extensions/develop/concepts/content-scripts
- MDNのbackground対応表: https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/manifest.json/background
- MDNのbackgroundライフサイクル: https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/Background_scripts
- MDNのホスト権限: https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/manifest.json/host_permissions
- MDNのFirefox固有manifest設定: https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/manifest.json/browser_specific_settings
- Firefoxのデータ収集同意: https://extensionworkshop.com/documentation/develop/firefox-builtin-data-consent/
- Firefox 153のファイルアクセス変更: https://blog.mozilla.org/addons/2026/07/23/firefox-153-webextensions-api-updates/
