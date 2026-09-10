#!/usr/bin/env python3
"""v278: decompose current exhibition information for 4-head opponent selection.

Important finding from code audit: v93/v96's `direct` feature uses current display
and original-exhibition turn/average, but its ST term is the prior-only corrected
ST strength from the model row, not the current start-exhibition rank returned by
`corrected_direct`.  It also does not expose current original lap/straight as
separate opponent features.  v278 measures those pre-result components directly.

Discipline
----------
* 2026-07/08 excluded; September not read.
* Current preview files are loaded before outcome use; outcomes are labels only.
* No odds are used.
* Each role-model evaluation month trains only on earlier boat-4-win races.
* v268/v273 head selectors are unchanged; S+A is reporting only.
"""
from __future__ import annotations
from pathlib import Path
from collections import defaultdict
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

import analyze_v274_4head_opponent_feature_audit as v274
import analyze_v270_4head_win_feature_importance as v270
import analyze_v251_4head_newroi_bridge as v251
import analyze_v96_4corner_monthly_walkforward_tiebreak as v96
from backtest import rows
from backtest_v51_lane_corrected_tickets import corrected_direct

ROOT=Path(__file__).resolve().parent
OUT_UNI=ROOT/'analysis_v278_4head_opponent_current_exhibition_univariate.csv'
OUT_FAM=ROOT/'analysis_v278_4head_opponent_current_exhibition_family.csv'
OUT_MONTH=ROOT/'analysis_v278_4head_opponent_current_exhibition_monthly.csv'
SUM=ROOT/'summary_v278_4head_opponent_current_exhibition_audit.md'
BOATS=v274.BOATS
MONTHS=('2026-02','2026-03','2026-04','2026-05','2026-06')
HOLD=('2026-04','2026-05','2026-06')
MIN_TRAIN=40
CUR=('cur_ex','cur_st','cur_orig_lap','cur_orig_turn','cur_orig_straight','cur_orig_avg')
BASE=('v93_grade','v93_national','v93_local','v93_motor','v93_waku','v93_nst')
PLAYER=('pref_pl_all_p2','pref_pl_all_win','pref_pl_frame_p2','pref_pl_recent_p2','pref_pl_frame_win')


def bycode(path):
    return {str(r.get('レースコード','')).zfill(12):r for r in rows(path) if r.get('レースコード')}

def model():
    return Pipeline([('imp',SimpleImputer(strategy='median')),('sc',StandardScaler()),
                     ('lr',LogisticRegression(C=.16,max_iter=2500))])

def add_current(long):
    z=long.copy();cache={};vals=[]
    for _,r in z.iterrows():
        ds=str(r.date);code=str(r.race_code).zfill(12);b=int(r.boat);ymd=ds.replace('-','/')
        if ds not in cache:
            cache[ds]=(bycode(f'data/previews/tkz/{ymd}.csv'),
                       bycode(f'data/previews/stt/{ymd}.csv'),
                       bycode(f'data/previews/original_exhibition/{ymd}.csv'))
        tkz,stt,orig=cache[ds]
        ex,st,os=corrected_direct(code,tkz,stt,orig,{i:0.0 for i in range(1,7)})
        q=os.get(b,{'lap':.5,'turn':.5,'straight':.5,'avg':.5})
        vals.append((ex.get(b,np.nan),st.get(b,np.nan),q.get('lap',np.nan),q.get('turn',np.nan),q.get('straight',np.nan),q.get('avg',np.nan)))
    for j,c in enumerate(CUR):z[c]=[x[j] for x in vals]
    return z

def univariate(z):
    rowsout=[]
    q=z[z.month.isin(MONTHS)].copy()
    for c in CUR:
        for role,yc in [('SECOND','y2'),('THIRD','y3')]:
            x=pd.to_numeric(q[c],errors='coerce');m=x.notna()
            if m.sum()<50 or q.loc[m,yc].nunique()<2:continue
            a=roc_auc_score(q.loc[m,yc],x[m]);sgn=1 if a>=.5 else -1;auc=max(a,1-a)
            top1=top2=n=0;mons=[];pos=0;seen=0
            t=q.loc[m,['race_code','month','boat',yc]].copy();t['x']=sgn*x[m].to_numpy()
            for _,g in t.groupby('race_code'):
                if len(g)!=5 or g[yc].sum()!=1:continue
                gg=g.sort_values(['x','boat'],ascending=[False,True]);actual=int(gg.loc[gg[yc]==1,'boat'].iloc[0]);pred=gg.boat.astype(int).tolist();n+=1
                top1+=int(pred[0]==actual);top2+=int(actual in pred[:2])
            for mon,g in t.groupby('month'):
                if g[yc].sum()<5:continue
                ma=roc_auc_score(g[yc],g.x);seen+=1;pos+=int(ma>.5);mons.append(f'{mon}:{ma:.3f}')
            rowsout.append({'role':role,'feature':c,'direction':'high' if sgn==1 else 'low','auc':auc,
                            'races':n,'top1_pct':100*top1/n if n else np.nan,'top2_pct':100*top2/n if n else np.nan,
                            'month_positive':pos,'month_seen':seen,'month_auc':';'.join(mons)})
    return pd.DataFrame(rowsout).sort_values(['role','auc'],ascending=[True,False])

def good(tr,fs):
    out=[]
    for c in fs:
        if c not in tr:continue
        x=pd.to_numeric(tr[c],errors='coerce')
        if x.notna().mean()>=.55 and x.nunique(dropna=True)>=2:out.append(c)
    return out

def pair_order(g,p2,p3):
    d2={int(b):float(p) for b,p in zip(g.boat,p2)};d3={int(b):float(p) for b,p in zip(g.boat,p3)}
    a=[]
    for s in BOATS:
        for t in BOATS:
            if s==t:continue
            sc=np.log(max(d2[s],1e-9))+np.log(max(d3[t],1e-9));a.append((sc,s,t))
    a.sort(key=lambda x:(-x[0],x[1],x[2]));return [(s,t) for _,s,t in a]

def prank(order,actual):
    try:return order.index(actual)+1
    except ValueError:return 0

def predict(z,fs,name,base,sel):
    out=[]
    for mon in MONTHS:
        tr=z[z.month<mon].copy();te=z[z.month==mon].copy()
        if tr.race_code.nunique()<MIN_TRAIN or te.empty:continue
        use=good(tr,fs)
        if len(use)<4:continue
        m2=model();m3=model();m2.fit(tr[use],tr.y2);m3.fit(tr[use],tr.y3)
        te=te.copy();te['p2']=m2.predict_proba(te[use])[:,1];te['p3']=m3.predict_proba(te[use])[:,1]
        for code,g in te.groupby('race_code'):
            if len(g)!=5:continue
            actual=(int(g.loc[g.y2==1,'boat'].iloc[0]),int(g.loc[g.y3==1,'boat'].iloc[0]))
            new=pair_order(g,g.p2,g.p3);key=(str(g.date.iloc[0]),str(code).zfill(12));old=base.get(key,[])
            out.append({'family':name,'month':mon,'date':g.date.iloc[0],'race_code':str(code).zfill(12),
                        'n_features':len(use),'new_rank':prank(new,actual),'v96_rank':prank(old,actual),
                        'selected_SA':int(str(code).zfill(12) in sel)})
    return pd.DataFrame(out)

def metrics(g,prefix):
    o={'races':len(g)}
    for k in (1,2,4,6,10,20):o[f'{prefix}_top{k}_pct']=100*((g[f'{prefix}_rank']>0)&(g[f'{prefix}_rank']<=k)).mean() if len(g) else np.nan
    return o

def main():
    d,_,_=v270.prepare();d=d[d._date<pd.Timestamp('2026-07-01')].copy();d['date']=d.date.astype(str)
    specs=v274.feature_specs(d);long=v274.build_long(d,specs);z=add_current(long)
    uni=univariate(z);uni.to_csv(OUT_UNI,index=False)
    base=v251.pair_orders(v96.read());sel=v274.selected_codes()
    fams={'CURRENT_ONLY':list(CUR),
          'BASE_CURRENT':list(BASE+CUR),
          'BASE_CURRENT_PLAYER':list(BASE+CUR+PLAYER)}
    pp=[]
    for n,fs in fams.items():
        q=predict(z,fs,n,base,sel)
        if not q.empty:pp.append(q)
    p=pd.concat(pp,ignore_index=True);rowsout=[];monthly=[]
    for fam,g in p.groupby('family'):
        for scope,gg in [('ALL',g),('HOLD_ALL',g[g.month.isin(HOLD)]),('HOLD_SA',g[(g.month.isin(HOLD))&(g.selected_SA==1)])]:
            if gg.empty:continue
            rec={'family':fam,'scope':scope,'avg_features':gg.n_features.mean(),**metrics(gg,'new'),**metrics(gg,'v96')}
            for k in (1,2,4,6,10):rec[f'delta_top{k}_pt']=rec[f'new_top{k}_pct']-rec[f'v96_top{k}_pct']
            rowsout.append(rec)
        for mon,gg in g[g.month.isin(HOLD)].groupby('month'):
            monthly.append({'family':fam,'month':mon,**metrics(gg,'new'),**metrics(gg,'v96')})
    o=pd.DataFrame(rowsout);o.to_csv(OUT_FAM,index=False);pd.DataFrame(monthly).to_csv(OUT_MONTH,index=False)

    L=['# v278 4-head opponent current-exhibition component audit','',
       '- Code audit: v93/v96 direct = 35% current display + 20% prior-only corrected ST strength + 25% current original turn + 20% current original average.',
       '- Therefore current start-exhibition itself and separate current original lap/straight were not explicit v96 opponent features.',
       '- v278 decomposes current display, current start exhibition, lap, turn, straight and average.',
       '- Jul/Aug excluded; September not read; no odds; head selectors unchanged.','']
    for role in ('SECOND','THIRD'):
        L += [f'## {role}: current exhibition components','',
              '|feature|direction|AUC|Top1|Top2|month +|','|---|---|---:|---:|---:|---:|']
        for _,r in uni[uni.role==role].iterrows():
            L.append(f'|{r.feature}|{r.direction}|{r.auc:.4f}|{r.top1_pct:.1f}%|{r.top2_pct:.1f}%|{int(r.month_positive)}/{int(r.month_seen)}|')
        L.append('')
    L += ['## Apr-Jun role-model pair comparison','',
          '|scope|family|R|T1|T2|T4|T6|T10|v96 T2|T4|T6|T10|',
          '|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for scope in ('HOLD_ALL','HOLD_SA'):
        for _,r in o[o.scope==scope].sort_values(['new_top2_pct','new_top4_pct'],ascending=False).iterrows():
            L.append(f'|{scope}|{r.family}|{int(r.races)}|{r.new_top1_pct:.1f}%|{r.new_top2_pct:.1f}%|{r.new_top4_pct:.1f}%|{r.new_top6_pct:.1f}%|{r.new_top10_pct:.1f}%|{r.v96_top2_pct:.1f}%|{r.v96_top4_pct:.1f}%|{r.v96_top6_pct:.1f}%|{r.v96_top10_pct:.1f}%|')
    # identify current component with best cross-role/consistency evidence
    u=uni.copy();u['cons']=u.month_positive/u.month_seen.replace(0,np.nan);u['score']=(u.auc-.5)*u.cons
    best=u.sort_values(['score','auc'],ascending=False).iloc[0]
    L += ['','## Finding',
          f'- Strongest stable decomposed current component: **{best.feature}** for {best.role}, AUC {best.auc:.4f}, month consistency {int(best.month_positive)}/{int(best.month_seen)}.',
          '- Do not replace v96 from this audit alone. If one or more current components are stable, the next safe test is a v96 Top4-preserving tiebreak using only those components, analogous to v277.',
          '- This keeps the robust v96 candidate set while testing whether current exhibition can improve ordering inside that set.']
    SUM.write_text('\n'.join(L)+'\n',encoding='utf-8');print('\n'.join(L))

if __name__=='__main__':main()
