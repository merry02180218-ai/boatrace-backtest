#!/usr/bin/env python3
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parent
SRC=ROOT/'analysis_v250_4head_rebuild_baseline.csv'
OUT=ROOT/'analysis_v262_4head_headrate40_r200_search.csv'
SUMMARY=ROOT/'summary_v262_4head_headrate40_r200_search.md'

# Research/model-selection audit. Jul/Aug NON-PRISTINE.
PRE_CUTS=np.round(np.arange(.20,.451,.005),3)
POST_CUTS=np.round(np.arange(.20,.451,.005),3)


def load():
    d=pd.read_csv(SRC,dtype={'race_code':str,'venue':str})
    d['race_code']=d['race_code'].str.zfill(12)
    w=d.pivot_table(index=['date','month','race_code','venue'],columns='variant',values=['p4head','y4head'],aggfunc='last')
    w.columns=['_'.join(c) for c in w.columns]
    w=w.reset_index()
    w['head4']=w['y4head_PRE'].astype(int)
    return w


def stats(q):
    r=len(q); h=int(q.head4.sum())
    return r,h,(h/r if r else np.nan)


def main():
    d=load(); rows=[]
    for pc in PRE_CUTS:
        a=d[d.p4head_PRE>=pc]
        if len(a)<150: continue
        for qc in POST_CUTS:
            z=a[a.p4head_POST>=qc]
            R,H,HR=stats(z)
            if R<150: continue
            train=z[z.month<='2026-06']; Rt,Ht,HRt=stats(train)
            ja=z[z.month>='2026-07']; Rj,Hj,HRj=stats(ja)
            mons=[]
            for m,g in z.groupby('month'):
                mons.append(g.head4.mean())
            rows.append({'pre_cut':pc,'post_cut':qc,'R':R,'heads':H,'head_rate':HR,
                         'febjun_R':Rt,'febjun_heads':Ht,'febjun_head_rate':HRt,
                         'julaug_R':Rj,'julaug_heads':Hj,'julaug_head_rate':HRj,
                         'min_month_head_rate':min(mons) if mons else np.nan,
                         'median_month_head_rate':float(np.median(mons)) if mons else np.nan})
    o=pd.DataFrame(rows)
    # Prefer: >=200R and >=40% overall, then highest Feb-Jun rate and volume.
    o['pass_200_40']=(o.R>=200)&(o.head_rate>=.40)
    o['pass_febjun_40']=(o.febjun_R>=120)&(o.febjun_head_rate>=.40)
    o=o.sort_values(['pass_200_40','pass_febjun_40','febjun_head_rate','head_rate','R'],ascending=[False,False,False,False,False])
    o.to_csv(OUT,index=False)

    L=['# v262 4-head: head-rate >=40% while keeping >=200 races','',
       '- Source: v250 monthly walk-forward PRE/POST p4head predictions.','- Search only PRE/POST probability thresholds; no result-aware feature gate is added.','- 2026-07/08 are NON-PRISTINE and shown separately.','- This is retrospective/model-selection evidence, not pristine validation.','']
    p=o[o.pass_200_40]
    if len(p):
        L += ['## Feasible >=200R & >=40% overall','|PRE|POST|R|heads|head rate|Feb-Jun R|Feb-Jun head rate|Jul-Aug R|Jul-Aug head rate|min monthly|','|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
        for _,r in p.head(20).iterrows():
            L.append(f"|{r.pre_cut:.3f}|{r.post_cut:.3f}|{int(r.R)}|{int(r.heads)}|{100*r.head_rate:.2f}%|{int(r.febjun_R)}|{100*r.febjun_head_rate:.2f}%|{int(r.julaug_R)}|{100*r.julaug_head_rate:.2f}%|{100*r.min_month_head_rate:.2f}%|")
    else:
        L += ['## Feasible >=200R & >=40% overall','None with PRE/POST thresholds alone.']
    L += ['','## Best volume among >=40% overall','|PRE|POST|R|head rate|Feb-Jun R|Feb-Jun head rate|','|---:|---:|---:|---:|---:|---:|']
    for _,r in o[o.head_rate>=.40].sort_values('R',ascending=False).head(15).iterrows():
        L.append(f"|{r.pre_cut:.3f}|{r.post_cut:.3f}|{int(r.R)}|{100*r.head_rate:.2f}%|{int(r.febjun_R)}|{100*r.febjun_head_rate:.2f}%|")
    L += ['','## Best Feb-Jun robust cells (>=150 overall R)','|PRE|POST|R|overall head rate|Feb-Jun R|Feb-Jun head rate|','|---:|---:|---:|---:|---:|---:|']
    for _,r in o.sort_values(['febjun_head_rate','R'],ascending=[False,False]).head(20).iterrows():
        L.append(f"|{r.pre_cut:.3f}|{r.post_cut:.3f}|{int(r.R)}|{100*r.head_rate:.2f}%|{int(r.febjun_R)}|{100*r.febjun_head_rate:.2f}%|")
    SUMMARY.write_text('\n'.join(L)+'\n',encoding='utf-8')
    print('\n'.join(L))

if __name__=='__main__': main()
