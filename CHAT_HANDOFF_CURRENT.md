# Chat handoff — canonical current state

Updated: 2026-09-05 (JST)
Repository: `merry02180218-ai/boatrace-backtest`
Default branch: `main`

## How the next chat should start

1. Read this file first: `CHAT_HANDOFF_CURRENT.md`.
2. Then inspect the actual current repo files/workflow results through the connected GitHub connector.
3. If the user says “続き”, “引き継ぎ”, “GitHub見て”, or asks about a model/version, do not rely only on chat memory. Fetch the relevant files/actions from this repo.
4. Prefer the latest finalized rule/result when older versions conflict.
5. For public live BOAT RACE information, use the web/official source; for repo code/actions/results, use GitHub.

## GitHub operating policy

- Canonical repo: `merry02180218-ai/boatrace-backtest`.
- Use the connected GitHub connector directly; do not say GitHub is unavailable unless an actual connector call fails.
- Typical flow:
  - find code/results with repository search;
  - fetch exact files with `fetch_file`;
  - inspect Actions workflow run/job/log/artifact when a test was run;
  - use `create_file` / `update_file` for repo changes;
  - after a workflow completes, inspect the generated summary/result file instead of guessing from the workflow name.
- Do not substitute web search for private/connected repo inspection.
- Keep all prediction/backtest logic no-leak unless explicitly doing post-hoc descriptive analysis.

## Global BOAT RACE no-leak rules

Prediction side must be frozen before result/payout.

Never use as a current-race prediction feature:
- actual race result/payout,
- post-race actual course,
- same-race final/deadline odds,
- later weather/wind,
- same-day result-derived labels.

Allowed:
- official pre-race program data,
- current exhibition entry/course,
- current exhibition time,
- current exhibition ST,
- current original exhibition (lap / turn / straight etc.),
- current pre-race wind,
- strictly prior-date historical results/odds for fitted priors,
- same-race final odds only after ticket freeze for post-hoc evaluation.

Entry gate is active:
- 3-head model: target 3 must exhibit course 3.
- 4-corner model: target 4 must exhibit course 4.
- 5-head model: target 5 must exhibit course 5.
- 1-head model: target 1 must exhibit course 1.
If target course changes, exclude; do not re-score to a new course.

Final grade convention for the existing 3/4/5 models:
- A >= 55
- S >= 67
- below 55 = B / skip

## Existing production family (3-head / 4-corner / 5-head)

Structural pre-scan models across all active venues/races:
- 3号艇まくり
- 3号艇まくり差し
- 4カドまくり
- 5頭展開

Structural gates:
- 3m: `3strength>=.50`, `3ST>=.55`, `2wallweak>=.55`
- 3ms: `3strength>=.50`, `3ST>=.45`, `1weak>=.45`, `2wall>=.45`
- 4c: `4strength>=.50`, `4ST>=.55`, `3wall>=.55`
- 5head: `4attack_nonmotor>=.55`, `1_2_resistance>=.55`, `5strength>=.50`

Direct weights:
- 3m: ex .28 + ST .28 + straight .22 + origavg .17 + venue .05
- 3ms: ex .17 + ST .22 + lap .17 + turn .27 + avg .12 + venue .05
- 4c production: ex .28 + ST .30 + straight .22 + avg .15 + venue .05
- 5head:
  - 4attack = .32 ex + .38 ST + .18 straight + .12 avg
  - 5take = .22 ex + .17 ST + .27 lap + .27 turn + .07 avg
  - final = .43 attack4 + .52 take5 + venue .05

Current opponent base is v51:
`total=.16grade+.19national+.08local+.17motor+.13waku+.09nationalST+.18direct`
All head-fixed ordered opponent pairs are ranked across the full 20 combinations.

### 3HEAD role shadow
- v98/v99/v100: current score 80% + role score 20%.
- v100 prospective starts 2026-09-05.
- Changes only 3-head opponent ranking, not candidate/head/grade.
- Production is not automatically replaced yet.

### 4C 7-ticket value shadow
- v105 exact 7-ticket monthly stability PASS.
- v106 prospective starts 2026-09-05.
- role lambda 0.10, historical price lambda 0.15, exactly 7 tickets.
- CURRENT7 remains production reference; ROLE7/V106_7 are shadow until prospective adoption criteria pass.
- Current-race final odds are never used to rank v106 tickets.

### 5HEAD
- Keep current v51 opponent ranking.
- Prior role/value overlays for 5HEAD were rejected.

## 1号艇モデル — current frozen decision

User decision on 2026-09-05: “とりあえず1号艇モデルはそれで大丈夫”.
So stop further tuning for now and keep **v109 + v110 fixed 7 tickets** as the current 1-head candidate implementation.

### v109 — head judgment
Status: PASS / operational-head candidate.
Strict monthly walk-forward.
Observed aggregate:
- A (predicted >=65%): 5,229R, 1-head win rate ~73.3%
- S (predicted >=72%): 3,308R, 1-head win rate ~76.7%
Monthly Jun/Jul/Aug remained stable around A 73%, S 76-77%.

Interpretation:
- 1-head selection itself is operationally promising.
- Do not equate this with profitability of fixed tickets.

### v110 — dedicated 2nd/3rd opponent model
Status: PASS / keep.
Chosen role blend lambda = 0.50.
7-ticket representative holdout results:
- A: trifecta hit ~49.0%, head-win conditional coverage ~66.9%
- S: trifecta hit ~51.0%, head-win conditional coverage ~66.5%
Month-by-month 7-ticket coverage improved in all 6 Jun/Jul/Aug × A/S cells.

Current operational form for 1-head model:
- v109 decides 1-head A/S.
- v110 ranks head-fixed 20 combinations.
- Use fixed top 7 tickets for shadow/operational evaluation.

### Rejected 1-head extensions
Do not revive without a new reason/data split:
- v111 prior-only price overlay: FAIL / reject.
- v112 pre-close odds EV selection: FAIL (improved ROI vs fixed7 but still <100%).
- v113 exact role probability + calibration EV: FAIL.
- v114 hybrid-score probability EV: FAIL.
- v115 pre-odds race filter: FAIL; hit rate improved but ROI did not become viable.

Important anti-overfit decision:
- Do not keep tuning on August 2026 repeatedly.
- Next meaningful validation should be genuinely prospective/unseen.

## 2026-09-05 full field structural scan (v107)

Files:
- `predict_v107_20260905_official_fullscan.py`
- `.github/workflows/v107-20260905-official-fullscan.yml`
- `prediction_v107_20260905_official_fullscan.md`
- `pred_v107_20260905_official_fullscan.csv`

Run: 33891362627 — SUCCESS.
Official scan: 14 active venues, 168/168 races, 0 active-venue errors.
Prior same-frame history coverage ~99.1%.

Structural candidates in deadline order:
1. 三国2R 08:58 — head4 — 4カド — 長谷川雅和 — struct 59.6 — v106 observation
2. 福岡2R 12:18 — head3 — 3まくり — 堀越雄貴 — struct 59.5 — v100
3. 江戸川5R 13:02 — head3 — 3まくり差し — 中島昂章 — struct 57.6 — v100
4. 尼崎6R 13:10 — head4 — 4カド — 柳沢一 — struct 76.7 — v106 observation
5. 津7R 13:46 — head5 — 5頭展開 — 木村仁紀 — struct 81.5
6. 徳山11R 13:50 — head5 — 5頭展開 — 佐藤大佑 — struct 73.8
7. 江戸川8R 14:24 — head5 — 5頭展開 — 松本博昭 — struct 68.8
8. 福岡6R 14:27 — head4 — 4カド — 溝口海義也 — struct 76.2 — v106 observation
9. 宮島8R 14:46 — head3 — 3まくり — 小原聡将 — struct 74.1 — v100
10. 江戸川12R 16:25 — head5 — 5頭展開 — 新田泰章 — struct 76.0
11. 津12R 16:35 — head5 — 5頭展開 — 石丸海渡 — struct 81.4
12. 住之江7R 18:04 — head4 — 4カド — 柏野幸二 — struct 68.6 — v106 observation
13. 住之江10R 19:32 — head5 — 5頭展開 — 山本修一 — struct 70.2
14. 蒲郡11R 20:10 — head5 — 5頭展開 — 高倉孝太 — struct 66.9

These are pre-exhibition structural candidates only. Final A/S/B requires current exhibition/original/entry/wind.

## Last live task in this chat: 福岡2R

The user uploaded pre-race screenshots and asked “福岡2R 判定して”, then asked to preserve the whole chat for the next conversation before a final answer was delivered.

Pre-race screenshot data to preserve:
- race: 福岡2R, deadline 12:18 JST, 2026-09-05
- target: 3号艇 堀越雄貴 B1
- structural model: 3号艇まくり, v107 struct 59.5
- exhibition entry: 1-2-3-4-5-6, so target 3 stayed course 3 -> entry gate PASS
- exhibition times: 1=6.86, 2=6.79, 3=6.80, 4=6.88, 5=6.83, 6=6.79
- exhibition ST: 1=.05, 2=.07, 3=F.08, 4=.02, 5=.06, 6=.44
- current original exhibition shown in screenshot:
  - lap: 1=37.59, 2=37.82, 3=38.20, 4=39.00, 5=38.24, 6=38.88
  - turn: 1=5.85, 2=6.10, 3=5.93, 4=5.80, 5=5.85, 6=6.16
  - straight: 1=7.55, 2=7.50, 3=7.52, 4=7.61, 5=7.58, 6=7.49
- weather screenshot: 28.0C, sunny, wind 5m, water 28.0C, wave 5cm
- historical/average original-exhibition row visible in screenshot:
  - avg lap: 1=38.24, 2=38.10, 3=38.10, 4=38.19, 5=37.87, 6=38.25
  - avg turn: 1=5.83, 2=5.56, 3=5.76, 4=5.76, 5=5.77, 6=5.80
  - avg straight: 1=7.71, 2=7.74, 3=7.61, 4=7.65, 5=7.58, 6=7.59

Important: if this race is evaluated later, do not use the result/payout to retroactively change the pre-race judgment. If a final pre-race judgment needs to be reconstructed, use only the preserved screenshot data + prior data that existed before the deadline.

## Wind handling

Do not apply a universal numeric wind correction.
Previous v83-v85/v89 numeric wind corrections failed.
v86 freshwater + 5HEAD + headwind 0-2m is caution only.
Wind may inform qualitative/direct context but should not create a candidate or hard-exclude unless a validated special rule says so.

Facing degrees used by the project:
桐生90, 戸田0, 江戸川200, 平和島270, 多摩川180, 浜名湖90, 蒲郡90, 常滑270, 津90, 三国270, びわこ0, 住之江0, 尼崎0, 鳴門0, 丸亀0, 児島0, 宮島90, 徳山0, 下関0, 若松0, 芦屋0, 福岡0, 唐津0, 大村0.

## Motor/original exhibition policy

Do not evaluate motors from raw motor 2連率 alone.
Classify/contextualize motor as stretch / acceleration-turn / balanced using recent exhibition, original exhibition, race content, and prior users where possible.
- 3m / 4c: emphasize stretch,行き足,ST.
- 3ms / 5head: emphasize acceleration, turn, lap.
Compare exhibition/original data with course/frame context rather than raw times only.

## Source policy

Historical primary:
- waku10 / BoatraceCSV programs and race cards.
- BOATCAST fallback where applicable.

Odds:
- strict pre-close odds: timestamped BoatraceCSV od3 where available.
- Kyotei24 final odds may be used for post-hoc descriptive evaluation or strictly prior-date historical price tendency, but not as same-race pre-close prediction input.

## What not to do next

- Do not reopen v111-v115 just because the user asks “もっと良くできる?” without a new prospective dataset/idea.
- Do not call v106 production-adopted yet.
- Do not call v100 production-adopted yet.
- Do not use result/payout to “improve” a live judgment after the fact.
- Do not replace current official exhibition/original data with a generic web summary when screenshots/official source exist.

## Preferred answer style

Japanese, concise, direct, action-first.
When a race is B, say clearly `見送り` and do not force tickets.
When A/S, give the grade and head-fixed ticket ranking, and distinguish current production tickets from shadow tickets (v100/v106) before result.
