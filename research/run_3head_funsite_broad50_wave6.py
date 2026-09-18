from __future__ import annotations
import csv, io, json, re, urllib.request, warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np
import pandas as pd
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import ExtraTreesClassifier, RandomForestClassifier, HistGradientBoostingClassifier, GradientBoostingClassifier
from sklearn.tree import DecisionTreeClassifier

from run_3head_funsite_broad50 import features, SRC, EX
from run_3head_funsite_broad50_wave2 import add_signals

warnings.filterwarnings("ignore")
BASE='https://boatracecsv.github.io/data'
BANDS=[(1,4),(1,6),(1,8),(1,10),(1,12)]
QS=[.70,.75,.80,.85,.875,.90,.925,.95,.965,.975,.985,.99]
MODEL_Q=[.70,.75,.80,.85,.90,.925,.95,.975]
MODEL_K=[2,3,4,5,6]
SIGNALS=[
    'sig_vs2_全国2連対率','sig_vs2_全国平均ST','sig_attack_player_inner',
    'sig_b1_pressure','sig_b4_counter_margin','sig_attack_motor_inner',
    'sig_attack_recent_inner','sig_rank_全国2連対率','sig_rank_全国平均ST',
    'sig_vs2_rn_trend_mean','sig_vs2_rn_trend_win','sig_vs2_rl_trend_mean',
    'sig_inner_rn_trend_mean','sig_inner_rl_trend_mean'
]

def fetch(kind,d):
    u=f'{BASE}/{kind}/{d:%Y/%m/%d}.csv'
    try:
        with urllib.request.urlopen(u,timeout=30) as r:
            return list(csv.DictReader(io.StringIO(r.read().decode('utf-8-sig'))))
    except Exception:
        return []

def ranks(s):
    return [int(x) for x in re.findall(r'(?<!\d)[1-6](?!\d)',s or '')]

def date_or_none(v):
    if not v:return None
    try:return pd.Timestamp(v).normalize()
    except:return None

def recent_extras(row,b,p,target):
    sess=[]
    violations=0
    for k in range(1,6):
        st=date_or_none(row.get(f'艇{b}_前{k}節_開始日'))
        en=date_or_none(row.get(f'艇{b}_前{k}節_終了日'))
        raw=(row.get(f'艇{b}_前{k}節_着順列') or '')
        if en is not None and en >= target:
            violations+=1
            continue
        rr=ranks(raw)
        if en is not None or rr:
            sess.append((k,st,en,rr))
    days=[(target-en).days for _,_,en,_ in sess if en is not None]
    recent=[x for k,_,_,rr in sess if k<=2 for x in rr]
    older=[x for k,_,_,rr in sess if k>=3 for x in rr]
    allr=[x for _,_,_,rr in sess for x in rr]
    def mean(v):return float(np.mean(v)) if v else np.nan
    def win(v):return float(np.mean(np.asarray(v)==1)) if v else np.nan
    recent_mean=mean(recent);older_mean=mean(older)
    recent_win=win(recent);older_win=win(older)
    return {
        f'{p}_days1':float(days[0]) if days else np.nan,
        f'{p}_days_mean':mean(days),
        f'{p}_valid_sessions':float(len(sess)),
        f'{p}_starts_safe':float(len(allr)),
        f'{p}_recent2_mean':recent_mean,
        f'{p}_recent2_win':recent_win,
        f'{p}_older3_mean':older_mean,
        f'{p}_older3_win':older_win,
        f'{p}_trend_mean':older_mean-recent_mean if np.isfinite(older_mean) and np.isfinite(recent_mean) else np.nan,
        f'{p}_trend_win':recent_win-older_win if np.isfinite(recent_win) and np.isfinite(older_win) else np.nan,
    },violations

def make_row(rc,rn,rl,target):
    total_bad=0
    for source in (rn,rl):
        for b in range(1,7):
            for k in range(1,6):
                en=date_or_none(source.get(f'艇{b}_前{k}節_終了日'))
                if en is not None and en >= target:
                    total_bad+=1
    if total_bad:
        return None,total_bad
    o=features(rc,rn,rl)
    for b in range(1,7):
        e,bad=recent_extras(rn,b,'rn',target);o.update({f'b{b}_{k}':v for k,v in e.items()});total_bad+=bad
        e,bad=recent_extras(rl,b,'rl',target);o.update({f'b{b}_{k}':v for k,v in e.items()});total_bad+=bad
    return o,total_bad

def add_extra_gaps(x):
    x=x.copy()
    extras=[
      'rn_days1','rn_days_mean','rn_valid_sessions','rn_starts_safe','rn_recent2_mean','rn_recent2_win',
      'rn_older3_mean','rn_older3_win','rn_trend_mean','rn_trend_win',
      'rl_days1','rl_days_mean','rl_valid_sessions','rl_starts_safe','rl_recent2_mean','rl_recent2_win',
      'rl_older3_mean','rl_older3_win','rl_trend_mean','rl_trend_win'
    ]
    high_good={'rn_recent2_win','rn_older3_win','rn_trend_mean','rn_trend_win',
               'rl_recent2_win','rl_older3_win','rl_trend_mean','rl_trend_win',
               'rn_valid_sessions','rn_starts_safe','rl_valid_sessions','rl_starts_safe'}
    low_good={'rn_recent2_mean','rn_older3_mean','rl_recent2_mean','rl_older3_mean'}
    for c in extras:
        cols=[f'b{i}_{c}' for i in range(1,7)]
        if not all(z in x.columns for z in cols):continue
        vals=x[cols].apply(pd.to_numeric,errors='coerce')
        if c in high_good:sign=1.0
        elif c in low_good:sign=-1.0
        else:sign=1.0
        b3=vals[f'b3_{c}']
        x[f'sig_vs2_{c}']=sign*(b3-vals[f'b2_{c}'])
        x[f'sig_vs1_{c}']=sign*(b3-vals[f'b1_{c}'])
        x[f'sig_vs4_{c}']=sign*(b3-vals[f'b4_{c}'])
        x[f'sig_inner_{c}']=sign*(b3-vals[[f'b1_{c}',f'b2_{c}']].mean(axis=1))
    return x

def load_canonical():
    use=['date','race_code_norm','settle__usable','closing_odds__ok','settle__winner']
    b=pd.read_csv(SRC,usecols=use,low_memory=False)
    b['date']=pd.to_datetime(b.date,errors='coerce')
    b['rc']=pd.to_numeric(b.race_code_norm,errors='coerce').astype('Int64')
    b=b[(b.date>='2026-02-01')&(b.date<'2026-04-01')&
        (b.settle__usable==1)&(b.closing_odds__ok==1)&(~b.rc.isin(EX))].copy()
    return b[['rc','date','settle__winner']]

def build_pre(start,end,need_results=False):
    rows=[];res=[];bad_races=0;bad_sessions=0;days_ok=0
    days=list(pd.date_range(start,end))
    kinds=['programs/race_cards','programs/recent_national','programs/recent_local']
    if need_results:kinds.append('results/realtime')
    cache={}
    with ThreadPoolExecutor(max_workers=16) as ex:
        fut={ex.submit(fetch,k,day.date()):(day,k) for day in days for k in kinds}
        for f in as_completed(fut):
            day,k=fut[f]
            try:cache[(day,k)]=f.result()
            except Exception:cache[(day,k)]=[]
    for day in days:
        parts={k:cache.get((day,k),[]) for k in ['programs/race_cards','programs/recent_national','programs/recent_local']}
        if not all(parts.values()):continue
        days_ok+=1
        maps={k:{str(r.get('レースコード','')):r for r in v} for k,v in parts.items()}
        keys=set.intersection(*[set(m) for m in maps.values()])
        for rc_code in keys:
            if not rc_code.isdigit():continue
            o,bad=make_row(maps['programs/race_cards'][rc_code],maps['programs/recent_national'][rc_code],maps['programs/recent_local'][rc_code],pd.Timestamp(day.date()))
            if o is None:
                bad_races+=1;bad_sessions+=bad;continue
            o['date']=pd.Timestamp(day.date())
            rows.append(o)
        if need_results:
            for rr in cache.get((day,'results/realtime'),[]):
                rc_code=str(rr.get('レースコード',''))
                w=str(rr.get('1着_艇番','')).strip()
                if rc_code.isdigit() and w in {'1','2','3','4','5','6'}:
                    res.append({'rc':int(rc_code),'result_winner':int(w),'result_date':pd.Timestamp(day.date())})
    x=pd.DataFrame(rows)
    if len(x):
        x=x.drop_duplicates('rc')
        x=add_signals(x)
        x=add_extra_gaps(x)
    r=pd.DataFrame(res).drop_duplicates('rc') if res else pd.DataFrame(columns=['rc','result_winner','result_date'])
    return x,r,{'days_ok':days_ok,'bad_races':bad_races,'bad_sessions':bad_sessions}

def model(name):
    if name=='logit':
        return make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),
          LogisticRegression(C=.08,class_weight='balanced',solver='liblinear',max_iter=2500,random_state=61))
    if name=='extra':
        return make_pipeline(SimpleImputer(strategy='median'),
          ExtraTreesClassifier(n_estimators=550,min_samples_leaf=10,max_features=.75,class_weight='balanced',random_state=61,n_jobs=-1))
    if name=='rf':
        return make_pipeline(SimpleImputer(strategy='median'),
          RandomForestClassifier(n_estimators=450,min_samples_leaf=12,max_features=.6,class_weight='balanced',random_state=61,n_jobs=-1))
    if name=='hist':
        return make_pipeline(SimpleImputer(strategy='median'),
          HistGradientBoostingClassifier(max_iter=260,max_leaf_nodes=11,l2_regularization=3,learning_rate=.04,random_state=61))
    if name=='tree':
        return make_pipeline(SimpleImputer(strategy='median'),
          DecisionTreeClassifier(max_depth=3,min_samples_leaf=30,class_weight='balanced',random_state=61))
    return make_pipeline(SimpleImputer(strategy='median'),
      GradientBoostingClassifier(n_estimators=170,learning_rate=.035,max_depth=2,min_samples_leaf=25,random_state=61))

MODEL_NAMES=['logit','extra','rf','hist','tree','gb']

def numeric_features(d):
    ex={'rc','venue','date','settle__winner','result_winner','result_date','y'}
    return [c for c in d.columns if c not in ex and pd.api.types.is_numeric_dtype(d[c]) and d[c].notna().sum()>=50]

def band_mask(frame,band):
    r=pd.to_numeric(frame.race_no,errors='coerce').to_numpy()
    return (r>=band[0])&(r<=band[1])

def pct_ref(ref,x):
    a=np.asarray(ref,float);a=a[np.isfinite(a)];a=np.sort(a)
    xx=np.asarray(x,float)
    out=np.searchsorted(a,xx,side='right')/max(1,len(a))
    out[~np.isfinite(xx)]=np.nan
    return out

def metric(mask,frame):
    m=np.asarray(mask,bool);y=frame.y.to_numpy(dtype=int);n=int(m.sum())
    return {'n':n,'hits':int(y[m].sum()) if n else 0,'rate':float(y[m].mean()) if n else None,
            'venues':int(frame.loc[m,'venue'].nunique()) if n else 0}

def weekly_metrics(mask,feb):
    m=np.asarray(mask,bool);out=[]
    for lo,hi in [(1,7),(8,14),(15,21),(22,28)]:
        w=(feb.date.dt.day>=lo)&(feb.date.dt.day<=hi)
        mm=m&w.to_numpy()
        z=metric(mm,feb);z['week']=f'{lo:02d}-{hi:02d}';out.append(z)
    return out

def stability(z):
    if z['h1']['n']<20 or z['h2']['n']<20:return False
    if z['h1']['venues']<8 or z['h2']['venues']<8:return False
    if (z['h1']['rate'] or 0)<.50 or (z['h2']['rate'] or 0)<.50:return False
    eligible=[w for w in z['weeks'] if w['n']>=5]
    if len(eligible)<3:return False
    return sum((w['rate'] or 0)>=.45 for w in eligible)>=3

def near_stability(z):
    if z['h1']['n']<25 or z['h2']['n']<25:return False
    if z['h1']['venues']<8 or z['h2']['venues']<8:return False
    if (z['h1']['rate'] or 0)<.47 or (z['h2']['rate'] or 0)<.47:return False
    return True

def score_weights(used):
    support=[
      {},
      {'sig_b1_pressure':.5},
      {'sig_b4_counter_margin':.5},
      {'sig_attack_motor_inner':.5},
      {'sig_attack_recent_inner':.5},
      {'sig_vs2_rn_trend_mean':.5},
      {'sig_vs2_rn_trend_win':.5},
      {'sig_vs2_rl_trend_mean':.5},
      {'sig_inner_rn_trend_mean':.5},
      {'sig_b1_pressure':.5,'sig_b4_counter_margin':.5},
      {'sig_attack_motor_inner':.5,'sig_vs2_rn_trend_mean':.5},
    ]
    out=[]
    for a in [1.5,2.0,2.5,3.0]:
      for b in [1.5,2.0,2.5,3.0]:
       for c in [.5,1.0,1.5]:
        for s in support:
          d={'sig_vs2_全国2連対率':a,'sig_vs2_全国平均ST':b,'sig_attack_player_inner':c,
             'sig_rank_全国2連対率':.5,'sig_rank_全国平均ST':.5}
          d.update(s);out.append({k:float(d.get(k,0)) for k in used})
    return out

def signal_context(jan,frames,band):
    bm=band_mask(jan,band)
    used=[];refs={}
    for c in SIGNALS:
        if c not in jan.columns:continue
        a=pd.to_numeric(jan.loc[bm,c],errors='coerce').to_numpy(float)
        a=a[np.isfinite(a)]
        if len(a)<50:continue
        used.append(c);refs[c]=np.sort(a)
    mats={}
    for key,fr in frames.items():
        cols=[]
        for c in used:
            cols.append(pct_ref(refs[c],pd.to_numeric(fr[c],errors='coerce').to_numpy(float)))
        mats[key]=np.column_stack(cols)
    return used,mats

def weighted_score(mat,w):
    valid=np.isfinite(mat)
    num=np.nansum(mat*w,axis=1);den=np.sum(valid*w,axis=1)
    return np.divide(num,den,out=np.full(len(mat),np.nan),where=den>0)

def model_context(jan,frames,band,feats):
    train=jan.loc[band_mask(jan,band)].copy()
    stacks={k:[] for k in frames}
    for name in MODEL_NAMES:
        m=model(name);m.fit(train[feats],train.y)
        ref=m.predict_proba(train[feats])[:,1]
        for key,fr in frames.items():
            stacks[key].append(pct_ref(ref,m.predict_proba(fr[feats])[:,1]))
    return {k:np.column_stack(v) for k,v in stacks.items()}

def public(z):
    return {k:v for k,v in z.items() if not k.startswith('_')}

def candidate_key(z):
    return (z['h1']['n']+z['h2']['n'],min(z['h1']['rate'],z['h2']['rate']),sum(w['rate'] or 0 for w in z['weeks']))

def main():
    canon=load_canonical()
    jan,jres,ja=build_pre('2026-01-01','2026-01-31',True)
    feb,fres,fa=build_pre('2026-02-01','2026-02-28',True)
    mar,_,ma=build_pre('2026-03-01','2026-03-31',False)

    # Cross-source February winner validation.
    fc=canon[canon.date<'2026-03-01'].merge(fres[['rc','result_winner']],on='rc',how='inner')
    agree=float((pd.to_numeric(fc.settle__winner,errors='coerce')==fc.result_winner).mean()) if len(fc) else 0.0
    if len(fc)<3000 or agree<.995:
        raise RuntimeError(f'February results/realtime winner cross-check failed: n={len(fc)} agreement={agree}')

    jan=jan.merge(jres[['rc','result_winner']],on='rc',how='inner')
    jan['y']=(jan.result_winner==3).astype(int)
    feb=canon[canon.date<'2026-03-01'][['rc','date','settle__winner']].merge(feb.drop(columns=['date']),on='rc',how='inner')
    mar=canon[canon.date>='2026-03-01'][['rc','date','settle__winner']].merge(mar.drop(columns=['date']),on='rc',how='inner')
    feb['y']=(pd.to_numeric(feb.settle__winner,errors='coerce')==3).astype(int)
    mar['y']=(pd.to_numeric(mar.settle__winner,errors='coerce')==3).astype(int)

    feats=numeric_features(pd.concat([jan,feb,mar],ignore_index=True,sort=False))
    # Align feature columns.
    for fr in [jan,feb,mar]:
        for c in feats:
            if c not in fr.columns:fr[c]=np.nan

    h1=(feb.date.dt.day<=14).to_numpy();h2=~h1
    frames={'feb':feb,'mar':mar}
    rows=[]
    candidate_count=0

    def keep_half(h1m,h2m):
        strict_half=(h1m['n']>=20 and h2m['n']>=20 and h1m['venues']>=8 and h2m['venues']>=8 and
                     (h1m['rate'] or 0)>=.50 and (h2m['rate'] or 0)>=.50)
        near_half=(h1m['n']>=25 and h2m['n']>=25 and h1m['venues']>=8 and h2m['venues']>=8 and
                   (h1m['rate'] or 0)>=.47 and (h2m['rate'] or 0)>=.47)
        return strict_half or near_half

    for band in BANDS:
        if int(band_mask(jan,band).sum())<300:continue
        used,mats=signal_context(jan,frames,band)
        stacks=model_context(jan,{'jan':jan,'feb':feb,'mar':mar},band,feats)
        bf=band_mask(feb,band);bm=band_mask(mar,band)

        # Model-only percentile consensus.
        for q in MODEL_Q:
            for k in MODEL_K:
                mf=bf&((stacks['feb']>=q).sum(axis=1)>=k)
                mm=bm&((stacks['mar']>=q).sum(axis=1)>=k)
                candidate_count+=1
                h1m=metric(mf&h1,feb);h2m=metric(mf&h2,feb)
                if keep_half(h1m,h2m):
                    z={'kind':'jan_model_consensus','band':list(band),'q':q,'k':k,
                       'h1':h1m,'h2':h2m,'weeks':weekly_metrics(mf,feb),'_mar':mm}
                    rows.append(z)

        # Mean model-percentile score.
        meanf=np.nanmean(stacks['feb'],axis=1);meanm=np.nanmean(stacks['mar'],axis=1)
        meanj=np.nanmean(stacks['jan'],axis=1)
        ref=meanj[band_mask(jan,band)&np.isfinite(meanj)]
        for q in QS:
            th=float(np.quantile(ref,q))
            mf=bf&np.isfinite(meanf)&(meanf>=th);mm=bm&np.isfinite(meanm)&(meanm>=th)
            candidate_count+=1
            h1m=metric(mf&h1,feb);h2m=metric(mf&h2,feb)
            if keep_half(h1m,h2m):
                z={'kind':'jan_model_mean','band':list(band),'q':q,'threshold':th,
                   'h1':h1m,'h2':h2m,'weeks':weekly_metrics(mf,feb),'_mar':mm}
                rows.append(z)

        # Opponent-specific continuous score and score+model.
        wgrid=score_weights(used)
        sjmat=signal_context(jan,{'jan':jan},band)[1]['jan']
        for weights in wgrid:
            w=np.array([weights[c] for c in used],float)
            sj=weighted_score(sjmat,w);sf=weighted_score(mats['feb'],w);sm=weighted_score(mats['mar'],w)
            ref=sj[band_mask(jan,band)&np.isfinite(sj)]
            if len(ref)<100:continue
            for q in [.80,.85,.90,.925,.95,.965,.975,.985,.99]:
                th=float(np.quantile(ref,q))
                basef=bf&np.isfinite(sf)&(sf>=th);basem=bm&np.isfinite(sm)&(sm>=th)
                candidate_count+=1
                h1m=metric(basef&h1,feb);h2m=metric(basef&h2,feb)
                if keep_half(h1m,h2m):
                    z={'kind':'jan_attack_score','band':list(band),'q':q,'threshold':th,'weights':weights,
                       'h1':h1m,'h2':h2m,'weeks':weekly_metrics(basef,feb),'_mar':basem}
                    rows.append(z)
                for mq,mk in [(.70,2),(.75,2),(.75,3),(.80,2),(.80,3),(.85,2),(.85,3)]:
                    mf=basef&((stacks['feb']>=mq).sum(axis=1)>=mk)
                    mm=basem&((stacks['mar']>=mq).sum(axis=1)>=mk)
                    candidate_count+=1
                    h1m=metric(mf&h1,feb);h2m=metric(mf&h2,feb)
                    if keep_half(h1m,h2m):
                        zz={'kind':'jan_attack_model','band':list(band),'q':q,'threshold':th,'weights':weights,
                            'model_q':mq,'model_k':mk,
                            'h1':h1m,'h2':h2m,'weeks':weekly_metrics(mf,feb),'_mar':mm}
                        rows.append(zz)

    stable=[z for z in rows if stability(z)]
    near=[z for z in rows if near_stability(z)]
    stable=sorted(stable,key=candidate_key,reverse=True)
    near=sorted(near,key=candidate_key,reverse=True)
    volume=stable[0] if stable else None
    precision=max(stable,key=lambda z:(min(z['h1']['rate'],z['h2']['rate']),z['h1']['n']+z['h2']['n'])) if stable else None

    def march(z):
        if z is None:return None
        sel=mar.loc[z['_mar']].sort_values(['date','rc']).copy();n=len(sel);half=n//2
        return {'n':n,'hits':int(sel.y.sum()),'rate':float(sel.y.mean()) if n else None,
                'early_n':half,'early_hits':int(sel.iloc[:half].y.sum()),
                'late_n':n-half,'late_hits':int(sel.iloc[half:].y.sum()),
                'venue_count':int(sel.venue.nunique()) if n else 0}

    out={
      'policy':{
        'january_training_only':True,'february_selection_only':True,'march_one_shot':True,
        'september_outcomes_read':False,'production_v288_changed':False,
        'recent_end_date_fail_closed':True,'waku10_used':False
      },
      'cross_source_feb_winner_check':{'n':len(fc),'agreement':agree},
      'source_audit':{'jan':ja,'feb':fa,'mar':ma},
      'rows':{'jan_train':len(jan),'feb_select':len(feb),'march_test':len(mar)},
      'features':len(feats),'candidate_count':candidate_count,'retained_half_stable_candidates':len(rows),
      'strict50_stable_count':len(stable),'near50_count':len(near),
      'strict50_frontier':[public(z) for z in stable[:30]],
      'near50_frontier':[public(z) for z in near[:30]],
      'volume_frozen':public(volume) if volume else None,
      'precision_frozen':public(precision) if precision else None,
      'march_volume':march(volume),
      'march_precision':march(precision)
    }
    with open('research_3head_funsite_broad50_wave6_result.json','w') as f:
        json.dump(out,f,ensure_ascii=False,indent=2,default=str)
    print(json.dumps(out,ensure_ascii=False,indent=2,default=str))

if __name__=='__main__':
    main()
