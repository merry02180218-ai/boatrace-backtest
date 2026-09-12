#!/usr/bin/env python3
"""Outcome-blind operational variable-N research for immutable HEAD4_V291_COMP7 races.

This does NOT add races.  The frozen v291 entry set remains exactly the races that
pass N=4 composite >= 7.0.  For each such race, the rule may expand beyond Top4
using the frozen v283 pair order and archived pre-deadline closing odds, while
keeping the per-race bank fixed at 10,000 JPY.

Rule family is deliberately small and operational:
  choose the largest N in [4, maxN] whose composite odds remain >= floor.

Development/evaluation uses Apr-Jun 2026 only. Jul/Aug are NON-PRISTINE and all
September outcomes are prohibited. No v96 signal is used.
"""
from __future__ import annotations
from pathlib import Path
import json
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parent
SRC=ROOT/'analysis_v291_4head_composite_odds_alln_exactalive.csv'
OUT=ROOT/'analysis_4head_v291_base_variable_n.csv'
MONTH=ROOT/'analysis_4head_v291_base_variable_n_monthly.csv'
LOMO=ROOT/'analysis_4head_v291_base_variable_n_lomo.csv'
SUM=ROOT/'summary_4head_v291_base_variable_n.md'
CAND=ROOT/'head4_v291_base_variable_n_candidate.json'
BANK=10000
MONTHS=('2026-04','2026-05','2026-06')
FLOORS=(3.0,3.5,4.0,4.5,5.0,5.5,6.0,6.5)
MAXNS=(5,6,8,10,12,16,20)
GRID=[(float(f),int(n)) for f in FLOORS for n in MAXNS]


def metrics(g):
    if len(g)==0:
        return {'R':0,'return_yen':0.0,'profit_yen':0.0,'roi_pct':np.nan,'hit_rate_pct':np.nan,'avg_n':np.nan,'avg_comp_odds':np.nan}
    ret=float(g.return_yen.sum()); cost=len(g)*BANK
    return {'R':int(len(g)),'return_yen':ret,'profit_yen':ret-cost,'roi_pct':100*ret/cost,
            'hit_rate_pct':100*float(g.hit.mean()),'avg_n':float(g.n.mean()),'avg_comp_odds':float(g.comp_odds.mean())}


def load():
    q=pd.read_csv(SRC,dtype={'race_code':str});q['race_code']=q.race_code.astype(str).str.zfill(12)
    if set(q.month.astype(str).unique())!=set(MONTHS): raise RuntimeError('forbidden month in source')
    if set(q.n.astype(int).unique())!=set(range(2,21)): raise RuntimeError('N universe mismatch')
    for code,g in q.groupby('race_code'):
        if len(g)!=19 or g.n.nunique()!=19: raise RuntimeError(f'incomplete N curve {code}')
    base=q[(q.n==4)&(q.comp_odds>=7.0)].copy()
    if len(base)!=29 or base.race_code.nunique()!=29: raise RuntimeError(f'frozen v291 base identity mismatch R={len(base)}')
    return q,base


def select(q,base_ids,floor,maxn,months=MONTHS):
    ids=set(base_ids)
    z=q[(q.month.isin(months))&(q.race_code.isin(ids))&(q.n>=4)&(q.n<=int(maxn))].copy()
    z=z[z.comp_odds>=float(floor)].copy()
    # N=4 is always available because immutable base entry requires composite >=7.
    r=z.sort_values(['race_code','n']).groupby('race_code',as_index=False).tail(1).copy()
    expected=sum(1 for c in ids if str(q.loc[q.race_code.eq(c),'month'].iloc[0]) in months)
    if len(r)!=expected or r.race_code.duplicated().any(): raise RuntimeError('variable-N selection lost/duplicated base race')
    return r


def summarize(q,base_ids,floor,maxn,months=MONTHS):
    r=select(q,base_ids,floor,maxn,months); x=metrics(r); mrows=[]
    for m in months:
        mm=metrics(r[r.month==m]);mrows.append({'floor':floor,'maxn':maxn,'month':m,**mm})
    md=pd.DataFrame(mrows);valid=md[md.R>0]
    return {'floor':floor,'maxn':maxn,**x,'min_month_roi_pct':float(valid.roi_pct.min()) if len(valid) else np.nan,
            'min_month_R':int(md.R.min()) if len(md) else 0},mrows


def choose(tab,base_hit):
    # All rules operate on exactly the immutable 29-race entry set. Require actual
    # ticket expansion and a hit-rate gain; ROI gates are standalone, not masked by
    # any other route.
    common=(tab.R==29)&(tab.avg_n>4.0)&(tab.hit_rate_pct>base_hit)
    tiers=[
      ('STRONG_STABLE',common&(tab.roi_pct>=200)&(tab.min_month_roi_pct>=120)),
      ('SAFE_STABLE',common&(tab.roi_pct>=150)&(tab.min_month_roi_pct>=100)),
      ('POSITIVE_STABLE',common&(tab.roi_pct>=120)&(tab.min_month_roi_pct>=100)),
    ]
    for name,mask in tiers:
        z=tab[mask].sort_values(['min_month_roi_pct','roi_pct','hit_rate_pct','avg_n'],ascending=[False,False,False,True])
        if len(z): return name,z.iloc[0]
    return 'NO_SAFE_VARIABLE_N_CANDIDATE',None


def lomo(q,base_ids,base_hit):
    rows=[]
    for hold in MONTHS:
        train=tuple(m for m in MONTHS if m!=hold); rec=[]
        # base hit threshold must be computed only on the training months for rule selection.
        btr=q[(q.race_code.isin(base_ids))&(q.n==4)&(q.month.isin(train))].copy(); bh=metrics(btr)['hit_rate_pct']
        for f,n in GRID: rec.append(summarize(q,base_ids,f,n,train)[0])
        tier,ch=choose(pd.DataFrame(rec),bh)
        if ch is None:
            rows.append({'holdout_month':hold,'status':'NO_TRAIN_CANDIDATE'});continue
        rv=select(q,base_ids,float(ch.floor),int(ch.maxn),(hold,)); xv=metrics(rv)
        rb=q[(q.race_code.isin(base_ids))&(q.n==4)&(q.month==hold)].copy(); xb=metrics(rb)
        rows.append({'holdout_month':hold,'status':'OK','train_tier':tier,'floor':float(ch.floor),'maxn':int(ch.maxn),
                     'hold_R':xv['R'],'hold_roi_pct':xv['roi_pct'],'hold_profit_yen':xv['profit_yen'],
                     'hold_hit_rate_pct':xv['hit_rate_pct'],'hold_avg_n':xv['avg_n'],
                     'base_hold_roi_pct':xb['roi_pct'],'base_hold_hit_rate_pct':xb['hit_rate_pct'],
                     'roi_delta_vs_base':xv['roi_pct']-xb['roi_pct'],'hit_delta_vs_base':xv['hit_rate_pct']-xb['hit_rate_pct']})
    return pd.DataFrame(rows)


def main():
    q,base=load(); ids=set(base.race_code); bm=metrics(base)
    rows=[];mrows=[]
    for f,n in GRID:
        s,m=summarize(q,ids,f,n);rows.append(s);mrows.extend(m)
    A=pd.DataFrame(rows);M=pd.DataFrame(mrows);tier,ch=choose(A,bm['hit_rate_pct']);L=lomo(q,ids,bm['hit_rate_pct'])
    A.to_csv(OUT,index=False);M.to_csv(MONTH,index=False);L.to_csv(LOMO,index=False)
    lomo_ok=bool(len(L)==3 and L.status.eq('OK').all() and (L.hold_R>0).all() and (L.hold_roi_pct>=100).all())
    payload={'schema':'head4_v291_base_variable_n_v1','development_months':list(MONTHS),
             'jul_aug_outcomes_used':False,'september_outcomes_used':False,'v96_used':False,
             'base':{'policy':'HEAD4_V291_COMP7','R':bm['R'],'roi_pct':bm['roi_pct'],'hit_rate_pct':bm['hit_rate_pct'],'avg_n':4.0,'immutable_entry_set':True},
             'rule_family':'largest N>=4 with composite_odds >= floor, capped at maxN; fixed 10000 JPY bank',
             'selection_tier':tier,'lomo_all_holdouts_profitable':lomo_ok}
    lines=['# HEAD4 v291 base-race variable-N expansion','',
           '- Entry identities remain immutable `HEAD4_V291_COMP7`; no races are added or removed.',
           '- Bank remains exactly ¥10,000 per race; only the number of ranked tickets can expand beyond Top4.',
           '- Rule: largest N with composite odds >= floor, capped by maxN.',
           '- Apr-Jun only; Jul/Aug NON-PRISTINE; September outcomes excluded; no v96.','',
           f'- Baseline: **{bm["R"]}R / ROI {bm["roi_pct"]:.2f}% / hit {bm["hit_rate_pct"]:.2f}% / N=4**.','',
           f'## Selection: {tier}']
    if ch is None:
        lines += ['','No variable-N expansion passed standalone stability + hit-rate gates.']
    else:
        cand={'floor':float(ch.floor),'maxn':int(ch.maxn),'R':int(ch.R),'roi_pct':float(ch.roi_pct),
              'min_month_roi_pct':float(ch.min_month_roi_pct),'hit_rate_pct':float(ch.hit_rate_pct),
              'avg_n':float(ch.avg_n),'avg_comp_odds':float(ch.avg_comp_odds),
              'status':'RESEARCH_CANDIDATE_NOT_FROZEN' if lomo_ok else 'REJECT_LOMO'}
        payload['candidate']=cand
        lines += ['',f'- Rule: **floor={ch.floor:.1f}, maxN={int(ch.maxn)}**',
                  f'- Full Apr-Jun: **{int(ch.R)}R / ROI {ch.roi_pct:.2f}% / hit {ch.hit_rate_pct:.2f}% / avg N {ch.avg_n:.2f}**',
                  f'- Monthly ROI floor: **{ch.min_month_roi_pct:.2f}%**.','',
                  '|month|R|ROI|profit|hit|avg N|','|---|---:|---:|---:|---:|---:|']
        mm=M[(M.floor==ch.floor)&(M.maxn==ch.maxn)].sort_values('month')
        for _,r in mm.iterrows(): lines.append(f'|{r.month}|{int(r.R)}|{r.roi_pct:.2f}%|{r.profit_yen:+.0f}円|{r.hit_rate_pct:.2f}%|{r.avg_n:.2f}|')
    lines += ['','## LOMO','','|holdout|train rule|R|variable ROI|base ROI|variable hit|base hit|','|---|---|---:|---:|---:|---:|---:|']
    for _,r in L.iterrows():
        if r.status!='OK': lines.append(f'|{r.holdout_month}|NO_TRAIN_CANDIDATE|-|-|-|-|-|')
        else: lines.append(f'|{r.holdout_month}|floor={r.floor:.1f}, maxN={int(r.maxn)}|{int(r.hold_R)}|{r.hold_roi_pct:.2f}%|{r.base_hold_roi_pct:.2f}%|{r.hold_hit_rate_pct:.2f}%|{r.base_hold_hit_rate_pct:.2f}%|')
    lines += ['',f'- All LOMO holdout variable-N routes profitable: **{"YES" if lomo_ok else "NO"}**.',
              '- Promotion requires a standalone candidate and all three LOMO holdouts >=100% ROI.',
              '- This research does not modify production v291; any promotion requires a new policy/version.']
    CAND.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    SUM.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(SUM.read_text(encoding='utf-8'))

if __name__=='__main__': main()
