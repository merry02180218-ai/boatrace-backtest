#!/usr/bin/env python3
"""Retrospective closing-odds diagnostic for the fixed HEAD4 86R/78R candidate.

This is deliberately NOT a prospective ROI audit. It replays the frozen v283
opponent artifact on Apr-Aug pre-result features and prices the four fixed
4-s-t tickets with official closing displayed trifecta odds. September is never
selected or consumed. Production policy is not changed.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd

import audit_4head_86r_independent as cand
import analyze_v96_4corner_monthly_walkforward_tiebreak as c4
import analyze_v221_3head_scenario_pair as v221
import analyze_v264_4head_feature_exhaustive as v264
import analyze_v274_4head_opponent_feature_audit as v274
import analyze_v278_4head_opponent_current_exhibition_audit as v278
import analyze_v279_4head_opponent_listwise_rebuild as v279
import analyze_v282_4head_conditional_third as v282
from head4_v291_downstream_inference import load_artifact, score_second, score_conditional_third, v283_top4, BOATS

ROOT=Path(__file__).resolve().parent
OUT=Path('/tmp/head4_v283_closing'); OUT.mkdir(parents=True,exist_ok=True)
START='2026-04-01'; END='2026-08-31'
STAKE_PER_TICKET=100


def source_rows(codes):
    # analysis_v93 is the frozen historical feature table used by the v279/v282
    # lineage. Its research horizon is Jan-Aug 2026. Fail closed if that contract
    # has changed rather than permitting September into this diagnostic.
    rs=c4.read()
    dates=[str(r.get('date','')) for r in rs]
    if any(d>END for d in dates if d):
        raise RuntimeError('SEPTEMBER_OR_LATER_PRESENT_IN_V93_SOURCE_ABORT')
    d=pd.DataFrame(rs)
    d['race_code']=d.race_code.astype(str).str.zfill(12)
    d=d[d.race_code.isin(codes)].copy()
    d['date']=d.date.astype(str)
    d=d[(d.date>=START)&(d.date<=END)].copy()
    d=v221.build(d,'date')
    return d


def build_long_all(d):
    specs=v274.feature_specs(d); rec=[]
    for _,r in d.iterrows():
        base={'date':str(r.get('date','')),'race_code':str(r.get('race_code','')).zfill(12),'month':str(r.get('date',''))[:7]}
        for b in BOATS:
            z=dict(base); z['boat']=b
            for n,s in specs.items(): z[n]=v274.fval(r,b,s)
            rec.append(z)
    z=pd.DataFrame(rec)
    z=v278.add_current(z)
    relseed=[c for c in list(v279.ABILITY)+list(v279.PLAYER)+list(v279.PRIOR_HINTS)+list(v279.START_HINTS)+list(v279.POSITION)+list(v279.CURRENT) if c in z]
    z=v279.add_relative(z,relseed)
    return z


def conditional_rows(g, second_features, cond_features):
    by={int(r.boat):r for _,r in g.iterrows()}; out=[]
    # Exact feature construction from v282.make_pairs, but label-free.
    tbase=[c for c in second_features if c in g.columns]
    scenario=[c for c in g.columns if c.startswith('is_boat') or c in ('is_inner123','is_outer56','is_inner_edge3','is_outer_edge5','h4_attack','h4_turning') or '__vs4' in c or '__abs4' in c or c.startswith('h4_attack_x_')]
    for s in BOATS:
        sr=by[s]
        for t in BOATS:
            if t==s: continue
            tr=by[t]; r={'second_boat':s,'third_boat':t}
            for c in tbase: r[f't_{c}']=tr.get(c,np.nan)
            for c in scenario: r[f't_{c}']=tr.get(c,np.nan)
            r['pair_same_side4']=float((s<4 and t<4) or (s>4 and t>4))
            r['pair_second_inner']=float(s<4); r['pair_second_outer']=float(s>4)
            r['pair_third_inner']=float(t<4); r['pair_third_outer']=float(t>4)
            r['pair_adjacent']=float(abs(t-s)==1); r['pair_distance']=float(abs(t-s)); r['pair_third_minus_second']=float(t-s)
            for b in BOATS: r[f'pair_second_is{b}']=float(s==b)
            for c in v282.PAIR_KEYS:
                if c in g.columns:
                    tv=pd.to_numeric(pd.Series([tr.get(c,np.nan)]),errors='coerce').iloc[0]
                    sv=pd.to_numeric(pd.Series([sr.get(c,np.nan)]),errors='coerce').iloc[0]
                    r[f'diff_{c}']=tv-sv if pd.notna(tv) and pd.notna(sv) else np.nan
                    r[f'prod_{c}']=tv*sv if pd.notna(tv) and pd.notna(sv) else np.nan
            # Frozen scorer requires every frozen key to exist; absent-but-valid
            # historical values are represented as NaN and use frozen imputation.
            for c in cond_features: r.setdefault(c,np.nan)
            out.append(r)
    return out


def odds_for_date(ds):
    p=ROOT/'data'/'official_closing_odds3t'/ds[:4]/ds[5:7]/(ds[8:10]+'.csv')
    if not p.is_file(): return pd.DataFrame()
    q=pd.read_csv(p,dtype={'jcd':str,'rno':str})
    if 'source_type' in q: q=q[q.source_type.astype(str)=='official_closing']
    if 'snapshot_type' in q: q=q[q.snapshot_type.astype(str)=='closing_displayed']
    q['jcd']=q.jcd.astype(str).str.zfill(2); q['rno']=q.rno.astype(str).str.zfill(2)
    q['race_code']=ds.replace('-','')+q.jcd+q.rno
    return q


def main():
    cx=cand.rebuild(); cx=cx[(cx.date>=START)&(cx.date<=END)].copy(); codes=set(cx.race_code.astype(str).str.zfill(12))
    assert len(cx)==164 and int(cx.head4.sum())==70
    d=source_rows(codes)
    if set(d.race_code)!=codes: raise RuntimeError(f'feature source coverage mismatch {len(set(d.race_code))}/{len(codes)}')
    long=build_long_all(d); art=load_artifact()
    sf=list(art['v283_SECOND']['features']); cf=list(art['v283_COND_THIRD']['features'])
    rec=[]
    odds_cache={}
    truth={str(r.race_code).zfill(12):(int(float(r.winner)),int(float(r.second)),int(float(r.third))) for _,r in d.iterrows() if str(r.get('valid_result','0')) in ('1','1.0')}
    for code,g in long.groupby('race_code'):
        if len(g)!=5: continue
        sr=[]
        for _,r in g.iterrows():
            x={'boat':int(r.boat)}
            for f in sf: x[f]=r.get(f,np.nan)
            sr.append(x)
        p2=score_second(sr,art); cr=conditional_rows(g,sf,cf); pc=score_conditional_third(cr,art); pairs=v283_top4(p2,pc)
        ds=str(g.date.iloc[0]); oq=odds_cache.setdefault(ds,odds_for_date(ds)); oo=oq[oq.race_code.astype(str)==str(code)] if len(oq) else oq
        covered=len(oo)==1
        actual=truth.get(str(code)); hit_pair=(actual[1],actual[2]) if actual and actual[0]==4 else None
        hit=bool(hit_pair in pairs) if covered else False
        odd=np.nan
        if hit:
            col=f'4-{hit_pair[0]}-{hit_pair[1]}'; odd=pd.to_numeric(oo.iloc[0].get(col),errors='coerce')
        payout=float(odd*STAKE_PER_TICKET) if hit and pd.notna(odd) else 0.0
        rec.append({'date':ds,'month':ds[:7],'race_code':str(code),'pairs':'|'.join(f'4-{s}-{t}' for s,t in pairs),'odds_covered':int(covered),'head4':int(actual is not None and actual[0]==4),'hit':int(hit and pd.notna(odd)),'hit_odds':odd,'stake_yen':4*STAKE_PER_TICKET if covered else 0,'payout_yen':payout})
    r=pd.DataFrame(rec); r.to_csv(OUT/'race_detail.csv',index=False)
    if len(r)!=164: raise RuntimeError(f'v283 replay coverage mismatch {len(r)}/164')
    periods=[(m,[m]) for m in ['2026-04','2026-05','2026-06','2026-07','2026-08']]+[('Apr-Jun',['2026-04','2026-05','2026-06']),('Jul-Aug',['2026-07','2026-08']),('Apr-Aug',['2026-04','2026-05','2026-06','2026-07','2026-08'])]
    out=[]
    for name,mons in periods:
        g=r[r.month.isin(mons)]; cov=g[g.odds_covered==1]; stake=float(cov.stake_yen.sum()); pay=float(cov.payout_yen.sum())
        out.append({'period':name,'candidate_R':len(g),'head4_R':int(g.head4.sum()),'covered_R':len(cov),'coverage_pct':100*len(cov)/len(g) if len(g) else np.nan,'hits':int(cov.hit.sum()),'hit_rate_candidate_pct':100*cov.hit.sum()/len(g) if len(g) else np.nan,'stake_yen':stake,'payout_yen':pay,'profit_yen':pay-stake,'roi_pct':100*pay/stake if stake else np.nan,'status':'RETROSPECTIVE_CLOSING_ODDS_DIAGNOSTIC'})
    s=pd.DataFrame(out); s.to_csv(OUT/'roi_summary.csv',index=False)
    meta={'status':'RETROSPECTIVE_CLOSING_ODDS_DIAGNOSTIC','candidate':'HEAD4_86R_ORIGAVG_RESEARCH','opponent':'frozen v283 PLAYER_START + COND_BASE TOP2XTOP2 alpha2=.60 Top4','stake_per_ticket_yen':100,'formal_prospective_roi':'NOT_COMPUTABLE','odds_source':'official_closing/closing_displayed','september':'UNREAD','v96_used':False,'production':'HEAD4_V291_COMP7 unchanged'}
    (OUT/'meta.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
    print('HEAD4_V283_CLOSING_ODDS_DIAGNOSTIC_OK'); print(s.to_string(index=False)); print('FORMAL_PROSPECTIVE_ROI_NOT_COMPUTABLE'); print('SEPTEMBER_UNREAD'); print('PRODUCTION_UNCHANGED')

if __name__=='__main__': main()
