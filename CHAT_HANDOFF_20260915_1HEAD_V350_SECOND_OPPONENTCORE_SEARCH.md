# 1号艇 v350 2着 opponentCore 係数探索

## 作業開始
- 正式基準は v349 production。
- 3着側は現行係数 `g3=1.00` を固定する。
- 今回は2着側の opponentCore 係数 `g2` だけを細かく探索する。
- 目的は単一点の最大値ではなく、Feb-Jun pristine の的中数・月別安定性・近傍台地性を見て適切な g2 を決めること。
- Jul-Aug は `NON_PRISTINE_SUPPORT_ONLY` として参考値のみ。
- September 2026 outcomes は UNREAD のまま維持する。
- 結果を見て対象レースを後から除外しない。

## 命名ルール
- v350以降の新規コード、Workflow、Artifact、引き継ぎでは `opponentCore` を使用する。
- 既存v349 productionの名称は再現性のため変更しない。

## 検証予定
- g3=1.00固定。
- g2を現行 .50 の周辺から細粒度で走査する。
- 比較基準は現行 v349 の g2=.50 / g3=1.00。
- Feb-Jun pristine を最優先し、月別最悪値、全期間、Jul-Aug support-only、race-level gain/loss も確認する。
- 最良点の前後も比較して過学習的な尖りか台地かを確認する。

## 現時点
- production変更はまだ行わない。
- 研究結果を確認してから昇格可否を判断する。
