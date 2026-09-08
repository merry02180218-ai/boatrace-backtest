# v219 — 3号艇モデル全面再設計プロトコル

Updated: 2026-09-09 JST

## 目的
3号艇LIVEを、旧来の的中率中心ではなく、**1レース総投資10,000円・100円単位Dutch配分後の実現ROI**を最終目的として全面的に再評価する。

## 汚染期間の扱い
- 2026-07、2026-08は、PRE、v165/v166、TopN、可変点数、合成オッズ、ROI仮説、失敗例・成功例を反復閲覧しているため、**model selection / threshold selection / validation に使用禁止**。
- 7月・8月は descriptive / shadow / sanity check のみに使用可。
- 7月・8月で良く見えるルールを本番採用してはならない。

## ROI定義
- 選択した1レースあたり総投資額は常に10,000円。
- 選択券をオッズ逆数比例でDutch配分し、100円単位へHamilton/largest-remainderで丸める。
- 全実購入券の投資額合計は正確に10,000円。
- 0円配分になる券は「購入点数」に含めない。候補TopNと実購入券が不一致になる設計は禁止。
- 合成オッズ `O_combined = 1 / sum(1/o_i)` は評価特徴であり、ROIそのものではない。
- 実現ROI = `総払戻 / (settled selected races * 10,000)`。
- LIVEの点数・価値判断に使えるオッズは締切前に実際に取得したsnapshotのみ。closing oddsをLIVE snapshotの代用にしない。

## 全面見直し対象
### A. PRE / workload screen
- PREは収益フィルタではなく、展示確認対象を絞る運用層として再定義する。
- hard dropによるproduction race取りこぼしを明示計測する。
- 7・8月を使って新しいcutを決めない。

### B. 3号艇1着判定（旧v165）
- `p3head>=0.30`を既定値として固定せず再監査する。
- discriminationだけでなく calibration / Brier / log loss / race-count / downstream Dutch ROIを時系列で確認する。
- 展示タイム、展示ST、original展示、直前コース等のFINAL情報は締切前取得時のみ使用。
- leakage、重複レース、同日未来情報、結果由来特徴を監査する。

### C. 相手順位（旧v166）
- Top10固定を前提にしない。
- ordered-pair rank qualityを TopK coverage / probability calibration / conditional coverage で評価する。
- 相手モデルのscoreを単純正規化した値が真の条件付き確率として使えるかを別途検証する。
- 未校正scoreから期待値を作って本番採用しない。

### D. 点数選択
- 点数は `v166 ranking -> current odds -> TopNごとの合成オッズ / 購入可能性 / 校正済み確率` を見て決める設計を優先する。
- Top4〜20を候補とし、100円Dutchで全券に最低100円入るNのみ実購入候補。
- ルールの閾値は7・8月で調整禁止。
- fixed TopN、確率mass、effN、entropy、現在オッズを用いたruleを同一walk-forwardで比較する。

### E. 1万円Dutch
- 100円単位Hamiltonをcanonicalとする。
- 各候補Nについて total stake=10,000 をassert。
- hitでもactual ticket stake=0ならhit扱いしない。
- theoretical composite oddsとactual rounded equal-return dispersionを両方保存する。

## 検証プロトコル
1. 7・8月を完全隔離する。
2. 過去期間は必ず時系列で、各評価月より前のデータだけでfit/tuneする。
3. 月次walk-forwardで以下を凍結して次月を1回だけ評価する。
   - PRE rule
   - head model / head cut
   - opponent model / calibration
   - point rule
   - Dutch allocator
4. 主要指標
   - selected races
   - 3-head rate
   - conditional TopK coverage
   - final trifecta hit rate
   - average / median points
   - average / median composite odds
   - total stake / return / profit / ROI
   - max drawdown
   - monthly ROI dispersion
   - top1/top3/top5 profitable race removal sensitivity
   - odds-band / p3-band / venue / month stability
5. 単一高配当でROIが成立していないか必ず確認する。
6. 7・8月は最後にshadow表示のみ行い、採否には使わない。
7. 2026-09以降のLIVE freezeを真のprospective validationとして蓄積する。

## 現行モデルの扱い
- v165、v166、v218は削除しない。
- v165/v166はbaseline comparatorに降格。
- v218のodds fetch / freeze / Dutch基盤は再利用可。
- v218の `p3head * normalized v166 mass * composite odds` は未校正SHADOW仮説であり、本番EVとは扱わない。

## v219で最初に実施する監査
1. Dec-2025〜Jun-2026を中心に、利用可能なそれ以前データも含めて月次walk-forward datasetを再構築。
2. head cutをROIだけで選ばず、校正とrace volume制約を含めてprior-onlyで選ぶ。
3. v166 scoreの校正を監査し、必要ならconditional pair probability modelへ変更。
4. fixed TopN vs odds-aware variable Nを同一walk-forward条件で比較。
5. 10,000円Dutchのrounded returnで統一settlement。
6. 7・8月は参考表としてのみ最後に添付。

## 採用条件
- 7・8月成績は採用根拠に含めない。
- prior-only walk-forwardでbaseline改善が複数月に分散していること。
- top1/top3高収益レース除外後も極端に崩れないこと。
- 2026-09以降のprospective LIVE freezeで挙動を確認すること。
- 条件を満たすまではSHADOW運用。
