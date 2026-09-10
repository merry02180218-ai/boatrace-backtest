#!/usr/bin/env python3
"""Deadline-time 3-head scorer using a prebuilt model cache.
No historical rebuild or model fit is allowed here.
"""
from __future__ import annotations
import hashlib, json, time
import joblib
import numpy as np
import pandas as pd

import analyze_v222_3head_broad_feature_audit as v222
import analyze_v234_3head_waku10_restored_replay as v234
import analyze_v242_3head_target_comp3_min5_max10 as v242
import fetch_live_trifecta_odds as live

CACHE='cache_20260910_3head_live.joblib'
OUT='smoke_20260910_3head_cached_live.json'
TXT='smoke_20260910_3head_cached_live.txt'
TARGETS=[('児島',16,5,'平田さやか'),('鳴門',14,7,'今井美亜')]
KEEP=-0.1999999999999999
RESCUE=0.5672342857142857


def fetch_odds(jcd,rno):
    params={'rno':rno,'jcd':f'{jcd:02d}','hd':'20260910'}
    r=live.safe_get(live.BASE,params)
    html=r.text
    parsed=live.parse_odds(html)
    exp=live.expected_combos()
    if set(parsed)!=exp or len(parsed)!=120:
        raise RuntimeError(f'odds incomplete jcd={jcd} r={rno}: {len(parsed)}')
    return {f'{a}-{b}-{c}':float(o) for (a,b,c),o in parsed.items()}, {
        'resolved_url':r.url,
        'parsed_count':len(parsed),
        'html_sha256':hashlib.sha256(html.encode('utf-8',errors='replace')).hexdigest(),
        'result_endpoint_requested':False,
        'payout_endpoint_requested':False,
        'post_deadline_smoke_test':True,
    }


def dutch(ts,vals):
    stakes=np.asarray(v234.v205.round_dutch(vals,10000),int)
    if int(stakes.sum())!=10000:
        raise RuntimeError('Dutch sum invariant')
    return [{'combo':q,'odds':float(o),'stake':int(s)} for q,o,s in zip(ts,vals,stakes) if s>0]


def main():
    t0=time.perf_counter()
    z=joblib.load(CACHE)
    load_s=time.perf_counter()-t0
    head=z['head_model']; hfs=z['head_features']; cats=z['head_cats']; pair=z['pair_model']; cur=z['current_rows'].copy()
    for c in hfs:
        cur[c]=pd.to_numeric(cur[c],errors='coerce')
    cur['_p_live']=head.predict_proba(cur[hfs+cats])[:,1]

    results=[]
    for name,jcd,rno,racer in TARGETS:
        code=f'20260910{jcd:02d}{rno:02d}'
        q=cur[cur.race_code.astype(str).str.zfill(12)==code]
        if len(q)!=1:
            raise RuntimeError(f'target row count {code}={len(q)}')
        r=q.iloc[0]
        p3=float(r['_p_live'])
        ts=v242.safe_order(r,pair)
        if ts is None:
            raise RuntimeError(f'pair-rank-invalid {code}')
        odds,meta=fetch_odds(jcd,rno)
        ch=v242.choose_n(ts,odds)
        raw_n=ch.get('raw_n'); raw_comp=ch.get('raw_comp'); action=ch.get('action')
        top_n=ch.get('top_n'); comp_odds=ch.get('comp_odds')
        minus=float(r.get('c_b3_minus_b5_st'))
        attack=float(r.get('c_attack3_stretch'))
        v242_buyable=(action=='bet')
        base=bool(v242_buyable and p3>=.45 and raw_n is not None and 7<=raw_n<=18 and comp_odds is not None and 3.05<=comp_odds<=4.0)
        keep=bool(np.isfinite(minus) and minus>=KEEP)
        rescue=bool(np.isfinite(attack) and attack<=RESCUE)
        final=bool(v242_buyable and ((base and keep) or ((not base) and rescue)))
        tickets=[]
        if final:
            n=int(top_n)
            vals=[float(odds[x]) for x in ts[:n]]
            tickets=dutch(ts[:n],vals)
        results.append({
            'race':f'{name}{rno}R','race_code':code,'racer3':racer,'pre_grade':'A',
            'p3':p3,'pair_order20':ts,'raw_top_n':raw_n,'raw_comp_odds':raw_comp,
            'v242_action':action,'purchased_top_n':top_n,'comp_odds':comp_odds,
            'f__c_b3_minus_b5_st':minus,'keep_pass':keep,
            'f__c_attack3_stretch':attack,'rescue_pass':rescue,
            'v243_base':base,'official_final_bet':final,
            'tickets':tickets,'total_stake':sum(x['stake'] for x in tickets),
            'odds_snapshot':meta,
        })
    elapsed=time.perf_counter()-t0
    obj={
        'date':'2026-09-10',
        'mode':'NON-PRISTINE post-deadline cached-live smoke test',
        'historical_rebuild_during_live':False,
        'model_fit_during_live':False,
        'target_result_or_payout_used':False,
        'cache_load_seconds':load_s,
        'total_live_seconds':elapsed,
        'canonical_chain':'v249 PRE A -> v243 final -> v242 variable 5-10 -> 10000 yen Dutch',
        'results':results,
    }
    open(OUT,'w',encoding='utf-8').write(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
    lines=[f'LIVE_SECONDS={elapsed:.3f} cache_load={load_s:.3f}']
    for x in results:
        lines.append(f"{x['race']} p3={x['p3']:.6f} rawN={x['raw_top_n']} rawComp={x['raw_comp_odds']} topN={x['purchased_top_n']} comp={x['comp_odds']} base={x['v243_base']} keep={x['keep_pass']} rescue={x['rescue_pass']} FINAL={x['official_final_bet']}")
        for t in x['tickets']:
            lines.append(f"  {t['combo']} odds={t['odds']:.1f} stake={t['stake']}")
        if x['tickets']:
            lines.append(f"  TOTAL={x['total_stake']}")
    open(TXT,'w',encoding='utf-8').write('\n'.join(lines)+'\n')
    print('\n'.join(lines),flush=True)

if __name__=='__main__':
    main()
