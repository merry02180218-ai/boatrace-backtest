#!/usr/bin/env python3
"""Leakage-disciplined A-layer variable-N target-composite rescue research.

This expands the rejected FIXED/ADAPT prefix search without touching the frozen
HEAD4_V291_COMP7 bets.  For each frozen v273 A race that the current base passes,
the ticket count is selected only from the pre-result v283 prefix composite-odds
curve: among N=2..maxN choose the N whose composite odds is closest to a fixed
target, then require a fixed minimum composite floor.  Thus Top4 is not fixed,
and the rule is directly reproducible from a pre-deadline official 120/120 odds
snapshot.

Hard guards: Apr-Jun only; no Jul/Aug/Sep outcomes; no v96; exact 10,000 JPY
settlement already encoded in the frozen all-N development table; BASE immutable.
"""
from __future__ import annotations
from pathlib import Path
import json
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parent
SRC=ROOT/'analysis_v288_4head_composite_odds_alln_detail.csv'
OUT=ROOT/'analysis_4head_v291_a_targetcomp_rescue.csv'
MONTH=ROOT/'analysis_4head_v291_a_targetcomp_rescue_monthly.csv'
LOMO=ROOT/'analysis_4head_v291_a_targetcomp_rescue_lomo.csv'
SUM=ROOT/'summary_4head_v291_a_targetcomp_rescue.md'
CAND=ROOT/'head4_v291_a_targetcomp_rescue_candidate.json'
BANK=10000
MONTHS=('2026-04','2026-05','2026-06')
TARGETS=tuple(np.arange(5.0,15.01,.5).round(2))
MAXNS=(4,6,8,10,12,16,20)
FLOORS=tuple(np.arange(3.0,8.01,.5).round(2))
GRID=[(float(t),int(n),float(f)) for t in TARGETS for n in MAXNS for f in FLOORS]


def met(g):
    if len(g)==0:return {'R':0,'return_yen':0.,'profit_yen':0.,'roi_pct':np.nan,'head_rate_pct':np.nan,'hit_rate_pct':np.nan,'avg_n':np.nan,'avg_comp_odds':np.nan}
    ret=float(g.return_yen.sum());cost=len(g)*BANK
    return {'R':int(len(g)),'return_yen':ret,'profit_yen':ret-cost,'roi_pct':100*ret/cost,
            'head_rate_pct':100*float(g.head4_win.mean()),'hit_rate_pct':100*float(g.hit.mean()),
            'avg_n':float(g.n.mean()),'avg_comp_odds':float(g.comp_odds.mean())}


def load():
    q=pd.read_csv(SRC,dtype={'race_code':str});q['race_code']=q.race_code.astype(str).str.zfill(12)
    if set(q.month.astype(str).unique())!=set(MONTHS):raise RuntimeError('forbidden month in all-N source')
    if q.race_code.nunique()!=100 or len(q)!=1900:raise RuntimeError('expected exactly 100 races x N2..20')
    if set(q.layer.astype(str).unique())-{'S','A'}:raise RuntimeError('unexpected layer')
    if set(q.n.astype(int).unique())!=set(range(2,21)):raise RuntimeError('N universe mismatch')
    for code,g in q.groupby('race_code'):
        z=g.sort_values('n')
        if len(z)!=19 or z.n.nunique()!=19:raise RuntimeError(f'incomplete N curve {code}')
        if np.any(np.diff(z.comp_odds.to_numpy(float))>1e-9):raise RuntimeError(f'non-monotone composite curve {code}')
    return q


def base(q,months=MONTHS):
    z=q[(q.month.isin(months))&(q.n==4)&(q.comp_odds>=7.0)].copy()
    if z.race_code.duplicated().any():raise RuntimeError('duplicate base race')
    return z


def a_universe(q,months=MONTHS):
    b=set(base(q,months).race_code)
    return q[(q.month.isin(months))&(q.layer=='A')&(~q.race_code.isin(b))].copy()


def select(q,target,maxn,floor,months=MONTHS):
    z=a_universe(q,months)
    z=z[(z.n>=2)&(z.n<=int(maxn))].copy()
    if z.empty:return z
    z['dist']=(z.comp_odds-float(target)).abs()
    # deterministic tie-break: fewer tickets first.
    r=z.sort_values(['race_code','dist','n']).groupby('race_code',as_index=False).head(1).copy()
    r=r[r.comp_odds>=float(floor)].copy()
    if r.race_code.duplicated().any():raise RuntimeError('duplicate rescue selection')
    return r


def summarize(q,target,maxn,floor,months=MONTHS):
    r=select(q,target,maxn,floor,months);rm=met(r);mrs=[]
    for m in months:
        x=met(r[r.month==m]);mrs.append({'target':target,'maxn':maxn,'floor':floor,'month':m,**x})
    md=pd.DataFrame(mrs);valid=md[md.R>0]
    s={'target':target,'maxn':maxn,'floor':floor,**rm,
       'min_month_R':int(md.R.min()) if len(md) else 0,
       'min_month_roi_pct':float(valid.roi_pct.min()) if len(valid) else np.nan}
    return s,mrs


def choose(tab):
    tiers=[
      ('STRONG_ALL_MONTHS',(tab.R>=12)&(tab.min_month_R>=2)&(tab.roi_pct>=140)&(tab.min_month_roi_pct>=120)),
      ('SAFE_ALL_MONTHS',(tab.R>=12)&(tab.min_month_R>=2)&(tab.roi_pct>=125)&(tab.min_month_roi_pct>=110)),
      ('POSITIVE_ALL_MONTHS',(tab.R>=9)&(tab.min_month_R>=2)&(tab.roi_pct>=115)&(tab.min_month_roi_pct>=100)),
    ]
    for name,mask in tiers:
        z=tab[mask].sort_values(['R','min_month_roi_pct','roi_pct','avg_n'],ascending=[False,False,False,True])
        if len(z):return name,z.iloc[0]
    return 'NO_STANDALONE_SAFE_CANDIDATE',None


def lomo(q):
    rows=[]
    for hold in MONTHS:
        trmons=tuple(m for m in MONTHS if m!=hold); rec=[]
        for t,n,f in GRID:rec.append(summarize(q,t,n,f,trmons)[0])
        tier,ch=choose(pd.DataFrame(rec))
        if ch is None:
            rows.append({'holdout_month':hold,'status':'NO_TRAIN_CANDIDATE'});continue
        r=select(q,float(ch.target),int(ch.maxn),float(ch.floor),(hold,));x=met(r)
        rows.append({'holdout_month':hold,'status':'OK','train_tier':tier,'target':float(ch.target),'maxn':int(ch.maxn),
                     'floor':float(ch.floor),'hold_R':x['R'],'hold_roi_pct':x['roi_pct'],'hold_profit_yen':x['profit_yen'],
                     'hold_avg_n':x['avg_n'],'hold_comp_odds':x['avg_comp_odds']})
    return pd.DataFrame(rows)


def main():
    q=load();rows=[];mrows=[]
    for t,n,f in GRID:
        s,m=summarize(q,t,n,f);rows.append(s);mrows.extend(m)
    A=pd.DataFrame(rows);M=pd.DataFrame(mrows);tier,ch=choose(A);L=lomo(q)
    A.to_csv(OUT,index=False);M.to_csv(MONTH,index=False);L.to_csv(LOMO,index=False)
    bm=met(base(q));lomo_ok=bool(len(L)==3 and L.status.eq('OK').all() and (L.hold_R>=1).all() and (L.hold_roi_pct>=100).all())
    payload={'schema':'head4_v291_a_targetcomp_rescue_v1','development_months':list(MONTHS),
             'jul_aug_outcomes_used':False,'september_outcomes_used':False,'v96_used':False,
             'base':{'policy':'HEAD4_V291_COMP7','R':bm['R'],'immutable':True},'selection_tier':tier,
             'lomo_all_holdouts_profitable':lomo_ok}
    lines=['# HEAD4 v291 A-layer target-composite variable-N rescue','',
           '- BASE HEAD4_V291_COMP7 bets are immutable and excluded from rescue economics.',
           '- Rescue universe = frozen v273 A-layer races outside the current N4/COMP7 bets.',
           '- N is chosen from the frozen v283 prefix curve by fixed target composite odds; Top4 is not fixed.',
           '- Rule inputs are pre-result pair order + official odds only. No v96. Jul/Aug/Sep outcomes excluded.','',
           f'- BASE: **{bm["R"]}R / ROI {bm["roi_pct"]:.2f}%**.','',f'## Selection: {tier}']
    if ch is None:
        lines+=['','No target-composite A rescue passed the standalone all-month safety tiers.']
    else:
        payload['candidate']={'target':float(ch.target),'maxn':int(ch.maxn),'floor':float(ch.floor),'R':int(ch.R),
                              'roi_pct':float(ch.roi_pct),'min_month_roi_pct':float(ch.min_month_roi_pct),
                              'avg_n':float(ch.avg_n),'avg_comp_odds':float(ch.avg_comp_odds),'status':'RESEARCH_CANDIDATE_NOT_FROZEN'}
        lines += ['',f'- Rule: **target={ch.target:.1f}, maxN={int(ch.maxn)}, composite floor={ch.floor:.1f}**',
                  f'- Added standalone: **{int(ch.R)}R / ROI {ch.roi_pct:.2f}% / monthly floor {ch.min_month_roi_pct:.2f}%**',
                  f'- avg N {ch.avg_n:.2f} / avg composite {ch.avg_comp_odds:.3f}.','',
                  '|month|R|ROI|profit|avg N|','|---|---:|---:|---:|---:|']
        mm=M[(M.target==ch.target)&(M.maxn==ch.maxn)&(M.floor==ch.floor)].sort_values('month')
        for _,r in mm.iterrows():lines.append(f'|{r.month}|{int(r.R)}|{r.roi_pct:.2f}%|{r.profit_yen:+.0f}円|{r.avg_n:.2f}|')
    lines += ['','## LOMO','','|holdout|train rule|hold R|hold ROI|hold profit|','|---|---|---:|---:|---:|']
    for _,r in L.iterrows():
        if r.status!='OK':lines.append(f'|{r.holdout_month}|NO_TRAIN_CANDIDATE|-|-|-|')
        else:lines.append(f'|{r.holdout_month}|target {r.target:.1f} / maxN {int(r.maxn)} / floor {r.floor:.1f}|{int(r.hold_R)}|{r.hold_roi_pct:.2f}%|{r.hold_profit_yen:+.0f}円|')
    lines += ['',f'- All held-out rescue ROIs >=100%: **{"YES" if lomo_ok else "NO"}**.','',
              '## Promotion guard','- Promotion requires a selected standalone-safe rule AND all three LOMO holdouts >=100%.',
              '- A_SCORE LIVE scale must also be frozen outcome-blind before any production use.',
              '- A promoted rule receives a new policy ID; v291 history remains unchanged.']
    CAND.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    SUM.write_text('\n'.join(lines)+'\n',encoding='utf-8');print('\n'.join(lines))

if __name__=='__main__':main()
