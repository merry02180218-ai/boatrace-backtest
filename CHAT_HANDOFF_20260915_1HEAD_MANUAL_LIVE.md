# 1号艇 v351 手動LIVE 引き継ぎ — 2026-09-15

## 重要ルール
- September 2026結果・払戻は `UNREAD` 維持。研究では `race_code < 20260901` hard guard。
- production profile: `1HEAD_PRODUCTION_20260915_HEAD078_V351_OPPONENTCORE_G2_045_G3_100`。
- HEAD cutoff `.78`、opponent core SECOND G2=.45 / THIRD G3=1.00。
- LIVEでは結果・払戻を絶対に使用しない。`result_or_payout_used=False` / `chronology_guard=True`。
- `half`（半周ラップ）は桐生(JCD01)だけ。`half+turn+straight` は桐生専用schema。
- 正式schema: `lap+turn+straight`, `lap+turn`, `half+turn+straight`, `base`。`turn+straight`は保留。

## exact3〜Wave11 要約
- exact3分解: EXACT3_HIT=106 / OPPONENT_PAIR_MISS=115 / ORDER_MISS=14。主因は相手2艇選択。
- Wave3: 235R、first pair KEEP67 / REPLACE_ONE144 / REPLACE_BOTH24。one-replace方向を研究。
- Wave4 June frozen: 71R、baseline22/71=30.99%。th=-0.05で24/71=33.80%、rescue5/damage3。production変更なし。
- Wave5: 主力lap+turn+straightはrescue3/damage3で差引0。
- Wave6場別: 浜名湖+2、びわこ-2、常滑0、住之江+1、徳山+1。小標本でproduction変更なし。
- Wave7 桐生×2号艇: Run `34997552243` / Job `104477496635` / Artifact `10408383148`。actual pairに2号艇8/15、現行first pairは2を15/15含む。false keep2=7。
- Wave8: Run `34999916439` / Job `104485468453` / Artifact `10409258569`。KIRYU_R=15 / KEEP2=8 / DROP2=7。half単独分離は弱い。
- Wave9: strict fold-local LOO。桐生half追加は改善せず `SHARED_PLUS_HALF` REJECT。
- Wave10: Run `35059052599` / Job `104675293447` / Artifact `10432685265`。mass `[.350,.375)` 145RのうちHEAD hitかつexact3 miss=81R。schema分類をvenue mapで修正、halfは桐生のみ。
- Wave11: Run `35062917684` / Job `104686861402` / Artifact `10433019414` / success。81R中 first pair `KEEP_ONE_REPLACE_ONE=57` (70.4%) / `REPLACE_BOTH=19` / `ORDER_ONLY=5`。one-replace方向に強いoracle余地。ただし結果非依存guardが必要。

## Wave12 結果非依存 one-replace guard — 完了
- 実装 `research_v351_mass_rescue_wave12_frozen_guard.py` commit `115d10fb56d9018a4edfeac8cb93ab5f30870b7b`、workflow commit `6951e9cd425710de2168c4b281fb3a9a70dc9809`。
- Run `35065633476` / Job `104695158122` / Artifact `10434198373` / success。
- Wave4の全期間median補完リークを修正し、`SimpleImputer -> StandardScaler -> LogisticRegression` をtraining fold内fit。
- Feb-Apr学習→Mayで閾値選択→Feb-May再学習→June完全frozen test。
- May側選択threshold=.25。June 25Rでbaseline pair hit=5/25、override=0、rescue=0、damage=0、final=5/25、delta=0。
- 結論: WAVE11のone-replace oracle余地はあるが、単純な確率差guardでは安全に発火できない。Wave12 fixed rule REJECT。production変更なし。

## Wave13 KEEP/DROP分解 — 完了
- Run `35074784229` / Job `104724478934` / Artifact `10438502916` / success。Artifact SHA256 `6ffe5e43...aefbe1`。
- one-replace解析可能50Rで SECONDを残す25R / THIRDを残す25R。位置だけでは判別不能。
- 艇番keep率: 2号艇17/40=42.5%、3号艇14/24=58.3%、4号艇13/24=54.2%、5号艇4/7=57.1%、6号艇2/5=40.0%。
- 展示順位が良い方を残す約42%、ST順位が良い方を残す約38%で、単独特徴は弱い。
- 結論: 『強い方を単純に残す』では不十分。相手艇同士の攻撃構造・展開関係を見る必要あり。production変更なし。

## Wave14 2号艇 vs 3号艇 inner attack structure — 完了
- commit `3fc653253bea32139f4fd2ed480621c336195d22`。
- Run `35080771943` / Job `104743967023` / Artifact `10440564699` / success。Artifact SHA256 `547975a4...6509`。
- 対象98R。2号艇優勢47R / 3号艇優勢33R / 同等18R。
- 2号艇優勢: actual pairに2号艇55.3%、3号艇48.9%。3号艇優勢: actual pairに2号艇54.5%、3号艇36.4%。同等: 2号艇50.0%、3号艇61.1%。
- actual pairに4〜6号艇が入る率は全体77/98=78.6%。2優勢時78.72%、3優勢時78.79%。
- 重要な再解釈: Wave14の目的は『2と3の強い方をそのまま相手に採る』ではない。仮説は『1号艇が2/3の強い攻撃艇を警戒することでターン/展開が変わり、弱い内艇や4〜6号艇の2・3着浮上構造が変化する』こと。
- よって強い艇本人の着内率だけでWave14を否定しない。優勢度→実際の2着/3着→外艇浮上を展開構造として分解する。
- production変更なし。September outcomes UNREAD。

## 2026-09-16 daily PRE / 手動LIVE
- 正式取得は BoatRace Biyori。基準Run `35034996720` / Job `104601998526` / Artifact `10423825328` / 13場156R。
- 手動入口 `.github/workflows/manual-1head-v351-live.yml`。ユーザー明示要求時だけtrigger。controller自動運用は復活させない。
- validation Run `35041039151` / Job `104620732127` / Artifact `10424643529` / success。
- 結果・払戻・オッズは読まない。`result_or_payout_used=False` / `chronology_guard=True`。

## opponent mass `.375` 監査
- Run `35039558019` / Job `104616158961` / Artifact `10424409413` / success。
- `[.350,.375)` は145R / HEAD77.24% / exact3 21.38%。単純な `.375 -> .350` 緩和はREJECT。production `.375` 維持。

## Wave15 1号艇の2/3警戒→相手着順構造 — 完了
- Run `35111618442` / Job `104846502944` / Artifact `10454356574` / success。
- Run head SHA `b494a0553af41491b473a216319d38afed5e2639`。Artifact SHA256 `5d5840825821f65dadefa8e4865c6ff03ab019abbde5011f3de7c84eb1692aac`。
- historical 98Rのみ。September outcomes/payoutsは使用していない。本番設定変更なし。
- 2号艇が明確に3号艇より強い40R: actual SECOND 2号艇32.5%、4号艇25.0%、actual THIRD 3号艇35.0%。4〜6号艇がどちらかに入る75.0%、4〜6両方12.5%。
- 3号艇が明確に2号艇より強い29R: actual SECOND 2号艇31.0%、3号艇24.1%、actual THIRD 5号艇31.0%、3号艇13.8%。4〜6号艇がどちらかに入る79.3%、4〜6両方27.6%。
- 解釈: 『強い2/3号艇本人をそのまま買う』より、1号艇の警戒で展開が変わり外艇が浮上する仮説を追加検証する価値あり。特に探索上は2優勢→4号艇、3優勢→5号艇の着順差が見える。
- ただし同じ98Rを見た探索結果であり、本番採用根拠にはしない。

## BEFORE: Wave16 2優勢→4 / 3優勢→5 の月別frozen検証 — 2026-09-17
- Wave15で見えた『2号艇優勢時は4号艇、3号艇優勢時は5号艇が浮上』を探索データへ最適化せず、時系列で固定検証する。
- まずWave15と同一の攻撃強度定義・band定義をコードから再利用し、探索月と検証月を分離する。閾値・ルールは学習側で固定し、検証月では変更しない。
- 比較対象は現行HYBRID 3点をbaselineとし、候補ルールは『2優勢→4を相手候補へ』『3優勢→5を相手候補へ』。救済で既存ticketを壊すdamageも必ず計測する。
- 月別で対象R、現行的中、救済数、破壊数、差引、2着/3着別の4・5浮上率を出す。小標本なら採用しない。
- historical `race_code < 20260901` hard guard。September 2026 outcomes/payoutsは `UNREAD` 維持。
- 展示をHEAD学習特徴へ直接追加しない。post-ranking / ticket-rescueのみ。本番v351は検証完了まで変更しない。
- fresh Actionsで再現し、Run/Job/Artifact/commit/結論をAFTER追記する。
