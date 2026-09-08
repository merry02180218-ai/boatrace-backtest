#!/usr/bin/env python3
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parent
SRC=ROOT/'analysis_v196_3head_6month_failure_diagnostics.csv'
OUT=ROOT/'analysis_v197_3head_turn_forward_validation.csv'
SUM=ROOT/'summary_v197_3head_turn_forward_validation.md'
CANDS=[-1.2,-1.0,-.9,-.8,-.7,-.6,-.5,-.4,-.3,-.2,0.0,.2]

def metric(g):
    if len(g)==0:return dict(R=0,head=0,hit=0,cov=0,cost=0,ret=0,roi=0)
    h=g[g.y3head==1];s=g[g.valid_payout==1];cost=s.cost_yen.sum();ret=s.return_yen.sum()
    return dict(R=len(g),head=100*g.y3head.mean(),hit=100*g.hit.mean(),cov=100*h.hit.mean() if len(h) else 0,cost=cost,ret=ret,roi=100*ret/cost if cost else 0)
def choose(train):
    rows=[]
    for th in CANDS:
        g=train[pd.to_numeric(train.turn_margin23,errors='coerce')>=th];m=metric(g);keep=len(g)/len(train) if len(train) else 0
        if len(g)>=40 and keep>=.55:rows.append((m['roi'],m['hit'],m['head'],th,m))
    if not rows:return -999,metric(train)
    b=max(rows,key=lambda x:(x[0],x[1],x[2],x[3]));return b[3],b[4]
def fmt(label,m):return f"|{label}|{m['R']}|{m['head']:.2f}%|{m['hit']:.2f}%|{m['cov']:.2f}%|{m['cost']:.0f}|{m['ret']:.0f}|{m['roi']:.1f}%|"
def main():
    z=pd.read_csv(SRC);z['turn_margin23']=pd.to_numeric(z['turn_margin23'],errors='coerce');z=z[z.p3head>=.30].copy()
    tune=z[z.month.isin(['2026-03','2026-04','2026-05'])];test=z[z.month.isin(['2026-06','2026-07','2026-08'])]
    th,_=choose(tune);bt=metric(tune);ft=metric(tune[tune.turn_margin23>=th]);btest=metric(test);ftest=metric(test[test.turn_margin23>=th])
    L=['# v197 3号艇 turn-margin forward validation','', '- base: v165 p3head>=0.30 -> v166 lambda=1.00 -> Top10', '- candidate: turn_margin23 threshold', '- NOTE: v196 already exposed Mar-Aug behavior, so this is pseudo-forward, not pristine prospective evidence.','','## Fixed: tune Mar-May, test Jun-Aug',f'- chosen cut: **{th:.3f}**','','|segment|R|3-head|hit|Top10 cov|cost|return|ROI|','|---|---:|---:|---:|---:|---:|---:|---:|',fmt('Mar-May BASE',bt),fmt('Mar-May FILTER',ft),fmt('Jun-Aug BASE',btest),fmt('Jun-Aug FILTER',ftest),'','## Rolling walk-forward','|test month|cut|BASE R|BASE ROI|FILTER R|FILTER head|FILTER hit|FILTER ROI|','|---|---:|---:|---:|---:|---:|---:|---:|']
    rows=[{'mode':'fixed','test':'2026-06..08','cut':th,**{f'base_{k}':v for k,v in btest.items()},**{f'filter_{k}':v for k,v in ftest.items()}}];roll=[]
    months=['2026-04','2026-05','2026-06','2026-07','2026-08']
    for mon in months:
        tr=z[z.month<mon];te=z[z.month==mon];cut,_=choose(tr);bm=metric(te);fm=metric(te[te.turn_margin23>=cut])
        L.append(f"|{mon}|{cut:.3f}|{bm['R']}|{bm['roi']:.1f}%|{fm['R']}|{fm['head']:.2f}%|{fm['hit']:.2f}%|{fm['roi']:.1f}%|")
        roll.append(te[te.turn_margin23>=cut]);rows.append({'mode':'rolling','test':mon,'cut':cut,**{f'filter_{k}':v for k,v in fm.items()}})
    rr=pd.concat(roll,ignore_index=True);rb=metric(z[z.month.isin(months)]);rf=metric(rr)
    L += ['','## Rolling aggregate Apr-Aug','|segment|R|3-head|hit|Top10 cov|cost|return|ROI|','|---|---:|---:|---:|---:|---:|---:|---:|',fmt('BASE',rb),fmt('FILTER',rf),'','## Decision','- Production is unchanged.', '- If fixed and rolling checks both improve materially, use the gate only as Sep SHADOW and require prospective confirmation before adoption.']
    pd.DataFrame(rows).to_csv(OUT,index=False);SUM.write_text('\n'.join(L)+'\n',encoding='utf-8');print('\n'.join(L))
if __name__=='__main__':main()
