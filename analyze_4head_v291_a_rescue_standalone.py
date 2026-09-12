#!/usr/bin/env python3
"""Research an A-layer rescue that is profitable on its own.

Immutable base: HEAD4_V291_COMP7 (N4, composite >=7) on frozen v283 ordering.
Only BASE-PASS races already labelled A by frozen v273 OOF semantics may be
rescued. Candidate rules use only prefix length N and contemporaneous composite
odds, so every selected rule is live-computable from the frozen full pair order
and one official pre-deadline odds snapshot.

Hard discipline:
- input must be Apr-Jun only (Jul/Aug/Sep rejected)
- no model refit, no v96, no September outcomes
- rescue-only economics must stand on their own; BASE profit cannot hide losses
- LOMO chooses on two months and tests on the untouched third month
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parent
SRC=ROOT/'analysis_v288_4head_composite_odds_alln_detail.csv'
OUT=ROOT/'analysis_4head_v291_a_rescue_standalone.csv'
MONTH=ROOT/'analysis_4head_v291_a_rescue_standalone_monthly.csv'
LOMO=ROOT/'analysis_4head_v291_a_rescue_standalone_lomo.csv'
SUM=ROOT/'summary_4head_v291_a_rescue_standalone.md'
CAND=ROOT/'head4_v291_a_rescue_candidate.json'
BANK=10000
MONTHS=('2026-04','2026-05','2026-06')
FLOORS=tuple(np.arange(4.0,15.01,.5).round(2))
GRID=[('FIXED',n,float(f)) for n in range(2,13) for f in FLOORS]
GRID += [('ADAPT',n,float(f)) for n in range(3,13) for f in FLOORS]


def met(g):
    if len(g)==0:return {'R':0,'return_yen':0.,'profit_yen':0.,'roi_pct':np.nan,'head_rate_pct':np.nan,'hit_rate_pct':np.nan}
    ret=float(g.return_yen.sum()); cost=len(g)*BANK
    return {'R':len(g),'return_yen':ret,'profit_yen':ret-cost,'roi_pct':100*ret/cost,
            'head_rate_pct':100*float(g.head4_win.mean()),'hit_rate_pct':100*float(g.hit.mean())}


def load():
    q=pd.read_csv(SRC,dtype={'race_code':str});q['race_code']=q.race_code.astype(str).str.zfill(12)
    if set(q.month.astype(str).unique())!=set(MONTHS):raise RuntimeError('forbidden month in source')
    if q.race_code.nunique()!=100 or len(q)!=1900:raise RuntimeError('expected frozen 100-race x N2..20 source')
    if set(q.layer.astype(str).unique())-{'S','A'}:raise RuntimeError('unexpected layer')
    if set(q.n.astype(int).unique())!=set(range(2,21)):raise RuntimeError('N universe mismatch')
    for code,g in q.groupby('race_code'):
        z=g.sort_values('n')
        if len(z)!=19 or z.n.nunique()!=19:raise RuntimeError(f'incomplete N curve {code}')
        if np.any(np.diff(z.comp_odds.to_numpy(float))>1e-9):raise RuntimeError(f'non-monotone comp {code}')
    return q


def base(q,months=MONTHS):
    z=q[(q.month.isin(months))&(q.n==4)&(q.comp_odds>=7.0)].copy()
    if z.race_code.duplicated().any():raise RuntimeError('duplicate base')
    return z


def a_pass(q,months=MONTHS):
    b=set(base(q,months).race_code)
    return q[(q.month.isin(months))&(q.layer=='A')&(~q.race_code.isin(b))].copy()


def rescue(q,family,param,floor,months=MONTHS):
    z=a_pass(q,months)
    if family=='FIXED':
        r=z[(z.n==int(param))&(z.comp_odds>=float(floor))].copy()
    else:
        z=z[(z.n>=2)&(z.n<=int(param))&(z.comp_odds>=float(floor))].sort_values(['race_code','n'])
        r=z.groupby('race_code',as_index=False).tail(1).copy() if len(z) else z.iloc[0:0].copy()
    if r.race_code.duplicated().any():raise RuntimeError('duplicate rescue race')
    return r


def summarize(q,f,p,fl,months=MONTHS):
    r=rescue(q,f,p,fl,months); rm=met(r); rows=[]
    for m in months:
        x=met(r[r.month==m]); rows.append({'family':f,'param':int(p),'floor':float(fl),'month':m,**x})
    md=pd.DataFrame(rows); valid=md[md.R>0]
    s={'family':f,'param':int(p),'floor':float(fl),**rm,
       'min_month_roi_pct':float(valid.roi_pct.min()) if len(valid) else np.nan,
       'min_month_R':int(md.R.min()) if len(md) else 0}
    return s,rows


def choose(tab):
    # Volume first, but extra bets must be independently profitable in every month.
    tiers=[
      ('STRONG_120_ALL_MONTHS',(tab.R>=12)&(tab.min_month_R>=2)&(tab.roi_pct>=140)&(tab.min_month_roi_pct>=120)),
      ('PROFITABLE_110_ALL_MONTHS',(tab.R>=12)&(tab.min_month_R>=2)&(tab.roi_pct>=125)&(tab.min_month_roi_pct>=110)),
      ('POSITIVE_ALL_MONTHS',(tab.R>=9)&(tab.min_month_R>=2)&(tab.roi_pct>=115)&(tab.min_month_roi_pct>=100)),
    ]
    for name,mask in tiers:
        z=tab[mask].sort_values(['R','min_month_roi_pct','roi_pct'],ascending=False)
        if len(z):return name,z.iloc[0]
    return 'NO_STANDALONE_SAFE_CANDIDATE',None


def lomo(q):
    out=[]
    for hold in MONTHS:
        train=tuple(m for m in MONTHS if m!=hold); rec=[]
        for f,p,fl in GRID:rec.append(summarize(q,f,p,fl,train)[0])
        tier,ch=choose(pd.DataFrame(rec))
        if ch is None:
            out.append({'holdout_month':hold,'status':'NO_TRAIN_CANDIDATE'});continue
        r=rescue(q,str(ch.family),int(ch.param),float(ch.floor),(hold,)); x=met(r)
        out.append({'holdout_month':hold,'status':'OK','train_tier':tier,'family':ch.family,'param':int(ch.param),
                    'floor':float(ch.floor),'hold_R':x['R'],'hold_roi_pct':x['roi_pct'],'hold_profit_yen':x['profit_yen'],
                    'hold_head_rate_pct':x['head_rate_pct'],'hold_hit_rate_pct':x['hit_rate_pct']})
    return pd.DataFrame(out)


def main():
    q=load(); allr=[]; allm=[]
    for f,p,fl in GRID:
        s,m=summarize(q,f,p,fl);allr.append(s);allm.extend(m)
    A=pd.DataFrame(allr);M=pd.DataFrame(allm);tier,ch=choose(A);L=lomo(q)
    A.to_csv(OUT,index=False);M.to_csv(MONTH,index=False);L.to_csv(LOMO,index=False)
    b=base(q); bm=met(b)
    payload={'schema':'head4_v291_a_rescue_research_v1','development_months':list(MONTHS),
             'jul_aug_outcomes_used':False,'september_outcomes_used':False,'v96_used':False,
             'base':{'policy':'HEAD4_V291_COMP7','R':bm['R'],'immutable':True},'selection_tier':tier}
    lines=['# HEAD4 v291 A-layer standalone rescue research','',
           '- Existing HEAD4_V291_COMP7 bets are immutable and excluded from rescue evaluation.',
           '- Rescue universe = frozen v273 A-layer races that current COMP7 base passes.',
           '- Rule inputs = frozen v283 prefix order + pre-deadline odds only; Top4 is not fixed.',
           '- Jul/Aug/Sep outcomes are excluded. No v96.','',
           f'- Current BASE: **{bm["R"]}R / ROI {bm["roi_pct"]:.2f}%**.','',
           f'## Selection: {tier}']
    if ch is None:
        lines += ['','No A-rescue rule passed standalone monthly-profitability guardrails.']
    else:
        payload['candidate']={'family':str(ch.family),'param':int(ch.param),'floor':float(ch.floor),'R':int(ch.R),
                              'roi_pct':float(ch.roi_pct),'min_month_roi_pct':float(ch.min_month_roi_pct),
                              'status':'RESEARCH_CANDIDATE_NOT_FROZEN'}
        lines += ['',f'- Rule: **{ch.family} param={int(ch.param)} / composite >= {ch.floor:.1f}**',
                  f'- Added standalone: **{int(ch.R)}R / ROI {ch.roi_pct:.2f}% / monthly floor {ch.min_month_roi_pct:.2f}%**.',
                  f'- Head rate {ch.head_rate_pct:.2f}% / trifecta hit {ch.hit_rate_pct:.2f}%.','',
                  '|month|added R|standalone ROI|profit|','|---|---:|---:|---:|']
        z=M[(M.family==ch.family)&(M.param==ch.param)&(M.floor==ch.floor)].sort_values('month')
        for _,r in z.iterrows():lines.append(f'|{r.month}|{int(r.R)}|{r.roi_pct:.2f}%|{r.profit_yen:+.0f}円|')
    lines += ['','## LOMO selection-procedure check','','|holdout|train-selected rule|hold R|hold ROI|hold profit|',
              '|---|---|---:|---:|---:|']
    for _,r in L.iterrows():
        if r.status!='OK':lines.append(f'|{r.holdout_month}|NO_TRAIN_CANDIDATE|-|-|-|')
        else:lines.append(f'|{r.holdout_month}|{r.family} {int(r.param)} / {r.floor:.1f}|{int(r.hold_R)}|{r.hold_roi_pct:.2f}%|{r.hold_profit_yen:+.0f}円|')
    lomo_ok=bool(len(L)==3 and L.status.eq('OK').all() and (L.hold_R>=1).all() and (L.hold_roi_pct>=100).all())
    payload['lomo_all_holdouts_profitable']=lomo_ok
    lines += ['',f'- All LOMO holdout rescue ROIs >=100%: **{"YES" if lomo_ok else "NO"}**.','',
              '## Production decision gate','',
              '- Promotion requires both a standalone-safe fixed rule and all LOMO held-out months >=100%.',
              '- Even then A-layer LIVE score-scale mapping must be frozen outcome-blind before deployment.',
              '- Formal prospective performance begins only after a new policy version + official pre-deadline odds audit are operational.']
    CAND.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    SUM.write_text('\n'.join(lines)+'\n',encoding='utf-8');print('\n'.join(lines))

if __name__=='__main__':main()
