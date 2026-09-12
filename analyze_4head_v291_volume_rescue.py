#!/usr/bin/env python3
"""Auto-research a production-feasible volume extension for HEAD4_V291_COMP7.

The current N4/composite>=7 BET set is immutable BASE. Research may only ADD
races that BASE passed. It never changes a BASE ticket, BASE stake, or BASE
BET/PASS decision. Rescue selection uses only the frozen v283 pair order and
archived odds; result columns are used only after selection for Apr-Jun
settlement/evaluation.

Safety:
- source must contain Apr-Jun only; Jul/Aug/Sep rows are rejected
- no head-model refit, no threshold changes, no v96
- every BET = 10,000 JPY, using already-settled exact Dutch returns in v288
- candidate families are deterministic and live-computable from one odds snapshot
- LOMO diagnostic selects parameters on two months and evaluates the third
"""
from __future__ import annotations

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
FLOORS=tuple(np.arange(5.0,15.01,0.5).round(2))
FIXED_NS=tuple(range(2,13))
ADAPT_MAXNS=tuple(range(3,13))


def agg(g: pd.DataFrame) -> dict:
    if g.empty:
        return {'R':0,'head4_wins':0,'hits':0,'return_yen':0.0,'profit_yen':0.0,'roi_pct':float('nan')}
    ret=float(g.return_yen.sum()); cost=len(g)*BANK
    return {'R':len(g),'head4_wins':int(g.head4_win.sum()),'hits':int(g.hit.sum()),
            'return_yen':ret,'profit_yen':ret-cost,'roi_pct':100*ret/cost}


def load_source() -> pd.DataFrame:
    q=pd.read_csv(SRC,dtype={'race_code':str})
    q['race_code']=q.race_code.astype(str).str.zfill(12)
    got=set(q.month.astype(str).unique())
    if got != set(MONTHS):
        raise RuntimeError(f'forbidden/unexpected months in source: {sorted(got)}')
    if q.race_code.nunique()!=100 or len(q)!=1900:
        raise RuntimeError(f'expected 100 races x N2..20 = 1900 rows, got {q.race_code.nunique()} / {len(q)}')
    if set(q.n.astype(int).unique()) != set(range(2,21)):
        raise RuntimeError('N universe mismatch')
    for code,g in q.groupby('race_code'):
        if len(g)!=19 or g.n.nunique()!=19:
            raise RuntimeError(f'incomplete N curve: {code}')
        z=g.sort_values('n').comp_odds.to_numpy(float)
        if np.any(np.diff(z)>1e-9):
            raise RuntimeError(f'non-monotone composite curve: {code}')
    return q


def base_rows(q: pd.DataFrame, scope: str, months=MONTHS) -> pd.DataFrame:
    z=q[(q.n==BASE_N)&q.month.isin(months)].copy()
    if scope=='S': z=z[z.layer=='S']
    return z[z.comp_odds>=BASE_FLOOR].copy()


def universe_codes(q: pd.DataFrame, scope: str, months=MONTHS) -> set[str]:
    z=q[q.month.isin(months)]
    if scope=='S': z=z[z.layer=='S']
    return set(z.race_code.astype(str))


def pick_rescue(qrace: pd.DataFrame, family: str, param: int, floor: float):
    if family=='FIXED':
        z=qrace[qrace.n==int(param)]
        if z.empty:return None
        r=z.iloc[0]
        return r if float(r.comp_odds)>=floor else None
    if family=='ADAPT':
        z=qrace[(qrace.n>=2)&(qrace.n<=int(param))&(qrace.comp_odds>=floor)].sort_values('n')
        return z.iloc[-1] if len(z) else None
    raise ValueError(family)


def apply_rule(q: pd.DataFrame, scope: str, family: str, param: int, floor: float, months=MONTHS):
    b=base_rows(q,scope,months)
    bc=set(b.race_code.astype(str)); uc=universe_codes(q,scope,months)
    add=[]
    qq=q[q.month.isin(months)]
    if scope=='S':qq=qq[qq.layer=='S']
    for _,g in qq[qq.race_code.isin(uc-bc)].groupby('race_code'):
        r=pick_rescue(g,family,param,float(floor))
        if r is not None:add.append(r)
    rescue=pd.DataFrame(add,columns=q.columns) if add else q.iloc[0:0].copy()
    combined=pd.concat([b,rescue],ignore_index=True)
    if combined.race_code.duplicated().any():raise RuntimeError('duplicate race in combined policy')
    return b,rescue,combined


def summarize_policy(q,scope,family,param,floor,months=MONTHS):
    b,r,c=apply_rule(q,scope,family,param,floor,months)
    a=agg(c); ba=agg(b); ra=agg(r)
    mr=[]
    for m in months:
        cm=c[c.month==m]; rm=r[r.month==m]; bm=b[b.month==m]
        ca=agg(cm); raa=agg(rm); baa=agg(bm)
        mr.append({'scope':scope,'family':family,'param':param,'floor':floor,'month':m,
                   'R':ca['R'],'roi_pct':ca['roi_pct'],'profit_yen':ca['profit_yen'],
                   'base_R':baa['R'],'base_roi_pct':baa['roi_pct'],
                   'added_R':raa['R'],'added_roi_pct':raa['roi_pct'],'added_profit_yen':raa['profit_yen']})
    mm=pd.DataFrame(mr)
    vals=mm.roi_pct.dropna()
    return {
        'scope':scope,'family':family,'param':int(param),'floor':float(floor),
        'R':a['R'],'added_R':ra['R'],'head4_wins':a['head4_wins'],'hits':a['hits'],
        'return_yen':a['return_yen'],'profit_yen':a['profit_yen'],'roi_pct':a['roi_pct'],
        'base_R':ba['R'],'base_roi_pct':ba['roi_pct'],'rescue_roi_pct':ra['roi_pct'],
        'min_month_roi_pct':float(vals.min()) if len(vals) else float('nan'),
        'min_added_per_month':int(mm.added_R.min()) if len(mm) else 0,
        'max_added_per_month':int(mm.added_R.max()) if len(mm) else 0,
    }, mr


def pareto(df: pd.DataFrame) -> pd.DataFrame:
    z=df.copy(); keep=[]
    for i,r in z.iterrows():
        dom=z[(z.R>=r.R)&(z.roi_pct>=r.roi_pct)&(z.min_month_roi_pct>=r.min_month_roi_pct)&
              ((z.R>r.R)|(z.roi_pct>r.roi_pct)|(z.min_month_roi_pct>r.min_month_roi_pct))]
        if dom.empty:keep.append(i)
    return z.loc[keep].sort_values(['R','min_month_roi_pct','roi_pct'],ascending=[False,False,False])


def choose_tier(c: pd.DataFrame, base_roi: float, base_min: float):
    common=(c.added_R>=6)&(c.min_added_per_month>=1)
    tiers=[
        ('STRICT_PRESERVE_FLOOR', common&(c.min_month_roi_pct>=base_min-1e-9)&(c.roi_pct>=0.80*base_roi)),
        ('BALANCED_150_220', common&(c.min_month_roi_pct>=150.0)&(c.roi_pct>=220.0)),
        ('SAFE_VOLUME_120_180', common&(c.min_month_roi_pct>=120.0)&(c.roi_pct>=180.0)),
        ('POSITIVE_ALL_MONTHS', common&(c.min_month_roi_pct>=100.0)&(c.roi_pct>=150.0)),
    ]
    for name,mask in tiers:
        z=c[mask].copy()
        if len(z):
            z=z.sort_values(['R','min_month_roi_pct','roi_pct','added_R'],ascending=[False,False,False,False])
            return name,z.iloc[0]
    return 'NO_SAFE_CANDIDATE',None


def lomo(q: pd.DataFrame, scope: str, grid: pd.DataFrame):
    rows=[]
    for hold in MONTHS:
        train=tuple(m for m in MONTHS if m!=hold)
        btrain=base_rows(q,scope,train); bta=agg(btrain)
        bm=[agg(btrain[btrain.month==m])['roi_pct'] for m in train]
        bmin=float(np.nanmin(bm))
        rec=[]
        for _,r in grid.iterrows():
            s,_=summarize_policy(q,scope,r.family,int(r.param),float(r.floor),train)
            rec.append(s)
        tr=pd.DataFrame(rec)
        tier,ch=choose_tier(tr,bta['roi_pct'],bmin)
        if ch is None:
            rows.append({'scope':scope,'holdout_month':hold,'status':'NO_CANDIDATE'})
            continue
        _,res,comb=apply_rule(q,scope,str(ch.family),int(ch.param),float(ch.floor),(hold,))
        ca=agg(comb);ra=agg(res);ba=agg(base_rows(q,scope,(hold,)))
        rows.append({'scope':scope,'holdout_month':hold,'status':'OK','train_tier':tier,
                     'family':ch.family,'param':int(ch.param),'floor':float(ch.floor),
                     'hold_base_R':ba['R'],'hold_added_R':ra['R'],'hold_R':ca['R'],
                     'hold_base_roi_pct':ba['roi_pct'],'hold_rescue_roi_pct':ra['roi_pct'],
                     'hold_roi_pct':ca['roi_pct'],'hold_profit_yen':ca['profit_yen']})
    return rows


def main():
    q=load_source(); allrows=[]; monthrows=[]
    grid=[]
    for n in FIXED_NS:
        for fl in FLOORS:grid.append(('FIXED',n,float(fl)))
    for n in ADAPT_MAXNS:
        for fl in FLOORS:grid.append(('ADAPT',n,float(fl)))
    grid_df=pd.DataFrame(grid,columns=['family','param','floor'])

    chosen={}; lrows=[]
    for scope in ('S+A','S'):
        for family,param,fl in grid:
            s,m=summarize_policy(q,scope,family,param,fl)
            allrows.append(s);monthrows.extend(m)
        sub=pd.DataFrame([x for x in allrows if x['scope']==scope])
        b=base_rows(q,scope);ba=agg(b)
        bmin=min(agg(b[b.month==m])['roi_pct'] for m in MONTHS)
        tier,ch=choose_tier(sub,ba['roi_pct'],bmin)
        chosen[scope]=(tier,ch,ba,bmin)
        lrows.extend(lomo(q,scope,grid_df))

    A=pd.DataFrame(allrows); M=pd.DataFrame(monthrows if False else monthrows); L=pd.DataFrame(lrows)
    A.to_csv(OUT,index=False);M.to_csv(MONTH,index=False);L.to_csv(LOMO,index=False)
    fronts=[]
    for scope in ('S+A','S'):
        f=pareto(A[A.scope==scope]);f.insert(0,'frontier_scope',scope);fronts.append(f)
    F=pd.concat(fronts,ignore_index=True);F.to_csv(FRONT,index=False)

    payload={'schema':'head4_v291_volume_rescue_research_v1','generated_from':'analysis_v288_4head_composite_odds_alln_detail.csv',
             'development_months':list(MONTHS),'jul_aug_outcomes_used':False,'september_outcomes_used':False,
             'base':{'n':BASE_N,'composite_floor':BASE_FLOOR,'stake_yen':BANK,'immutable':True},'scopes':{}}
    for scope,(tier,ch,ba,bmin) in chosen.items():
        payload['scopes'][scope]={'selection_tier':tier,'base_R':ba['R'],'base_roi_pct':ba['roi_pct'],'base_min_month_roi_pct':bmin}
        if ch is not None:
            payload['scopes'][scope]['candidate']={'family':str(ch.family),'param':int(ch.param),'floor':float(ch.floor),
                'combined_R':int(ch.R),'added_R':int(ch.added_R),'combined_roi_pct':float(ch.roi_pct),
                'min_month_roi_pct':float(ch.min_month_roi_pct),'status':'RESEARCH_CANDIDATE_NOT_FROZEN'}
    CAND.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

    lines=['# HEAD4 v291 volume-rescue auto research','',
      '- BASE is immutable: v283 order, N=4, composite >= 7.0, 10,000 JPY Dutch.',
      '- Rescue is evaluated **only on BASE PASS races**; BASE bets are never changed.',
      '- Candidate inputs are frozen pair order + odds only. Outcomes are settlement/evaluation only.',
      '- Source is hard-rejected unless it contains Apr-Jun only. Jul/Aug and September outcomes are not used.',
      '- This is development evidence from archived odds, not formal prospective OOS.','']
    for scope in ('S+A','S'):
        tier,ch,ba,bmin=chosen[scope]
        lines += [f'## {scope}', '', f'- BASE: {ba["R"]}R / ROI **{ba["roi_pct"]:.2f}%** / monthly floor **{bmin:.2f}%**.', f'- selection tier: **{tier}**']
        if ch is None:
            lines += ['- No rescue candidate passed safety tiers.',''];continue
        lines += [f'- selected rescue: **{ch.family} param={int(ch.param)} floor={ch.floor:.1f}**',
                  f'- combined: **{int(ch.R)}R** ({int(ch.added_R):+d}) / ROI **{ch.roi_pct:.2f}%** / monthly floor **{ch.min_month_roi_pct:.2f}%**.',
                  f'- rescue-only ROI: **{ch.rescue_roi_pct:.2f}%**.','',
                  '|month|combined R|added R|combined ROI|base ROI|added ROI|','|---|---:|---:|---:|---:|---:|']
        mm=M[(M.scope==scope)&(M.family==ch.family)&(M.param==ch.param)&(M.floor==ch.floor)].sort_values('month')
        for _,r in mm.iterrows():
            ar='-' if pd.isna(r.added_roi_pct) else f'{r.added_roi_pct:.2f}%'
            lines.append(f'|{r.month}|{int(r.R)}|{int(r.added_R)}|{r.roi_pct:.2f}%|{r.base_roi_pct:.2f}%|{ar}|')
        lines += ['','### LOMO search-procedure check','', '|holdout|train-chosen rule|added R|combined R|combined ROI|','|---|---|---:|---:|---:|']
        for _,r in L[L.scope==scope].iterrows():
            if r.status!='OK':lines.append(f'|{r.holdout_month}|NO_CANDIDATE|-|-|-|')
            else:lines.append(f'|{r.holdout_month}|{r.family} {int(r.param)} / {r.floor:.1f}|{int(r.hold_added_R)}|{int(r.hold_R)}|{r.hold_roi_pct:.2f}%|')
        lines += ['']
    lines += ['## Production-readiness rule','',
              '- `S` candidate is the only immediately deployable scope after ticket-selector code + immutable pre-deadline odds audit are wired.',
              '- `S+A` remains development-only until the frozen A_SCORE LIVE-scale mapping is completed.',
              '- A new policy version must be frozen; do not rewrite HEAD4_V291_COMP7 history.',
              '- Formal performance starts only after the new selector and pre-deadline snapshot persistence are operational.']
    SUM.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print('\n'.join(lines))

if __name__=='__main__':main()
