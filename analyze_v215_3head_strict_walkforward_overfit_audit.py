#!/usr/bin/env python3
"""v215: strict walk-forward overfit audit for v165 -> v166 under new 10k Dutch ROI.

Purpose
- Diagnose whether strong Jul/Aug performance is likely overfit/regime-specific.
- v165 threshold is FIXED at p3head>=0.30; no retuning.
- Each month reconstructs v165 and v166 using only earlier dates.
- For opponent selection, precompute lambda x point-count candidates for each month.
- Starting Jan-2026, choose (lambda, points) using ONLY already-settled prior audit months,
  then apply once to the next month. Dec-2025 is diagnostic seed only and excluded from adaptive OOS aggregate.
- Selection objective: highest cumulative prior new-ROI, tie-break by more settled races coverage consistency,
  then fewer points. No current/future month outcome/odds can affect the choice.

Also report stage decomposition per month:
1) v165 candidate count and actual 3-head rate
2) v166 coverage among actual 3-head wins
3) realized TopN hit rate and new 10k Dutch ROI
"""
from pathlib import Path
from datetime import date
import numpy as np
import pandas as pd
import analyze_v165_3head_monthly_walkforward as v165
import analyze_v166_3head_pair_direct as v166
import analyze_v205_3head_operational_replay as v205
import analyze_v211_3head_variable_points_newroi as v211

ROOT=Path(__file__).resolve().parent
SRC=ROOT/'analysis_v108_1head_feasibility.csv'
OUT=ROOT/'analysis_v215_3head_strict_walkforward_overfit_audit.csv'
SUM=ROOT/'summary_v215_3head_strict_walkforward_overfit_audit.md'
MONTHS=['2025-12']+[f'2026-{m:02d}' for m in range(1,9)]
LAMBDAS=(0.0,0.25,0.50,0.75,1.00)
POINTS=(4,6,8,10,12,15)
CUT=.30; BANK=10000


def settle(r,od,ordered,n):
    return v211.settle_topn(type('R',(),{'actual_combo':str(r.get('actual_combo','')).strip()})(),od,ordered,n)

def mtr(g):
    if g.empty:return dict(R=0,head=0,hit=0,cov=0,roi=0,ret=0,cost=0,profit=0,comp=0)
    cost=float(g.cost.sum());ret=float(g.return_yen.sum())
    heads=g[g.head3==1]
    cov=100*float(heads.pair_hit.mean()) if len(heads) else 0
    return dict(R=len(g),head=100*float(g.head3.mean()),hit=100*float(g.hit.mean()),cov=cov,
                roi=100*ret/cost if cost else 0,ret=ret,cost=cost,profit=ret-cost,
                comp=float(g.composite_odds.mean()))

def main():
    src_path,df=v165.load();dc=v165.pc(df,['date','race_date','ymd']);vc=v165.pc(df,['venue','jcd','stadium','place'])
    if Path(src_path).name!='analysis_v108_1head_feasibility.csv':raise SystemExit(f'v165 source mismatch {src_path}')
    y,td=v165.target(df);fs=v165.feats(df)
    d=df.copy();d['_date']=pd.to_datetime(d[dc].astype(str),errors='coerce');d['_y']=y
    d=d[d._date.notna()&d._y.notna()].copy()
    src=v166.read(str(SRC))
    odds=v205.load_odds();oi=odds.set_index('race_code',drop=False)
    rows=[];diag={}
    # Build every month with strict prior-only models for every lambda/point candidate.
    for mon in MONTHS:
        first=pd.Timestamp(mon+'-01');end=first+pd.offsets.MonthBegin(1)
        tr=d[d._date<first].copy();te=d[(d._date>=first)&(d._date<end)].copy()
        nums=[]
        for c in fs:
            q=pd.to_numeric(d[c],errors='coerce')
            if q.notna().mean()>=.8:
                tr[c]=pd.to_numeric(tr[c],errors='coerce');te[c]=pd.to_numeric(te[c],errors='coerce');nums.append(c)
        cats=[vc] if vc and vc not in nums else []
        hm=v165.model(nums,cats);hm.fit(tr[nums+cats],tr._y.astype(int));pp=hm.predict_proba(te[nums+cats])[:,1]
        pm,pair_n=v166.fit([r for r in src if date.fromisoformat(r['date'])<date.fromisoformat(mon+'-01')])
        cands=[]
        for ix,p in zip(te.index,pp):
            if float(p)<CUT:continue
            rr=dict(src[int(ix)])
            if v166.ii(rr.get('course3'),3)!=3:continue
            cands.append((str(rr.get('race_code')),float(p),rr))
        diag[mon]={'candidates':len(cands),'pair_train':pair_n}
        for code,p,rr in cands:
            if code not in oi.index:continue
            od=oi.loc[code];od=od.iloc[-1] if isinstance(od,pd.DataFrame) else od
            actual=str(rr.get('actual_combo','')).strip();head3=int(actual.startswith('3-'))
            for lam in LAMBDAS:
                ordered=v166.order(rr,pm,lam)
                rank=(ordered.index(actual)+1) if actual in ordered else 0
                for n in POINTS:
                    s=settle(rr,od,ordered,n)
                    if s is None:continue
                    rows.append({'month':mon,'date':rr.get('date'),'race_code':code,'p3head':p,
                                 'lambda':lam,'points':n,'head3':head3,'pair_rank':rank,
                                 'pair_hit':int(head3 and 0<rank<=n),'actual_combo':actual,
                                 'pair_train_3wins':pair_n,'odds_source':str(od.get('odds_source','unknown')),
                                 **s})
    z=pd.DataFrame(rows)
    if z.empty:raise SystemExit('no rows')

    # Strict adaptive choice: target month chooses only from prior audit months.
    picks=[]
    for i,mon in enumerate(MONTHS):
        if i==0:
            lam,n=1.0,10;reason='seed diagnostic only'
        else:
            prior=MONTHS[:i]
            cand=[]
            for lam0 in LAMBDAS:
                for n0 in POINTS:
                    g=z[(z.month.isin(prior))&(z['lambda']==lam0)&(z.points==n0)]
                    mm=mtr(g)
                    # Need meaningful history; Dec alone is allowed for Jan, later naturally grows.
                    if mm['R']<30:continue
                    # Secondary stability: worst prior monthly ROI.
                    worst=min((mtr(g[g.month==m])['roi'] for m in prior if len(g[g.month==m])),default=-1e9)
                    cand.append((mm['roi'],worst,-n0,lam0,n0,mm['R']))
            if not cand:lam,n=1.0,10;reason='fallback'
            else:
                cand.sort(reverse=True);_,worst,_,lam,n,pr=cand[0];reason=f'prior-only ROI selection; priorR={pr}; worst={worst:.1f}'
        g=z[(z.month==mon)&(z['lambda']==lam)&(z.points==n)].copy();mm=mtr(g)
        picks.append({'month':mon,'selected_lambda':lam,'selected_points':n,'selection_reason':reason,**mm})
        z.loc[g.index,'wf_selected']=1
    z['wf_selected']=z.get('wf_selected',0).fillna(0).astype(int)
    z.to_csv(OUT,index=False)
    p=pd.DataFrame(picks)

    # Fixed lambda=1 Top10 diagnostic monthly table for stage decomposition.
    base=z[(z['lambda']==1.0)&(z.points==10)]
    L=['# v215 strict walk-forward overfit audit','',
       '- v165: monthly prior-only fit, fixed BUY threshold p3head>=0.30',
       '- v166: monthly prior-only pair fit',
       '- adaptive opponent strategy: each target month selects lambda in {0,.25,.50,.75,1.0} and points in {4,6,8,10,12,15} using only earlier audit months under the new 10k Dutch ROI',
       '- Dec-2025 is seed/diagnostic only; adaptive OOS aggregate starts Jan-2026',
       '- current-month results/odds never enter model or strategy choice before settlement','',
       '## Stage decomposition: fixed lambda=1.00 / Top10','|month|candidates|settled|3-head rate|Top10 coverage given 3-head|trifecta hit|avg comp|ROI|profit|','|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for mon in MONTHS:
        g=base[base.month==mon];mm=mtr(g)
        L.append(f"|{mon}|{diag.get(mon,{}).get('candidates',0)}|{mm['R']}|{mm['head']:.2f}%|{mm['cov']:.2f}%|{mm['hit']:.2f}%|{mm['comp']:.3f}|{mm['roi']:.1f}%|{mm['profit']:+.0f}|")
    L += ['','## Strict walk-forward selected opponent strategy','|target month|lambda|points|settled|3-head rate|coverage|hit|avg comp|ROI|profit|','|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for _,r in p.iterrows():
        L.append(f"|{r.month}|{r.selected_lambda:.2f}|{int(r.selected_points)}|{int(r.R)}|{r.head:.2f}%|{r.cov:.2f}%|{r.hit:.2f}%|{r.comp:.3f}|{r.roi:.1f}%|{r.profit:+.0f}|")
    oos=p[p.month!='2025-12'];cost=float(oos.cost.sum());ret=float(oos.ret.sum())
    L += ['','## Adaptive OOS aggregate Jan-Aug',
          f"- races: **{int(oos.R.sum())}**",
          f"- cost: **{cost:.0f} yen**",
          f"- return: **{ret:.0f} yen**",
          f"- ROI: **{100*ret/cost if cost else 0:.1f}%**",
          f"- profit: **{ret-cost:+.0f} yen**",'']
    # Early vs late fixed Top10 regime split.
    early=base[base.month.isin(['2025-12','2026-01','2026-02','2026-03','2026-04','2026-05','2026-06'])]
    late=base[base.month.isin(['2026-07','2026-08'])]
    me,ml=mtr(early),mtr(late)
    L += ['## Regime comparison for unchanged lambda=1 / Top10',
          f"- Dec-Jun: R={me['R']}, 3-head={me['head']:.2f}%, coverage={me['cov']:.2f}%, hit={me['hit']:.2f}%, ROI={me['roi']:.1f}%",
          f"- Jul-Aug: R={ml['R']}, 3-head={ml['head']:.2f}%, coverage={ml['cov']:.2f}%, hit={ml['hit']:.2f}%, ROI={ml['roi']:.1f}%",'',
          '## Interpretation guardrails',
          '- If 3-head rate itself rises sharply late, v165/regime shift is a major source of the ROI jump.',
          '- If 3-head rate is stable but pair coverage/ROI rises sharply, v166/opponent or odds regime is the larger source.',
          '- If adaptive prior-only lambda/points still fail to reach 100% OOS, Jul/Aug rule-search gains should be treated as likely overfit or regime-specific rather than production proof.',
          '- No production change is made by this audit.']
    SUM.write_text('\n'.join(L)+'\n',encoding='utf-8');print('\n'.join(L))

if __name__=='__main__':main()
