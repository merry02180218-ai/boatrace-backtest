#!/usr/bin/env python3
"""v195: six-month backtest of the exact current 3-head production operation.

Operation frozen exactly as production:
  exhibition/direct data -> monthly WF v165 p3head >= .30
  -> v166 direct ordered-pair lambda=1.00 -> Top10
  -> equal 100 yen each; payout settlement only.

Evaluation: 2026-03..2026-08. Each month refits v165 and v166 only on dates before
that month. No result/payout/odds is used in prediction/ranking.
"""
from pathlib import Path
from datetime import date
import csv
import numpy as np
import pandas as pd
import analyze_v165_3head_monthly_walkforward as v165
import analyze_v166_3head_pair_direct as v166
ROOT=Path(__file__).resolve().parent
MONTHS=[f'2026-{m:02d}' for m in range(3,9)]
CUT=.30; TOPN=10; LAM=1.0

def ff(x,d=0.):
    try:return float(x)
    except:return d

def ii(x,d=0):
    try:return int(float(x))
    except:return d

def combo(x):
    try:return [int(z) for z in str(x).replace(' ','').split('-')]
    except:return []

def main():
    src_path,df=v165.load(); dc=v165.pc(df,['date','race_date','ymd']); vc=v165.pc(df,['venue','jcd','stadium','place'])
    y,td=v165.target(df); fs=v165.feats(df)
    d=df.copy(); d['_date']=pd.to_datetime(d[dc].astype(str),errors='coerce'); d['_y']=y
    d=d[d._date.notna()&d._y.notna()].copy()
    # v166 source rows are canonical frozen v108 rows. Index identity must match v165 source.
    src=v166.read(str(ROOT/'analysis_v108_1head_feasibility.csv'))
    if Path(src_path).name!='analysis_v108_1head_feasibility.csv': raise SystemExit(f'v165 source mismatch: {src_path}')
    rows=[]
    for mon in MONTHS:
        m=pd.Timestamp(mon+'-01'); e=m+pd.offsets.MonthBegin(1)
        tr=d[d._date<m].copy(); te=d[(d._date>=m)&(d._date<e)].copy()
        if len(tr)<200 or len(te)<20 or tr._y.nunique()<2: continue
        nums=[]
        for c in fs:
            q=pd.to_numeric(d[c],errors='coerce')
            if q.notna().mean()>=.8:
                tr[c]=pd.to_numeric(tr[c],errors='coerce');te[c]=pd.to_numeric(te[c],errors='coerce');nums.append(c)
        cats=[vc] if vc and vc not in nums else []
        hm=v165.model(nums,cats); hm.fit(tr[nums+cats],tr._y.astype(int)); probs=hm.predict_proba(te[nums+cats])[:,1]
        pair_train=[r for r in src if date.fromisoformat(r['date'])<date.fromisoformat(mon+'-01')]
        pm,pair_n=v166.fit(pair_train)
        for ix,p in zip(te.index,probs):
            if p<CUT: continue
            r=dict(src[int(ix)])
            # production entry gate: boat3 must actually exhibit from course3
            # canonical source direct rows are retained only when usable; explicit course field if present is enforced.
            c3=ii(r.get('course3'),3)
            if c3!=3: continue
            rank=v166.order(r,pm,LAM); top=rank[:TOPN]
            act=(r.get('actual_combo') or '').strip(); hit=int(act in top)
            validpay=ii(r.get('valid_payout'))==1
            payout=ff(r.get('payout100')) if hit and validpay else 0.
            rows.append({'month':mon,'date':r.get('date'),'race_code':r.get('race_code'),'p3head':float(p),'actual_combo':act,'y3head':int(combo(act)[:1]==[3]),'hit':hit,'valid_payout':int(validpay),'return_yen':payout,'cost_yen':TOPN*100 if validpay else 0,'top10':';'.join(top),'pair_train_3wins':pair_n})
    o=pd.DataFrame(rows); o.to_csv(ROOT/'analysis_v195_3head_production_6month_backtest.csv',index=False)
    L=['# v195 3号艇 production exact-operation 6-month backtest','',f'- months: {MONTHS[0]} .. {MONTHS[-1]}',f'- operation: v165 p3head >= {CUT:.2f} -> v166 lambda={LAM:.2f} -> Top{TOPN}', '- each target month trains only on earlier dates', '- equal stake: 100 yen x 10 tickets; payout settlement only after frozen ranking', '- no result/payout/odds in prediction or ticket ranking','','|month|candidates|3-head|hit|3-head Top10 coverage|cost|return|ROI|','|---|---:|---:|---:|---:|---:|---:|---:|']
    for mon in MONTHS:
        g=o[o.month==mon]; h=g[g.y3head==1]; settled=g[g.valid_payout==1]
        cov=100*h.hit.mean() if len(h) else 0; roi=100*settled.return_yen.sum()/settled.cost_yen.sum() if settled.cost_yen.sum() else 0
        L.append(f'|{mon}|{len(g)}|{100*g.y3head.mean():.2f}%|{100*g.hit.mean():.2f}%|{cov:.2f}%|{settled.cost_yen.sum():.0f}|{settled.return_yen.sum():.0f}|{roi:.1f}%|')
    h=o[o.y3head==1];settled=o[o.valid_payout==1];roi=100*settled.return_yen.sum()/settled.cost_yen.sum() if settled.cost_yen.sum() else 0
    L += ['','## Aggregate',f'- candidates: {len(o)}R',f'- 3-head rate: {100*o.y3head.mean():.2f}%',f'- trifecta hit rate: {100*o.hit.mean():.2f}%',f'- conditional Top10 coverage: {100*h.hit.mean():.2f}%',f'- cost: {settled.cost_yen.sum():.0f} yen',f'- return: {settled.return_yen.sum():.0f} yen',f'- ROI: {roi:.1f}%']
    (ROOT/'summary_v195_3head_production_6month_backtest.md').write_text('\n'.join(L)+'\n',encoding='utf-8');print('\n'.join(L))
if __name__=='__main__':main()
