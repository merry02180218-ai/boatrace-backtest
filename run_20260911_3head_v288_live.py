#!/usr/bin/env python3
"""Fast cached 3-head v288 deadline scorer for 2026-09-11.

Pipeline in one process after the morning cache exists:
Boatcast exhibition/start/original -> official odds3t 120/120 -> v243 final
-> v288 S/A/B -> v242 Top5..10 -> exactly 10,000 yen Dutch.
No result/payout endpoint is requested.
"""
from __future__ import annotations
import argparse, hashlib, json, re, time
from datetime import datetime, timezone, timedelta
import joblib
import numpy as np
import pandas as pd
import requests

import analyze_v242_3head_target_comp3_min5_max10 as v242
import analyze_v234_3head_waku10_restored_replay as v234
import backtest_v51_lane_corrected_tickets as v51
import fetch_live_trifecta_odds as live

JST=timezone(timedelta(hours=9))
CACHE='cache_20260911_3head_v288_live.joblib'
KEEP=-0.1999999999999999
RESCUE=0.5672342857142857
S_WAKU_MAX=0.4999999999999999
S_ST_MIN=-0.6
S_MEET_MAX=0.861111111111111
A_ST_MIN=0.6
A_WALL_MAX=0.24875
B_MOTOR_MIN=0.22388571428571424
B_NST_MAX=-0.0714285714285712


def get_text(url):
    r=requests.get(url,headers={'User-Agent':'Mozilla/5.0'},timeout=12)
    r.raise_for_status()
    return r.content.decode('utf-8',errors='replace')

def fl(x):
    try:return float(str(x).strip().replace('F','-').replace('L',''))
    except:return None

def parse_tkz(body,code):
    lines=[x for x in body.splitlines() if x.strip()]
    if len(lines)<8 or not lines[0].startswith('data='):raise RuntimeError('Boatcast tkz incomplete')
    q={'レースコード':code}
    for b,row in enumerate(lines[2:8],1):
        c=row.split('\t');q[f'艇{b}_展示タイム']=c[1] if len(c)>1 else ''
        q[f'艇{b}_チルト']=c[6].replace(' ','') if len(c)>6 else ''
    return {code:q}

def parse_stt(body,code):
    lines=[x for x in body.splitlines() if x.strip()]
    if len(lines)<8 or not lines[0].startswith('data='):raise RuntimeError('Boatcast stt incomplete')
    q={'レースコード':code}
    for row in lines[2:8]:
        c=row.split('\t')
        if len(c)<5:continue
        b=int(c[1]); val=c[4].strip(); flag=c[5].strip() if len(c)>5 else ''
        if flag=='F' and val and not val.startswith('-'): val='-'+val.lstrip('.') if False else '-0'+val.lstrip('0')
        # Existing feature code accepts signed numeric ST. F.05 means -0.05.
        if flag=='F': val='-'+val.lstrip('.').rjust(2,'0') if False else str(-abs(float(val)))
        elif flag=='L': val=str(abs(float(val)))
        q[f'艇{b}_スタート展示']=val
    return {code:q}

def parse_orig(body,code):
    lines=[x for x in body.splitlines() if x.strip()]
    if len(lines)<9 or not lines[0].startswith('data='):raise RuntimeError('Boatcast original exhibition incomplete')
    meta=lines[1].split('\t'); n=int(meta[1]) if len(meta)>1 and meta[1].isdigit() else 0
    labels=lines[2].split('\t')[:n];q={'レースコード':code}
    for k,label in enumerate(labels,1):q[f'計測項目{k}']=label.replace('　','').strip()
    for row in lines[3:9]:
        c=row.split('\t'); b=int(c[0])
        for k in range(1,n+1):q[f'艇{b}_値{k}']=c[k+1] if len(c)>k+1 else ''
    return {code:q}

def fetch_direct(date,jcd,rno,code):
    jo=f'{jcd:02d}';rr=f'{rno:02d}'
    urls={
      'tkz':f'https://race.boatcast.jp/hp_txt/{jo}/bc_j_tkz_{date}_{jo}_{rr}.txt',
      'stt':f'https://race.boatcast.jp/hp_txt/{jo}/bc_j_stt_{date}_{jo}_{rr}.txt',
      'orig':f'https://race.boatcast.jp/txt/{jo}/bc_oriten_{date}_{jo}_{rr}.txt'}
    bodies={k:get_text(u) for k,u in urls.items()}
    return parse_tkz(bodies['tkz'],code),parse_stt(bodies['stt'],code),parse_orig(bodies['orig'],code),{
      k:hashlib.sha256(v.encode('utf-8')).hexdigest() for k,v in bodies.items()}

def update_current_features(r,tkz,stt,orig,stbias):
    r=r.copy();code=str(r['race_code']).zfill(12)
    ex,st,os=v51.corrected_direct(code,tkz,stt,orig,stbias)
    tr=tkz[code]
    for b in range(1,7):
        r[f'c_b{b}_ex']=ex[b];r[f'c_b{b}_st']=st[b]
        r[f'c_b{b}_lap']=os[b]['lap'];r[f'c_b{b}_turn']=os[b]['turn']
        r[f'c_b{b}_straight']=os[b]['straight'];r[f'c_b{b}_origavg']=os[b]['avg']
        try:r[f'c_b{b}_tilt']=float(str(tr.get(f'艇{b}_チルト','0')).replace('+',''))
        except:r[f'c_b{b}_tilt']=0.0
    mets=['ex','st','lap','turn','straight','origavg','motor','wr','waku_wr','nst','waku_st','waku_sr','pastwin','meetst']
    for met in mets:
        vals=[float(r[f'c_b{b}_{met}']) for b in range(1,7)]
        r[f'c_{met}_spread']=max(vals)-min(vals);r[f'c_{met}_sd']=float(np.std(vals))
        for b in [1,2,4,5,6]:r[f'c_b3_minus_b{b}_{met}']=float(r[f'c_b3_{met}'])-float(r[f'c_b{b}_{met}'])
        r[f'c_b3_inside_{met}']=float(r[f'c_b3_{met}'])-max(float(r[f'c_b1_{met}']),float(r[f'c_b2_{met}']))
        r[f'c_b3_outside_{met}']=float(r[f'c_b3_{met}'])-max(float(r[f'c_b4_{met}']),float(r[f'c_b5_{met}']),float(r[f'c_b6_{met}']))
    r['c_wall12_weak']=.30*(1-r['c_b1_waku_wr'])+.30*(1-r['c_b2_waku_wr'])+.20*r['c_b3_minus_b2_st']+.20*r['c_b3_minus_b2_straight']
    r['c_attack3_stretch']=.28*r['c_b3_ex']+.28*r['c_b3_st']+.24*r['c_b3_straight']+.20*r['c_b3_motor']
    r['c_attack3_turn']=.18*r['c_b3_ex']+.20*r['c_b3_st']+.27*r['c_b3_turn']+.20*r['c_b3_lap']+.15*r['c_b3_motor']
    r['c_outer_follow']=max(.35*r[f'c_b{b}_st']+.30*r[f'c_b{b}_straight']+.20*r[f'c_b{b}_motor']+.15*r[f'c_b{b}_wr'] for b in [4,5,6])
    return r

def fetch_odds(date,jcd,rno):
    params={'rno':rno,'jcd':f'{jcd:02d}','hd':date}
    resp=live.safe_get(live.BASE,params);html=resp.text; parsed=live.parse_odds(html)
    if set(parsed)!=live.expected_combos() or len(parsed)!=120:raise RuntimeError(f'odds incomplete: {len(parsed)}')
    return {f'{a}-{b}-{c}':float(o) for (a,b,c),o in parsed.items()},{'url':resp.url,'count':120,'sha256':hashlib.sha256(html.encode('utf-8',errors='replace')).hexdigest()}

def dutch(ts,vals):
    stakes=np.asarray(v234.v205.round_dutch(vals,10000),int)
    if int(stakes.sum())!=10000:raise RuntimeError('Dutch total != 10000')
    return [{'combo':q,'odds':float(o),'stake':int(s)} for q,o,s in zip(ts,vals,stakes) if s>0]

def deadline_state(deadline):
    if not deadline:return 'UNSPECIFIED'
    now=datetime.now(JST);dl=datetime.fromisoformat(deadline)
    if dl.tzinfo is None:dl=dl.replace(tzinfo=JST)
    return 'LIVE' if now<dl else 'RETROSPECTIVE_ONLY'

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--jcd',type=int,required=True);ap.add_argument('--race',type=int,required=True)
    ap.add_argument('--date',default='20260911');ap.add_argument('--cache',default=CACHE);ap.add_argument('--deadline-jst')
    args=ap.parse_args();t0=time.perf_counter();z=joblib.load(args.cache)
    code=f'{args.date}{args.jcd:02d}{args.race:02d}'
    pc=z['pre_candidates'].get(code)
    if not pc:
        print(json.dumps({'race_code':code,'decision':'NO_BET','reason':'not PRE S/A candidate'},ensure_ascii=False));return
    q=z['current_rows'];q=q[q.race_code.astype(str).str.zfill(12)==code]
    if len(q)!=1:raise RuntimeError(f'cached current row count={len(q)}')
    tkz,stt,orig,direct_sha=fetch_direct(args.date,args.jcd,args.race,code)
    r=update_current_features(q.iloc[0],tkz,stt,orig,z['st_bias'])
    hfs=z['head_features'];cats=z['head_cats']
    X=pd.DataFrame([r])
    for c in hfs:X[c]=pd.to_numeric(X[c],errors='coerce')
    p3=float(z['head_model'].predict_proba(X[hfs+cats])[:,1][0])
    ts=v242.safe_order(r,z['pair_model'])
    if ts is None:raise RuntimeError('pair-rank-invalid')
    odds,odmeta=fetch_odds(args.date,args.jcd,args.race);ch=v242.choose_n(ts,odds)
    raw_n=ch.get('raw_n');top_n=ch.get('top_n');comp=ch.get('comp_odds');action=ch.get('action')
    minus=float(r['c_b3_minus_b5_st']);attack=float(r['c_attack3_stretch'])
    buyable=action=='bet';base=bool(buyable and p3>=.45 and raw_n is not None and 7<=raw_n<=18 and comp is not None and 3.05<=comp<=4.0)
    keep=minus>=KEEP;rescue=attack<=RESCUE
    v243=bool(buyable and ((base and keep) or ((not base) and rescue)))
    S=bool(r['c_b3_minus_b4_waku_st']<=S_WAKU_MAX and r['c_b3_minus_b4_st']>=S_ST_MIN and r['c_b3_meetst']<=S_MEET_MAX)
    A=bool(r['c_b3_minus_b4_st']>=A_ST_MIN and r['c_wall12_weak']<=A_WALL_MAX)
    B=bool(r['c_b3_minus_b2_motor']>=B_MOTOR_MIN and r['c_b3_inside_nst']<=B_NST_MAX)
    route='S' if S else ('A' if A else ('B' if B else None))
    final=bool(v243 and route)
    tickets=[]
    if final:
        vals=[float(odds[x]) for x in ts[:int(top_n)]];tickets=dutch(ts[:int(top_n)],vals)
    obj={'race_code':code,'deadline_state':deadline_state(args.deadline_jst),'pre':pc,'p3':p3,'v242_action':action,
      'raw_top_n':raw_n,'raw_comp_odds':ch.get('raw_comp'),'top_n':top_n,'comp_odds':comp,
      'v243':{'base':base,'minus_b5_st':minus,'keep':keep,'attack3_stretch':attack,'rescue':rescue,'pass':v243},
      'v288':{'route':route,'S':S,'A':A,'B':B,'b3_minus_b4_waku_st':float(r['c_b3_minus_b4_waku_st']),
       'b3_minus_b4_st':float(r['c_b3_minus_b4_st']),'b3_meetst':float(r['c_b3_meetst']),'wall12_weak':float(r['c_wall12_weak']),
       'b3_minus_b2_motor':float(r['c_b3_minus_b2_motor']),'b3_inside_nst':float(r['c_b3_inside_nst'])},
      'decision':'BET' if final else 'NO_BET','tickets':tickets,'total_stake':sum(x['stake'] for x in tickets),
      'direct_sha256':direct_sha,'odds':odmeta,'result_or_payout_used':False,'seconds':time.perf_counter()-t0}
    print(json.dumps(obj,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
