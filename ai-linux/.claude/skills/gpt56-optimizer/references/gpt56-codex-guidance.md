# GPT-5.6 Codexセッション最適化ガイダンス

この資料はCodexでGPT-5.6を使う際の判断基準をまとめる。提供状況やUIは変わり得るため、現在性が重要な依頼ではOpenAI公式資料と実際のセッション表示を優先する。

## Codexでのモデル選択

- **Sol**: 複雑、曖昧、高価値、判断や仕上がり品質を重視する作業に選ぶ。不明ならSolから始める。
- **Terra**: 日常的な実装、修正、レビューなど、推論・ツール利用と速度・コストの均衡を取る作業に選ぶ。
- **Luna**: 抽出、分類、変換、定型要約など、正解条件が明確で反復量が多い作業に選ぶ。
- Codexの既定Power設定はSolのmedium。CLIでは `/model`、起動時は `codex --model gpt-5.6`、恒久設定は `config.toml` の `model` を使用できる。実際に選べる項目は利用面とアカウントで確認する。

## 推論努力と並列実行

- 最低限必要な推論努力を使う。明確で小さい作業はLow、通常の複数ステップはMedium、難しい分析・設計・デバッグはHighまたはExtra Highを起点にする。
- 既定の努力で代表タスクを試し、品質が不足したときに上げる。努力を上げる前に、成功条件、依存関係、ツール経路、検証条件の不足を直す。
- **Max**は単一タスクにより深い推論を与える。最難関かつ速度や使用量より深さを優先する場合だけ使う。
- **Ultra**は分離可能な作業をサブエージェントで並列化する。独立した作業流が複数あり、同じファイルを競合編集しない場合だけ使う。

## CodexとResponses APIを混同しない

Codexのモデル選択UI、`/model`、推論スライダーと、Responses APIのリクエスト設定を分けて扱う。

Responses APIではGPT-5.6が `reasoning.effort` の `none` から `max`、`reasoning.mode: "pro"`、`reasoning.context`、`text.verbosity`、Programmatic Tool Callingなどを提供する。これらはAPIアプリの設計には有効だが、Codexセッションで同名の設定を直接指定できるとは限らない。

## セッション設計

1. 成果、必要な文脈、重要な制約、完了条件を明示する。
2. 同じ指示を一度だけ書き、矛盾、不要な例、無関係なツールを除く。
3. 回答・計画・診断・レビューでは、依頼が変更まで含まない限り編集しない。
4. 実装・修正では、範囲内のローカル変更と非破壊検証を自律的に進める。
5. 外部書き込み、破壊的操作、購入、権限拡張、重大なスコープ拡張だけを承認境界に置く。

## ツールと状態

- 独立した読み取りは並列化し、結果に依存する判断は逐次化する。並列取得後は統合してから変更する。
- 空、部分的、または不自然に狭い検索結果には、意味のある代替を1〜2回試す。
- 長い作業では、最初に短い作業予告を出し、主要フェーズの変化だけを報告する。通常のツール呼び出しを逐一実況しない。
- コンテキスト圧縮は主要マイルストーン後に行い、目標、制約、決定、未完了項目、検証証拠を保つ。
- 検証は変更に近いものを優先する。コードでは対象テスト、型検査、lint、ビルド、スモークテスト、視覚成果物ではレンダリングと目視確認を使う。

## 公式資料

- [Using GPT-5.6](https://developers.openai.com/api/docs/guides/latest-model.md)
- [Prompting guidance for GPT-5.6 Sol](https://developers.openai.com/api/docs/guides/prompt-guidance-gpt-5p6.md)
- [Codex models](https://learn.chatgpt.com/docs/models.md)
- [Codex best practices](https://learn.chatgpt.com/guides/best-practices.md)
