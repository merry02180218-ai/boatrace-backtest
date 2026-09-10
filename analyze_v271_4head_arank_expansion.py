#!/usr/bin/env python3
"""v271: expand frozen v268 with a separate A-rank rescue model.

The v268 S-rank rule remains untouched.  We build a compact A-score from the
stable v270 feature families, score Apr-Jun 2026 month-walk-forward, and only
consider races OUTSIDE v268 S-rank.  The purpose is to see whether race count
can be increased toward ~100 while preserving exact current new-ROI economics.

Discipline
----------
* July/August 2026 are excluded completely.
* v268 S rule is frozen: PRE>=.28, POST>=.25, ENV_ENTRY>=.224790.
* A-score for each evaluation month is fit only on earlier races.
* Tickets use the frozen 4-x-y v96 prior-only pair order and N=2..20 whose
  composite odds is nearest 10.5.
* Exactly 10,000 yen/race inverse-odds Dutch, 100-yen Hamilton rounding.
* Archived odds are a development proxy; this is NOT formal prospective ROI.
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd

import analyze_v264_4head_feature_exhaustive as v264
import analyze_v270_4head_win_feature_importance as v270
import analyze_v251_4head_newroi_bridge as v251
import analyze_v96_4corner_monthly_walkforward_tiebreak as c4
from analyze_v205_3head_operational_replay import load_odds

ROOT = Path(__file__).resolve().parent
F4 = ROOT/'analysis_v264_4head_feature_exhaustive.csv'
OUT = ROOT/'analysis_v271_4head_arank_expansion.csv'
DETAIL = ROOT/'analysis_v271_4head_arank_races.csv'
SUM = ROOT/'summary_v271_4head_arank_expansion.md'
BANK=10000
COMP_TARGET=10.5
NS=tuple(range(2,21))
EVAL_MONTHS=('2026-04','2026-05','2026-06')
S_PRE=.28
S_POST=.25
S_ENV=.224790

# Chosen before this v271 ROI search from the stable v270 importance result.
# Highly correlated raw families are kept compact; no Jul/Aug information.
A_FEATURES=(
    'v91_ex','score_CORR20_v91','score_wind_v83','score_RAW20_v91',
    'score_BASE_v91','preview_comp',
    'rel_pl_all_win_4v1','rel_pl_all_p2_4v1','rel_pl_recent_p2_4v1',
    'opp_grade_b1_v93','opp_score_b1_v93','opp_national_b1_v93',
    'b1_pl_all_win','b1_pl_all_p2','b1_pl_frame_win',
    'rel_pl_recent_p2_4v3','b4_pl_recent_p2',
)

# Small, pre-declared boundary grid.  A-rank is explicitly not allowed to
# modify the S-rank rule; these gates only define rescue candidates outside S.
GATES={
    'BAL_22_20':(.22,.20),
    'BAL_20_20':(.20,.20),
    'PRE24_POST18':(.24,.18),
    'PRE20_POST22':(.20,.22),
    'PRE26_POST16':(.26,.16),
    'PRE18_POST24':(.18,.24),
    'BROAD_18_18':(.18,.18),
}
A_CUTS=tuple(np.round(np.arange(.16,.501,.01),2))


def num(s): return pd.to_numeric(s,errors='coerce')


def env_scores():
    f=pd.read_csv(F4,dtype={'race_code':str})
    f['race_code']=f.race_code.astype(str).str.zfill(12)
    f=f[(f.month.isin(EVAL_MONTHS)) & (f.variant=='ENV_ENTRY')].copy()
    return f[['date','month','race_code','p']].rename(columns={'p':'ENV_ENTRY'})


def oof_a_scores():
    d,_,_=v270.prepare()
    rows=[]
    for mon in EVAL_MONTHS:
        first=pd.Timestamp(mon+'-01'); nxt=first+pd.offsets.MonthBegin(1)
        tr=d[d._date<first].copy(); te=d[(d._date>=first)&(d._date<nxt)].copy()
        fs=[c for c in A_FEATURES if c in d.columns and v264.goodcol(tr,c,.55)]
        if len(tr)<500 or te.empty or len(fs)<8: continue
        m=v264.lr_model(); m.fit(tr[fs].apply(num),tr.y4)
        pr=m.predict_proba(te[fs].apply(num))[:,1]
        for (_,r),p in zip(te.iterrows(),pr):
            rec={'date':str(r.date),'month':mon,'race_code':str(r.race_code).zfill(12),
                 'PRE':float(r.PRE) if pd.notna(r.PRE) else np.nan,
                 'POST':float(r.POST) if pd.notna(r.POST) else np.nan,
                 'a_score':float(p),'y4':int(r.y4)}
            for c in A_FEATURES:
                if c in r.index: rec[c]=r[c]
            rows.append(rec)
    z=pd.DataFrame(rows)
    e=env_scores(); e['date']=e.date.astype(str)
    return z.merge(e,on=['date','month','race_code'],how='inner')


def settle_all(z):
    rs=c4.read(); orders=v251.pair_orders(rs); actual=v251.actual_map(rs)
    od=load_odds(); oi=od.set_index('race_code',drop=False) if not od.empty else pd.DataFrame()
    rows=[]
    for _,r in z.iterrows():
        code=str(r.race_code).zfill(12); k=(str(r.date),code)
        order=orders.get(k); a=actual.get(k)
        if not order or not a or a[3]!=1 or code not in oi.index: continue
        o=oi.loc[code]; o=o.iloc[-1] if isinstance(o,pd.DataFrame) else o
        choices=[]
        for n in NS:
            tickets=[f'4-{x}-{y}' for x,y in order[:n]]
            s=v251.settle(code,tickets,o,a)
            if s is None: continue
            hit,ret,comp=s; choices.append((n,int(hit),float(ret),float(comp)))
        if not choices: continue
        n,hit,ret,comp=min(choices,key=lambda x:(abs(x[3]-COMP_TARGET),x[0]))
        rec=r.to_dict(); rec.update({'n':n,'hit':hit,'return_yen':ret,'comp_odds':comp,
                                     'actual_head4':int(a[0]==4)})
        rec['is_S']=bool(float(r.PRE)>=S_PRE and float(r.POST)>=S_POST and float(r.ENV_ENTRY)>=S_ENV)
        rows.append(rec)
    return pd.DataFrame(rows)


def metrics(q,prefix=''):
    if q.empty: return {}
    cost=len(q)*BANK; ret=float(q.return_yen.sum())
    mm=[]
    for mon,g in q.groupby('month'):
        c=len(g)*BANK; rr=float(g.return_yen.sum())
        mm.append((mon,len(g),100*rr/c,100*g.hit.mean(),100*g.actual_head4.mean()))
    return {
        prefix+'R':int(len(q)), prefix+'head4_rate_pct':100*q.actual_head4.mean(),
        prefix+'hit_pct':100*q.hit.mean(), prefix+'return_yen':ret,
        prefix+'profit_yen':ret-cost, prefix+'roi_pct':100*ret/cost,
        prefix+'min_month_roi_pct':min(x[2] for x in mm),
        prefix+'month_detail':';'.join(f'{m}:{n}R ROI{roi:.2f}% hit{hit:.2f}% head{head:.2f}%' for m,n,roi,hit,head in mm),
        prefix+'avg_n':q.n.mean(), prefix+'avg_comp_odds':q.comp_odds.mean(),
    }


def main():
    scored=oof_a_scores(); settled=settle_all(scored)
    if settled.empty: raise RuntimeError('no settled rows')
    S=settled[settled.is_S].copy()
    outside=settled[~settled.is_S].copy()
    sm=metrics(S,'s_')
    rows=[]
    for name,(pc,oc) in GATES.items():
        pool=outside[(outside.PRE>=pc)&(outside.POST>=oc)].copy()
        for cut in A_CUTS:
            A=pool[pool.a_score>=cut].copy()
            if len(A)<10: continue
            C=pd.concat([S,A],ignore_index=True).drop_duplicates('race_code')
            am=metrics(A,'a_'); cm=metrics(C,'combined_')
            rec={'gate':name,'pre_cut':pc,'post_cut':oc,'a_score_cut':cut,
                 'pool_R':len(pool),**sm,**am,**cm}
            rec['robust_combined_roi']=min(rec['combined_roi_pct'],rec['combined_min_month_roi_pct'])
            rec['target_distance']=abs(rec['combined_R']-100)
            rows.append(rec)
    o=pd.DataFrame(rows)
    if o.empty: raise RuntimeError('no A-rank cells')
    o['candidate_ok']=(o.combined_R.between(80,120) & (o.a_R>=20))
    o=o.sort_values(['candidate_ok','robust_combined_roi','combined_roi_pct','target_distance','combined_R'],ascending=[False,False,False,True,False])
    o.to_csv(OUT,index=False)

    # Persist race-level rows for audit, without making any rule production.
    settled.to_csv(DETAIL,index=False)

    near=o[o.candidate_ok].copy()
    best=near.iloc[0] if len(near) else o.iloc[0]
    # Also identify the closest-to-100 cell among those with combined ROI>=100,
    # preferring a >=90 monthly floor. This is descriptive model selection only.
    viable=o[(o.combined_roi_pct>=100)&(o.combined_min_month_roi_pct>=90)&(o.a_R>=20)]
    closest=viable.sort_values(['target_distance','robust_combined_roi'],ascending=[True,False]).iloc[0] if len(viable) else None
    maxr=o[(o.combined_roi_pct>=100)&(o.combined_min_month_roi_pct>=90)].sort_values(['combined_R','robust_combined_roi'],ascending=[False,False])
    maxrow=maxr.iloc[0] if len(maxr) else None

    L=['# v271 4-head A-rank expansion audit','',
       '- v268 remains frozen S-rank and is never modified here.',
       '- A-score uses only v270 stable pre-result features and is generated month-walk-forward.',
       '- Evaluation months: Apr-Jun 2026 only; Jul/Aug excluded completely.',
       '- Ticket/settlement: prior-only v96 4-x-y pair order, N=2..20 nearest composite odds 10.5, exact 10,000-yen Dutch/Hamilton.',
       '- Archived odds proxy => retrospective development/model-selection only, NOT prospective/live OOS.', '',
       '## Frozen S benchmark',
       f"- S: {sm.get('s_R',0)}R, head {sm.get('s_head4_rate_pct',np.nan):.2f}%, hit {sm.get('s_hit_pct',np.nan):.2f}%, ROI {sm.get('s_roi_pct',np.nan):.2f}%, monthly floor {sm.get('s_min_month_roi_pct',np.nan):.2f}%.",'',
       '## Best S+A cells around 80-120 races',
       '|gate|PRE|POST|A cut|A R|A head|A hit|A ROI|total R|total head|total hit|total ROI|min month ROI|',
       '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    show=near.head(20) if len(near) else o.head(20)
    for _,r in show.iterrows():
        L.append(f"|{r.gate}|{r.pre_cut:.2f}|{r.post_cut:.2f}|{r.a_score_cut:.2f}|{int(r.a_R)}|{r.a_head4_rate_pct:.2f}%|{r.a_hit_pct:.2f}%|{r.a_roi_pct:.2f}%|{int(r.combined_R)}|{r.combined_head4_rate_pct:.2f}%|{r.combined_hit_pct:.2f}%|{r.combined_roi_pct:.2f}%|{r.combined_min_month_roi_pct:.2f}%|")
    L+=['','## Descriptive checkpoints']
    if closest is not None:
        r=closest; L.append(f"- Closest to 100R with combined ROI>=100% and monthly floor>=90%: {r.gate}, A cut {r.a_score_cut:.2f}, A={int(r.a_R)}R, total={int(r.combined_R)}R, A ROI={r.a_roi_pct:.2f}%, combined ROI={r.combined_roi_pct:.2f}%, floor={r.combined_min_month_roi_pct:.2f}%.")
    else:
        L.append('- No cell reached combined ROI>=100% and monthly floor>=90% with >=20 A races.')
    if maxrow is not None:
        r=maxrow; L.append(f"- Maximum race count while combined ROI>=100% and floor>=90%: total={int(r.combined_R)}R ({r.gate}, A cut {r.a_score_cut:.2f}), combined ROI={r.combined_roi_pct:.2f}%, floor={r.combined_min_month_roi_pct:.2f}%.")
    L+=['','## Guardrail','- Do NOT alter HEAD4_V268_FROZEN_20260910.md from this retrospective search.','- Any A-rank rule chosen from v271 must be frozen as a separate version before September outcomes are inspected/used.','- Formal prospective evaluation starts only after that separate A-rule freeze.','']
    SUM.write_text('\n'.join(L),encoding='utf-8'); print('\n'.join(L))

if __name__=='__main__': main()
