from __future__ import annotations
import json, warnings
import numpy as np
import pandas as pd
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier

from run_3head_funsite_broad50_wave6 import build_pre, load_canonical

warnings.filterwarnings("ignore")

WINDOWS=[14,21,28,42]
BANDS=[(1,4),(1,6),(1,8),(1,10),(1,12)]
ATTACK_Q=[.80,.85,.90,.925,.95,.975]
MODEL_Q=[.75,.80,.85,.90,.925,.95,.975]

ATTACK_SIGNALS=[
    'sig_vs2_全国2連対率',
    'sig_vs2_全国平均ST',
    'sig_attack_player_inner',
    'sig_rank_全国2連対率',
    'sig_rank_全国平均ST',
    'sig_b4_counter_margin',
    'sig_attack_motor_inner',
    'sig_attack_recent_inner',
    'sig_vs2_rn_trend_mean',
    'sig_vs2_rn_trend_win',
]
WEIGHT_VARIANTS=[
    {'name':'p25_st25','w':{'sig_vs2_全国2連対率':2.5,'sig_vs2_全国平均ST':2.5,'sig_attack_player_inner':.5,'sig_rank_全国2連対率':.5,'sig_rank_全国平均ST':.5}},
    {'name':'p30_st20','w':{'sig_vs2_全国2連対率':3.0,'sig_vs2_全国平均ST':2.0,'sig_attack_player_inner':.5,'sig_rank_全国2連対率':.5,'sig_rank_全国平均ST':.5}},
    {'name':'p20_st30','w':{'sig_vs2_全国2連対率':2.0,'sig_vs2_全国平均ST':3.0,'sig_attack_player_inner':.5,'sig_rank_全国2連対率':.5,'sig_rank_全国平均ST':.5}},
    {'name':'inner','w':{'sig_vs2_全国2連対率':2.5,'sig_vs2_全国平均ST':2.5,'sig_attack_player_inner':1.5,'sig_rank_全国2連対率':.5,'sig_rank_全国平均ST':.5}},
    {'name':'counter','w':{'sig_vs2_全国2連対率':2.5,'sig_vs2_全国平均ST':2.5,'sig_attack_player_inner':.5,'sig_rank_全国2連対率':.5,'sig_rank_全国平均ST':.5,'sig_b4_counter_margin':.5}},
    {'name':'motor','w':{'sig_vs2_全国2連対率':2.5,'sig_vs2_全国平均ST':2.5,'sig_attack_player_inner':.5,'sig_rank_全国2連対率':.5,'sig_rank_全国平均ST':.5,'sig_attack_motor_inner':.5}},
    {'name':'recent','w':{'sig_vs2_全国2連対率':2.5,'sig_vs2_全国平均ST':2.5,'sig_attack_player_inner':.5,'sig_rank_全国2連対率':.5,'sig_rank_全国平均ST':.5,'sig_attack_recent_inner':.5}},
    {'name':'trend','w':{'sig_vs2_全国2連対率':2.5,'sig_vs2_全国平均ST':2.5,'sig_attack_player_inner':.5,'sig_rank_全国2連対率':.5,'sig_rank_全国平均ST':.5,'sig_vs2_rn_trend_mean':.5,'sig_vs2_rn_trend_win':.5}},
]

def pct_ref(ref,x):
    a=np.asarray(ref,float)
    a=a[np.isfinite(a)]
    xx=np.asarray(x,float)
    out=np.full(len(xx),np.nan)
    if len(a)==0:return out
    a=np.sort(a)
    ok=np.isfinite(xx)
    out[ok]=np.searchsorted(a,xx[ok],side='right')/len(a)
    return out

def model_pair():
    logit=make_pipeline(
        SimpleImputer(strategy='median'),
        StandardScaler(),
        LogisticRegression(C=.08,class_weight='balanced',solver='liblinear',max_iter=2000,random_state=71)
    )
    hist=make_pipeline(
        SimpleImputer(strategy='median'),
        HistGradientBoostingClassifier(max_iter=140,max_leaf_nodes=9,l2_regularization=4,learning_rate=.04,random_state=71)
    )
    return logit,hist

def metric(mask,frame):
    m=np.asarray(mask,bool);y=frame.y.to_numpy(dtype=int);n=int(m.sum())
    return {'n':n,'hits':int(y[m].sum()) if n else 0,'rate':float(y[m].mean()) if n else None,
            'venues':int(frame.loc[m,'venue'].nunique()) if n else 0}

def weekly(mask,feb):
    out=[]
    day=feb.date.dt.day.to_numpy()
    for lo,hi in [(1,7),(8,14),(15,21),(22,28)]:
        m=np.asarray(mask,bool)&(day>=lo)&(day<=hi)
        z=metric(m,feb);z['week']=f'{lo:02d}-{hi:02d}';out.append(z)
    return out

def strict_stable(z):
    a,b=z['h1'],z['h2']
    if a['n']<20 or b['n']<20 or a['venues']<8 or b['venues']<8:return False
    if (a['rate'] or 0)<.50 or (b['rate'] or 0)<.50:return False
    ew=[w for w in z['weeks'] if w['n']>=5]
    return len(ew)>=3 and sum((w['rate'] or 0)>=.45 for w in ew)>=3

def near_stable(z):
    a,b=z['h1'],z['h2']
    return (a['n']>=25 and b['n']>=25 and a['venues']>=8 and b['venues']>=8 and
            (a['rate'] or 0)>=.47 and (b['rate'] or 0)>=.47)

def attack_percentiles(train,target):
    norm={}
    for c in ATTACK_SIGNALS:
        if c not in train.columns or c not in target.columns:continue
        ref=pd.to_numeric(train[c],errors='coerce').to_numpy(float)
        x=pd.to_numeric(target[c],errors='coerce').to_numpy(float)
        if np.isfinite(ref).sum()>=50:
            norm[c]=pct_ref(ref,x)
    out={}
    for v in WEIGHT_VARIANTS:
        cols=[];weights=[]
        for c,w in v['w'].items():
            if c in norm:
                cols.append(norm[c]);weights.append(float(w))
        if not cols:continue
        a=np.column_stack(cols);w=np.asarray(weights,float)
        valid=np.isfinite(a)
        num=np.nansum(a*w,axis=1)
        den=np.sum(valid*w,axis=1)
        out[v['name']]=np.divide(num,den,out=np.full(len(target),np.nan),where=den>0)
    return out

def curated_features(all_data):
    cols=[]
    for c in all_data.columns:
        if not c.startswith('sig_'):continue
        if not pd.api.types.is_numeric_dtype(all_data[c]):continue
        if all_data[c].notna().sum()<100:continue
        cols.append(c)
    return sorted(cols)

def walk_predictions(history,target,windows,feats):
    rows=[]
    target=target.sort_values(['date','rc']).copy()
    for day in sorted(target.date.dt.normalize().unique()):
        day=pd.Timestamp(day)
        today=target[target.date.dt.normalize()==day].copy()
        if len(today)==0:continue
        for window in windows:
            lo=day-pd.Timedelta(days=window)
            train=history[(history.date<day)&(history.date>=lo)].copy()
            if len(train)<500 or train.y.nunique()<2:continue
            logit,hist=model_pair()
            logit.fit(train[feats],train.y);hist.fit(train[feats],train.y)
            lp_train=logit.predict_proba(train[feats])[:,1]
            hp_train=hist.predict_proba(train[feats])[:,1]
            lp=pct_ref(lp_train,logit.predict_proba(today[feats])[:,1])
            hp=pct_ref(hp_train,hist.predict_proba(today[feats])[:,1])
            ap=attack_percentiles(train,today)
            base=today[['rc','date','venue','race_no','y']].copy()
            base['window']=window
            base['p_logit']=lp;base['p_hist']=hp
            base['p_mean']=(lp+hp)/2
            for name,val in ap.items():base[f'a_{name}']=val
            rows.append(base)
    return pd.concat(rows,ignore_index=True) if rows else pd.DataFrame()

def candidate_mask(pred,cand):
    rn=pd.to_numeric(pred.race_no,errors='coerce').to_numpy()
    lo,hi=cand['band'];m=(rn>=lo)&(rn<=hi)
    kind=cand['kind']
    if kind=='attack':
        m &= pd.to_numeric(pred[f"a_{cand['attack']}"],errors='coerce').to_numpy()>=cand['attack_q']
    elif kind=='model':
        m &= pd.to_numeric(pred[cand['model']],errors='coerce').to_numpy()>=cand['model_q']
    elif kind=='attack_model':
        m &= pd.to_numeric(pred[f"a_{cand['attack']}"],errors='coerce').to_numpy()>=cand['attack_q']
        m &= pd.to_numeric(pred[cand['model']],errors='coerce').to_numpy()>=cand['model_q']
    return m

def evaluate_candidate(pred,cand):
    sub=pred[pred.window==cand['window']].copy()
    m=candidate_mask(sub,cand)
    d=sub.date.dt.day.to_numpy()
    h1=metric(m&(d<=14),sub);h2=metric(m&(d>=15),sub)
    return {**cand,'h1':h1,'h2':h2,'weeks':weekly(m,sub)}

def candidate_universe(feb_pred):
    rows=[]
    for window in WINDOWS:
        sub=feb_pred[feb_pred.window==window]
        if len(sub)==0:continue
        attacks=[c[2:] for c in sub.columns if c.startswith('a_')]
        for band in BANDS:
            for a in attacks:
                for aq in ATTACK_Q:
                    rows.append({'kind':'attack','window':window,'band':list(band),'attack':a,'attack_q':aq})
            for model_name in ['p_logit','p_hist','p_mean']:
                for mq in MODEL_Q:
                    rows.append({'kind':'model','window':window,'band':list(band),'model':model_name,'model_q':mq})
            for a in attacks:
                for aq in ATTACK_Q:
                    for model_name in ['p_logit','p_hist','p_mean']:
                        for mq in [.80,.85,.90,.925,.95]:
                            rows.append({'kind':'attack_model','window':window,'band':list(band),'attack':a,'attack_q':aq,'model':model_name,'model_q':mq})
    return rows

def public(z):
    return {k:v for k,v in z.items() if not k.startswith('_')}

def select_feb(feb_pred):
    strict=[];near=[];total=0
    for cand in candidate_universe(feb_pred):
        total+=1
        z=evaluate_candidate(feb_pred,cand)
        if strict_stable(z):strict.append(z)
        if near_stable(z):near.append(z)
    strict=sorted(strict,key=lambda z:(z['h1']['n']+z['h2']['n'],min(z['h1']['rate'],z['h2']['rate'])),reverse=True)
    near=sorted(near,key=lambda z:(z['h1']['n']+z['h2']['n'],min(z['h1']['rate'],z['h2']['rate'])),reverse=True)
    volume=strict[0] if strict else None
    precision=max(strict,key=lambda z:(min(z['h1']['rate'],z['h2']['rate']),z['h1']['n']+z['h2']['n'])) if strict else None
    return total,strict,near,volume,precision

def march_eval(pred,cand):
    if cand is None:return None
    sub=pred[pred.window==cand['window']].copy()
    m=candidate_mask(sub,cand)
    sel=sub.loc[m].sort_values(['date','rc']).copy();n=len(sel);half=n//2
    return {'n':n,'hits':int(sel.y.sum()),'rate':float(sel.y.mean()) if n else None,
            'early_n':half,'early_hits':int(sel.iloc[:half].y.sum()),
            'late_n':n-half,'late_hits':int(sel.iloc[half:].y.sum()),
            'venue_count':int(sel.venue.nunique()) if n else 0}

def main():
    canon=load_canonical()
    jan,jres,ja=build_pre('2026-01-01','2026-01-31',True)
    feb,fres,fa=build_pre('2026-02-01','2026-02-28',True)
    mar,_,ma=build_pre('2026-03-01','2026-03-31',False)

    fc=canon[canon.date<'2026-03-01'].merge(fres[['rc','result_winner']],on='rc',how='inner')
    agree=float((pd.to_numeric(fc.settle__winner,errors='coerce')==fc.result_winner).mean()) if len(fc) else 0.0
    if len(fc)<3000 or agree<.995:raise RuntimeError(f'winner cross-check failed n={len(fc)} agreement={agree}')

    jan=jan.merge(jres[['rc','result_winner']],on='rc',how='inner')
    jan['y']=(jan.result_winner==3).astype(int)
    feb=canon[canon.date<'2026-03-01'][['rc','date','settle__winner']].merge(feb.drop(columns=['date']),on='rc',how='inner')
    mar=canon[canon.date>='2026-03-01'][['rc','date','settle__winner']].merge(mar.drop(columns=['date']),on='rc',how='inner')
    feb['y']=(pd.to_numeric(feb.settle__winner,errors='coerce')==3).astype(int)
    mar['y']=(pd.to_numeric(mar.settle__winner,errors='coerce')==3).astype(int)

    all_pre=pd.concat([jan,feb,mar],ignore_index=True,sort=False)
    feats=curated_features(all_pre)
    for fr in [jan,feb,mar]:
        for c in feats:
            if c not in fr.columns:fr[c]=np.nan

    # Phase 1: February walk-forward only. No March outcome is read for selection.
    feb_history=pd.concat([jan,feb],ignore_index=True,sort=False)
    feb_pred=walk_predictions(feb_history,feb,WINDOWS,feats)
    total,strict,near,volume,precision=select_feb(feb_pred)

    march_volume=None;march_precision=None
    replay_windows=sorted(set([z['window'] for z in [volume,precision] if z is not None]))
    march_pred_rows=[]
    if replay_windows:
        # Phase 2 begins only after February freeze. Earlier March labels are allowed only
        # for later-day refits, exactly as they would be known in live daily operation.
        full_history=pd.concat([jan,feb,mar],ignore_index=True,sort=False)
        march_pred=walk_predictions(full_history,mar,replay_windows,feats)
        march_volume=march_eval(march_pred,volume)
        march_precision=march_eval(march_pred,precision)

    out={
      'policy':{
        'feb_walk_forward_selection_only':True,'march_single_chronological_replay':True,
        'target_day_labels_in_training':False,'earlier_march_labels_only_for_later_march_refits':True,
        'september_outcomes_read':False,'production_v288_changed':False,'waku10_used':False,
        'recent_end_date_fail_closed':True
      },
      'cross_source_feb_winner_check':{'n':len(fc),'agreement':agree},
      'source_audit':{'jan':ja,'feb':fa,'mar':ma},
      'rows':{'jan':len(jan),'feb':len(feb),'mar':len(mar),'feb_prediction_rows':len(feb_pred)},
      'features':len(feats),'feature_names':feats,
      'candidate_count':total,'strict50_stable_count':len(strict),'near50_count':len(near),
      'strict50_frontier':[public(z) for z in strict[:30]],
      'near50_frontier':[public(z) for z in near[:30]],
      'volume_frozen':public(volume) if volume else None,
      'precision_frozen':public(precision) if precision else None,
      'march_volume':march_volume,'march_precision':march_precision
    }
    with open('research_3head_funsite_broad50_wave7_result.json','w') as f:
        json.dump(out,f,ensure_ascii=False,indent=2,default=str)
    print(json.dumps(out,ensure_ascii=False,indent=2,default=str))

if __name__=='__main__':
    main()
