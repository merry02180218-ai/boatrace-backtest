from __future__ import annotations
import json, math, re
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np
import pandas as pd

from run_3head_funsite_broad50_wave16 import (
    fetch, build_pre_enhanced, load_canonical, choose_features, walk_predictions, eval_candidate
)

HIST_START='2025-04-01'
HIST_END='2026-02-28'
TARGET_MONTHS=['nov','dec','jan','feb']
WINDOWS=[21,42]
BANDS=[(1,4),(1,6),(1,8),(1,10),(1,12)]
MODELS=['p_logit','p_hist','p_mean']
QS=[.95,.96,.97,.975,.98,.985,.99,.9925,.995]

def fnum(v):
    try:
        x=float(v)
        return x if np.isfinite(x) else np.nan
    except Exception:
        return np.nan

def ival(v):
    try:return int(str(v).strip())
    except Exception:return None

def norm_move(v):
    s=str(v or '').replace('　','').replace(' ','')
    if 'まくり差し' in s:return 'makurizashi'
    if 'まくり' in s:return 'makuri'
    if '逃げ' in s:return 'nige'
    if '差し' in s:return 'sashi'
    if '抜' in s:return 'nuki'
    if '恵' in s:return 'megumi'
    return 'other'

def prefetch_archive(start,end):
    days=list(pd.date_range(start,end))
    cache={}
    kinds=['programs/race_cards','results/realtime']
    with ThreadPoolExecutor(max_workers=24) as ex:
        fut={ex.submit(fetch,k,d.date()):(d,k) for d in days for k in kinds}
        for f in as_completed(fut):
            d,k=fut[f]
            try:cache[(d.normalize(),k)]=f.result()
            except Exception:cache[(d.normalize(),k)]=[]
    return days,cache

def build_day_data(days,cache):
    day_events={}
    day_targets={}
    audit={'days':0,'racecard_days':0,'result_days':0,'matched_result_races':0,'events':0}
    for day in days:
        day=day.normalize(); audit['days']+=1
        cards=cache.get((day,'programs/race_cards'),[])
        results=cache.get((day,'results/realtime'),[])
        if cards:audit['racecard_days']+=1
        if results:audit['result_days']+=1
        cmap={str(r.get('レースコード','')):r for r in cards}
        trows=[]
        for code,rc in cmap.items():
            if not code.isdigit():continue
            venue=str(rc.get('レース場コード','')).zfill(2)
            rn=int(re.sub(r'\D','',str(rc.get('レース回','0'))) or 0)
            row={'rc':int(code),'date':day,'venue':venue,'race_no':rn}
            for b in range(1,7):
                row[f'reg{b}']=ival(rc.get(f'艇{b}_登録番号'))
            trows.append(row)
        day_targets[day]=trows

        ev=[]
        for rr in results:
            code=str(rr.get('レースコード',''))
            rc=cmap.get(code)
            if rc is None or not code.isdigit():continue
            audit['matched_result_races']+=1
            venue=str(rc.get('レース場コード','')).zfill(2)
            rn=int(re.sub(r'\D','',str(rc.get('レース回','0'))) or 0)
            rank_by_boat={}
            for rank in range(1,7):
                b=ival(rr.get(f'{rank}着_艇番'))
                if b is not None:rank_by_boat[b]=rank
            winner=ival(rr.get('1着_艇番'))
            move=norm_move(rr.get('決まり手'))
            for course in range(1,7):
                boat=ival(rr.get(f'{course}コース_艇番'))
                if boat is None or boat<1 or boat>6:continue
                reg=ival(rc.get(f'艇{boat}_登録番号'))
                if reg is None:continue
                st=fnum(rr.get(f'{course}コース_スタートタイミング'))
                rank=rank_by_boat.get(boat)
                ev.append({
                    'date':day,'rc':int(code),'venue':venue,'race_no':rn,
                    'reg':reg,'frame':boat,'course':course,'st':st,
                    'win':1 if winner==boat else 0,
                    'top2':1 if rank is not None and rank<=2 else 0,
                    'top3':1 if rank is not None and rank<=3 else 0,
                    'same_frame':1 if boat==course else 0,
                    'move':move if winner==boat else None
                })
        audit['events']+=len(ev)
        day_events[day]=ev
    return day_targets,day_events,audit

def new_stat():
    return {'n':0,'wins':0,'top2':0,'top3':0,'st_n':0,'st_sum':0.0,'st_sq':0.0,
            'ewma_st':np.nan,'same':0,'moves':defaultdict(int)}

def upd(s,e):
    s['n']+=1;s['wins']+=e['win'];s['top2']+=e['top2'];s['top3']+=e['top3'];s['same']+=e['same_frame']
    st=e['st']
    if np.isfinite(st):
        s['st_n']+=1;s['st_sum']+=st;s['st_sq']+=st*st
        s['ewma_st']=st if not np.isfinite(s['ewma_st']) else 0.25*st+0.75*s['ewma_st']
    if e['win'] and e['move']:s['moves'][e['move']]+=1

def rate(num,den,prior,k):
    return (num+k*prior)/(den+k) if den+k>0 else prior

def st_mean(s,prior,k=8):
    return (s['st_sum']+k*prior)/(s['st_n']+k) if s['st_n']+k>0 else prior

def st_sd(s):
    if s['st_n']<2:return np.nan
    m=s['st_sum']/s['st_n']
    v=max(0.0,s['st_sq']/s['st_n']-m*m)
    return math.sqrt(v)

def summarize_course(s,g):
    gn=max(g['n'],1)
    gw=g['wins']/gn; gt2=g['top2']/gn; gt3=g['top3']/gn
    gst=g['st_sum']/g['st_n'] if g['st_n'] else 0.18
    out={
      'starts':float(s['n']),
      'win':rate(s['wins'],s['n'],gw,12),
      'top2':rate(s['top2'],s['n'],gt2,12),
      'top3':rate(s['top3'],s['n'],gt3,12),
      'avg_st':st_mean(s,gst,8),
      'st_sd':st_sd(s),
      'ewma_st':s['ewma_st'] if np.isfinite(s['ewma_st']) else gst,
      'same_frame':rate(s['same'],s['n'],g['same']/gn,12)
    }
    for mv in ['nige','sashi','makuri','makurizashi','nuki']:
        gp=g['moves'][mv]/gn
        out[mv]=rate(s['moves'][mv],s['n'],gp,12)
    return out

def venue_rate(s,g,prior_k):
    gp=g['wins']/g['n'] if g['n'] else 1/6
    return rate(s['wins'],s['n'],gp,prior_k)

def build_causal_course_features(day_targets,day_events,days):
    racer_course=defaultdict(new_stat)
    racer_frame=defaultdict(new_stat)
    global_course=defaultdict(new_stat)
    venue_course=defaultdict(new_stat)
    venue_race_course=defaultdict(new_stat)
    out=[]

    target_lo=pd.Timestamp('2025-11-01')
    target_hi=pd.Timestamp('2026-02-28')

    for day in sorted(days):
        day=day.normalize()

        # Snapshot BEFORE today's results: strict prior-date causality.
        if target_lo<=day<=target_hi:
            for tr in day_targets.get(day,[]):
                z={'rc':tr['rc']}
                per={}
                for b in range(1,7):
                    reg=tr.get(f'reg{b}')
                    course=b
                    gs=global_course[course]
                    rs=racer_course[(reg,course)] if reg is not None else new_stat()
                    fs=racer_frame[(reg,b)] if reg is not None else new_stat()
                    sm=summarize_course(rs,gs)
                    # Frame -> actual course stability is distinct from racer-course sample.
                    gfn=max(global_course[course]['n'],1)
                    global_same=global_course[course]['same']/gfn
                    frame_same=rate(fs['same'],fs['n'],global_same,12)
                    vs=venue_course[(tr['venue'],course)]
                    vrs=venue_race_course[(tr['venue'],tr['race_no'],course)]
                    sm['frame_to_course']=frame_same
                    sm['venue_win']=venue_rate(vs,gs,40)
                    # venue-race shrinks toward venue-course, then global through venue rate.
                    vr_prior=sm['venue_win']
                    sm['venue_race_win']=rate(vrs['wins'],vrs['n'],vr_prior,60)
                    per[b]=sm
                    for k,v in sm.items():z[f'course_b{b}_{k}']=v

                # Core matchup features: lower ST is better, hence opponent - boat3.
                for opp in [1,2,4]:
                    z[f'course_gap{opp}_win']=per[3]['win']-per[opp]['win']
                    z[f'course_gap{opp}_venue_win']=per[3]['venue_win']-per[opp]['venue_win']
                    z[f'course_gap{opp}_venue_race_win']=per[3]['venue_race_win']-per[opp]['venue_race_win']
                    z[f'course_st_edge{opp}']=per[opp]['avg_st']-per[3]['avg_st']
                    z[f'course_ewma_st_edge{opp}']=per[opp]['ewma_st']-per[3]['ewma_st']

                attack3=per[3]['makuri']+per[3]['makurizashi']
                z['course_b3_attack_move']=attack3
                z['course_b1_escape']=per[1]['nige']
                z['course_attack_minus_b1_escape']=attack3-per[1]['nige']
                z['course_attack_minus_b2_win']=attack3-per[2]['win']
                z['course_attack_minus_b4_win']=attack3-per[4]['win']
                z['course_inner_st_edge']=((per[1]['avg_st']+per[2]['avg_st'])/2)-per[3]['avg_st']
                z['course_inner_win_gap']=per[3]['win']-((per[1]['win']+per[2]['win'])/2)
                z['course_venue3_strength']=per[3]['venue_win']
                z['course_venue_race3_strength']=per[3]['venue_race_win']
                out.append(z)

        # Only after all target snapshots for the day are created, update with today's outcomes.
        for e in day_events.get(day,[]):
            upd(racer_course[(e['reg'],e['course'])],e)
            upd(racer_frame[(e['reg'],e['frame'])],e)
            upd(global_course[e['course']],e)
            upd(venue_course[(e['venue'],e['course'])],e)
            upd(venue_race_course[(e['venue'],e['race_no'],e['course'])],e)

    return pd.DataFrame(out).drop_duplicates('rc')

def candidate_universe(family):
    out=[]
    for w in WINDOWS:
        for band in BANDS:
            for model in MODELS:
                for q in QS:
                    out.append({'family':family,'window':w,'band':list(band),'model':model,'q':q})
    return out

def combined(z):
    n=z['h1']['n']+z['h2']['n'];h=z['h1']['hits']+z['h2']['hits']
    return {'n':n,'hits':h,'rate':h/n if n else None}

def pre_metrics(ms):
    rates=[ms[m][h]['rate'] for m in ['nov','dec','jan'] for h in ['h1','h2']]
    monthly={m:combined(ms[m]) for m in ['nov','dec','jan']}
    n=sum(v['n'] for v in monthly.values());hits=sum(v['hits'] for v in monthly.values())
    valid=[r for r in rates if r is not None]
    persistent_worst=min(valid) if len(valid)==len(rates) else -1.0
    return {'persistent_worst':persistent_worst,'persistent_combined':hits/n if n else None,
            'avg_month_n':sum(v['n'] for v in monthly.values())/3,'monthly':monthly}

def eligible(ms,lo=40,hi=70):
    for m in ['nov','dec','jan']:
        z=ms[m];n=z['h1']['n']+z['h2']['n']
        if n<lo or n>hi:return False
        for h in ['h1','h2']:
            if z[h]['n']<8 or z[h]['venues']<6 or z[h]['rate'] is None:return False
    return True

def rank_key(row):
    p=row['pre']
    return (p['persistent_worst'],p['persistent_combined'],-abs(p['avg_month_n']-50.0))

def eval_family(preds,family):
    rows=[]
    for c in candidate_universe(family):
        ms={m:eval_candidate(preds[m],c,False) for m in ['nov','dec','jan']}
        p=pre_metrics(ms)
        rows.append({'candidate':c,'months':ms,'pre':p})
    strict=sorted([r for r in rows if eligible(r['months'])],key=rank_key,reverse=True)
    wide=sorted([r for r in rows if eligible(r['months'],30,80)],key=rank_key,reverse=True)
    primary=strict[0] if strict else (wide[0] if wide else None)
    ref=None
    if primary:
        f=eval_candidate(preds['feb'],primary['candidate'],True)
        a,b=f['h1'],f['h2'];n=a['n']+b['n'];h=a['hits']+b['hits']
        ref={'candidate':primary['candidate'],'h1':a,'h2':b,'combined_n':n,'combined_hits':h,
             'combined_rate':h/n if n else None,
             'worst_half_rate':min(a['rate'],b['rate']) if a['rate'] is not None and b['rate'] is not None else None}
    return {'strict_count':len(strict),'wide_count':len(wide),
            'primary_source':'strict_40_70' if strict else ('wide_30_80' if wide else None),
            'primary_pre_feb':primary,'top10_strict':strict[:10],'top10_wide':wide[:10],
            'feb_reference_non_pristine':ref}

def main():
    # Existing PRE datasets.
    octo,ores,oa=build_pre_enhanced('2025-10-01','2025-10-31',True)
    nov,nres,na=build_pre_enhanced('2025-11-01','2025-11-30',True)
    dec,dres,da=build_pre_enhanced('2025-12-01','2025-12-31',True)
    jan,jres,ja=build_pre_enhanced('2026-01-01','2026-01-31',True)
    feb,fres,fa=build_pre_enhanced('2026-02-01','2026-02-28',True)
    canon=load_canonical()

    fc=canon[canon.date<'2026-03-01'].merge(fres[['rc','result_winner']],on='rc',how='inner')
    agree=float((pd.to_numeric(fc.settle__winner,errors='coerce')==fc.result_winner).mean()) if len(fc) else 0.0
    if len(fc)<3000 or agree<.995:raise RuntimeError(f'winner cross-check failed n={len(fc)} agreement={agree}')

    frames=[]
    for x,r in [(octo,ores),(nov,nres),(dec,dres),(jan,jres)]:
        y=x.merge(r[['rc','result_winner']],on='rc',how='inner')
        y['y']=(y.result_winner==3).astype(int);frames.append(y)
    octo,nov,dec,jan=frames
    feb=canon[canon.date<'2026-03-01'][['rc','date','settle__winner']].merge(
        feb.drop(columns=['date']),on='rc',how='inner')
    feb['y']=(pd.to_numeric(feb.settle__winner,errors='coerce')==3).astype(int)

    # New causal archive features.
    days,cache=prefetch_archive(HIST_START,HIST_END)
    day_targets,day_events,archive_audit=build_day_data(days,cache)
    course=build_causal_course_features(day_targets,day_events,days)

    def merge_course(x):
        return x.merge(course,on='rc',how='left',validate='one_to_one')
    nov=merge_course(nov);dec=merge_course(dec);jan=merge_course(jan);feb=merge_course(feb)
    # Oct has no usable PRE rows in this source period; leave as-is.
    all_data=pd.concat([nov,dec,jan,feb],ignore_index=True,sort=False)
    _,enh_feats,_=choose_features(all_data)
    course_feats=[c for c in all_data.columns if c.startswith('course_') and
                  pd.api.types.is_numeric_dtype(all_data[c]) and all_data[c].notna().sum()>=200]
    feature_sets={'COURSEPLUS':sorted(set(enh_feats+course_feats))}

    histories={
      'nov':pd.concat([octo,nov],ignore_index=True,sort=False),
      'dec':pd.concat([octo,nov,dec],ignore_index=True,sort=False),
      'jan':pd.concat([octo,nov,dec,jan],ignore_index=True,sort=False),
      'feb':pd.concat([octo,nov,dec,jan,feb],ignore_index=True,sort=False)
    }
    targets={'nov':nov,'dec':dec,'jan':jan,'feb':feb}
    preds={m:walk_predictions(histories[m],targets[m],feature_sets) for m in targets}

    results={'COURSEPLUS':eval_family(preds,'COURSEPLUS')}

    out={
      'policy':{
        'course_history_strict_prior_date':True,'same_day_results_used':False,
        'current_precomputed_estimate_tables_used':False,'target_monthly_volume_40_70':True,
        'pre_feb_selection_only':True,'february_reference_non_pristine':True,
        'march_outcomes_opened':False,'september_outcomes_read':False,'production_v288_changed':False
      },
      'history_source':{'start':HIST_START,'end':HIST_END,'audit':archive_audit},
      'cross_source_feb_winner_check':{'n':len(fc),'agreement':agree},
      'source_audit':{'oct':oa,'nov':na,'dec':da,'jan':ja,'feb':fa},
      'rows':{'oct':len(octo),'nov':len(nov),'dec':len(dec),'jan':len(jan),'feb':len(feb),
              'course_feature_rows':len(course)},
      'feature_counts':{'enhanced':len(enh_feats),'course_new':len(course_feats),
                        'courseplus':len(feature_sets['COURSEPLUS'])},
      'course_feature_names':course_feats,
      'wave17_enhanced_baseline':{'avg_month_n':42.666666666666664,'pre_feb_combined_rate':0.34375,'persistent_worst':0.2857142857142857,'feb_reference_rate':0.36666666666666664},
      'results':results
    }
    with open('research_3head_funsite_broad50_wave18_result.json','w') as f:
        json.dump(out,f,ensure_ascii=False,indent=2,default=str)
    print(json.dumps(out,ensure_ascii=False,indent=2,default=str))

if __name__=='__main__':
    main()
