#!/usr/bin/env python3
"""Retrospective decomposition of frozen v283 opponent misses on Apr-Aug HEAD4 candidates.
September is not selected/read. Production and frozen v283 are unchanged.
"""
from pathlib import Path
import json
import pandas as pd

import audit_4head_86r_independent as cand
import audit_4head_86r_v283_closing_odds as audit
from head4_v291_downstream_inference import load_artifact, score_second, score_conditional_third, v283_top4, BOATS

OUT=Path('/tmp/head4_v283_miss_decomp'); OUT.mkdir(parents=True,exist_ok=True)
START='2026-04-01'; END='2026-08-31'


def main():
    cx=cand.rebuild(); cx=cx[(cx.date>=START)&(cx.date<=END)].copy()
    codes=set(cx.race_code.astype(str).str.zfill(12))
    assert len(cx)==164 and int(cx.head4.sum())==70
    d=audit.source_rows(codes)
    long=audit.build_long_all(d); art=load_artifact()
    sf=list(art['v283_SECOND']['features']); cf=list(art['v283_COND_THIRD']['features'])
    truth={str(r.race_code).zfill(12):(int(float(r.winner)),int(float(r.second)),int(float(r.third))) for _,r in d.iterrows() if str(r.get('valid_result','0')) in ('1','1.0')}
    rec=[]
    for code,g in long.groupby('race_code'):
        actual=truth.get(str(code))
        if not actual or actual[0]!=4: continue
        sr=[]
        for _,r in g.iterrows():
            x={'boat':int(r.boat)}
            for f in sf: x[f]=r[f]
            sr.append(x)
        p2=score_second(sr,art)
        cr=audit.conditional_rows(g,sf,cf); pc=score_conditional_third(cr,art)
        pairs=v283_top4(p2,pc)
        second_top2=sorted(BOATS,key=lambda s:(-float(p2[s]),s))[:2]
        a2,a3=actual[1],actual[2]
        third_top2=sorted((t for t in BOATS if t!=a2),key=lambda t:(-float(pc[(a2,t)]),t))[:2]
        second_hit=a2 in second_top2
        third_hit=a3 in third_top2
        pair_hit=(a2,a3) in pairs
        if not second_hit: miss='SECOND_MISS'
        elif not third_hit: miss='THIRD_MISS'
        elif not pair_hit: miss='PAIR_RANK_MISS'
        else: miss='CAPTURE'
        ds=str(g.date.iloc[0])
        rec.append({'date':ds,'month':ds[:7],'race_code':str(code),'actual_second':a2,'actual_third':a3,
                    'second_top2':'|'.join(map(str,second_top2)),'second_top2_hit':int(second_hit),
                    'actual_second_third_top2':'|'.join(map(str,third_top2)),'conditional_third_top2_hit':int(third_hit),
                    'final_pairs':'|'.join(f'{s}>{t}' for s,t in pairs),'final_pair_hit':int(pair_hit),'miss_stage':miss})
    r=pd.DataFrame(rec).sort_values(['date','race_code']); assert len(r)==70
    r.to_csv(OUT/'head4_70r_miss_detail.csv',index=False)
    periods=[('Apr-Jun',['2026-04','2026-05','2026-06']),('Jul-Aug',['2026-07','2026-08'])]+[(m,[m]) for m in ['2026-04','2026-05','2026-06','2026-07','2026-08']]
    rows=[]
    for name,mons in periods:
        g=r[r.month.isin(mons)]
        z={'period':name,'head4_R':len(g)}
        for k in ['CAPTURE','SECOND_MISS','THIRD_MISS','PAIR_RANK_MISS']:
            n=int((g.miss_stage==k).sum()); z[k]=n; z[k+'_pct']=100*n/len(g) if len(g) else 0
        z['second_top2_hit']=int(g.second_top2_hit.sum()); z['second_top2_hit_pct']=100*g.second_top2_hit.mean() if len(g) else 0
        z['conditional_third_top2_hit_given_second_selected']=int(((g.second_top2_hit==1)&(g.conditional_third_top2_hit==1)).sum())
        den=int(g.second_top2_hit.sum()); z['conditional_third_top2_hit_given_second_selected_pct']=100*z['conditional_third_top2_hit_given_second_selected']/den if den else 0
        rows.append(z)
    s=pd.DataFrame(rows); s.to_csv(OUT/'miss_summary.csv',index=False)
    meta={'status':'RETROSPECTIVE_V283_MISS_DECOMPOSITION','candidate_R':164,'head4_R':70,'frozen_v283':'unchanged','production':'HEAD4_V291_COMP7 unchanged','formal_prospective_roi':'NOT_COMPUTABLE','september':'UNREAD','v96_used':False}
    (OUT/'meta.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
    print('HEAD4_V283_MISS_DECOMPOSITION_OK'); print(s.to_string(index=False)); print('SEPTEMBER_UNREAD'); print('PRODUCTION_UNCHANGED')

if __name__=='__main__': main()
