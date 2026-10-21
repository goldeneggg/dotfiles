## 8. より良いソースを集める検索テンプレート

### 8.1 基本式

検索は次の3要素で設計します。

```text
[Topic] + [Information Type] + [Source Constraint]
```

例：

```text
kubernetes autoscaling official documentation
kubernetes autoscaling architecture
kubernetes autoscaling limitations
kubernetes autoscaling production case study
kubernetes autoscaling postmortem
kubernetes autoscaling benchmark
kubernetes autoscaling site:kubernetes.io
```

### 8.2 Information Type一覧

| 目的 | 検索語の例 |
|---|---|
| 基礎・公式仕様 | `official documentation`, `specification`, `FAQ`, `design guide` |
| 設計・実装 | `architecture`, `reference architecture`, `tutorial`, `best practices` |
| 制約・反証 | `limitations`, `known issues`, `pitfalls`, `tradeoffs`, `alternatives` |
| 本番運用 | `production`, `at scale`, `operations`, `lessons learned` |
| 失敗から学ぶ | `postmortem`, `incident`, `failure`, `root cause` |
| 性能・比較 | `benchmark`, `performance`, `comparison`, `evaluation` |
| 変更・移行 | `migration guide`, `upgrade guide`, `release notes`, `changelog` |
| セキュリティ | `security advisory`, `threat model`, `vulnerability`, `hardening` |
| 実証・研究 | `research paper`, `systematic review`, `whitepaper`, `dataset` |
| 意思決定 | `decision record`, `case study`, `cost`, `ROI`, `adoption` |

`best practices` や成功事例だけでなく、`limitations`、`tradeoffs`、`postmortem`、`known issues` を併用すると、成功例だけを集める偏りを減らせます。

### 8.3 Source Constraint一覧

```text
site:[公式ドメイン]
filetype:pdf
before:[日付]
after:[日付]
[製品名またはバージョン]
[対象業界・地域・組織規模]
[著者・研究機関・標準化団体]
```

### 8.4 AIに検索計画を作らせる

```text
私の調査目的は「[目的]」です。

検索を始める前に、偏りの少ないソース群を集めるための検索計画を作成してください。

以下を含めてください。
- 調査すべきサブテーマ
- 各サブテーマで必要な情報タイプ
- 一次情報を優先する検索語
- 成功事例だけでなく、制約・反証・失敗事例を探す検索語
- 情報の鮮度や対象バージョンの条件
- 採用・除外するソースの基準
- 調査を打ち切る条件

検索式は `[Topic] + [Information Type] + [Source Constraint]` の形で提示してください。
```
