from __future__ import annotations
import json, re, warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np
import pandas as pd
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier

from run_3head_funsite_broad50_wave6 import (
    fetch, make_row, add_signals, add_extra_gaps, load_canonical
)

warnings.filterwarnings("ignore")

WINDOWS=[21,42]
BANDS=[(1,6),(1,8),(1,10),(1,12)]
QS=[.75,.80,.85,.875,.90,.925,.95,.975]
DISCOVERY_SUPPORTS=[15,20,30,50,75,100]
FEB_SUPPORTS=[20,30,50,75,100]

CLASS_SCORE={'B2':0.0,'B1':1.0,'A2':2.0,'A1':3.0}
VENUE_BRANCH={
 '01':'群馬','02':'埼玉','03':'東京','04':'東京','05':'東京','06':'静岡',
 '07':'愛知','08':'愛知','09':'三重','10':'福井','11':'滋賀','12':'大阪',
 '13':'兵庫','14':'徳島','15':'香川','16':'岡山','17':'広島','18':'山口',
 '19':'山口','20':'福岡','21':'福岡','22':'福岡','23':'佐賀','24':'長崎'
}

NEW_BASE_FIELDS=[
 'age','period','class_score','prize_excl','motor_flag','boat_flag','home_branch',
 'has_other_race','second_appearance','other_race_delta',
 'rn_last_starts','rn_last_mean','rn_last_win','rn_last_top2','rn_last_top3',
 'rn_second_starts','rn_second_mean','rn_second_win','rn_second_top2','rn_second_top3',
 'rn_last_grade','rn_mean_grade','rn_max_grade','rn_grade_win','rn_grade_top2','rn_grade_top3',
 'rn_unique_venues','rn_same_current_venue_share',
 'rl_last_starts','rl_last_mean','rl_last_win','rl_last_top2','rl_last_top3',
 'rl_second_starts','rl_second_mean','rl_second_win','rl_second_top2','rl_second_top3',
 'rl_last_grade','rl_mean_grade','rl_max_grade','rl_grade_win','rl_grade_top2','rl_grade_top3'
]

def num(v):
    try:return float(v)
    except:return np.nan

def int_from(v):
    m=re.search(r'\d+',str(v or ''))
    return float(m.group()) if m else np.nan

def ranks(s):
    return [int(x) for x in re.findall(r'(?<!\d)[1-6](?!\d)',str(s or ''))]

def grade_score(v):
    s=str(v or '').upper().replace('Ⅰ','I').replace('Ⅱ','II').replace('Ⅲ','III')
    if 'ＳＧ' in s or 'SG' in s:return 4.0
    if 'ＧI' in s or 'GI' in s or 'G1' in s:return 3.0
    if 'ＧII' in s or 'GII' in s or 'G2' in s:return 2.0
    if 'ＧIII' in s or 'GIII' in s or 'G3' in s:return 1.0
    if '一般' in s:return 0.0
    return np.nan

def stats(rr):
    a=np.asarray(rr,float)
    return {
      'starts':float(len(a)),
      'mean':float(a.mean()) if len(a) else np.nan,
      'win':float((a==1).mean()) if len(a) else np.nan,
      'top2':float((a<=2).mean()) if len(a) else np.nan,
      'top3':float((a<=3).mean()) if len(a) else np.nan
    }

def recent_detail(row,b,p,target,current_venue):
    sess=[]
    for k in range(1,6):
        end=row.get(f'艇{b}_前{k}節_終了日')
        en=pd.to_datetime(end,errors='coerce')
        if pd.notna(en) and en.normalize()>=target.normalize():
            continue
        rr=ranks(row.get(f'艇{b}_前{k}節_着順列'))
        g=grade_score(row.get(f'艇{b}_前{k}節_グレード'))
        venue=str(row.get(f'艇{b}_前{k}節_場コード','')).zfill(2)
        if rr or pd.notna(en):
            sess.append({'k':k,'r':rr,'g':g,'venue':venue})
    out={}
    for idx,label in [(0,'last'),(1,'second')]:
        s=stats(sess[idx]['r']) if len(sess)>idx else stats([])
        for key,val in s.items():out[f'{p}_{label}_{key}']=val
    grades=[x['g'] for x in sess if np.isfinite(x['g'])]
    out[f'{p}_last_grade']=sess[0]['g'] if sess and np.isfinite(sess[0]['g']) else np.nan
    out[f'{p}_mean_grade']=float(np.mean(grades)) if grades else np.nan
    out[f'{p}_max_grade']=float(np.max(grades)) if grades else np.nan

    wr=[];ww=[]
    for s in sess:
        if not s['r']:continue
        w=1.0+(0.30*s['g'] if np.isfinite(s['g']) else 0.0)
        for r in s['r']:
            wr.append(r);ww.append(w)
    if wr:
        a=np.asarray(wr,float);w=np.asarray(ww,float)
        out[f'{p}_grade_win']=float(np.average(a==1,weights=w))
        out[f'{p}_grade_top2']=float(np.average(a<=2,weights=w))
        out[f'{p}_grade_top3']=float(np.average(a<=3,weights=w))
    else:
        out[f'{p}_grade_win']=out[f'{p}_grade_top2']=out[f'{p}_grade_top3']=np.nan

    if p=='rn':
        venues=[x['venue'] for x in sess if x['venue'] and x['venue']!='00']
        out['rn_unique_venues']=float(len(set(venues))) if venues else np.nan
        out['rn_same_current_venue_share']=float(np.mean([v==current_venue for v in venues])) if venues else np.nan
    return out

def extra_row(rc,rn,rl,target):
    out={}
    venue=str(rc.get('レース場コード','')).zfill(2)
    race_no=int(re.sub(r'\D','',str(rc.get('レース回','0'))) or 0)
    home=VENUE_BRANCH.get(venue,'')
    for b in range(1,7):
        cls=str(rc.get(f'艇{b}_級別','')).strip()
        branch=str(rc.get(f'艇{b}_支部','')).strip()
        hayami=int_from(rc.get(f'艇{b}_早見'))
        prize=str(rc.get(f'艇{b}_賞除','')).strip()
        vals={
          'age':num(rc.get(f'艇{b}_年齢')),
          'period':int_from(rc.get(f'艇{b}_期別')),
          'class_score':CLASS_SCORE.get(cls,np.nan),
          'prize_excl':1.0 if prize not in {'','0','0.0','nan','None'} else 0.0,
          'motor_flag':num(rc.get(f'艇{b}_モーターフラグ')),
          'boat_flag':num(rc.get(f'艇{b}_ボートフラグ')),
          'home_branch':1.0 if home and branch==home else 0.0,
          'has_other_race':1.0 if np.isfinite(hayami) else 0.0,
          'second_appearance':1.0 if np.isfinite(hayami) and hayami<race_no else 0.0,
          'other_race_delta':float(hayami-race_no) if np.isfinite(hayami) else np.nan,
        }
        vals.update(recent_detail(rn,b,'rn',target,venue))
        vals.update(recent_detail(rl,b,'rl',target,venue))
        for k,v in vals.items():out[f'new_b{b}_{k}']=v
    return out

def add_new_gaps(x):
    x=x.copy()
    for feat in NEW_BASE_FIELDS:
        cols=[f'new_b{i}_{feat}' for i in range(1,7)]
        if not all(c in x.columns for c in cols):continue
        vals=x[cols].apply(pd.to_numeric,errors='coerce')
        b3=vals[f'new_b3_{feat}']
        for opp in [1,2,4]:
            x[f'new_gap{opp}_{feat}']=b3-vals[f'new_b{opp}_{feat}']
        x[f'new_inner_gap_{feat}']=b3-vals[[f'new_b1_{feat}',f'new_b2_{feat}']].mean(axis=1)
        x[f'new_all_gap_{feat}']=b3-vals[[f'new_b1_{feat}',f'new_b2_{feat}',f'new_b4_{feat}',f'new_b5_{feat}',f'new_b6_{feat}']].mean(axis=1)
    return x

def build_pre_enhanced(start,end,need_results=False):
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
        for code in keys:
            if not code.isdigit():continue
            rc=maps['programs/race_cards'][code];rn=maps['programs/recent_national'][code];rl=maps['programs/recent_local'][code]
            o,bad=make_row(rc,rn,rl,pd.Timestamp(day.date()))
            if o is None:
                bad_races+=1;bad_sessions+=bad;continue
            o.update(extra_row(rc,rn,rl,pd.Timestamp(day.date())))
            o['date']=pd.Timestamp(day.date());rows.append(o)
        if need_results:
            for rr in cache.get((day,'results/realtime'),[]):
                code=str(rr.get('レースコード',''));w=str(rr.get('1着_艇番','')).strip()
                if code.isdigit() and w in {'1','2','3','4','5','6'}:
                    res.append({'rc':int(code),'result_winner':int(w),'result_date':pd.Timestamp(day.date())})
    x=pd.DataFrame(rows)
    if len(x):
        x=x.drop_duplicates('rc')
        x=add_signals(x)
        x=add_extra_gaps(x)
        x=add_new_gaps(x)
    r=pd.DataFrame(res).drop_duplicates('rc') if res else pd.DataFrame(columns=['rc','result_winner','result_date'])
    return x,r,{'days_ok':days_ok,'bad_races':bad_races,'bad_sessions':bad_sessions}

def model_pair():
    logit=make_pipeline(
      SimpleImputer(strategy='median'),StandardScaler(),
      LogisticRegression(C=.08,class_weight='balanced',solver='liblinear',max_iter=1800,random_state=161)
    )
    hist=make_pipeline(
      SimpleImputer(strategy='median'),
      HistGradientBoostingClassifier(max_iter=110,max_leaf_nodes=9,l2_regularization=4,
                                     learning_rate=.045,random_state=161)
    )
    return logit,hist

def pct_ref(ref,x):
    a=np.asarray(ref,float);a=a[np.isfinite(a)];a=np.sort(a)
    xx=np.asarray(x,float);out=np.full(len(xx),np.nan)
    if len(a)==0:return out
    ok=np.isfinite(xx);out[ok]=np.searchsorted(a,xx[ok],side='right')/len(a)
    return out

def choose_features(all_data):
    base=[c for c in all_data.columns if c.startswith('sig_') and
          pd.api.types.is_numeric_dtype(all_data[c]) and all_data[c].notna().sum()>=200]
    new=[c for c in all_data.columns if c.startswith('new_') and
         pd.api.types.is_numeric_dtype(all_data[c]) and all_data[c].notna().sum()>=200]
    return sorted(base),sorted(set(base+new)),sorted(new)

def walk_predictions(history,target,feature_sets):
    rows=[]
    target=target.sort_values(['date','rc']).copy()
    for dayv in sorted(target.date.dt.normalize().unique()):
        day=pd.Timestamp(dayv);today=target[target.date.dt.normalize()==day].copy()
        for window in WINDOWS:
            tr=history[(history.date<day)&(history.date>=day-pd.Timedelta(days=window))].copy()
            if len(tr)<500 or tr.y.nunique()<2:continue
            for family,feats in feature_sets.items():
                if len(feats)<5:continue
                logit,hist=model_pair()
                logit.fit(tr[feats],tr.y);hist.fit(tr[feats],tr.y)
                ltr=logit.predict_proba(tr[feats])[:,1];htr=hist.predict_proba(tr[feats])[:,1]
                lp=pct_ref(ltr,logit.predict_proba(today[feats])[:,1])
                hp=pct_ref(htr,hist.predict_proba(today[feats])[:,1])
                z=today[['rc','date','venue','race_no','y']].copy()
                z['window']=window;z['family']=family
                z['p_logit']=lp;z['p_hist']=hp;z['p_mean']=(lp+hp)/2
                rows.append(z)
    return pd.concat(rows,ignore_index=True) if rows else pd.DataFrame()

def metric(mask,frame):
    m=np.asarray(mask,bool);y=frame.y.to_numpy(dtype=int);n=int(m.sum())
    return {'n':n,'hits':int(y[m].sum()) if n else 0,
            'rate':float(y[m].mean()) if n else None,
            'venues':int(frame.loc[m,'venue'].nunique()) if n else 0}

def eval_candidate(pred,c,feb=False):
    sub=pred[(pred.family==c['family'])&(pred.window==c['window'])].copy()
    rn=pd.to_numeric(sub.race_no,errors='coerce').to_numpy()
    sc=pd.to_numeric(sub[c['model']],errors='coerce').to_numpy(float)
    lo,hi=c['band'];m=(rn>=lo)&(rn<=hi)&np.isfinite(sc)&(sc>=c['q'])
    d=sub.date.dt.day.to_numpy()
    if feb:
        m1=m&(d<=14);m2=m&(d>=15)
    else:
        m1=m&(d<=15);m2=m&(d>=16)
    z=dict(c);z['h1']=metric(m1,sub);z['h2']=metric(m2,sub)
    return z

def universe(family):
    out=[]
    for w in WINDOWS:
      for band in BANDS:
       for model in ['p_logit','p_hist','p_mean']:
        for q in QS:
         out.append({'family':family,'window':w,'band':list(band),'model':model,'q':q})
    return out

def worst(z):
    if z['h1']['rate'] is None or z['h2']['rate'] is None:return -1
    return min(z['h1']['rate'],z['h2']['rate'])

def combined(z):
    n=z['h1']['n']+z['h2']['n'];h=z['h1']['hits']+z['h2']['hits']
    return h/n if n else -1

def freeze(pre_preds,family):
    rows=[]
    for c in universe(family):
        ms={m:eval_candidate(pre_preds[m],c,False) for m in ['nov','dec','jan']}
        rates=[ms[m][h]['rate'] for m in ms for h in ['h1','h2']]
        if any(r is None for r in rates):continue
        rows.append({'candidate':c,'months':ms,'persistent_worst':min(rates),
                     'persistent_combined':sum(ms[m][h]['hits'] for m in ms for h in ['h1','h2'])/
                                           sum(ms[m][h]['n'] for m in ms for h in ['h1','h2'])})
    frozen=[];strata={}
    for mn in DISCOVERY_SUPPORTS:
        pool=[]
        for z in rows:
            ok=all(z['months'][m][h]['n']>=mn and z['months'][m][h]['venues']>=8
                   for m in ['nov','dec','jan'] for h in ['h1','h2'])
            if ok:pool.append(z)
        pool=sorted(pool,key=lambda z:(z['persistent_worst'],z['persistent_combined'],
                                       sum(z['months'][m][h]['n'] for m in ['nov','dec','jan'] for h in ['h1','h2'])),reverse=True)
        strata[str(mn)]={'candidate_count':len(pool),'best':pool[0] if pool else None}
        frozen.extend(pool[:20])
    out=[];seen=set()
    for z in frozen:
        c=z['candidate'];k=(c['window'],tuple(c['band']),c['model'],c['q'])
        if k not in seen:seen.add(k);out.append(z)
    return out,strata

def feb_frontier(pred,frozen,family):
    evals=[]
    for z in frozen:
        e=eval_candidate(pred,{**z['candidate'],'family':family},True)
        evals.append({'pre_feb':z,'feb':e})
    out={}
    for mn in FEB_SUPPORTS:
        pool=[z for z in evals if z['feb']['h1']['n']>=mn and z['feb']['h2']['n']>=mn and
              z['feb']['h1']['venues']>=8 and z['feb']['h2']['venues']>=8]
        if pool:
            best=max(pool,key=lambda z:(worst(z['feb']),combined(z['feb']),
                                        z['feb']['h1']['n']+z['feb']['h2']['n']))
            a=best['feb']['h1'];b=best['feb']['h2'];n=a['n']+b['n'];h=a['hits']+b['hits']
            best={**best,'feb_worst_half_rate':min(a['rate'],b['rate']),
                  'feb_combined_n':n,'feb_combined_hits':h,'feb_combined_rate':h/n}
        else:best=None
        out[str(mn)]={'candidate_count':len(pool),'best':best}
    return out,evals

def main():
    canon=load_canonical()
    octo,ores,oa=build_pre_enhanced('2025-10-01','2025-10-31',True)
    nov,nres,na=build_pre_enhanced('2025-11-01','2025-11-30',True)
    dec,dres,da=build_pre_enhanced('2025-12-01','2025-12-31',True)
    jan,jres,ja=build_pre_enhanced('2026-01-01','2026-01-31',True)
    feb,fres,fa=build_pre_enhanced('2026-02-01','2026-02-28',True)

    fc=canon[canon.date<'2026-03-01'].merge(fres[['rc','result_winner']],on='rc',how='inner')
    agree=float((pd.to_numeric(fc.settle__winner,errors='coerce')==fc.result_winner).mean()) if len(fc) else 0.0
    if len(fc)<3000 or agree<.995:raise RuntimeError(f'winner cross-check failed n={len(fc)} agreement={agree}')

    frames=[]
    for x,r in [(octo,ores),(nov,nres),(dec,dres),(jan,jres)]:
        y=x.merge(r[['rc','result_winner']],on='rc',how='inner')
        y['y']=(y.result_winner==3).astype(int);frames.append(y)
    octo,nov,dec,jan=frames
    feb=canon[canon.date<'2026-03-01'][['rc','date','settle__winner']].merge(feb.drop(columns=['date']),on='rc',how='inner')
    feb['y']=(pd.to_numeric(feb.settle__winner,errors='coerce')==3).astype(int)

    all_data=pd.concat([octo,nov,dec,jan,feb],ignore_index=True,sort=False)
    base_feats,enh_feats,new_feats=choose_features(all_data)
    feature_sets={'BASE':base_feats,'ENHANCED':enh_feats}

    coverage={c:float(pd.to_numeric(all_data[c],errors='coerce').notna().mean()) for c in new_feats}

    histories={
      'nov':pd.concat([octo,nov],ignore_index=True,sort=False),
      'dec':pd.concat([octo,nov,dec],ignore_index=True,sort=False),
      'jan':pd.concat([octo,nov,dec,jan],ignore_index=True,sort=False),
      'feb':pd.concat([octo,nov,dec,jan,feb],ignore_index=True,sort=False)
    }
    targets={'nov':nov,'dec':dec,'jan':jan,'feb':feb}
    preds={m:walk_predictions(histories[m],targets[m],feature_sets) for m in targets}

    results={}
    wave9={'20':0.391304347826087,'30':0.375,'50':0.34408602150537637,
           '75':0.34408602150537637,'100':0.3235294117647059}
    for family in ['BASE','ENHANCED']:
        frozen,strata=freeze(preds,family)
        front,evals=feb_frontier(preds['feb'],frozen,family)
        results[family]={'pre_feb_strata':strata,'frozen_count':len(frozen),
                         'feb_support_frontier':front,'feb_frozen_evals':evals}

    improvement_vs_base={};improvement_vs_wave9={}
    for k in map(str,FEB_SUPPORTS):
        eb=results['ENHANCED']['feb_support_frontier'][k]['best']
        bb=results['BASE']['feb_support_frontier'][k]['best']
        er=eb['feb_worst_half_rate'] if eb else None
        br=bb['feb_worst_half_rate'] if bb else None
        improvement_vs_base[k]=(er-br) if er is not None and br is not None else None
        improvement_vs_wave9[k]=(er-wave9[k]) if er is not None else None

    out={
      'policy':{
        'unused_pre_only':True,'current_meet_fields_used':False,
        'raw_ids_used_as_ordinal_features':False,
        'pre_feb_selection_only':True,'february_one_shot_transfer':True,
        'march_outcomes_opened':False,'september_outcomes_read':False,
        'production_v288_changed':False
      },
      'cross_source_feb_winner_check':{'n':len(fc),'agreement':agree},
      'source_audit':{'oct':oa,'nov':na,'dec':da,'jan':ja,'feb':fa},
      'rows':{'oct':len(octo),'nov':len(nov),'dec':len(dec),'jan':len(jan),'feb':len(feb)},
      'feature_counts':{'base':len(base_feats),'new':len(new_feats),'enhanced':len(enh_feats)},
      'new_feature_coverage':coverage,
      'results':results,
      'wave9_baseline':wave9,
      'improvement_enhanced_vs_base':improvement_vs_base,
      'improvement_enhanced_vs_wave9':improvement_vs_wave9
    }
    with open('research_3head_funsite_broad50_wave16_result.json','w') as f:
        json.dump(out,f,ensure_ascii=False,indent=2,default=str)
    print(json.dumps(out,ensure_ascii=False,indent=2,default=str))

if __name__=='__main__':
    main()
