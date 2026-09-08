#!/usr/bin/env python3
"""v208: audit the v207 8% PRE through actual production FINAL and od3 settlement.
Uses the already-frozen v207 July-selected 8% rule (base+prior_ex, cut=.280323),
then actual v165 production-pass rows / frozen v166 Top10 from v195. No reselection.
August is the primary untouched evaluation. Odds are BoatraceCSV od3 only.
"""
from pathlib import Path
import math
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parent
V207=ROOT/'analysis_v207_3head_enhanced_pre.csv'
V207ROI=ROOT/'analysis_v207_3head_enhanced_pre_roi.csv'
V195=ROOT/'analysis_v195_3head_production_6month_backtest.csv'
V108=ROOT/'analysis_v108_1head_feasibility.csv'
SUMMARY=ROOT/'summary_v208_3head_v207_8pct_operational_funnel.md'
OUT=ROOT/'analysis_v208_3head_v207_8pct_operational_funnel.csv'
CUT=.280323

def code(x):
    try:return str(int(float(x))).zfill(12)
    except:return str(x).strip().replace('.0','').zfill(12)

def main():
    # v207 output is aggregate, so reconstruct exact 8% pass codes from the committed monetary replay
    # for August production-pass rows; PRE population/watch counts are frozen in v207 summary/output.
    roi=pd.read_csv(V207ROI,dtype={'race_code':str})
    tag='v207_8pct_base+prior_ex'
    aug=roi[roi.tag==tag].copy()
    aug['_code']=aug.race_code.map(code)
    prod=pd.read_csv(V195,dtype={'race_code':str}); prod['_code']=prod.race_code.map(code)
    feat=pd.read_csv(V108,dtype={'race_code':str},usecols=['race_code','turn_margin23','st_margin23','straight_margin23','ex_margin23']); feat['_code']=feat.race_code.map(code)
    z=aug.merge(prod[['_code','month','p3head','actual_combo','top10']],on='_code',how='left',suffixes=('','_prod')).merge(feat.drop(columns='race_code').drop_duplicates('_code'),on='_code',how='left')
    z['final_pass']=1
    z['pickup']=((pd.to_numeric(z.p3head)>=.30)&(pd.to_numeric(z.turn_margin23)>=-.2)&(pd.to_numeric(z.st_margin23)>=-.2)).astype(int)
    z.to_csv(OUT,index=False,encoding='utf-8-sig')

    # Frozen funnel counts from v207: Aug all races 4776, PRE watch 421. Actual v165 pass + od3 settle = rows here.
    allR=4776; preR=421; finalR=len(z)
    hit=int(z.top10_hit.sum()); ret=float(z.return_yen.sum()); cost=float(z.cost_yen.sum()); roi_pct=100*ret/cost if cost else 0
    formal=110; pre_formal=85 # 77.3% of 110, exact integer implied by v207
    pickup=z[z.pickup==1]; pret=float(pickup.return_yen.sum()); pcost=float(pickup.cost_yen.sum())
    L=['# v208 — v207 8% PRE -> production FINAL operational replay','',
       '**Rule is frozen before this replay: v207 8% = base+prior_ex, cut 0.280323. No August retuning.**','',
       '## August untouched funnel',
       '|stage|R|rate / note|','|---|---:|---|',
       f'|All races|{allR}|100%|',
       f'|v207 8% PRE watch|{preR}|{100*preR/allR:.1f}% of all races; formal recall {100*pre_formal/formal:.1f}% ({pre_formal}/{formal})|',
       f'|Actual FINAL pass (v165 p3head>=30%) + frozen v166 Top10 + od3 settle|{finalR}|{100*finalR/preR:.1f}% of PRE watch|','',
       '## August untouched betting result after FINAL','',
       '- Odds source: BoatraceCSV od3 only (pre-deadline snapshot).',
       '- Bank: ¥10,000 per FINAL-pass race, inverse-odds Dutch, 100-yen units.',
       f'- Settled races: **{finalR}R**',f'- Top10 hits: **{hit}R / {100*hit/finalR:.1f}%**',
       f'- Average composite odds: **{z.composite_odds.mean():.3f}**',f'- Cost: **¥{cost:,.0f}**',f'- Return: **¥{ret:,.0f}**',f'- ROI: **{roi_pct:.1f}%**','',
       '## FINAL/PICK UP shadow subset','',
       f'- PICK UP: **{len(pickup)}R**',f'- PICK UP hits: **{int(pickup.top10_hit.sum())}R / {(100*pickup.top10_hit.mean() if len(pickup) else 0):.1f}%**',f'- PICK UP ROI: **{(100*pret/pcost if pcost else 0):.1f}%**','',
       '## Interpretation','- This is the operational path the user asked for: PRE candidate -> exhibition-based v165 FINAL -> v166 Top10 -> od3 Dutch settlement.',
       '- August remains untouched with respect to v207 feature-set/cut selection. Production is not changed by this report.']
    SUMMARY.write_text('\n'.join(L)+'\n',encoding='utf-8')
    print('\n'.join(L))
if __name__=='__main__':main()
