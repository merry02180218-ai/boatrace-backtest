#!/usr/bin/env python3
import pandas as pd
from pathlib import Path
ROOT=Path(__file__).resolve().parent
SRC=ROOT/'analysis_v205_3head_operational_replay.csv'
OUT=ROOT/'analysis_v209_pre_dropped_aug_profit.csv'
SUM=ROOT/'summary_v209_pre_dropped_aug_profit.md'

def stat(g):
    c=float(g.cost.sum()) if len(g) else 0
    r=float(g.return_yen.sum()) if len(g) else 0
    return len(g), int(g.hit.sum()) if len(g) else 0, (100*g.hit.mean() if len(g) else 0), c, r, (100*r/c if c else 0), r-c

def main():
    d=pd.read_csv(SRC,dtype={'race_code':str})
    a=d[d.month=='2026-08'].copy()
    passed=a[a.pre_watch==True].copy()
    dropped=a[a.pre_watch==False].copy()
    dropped.to_csv(OUT,index=False,encoding='utf-8-sig')
    A=stat(a); P=stat(passed); D=stat(dropped)
    L=['# v209 — August PRE-dropped profit audit','',
       '|segment|R|hit|hit rate|cost|return|ROI|profit|','|---|---:|---:|---:|---:|---:|---:|---:|',
       f'|All v165->v166|{A[0]}|{A[1]}|{A[2]:.1f}%|¥{A[3]:,.0f}|¥{A[4]:,.0f}|{A[5]:.1f}%|¥{A[6]:,.0f}|',
       f'|PRE pass|{P[0]}|{P[1]}|{P[2]:.1f}%|¥{P[3]:,.0f}|¥{P[4]:,.0f}|{P[5]:.1f}%|¥{P[6]:,.0f}|',
       f'|PRE dropped|{D[0]}|{D[1]}|{D[2]:.1f}%|¥{D[3]:,.0f}|¥{D[4]:,.0f}|{D[5]:.1f}%|¥{D[6]:,.0f}|','',
       '## Dropped races','|date|race_code|pre p|p3head|turn|ST|actual|hit|comp|return|profit|','|---|---|---:|---:|---:|---:|---|---:|---:|---:|---:|']
    for _,r in dropped.sort_values(['date','race_code']).iterrows():
        L.append(f"|{r.date}|{r.race_code}|{r.pre_prob_eval:.6f}|{r.p3head:.4f}|{r.turn_margin23:.3f}|{r.st_margin23:.3f}|{r.actual_combo}|{int(r.hit)}|{r.composite_odds:.3f}|¥{r.return_yen:,.0f}|¥{r.profit:,.0f}|")
    SUM.write_text('\n'.join(L)+'\n',encoding='utf-8')
    print('\n'.join(L))
if __name__=='__main__': main()
