#!/usr/bin/env python3
"""v208: frozen v207 8% PRE -> actual v165 FINAL -> v166 Top10 -> od3 settlement.
No August retuning. FINAL count is measured before odds availability/settlement.
"""
from pathlib import Path
import numpy as np, pandas as pd
import analyze_v207_3head_enhanced_pre as v207
ROOT=Path(__file__).resolve().parent
ATT=ROOT/'analysis_3attack_rows.csv'; V195=ROOT/'analysis_v195_3head_production_6month_backtest.csv'; V108=ROOT/'analysis_v108_1head_feasibility.csv'; V207ROI=ROOT/'analysis_v207_3head_enhanced_pre_roi.csv'
OUT=ROOT/'analysis_v208_3head_v207_8pct_operational_funnel.csv'; SUMMARY=ROOT/'summary_v208_3head_v207_8pct_operational_funnel.md'
CUT=.280323

def code(x):
    try:return str(int(float(x))).zfill(12)
    except:return str(x).strip().replace('.0','').zfill(12)

def main():
    hist,miss,cover,missing_dates=v207.restore.hist_rows(); h=pd.DataFrame(hist); h['_code']=h.race_code.map(code)
    att=pd.read_csv(ATT);att['_code']=att.race_code.map(code); extras=v207.PRIOR_EX
    h=h.merge(att[['_code']+extras],on='_code',how='inner',validate='one_to_one')
    for c in extras:h[c]=pd.to_numeric(h[c],errors='coerce').fillna(.5)
    h['venue']=h.venue.astype(str); tr=h[h.month=='2026-06'].copy(); te=h[h.month=='2026-08'].copy()
    m=v207.fit_model(tr,extras); pa=v207.probs(m,te,extras); pre=te[np.asarray(pa)>=CUT].copy(); pre_codes=set(pre._code)
    prod=pd.read_csv(V195,dtype={'race_code':str});prod=prod[prod.month=='2026-08'].copy();prod['_code']=prod.race_code.map(code)
    final=prod[prod._code.isin(pre_codes)].copy() # v195 rows are actual v165 production pass with frozen v166 Top10
    feat=pd.read_csv(V108,dtype={'race_code':str},usecols=['race_code','turn_margin23','st_margin23']);feat['_code']=feat.race_code.map(code)
    final=final.merge(feat.drop(columns='race_code').drop_duplicates('_code'),on='_code',how='left')
    final['pickup']=((pd.to_numeric(final.p3head)>=.30)&(pd.to_numeric(final.turn_margin23)>=-.2)&(pd.to_numeric(final.st_margin23)>=-.2)).astype(int)
    roi=pd.read_csv(V207ROI,dtype={'race_code':str});settled=roi[roi.tag=='v207_8pct_base+prior_ex'].copy();settled['_code']=settled.race_code.map(code)
    final['od3_settled']=final._code.isin(set(settled._code)).astype(int)
    final.to_csv(OUT,index=False,encoding='utf-8-sig')
    allR=len(te);preR=len(pre);formal=int(te.label.sum());preformal=int(pre.label.sum());finalR=len(final);settledR=len(settled)
    hit=int(settled.top10_hit.sum());cost=float(settled.cost_yen.sum());ret=float(settled.return_yen.sum()); roi_pct=100*ret/cost if cost else 0
    pickcodes=set(final.loc[final.pickup==1,'_code']); pickup=settled[settled._code.isin(pickcodes)];pc=float(pickup.cost_yen.sum());pr=float(pickup.return_yen.sum())
    L=['# v208 — v207 8% PRE -> production FINAL operational replay','',
       '**Frozen rule: v207 8% = base+prior_ex, cut 0.280323. August is not retuned.**','',
       '## August untouched funnel','|stage|R|rate / note|','|---|---:|---|',
       f'|All races|{allR}|100%|',f'|v207 8% PRE watch|{preR}|{100*preR/allR:.1f}% of all; formal recall {100*preformal/formal:.1f}% ({preformal}/{formal})|',
       f'|Actual v165 FINAL pass (p3head>=30%)|{finalR}|{100*finalR/preR:.1f}% of PRE watch|',
       f'|od3-settled FINAL races|{settledR}|{100*settledR/finalR:.1f}% of FINAL pass|','',
       '## August untouched result after FINAL','- v166 tickets: frozen Top10 from production replay.','- Odds: BoatraceCSV od3 only; ¥10,000/race inverse-odds Dutch in ¥100 units.',
       f'- Top10 hit: **{hit}/{settledR} = {100*hit/settledR:.1f}%**',f'- Average composite odds: **{settled.composite_odds.mean():.3f}**',f'- Cost: **¥{cost:,.0f}**',f'- Return: **¥{ret:,.0f}**',f'- ROI: **{roi_pct:.1f}%**','',
       '## PICK UP inside FINAL',f'- FINAL PICK UP races: **{int(final.pickup.sum())}R**; od3 settled: **{len(pickup)}R**',f'- Settled PICK UP hit: **{int(pickup.top10_hit.sum())}/{len(pickup)} = {(100*pickup.top10_hit.mean() if len(pickup) else 0):.1f}%**',f'- Settled PICK UP ROI: **{(100*pr/pc if pc else 0):.1f}%**','',
       '## Audit','- PRE is determined before current-race exhibition. v165 FINAL uses current exhibition margins. v195 supplies the frozen production v166 Top10.',f'- reconstructed June={len(tr)}, August={len(te)}, unmatched={miss}; missing dates={missing_dates or "none"}.','- Production remains unchanged; this is SHADOW evaluation.']
    SUMMARY.write_text('\n'.join(L)+'\n',encoding='utf-8');print('\n'.join(L))
if __name__=='__main__':main()
