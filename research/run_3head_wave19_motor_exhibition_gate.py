from __future__ import annotations
import json, math, re
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np
import pandas as pd
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

from run_3head_funsite_broad50_wave16 import (
    fetch, build_pre_enhanced, load_canonical, choose_features, walk_predictions, pct_ref
)

MOTOR_START='2025-07-01'
POST_START='2025-10-01'
END='2026-02-28'
BROAD_QS=[.90,.925,.95,.97,.98,.985,.99]
POST_QS=[.50,.60,.70,.75,.80,.85,.875,.90,.925,.95,.975]
BANDS=[(1,8),(1,12)]
VARIANTS=['PRE','MOTOR','EXHIBIT','BOTH']

def fnum(v):
    try:
        x=float(v)
        return x if np.isfinite(x) else np.nan
    except Exception:
        return np.nan

def ival(v):
    try:return int(str(v).strip())
    except Exception:return None

def bycode(rows):
    return {str(r.get('レースコード','')):r for r in rows if str(r.get('レースコード','')).isdigit()}

def rank_map(result):
    out={}
    for rank in range(1,7):
        b=ival(result.get(f'{rank}着_艇番'))
        if b is not None:out[b]=rank
    return out

def actual_st_by_boat(result):
    out={}
    for course in range(1,7):
        b=ival(result.get(f'{course}コース_艇番'))
        st=fnum(result.get(f'{course}コース_スタートタイミング'))
        if b is not None and np.isfinite(st):out[b]=st
    return out

def prefetch_sources():
    days=list(pd.date_range(MOTOR_START,END))
    cache={}
    tasks=[]
    for d in days:
        tasks.extend([(d,'programs/race_cards'),(d,'results/realtime')])
        if d>=pd.Timestamp(POST_START):
            tasks.extend([(d,'previews/tkz'),(d,'previews/stt'),(d,'previews/original_exhibition')])
    with ThreadPoolExecutor(max_workers=24) as ex:
        fut={ex.submit(fetch,k,d.date()):(d.normalize(),k) for d,k in tasks}
        for f in as_completed(fut):
            d,k=fut[f]
            try:cache[(d,k)]=f.result()
            except Exception:cache[(d,k)]=[]
    return days,cache

def new_motor():
    return {'n':0,'wins':0,'top2':0,'top3':0,'rank_n':0,'rank_sum':0.0,
            'st_n':0,'st_sum':0.0,'ewma_rank':np.nan,'ewma_st':np.nan,'last_date':None}

def update_motor(s,rank,st,day):
    s['n']+=1
    if rank is not None:
        s['wins']+=int(rank==1);s['top2']+=int(rank<=2);s['top3']+=int(rank<=3)
        s['rank_n']+=1;s['rank_sum']+=rank
        s['ewma_rank']=float(rank) if not np.isfinite(s['ewma_rank']) else .30*rank+.70*s['ewma_rank']
    if np.isfinite(st):
        s['st_n']+=1;s['st_sum']+=st
        s['ewma_st']=float(st) if not np.isfinite(s['ewma_st']) else .30*st+.70*s['ewma_st']
    s['last_date']=pd.Timestamp(day).normalize()

def shr(num,den,prior,k):
    return (num+k*prior)/(den+k) if den+k else prior

def motor_summary(s,g,day):
    gn=max(g['n'],1)
    gp_win=g['wins']/gn;gp2=g['top2']/gn;gp3=g['top3']/gn
    gr=g['rank_sum']/g['rank_n'] if g['rank_n'] else 3.5
    gst=g['st_sum']/g['st_n'] if g['st_n'] else .18
    mean_rank=(s['rank_sum']+12*gr)/(s['rank_n']+12) if s['rank_n']+12 else gr
    mean_st=(s['st_sum']+8*gst)/(s['st_n']+8) if s['st_n']+8 else gst
    return {
      'starts':float(s['n']),
      'win':shr(s['wins'],s['n'],gp_win,12),
      'top2':shr(s['top2'],s['n'],gp2,12),
      'top3':shr(s['top3'],s['n'],gp3,12),
      'mean_rank':mean_rank,
      'ewma_rank':s['ewma_rank'] if np.isfinite(s['ewma_rank']) else gr,
      'mean_st':mean_st,
      'ewma_st':s['ewma_st'] if np.isfinite(s['ewma_st']) else gst,
      'days_since':float((pd.Timestamp(day).normalize()-s['last_date']).days) if s['last_date'] is not None else 999.0
    }

def norm_label(v):
    s=str(v or '').replace('　','').replace(' ','')
    if 'まわり足' in s or '回り足' in s:return 'turn'
    if '直線' in s:return 'straight'
    if '一周' in s or '半周ラップ' in s:return 'lap'
    return None

def exhibition_features(tk,st,og):
    z={}
    ex=[fnum(tk.get(f'艇{b}_展示タイム')) for b in range(1,7)] if tk else [np.nan]*6
    ss=[fnum(st.get(f'艇{b}_スタート展示')) for b in range(1,7)] if st else [np.nan]*6
    common=all(np.isfinite(x) for x in ex) and all(np.isfinite(x) for x in ss)
    z['post_common_ready']=1.0 if common else 0.0
    if all(np.isfinite(x) for x in ex):
        e3=ex[2];others=[ex[i] for i in range(6) if i!=2]
        z.update({
          'post_ex3':e3,
          'post_ex_field_edge':float(np.mean(others)-e3),
          'post_ex_rank3':float(1+sum(x<e3 for x in others)),
          'post_ex_edge1':ex[0]-e3,'post_ex_edge2':ex[1]-e3,'post_ex_edge4':ex[3]-e3,
          'post_ex_inner_edge':float(np.mean(ex[:2])-e3)
        })
    if all(np.isfinite(x) for x in ss):
        s3=ss[2];others=[ss[i] for i in range(6) if i!=2]
        z.update({
          'post_st3':s3,
          'post_st_field_edge':float(np.mean(others)-s3),
          'post_st_rank3':float(1+sum(x<s3 for x in others)),
          'post_st_edge1':ss[0]-s3,'post_st_edge2':ss[1]-s3,'post_st_edge4':ss[3]-s3,
          'post_st_inner_edge':float(np.mean(ss[:2])-s3)
        })
    if st:
        c3=ival(st.get('艇3_コース'))
        z['post_course3']=float(c3) if c3 is not None else np.nan
        z['post_course3_shift']=float(c3-3) if c3 is not None else np.nan
        z['post_course3_abs_shift']=float(abs(c3-3)) if c3 is not None else np.nan
    if tk:
        z['post_tilt3']=fnum(tk.get('艇3_チルト'))
        z['post_weight3']=fnum(tk.get('艇3_体重(kg)'))
        z['post_adjust3']=fnum(tk.get('艇3_体重調整(kg)'))

    metrics={}
    if og:
        for k in range(1,5):
            lab=norm_label(og.get(f'計測項目{k}'))
            if lab:
                vals=[fnum(og.get(f'艇{b}_値{k}')) for b in range(1,7)]
                if all(np.isfinite(x) for x in vals):metrics[lab]=vals
    for lab in ['turn','straight','lap']:
        vals=metrics.get(lab)
        z[f'post_{lab}_available']=1.0 if vals is not None else 0.0
        if vals is not None:
            v3=vals[2];others=[vals[i] for i in range(6) if i!=2]
            z[f'post_{lab}3']=v3
            z[f'post_{lab}_field_edge']=float(np.mean(others)-v3)
            z[f'post_{lab}_edge1']=vals[0]-v3
            z[f'post_{lab}_edge2']=vals[1]-v3
            z[f'post_{lab}_edge4']=vals[3]-v3
            z[f'post_{lab}_inner_edge']=float(np.mean(vals[:2])-v3)
    return z

def build_motor_exhibition(days,cache):
    state=defaultdict(new_motor);global_venue=defaultdict(new_motor)
    rows=[];audit={'motor_days':0,'post_days':0,'motor_events':0,'post_rows':0,'common_ready':0}
    t0=pd.Timestamp(POST_START)
    for day in sorted(days):
        day=day.normalize()
        cards=bycode(cache.get((day,'programs/race_cards'),[]))
        results=bycode(cache.get((day,'results/realtime'),[]))
        if cards:audit['motor_days']+=1

        if day>=t0 and cards:
            audit['post_days']+=1
            tkz=bycode(cache.get((day,'previews/tkz'),[]))
            stt=bycode(cache.get((day,'previews/stt'),[]))
            org=bycode(cache.get((day,'previews/original_exhibition'),[]))
            for code,rc in cards.items():
                venue=str(rc.get('レース場コード','')).zfill(2)
                z={'rc':int(code),'date':day}
                per={}
                for b in range(1,7):
                    mid=ival(rc.get(f'艇{b}_モーター番号'))
                    s=state[(venue,mid)] if mid is not None else new_motor()
                    g=global_venue[venue]
                    sm=motor_summary(s,g,day);per[b]=sm
                    for k,v in sm.items():z[f'post_motor_b{b}_{k}']=v
                for opp in [1,2,4]:
                    z[f'post_motor_gap{opp}_top2']=per[3]['top2']-per[opp]['top2']
                    z[f'post_motor_gap{opp}_top3']=per[3]['top3']-per[opp]['top3']
                    z[f'post_motor_rank_edge{opp}']=per[opp]['ewma_rank']-per[3]['ewma_rank']
                    z[f'post_motor_st_edge{opp}']=per[opp]['ewma_st']-per[3]['ewma_st']
                z['post_motor_inner_rank_edge']=((per[1]['ewma_rank']+per[2]['ewma_rank'])/2)-per[3]['ewma_rank']
                z['post_motor_inner_top2_gap']=per[3]['top2']-((per[1]['top2']+per[2]['top2'])/2)
                z.update(exhibition_features(tkz.get(code,{}),stt.get(code,{}),org.get(code,{})))
                rows.append(z);audit['post_rows']+=1
                audit['common_ready']+=int(z.get('post_common_ready',0)==1)

        # Update states strictly after snapshots.
        for code,rr in results.items():
            rc=cards.get(code)
            if rc is None:continue
            venue=str(rc.get('レース場コード','')).zfill(2)
            rm=rank_map(rr);stm=actual_st_by_boat(rr)
            for b in range(1,7):
                mid=ival(rc.get(f'艇{b}_モーター番号'))
                if mid is None:continue
                e_rank=rm.get(b);e_st=stm.get(b,np.nan)
                update_motor(state[(venue,mid)],e_rank,e_st,day)
                update_motor(global_venue[venue],e_rank,e_st,day)
                audit['motor_events']+=1
    return pd.DataFrame(rows).drop_duplicates('rc'),audit

def prep_month(x,res):
    y=x.merge(res[['rc','result_winner']],on='rc',how='inner')
    y['y']=(y.result_winner==3).astype(int)
    return y

def make_pre_scores(frames):
    all_data=pd.concat(list(frames.values()),ignore_index=True,sort=False)
    _,enh,_=choose_features(all_data)
    feature_sets={'ENHANCED':enh}
    order=['oct','nov','dec','jan','feb']
    histories={}
    # September 2025 is present in frames only as history support, never a reported validation month.
    sep=frames['sep']
    acc=sep.copy()
    for m in order:
        acc=pd.concat([acc,frames[m]],ignore_index=True,sort=False)
        histories[m]=acc.copy()
    preds={m:walk_predictions(histories[m],frames[m],feature_sets) for m in order}
    out={}
    for m,p in preds.items():
        q=p[(p.family=='ENHANCED')&(p.window==42)][['rc','date','venue','race_no','y','p_logit']].copy()
        q=q.rename(columns={'p_logit':'pre_score'})
        out[m]=q.drop_duplicates('rc')
    return out,len(enh)

def rolling_post_scores(allrows,target_month,features,require_common):
    target=allrows[allrows.month==target_month].sort_values(['date','rc']).copy()
    outs=[]
    for dayv in sorted(target.date.dt.normalize().unique()):
        day=pd.Timestamp(dayv)
        tr=allrows[(allrows.date<day)&(allrows.date>=day-pd.Timedelta(days=60))].copy()
        if require_common:tr=tr[tr.post_common_ready==1].copy()
        tr=tr[tr.y.notna()].copy()
        today=target[target.date.dt.normalize()==day].copy()
        if require_common:today=today[today.post_common_ready==1].copy()
        if len(tr)<120 or tr.y.nunique()<2 or len(today)==0:continue
        feats=[c for c in features if c in tr.columns and c in today.columns and pd.to_numeric(tr[c],errors='coerce').notna().sum()>=50]
        if len(feats)<3:continue
        model=make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),
            LogisticRegression(C=.20,class_weight='balanced',solver='liblinear',max_iter=1800,random_state=190))
        model.fit(tr[feats],tr.y.astype(int))
        ptr=model.predict_proba(tr[feats])[:,1]
        p=model.predict_proba(today[feats])[:,1]
        z=today[['rc']].copy();z['score']=pct_ref(ptr,p);outs.append(z)
    return pd.concat(outs,ignore_index=True).drop_duplicates('rc') if outs else pd.DataFrame(columns=['rc','score'])

def metrics(mask,df):
    m=np.asarray(mask,bool);n=int(m.sum());y=df.y.to_numpy(dtype=int)
    return {'n':n,'hits':int(y[m].sum()) if n else 0,'rate':float(y[m].mean()) if n else None,
            'venues':int(df.loc[m,'venue'].nunique()) if n else 0}

def eval_selector(df,c,month):
    rn=pd.to_numeric(df.race_no,errors='coerce').to_numpy()
    pre=pd.to_numeric(df.pre_score,errors='coerce').to_numpy(float)
    lo,hi=c['band'];m=(rn>=lo)&(rn<=hi)&np.isfinite(pre)&(pre>=c['bq'])
    if c['variant']!='PRE':
        ps=pd.to_numeric(df[c['score_col']],errors='coerce').to_numpy(float)
        m &= np.isfinite(ps)&(ps>=c['pq'])
    d=df.date.dt.day.to_numpy()
    split=15 if month!='feb' else 14
    return {'h1':metrics(m&(d<=split),df),'h2':metrics(m&(d>split),df)}

def eligible(ms,lo=40,hi=70):
    for m in ['nov','dec','jan']:
        z=ms[m];n=z['h1']['n']+z['h2']['n']
        if n<lo or n>hi:return False
        for h in ['h1','h2']:
            if z[h]['n']<8 or z[h]['venues']<6 or z[h]['rate'] is None:return False
    return True

def summarize(ms):
    rates=[ms[m][h]['rate'] for m in ['nov','dec','jan'] for h in ['h1','h2']]
    ns=[ms[m]['h1']['n']+ms[m]['h2']['n'] for m in ['nov','dec','jan']]
    hits=sum(ms[m][h]['hits'] for m in ['nov','dec','jan'] for h in ['h1','h2'])
    n=sum(ns)
    return {'persistent_worst':min(rates),'combined_rate':hits/n,'combined_n':n,'combined_hits':hits,
            'avg_month_n':float(np.mean(ns)),'monthly_n':dict(zip(['nov','dec','jan'],ns))}

def rank_key(z):
    s=z['summary']
    return (s['persistent_worst'],s['combined_rate'],-abs(s['avg_month_n']-50.0))

def main():
    canon=load_canonical()
    raw={}
    for m,(a,b) in {
      'sep':('2025-09-01','2025-09-30'),'oct':('2025-10-01','2025-10-31'),
      'nov':('2025-11-01','2025-11-30'),'dec':('2025-12-01','2025-12-31'),
      'jan':('2026-01-01','2026-01-31'),'feb':('2026-02-01','2026-02-28')}.items():
        x,r,audit=build_pre_enhanced(a,b,True);raw[m]=(x,r,audit)
    frames={m:prep_month(x,r) for m,(x,r,_) in raw.items()}

    fc=canon[canon.date<'2026-03-01'].merge(raw['feb'][1][['rc','result_winner']],on='rc',how='inner')
    agree=float((pd.to_numeric(fc.settle__winner,errors='coerce')==fc.result_winner).mean()) if len(fc) else 0.0
    if len(fc)<3000 or agree<.995:raise RuntimeError(f'winner cross-check failed n={len(fc)} agreement={agree}')

    prescores,enh_count=make_pre_scores(frames)

    days,cache=prefetch_sources()
    post,audit=build_motor_exhibition(days,cache)

    months={}
    for m in ['oct','nov','dec','jan','feb']:
        q=prescores[m].merge(post,on=['rc','date'],how='left',validate='one_to_one')
        q['month']=m
        months[m]=q
    allrows=pd.concat(list(months.values()),ignore_index=True,sort=False)

    motor_feats=[c for c in allrows.columns if c.startswith('post_motor_') and c!='post_motor_number']
    exhibit_feats=[c for c in allrows.columns if c.startswith('post_') and not c.startswith('post_motor_') and c!='post_common_ready']
    motor_inputs=['pre_score']+motor_feats
    exhibit_inputs=['pre_score']+exhibit_feats
    both_inputs=['pre_score']+motor_feats+exhibit_feats

    for m in ['nov','dec','jan','feb']:
        for name,feats,req in [('MOTOR',motor_inputs,False),('EXHIBIT',exhibit_inputs,True),('BOTH',both_inputs,True)]:
            sc=rolling_post_scores(allrows,m,feats,req).rename(columns={'score':f'post_score_{name.lower()}'})
            months[m]=months[m].merge(sc,on='rc',how='left')
    # Keep October only as model history; selector evaluation starts Nov.
    score_cols={'MOTOR':'post_score_motor','EXHIBIT':'post_score_exhibit','BOTH':'post_score_both'}

    candidates=[]
    for variant in VARIANTS:
        for band in BANDS:
            for bq in BROAD_QS:
                if variant=='PRE':
                    candidates.append({'variant':variant,'band':list(band),'bq':bq,'pq':None,'score_col':None})
                else:
                    for pq in POST_QS:
                        candidates.append({'variant':variant,'band':list(band),'bq':bq,'pq':pq,'score_col':score_cols[variant]})

    evals=[]
    for c in candidates:
        ms={m:eval_selector(months[m],c,m) for m in ['nov','dec','jan']}
        if not eligible(ms,40,70):continue
        evals.append({'candidate':c,'months':ms,'summary':summarize(ms)})

    by_variant={}
    for variant in VARIANTS:
        pool=sorted([z for z in evals if z['candidate']['variant']==variant],key=rank_key,reverse=True)
        best=pool[0] if pool else None
        ref=None
        if best:
            f=eval_selector(months['feb'],best['candidate'],'feb')
            n=f['h1']['n']+f['h2']['n'];h=f['h1']['hits']+f['h2']['hits']
            ref={'h1':f['h1'],'h2':f['h2'],'combined_n':n,'combined_hits':h,
                 'combined_rate':h/n if n else None,
                 'worst_half_rate':min(f['h1']['rate'],f['h2']['rate']) if f['h1']['rate'] is not None and f['h2']['rate'] is not None else None}
        by_variant[variant]={'eligible_count':len(pool),'best_pre_feb':best,'feb_reference_non_pristine':ref,'top10':pool[:10]}

    overall_pool=sorted(evals,key=rank_key,reverse=True)
    overall=overall_pool[0] if overall_pool else None

    out={
      'policy':{
        'two_stage_pre_then_head_gate':True,'motor_strict_prior_day':True,'same_day_results_used':False,
        'exhibition_used_only_post_pre':True,'direct_exhibition_pair_ranking_rejected_preserved':True,
        'selection_nov_dec_jan_only':True,'february_reference_non_pristine':True,
        'march_outcomes_opened':False,'september_2026_outcomes_read':False,'production_v288_changed':False
      },
      'prior_exhibition_v5_context':{'feb_common_ready_head_races':390,'A_static_capture':0.3717948718,'B_exhibit_capture':0.3666666667,'C_original_capture':0.3461538462},
      'cross_source_feb_winner_check':{'n':len(fc),'agreement':agree},
      'source_audit':{m:raw[m][2] for m in raw},
      'post_source_audit':audit,
      'feature_counts':{'enhanced_pre':enh_count,'motor':len(motor_feats),'exhibition':len(exhibit_feats),'both_post':len(motor_feats)+len(exhibit_feats)},
      'rows':{m:len(months[m]) for m in months},
      'common_ready':{m:int(pd.to_numeric(months[m].post_common_ready,errors='coerce').fillna(0).eq(1).sum()) for m in months},
      'candidate_grid_count':len(candidates),'eligible_final_count':len(evals),
      'results_by_variant':by_variant,
      'overall_best_pre_feb':overall
    }
    with open('research_3head_wave19_motor_exhibition_gate_result.json','w') as f:
        json.dump(out,f,ensure_ascii=False,indent=2,default=str)
    print(json.dumps(out,ensure_ascii=False,indent=2,default=str))

if __name__=='__main__':
    main()
