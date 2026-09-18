#!/usr/bin/env python3
"""Venue-aware original exhibition audit for HEAD4 production.

Checks:
- HEAD4 venue contract exactly matches the 1HEAD v351 live probe contract.
- no-original venues do not fetch the original endpoint.
- two-channel venues neutralize the frozen wall-family ranks exactly as research did.
- no-original venues cannot enter orig-dependent base/expansion selection.
- frozen 208R universe venue composition remains consistent with the structural research universe.

No September outcomes are read.
"""
from __future__ import annotations
from pathlib import Path
import json, math, os
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
    must(venue.ORIG_REQUIRED==oneprobe.ORIG_REQUIRED,'HEAD4 venue map differs from 1HEAD')
    must(venue.required_orig(3)==() and venue.required_orig(9)==(),'no-original venue drift')
    must(venue.required_orig(12)==('avg','turn'),'JCD12 schema drift')
    must(venue.required_orig(13)==('avg','turn'),'JCD13 schema drift')
    must(venue.required_orig(18)==('avg','turn'),'JCD18 schema drift')
    must(venue.required_orig(4)==('avg','turn','straight'),'standard schema drift')

    raw3={b:[6.8+b/100,5.2+b/100,7.1+b/100] for b in range(1,7)}
    a3=live._orig_live_audit(['一周','まわり足','直線'],raw3)
    must(a3['orig_avg_available'] and a3['orig_turn_available'] and a3['orig_straight_available'],'3-channel audit failed')

    raw2={b:[6.8+b/100,5.2+b/100] for b in range(1,7)}
    a2=live._orig_live_audit(['一周','まわり足'],raw2)
    must(a2['orig_avg_available'] and a2['orig_turn_available'] and not a2['orig_straight_available'],'2-channel audit failed')

    # fetch_current must not even request the original endpoint at JCD03/09.
    orig_get=live._get_fast
    seen=[]
    def fake_get(url,timeout=4,attempts=2):
        seen.append(url); return url
    live._get_fast=fake_get
    try:
        t,s,o=live.fetch_current('20260919',3,4,1)
        must(o is None,'JCD03 unexpectedly fetched original')
        must(len(seen)==2 and not any('oriten' in u for u in seen),f'JCD03 fetch set wrong: {seen}')
        seen.clear()
        t,s,o=live.fetch_current('20260919',4,4,1)
        must(o is not None and len(seen)==3 and any('oriten' in u for u in seen),f'JCD04 original fetch missing: {seen}')
    finally:
        live._get_fast=orig_get

    # JCD12/13/18 research wall family is unavailable without straight:
    # all three frozen wall-derived score terms must land on neutral rank .5.
    exh2={
      'current_boats':boats(True),
      'orig_avg_available':True,
      'orig_straight_available':False,
      'wall_exhibition_ready':False,
      'venue_original_required':['avg','turn'],
    }
    card,state=fake_state_card(12)
    d2=live.newfeature_decide(.25,.40,4.0,exh2,card,state,12)
    for k in ('attack4','stwall_center','wall_rev'):
        must(abs(float(d2['newfeature_ranks'][k])-.5)<1e-12,f'JCD12 {k} not neutral: {d2["newfeature_ranks"][k]}')
    must(d2['wall_exhibition_ready'] is False,'JCD12 wall should be unavailable')

    # JCD03/09 have no orig_avg structural feature in the research universe.
    # Strong hp/mass/odds must not fabricate a selectable row.
    exh0={
      'current_boats':boats(False),
      'orig_avg_available':False,
      'orig_straight_available':False,
      'wall_exhibition_ready':False,
      'venue_original_required':[],
    }
    card,state=fake_state_card(3)
    d0=live.newfeature_decide(.90,.90,20.0,exh0,card,state,3)
    must(d0['base120_selected'] is False,'no-original venue entered base120')
    must(d0['newfeature_expanded_added'] is False,'no-original venue entered expansion')
    must(d0['selected'] is False,'no-original venue selected')
    must(d0['venue_schema_supported_for_selection'] is False,'no-original venue support flag wrong')

    return {'map_matches_1head':True,'three_channel':a3,'two_channel':a2,
            'two_channel_wall_ranks':{k:d2['newfeature_ranks'][k] for k in ('attack4','stwall_center','wall_rev')},
            'no_original_selected':d0['selected']}

def historical_208():
    p=os.environ.get('EXPANDED_FEATURES_208')
    if not p:return {'status':'SKIP_NO_TABLE'}
    z=pd.read_csv(p,dtype={'race_code':str})
    z['race_code']=z.race_code.astype(str).str.zfill(12)
    if any(z.month.astype(str).str.startswith('2026-09')):raise RuntimeError('SEPTEMBER ACCESS')
    must(len(z)==208,'208 universe drift')
    z['jcd']=z.race_code.str[8:10].astype(int)
    z['schema_class']=z.jcd.map(lambda j:'none' if not venue.required_orig(j) else ('avg_turn' if venue.required_orig(j)==('avg','turn') else 'avg_turn_straight'))
    grp=(z.groupby(['jcd','schema_class'],as_index=False)
           .agg(R=('race_code','size'),base120_R=('base120','sum'),wall_ready_R=('wall_ready','sum')))
    none=z[z.schema_class.eq('none')]
    # Structural 208R was built with orig_avg_available, so no-original venues must be absent.
    must(len(none)==0,f'no-original venue unexpectedly present in structural208: {none.race_code.tolist()[:10]}')
    two=z[z.schema_class.eq('avg_turn')]
    # Research wall audit required straight + avg; partial-schema venues must have no wall-ready rows.
    must(int(two.wall_ready.sum())==0,f'partial-schema wall-ready drift: {int(two.wall_ready.sum())}')
    grp.to_csv(OUT/'venue_208.csv',index=False)
    return {
      'R':len(z),
      'venue_rows':grp.to_dict('records'),
      'no_original_R':int(len(none)),
      'avg_turn_R':int(len(two)),
      'avg_turn_wall_ready_R':int(two.wall_ready.sum()),
      'status':'PASS',
    }

def main():
    unit=unit_contract()
    hist=historical_208()
    result={
      'profile':'HEAD4_NEWFEATURE_FIXED156_V1',
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
