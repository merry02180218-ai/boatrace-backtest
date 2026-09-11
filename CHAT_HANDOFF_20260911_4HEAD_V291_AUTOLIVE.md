# CHAT HANDOFF — 2026-09-11 — 4HEAD v291 AUTO LIVE

## 最優先ルール
- repo: `merry02180218-ai/boatrace-backtest`
- 次チャットでは必ず最新GitHubを最初に確認し、このhandoffより新しいcommit/fileがあれば最新GitHubを優先する。
- 2026-07/08 は NON-PRISTINE / 過学習扱い。性能評価・閾値調整・救済に使わない。
- 2026-09 の結果はLIVEモデルの選定・調整・救済に使わない。特に当日結果を予想前に見ない。
- ROI: 1レース10,000円。ROI = total payout / total settled stake * 100。外れは payout=0 / profit=-10,000。合成オッズはROIではなくmarket feature。

## PRODUCTION絶対遵守ルール — 4HEAD v291
以下は実運用で変更・緩和・救済してはいけない固定条件。今後の実装・修正・LIVE判定では必ずこの節を先に確認すること。

1. **2026-07/08 は NON-PRISTINE**
   - 性能評価、閾値調整、モデル選定、救済条件作成に使わない。
   - 実装のfeature parity確認に使う場合も outcome は見ない。
2. **2026-09 は完全 outcome-blind**
   - 9月の結果、払戻、的中可否をLIVEモデルの fitting / calibration / threshold selection / rescue に一切使わない。
   - 当日結果を予想・BET/PASS/NO_BET確定前に取得しない。
3. **production route で v96 を禁止**
   - v96 input、fallback、救済分岐を一切使用しない。
4. **締切後オッズ禁止**
   - 使用可能なのは公式3連単120通りの締切前snapshotのみ。
   - 締切超過、snapshot欠落、不完全120通り、取得時刻を保証できない場合は代替せず `ERROR_NO_BET`。
   - 締切後オッズへのfallbackは禁止。
5. **必要データ不足は fail closed**
   - PRE / POST / ENV_ENTRY / v283 p2 / conditional / official odds の必須入力が不足・不整合・期限切れなら `ERROR_NO_BET`。
   - 推測値、ダミー値、旧モデル、別sourceで救済しない。
6. **LIVE入力に対する `.fit()` / 再学習禁止**
   - 7月・8月・9月のLIVE/current rowsを使って imputer / scaler / model / calibration / threshold を fit または再fitしない。
   - POST / ENV_ENTRY / v283 は 2026-06-30 までで凍結された exact recipe / artifact の inference のみ許可。
7. **判定auditは結果取得前に永続化**
   - BET / PASS / NO_BET / ERROR_NO_BET と、その時点のscore・閾値・Top4・odds snapshot/hash・stake・source timestampを結果取得前に保存する。

この節と他の古い記述が競合した場合は、最新GitHub上のより新しい明示的なproduction仕様を優先する。ただし7/8 NON-PRISTINE、9月 outcome-blind、締切後オッズ禁止、LIVE再学習禁止を緩める変更は、ユーザーが明示的に方針変更しない限り行わない。

## 現行4号艇頭モデル
Policy: `HEAD4_V291_COMP7`

S layer:
- PRE >= 0.28 inclusive
- POST >= 0.25 inclusive
- ENV_ENTRY >= 0.224790 inclusive
- opponent/partner selection = independent v283
- Top4 fixed
- exactly 4 tickets, all head=4
- composite odds >= 7.0 => BET; exactly 7.000000 is BET
- composite odds < 7.0 => PASS
- 10,000 JPY Dutch
- v96 prohibited in production route
- deadline exceeded => hard fail `ERROR_NO_BET`
- odds must be immutable official pre-deadline trifecta snapshot; never substitute post-deadline odds
- persist BET / NO_BET / PASS audit before result

Prospective chain:
`4-head S eligibility -> frozen independent v283 opponent ranking -> Top4 tickets -> immutable pre-deadline trifecta odds -> comp>=7 -> exact 10k Dutch -> audit`

v291 is market/ticket overlay. S judgment itself is frozen v268. v283 is independent opponent model.

## v283 frozen semantics
- SECOND: independent PLAYER_START listwise, L2=10
- THIRD: conditional P(third=t | candidate second=s, pre-result context), COND_BASE, L2=0.3
- pair ordering TOP2XTOP2, alpha2=0.60
- v96 prohibited

## PRE automation completed on 2026-09-11
Generalized daily PRE scanner was implemented and CI-tested.
Files added/used include:
- `fetch_4head_v291_pre_inputs_live.py`
- `scan_4head_v291_pre_live.py`
- `.github/workflows/live-4head-v291-pre-daily.yml`
- date-specific audit versions remain for reproducibility:
  - `scan_20260911_4head_v291_pre.py`
  - `fetch_kyoteibiyori_v291_pre_inputs.py`
  - `.github/workflows/scan-20260911-4head-v291-pre.yml`

Daily PRE behavior:
- scheduled around 09:30 JST plus manual date execution
- target date in JST
- active venues auto-discovered
- all races preserved; tolerant Waku10 handling prevents silent race drops
- PRE model exact v250 recipe
- training labels frozen through 2026-06-30
- no Jul/Aug/Sep labels for fitting/calibration/threshold selection
- no current-day exhibition/ST/original-exhibition for PRE
- PRE threshold remains exactly/inclusively 0.28
- outputs CSV / Markdown / audit artifact

PRE features:
- legacy_score4
- racer4
- hist_st_edge_4v3
- wall3_weak
- inner12_resistance
- motor4_2ren
- motor4_hist
- turnfoot4_prior
- past_win4

Model recipe: median imputer -> StandardScaler -> LogisticRegression(C=0.35, max_iter=1000, class_weight=None).

Important commits from this work:
- `75c482e93d24d9c5bc543d0b3669fb8496c9b067` — date-specific result-blind PRE scan
- `cf250593cdec15c592a52ca4f1403b0d1ba44d52` — tolerant Waku10 PRE input fetcher
- `68cc32c29a81a5a7c4fd5c91f8ac81e70c7c9aab` — date-specific workflow update
- `2f618b60cdeee1ff965a0b542c117c57a226347f` — generalized daily PRE automation state reported as completed

Successful runs already verified:
- `34557396065` — full 2026-09-11 date-specific PRE, success, 144/144 races
- `34558379641` — generalized daily PRE initial run, success, 144/144 races

## 2026-09-11 PRE result
Formal complete result-blind scan:
- 12 venues
- 144/144 races
- PRE >= 0.28: 0 races
- therefore no formal v291 S candidate proceeds to POST/ENV_ENTRY on 2026-09-11

Top PRE values from date-specific audit:
1. 202609111207 / JCD12 7R (住之江7R): 0.1365504771
2. JCD05 5R: ~0.050062
3. JCD13 6R: ~0.044671
4. JCD02 5R: ~0.033657
5. JCD06 8R: ~0.033594

Do NOT lower threshold or rescue candidates because the distribution is low.

## Existing market/ticket runner
Previously confirmed:
- `run_20260911_4head_v291_live.py` commit `c2a63a1`
- consumes already-frozen PRE, POST, ENV_ENTRY, p2, cond
- applies S gate, v283 Top4, official 120 trifecta odds snapshot, composite odds >=7, Dutch via existing v234/v205 logic, audit JSONL
- limitation: it does NOT itself generate POST/ENV_ENTRY/p2/cond from raw race/exhibition data.

Verifier:
- `verify_20260911_4head_v291_live.py` commit `d5f8e54`
- verifies inclusive thresholds, exactly 4 unique 4-head tickets, exact comp=7 BET, below 7 PASS, exact 10k / 100-yen units, v96 ignored, S fail NO_BET, expired deadline hard fail.

Workflow:
- `.github/workflows/validate-4head-v291-live.yml` commit `b09aaa64f793b4ac9cd4c1a9fadaef134b0b33b4`
- run `34555835579` success.

## Current unfinished task — START HERE NEXT CHAT
User asked to complete full automation AFTER PRE:
`PRE candidate -> exhibition -> POST -> ENV_ENTRY -> v283 Top4 -> pre-deadline official trifecta odds -> comp>=7 -> 10k Dutch -> audit`

This is NOT completed yet. Do not claim it is completed.

At the end of the current chat we began locating the exact frozen v268/v283 implementation files in latest GitHub. Code search/index did not immediately surface them, so repository contents/tree search was being pursued. The user then requested this handoff.

### Required next actions
1. Inspect latest GitHub first and locate exact v268 POST/ENV_ENTRY lineage and exact v283 SECOND/THIRD model implementation/artifacts. Do not guess filenames/semantics.
2. Reuse/freeze those exact implementations; do not create approximate replacements.
3. Build a generalized post-exhibition LIVE runner triggered only for PRE>=0.28 candidates.
4. Fetch contemporaneous exhibition/entry information only after exhibition becomes available.
5. Generate POST and ENV_ENTRY with frozen thresholds; if either fails, persist NO_BET/PASS appropriately.
6. Generate independent v283 p2/conditional-third scores and exact Top4 tickets.
7. Fetch and freeze official pre-deadline 120-way trifecta odds snapshot. Hard fail if deadline exceeded; never use after-deadline odds.
8. Compute composite odds and apply inclusive >=7.0 rule.
9. If BET, allocate exact 10,000 JPY Dutch in 100-yen units using frozen rounding logic.
10. Persist a full audit record BEFORE result: source timestamps/hashes, PRE/POST/ENV_ENTRY, v283 scores, Top4, odds snapshot/hash, composite odds, stakes, BET/PASS/NO_BET reason.
11. Add verifier and GitHub Actions workflow. Run CI to completion in the same response if practical.
12. Keep 7/8 NON-PRISTINE and September outcome-blind throughout.

### Important implementation audit concern
Before declaring full production-safe, audit PRE/current feature parity. In the 2026-09-11 scan `turnfoot4_prior` was 0.5 for all 144 current rows, which may indicate current prior-exhibition cache/name matching/source-state issue. A semantic parity check can use July 1 PRE feature/prediction artifacts ONLY to compare implementation outputs, ignoring outcomes; this is not performance validation. Do not tune from Jul/Aug.

## User preference
- Japanese, concise, execution-oriented.
- User expects actual GitHub edits/tests/commits/results, not repeated promises.
- Do not ask unnecessary clarifying questions.
- If a workflow is running, poll it to completion in the same answer when practical.
- Latest GitHub always wins over this handoff.
