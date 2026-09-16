# 1号艇 v351 手動LIVE 引き継ぎ — 2026-09-15

## 重要ルール
- September 2026結果・払戻は `UNREAD` 維持。研究では `race_code < 20260901` hard guard。
- production profile: `1HEAD_PRODUCTION_20260915_HEAD078_V351_OPPONENTCORE_G2_045_G3_100`。
- HEAD cutoff `.78`、opponent core SECOND G2=.45 / THIRD G3=1.00。
- LIVEでは結果・払戻を絶対に使用しない。`result_or_payout_used=False` / `chronology_guard=True`。
- `half`（半周ラップ）は桐生(JCD01)だけ。`half+turn+straight` は桐生専用schema。
- 正式schema: `lap+turn+straight`, `lap+turn`, `half+turn+straight`, `base`。`turn+straight`は保留。

## exact3〜Wave6 要約
- exact3分解: EXACT3_HIT=106 / OPPONENT_PAIR_MISS=115 / ORDER_MISS=14。主因は相手2艇選択。
- Wave3: 235R、first pair KEEP67 / REPLACE_ONE144 / REPLACE_BOTH24。one-replace方向を研究。
- Wave4 June frozen: 71R、baseline22/71=30.99%。th=-0.05で24/71=33.80%、rescue5/damage3。production変更なし。
- Wave5: 主力lap+turn+straightはrescue3/damage3で差引0。
- Wave6場別: 浜名湖+2、びわこ-2、常滑0、住之江+1、徳山+1。小標本でproduction変更なし。

## Wave7 桐生×2号艇監査 — 完了
- Run `34997552243` / Job `104477496635` / Artifact `10408383148` / success。actual pairに2号艇8/15、現行first pairは2を15/15含む。false keep2=7。

## Wave8 桐生2号艇 KEEP/DROP特徴監査 — 完了
- Run `34999916439` / Job `104485468453` / Artifact `10409258569` / success。
- Artifact SHA256 `bd5241371d62bc7d2f19e7bb123e4d1144837f34729df06e13d09cce897cbe73`。
- KIRYU_R=15 / KEEP2=8 / DROP2=7。half単独分離は弱く、複合guardをLOO評価へ。

## Wave9 — 実行済み
- strict fold-local LOOを実行。桐生half追加は改善せず、多くの設定で悪化。`SHARED_PLUS_HALF` をproductionへ入れない方向。
- production変更なし、September outcomes UNREAD。

## 2026-09-16 daily PRE
- 正式取得は BoatRace Biyori。`fetch_1head_v351_biyori_cards.py --date YYYYMMDD --out race_cards.csv`。
- `race_shusso.php` + `request_race_shusso_detail_v4.php`、retry/backoff、完全12Rの場だけ採用。
- 結果・払戻・オッズは取得しない。`result_or_payout_used=False` / `chronology_guard=True`。
- Biyori -> v321 causal prepare -> `prepare_1head_v351_live_cache.py` -> PRE summary -> Actions artifact。
- 2026-09-16基準Run `35034996720` / Job `104601998526` / Artifact `10423825328` / 13場156R / SHA256 `bb1361755137655b8abd04d0ee09079b7a4f98910e64f7724bc7ec91b86fffec`。

## opponent mass `.375` 独立監査
### BEFORE
- HEAD>=.78を通過したhistorical raceだけで `OPPONENT_MASS_MIN=.375` の有効性を監査する。
- `race_code < 20260901` hard guard。September 2026 outcomes/payoutsは `UNREAD` 維持。
- 比較: `.30/.325/.35/.375/.40/.425/.45`、mass帯別R/HEAD/exact3、月別。production定数 `.375` は監査完了まで変更しない。

### AFTER — 2026-09-16
- cache recovery commit `c5b00997abeb84502468412e00bab4aed5a2d549`。
- fresh Run `35039558019` / Job `104616158961` / Artifact `10424409413` / success。
- `[.350,.375)` は145R / HEAD77.24% / exact3 21.38%。単純な `.375 -> .350` 緩和はREJECT。production `.375` は変更しない。
- September 2026 outcomes/payoutsは `UNREAD` 維持。

## mass直下 `[.350,.375)` 展示救済研究
- 展示をHEAD学習特徴へ直接追加する案はREJECT。post-ranking / ticket-rescueだけを研究する。
- Wave10分類修正 commit `6ae6fae56503283050fcaeb84dfab9239ee7ad96`。
- fresh Run `35059052599` / Job `104675293447` / Artifact `10432685265` / success。
- 145RのうちHEAD hitだがexact3 missの救済候補は81R。
- schema分類はvenue mapで修正し、halfを桐生(JCD01)だけに強制。
- 主力一周系の救済余地が大きく、次は現行相手の片方を保持し、もう片方だけ交換するone-replaceを研究する。

## BEFORE: Wave11 81R one-opponent rescue — 2026-09-16
- 対象はhistorical `race_code < 20260901` のみ。September 2026 outcomes/payoutsは `UNREAD` 維持。
- Wave10の `[.350,.375)` 145Rから、HEAD hitかつ現行3連単missの81Rを分析母集団とする。ただしルール探索時は結果ラベルを入力特徴へ混入させない。
- 目的は「現行相手を1艇残す＋もう1艇だけ交換」で、どちらを残すべきか／交換先はどの艇かを、展示データ形式・場・展示順位/差・ST環境・現行ticket構造から分解すること。
- まずoracle分解として、現行3点unionの各相手艇について actual pair に含まれる保持可能艇の頻度、交換1艇でactual pairへ到達可能な率、両方交換が必要な率を計測する。
- 次に結果非依存の候補guardを設計する。主力 `lap+turn+straight` / `lap+turn` を優先し、桐生halfは独立扱い。小標本の場別改善だけではproduction昇格しない。
- HEAD cutoff `.78` / production mass `.375` / G2=.45 / G3=1.00 / HYBRID 3点は変更しない。研究はpost-ranking / ticket-rescueのみ。
- fresh Actions Runで再現し、Run/Job/Artifact ID・commit SHA・結論をAFTERへ追記する。

## BEFORE: Wave10/11 JCD03分類欠落の復旧 — 2026-09-16
- Run `35061436857` / Job `104682400317` はworkflow全体表示successだが、Wave10は `unmapped schema jcd=[3]`、Wave11はWave10 CSV欠落で失敗。Artifact `10433355530` は不完全なので完了扱いしない。
- 原因確認: schema rebuildの母集団345RにはJCD03（江戸川）が1Rも無く、`analysis_v351_schema_map.csv` に03が生成されない。一方opponent-mass監査母集団にはJCD03が存在するためjoinで欠落した。
- これからJCD03を『元schema母集団に存在しない＝追加オリジナル展示形式を実証できない場』として明示的に `base` 扱いするfallbackを実装する。暗黙unknownや推測の一周系分類はしない。
- fallback適用後も、halfはJCD01桐生のみというinvariantを維持し、未定義JCDが他に出たらfail-closeする。
- Wave10→Wave11をfresh Runで再実行し、実際のschema別分類・one-replace oracle結果を確認してからAFTERを追記する。
- production設定は変更しない。September 2026 outcomes/payoutsは `UNREAD` 維持。

## 手動即時LIVE入口
- `.github/workflows/manual-1head-v351-live.yml`。ユーザーの明示要求時だけtrigger file pushで発火。controller自動運用は復活させない。
- validation Run `35041039151` / Job `104620732127` / Artifact `10424643529` / success。
- 結果・払戻・オッズは読まない。`result_or_payout_used=False` / `chronology_guard=True`。
