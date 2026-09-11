#!/usr/bin/env python3
"""v293: 1-head >=90% research with direct all-boat + prior-only history features.

Research rules
- Feature/model selection ends at 2026-06-30.
- Jul/Aug are not read for model selection/evaluation. Sep outcomes are not read at all.
- PRE variants contain no current-race exhibition/original-exhibition values.
- POST variants may use current exhibition after the 1-course entry gate is known.
- Player/prior exhibition history comes from v221.build(), which freezes day D traits
  before ingesting day D results/current preview into history.
- Monthly expanding walk-forward; Platt calibration and quantile cuts use training OOF only.
- Goal is realized 1-head rate, not ROI.
"""
from __future__ import annotations
from pathlib import Path
from collections import defaultdict
from datetime import date,timedelta
import math
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score,brier_score_loss,log_loss
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder,StandardScaler

import analyze_v108_1head_feasibility as v108
import analyze_v221_3head_scenario_pair as v221
from backtest import rows,race_features,grade_score,clamp,pct_motor
from backtest_v51_lane_corrected_tickets import corrected_direct,ff,ii,opp_place_score

ROOT=Path(__file__).resolve().parent
SRC=ROOT/'analysis_v108_1head_feasibility.csv'
PREFIX=ROOT/'analysis_v293_1head_direct_history'
SUMMARY=ROOT/'summary_v293_1head_direct_history_research.md'
PRELOAD=date(2025,10,1); END=date(2026,6,30); END_TS=pd.Timestamp(END)
TEST_MONTHS=['2026-02','2026-03','2026-04','2026-05','2026-06']
VENUES=[f'{i:02d}' for i in range(1,25)]
CUTS=[.75,.80,.82,.84,.86,.88,.90,.92,.94,.95,.96,.97,.98]
QS=[.90,.95,.975,.99,.995]
STATIC_KEYS=['grade','wr','local','motor','waku_wr','nst_strength','waku_sr_strength','past_win','meet_st_strength']
POST_KEYS=['ex','st','lap','turn','straight','orig_avg','direct','score']
PLAYER_KEYS=['all_win','all_p2','frame_races','frame_win','frame_p2','recent_p2']
PRIOR_KEYS=['p12_display','p12_overall','p12_turn','p12_straight','delta_display','delta_overall','delta_turn','delta_straight']


def bycode(rs):return {str(r.get('レースコード','')).zfill(12):r for r in rs if r.get('レースコード')}
def num(x):return pd.to_numeric(x,errors='coerce')
def safe_auc(y,p):return float(roc_auc_score(y,p)) if len(np.unique(y))>1 else float('nan')
def wilson(h,n):
    if not n:return (float('nan'),float('nan'))
    z=1.959963984540054;p=h/n;d=1+z*z/n;c=(p+z*z/(2*n))/d;r=z*math.sqrt((p*(1-p)+z*z/(4*n))/n)/d
    return max(0,c-r),min(1,c+r)

def fetch_day(d):
    y=d.strftime('%Y/%m/%d')
    return d,{'cards':rows(f'data/programs/race_cards/{y}.csv'),'waku':rows(f'data/programs/waku10/{y}.csv'),
              'tkz':rows(f'data/previews/tkz/{y}.csv'),'stt':rows(f'data/previews/stt/{y}.csv'),
              'orig':rows(f'data/previews/original_exhibition/{y}.csv')}

def boat_parts(x,b,ex,st,os):
    z=x[b]
    motor=.62*pct_motor(z['motor2'])+.38*pct_motor(z['motor3'])
    meet=.5 if z['meet_st'] is None else clamp((.22-z['meet_st'])/.12)
    direct=.35*ex[b]+.20*st[b]+.25*os[b]['turn']+.20*os[b]['avg']
    return {
      'grade':grade_score(z['grade']),'wr':clamp((z['wr']-3)/5),'local':clamp((z['local']-2.5)/5.5),
      'motor':motor,'waku_wr':clamp(z['waku_wr']/8),'nst_strength':clamp((.24-z['nst'])/.14),
      'waku_sr_strength':clamp((6-z['waku_sr'])/5),'past_win':z['past_win'],'meet_st_strength':meet,
      'ex':ex[b],'st':st[b],'lap':os[b]['lap'],'turn':os[b]['turn'],'straight':os[b]['straight'],
      'orig_avg':os[b]['avg'],'direct':direct,'score':opp_place_score(x,b,ex,st,os)
    }

def add_direct_source(base):
    """Rebuild pre/post all-boat components from source, preserving v108 prior-only ST-bias order."""
    idx=defaultdict(list)
    for ix,r in base.iterrows():
        dt=pd.to_datetime(r.date,errors='coerce')
        if pd.notna(dt) and dt<=END_TS:idx[str(r.race_code).zfill(12)].append(ix)
    days=[];d=PRELOAD
    while d<=END:days.append(d);d+=timedelta(days=1)
    from concurrent.futures import ThreadPoolExecutor,as_completed
    fetched={}
    with ThreadPoolExecutor(max_workers=10) as ex:
        fut=[ex.submit(fetch_day,d) for d in days]
        for j,f in enumerate(as_completed(fut),1):
            dd,z=f.result();fetched[dd]=z
            if j%60==0:print('source',j,'/',len(days),flush=True)
    sums=defaultdict(list);allv=[];extra={}
    for d in sorted(fetched):
        z=fetched[d];bias=v108.st_bias(sums,allv);cm=bycode(z['cards']);wm=bycode(z['waku']);tm=bycode(z['tkz']);sm=bycode(z['stt']);om=bycode(z['orig'])
        for code,ixes in [(c,idx[c]) for c in idx if c[:8]==d.strftime('%Y%m%d')]:
            card=cm.get(code);w=wm.get(code)
            if not card or not w:continue
            x=race_features(card,w);exs,sts,oss=corrected_direct(code,tm,sm,om,bias)
            for b in range(1,7):
                exs.setdefault(b,.5);sts.setdefault(b,.5);oss.setdefault(b,{'lap':.5,'turn':.5,'straight':.5,'avg':.5})
                for k in ('lap','turn','straight','avg'):oss[b].setdefault(k,.5)
            q={}
            for b in range(1,7):
                p=boat_parts(x,b,exs,sts,oss)
                for k,v in p.items():q[f'b{b}_{k}']=v
            for ix in ixes:extra[ix]=q
        v108.update_st(z['stt'],sums,allv)
    e=pd.DataFrame.from_dict(extra,orient='index')
    return base.join(e,how='left')

def add_rel(d):
    # Direct boat1-vs-opponent relations. Positive means boat1 stronger for strength-oriented columns.
    for k in STATIC_KEYS+POST_KEYS:
        a=f'b1_{k}'
        if a not in d:continue
        for b in range(2,7):
            z=f'b{b}_{k}'
            if z in d:d[f'rel_{k}_1v{b}']=num(d[a])-num(d[z])
        opp=[f'b{b}_{k}' for b in range(2,7) if f'b{b}_{k}' in d]
        if opp:
            o=d[opp].apply(num)
            d[f'rel_{k}_1vbest']=num(d[a])-o.max(axis=1)
            d[f'rel_{k}_1vavg']=num(d[a])-o.mean(axis=1)
    for fam,keys in [('pl',PLAYER_KEYS),('vh',PRIOR_KEYS),('gh',PRIOR_KEYS)]:
        for k in keys:
            a=f'b1_{fam}_{k}'
            if a not in d:continue
            for b in range(2,7):
                z=f'b{b}_{fam}_{k}'
                if z in d:d[f'rel_{fam}_{k}_1v{b}']=num(d[a])-num(d[z])
            opp=[f'b{b}_{fam}_{k}' for b in range(2,7) if f'b{b}_{fam}_{k}' in d]
            if opp:
                o=d[opp].apply(num);d[f'rel_{fam}_{k}_1vbest']=num(d[a])-o.max(axis=1);d[f'rel_{fam}_{k}_1vavg']=num(d[a])-o.mean(axis=1)
    # Explicit wall/attack risks; higher = greater threat to boat1.
    if all(f'b{x}_st' in d for x in [1,2,3]):
        d['wall23_st_attack']=d[['b2_st','b3_st']].apply(num).max(axis=1)-num(d.b1_st)
        d['boat2_st_wall_gap']=num(d.b2_st)-num(d.b1_st)
    if all(f'b{x}_direct' in d for x in [1,2,3]):
        d['wall23_direct_attack']=d[['b2_direct','b3_direct']].apply(num).max(axis=1)-num(d.b1_direct)
    if all(f'b{x}_motor' in d for x in [1,2,3]):
        d['wall23_motor_attack']=d[['b2_motor','b3_motor']].apply(num).max(axis=1)-num(d.b1_motor)
    return d

def available(d,cols,mincov=.55):
    out=[]
    for c in cols:
        if c in d and num(d[c]).notna().mean()>=mincov and num(d[c]).nunique(dropna=True)>1 and c not in out:out.append(c)
    return out

def families(d):
    static=[f'b{b}_{k}' for b in range(1,7) for k in STATIC_KEYS]
    staticrel=[c for c in d if c.startswith('rel_') and any(c.startswith('rel_'+k+'_') for k in STATIC_KEYS)]
    pl=[c for c in d if ('_pl_' in c or c.startswith('rel_pl_'))]
    prior=[c for c in d if ('_vh_' in c or '_gh_' in c or c.startswith('rel_vh_') or c.startswith('rel_gh_'))]
    post=[f'b{b}_{k}' for b in range(1,7) for k in POST_KEYS]
    postrel=[c for c in d if c.startswith('rel_') and any(c.startswith('rel_'+k+'_') for k in POST_KEYS)]
    wall=[c for c in ['wall23_st_attack','boat2_st_wall_gap','wall23_direct_attack','wall23_motor_attack'] if c in d]
    pre_static=available(d,static+staticrel)
    pre_hist=available(d,static+staticrel+pl+prior)
    post_direct=available(d,static+staticrel+post+postrel+wall)
    post_hist=available(d,static+staticrel+pl+prior+post+postrel+wall)
    return {
      'PRE_LR_DIRECT':('lr',pre_static),
      'PRE_HGB_HISTORY':('hgb',pre_hist),
      'POST_LR_DIRECT':('lr',post_direct),
      'POST_HGB_HISTORY':('hgb',post_hist),
    }

def pipe(kind,fs):
    if kind=='lr':
        pre=ColumnTransformer([('n',Pipeline([('i',SimpleImputer(strategy='median')),('s',StandardScaler())]),fs),('v',OneHotEncoder(categories=[VENUES],handle_unknown='ignore'),['venue'])])
        return Pipeline([('p',pre),('m',LogisticRegression(C=.25,max_iter=2500))])
    pre=ColumnTransformer([('n',SimpleImputer(strategy='median'),fs),('v',OneHotEncoder(categories=[VENUES],handle_unknown='ignore',sparse_output=False),['venue'])],sparse_threshold=0)
    return Pipeline([('p',pre),('m',HistGradientBoostingClassifier(max_iter=240,learning_rate=.045,max_leaf_nodes=15,min_samples_leaf=35,l2_regularization=1.5,random_state=293))])
def fitpred(kind,fs,tr,te):
    m=pipe(kind,fs);m.fit(tr[fs+['venue']],tr.head_hit);return m.predict_proba(te[fs+['venue']])[:,1]
def logit(p):p=np.clip(np.asarray(p,float),1e-6,1-1e-6);return np.log(p/(1-p))
def oof(kind,fs,tr):
    ms=sorted(tr.month.unique());a=[]
    for i in range(2,len(ms)):
        x=tr[tr.month.isin(ms[:i])];v=tr[tr.month==ms[i]]
        if len(x)<500 or v.empty:continue
        z=v[['date','month','race_code','head_hit']].copy();z['p']=fitpred(kind,fs,x,v);a.append(z)
    if not a:raise RuntimeError('no temporal OOF')
    return pd.concat(a,ignore_index=True)
def calfit(o):
    c=LogisticRegression(C=1e6,max_iter=1000);c.fit(logit(o.p).reshape(-1,1),o.head_hit);return c
def cal(c,p):return c.predict_proba(logit(p).reshape(-1,1))[:,1]
def smet(y,p):
    p=np.clip(np.asarray(p,float),1e-6,1-1e-6);y=np.asarray(y,int)
    return safe_auc(y,p),float(brier_score_loss(y,p)),float(log_loss(y,p,labels=[0,1]))
def selmet(g):
    n=len(g);h=int(g.head_hit.sum()) if n else 0;lo,hi=wilson(h,n)
    mm=g.groupby('test_month').head_hit.agg(['size','mean']) if n else pd.DataFrame()
    return {'R':n,'heads':h,'head_rate':h/n if n else np.nan,'wilson_lo':lo,'wilson_hi':hi,'months_covered':len(mm),'worst_month_head_rate':float(mm['mean'].min()) if len(mm) else np.nan,'min_month_R':int(mm['size'].min()) if len(mm) else 0}

def run(d,fams):
    preds=[];fm=[]
    for name,(kind,fs0) in fams.items():
        for tm in TEST_MONTHS:
            tr=d[d.month<tm].copy();te=d[d.month==tm].copy();fs=available(tr,fs0,.55)
            if len(fs)<5 or te.empty:continue
            oo=oof(kind,fs,tr);cc=calfit(oo);oop=cal(cc,oo.p);raw=fitpred(kind,fs,tr,te);pc=cal(cc,raw)
            z=te[['date','month','race_code','venue','race','head_hit']].copy();z['variant']=name;z['test_month']=tm;z['p_raw']=raw;z['p_cal']=pc
            for q in QS:
                ct=float(np.quantile(oop,q));z[f'q{q}_sel']=(pc>=ct).astype(int);z[f'q{q}_cut']=ct
            preds.append(z);fm.append({'variant':name,'month':tm,'features':len(fs),'train':len(tr),'test':len(te),'oof':len(oo)})
            print(name,tm,'f',len(fs),'tr',len(tr),'te',len(te),flush=True)
    return pd.concat(preds,ignore_index=True),pd.DataFrame(fm)
def evaluate(p):
    met=[];sel=[]
    for n,g in p.groupby('variant'):
        for sc in ['p_raw','p_cal']:
            A,B,L=smet(g.head_hit,g[sc]);met.append({'variant':n,'score':sc,'scope':'pooled_Feb-Jun','R':len(g),'auc':A,'brier':B,'logloss':L})
            for c in CUTS:sel.append({'variant':n,'score':sc,'source':'fixed_probability','rule':f'>={c:.3f}','cut':c,**selmet(g[g[sc]>=c])})
        for q in QS:sel.append({'variant':n,'score':'p_cal','source':'training_OOF_quantile','rule':f'q{q:.3f}','cut':np.nan,**selmet(g[g[f'q{q}_sel']==1])})
    return pd.DataFrame(met),pd.DataFrame(sel)
def pct(x):return '-' if pd.isna(x) else f'{100*x:.2f}%'
def make_summary(d,fams,meta,met,sel):
    L=['# v293 1HEAD direct/history PRE-POST research','',
       '- Research only; production unchanged.','- Model-selection/evaluation window ends 2026-06-30. Jul/Aug excluded; Sep outcomes unread.',
       '- Monthly expanding walk-forward. Platt calibration/quantile gates are training-OOF only.',
       '- PRE variants exclude every current-race exhibition/original-exhibition feature. POST variants may use them after entry confirmation.','',
       '## Feature sets','|variant|family|available features|','|---|---|---:|']
    for n,(k,fs) in fams.items():L.append(f'|{n}|{k}|{len(fs)}|')
    L+=['','## Pooled Feb-Jun metrics','|variant|score|R|AUC|Brier|LogLoss|','|---|---|---:|---:|---:|---:|']
    for _,r in met.sort_values(['score','brier']).iterrows():L.append(f'|{r.variant}|{r.score}|{int(r.R)}|{r.auc:.4f}|{r.brier:.4f}|{r.logloss:.4f}|')
    good=sel[(sel.R>=100)&(sel.head_rate>=.90)].sort_values(['R','wilson_lo'],ascending=False)
    L+=['','## >=90% realized zones, R>=100']
    if good.empty:L.append('- None.')
    else:
        L+=['|variant|score|source|rule|R|heads|rate|Wilson low|worst month|min month R|','|---|---|---|---|---:|---:|---:|---:|---:|---:|']
        for _,r in good.head(40).iterrows():L.append(f'|{r.variant}|{r.score}|{r.source}|{r.rule}|{int(r.R)}|{int(r.heads)}|{pct(r.head_rate)}|{pct(r.wilson_lo)}|{pct(r.worst_month_head_rate)}|{int(r.min_month_R)}|')
    best=sel[sel.R>=100].sort_values(['head_rate','wilson_lo','R'],ascending=False).head(25)
    L+=['','## Best zones with R>=100','|variant|score|source|rule|R|rate|Wilson low|worst month|min month R|','|---|---|---|---|---:|---:|---:|---:|---:|']
    for _,r in best.iterrows():L.append(f'|{r.variant}|{r.score}|{r.source}|{r.rule}|{int(r.R)}|{pct(r.head_rate)}|{pct(r.wilson_lo)}|{pct(r.worst_month_head_rate)}|{int(r.min_month_R)}|')
    L+=['','## Interpretation rule','- A realized >=90% row is a research finding, not yet production adoption. Require sample size, monthly floor, and prospective outcome-blind validation.','- If PRE improves materially, prioritize it for operational robustness. If only POST reaches the zone, keep PRE/POST separate rather than leaking exhibition into PRE.']
    return '\n'.join(L)+'\n'
def main():
    d=pd.read_csv(SRC,encoding='utf-8-sig',dtype={'race_code':str});d['race_code']=d.race_code.str.zfill(12);d['date']=pd.to_datetime(d.date,errors='coerce');d=d[(num(d.valid_result)==1)&(d.date<=END_TS)].copy();d['month']=d.date.dt.strftime('%Y-%m');d['venue']=d.venue.astype(str).str.replace('.0','',regex=False).str.zfill(2);d['head_hit']=num(d.head_hit).astype(int)
    if (d.date>=pd.Timestamp('2026-07-01')).any():raise RuntimeError('Jul/Aug leakage')
    print('base',len(d),flush=True);d=add_direct_source(d);print('direct source added',flush=True);d=v221.build(d,'date');print('prior history added',flush=True);d=add_rel(d)
    fams=families(d);p,meta=run(d,fams);met,sel=evaluate(p)
    p.to_csv(str(PREFIX)+'_predictions.csv',index=False,encoding='utf-8-sig');meta.to_csv(str(PREFIX)+'_folds.csv',index=False,encoding='utf-8-sig');met.to_csv(str(PREFIX)+'_metrics.csv',index=False,encoding='utf-8-sig');sel.to_csv(str(PREFIX)+'_selection.csv',index=False,encoding='utf-8-sig')
    SUMMARY.write_text(make_summary(d,fams,meta,met,sel),encoding='utf-8');print(SUMMARY.read_text(),flush=True)
if __name__=='__main__':main()
