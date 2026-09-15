# CHAT HANDOFF — 2026-09-15 — 4HEAD WR_ST AUG31 HISTORY VARIANT

## CURRENT RULES
- 2026年7月・8月結果は学習・検証に使用可。
- 2026年9月結果は `UNREAD` 維持。
- production `HEAD4_V291_COMP7` は変更しない。

## KEY AUDITED STATE
- 4-head fixed candidate: Apr-Jun 86R / 35頭 / 40.6977%; Jul-Aug 78R / 35頭 / 44.8718%。
- frozen opponent v283: SECOND `PLAYER_START`, conditional THIRD `COND_BASE`, `TOP2XTOP2`, alpha2=.60, Top4 exactly 4 tickets。v96禁止。
- independent audit Run `34984842829` / Job `104434176443` / Artifact `10402973600`: success。
- closing-odds diagnostic Run `34991765053` / Job `104457918590` / Artifact `10406490587`: success。
- current diagnostic: Apr-Aug 164R中115R coverage=70.12%, hits=17, stake=46,000円, payout=63,070円, profit=+17,070円, ROI=137.11%。Aug 31Rはcoverage 0。
- retrospective diagnosticのみ。formal prospective ROI=`NOT_COMPUTABLE`。Sep `UNREAD`、production unchanged。

## BEFORE — 締切時オッズ coverage 100% 回収監査
- main `data/official_closing_odds3t/2026` は01〜07を確認、08 pathは現時点で404。
- official closing odds取得コード `tools/fetch_official_closing_odds3t.py` と既存archive workflowあり。
- coverage回収BEFORE commit `4b9b63c0a7889e93a1b4a26015431aed45211c2e`。
- Aug専用回収workflow追加 commit `3ac4f10dd3e9a5c79d7ba741387a4b9253b150f7`。

## BEFORE — Actions多重発火の整理を最優先
ユーザー指示: 「発火が複数しちゃうからそれを先にどうにかしよう」。coverage回収より先にActions trigger整理を行う。

これからやること:
1. `.github/workflows` の4号艇研究/監査関連、とくに過去に一時的に `push` を広げたworkflow、v2重複workflow、今回追加したAug回収workflowの `on:` 条件を棚卸しする。
2. 通常のコード/handoff commitで不要な4号艇監査workflowが複数同時発火しないようにする。研究監査・回収系は原則 `workflow_dispatch` の手動起動へ寄せ、必要な専用push path以外のall-push triggerを除去する。
3. production/liveに必要なworkflowは勝手に停止しない。4号艇production `HEAD4_V291_COMP7` の運用経路は維持する。
4. 重複している `audit-4head-86r-independent.yml` / `audit-4head-86r-independent-v2.yml` など、同目的の監査workflowは正式な1本を残すか、push自動発火を止める。
5. 今回のAug締切時オッズ回収workflowも、登録用pushで勝手に走らず、明示的な手動dispatchだけで1回起動できる構成にする。
6. trigger整理commit後、そのcommitで発火したActions一覧を確認し、多重発火が解消したことを監査する。不要workflowがまだ発火するなら追加修正する。
7. 解消確認後にのみAug回収→coverage 100%診断へ戻る。
8. September outcomeは `UNREAD`、v96禁止、production unchanged。

Status: `HEAD4_ACTIONS_DUPLICATE_TRIGGER_CLEANUP_STARTED`
