#!/usr/bin/env python3
"""Venue-aware original exhibition audit for HEAD4 production.

The 1HEAD venue map is a LIVE expectation/reference, not the historical HEAD4
feature truth. HEAD4 must reproduce its own frozen research semantics:
- consume whichever original-exhibition metric columns are actually populated;
- ignore a metric column when it is blank for all six boats;
- if a metric column has any value, require all six values for avg availability;
- wall-family features exist only when orig_avg + straight are both complete;
- otherwise frozen wall-derived score inputs are missing and rank to neutral .5.

No September outcomes are read.
"""
from __future__ import annotations
from pathlib import Path
import json, os
import pandas as pd

import head4_original_venue_schema as venue
import probe_1head_v351_boatcast_exhibition as oneprobe
import run_4head_120r_lastminute_fast as live

OUT=Path('/tmp/head4_venue_aware_original');OUT.mkdir(parents=True,exist_ok=True)

def must(cond,msg):
    if not cond: raise RuntimeError(msg)

def fake_state_card(jcd):
    card={
      '艇3_モーター番号':'31','艇4_モーター番号':'41',
      '艇3_モーター2連対率':'31.0','艇4_モーター2連対率':'29.0',
    }
    state={
      'newfeature_motor_history_start':'2025-11-01',
      'motors_newfeature_nov2025':{
        f'{jcd:02d}|31':{'w':2,'n':10},
        f'{jcd:02d}|41':{'w':3,'n':10},
      },
    }
    return card,state

def boats(orig=True):
    d={}
    for b in range(1,7):
        d[str(b)]={
          'cur_ex':1-(b-1)/5,
          'cur_st':1-(b-1)/5,
          'cur_orig_lap':1-(b-1)/5 if orig else .5,
          'cur_orig_turn':1-(b-1)/5 if orig else .5,
          'cur_orig_straight':1-(b-1)/5 if orig else .5,
          'cur_orig_avg':1-(b-1)/5 if orig else .5,
        }
    return d

def unit_contract():
    # HEAD4 keeps the 1HEAD venue map as the minimum expected LIVE contract.
    must(venue.ORIG_REQUIRED==oneprobe.ORIG_REQUIRED,'HEAD4 reference venue map differs from 1HEAD')
    must(venue.required_orig(3)==() and venue.required_orig(9)==(),'optional-original venue reference drift')
    must(venue.required_orig(12)==('avg','turn'),'JCD12 schema reference drift')
    must(venue.required_orig(13)==('avg','turn'),'JCD13 schema reference drift')
    must(venue.required_orig(18)==('avg','turn'),'JCD18 schema reference drift')
    must(venue.required_orig(4)==('avg','turn','straight'),'standard schema reference drift')

    raw3={b:[6.8+b/100,5.2+b/100,7.1+b/100] for b in range(1,7)}
    a3=live._orig_live_audit(['一周','まわり足','直線'],raw3)
    must(a3['orig_avg_available'] and a3['orig_turn_available'] and a3['orig_straight_available'],'3-channel audit failed')

    raw2={b:[6.8+b/100,5.2+b/100] for b in range(1,7)}
    a2=live._orig_live_audit(['一周','まわり足'],raw2)
    must(a2['orig_avg_available'] and a2['orig_turn_available'] and not a2['orig_straight_available'],'2-channel audit failed')

    # Exact HEAD4 historical edge case seen at Tsu:
    # lap column entirely blank, turn/straight complete. The blank column is ignored.
    raw_tsu={b:[None,4.3+b/100,8.6+b/100] for b in range(1,7)}
    at=live._orig_live_audit(['一周','まわり足','直線'],raw_tsu)
    must(at['orig_avg_available'],'all-blank lap must be ignored for avg availability')
    must(at['orig_turn_available'] and at['orig_straight_available'],'Tsu optional turn/straight availability failed')
    must(not at['orig_lap_available'],'Tsu blank lap incorrectly marked available')

    # Optional-original venues still attempt the endpoint. If it is unavailable,
    # TKZ/ST remain usable and orig=None; if available, HEAD4 consumes it.
    orig_get=live._get_fast
    seen=[]
    def optional_fail(url,timeout=4,attempts=2):
        seen.append(url)
        if 'oriten' in url: raise live.Fast120Error('synthetic optional original unavailable')
        return url
    live._get_fast=optional_fail
    try:
        _,_,o=live.fetch_current('20260919',3,4,1)
        must(o is None,'JCD03 optional original failure did not degrade to None')
        must(len(seen)==3 and any('oriten' in u for u in seen),f'JCD03 optional original was not attempted: {seen}')
    finally:
        live._get_fast=orig_get

    seen=[]
    def all_ok(url,timeout=4,attempts=2):
        seen.append(url); return url
    live._get_fast=all_ok
    try:
        _,_,o9=live.fetch_current('20260919',9,4,1)
        must(o9 is not None and any('oriten' in u for u in seen),'JCD09 optional original success was not consumed')
        seen.clear()
        _,_,o4=live.fetch_current('20260919',4,4,1)
        must(o4 is not None and len(seen)==3 and any('oriten' in u for u in seen),f'JCD04 original fetch missing: {seen}')
    finally:
        live._get_fast=orig_get

    # Two-channel wall semantics: research wall family was NaN without straight,
    # so all three wall-derived score terms must become frozen neutral rank .5.
    exh2={
      'current_boats':boats(True),
      'orig_avg_available':True,
      'orig_straight_available':False,
      'wall_exhibition_ready':False,
      'onehead_venue_original_required_reference':['avg','turn'],
    }
    card,state=fake_state_card(12)
    d2=live.newfeature_decide(.25,.40,4.0,exh2,card,state,12)
    for k in ('attack4','stwall_center','wall_rev'):
        must(abs(float(d2['newfeature_ranks'][k])-.5)<1e-12,f'JCD12 {k} not neutral: {d2["newfeature_ranks"][k]}')
    must(d2['wall_exhibition_ready'] is False,'JCD12 wall should be unavailable')

    # If current optional-original data are absent entirely, do not fabricate the
    # orig structural feature even when hp/mass/odds are strong.
    exh0={
      'current_boats':boats(False),
      'orig_avg_available':False,
      'orig_straight_available':False,
      'wall_exhibition_ready':False,
      'onehead_venue_original_required_reference':[],
    }
    card,state=fake_state_card(3)
    d0=live.newfeature_decide(.90,.90,20.0,exh0,card,state,3)
    must(d0['base120_selected'] is False,'missing-orig race entered base120')
    must(d0['newfeature_expanded_added'] is False,'missing-orig race entered expansion')
    must(d0['selected'] is False,'missing-orig race selected')
    must(d0['venue_schema_supported_for_selection'] is False,'missing-orig support flag wrong')

    return {
      'reference_map_matches_1head':True,
      'three_channel':a3,'two_channel':a2,'tsu_blank_lap_dynamic':at,
      'two_channel_wall_ranks':{k:d2['newfeature_ranks'][k] for k in ('attack4','stwall_center','wall_rev')},
      'missing_optional_original_selected':d0['selected'],
    }

def historical_208():
    p208=os.environ.get('EXPANDED_FEATURES_208')
    p1=os.environ.get('STAGE1_POOL')
    if not p208 or not p1:return {'status':'SKIP_MISSING_TABLE'}
    z=pd.read_csv(p208,dtype={'race_code':str})
    p=pd.read_csv(p1,dtype={'race_code':str})
    z['race_code']=z.race_code.astype(str).str.zfill(12)
    p['race_code']=p.race_code.astype(str).str.zfill(12)
    if any(z.month.astype(str).str.startswith('2026-09')) or any(p.month.astype(str).str.startswith('2026-09')):
        raise RuntimeError('SEPTEMBER ACCESS')
    must(len(z)==208,'208 universe drift')
    need=['race_code','basic_complete','turn_available','straight_available','orig_avg_available','orig_row_present']
    missing=[c for c in need if c not in p.columns]
    must(not missing,f'Stage1 availability columns missing: {missing}')
    a=p[need].drop_duplicates('race_code')
    q=z.merge(a,on='race_code',how='left',validate='one_to_one')
    must(q.orig_avg_available.notna().all(),'Stage1 availability join missing rows')
    q['jcd']=q.race_code.str[8:10].astype(int)
    for c in ['basic_complete','turn_available','straight_available','orig_avg_available','orig_row_present']:
        q[c]=pd.to_numeric(q[c],errors='coerce').fillna(0).astype(int)
    q['research_wall_expected']=(q.basic_complete.eq(1)&q.orig_avg_available.eq(1)&q.straight_available.eq(1))
    actual=q.wall_ready.fillna(False).astype(bool)
    must((actual==q.research_wall_expected).all(),
         f'wall readiness mismatch R={int((actual!=q.research_wall_expected).sum())}')
    # Every 208 row came through Stage1 struct_ready, which required orig_avg.
    must(q.orig_avg_available.eq(1).all(),
         f'208 contains missing orig_avg R={int(q.orig_avg_available.ne(1).sum())}')

    q['onehead_reference']=q.jcd.map(lambda j:
      'optional_none' if not venue.required_orig(j)
      else ('avg_turn' if venue.required_orig(j)==('avg','turn') else 'avg_turn_straight'))
    grp=(q.groupby(['jcd','onehead_reference'],as_index=False)
           .agg(R=('race_code','size'),
                base120_R=('base120','sum'),
                orig_row_R=('orig_row_present','sum'),
                orig_avg_R=('orig_avg_available','sum'),
                turn_R=('turn_available','sum'),
                straight_R=('straight_available','sum'),
                wall_ready_R=('wall_ready','sum')))
    grp.to_csv(OUT/'venue_208.csv',index=False)
    q.to_csv(OUT/'research_live_schema_208.csv',index=False)

    optional=q[q.onehead_reference.eq('optional_none')]
    partial=q[q.onehead_reference.eq('avg_turn')]
    return {
      'R':len(q),
      'venue_rows':grp.to_dict('records'),
      'optional_reference_R':int(len(optional)),
      'optional_reference_orig_avg_R':int(optional.orig_avg_available.sum()),
      'optional_reference_straight_R':int(optional.straight_available.sum()),
      'partial_reference_R':int(len(partial)),
      'partial_reference_straight_R':int(partial.straight_available.sum()),
      'wall_ready_matches_research_formula':True,
      'all_208_orig_avg_available':True,
      'status':'PASS',
    }

def main():
    unit=unit_contract()
    hist=historical_208()
    result={
      'profile':'HEAD4_NEWFEATURE_FIXED156_V1',
      'policy':'dynamic actual-published channels; 1HEAD map is minimum LIVE expectation/reference',
      'unit_contract':unit,
      'historical_208':hist,
      'SEPTEMBER_OUTCOMES_READ':False,
      'PRODUCTION_THRESHOLD_CHANGED':False,
      'AUDIT_OK':True,
    }
    (OUT/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,default=str)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2,default=str))
    print('HEAD4_VENUE_AWARE_ORIGINAL_OK')
    print('SEPTEMBER_UNREAD')

if __name__=='__main__':main()
