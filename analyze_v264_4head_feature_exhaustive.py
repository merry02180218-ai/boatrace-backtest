#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import re
import numpy as np, pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score
import analyze_v96_4corner_monthly_walkforward_tiebreak as c4
import analyze_v221_3head_scenario_pair as v221

ROOT=Path(__file__).resolve().parent
PRED=ROOT/'analysis_v250_4head_rebuild_baseline.csv'
OUT=ROOT/'analysis_v264_4head_feature_exhaustive.csv'
UNI=ROOT/'analysis_v264_4head_feature_univariate.csv'
SUM=ROOT/'summary_v264_4head_feature_exhaustive.md'
MONTHS=[f'2026-{m:02d}' for m in range(2,7)]
TOPS=[10,20,30,50,100,150,200,300]

LEAK_PATTERNS=(
 'winner','second','third','payout','actual_','head_hit','ticket','route_hit','kimarite',
 'valid_result','valid_payout','result_join','production_buy','approved_','y4','_target'
)

def num(s): return pd.to_numeric(s,errors='coerce')
def goodcol(d,c,mincov=.60):
    if c not in d.columns:return False
    lc=c.lower()
    if any(x in lc for x in LEAK_PATTERNS):return False
    x=num(d[c]); return x.notna().mean()>=mincov and x.nunique(dropna=True)>=2

def lr_model():
    return Pipeline([('imp',SimpleImputer(strategy='median')),('sc',StandardScaler()),('lr',LogisticRegression(C=.18,max_iter=2500))])

def hgb_model():
    return Pipeline([('imp',SimpleImputer(strategy='median')),('hgb',HistGradientBoostingClassifier(max_iter=180,learning_rate=.045,max_leaf_nodes=15,l2_regularization=1.5,min_samples_leaf=35,random_state=264))])

def add_rel(d):
    # 3-head-success analogues: relative ST / attack lanes around boat 4.
    for family in ['st_raw','st_corr_strength','st_raw_strength','st_corr_rank','st_raw_rank']:
        c4n=f'{family}_b4'
        if c4n not in d:continue
        for b in [1,2,3,5,6]:
            cb=f'{family}_b{b}'
            if cb in d:d[f'rel_{family}_4v{b}']=num(d[c4n])-num(d[cb])
    # player/course and prior-foot relations, boat4 versus every pressure/resistance boat.
    for k in ['all_win','all_p2','frame_races','frame_win','frame_p2','recent_p2']:
        a=f'b4_pl_{k}'
        if a in d:
            for b in [1,2,3,5,6]:
                z=f'b{b}_pl_{k}'
                if z in d:d[f'rel_pl_{k}_4v{b}']=num(d[a])-num(d[z])
    for k in ['p12_display','p12_overall','p12_turn','p12_straight','delta_display','delta_overall','delta_turn','delta_straight']:
        a=f'b4_vh_{k}'
        if a in d:
            for b in [1,2,3,5,6]:
                z=f'b{b}_vh_{k}'
                if z in d:d[f'rel_vh_{k}_4v{b}']=num(d[a])-num(d[z])
    # attack x wall / resistance interactions.
    if 'POST' in d and 'PRE' in d:d['p4_joint']=num(d.POST)*num(d.PRE)
    if 'st_raw_b4' in d and 'st_raw_b3' in d:
        d['attack4_st_edge3']=num(d.st_raw_b3)-num(d.st_raw_b4)
    if 'st_corr_strength_b4' in d and 'st_corr_strength_b3' in d:
        d['attack4_corr_strength_edge3']=num(d.st_corr_strength_b4)-num(d.st_corr_strength_b3)
    if 'v91_straight' in d and 'st_raw_b4' in d:
        d['attack4_stretch_x_st']=num(d.v91_straight)*(0.30-num(d.st_raw_b4))
    if 'entry_confirmed_same' in d and 'POST' in d:
        d['post_x_entry_same']=num(d.POST)*num(d.entry_confirmed_same)
    return d

def families(d):
    base=[c for c in ['PRE','POST'] if goodcol(d,c)]
    st=[c for c in d.columns if (c.startswith('st_') or c.startswith('rel_st_') or c.startswith('attack4_')) and goodcol(d,c)]
    player=[c for c in d.columns if (re.match(r'b[1-6]_pl_',c) or c.startswith('rel_pl_')) and goodcol(d,c)]
    prior=[c for c in d.columns if (re.match(r'b[1-6]_[vg]h_',c) or c.startswith('rel_vh_')) and goodcol(d,c)]
    opp=[c for c in d.columns if (c.startswith('opp_') or c.startswith('rank_b')) and goodcol(d,c)]
    env=[c for c in ['preview_comp','relative_deg','relative_wind','wind_speed','wind_adjust_points','entry_confirmed_same','entry_course_preview','has_orig','has_stt','has_tkz','tilt','tilt_bonus','v91_ex','v91_st_corr','v91_st_raw','v91_straight','score_BASE_v91','score_CORR20_v91','score_RAW20_v91','score_wind_v83','history_adjust_online','history_pct_online','p4_joint','post_x_entry_same'] if goodcol(d,c)]
    allsafe=[]
    for c in base+st+player+prior+opp+env:
        if c not in allsafe:allsafe.append(c)
    return {
      'BASE_P4':base,
      'ST_3HEAD_ANALOG':base+st,
      'PLAYER_COURSE':base+player,
      'PRIOR_FOOT':base+prior,
      'OPP_CONTEXT':base+opp,
      'ENV_ENTRY':base+env,
      'ALL_SAFE_LINEAR':allsafe,
      'ALL_SAFE_HGB':allsafe,
    }

def topstats(q):
    q=q.sort_values('p',ascending=False).reset_index(drop=True); out=[]
    for n in TOPS:
        z=q.head(min(n,len(q)))
        if len(z):out.append((n,len(z),int(z.y4.sum()),z.y4.mean()))
    # largest cumulative N that still reaches 40/50/60%.
    cs=q.y4.cumsum()/np.arange(1,len(q)+1)
    mx={t:int(np.where(cs>=t)[0].max()+1) if np.any(cs>=t) else 0 for t in [.40,.50,.60]}
    return out,mx

def main():
    d=pd.DataFrame(c4.read());d['race_code']=d.race_code.astype(str).str.zfill(12);d['_date']=pd.to_datetime(d.date,errors='coerce')
    d=d[d._date<pd.Timestamp('2026-07-01')].copy();d=v221.build(d,'date')
    d['y4']=(num(d['winner'])==4).astype(int)
    p=pd.read_csv(PRED,dtype={'race_code':str});p.race_code=p.race_code.str.zfill(12)
    pw=p.pivot_table(index=['date','race_code'],columns='variant',values='p4head',aggfunc='last').reset_index();pw['date']=pw.date.astype(str);d['date']=d.date.astype(str)
    d=d.merge(pw[['date','race_code','PRE','POST']],on=['date','race_code'],how='left');d=add_rel(d)
    groups=families(d)
    preds=[]; coefs=[]
    for mon in MONTHS:
        first=pd.Timestamp(mon+'-01');nxt=first+pd.offsets.MonthBegin(1);tr=d[d._date<first].copy();te=d[(d._date>=first)&(d._date<nxt)].copy()
        for name,fs0 in groups.items():
            fs=[]
            for c in fs0:
                if goodcol(tr,c,.55) and c not in fs:fs.append(c)
            if len(fs)<2 or len(tr)<500 or te.empty:continue
            Xtr=tr[fs].apply(num);Xte=te[fs].apply(num)
            m=hgb_model() if name=='ALL_SAFE_HGB' else lr_model();m.fit(Xtr,tr.y4);pr=m.predict_proba(Xte)[:,1]
            for (_,r),z in zip(te.iterrows(),pr):preds.append({'month':mon,'date':r.date,'race_code':r.race_code,'variant':name,'p':float(z),'y4':int(r.y4)})
            if name=='ALL_SAFE_LINEAR':
                coef=m.named_steps['lr'].coef_[0]
                for c,v in zip(fs,coef):coefs.append({'month':mon,'feature':c,'coef':float(v)})
    o=pd.DataFrame(preds);o.to_csv(OUT,index=False)
    # Univariate descriptive audit on Feb-Jun pooled rows. It is explicitly retrospective.
    uq=[];ev=d[d._date.between(pd.Timestamp('2026-02-01'),pd.Timestamp('2026-06-30'))].copy()
    for c in groups['ALL_SAFE_LINEAR']:
        x=num(ev[c]);z=ev.loc[x.notna(),['y4']].copy();z['x']=x[x.notna()]
        if len(z)<300 or z.x.nunique()<4:continue
        try:a=roc_auc_score(z.y4,z.x); au=max(a,1-a);direction='high' if a>=.5 else 'low'
        except:continue
        z=z.sort_values('x',ascending=(direction=='low'));n=max(20,int(len(z)*.10));top=z.head(n)
        uq.append({'feature':c,'auc_oriented':au,'direction':direction,'n':len(z),'top10_n':len(top),'top10_head_rate':top.y4.mean(),'overall_head_rate':z.y4.mean(),'lift_pt':100*(top.y4.mean()-z.y4.mean())})
    u=pd.DataFrame(uq).sort_values(['auc_oriented','lift_pt'],ascending=False);u.to_csv(UNI,index=False)

    L=['# v264 4-head exhaustive feature audit','',
       '- Primary evaluation: Feb-Jun 2026 only; every month trains on earlier races only.','- Jul/Aug are excluded from this v264 audit.','- v221 player/prior-exhibition traits are frozen before the current day.','- Current-race ST/entry/wind/legacy POST fields are allowed only as pre-result final-selection features.','- Result/payout/ticket/actual-combination fields are explicitly excluded.','- Research/model-selection evidence only; not pristine validation.','',
       '## Variant diagnostics','|variant|features|AUC|best >=200R head rate|R|cut|','|---|---:|---:|---:|---:|---:|']
    for name,fs in groups.items():
        q=o[o.variant==name].copy();auc=roc_auc_score(q.y4,q.p) if len(q) and q.y4.nunique()>1 else np.nan;best=None
        for cut in np.arange(.10,.701,.0025):
            z=q[q.p>=cut]
            if len(z)<200:continue
            rec=(z.y4.mean(),len(z),cut)
            if best is None or rec[0]>best[0] or (rec[0]==best[0] and rec[1]>best[1]):best=rec
        L.append(f'|{name}|{len(fs)}|{auc:.4f}|{100*best[0]:.2f}%|{best[1]}|{best[2]:.4f}|' if best else f'|{name}|{len(fs)}|{auc:.4f}|--|--|--|')
    L+=['','## Top-N realized head rate','|variant|N|heads|head rate|','|---|---:|---:|---:|']
    for name in groups:
        q=o[o.variant==name];ts,mx=topstats(q)
        for n,nn,h,hr in ts:L.append(f'|{name}|{nn}|{h}|{100*hr:.2f}%|')
        L.append(f'|{name} max cumulative >=40/50/60%|{mx[.40]}/{mx[.50]}/{mx[.60]}|--|--|')
    L+=['','## Strongest individual features (retrospective descriptive)','|feature|oriented AUC|direction|top10 head rate|lift|','|---|---:|---|---:|---:|']
    for _,r in u.head(35).iterrows():L.append(f'|{r.feature}|{r.auc_oriented:.4f}|{r.direction}|{100*r.top10_head_rate:.2f}%|{r.lift_pt:+.2f}pt|')
    if coefs:
        cc=pd.DataFrame(coefs).groupby('feature').coef.agg(['mean','std']).reset_index();cc['absmean']=cc['mean'].abs();cc=cc.sort_values('absmean',ascending=False)
        L+=['','## ALL_SAFE_LINEAR coefficient stability','|feature|mean coef|sd|','|---|---:|---:|']
        for _,r in cc.head(30).iterrows():L.append(f'|{r.feature}|{r["mean"]:+.4f}|{r["std"]:.4f}|')
    SUM.write_text('\n'.join(L)+'\n',encoding='utf-8');print('\n'.join(L))

if __name__=='__main__':main()
