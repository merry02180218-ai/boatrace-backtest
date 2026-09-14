# 1号艇モデル 引き継ぎ — v341 v340購入後段ルール堅牢性監査

作成日: 2026-09-14
repo: merry02180218-ai/boatrace-backtest

## 作業開始記録
- 前回正式引き継ぎ: `CHAT_HANDOFF_20260914_1HEAD_V340_ODDS_DUTCH.md`
- 正式production本体は変更しない: `1HEAD_PRODUCTION_20260914_HEAD078`
  - HEAD/PRE cutoff = `0.78`
  - exhibition = v332 `ATTACK_ENV_SOFT`, env_w=0.1, q=0.65
  - SECOND = v317 `OUTER_L2_1`
  - THIRD = v318 `DROPSTART_T0.1`
  - ticket ranking = v320 `HYBRID alpha=.70`
- production identity: PASS 276R / head 241 / exact3(top3) 119 / SHA256 `89e0b32c3ffbed6212f98f0a9b2e230717b8e41010019e3321fb49e70148ba73`
- 2026年7月・8月はNON-PRISTINE。
- 2026年9月outcomesはUNREADを厳守し、今回も一切読まない。

## v339完走確認
- Run `34787687379`: SUCCESS
- final audit Job `103807404470`: SUCCESS
- final Artifact `10327069135`: `v339-1head-cutoff-local-stability`
- v339結論は0.78維持。0.7775/0.7750で頭率が明確に悪化し、0.7850はvolume/exact3が悪化。

## v340確定結果
- Run `34796402852`: SUCCESS
- final Artifact `10329904344`: `v340-1head-adaptive-odds-dutch-sharded`
- official closing trifecta odds coverage 276/276, missing 0
- baseline top3 all: stake 2,760,000円 / return 2,567,630円 / profit -192,370円 / ROI 93.0301%
- adaptive: skip 243R / keep3 26R / expand 7R / bought 33R / hits 11R
- adaptive: stake 330,000円 / return 381,260円 / profit +51,260円 / ROI 115.5333%
- `SEPTEMBER_OUTCOMES_READ=false`

## 今回やること — v341
v340の購入後段ルールをproduction昇格させる前に、固定済みrace-level結果だけで堅牢性と寄与を分解する。

1. Feb-Junのみ（pristine扱い）のadaptive ROI / 損益 / hit率を再集計し、Jul/Aug NON-PRISTINEを除いてもプラスか確認する。
2. skip / keep3 / expand別にR数・頭的中・top3 exact3・adaptive hit・stake・return・profit・ROIを分解する。
3. expand 7Rについて、同じ7Rをtop3のまま1万円Dutch購入した場合と実際のexpanded購入を直接比較し、点数追加の純増分を測る。
4. skip群について、top3を買っていた場合の仮想損益を集計し、「見送り」がどれだけROI改善へ寄与したかを定量化する。
5. 正式production本体およびv340購入後段候補は、この監査だけで黙って変更しない。
6. 9月outcomesはUNREADを維持する。

## 完了後に追記するもの
- 実装/workflow/handoff commit
- Actions Run / Job / Artifact ID
- pristine Feb-Jun結果
- action別寄与
- expand純増分
- skip回避損失
- 結論と次の再開地点
- `SEPTEMBER_OUTCOMES_READ=false`確認
