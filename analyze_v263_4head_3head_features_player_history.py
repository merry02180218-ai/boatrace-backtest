#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
import analyze_v96_4corner_monthly_walkforward_tiebreak as c4
import analyze_v221_3head_scenario_pair as v221

ROOT=Path(__file__).resolve().parent
PRED=ROOT/'analysis_v250_4head_rebuild_baseline.csv'
OUT=ROOT/'analysis_v263_4head_3head_features_player_history.csv'
SUM=ROOT/'summary_v263_4head_3head_features_player_history.md'
MONTHS=[f'2026-{m:02d}' for m in range(2,7)]

def ff(x):
    try:
        y=float(x); return y if np.isfinite(y) else np.nan
    except:return np.nan

def model():
    return Pipeline([('imp',SimpleImputer(strategy='median')),('sc',StandardScaler()),('lr',LogisticRegression(C=.25,max_iter=1800))])

def main():
    d=pd.DataFrame(c4.read())
    d['race_code']=d.race_code.astype(str).str.zfill(12)
    d['_date']=pd.to_datetime(d.date,errors='coerce')
    d=d[d._date<pd.Timestamp('2026-07-01')].copy()
    # v221 build freezes player and prior-exhibition traits before each race/day.
    d=v221.build(d,'date')
    d['y4']=(pd.to_numeric(d.get('winner'),errors='coerce')==4).astype(int)

    p=pd.read_csv(PRED,dtype={'race_code':str});p.race_code=p.race_code.str.zfill(12)
    pw=p.pivot_table(index=['date','race_code'],columns='variant',values='p4head',aggfunc='last').reset_index()
    pw['date']=pw.date.astype(str);d['date']=d.date.astype(str)
    d=d.merge(pw[['date','race_code','PRE','POST']],on=['date','race_code'],how='left')

    base=['PRE','POST']
    player4=[f'b4_pl_{k}' for k in ['all_win','all_p2','frame_win','frame_p2','recent_p2']]
    player3=[f'b3_pl_{k}' for k in ['all_win','all_p2','frame_win','frame_p2','recent_p2']]
    prior4=[f'b4_vh_{k}' for k in ['p12_display','p12_overall','p12_turn','p12_straight','delta_display','delta_turn','delta_straight']]
    prior3=[f'b3_vh_{k}' for k in ['p12_display','p12_overall','p12_turn','p12_straight','delta_display','delta_turn','delta_straight']]
    for c4n,c3n,k in zip(player4,player3,['all_win','all_p2','frame_win','frame_p2','recent_p2']):
        d[f'rel_pl_{k}']=pd.to_numeric(d[c4n],errors='coerce')-pd.to_numeric(d[c3n],errors='coerce')
    for k in ['p12_display','p12_overall','p12_turn','p12_straight','delta_display','delta_turn','delta_straight']:
        d[f'rel_vh_{k}']=pd.to_numeric(d[f'b4_vh_{k}'],errors='coerce')-pd.to_numeric(d[f'b3_vh_{k}'],errors='coerce')
    rel=[c for c in d.columns if c.startswith('rel_')]
    groups={
      'BASE_P4':base,
      'PLUS_PLAYER4':base+player4,
      'PLUS_PLAYER4_WALL3':base+player4+player3+rel[:5],
      'PLUS_PRIOR4':base+prior4,
      'PLUS_PLAYER_PRIOR':base+player4+prior4,
      'PLUS_ALL_3HEAD_STYLE':base+player4+player3+prior4+prior3+rel,
    }
    rows=[]
    for mon in MONTHS:
        first=pd.Timestamp(mon+'-01');nxt=first+pd.offsets.MonthBegin(1)
        tr=d[d._date<first].copy();te=d[(d._date>=first)&(d._date<nxt)].copy()
        for name,fs0 in groups.items():
            fs=[x for x in fs0 if x in d.columns and pd.to_numeric(d[x],errors='coerce').notna().mean()>=.60]
            if len(tr)<500 or tr.y4.nunique()<2:continue
            Xtr=tr[fs].apply(pd.to_numeric,errors='coerce');Xte=te[fs].apply(pd.to_numeric,errors='coerce')
            m=model();m.fit(Xtr,tr.y4);pr=m.predict_proba(Xte)[:,1]
            for (_,r),z in zip(te.iterrows(),pr):rows.append({'month':mon,'date':r.date,'race_code':r.race_code,'variant':name,'p':float(z),'y4':int(r.y4)})
    o=pd.DataFrame(rows);o.to_csv(OUT,index=False)

    L=['# v263 4-head: 3-head-derived features + player history audit','',
       '- Primary evaluation is Feb-Jun only; Jul/Aug excluded here because they are NON-PRISTINE and v221 history builder is intentionally pre-Jul.','- Every month trains only on earlier races. Player/history features are frozen before the race/day.','- Goal: identify a feature family that can sustain >=200 selected races and >=40% realized boat-4 win rate in Feb-Jun, not merely lift predicted probability.','',
       '## Variant diagnostics','|variant|AUC|best >=200R R|head rate|cut|','|---|---:|---:|---:|---:|']
    for name in groups:
        q=o[o.variant==name].copy();auc=roc_auc_score(q.y4,q.p) if q.y4.nunique()>1 else np.nan
        best=None
        for cut in np.arange(.15,.601,.0025):
            z=q[q.p>=cut]
            if len(z)<200:continue
            rec=(z.y4.mean(),len(z),cut,int(z.y4.sum()))
            if best is None or rec[0]>best[0] or (rec[0]==best[0] and rec[1]>best[1]):best=rec
        if best:L.append(f'|{name}|{auc:.4f}|{best[1]}|{100*best[0]:.2f}%|{best[2]:.4f}|')
        else:L.append(f'|{name}|{auc:.4f}|--|--|--|')
    L+=['','## Feasible cells >=200R and >=40%','|variant|cut|R|heads|head rate|monthly min|','|---|---:|---:|---:|---:|---:|']
    feasible=[]
    for name in groups:
        q=o[o.variant==name]
        for cut in np.arange(.15,.601,.0025):
            z=q[q.p>=cut]
            if len(z)<200 or z.y4.mean()<.40:continue
            mm=z.groupby('month').y4.agg(['count','mean']); mn=float(mm.loc[mm['count']>=15,'mean'].min()) if (mm['count']>=15).any() else np.nan
            feasible.append((mn,z.y4.mean(),len(z),name,cut,int(z.y4.sum())))
    feasible=sorted(feasible,key=lambda x:(x[0] if np.isfinite(x[0]) else -1,x[1],x[2]),reverse=True)
    for mn,hr,n,name,cut,h in feasible[:30]:L.append(f'|{name}|{cut:.4f}|{n}|{h}|{100*hr:.2f}%|{100*mn:.2f}%|')
    if not feasible:L.append('|none|--|--|--|--|--|')
    L+=['','## Interpretation','- Prefer variants that improve both aggregate head rate and monthly floor at >=200R.','- Do not adopt a rule from this retrospective search without future unseen validation.']
    SUM.write_text('\n'.join(L)+'\n',encoding='utf-8');print('\n'.join(L))
if __name__=='__main__':main()
