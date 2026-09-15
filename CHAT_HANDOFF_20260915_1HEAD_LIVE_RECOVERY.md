# 1号艇 v351 LIVE 引き継ぎ — 2026-09-15

## 最重要ルール
- 最新GitHubを最優先する。
- 2026年9月15日のレース結果・払戻は読まない。LIVE判断では `UNREAD` を維持する。
- `result_or_payout_used=False` / `chronology_guard=True` を維持する。
- 作業前にこの引き継ぎへ「これからやること」を記録し、作業後に結果・commit SHA・Actions Run/Job/Artifact ID・結論・次の再開地点を追記する。
- Actions/workflow名に `head4` 等が表示されても、名前だけで1号艇/4号艇を判定しない。必ず対象workflow・実行script・目的変数/処理内容まで確認する。

## 現在の1号艇production / LIVE
- 1号艇LIVEは v351。
- 基準として確認していたproduction HEAD: `bfc9b8ba9f72baf04434b4686e08b7f5538a8992`。
- 現在のmainは上記から3コミットahead、behind 0。
- `e9cb97b403b3508c5bd665a7fc28927868b81b54` は明確に1号艇v351 LIVE側。commit message: `ci: trigger v351 live after venue-aware probe fix`。
- e9cb97bの変更対象は `.github/workflows/auto-live-1head-v351-exhibition-20260915.yml` で、push pathsへ `probe_1head_v351_boatcast_exhibition.py` を1行追加したもの。
- したがってe9cb97b起点のActionsを表示名だけで4号艇と判断してはいけない。

## 徳山9Rで判明した展示READY問題
- 徳山はオリジナル展示の直線タイムを公開しない。v351 probeが全場で `orig_straight_all6` を必須にしていたため、徳山で誤ってREADYにならない問題があった。
- venue-aware修正commit: `376748f25079cd3a717fbb42da71fc8fcb5b4b9f`。
- 徳山(JCD18)は `avg + turn` を必須、straightは必須にしないよう変更。
- ただし全24場の現行2026仕様は最終監査が必要。特に古い調査情報をそのまま使わず、現在の公開項目を確認すること。
- オリジナル展示非公開場では `orig` URL自体が無い可能性があるため、required_origが空の場合のfetch/parseも安全化が必要。

## LIVE遅延問題
- 現行v351 workflowは5分cronで毎回新しいActions Runを立ち上げる構造。
- checkout / setup-python / pip install / PRE artifact取得 / 展示probe / gateという起動オーバーヘッドがあり、締切直前運用には遅い。
- さらにworkflowの `prepare` は `if: github.event_name != 'push'` なので、pushでworkflowを起動しても本体LIVE処理には使えない構造。
- e9cb97bはpush pathを追加しただけで、この問題を解決していない。
- ユーザー判断: 現状は遅すぎて実運用に使えない。

## main混線監査
`bfc9b8...` → 現在mainの比較で変更ファイルは3つ:
1. `.github/workflows/auto-live-1head-v351-exhibition-20260915.yml` — 1号艇v351 LIVE、+1行。
2. `probe_1head_v351_boatcast_exhibition.py` — 1号艇v351展示probe、+33/-3。
3. `analyze_4head_exhibition_original_trainonly.py` — 4号艇研究側、+1/-4。

現時点で1号艇v351のモデル本体・学習ロジック・相手選びを直接変更した形跡は確認していない。混線はLIVE周辺変更と4号艇研究変更が同時期にmainへ存在し、Actions表示の解釈を誤ったこと。

## これからやること（次の実作業前状態）
1. これ以上変更を重ねる前に、bfc9b8以降の3コミットを個別監査し、1号艇/4号艇の変更を完全に切り分ける。
2. 1号艇production本体が不変であることを再確認する。
3. v351 LIVEを高速化する。基本方針は「5分ごとに新規Run」ではなく、事前に1本のLIVE Runを起動して候補レースを待機し、展示公開を短間隔でprobe、READY直後にv351判定・買い目確定する方式。
4. 高速化後、Actions実動で Run ID / Job ID / Artifact ID / 展示READY時刻 / 判定完了時刻を確認し、実運用可能な遅延か測定する。
5. 9/15結果・払戻は一切読まない。

## 既知の監査ID
- 徳山9R旧失敗 Run: `34934002769`
- 徳山9R旧Job: `104267980339`
- 徳山9R旧Artifact: `10382617649`
- 旧status: `ERROR_NO_BET`（T-5でrequired exhibition unavailable扱い）
- chronology guardは維持、結果/払戻未使用。

## 次の再開地点
**まずコミット境界監査 → 1号艇production不変確認 → LIVE常駐/待機型高速化の実装。新しい変更を入れる前に必ずこのファイルへ作業開始内容を追記する。**
