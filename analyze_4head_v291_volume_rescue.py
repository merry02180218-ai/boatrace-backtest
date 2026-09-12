#!/usr/bin/env python3
"""Production-shaped volume research for HEAD4_V291_COMP7.

BASE is immutable: frozen v283 order, prefix N=4, composite>=7.0.  Research only
adds deterministic rescue bets among BASE PASS races.  Rescue uses pair order +
odds only; outcomes are settlement/evaluation only.  Source is hard-guarded to
Apr-Jun. Jul/Aug/Sep outcomes are never read. No model refit and no v96 signal.
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
BASE_N=4; BASE_FLOOR=7.0
FLOORS=tuple(np.arange(5.0,15.01,.5).round(2))
GRID=[('FIXED',n,float(f)) for n in range(2,13) for f in FLOORS]
GRID += [('ADAPT',n,float(f)) for n in range(3,13) for f in FLOORS]


def agg(g):
    if len(g)==0:return {'R':0,'head4_wins':0,'hits':0,'return_yen':0.,'profit_yen':0.,'roi_pct':np.nan}
    ret=float(g.return_yen.sum());cost=len(g)*BANK
    return {'R':len(g),'head4_wins':int(g.head4_win.sum()),'hits':int(g.hit.sum()),
            'return_yen':ret,'profit_yen':ret-cost,'roi_pct':100*ret/cost}


def load_source():
    q=pd.read_csv(SRC,dtype={'race_code':str});q['race_code']=q.race_code.astype(str).str.zfill(12)
    if set(q.month.astype(str).unique())!=set(MONTHS):raise RuntimeError('source must be Apr-Jun only')
    if q.race_code.nunique()!=100 or len(q)!=1900:raise RuntimeError('expected 100 races x N2..20')
    if set(q.n.astype(int).unique())!=set(range(2,21)):raise RuntimeError('N universe mismatch')
    for code,g in q.groupby('race_code'):
        z=g.sort_values('n')
        if len(z)!=19 or np.any(np.diff(z.comp_odds.to_numpy(float))>1e-9):raise RuntimeError(f'bad N curve {code}')
    return q


def scoped(q,scope):return q[q.layer=='S'].copy() if scope=='S' else q.copy()

def base(z):
    b=z[(z.n==BASE_N)&(z.comp_odds>=BASE_FLOOR)].copy()
    if b.race_code.duplicated().any():raise RuntimeError('duplicate BASE race')
    return b


def rescue(z,b,family,param,floor):
    x=z[~z.race_code.isin(set(b.race_code))]
    if family=='FIXED':
        return x[(x.n==int(param))&(x.comp_odds>=float(floor))].copy()
    x=x[(x.n>=2)&(x.n<=int(param))&(x.comp_odds>=float(floor))].sort_values(['race_code','n'])
    return x.groupby('race_code',as_index=False).tail(1).copy() if len(x) else x.iloc[0:0].copy()


def monthly_rows(scope,family,param,floor,b,r,c):
    out=[]
    for m in MONTHS:
        ba,ra,ca=agg(b[b.month==m]),agg(r[r.month==m]),agg(c[c.month==m])
        out.append({'scope':scope,'family':family,'param':int(param),'floor':float(floor),'month':m,
          'R':ca['R'],'return_yen':ca['return_yen'],'profit_yen':ca['profit_yen'],'roi_pct':ca['roi_pct'],
          'base_R':ba['R'],'base_return_yen':ba['return_yen'],'base_roi_pct':ba['roi_pct'],
          'added_R':ra['R'],'added_return_yen':ra['return_yen'],'added_profit_yen':ra['profit_yen'],'added_roi_pct':ra['roi_pct']})
    return out


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


def lomo(scope,A,M,base_month):
    out=[]
    for hold in MONTHS:
        trm=[m for m in MONTHS if m!=hold];rows=[]
        for (f,p,fl),g in M[(M.scope==scope)&M.month.isin(trm)].groupby(['family','param','floor']):
            R=int(g.R.sum());ret=float(g.return_yen.sum());added=int(g.added_R.sum())
            rows.append({'scope':scope,'family':f,'param':int(p),'floor':float(fl),'R':R,'added_R':added,
                         'roi_pct':100*ret/(R*BANK) if R else np.nan,'min_month_roi_pct':float(g.roi_pct.min()),
                         'min_added_per_month':int(g.added_R.min())})
        tr=pd.DataFrame(rows);bb=base_month[base_month.month.isin(trm)]
        br=int(bb.R.sum());bret=float(bb.return_yen.sum());broi=100*bret/(br*BANK);bmin=float(bb.roi_pct.min())
        tier,ch=choose(tr,broi,bmin)
        if ch is None:out.append({'scope':scope,'holdout_month':hold,'status':'NO_CANDIDATE'});continue
        h=M[(M.scope==scope)&(M.month==hold)&(M.family==ch.family)&(M.param==ch.param)&(M.floor==ch.floor)].iloc[0]
        out.append({'scope':scope,'holdout_month':hold,'status':'OK','train_tier':tier,'family':ch.family,
                    'param':int(ch.param),'floor':float(ch.floor),'hold_base_R':int(h.base_R),'hold_added_R':int(h.added_R),
                    'hold_R':int(h.R),'hold_base_roi_pct':float(h.base_roi_pct),'hold_rescue_roi_pct':float(h.added_roi_pct) if pd.notna(h.added_roi_pct) else np.nan,
                    'hold_roi_pct':float(h.roi_pct),'hold_profit_yen':float(h.profit_yen)})
    return out


def main():
    q=load_source();allrows=[];monthrows=[];chosen={};base_months={}
    for scope in ('S+A','S'):
        z=scoped(q,scope);b=base(z);ba=agg(b)
        bm=[]
        for m in MONTHS:
            x=agg(b[b.month==m]);bm.append({'scope':scope,'month':m,'R':x['R'],'return_yen':x['return_yen'],'roi_pct':x['roi_pct']})
        base_month=pd.DataFrame(bm);base_months[scope]=base_month;bmin=float(base_month.roi_pct.min())
        rec=[]
        for f,p,fl in GRID:
            r=rescue(z,b,f,p,fl);c=pd.concat([b,r],ignore_index=True)
            if c.race_code.duplicated().any():raise RuntimeError('rescue overlapped BASE')
            ca,ra=agg(c),agg(r);mm=monthly_rows(scope,f,p,fl,b,r,c);monthrows.extend(mm)
            s={'scope':scope,'family':f,'param':int(p),'floor':float(fl),'R':ca['R'],'added_R':ra['R'],
               'head4_wins':ca['head4_wins'],'hits':ca['hits'],'return_yen':ca['return_yen'],'profit_yen':ca['profit_yen'],
               'roi_pct':ca['roi_pct'],'base_R':ba['R'],'base_roi_pct':ba['roi_pct'],'rescue_roi_pct':ra['roi_pct'],
               'min_month_roi_pct':min(x['roi_pct'] for x in mm),'min_added_per_month':min(x['added_R'] for x in mm)}
            rec.append(s);allrows.append(s)
        sub=pd.DataFrame(rec);chosen[scope]=(*choose(sub,ba['roi_pct'],bmin),ba,bmin)
    A=pd.DataFrame(allrows);M=pd.DataFrame(monthrows)
    lrows=[]
    for scope in ('S+A','S'):lrows.extend(lomo(scope,A,M,base_months[scope]))
    L=pd.DataFrame(lrows)
    A.to_csv(OUT,index=False);M.to_csv(MONTH,index=False);L.to_csv(LOMO,index=False)
    pd.concat([pareto(A[A.scope==s]).assign(frontier_scope=s) for s in ('S+A','S')],ignore_index=True).to_csv(FRONT,index=False)

    payload={'schema':'head4_v291_volume_rescue_research_v1','development_months':list(MONTHS),
      'jul_aug_outcomes_used':False,'september_outcomes_used':False,
      'base':{'n':4,'composite_floor':7.0,'stake_yen':BANK,'immutable':True},'scopes':{}}
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
    lines += ['## Production guard','', '- S scope can be wired after selector + immutable pre-deadline odds audit are implemented.',
              '- S+A stays development-only until A_SCORE LIVE-scale mapping is formally frozen.',
              '- Any promoted rescue gets a new policy version; HEAD4_V291_COMP7 history is not rewritten.']
    CAND.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    SUM.write_text('\n'.join(lines)+'\n',encoding='utf-8');print('\n'.join(lines))

if __name__=='__main__':main()
