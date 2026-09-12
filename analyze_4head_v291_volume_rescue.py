#!/usr/bin/env python3
"""Production-shaped volume research for HEAD4_V291_COMP7.

Keep the current BASE (v283 prefix N4, composite>=7) unchanged and search only
for deterministic rescue bets among BASE PASS races.  Selection inputs are pair
order + odds only.  Apr-Jun outcomes are used only for development settlement.
Jul/Aug/Sep rows are rejected.  No model refit and no v96 signal are used.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parent
SRC=ROOT/'analysis_v288_4head_composite_odds_alln_detail.csv'
OUT=ROOT/'analysis_4head_v291_volume_rescue_candidates.csv'
MONTH=ROOT/'analysis_4head_v291_volume_rescue_monthly.csv'
FRONT=ROOT/'analysis_4head_v291_volume_rescue_frontier.csv'
LOMO=ROOT/'analysis_4head_v291_volume_rescue_lomo.csv'
CAND=ROOT/'head4_v291_volume_rescue_candidate.json'
SUM=ROOT/'summary_4head_v291_volume_rescue.md'
BANK=10000
MONTHS=('2026-04','2026-05','2026-06')
BASE_N=4
BASE_FLOOR=7.0
FLOORS=tuple(np.arange(5.0,15.01,.5).round(2))
FIXED_NS=tuple(range(2,13))
ADAPT_MAXNS=tuple(range(3,13))


def agg(g):
    if len(g)==0:return {'R':0,'head4_wins':0,'hits':0,'return_yen':0.,'profit_yen':0.,'roi_pct':np.nan}
    ret=float(g.return_yen.sum()); cost=len(g)*BANK
    return {'R':len(g),'head4_wins':int(g.head4_win.sum()),'hits':int(g.hit.sum()),
            'return_yen':ret,'profit_yen':ret-cost,'roi_pct':100*ret/cost}


def load_source():
    q=pd.read_csv(SRC,dtype={'race_code':str});q['race_code']=q.race_code.astype(str).str.zfill(12)
    if set(q.month.astype(str).unique())!=set(MONTHS):raise RuntimeError('source must be Apr-Jun only')
    if q.race_code.nunique()!=100 or len(q)!=1900:raise RuntimeError('expected 100 races x N2..20')
    if set(q.n.astype(int).unique())!=set(range(2,21)):raise RuntimeError('N universe mismatch')
    for code,g in q.groupby('race_code'):
        z=g.sort_values('n')
        if len(z)!=19 or z.n.nunique()!=19:raise RuntimeError(f'incomplete N curve {code}')
        if np.any(np.diff(z.comp_odds.to_numpy(float))>1e-9):raise RuntimeError(f'non-monotone composite {code}')
    return q


def scoped(q,scope,months):
    z=q[q.month.isin(months)]
    return z[z.layer=='S'] if scope=='S' else z


def base_rows(q,scope,months=MONTHS):
    z=scoped(q,scope,months);z=z[z.n==BASE_N]
    return z[z.comp_odds>=BASE_FLOOR].copy()


def pick(g,family,param,floor):
    if family=='FIXED':
        z=g[g.n==int(param)]
        return z.iloc[0] if len(z) and float(z.iloc[0].comp_odds)>=floor else None
    z=g[(g.n>=2)&(g.n<=int(param))&(g.comp_odds>=floor)].sort_values('n')
    return z.iloc[-1] if len(z) else None


def apply_rule(q,scope,family,param,floor,months=MONTHS):
    z=scoped(q,scope,months);b=base_rows(q,scope,months);bc=set(b.race_code)
    add=[]
    for code,g in z[~z.race_code.isin(bc)].groupby('race_code'):
        r=pick(g,family,param,float(floor))
        if r is not None:add.append(r)
    r=pd.DataFrame(add,columns=q.columns) if add else q.iloc[0:0].copy()
    c=pd.concat([b,r],ignore_index=True)
    if c.race_code.duplicated().any():raise RuntimeError('duplicate combined race')
    return b,r,c


def summarize(q,scope,family,param,floor,months=MONTHS):
    b,r,c=apply_rule(q,scope,family,param,floor,months);ba,ra,ca=agg(b),agg(r),agg(c);mm=[]
    for m in months:
        bm,rm,cm=b[b.month==m],r[r.month==m],c[c.month==m];x,y,z=agg(bm),agg(rm),agg(cm)
        mm.append({'scope':scope,'family':family,'param':int(param),'floor':float(floor),'month':m,
                   'R':z['R'],'roi_pct':z['roi_pct'],'profit_yen':z['profit_yen'],
                   'base_R':x['R'],'base_roi_pct':x['roi_pct'],'added_R':y['R'],
                   'added_roi_pct':y['roi_pct'],'added_profit_yen':y['profit_yen']})
    md=pd.DataFrame(mm); vals=md.roi_pct.dropna()
    s={'scope':scope,'family':family,'param':int(param),'floor':float(floor),'R':ca['R'],'added_R':ra['R'],
       'head4_wins':ca['head4_wins'],'hits':ca['hits'],'return_yen':ca['return_yen'],'profit_yen':ca['profit_yen'],
       'roi_pct':ca['roi_pct'],'base_R':ba['R'],'base_roi_pct':ba['roi_pct'],'rescue_roi_pct':ra['roi_pct'],
       'min_month_roi_pct':float(vals.min()) if len(vals) else np.nan,
       'min_added_per_month':int(md.added_R.min()) if len(md) else 0}
    return s,mm


def choose(c,base_roi,base_min):
    common=(c.added_R>=6)&(c.min_added_per_month>=1)
    tiers=[('STRICT_PRESERVE_FLOOR',common&(c.min_month_roi_pct>=base_min-1e-9)&(c.roi_pct>=.8*base_roi)),
           ('BALANCED_150_220',common&(c.min_month_roi_pct>=150)&(c.roi_pct>=220)),
           ('SAFE_VOLUME_120_180',common&(c.min_month_roi_pct>=120)&(c.roi_pct>=180)),
           ('POSITIVE_ALL_MONTHS',common&(c.min_month_roi_pct>=100)&(c.roi_pct>=150))]
    for name,mask in tiers:
        z=c[mask].sort_values(['R','min_month_roi_pct','roi_pct'],ascending=False)
        if len(z):return name,z.iloc[0]
    return 'NO_SAFE_CANDIDATE',None


def pareto(z):
    keep=[]
    for i,r in z.iterrows():
        d=z[(z.R>=r.R)&(z.roi_pct>=r.roi_pct)&(z.min_month_roi_pct>=r.min_month_roi_pct)&
            ((z.R>r.R)|(z.roi_pct>r.roi_pct)|(z.min_month_roi_pct>r.min_month_roi_pct))]
        if len(d)==0:keep.append(i)
    return z.loc[keep].sort_values(['R','min_month_roi_pct','roi_pct'],ascending=False)


def lomo(q,scope,grid):
    rows=[]
    for hold in MONTHS:
        train=tuple(m for m in MONTHS if m!=hold);bt=base_rows(q,scope,train);bta=agg(bt)
        bmin=min(agg(bt[bt.month==m])['roi_pct'] for m in train)
        rec=[summarize(q,scope,f,int(p),float(fl),train)[0] for f,p,fl in grid]
        tier,ch=choose(pd.DataFrame(rec),bta['roi_pct'],bmin)
        if ch is None:
            rows.append({'scope':scope,'holdout_month':hold,'status':'NO_CANDIDATE'});continue
        b,r,c=apply_rule(q,scope,str(ch.family),int(ch.param),float(ch.floor),(hold,));ba,ra,ca=agg(b),agg(r),agg(c)
        rows.append({'scope':scope,'holdout_month':hold,'status':'OK','train_tier':tier,'family':ch.family,
                     'param':int(ch.param),'floor':float(ch.floor),'hold_base_R':ba['R'],'hold_added_R':ra['R'],
                     'hold_R':ca['R'],'hold_base_roi_pct':ba['roi_pct'],'hold_rescue_roi_pct':ra['roi_pct'],
                     'hold_roi_pct':ca['roi_pct'],'hold_profit_yen':ca['profit_yen']})
    return rows


def main():
    q=load_source();grid=[('FIXED',n,float(fl)) for n in FIXED_NS for fl in FLOORS]
    grid += [('ADAPT',n,float(fl)) for n in ADAPT_MAXNS for fl in FLOORS]
    allrows=[];monthrows=[];chosen={};lrows=[]
    for scope in ('S+A','S'):
        rec=[]
        for f,p,fl in grid:
            s,m=summarize(q,scope,f,p,fl);rec.append(s);allrows.append(s);monthrows.extend(m)
        sub=pd.DataFrame(rec);b=base_rows(q,scope);ba=agg(b);bmin=min(agg(b[b.month==m])['roi_pct'] for m in MONTHS)
        tier,ch=choose(sub,ba['roi_pct'],bmin);chosen[scope]=(tier,ch,ba,bmin);lrows.extend(lomo(q,scope,grid))
    A=pd.DataFrame(allrows);M=pd.DataFrame(monthrows if False else monthrows);L=pd.DataFrame(lrows)
    A.to_csv(OUT,index=False);M.to_csv(MONTH,index=False);L.to_csv(LOMO,index=False)
    pd.concat([pareto(A[A.scope==s]).assign(frontier_scope=s) for s in ('S+A','S')],ignore_index=True).to_csv(FRONT,index=False)

    payload={'schema':'head4_v291_volume_rescue_research_v1','development_months':list(MONTHS),
      'jul_aug_outcomes_used':False,'september_outcomes_used':False,
      'base':{'n':BASE_N,'composite_floor':BASE_FLOOR,'stake_yen':BANK,'immutable':True},'scopes':{}}
    lines=['# HEAD4 v291 volume-rescue auto research','',
      '- BASE immutable: v283 prefix N=4 / composite >= 7.0 / 10,000 JPY Dutch.',
      '- Rescue only touches BASE PASS races and uses pair order + odds only.',
      '- Apr-Jun archived odds are development evidence; Jul/Aug/Sep outcomes are not used.','']
    for scope in ('S+A','S'):
        tier,ch,ba,bmin=chosen[scope];d={'selection_tier':tier,'base_R':ba['R'],'base_roi_pct':ba['roi_pct'],'base_min_month_roi_pct':bmin}
        lines += [f'## {scope}','',f'- BASE: {ba["R"]}R / ROI **{ba["roi_pct"]:.2f}%** / monthly floor **{bmin:.2f}%**.',f'- tier: **{tier}**']
        if ch is not None:
            d['candidate']={'family':str(ch.family),'param':int(ch.param),'floor':float(ch.floor),'combined_R':int(ch.R),
                            'added_R':int(ch.added_R),'combined_roi_pct':float(ch.roi_pct),'min_month_roi_pct':float(ch.min_month_roi_pct),
                            'status':'RESEARCH_CANDIDATE_NOT_FROZEN'}
            lines += [f'- rescue: **{ch.family} param={int(ch.param)} floor={ch.floor:.1f}**',
                      f'- combined: **{int(ch.R)}R ({int(ch.added_R):+d}) / ROI {ch.roi_pct:.2f}% / monthly floor {ch.min_month_roi_pct:.2f}%**',
                      f'- rescue-only ROI: **{ch.rescue_roi_pct:.2f}%**','',
                      '|month|combined R|added R|combined ROI|base ROI|added ROI|','|---|---:|---:|---:|---:|---:|']
            mm=M[(M.scope==scope)&(M.family==ch.family)&(M.param==ch.param)&(M.floor==ch.floor)].sort_values('month')
            for _,r in mm.iterrows():
                ar='-' if pd.isna(r.added_roi_pct) else f'{r.added_roi_pct:.2f}%'
                lines.append(f'|{r.month}|{int(r.R)}|{int(r.added_R)}|{r.roi_pct:.2f}%|{r.base_roi_pct:.2f}%|{ar}|')
        payload['scopes'][scope]=d
        lines += ['','### LOMO search-procedure check','','|holdout|train-chosen rule|added R|combined R|combined ROI|','|---|---|---:|---:|---:|']
        for _,r in L[L.scope==scope].iterrows():
            if r.status!='OK':lines.append(f'|{r.holdout_month}|NO_CANDIDATE|-|-|-|')
            else:lines.append(f'|{r.holdout_month}|{r.family} {int(r.param)} / {r.floor:.1f}|{int(r.hold_added_R)}|{int(r.hold_R)}|{r.hold_roi_pct:.2f}%|')
        lines.append('')
    lines += ['## Production guard','', '- S scope can be wired after the selector and immutable pre-deadline odds audit are implemented.',
              '- S+A stays development-only until A_SCORE LIVE-scale mapping is formally frozen.',
              '- Any promoted rescue gets a new policy version; HEAD4_V291_COMP7 history is not rewritten.']
    CAND.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    SUM.write_text('\n'.join(lines)+'\n',encoding='utf-8');print('\n'.join(lines))

if __name__=='__main__':main()
