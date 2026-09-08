#!/usr/bin/env python3
"""v219: clean pre-Jul 3-head redesign baseline under exact 10k Dutch ROI.

PURPOSE
- Rebuild the 3-head chain without using 2026-07/08 for tuning/model selection.
- Strict monthly prior-only v165 head model and prior-only v166 direct-pair model.
- Historical odds are settlement-only. No historical closing odds are used to choose races,
  point count, ranking, or thresholds.
- p3 cuts and fixed TopN are REPORTED as baselines, not selected/adopted here.

EVALUATION
- 2025-12 through 2026-06 only.
- Any Jul/Aug evaluation row is a hard error.
- Each evaluated month trains only on rows strictly before the first day of that month.
- Exact 10,000 yen Dutch allocation in 100-yen Hamilton units.
"""
from __future__ import annotations
from pathlib import Path
from datetime import date
import math
import numpy as np
import pandas as pd
from sklearn.metrics import brier_score_loss, roc_auc_score

import analyze_v165_3head_monthly_walkforward as v165
import analyze_v166_3head_pair_direct as v166
import analyze_v205_3head_operational_replay as v205

ROOT=Path(__file__).resolve().parent
SRC=ROOT/'analysis_v108_1head_feasibility.csv'
OUT=ROOT/'analysis_v219_3head_redesign_baseline.csv'
CAL=ROOT/'analysis_v219_3head_calibration.csv'
SUM=ROOT/'summary_v219_3head_redesign_baseline.md'
EVAL_MONTHS=['2025-12','2026-01','2026-02','2026-03','2026-04','2026-05','2026-06']
CONTAM_START=pd.Timestamp('2026-07-01')
CUTS=[.20,.25,.30,.35,.40]
POINTS=list(range(4,16))
BANK=10000


def safe_auc(y,p):
    try:return float(roc_auc_score(y,p)) if len(set(map(int,y)))>1 else float('nan')
    except:return float('nan')

def parse_actual(x):
    a=v166.combo(x)
    return '-'.join(map(str,a)) if len(a)==3 else ''

def max_drawdown(profits):
    c=np.cumsum(np.asarray(profits,float)); peak=np.maximum.accumulate(np.r_[0.0,c])
    dd=peak[1:]-c
    return float(dd.max()) if len(dd) else 0.0

def robustness(g):
    if g.empty:return {'roi':0.,'profit':0.,'maxdd':0.,'roi_rm1':0.,'roi_rm3':0.,'roi_rm5':0.}
    cost=float(g.cost.sum()); ret=float(g.return_yen.sum())
    z=g.sort_values(['date','race_code']).copy()
    d={'roi':100*ret/cost if cost else 0.,'profit':ret-cost,'maxdd':max_drawdown(z.profit)}
    byprofit=g.sort_values('profit',ascending=False)
    for k in (1,3,5):
        q=byprofit.iloc[k:] if len(byprofit)>k else byprofit.iloc[0:0]
        c=float(q.cost.sum());r=float(q.return_yen.sum())
        d[f'roi_rm{k}']=100*r/c if c else 0.
    return d

def head_fit_predict(df,fs,vc,first,nextm):
    tr=df[df._date<first].copy();te=df[(df._date>=first)&(df._date<nextm)].copy()
    if len(tr)<200 or len(te)<1 or tr._y.nunique()<2:return pd.DataFrame(),None,0
    nums=[]
    for c in fs:
        q=pd.to_numeric(df[c],errors='coerce')
        if q.notna().mean()>=.8:
            tr[c]=pd.to_numeric(tr[c],errors='coerce');te[c]=pd.to_numeric(te[c],errors='coerce');nums.append(c)
    cats=[vc] if vc and vc not in nums else []
    m=v165.model(nums,cats);m.fit(tr[nums+cats],tr._y.astype(int))
    te['_p3']=m.predict_proba(te[nums+cats])[:,1]
    return te,m,len(tr)

def pair_probs(r,m):
    score={}
    for s in v166.OPP:
        for t in v166.OPP:
            if s==t:continue
            q=float(m.predict_proba(np.asarray([v166.pvec(r,s,t)],float))[0,1])
            score[f'3-{s}-{t}']=max(q,1e-12)
    ordered=sorted(score,key=lambda k:(-score[k],k))
    a=np.asarray([score[k] for k in ordered],float);a=a/a.sum()
    return ordered,a

def settle(ordered,odrow,actual,n):
    ts=ordered[:n];vals=[]
    for t in ts:
        try:v=float(odrow[t])
        except:return None
        if not np.isfinite(v) or v<=0:return None
        vals.append(v)
    stakes=np.asarray(v205.round_dutch(vals,BANK),int)
    if len(stakes)!=n or int(stakes.sum())!=BANK:raise RuntimeError(f'Dutch invariant N={n}')
    funded=int((stakes>0).sum());zero=int((stakes<=0).sum())
    astake=0;ret=0.0
    if actual in ts:
        i=ts.index(actual);astake=int(stakes[i]);ret=float(astake*vals[i]) if astake>0 else 0.0
    funded_vals=[v for v,s in zip(vals,stakes) if s>0]
    comp=float(1/sum(1/v for v in funded_vals)) if funded_vals else float('nan')
    return {'points':n,'funded_points':funded,'zero_stake':zero,'hit':int(astake>0),
            'actual_stake':astake,'composite_odds':comp,'cost':BANK,'return_yen':ret,'profit':ret-BANK}

def main():
    if not SRC.exists():raise SystemExit(f'missing {SRC}')
    raw=pd.read_csv(SRC,dtype={'race_code':str})
    dc=v165.pc(raw,['date','race_date','ymd']);vc=v165.pc(raw,['venue','jcd','stadium','place'])
    if not dc:raise SystemExit('no date column')
    y,td=v165.target(raw);fs=v165.feats(raw)
    d=raw.copy();d['_date']=pd.to_datetime(d[dc].astype(str),errors='coerce');d['_y']=y
    d=d[d._date.notna()&d._y.notna()].copy()
    if not len(fs):raise SystemExit('no v165 features')
    odds=v205.load_odds()
    if odds.empty:raise SystemExit('no historical odds')
    oi=odds.set_index('race_code',drop=False)
    rows=[];calrows=[]
    raw_records=raw.to_dict('records')
    for mon in EVAL_MONTHS:
        first=pd.Timestamp(mon+'-01');nextm=first+pd.offsets.MonthBegin(1)
        if first>=CONTAM_START:raise RuntimeError(f'CONTAMINATION GUARD: {mon}')
        te,hm,hn=head_fit_predict(d,fs,vc,first,nextm)
        if te.empty:continue
        hist=[r for r in raw_records if pd.to_datetime(r.get(dc),errors='coerce')<first]
        pm,pair_n=v166.fit(hist)
        for ix,r in te.iterrows():
            if r['_date']>=CONTAM_START:raise RuntimeError(f'CONTAMINATION ROW {r[dc]}')
            rr=raw.loc[ix].to_dict();code=str(rr.get('race_code','')).zfill(12)
            if not code or code not in oi.index:continue
            if v166.ii(rr.get('valid_result'))!=1:continue
            if v166.ii(rr.get('course3'),3)!=3:continue
            actual=parse_actual(rr.get('actual_combo'))
            if not actual:continue
            od=oi.loc[code];od=od.iloc[-1] if isinstance(od,pd.DataFrame) else od
            ordered,pp=pair_probs(rr,pm);rank=ordered.index(actual)+1 if actual in ordered else 0
            p3=float(r['_p3']);y3=int(r['_y'])
            base={'date':r['_date'].strftime('%Y-%m-%d'),'month':mon,'race_code':code,
                  'venue':str(rr.get('venue','')).zfill(2),'p3head':p3,'y3head':y3,
                  'actual_combo':actual,'v166_rank20':rank,'head_train_rows':hn,
                  'pair_train_3wins':pair_n,'odds_source':str(od.get('odds_source','unknown'))}
            for n in POINTS:
                s=settle(ordered,od,actual,n)
                if s is None:continue
                mass=float(pp[:n].sum())
                rows.append({**base,'v166_mass':mass,**s})
            if y3:
                for n in POINTS:
                    calrows.append({'date':base['date'],'month':mon,'race_code':code,'points':n,
                                    'pred_mass':float(pp[:n].sum()),'covered':int(0<rank<=n)})
    z=pd.DataFrame(rows)
    if z.empty:raise SystemExit('no evaluable pre-Jul rows')
    if (pd.to_datetime(z.date)>=CONTAM_START).any():raise RuntimeError('CONTAMINATION GUARD FAILED')
    z.to_csv(OUT,index=False);pd.DataFrame(calrows).to_csv(CAL,index=False)

    # Head metrics use one row per race to avoid TopN duplication.
    one=z.sort_values('points').drop_duplicates('race_code')
    L=['# v219 3-head clean pre-Jul redesign baseline','',
       '- evaluation: **2025-12 through 2026-06 only**; 2026-07/08 are hard-excluded from tuning and evaluation',
       '- v165: strict monthly prior-only refit using the current explicit feature definition',
       '- v166: direct ordered-pair model refit from prior dates only; **lambda=1.00 direct model only** (no Jul/Aug selection)',
       '- historical odds are settlement-only; no closing odds choose a race, cutoff, ranking, or point count',
       '- stake: exactly **10,000 yen/race**, 100-yen Hamilton Dutch',
       '- p3 cuts and fixed TopN below are diagnostics/baselines, **not adopted rules**','',
       '## Head-model monthly audit','|month|R|actual 3-head|AUC|Brier|','|---|---:|---:|---:|---:|']
    for mon,g in one.groupby('month'):
        L.append(f"|{mon}|{len(g)}|{100*g.y3head.mean():.2f}%|{safe_auc(g.y3head,g.p3head):.4f}|{brier_score_loss(g.y3head,g.p3head):.5f}|")
    L += ['','## p3 cutoff diagnostics with fixed Top10','|cut|R|3-head rate|Top10 conditional coverage|trifecta hit|ROI|profit|max DD|ROI rm1|rm3|rm5|','|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for cut in CUTS:
        g=z[(z.points==10)&(z.p3head>=cut)].copy();heads=g[g.y3head==1]
        cov=100*((heads.v166_rank20>0)&(heads.v166_rank20<=10)).mean() if len(heads) else 0
        m=robustness(g)
        L.append(f"|{cut:.2f}|{len(g)}|{100*g.y3head.mean():.2f}%|{cov:.2f}%|{100*g.hit.mean():.2f}%|{m['roi']:.1f}%|{m['profit']:+.0f}|{m['maxdd']:.0f}|{m['roi_rm1']:.1f}%|{m['roi_rm3']:.1f}%|{m['roi_rm5']:.1f}%|")
    L += ['','## Fixed TopN diagnostics at legacy p3>=0.30','|N|R|funded avg|zero-stake races|conditional coverage|hit|avg composite|ROI|profit|max DD|rm1|rm3|rm5|','|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for n in POINTS:
        g=z[(z.points==n)&(z.p3head>=.30)].copy();heads=g[g.y3head==1]
        cov=100*((heads.v166_rank20>0)&(heads.v166_rank20<=n)).mean() if len(heads) else 0;m=robustness(g)
        L.append(f"|{n}|{len(g)}|{g.funded_points.mean():.2f}|{int((g.zero_stake>0).sum())}|{cov:.2f}%|{100*g.hit.mean():.2f}%|{g.composite_odds.mean():.3f}|{m['roi']:.1f}%|{m['profit']:+.0f}|{m['maxdd']:.0f}|{m['roi_rm1']:.1f}%|{m['roi_rm3']:.1f}%|{m['roi_rm5']:.1f}%|")
    L += ['','## Legacy baseline p3>=0.30 / Top10 by month','|month|R|3-head|coverage|hit|ROI|profit|','|---|---:|---:|---:|---:|---:|---:|']
    g0=z[(z.points==10)&(z.p3head>=.30)]
    for mon,g in g0.groupby('month'):
        h=g[g.y3head==1];cov=100*((h.v166_rank20>0)&(h.v166_rank20<=10)).mean() if len(h) else 0;m=robustness(g)
        L.append(f"|{mon}|{len(g)}|{100*g.y3head.mean():.2f}%|{cov:.2f}%|{100*g.hit.mean():.2f}%|{m['roi']:.1f}%|{m['profit']:+.0f}|")
    c=pd.DataFrame(calrows)
    L += ['','## v166 normalized-mass calibration audit (only races actually won by boat 3)','|N|mean normalized mass|realized coverage|gap|R|','|---:|---:|---:|---:|---:|']
    if not c.empty:
        for n,g in c.groupby('points'):
            pm=100*g.pred_mass.mean();ac=100*g.covered.mean();L.append(f'|{n}|{pm:.2f}%|{ac:.2f}%|{ac-pm:+.2f}pt|{len(g)}|')
    L += ['','## Interpretation rules','- Do not select a new p3 cutoff or TopN from this table alone; this first pass establishes failure modes and robustness.',
          '- A high aggregate ROI that collapses after removing the top 1/3/5 profit races is not stable evidence.',
          '- v166 normalized mass is not a probability until its calibration table supports that interpretation.',
          '- Historical closing odds were deliberately not used for odds-aware point selection; true odds-aware validation starts with immutable prospective LIVE snapshots.']
    SUM.write_text('\n'.join(L)+'\n',encoding='utf-8');print('\n'.join(L))

if __name__=='__main__':main()
