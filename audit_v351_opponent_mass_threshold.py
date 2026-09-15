#!/usr/bin/env python3
"""Audit the PRE opponent-mass cutoff for the 1-head stack.

Historical outcomes are hard limited to race_code < 20260901.  This does not
read September results/payouts.  HEAD is held at the production 0.78 threshold;
only opponent-mass thresholds are compared.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
import analyze_v298_1head_threat_listwise_trifecta5 as v298
import run_v300_1head_trifecta3_feature_upgrade as v300
import run_v310_1head_opponent_headrisk_second as v310
import run_v311_1head_opponent_second_family_autoresearch as v311
import run_v312_1head_opponent_outer_gate as v312
import run_v317_1head_opponent_error_features as v317
import run_v318_1head_opponent_third_rebuild as v318
import run_v321_1head_julaug_nonpristine_validation as v321
import run_v299_1head_trifecta3_policy_search as v299
import run_v323_1head_frozen_live_adapter as live
import onehead_production_profile as prod

CUTS=[.30,.325,.35,.375,.40,.425,.45]
MONTHS=['2026-02','2026-03','2026-04','2026-05','2026-06']

def combo(x):
    p=str(x).replace('>','-').split('-')
    return tuple(map(int,p[:3])) if len(p)>=3 and all(z.isdigit() for z in p[:3]) else None

def main():
    slim=pd.read_csv(live.PREP_SLIM,dtype={'race_code':str})
    slim.race_code=slim.race_code.astype(str).str.zfill(12)
    slim=slim[slim.race_code.str[:8]<'20260901'].copy()
    if 'month' not in slim: slim['month']=slim.race_code.str[:4]+'-'+slim.race_code.str[4:6]
    hp=pd.read_csv(live.DEV_PRED,dtype={'race_code':str})
    hp.race_code=hp.race_code.astype(str).str.zfill(12)
    hp=hp[hp.race_code.str[:8]<'20260901'].copy()
    pcol='p_head'
    if pcol not in hp: raise RuntimeError('DEV prediction file lacks p_head')
    hmap=hp.drop_duplicates('race_code').set_index('race_code')[pcol].to_dict()
    v300.setup_v298(); sufs=v298.suffixes(slim)
    sl=v300.augment_second(v298.second_long(slim,sufs))
    _,p3,p4=v312.load_cache(); sx,_=v317.add_engineered(v310.add_headrisk(sl,p3,p4),'OUTER')
    cl0=None
    rows=[]
    for mon in MONTHS:
        base_p2,_=v300.p2_predict(sl,mon,10.0,False)
        p2,_=v311.p2_predict_explicit(sx,mon,1.0,None,{'START'})
        if cl0 is None: cl0=v300.augment_third(v321._third_fold_long(slim,sufs,mon))
        else: cl0=v300.augment_third(v321._third_fold_long(slim,sufs,mon))
        base_pc,_=v300.pc_predict(cl0,mon,.3,False)
        pc,_=v318.pc_predict(cl0,mon,.1,'DROP_START')
        q=slim[slim.month.astype(str).eq(mon)].drop_duplicates('race_code')
        for _,r in q.iterrows():
            code=str(r.race_code).zfill(12)
            if code not in hmap or code not in base_p2 or code not in base_pc or code not in p2 or code not in pc: continue
            ph=float(hmap[code])
            if not np.isfinite(ph) or ph<prod.HEAD_CUTOFF: continue
            mass=float(v300.base5(base_p2[code],base_pc[code])[1])
            probs=v299.pair_prob(p2[code],pc[code],prod.TICKET_ALPHA)
            top=v299.STRATEGIES['HYBRID'](p2[code],pc[code],probs)[:3]
            tickets=[(1,int(s),int(t)) for s,t in top]
            a=combo(r.get('actual_combo',''))
            hh=int(a is not None and a[0]==1)
            exact=int(a in tickets) if a else 0
            rows.append({'month':mon,'race_code':code,'jcd':int(code[8:10]),'race':int(code[10:12]),'p_head':ph,'opp_mass':mass,'head_hit':hh,'exact3':exact,'actual_combo':'-'.join(map(str,a)) if a else '', 'tickets':';'.join('-'.join(map(str,t)) for t in tickets)})
    z=pd.DataFrame(rows).sort_values('race_code')
    if z.empty: raise RuntimeError('no audit rows')
    z.to_csv('analysis_v351_opponent_mass_threshold_rows.csv',index=False,encoding='utf-8-sig')
    out=[]
    for cut in CUTS:
        q=z[z.opp_mass>=cut]
        out.append({'scope':'ALL','cut':cut,'R':len(q),'HEAD':int(q.head_hit.sum()),'HEAD_rate':100*q.head_hit.mean() if len(q) else np.nan,'EXACT3':int(q.exact3.sum()),'EXACT3_rate':100*q.exact3.mean() if len(q) else np.nan})
        for mon,g in z.groupby('month'):
            qq=g[g.opp_mass>=cut]
            out.append({'scope':mon,'cut':cut,'R':len(qq),'HEAD':int(qq.head_hit.sum()),'HEAD_rate':100*qq.head_hit.mean() if len(qq) else np.nan,'EXACT3':int(qq.exact3.sum()),'EXACT3_rate':100*qq.exact3.mean() if len(qq) else np.nan})
    s=pd.DataFrame(out);s.to_csv('analysis_v351_opponent_mass_threshold_summary.csv',index=False,encoding='utf-8-sig')
    bands=[]
    for lo,hi in zip(CUTS[:-1],CUTS[1:]):
        q=z[(z.opp_mass>=lo)&(z.opp_mass<hi)]
        bands.append({'band':f'[{lo:.3f},{hi:.3f})','R':len(q),'HEAD':int(q.head_hit.sum()),'HEAD_rate':100*q.head_hit.mean() if len(q) else np.nan,'EXACT3':int(q.exact3.sum()),'EXACT3_rate':100*q.exact3.mean() if len(q) else np.nan})
    b=pd.DataFrame(bands);b.to_csv('analysis_v351_opponent_mass_bands.csv',index=False,encoding='utf-8-sig')
    print('SEPTEMBER_OUTCOMES_USED False')
    print('PRODUCTION_CHANGED False')
    print('HEAD_CUTOFF',prod.HEAD_CUTOFF,'CURRENT_MASS_CUT',prod.OPPONENT_MASS_MIN,'AUDIT_R',len(z))
    print('\nTHRESHOLDS')
    print(s[s.scope.eq('ALL')].to_string(index=False))
    print('\nBANDS')
    print(b.to_string(index=False))
if __name__=='__main__': main()
