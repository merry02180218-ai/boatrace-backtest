#!/usr/bin/env python3
"""Retrospective frozen-v283 rescue / close-margin ticket expansion study.
Apr-Jun is threshold-development; Jul-Aug is holdout confirmation. September is never read.
Production/frozen v283 are not modified.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd

import audit_4head_86r_independent as cand
import audit_4head_86r_v283_closing_odds as audit
from head4_v291_downstream_inference import load_artifact, score_second, score_conditional_third, BOATS

OUT=Path('/tmp/head4_v283_rescue_margin'); OUT.mkdir(parents=True,exist_ok=True)
START='2026-04-01'; END='2026-08-31'
GAPS=[0.01,0.02,0.03,0.04,0.05,0.075,0.10]

def main():
    cx=cand.rebuild(); cx=cx[(cx.date>=START)&(cx.date<=END)].copy(); assert len(cx)==164
    codes=set(cx.race_code.astype(str).str.zfill(12))
    d=audit.source_rows(codes); long=audit.build_long_all(d); art=load_artifact()
    sf=list(art['v283_SECOND']['features']); cf=list(art['v283_COND_THIRD']['features'])
    truth={str(r.race_code).zfill(12):(int(float(r.winner)),int(float(r.second)),int(float(r.third))) for _,r in d.iterrows() if str(r.get('valid_result','0')) in ('1','1.0')}
    rec=[]
    for code,g in long.groupby('race_code'):
        actual=truth.get(str(code))
        if not actual or actual[0]!=4: continue
        sr=[]
        for _,r in g.iterrows():
            x={'boat':int(r.boat)}; x.update({f:r[f] for f in sf}); sr.append(x)
        p2=score_second(sr,art); cr=audit.conditional_rows(g,sf,cf); pc=score_conditional_third(cr,art)
        a2,a3=actual[1],actual[2]
        sorder=sorted(BOATS,key=lambda s:(-float(p2[s]),s)); second_pass=a2 in sorder[:2]
        if not second_pass: continue
        torder=sorted((t for t in BOATS if t!=a2),key=lambda t:(-float(pc[(a2,t)]),t))
        gap23=float(pc[(a2,torder[1])]-pc[(a2,torder[2])])
        base_hit=a3 in torder[:2]
        rec.append({'date':str(g.date.iloc[0]),'month':str(g.date.iloc[0])[:7],'race_code':str(code),'actual_second':a2,'actual_third':a3,
                    'third_rank':torder.index(a3)+1,'third_order':'|'.join(map(str,torder)),'gap23':gap23,'base_hit':int(base_hit),
                    'rank3_rescuable':int((not base_hit) and torder.index(a3)==2)})
    r=pd.DataFrame(rec).sort_values(['date','race_code']); assert len(r)==40
    r.to_csv(OUT/'second_pass_40r.csv',index=False)

    rows=[]
    for gap in GAPS:
        for period,mask in [('Apr-Jun',r.month<='2026-06'),('Jul-Aug',r.month>='2026-07'),('July',r.month=='2026-07'),('August',r.month=='2026-08'),('Apr-Aug',pd.Series(True,index=r.index))]:
            q=r[mask].copy(); fire=q.gap23<=gap
            expanded_hit=(q.base_hit.eq(1) | (fire & q.third_rank.eq(3)))
            rows.append({'gap_threshold':gap,'period':period,'R':len(q),'base_hits':int(q.base_hit.sum()),'fire_R':int(fire.sum()),
                         'rank3_rescued_R':int((fire & q.rank3_rescuable.eq(1)).sum()),'expanded_hits':int(expanded_hit.sum()),
                         'capture_pct':100*expanded_hit.mean() if len(q) else np.nan,
                         'extra_third_candidates':int(fire.sum()),
                         'extra_ticket_count_if_both_second_branches_expand':int(2*fire.sum())})
    s=pd.DataFrame(rows); s.to_csv(OUT/'gap_scan_capture.csv',index=False)

    # Development-only choice: smallest threshold with best Apr-Jun rescued-per-fire rate, tie by more rescues then smaller gap.
    dev=s[s.period=='Apr-Jun'].copy(); dev['precision']=dev.rank3_rescued_R/dev.fire_R.replace(0,np.nan)
    dev=dev.sort_values(['precision','rank3_rescued_R','gap_threshold'],ascending=[False,False,True])
    chosen=float(dev.iloc[0].gap_threshold)
    chosen_table=s[s.gap_threshold==chosen].copy(); chosen_table.to_csv(OUT/'chosen_gap_holdout.csv',index=False)

    meta={'status':'RETROSPECTIVE_RESCUE_CLOSE_MARGIN_CAPTURE_STUDY','chosen_gap_from_apr_jun_only':chosen,
          'note':'Capture/cost structure first. Exact closing-odds ROI requires pair-level odds replay and is a separate diagnostic.',
          'production':'HEAD4_V291_COMP7 unchanged','frozen_v283':'unchanged','formal_prospective_roi':'NOT_COMPUTABLE','september':'UNREAD','v96_used':False}
    (OUT/'meta.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
    print('HEAD4_V283_RESCUE_CLOSE_MARGIN_SCAN_OK')
    print('\nAPR_JUN_DEVELOPMENT'); print(s[s.period=='Apr-Jun'].to_string(index=False))
    print('\nCHOSEN_HOLDOUT'); print(chosen_table.to_string(index=False))
    print('\nJULY_RANK3_MISSES'); print(r[(r.month=='2026-07')&(r.third_rank==3)][['date','race_code','actual_second','actual_third','gap23','third_order']].to_string(index=False))
    print('SEPTEMBER_UNREAD'); print('PRODUCTION_UNCHANGED')

if __name__=='__main__': main()
