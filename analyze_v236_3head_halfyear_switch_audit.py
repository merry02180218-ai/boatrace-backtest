#!/usr/bin/env python3
"""v236: audit whether the official Jul-1 half-year switch explains residual 3-head drift.

AUDIT ONLY. Jul/Aug 2026 are NON-PRISTINE and must never select/tune a rule.
Uses v234 restored Waku10 + frozen v224-like feature pipeline.
Tests the half-year-switch hypothesis by comparing same-racer continuity and source fields
around Jun30/Jul1, plus selected-race calibration by whether boat-3 grade changed at Jul1.
"""
from pathlib import Path
import numpy as np, pandas as pd
import analyze_v234_3head_waku10_restored_replay as v234
import analyze_v223_3head_unused_feature_audit as v223
import analyze_v235_3head_july_source_regime_audit as v235

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'analysis_v236_halfyear_switch_same_racer.csv'
CAL=ROOT/'analysis_v236_halfyear_switch_calibration.csv'
SUM=ROOT/'summary_v236_3head_halfyear_switch_audit.md'

FIELDS=['c_b3_grade','c_b3_wr','c_b3_local','c_b3_nst','c_b3_waku_wr','c_b3_waku_st','c_b3_waku_sr','c_b3_pastwin']

def main():
    cov=v234.reconstruct(); checked=v234.validate_parser()
    if (cov.source=='missing').any(): raise RuntimeError('no imputation allowed')
    d,dc,vc,basefs=v234.build_restored(); fs=v234.full_features(d,basefs); fs=[x for x in fs if x in d.columns]
    # racer identity: prefer explicit boat-3 racer/name columns available in rebuilt frame.
    ids=[c for c in d.columns if any(k in c.lower() for k in ['b3_racer','b3_player','b3_name','boat3_name'])]
    idc=ids[0] if ids else None
    if idc is None:
        # race-card-derived frames normally preserve racer id under one of these Japanese/raw aliases.
        ids=[c for c in d.columns if ('選手' in str(c) and ('3' in str(c) or '３' in str(c)))]
        idc=ids[0] if ids else None
    rows=[]
    if idc:
        pre=d[(d._date>=pd.Timestamp('2026-06-17'))&(d._date<pd.Timestamp('2026-07-01'))].copy()
        post=d[(d._date>=pd.Timestamp('2026-07-01'))&(d._date<pd.Timestamp('2026-07-15'))].copy()
        common=set(pre[idc].dropna().astype(str)) & set(post[idc].dropna().astype(str))
        for rid in common:
            a=pre[pre[idc].astype(str)==rid]; b=post[post[idc].astype(str)==rid]
            if not len(a) or not len(b): continue
            r={'racer':rid,'pre_races':len(a),'post_races':len(b)}
            for f in FIELDS:
                if f in d:
                    av=pd.to_numeric(a[f],errors='coerce').mean(); bv=pd.to_numeric(b[f],errors='coerce').mean()
                    r[f+'_pre']=av;r[f+'_post']=bv;r[f+'_delta']=bv-av
            rows.append(r)
    same=pd.DataFrame(rows); same.to_csv(OUT,index=False)

    # Frozen selected races: May-Aug, same selection logic as v235. Group by grade transition proxy.
    s=v235.select_months(d,vc,basefs,fs)
    # grade score changes are visible at period switch; compare July calibration by grade-score bands.
    rec=[]
    for mon,g in s.groupby('_month'):
        grade=pd.to_numeric(g.get('c_b3_grade'),errors='coerce') if 'c_b3_grade' in g else pd.Series(np.nan,index=g.index)
        for label,mask in [('A1_like',grade>=.9),('A2_like',(grade>=.6)&(grade<.9)),('B1_B2_like',grade<.6),('ALL',grade.notna())]:
            q=g[mask]
            if len(q): rec.append({'month':mon,'group':label,'R':len(q),'avg_p3':q._p.mean(),'actual_3head':q._y.mean(),'gap':q._p.mean()-q._y.mean()})
    cal=pd.DataFrame(rec);cal.to_csv(CAL,index=False)

    L=['# v236 official half-year switch audit','',
       '- AUDIT ONLY; Jul/Aug remain NON-PRISTINE. No model/rule tuning.',
       f'- Waku10 validation: {checked} races, missing restored dates {int((cov.source=="missing").sum())}.',
       '- Hypothesis: Jul-1 official second-half grade/stat period switch changes racer/source values and may break first-half calibration.','',
       f'- Same-racer identity column: {idc or "NOT FOUND"}; matched racers: {len(same)}.','',
       '## Selected calibration by boat-3 grade band','|month|group|R|avg p3|actual|gap pp|','|---|---|---:|---:|---:|---:|']
    for _,r in cal.iterrows(): L.append(f"|{r.month}|{r.group}|{int(r.R)}|{100*r.avg_p3:.2f}%|{100*r.actual_3head:.2f}%|{100*r.gap:+.2f}|")
    if len(same):
        L += ['', '## Same-racer Jun17-30 -> Jul1-14 median source-field deltas','|field|median delta|mean abs delta|','|---|---:|---:|']
        for f in FIELDS:
            c=f+'_delta'
            if c in same:
                x=pd.to_numeric(same[c],errors='coerce').dropna();
                if len(x): L.append(f'|{f}|{x.median():+.5f}|{x.abs().mean():.5f}|')
    L += ['', '## Decision rule for interpretation',
          '- If same racers show systematic grade/stat jumps exactly across Jul1 while coverage stays stable, treat the half-year source/reference-period switch as a serious causal candidate.',
          '- If same-racer source fields are stable but actual 3-head rate changes, favor genuine race/racer composition or performance regime shift.',
          '- July/August findings are diagnostic only; any correction must be validated on other historical half-year boundaries without using Jul/Aug to choose it.']
    SUM.write_text('\n'.join(L)+'\n',encoding='utf-8');print('\n'.join(L))
if __name__=='__main__':main()
