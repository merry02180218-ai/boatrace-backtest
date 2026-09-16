#!/usr/bin/env python3
"""Retrospective closing-odds diagnostic for the fixed HEAD4 candidate.
Default audit remains Apr-Aug. September is never selected or consumed.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import audit_4head_86r_independent as cand
import analyze_v221_3head_scenario_pair as v221
import analyze_v274_4head_opponent_feature_audit as v274
import analyze_v278_4head_opponent_current_exhibition_audit as v278
import analyze_v279_4head_opponent_listwise_rebuild as v279
import analyze_v281_4head_opponent_third_scenario as v281
import analyze_v282_4head_conditional_third as v282
from head4_v291_downstream_inference import load_artifact, score_second, score_conditional_third, v283_top4, BOATS
ROOT=Path(__file__).resolve().parent
OUT=Path('/tmp/head4_v283_closing'); OUT.mkdir(parents=True,exist_ok=True)
START='2026-04-01'; END='2026-08-31'; STAKE_PER_TICKET=100

def source_rows(codes,start=START,end=END):
    if str(end)>='2026-09-01': raise RuntimeError('September outcome access blocked')
    p=ROOT/'analysis_v93_4corner_second_third.csv'; d=pd.read_csv(p)
    if 'date' not in d or 'race_code' not in d: raise RuntimeError('V93_SOURCE_CONTRACT_MISSING_DATE_OR_RACE_CODE')
    d['date']=d.date.astype(str)
    # Source is allowed to contain later rows, but this function must never select September.
    d['race_code']=d.race_code.astype(str).str.zfill(12)
    d=d[d.race_code.isin(codes)].copy(); d=d[(d.date>=start)&(d.date<=end)].copy()
    if len(d) and (d.date.min()<start or d.date.max()>end): raise RuntimeError('V93_WINDOW_ESCAPE')
    d=v221.build(d,'date'); return d

def build_long_all(d):
    specs=v274.feature_specs(d); rec=[]
    for _,r in d.iterrows():
        base={'date':str(r.get('date','')),'race_code':str(r.get('race_code','')).zfill(12),'month':str(r.get('date',''))[:7]}
        for b in BOATS:
            z=dict(base); z['boat']=b
            for n,s in specs.items(): z[n]=v274.fval(r,b,s)
            rec.append(z)
    z=pd.DataFrame(rec); z=v278.add_current(z); z=v281.add_scenario(z)
    relseed=[c for c in list(v279.ABILITY)+list(v279.PLAYER)+list(v279.PRIOR_HINTS)+list(v279.START_HINTS)+list(v279.POSITION)+list(v279.CURRENT) if c in z]
    return v279.add_relative(z,relseed)

def conditional_rows(g, second_features, cond_features):
    by={int(r.boat):r for _,r in g.iterrows()}; out=[]; tbase=[c for c in second_features if c in g.columns]
    scenario=[c for c in g.columns if c.startswith('is_boat') or c in ('is_inner123','is_outer56','is_inner_edge3','is_outer_edge5','h4_attack','h4_turning') or '__vs4' in c or '__abs4' in c or c.startswith('h4_attack_x_')]
    for s in BOATS:
        sr=by[s]
        for t in BOATS:
            if t==s: continue
            tr=by[t]; r={'second_boat':s,'third_boat':t}
            for c in tbase:r[f't_{c}']=tr.get(c,np.nan)
            for c in scenario:r[f't_{c}']=tr.get(c,np.nan)
            r['pair_same_side4']=float((s<4 and t<4) or (s>4 and t>4)); r['pair_second_inner']=float(s<4); r['pair_second_outer']=float(s>4); r['pair_third_inner']=float(t<4); r['pair_third_outer']=float(t>4); r['pair_adjacent']=float(abs(t-s)==1); r['pair_distance']=float(abs(t-s)); r['pair_third_minus_second']=float(t-s)
            for b in BOATS:r[f'pair_second_is{b}']=float(s==b)
            for c in v282.PAIR_KEYS:
                if c in g.columns:
                    tv=pd.to_numeric(pd.Series([tr.get(c,np.nan)]),errors='coerce').iloc[0]; sv=pd.to_numeric(pd.Series([sr.get(c,np.nan)]),errors='coerce').iloc[0]
                    r[f'diff_{c}']=tv-sv if pd.notna(tv) and pd.notna(sv) else np.nan; r[f'prod_{c}']=tv*sv if pd.notna(tv) and pd.notna(sv) else np.nan
            missing=[c for c in cond_features if c not in r]
            if missing: raise RuntimeError(f'FROZEN_COND_FEATURE_MISSING:{missing[:5]}')
            out.append(r)
    return out

def odds_for_date(ds):
    if str(ds)>='2026-09-01': raise RuntimeError('September odds access blocked')
    p=ROOT/'data'/'official_closing_odds3t'/ds[:4]/ds[5:7]/(ds[8:10]+'.csv')
    if not p.is_file(): return pd.DataFrame()
    q=pd.read_csv(p,dtype={'jcd':str,'rno':str})
    if 'source_type' in q:q=q[q.source_type.astype(str)=='official_closing']
    if 'snapshot_type' in q:q=q[q.snapshot_type.astype(str)=='closing_displayed']
    q['jcd']=q.jcd.astype(str).str.zfill(2); q['rno']=q.rno.astype(str).str.zfill(2); q['race_code']=ds.replace('-','')+q.jcd+q.rno
    return q

def main():
    cx=cand.rebuild(); cx=cx[(cx.date>=START)&(cx.date<=END)].copy(); codes=set(cx.race_code.astype(str).str.zfill(12)); assert len(cx)==164 and int(cx.head4.sum())==70
    d=source_rows(codes); 
    if set(d.race_code)!=codes: raise RuntimeError(f'feature source coverage mismatch {len(set(d.race_code))}/{len(codes)}')
    long=build_long_all(d); art=load_artifact(); sf=list(art['v283_SECOND']['features']); cf=list(art['v283_COND_THIRD']['features']); rec=[]; odds_cache={}
    truth={str(r.race_code).zfill(12):(int(float(r.winner)),int(float(r.second)),int(float(r.third))) for _,r in d.iterrows() if str(r.get('valid_result','0')) in ('1','1.0')}
    for code,g in long.groupby('race_code'):
        sr=[]
        for _,r in g.iterrows(): x={'boat':int(r.boat)}; x.update({f:r[f] for f in sf}); sr.append(x)
        p2=score_second(sr,art); pc=score_conditional_third(conditional_rows(g,sf,cf),art); pairs=v283_top4(p2,pc); ds=str(g.date.iloc[0]); oq=odds_cache.setdefault(ds,odds_for_date(ds)); oo=oq[oq.race_code.astype(str)==str(code)] if len(oq) else oq; covered=len(oo)==1; actual=truth.get(str(code)); hp=(actual[1],actual[2]) if actual and actual[0]==4 else None; hit=bool(covered and hp in pairs); odd=pd.to_numeric(oo.iloc[0].get(f'4-{hp[0]}-{hp[1]}'),errors='coerce') if hit else np.nan; pay=float(odd*STAKE_PER_TICKET) if hit and pd.notna(odd) else 0
        rec.append({'date':ds,'month':ds[:7],'race_code':str(code),'odds_covered':int(covered),'head4':int(actual is not None and actual[0]==4),'hit':int(hit and pd.notna(odd)),'stake_yen':4*STAKE_PER_TICKET if covered else 0,'payout_yen':pay})
    r=pd.DataFrame(rec); r.to_csv(OUT/'race_detail.csv',index=False); print('HEAD4_V283_CLOSING_ODDS_DIAGNOSTIC_OK',len(r)); print('SEPTEMBER_UNREAD')
if __name__=='__main__':main()
