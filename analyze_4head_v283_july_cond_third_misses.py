#!/usr/bin/env python3
"""Retrospective July conditional-THIRD miss diagnostic for frozen v283.
Reads Apr-Aug only; September remains unread. Does not modify production/frozen policy.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd

import audit_4head_86r_independent as cand
import audit_4head_86r_v283_closing_odds as audit
from head4_v291_downstream_inference import load_artifact, score_second, score_conditional_third, BOATS

OUT=Path('/tmp/head4_v283_july_third'); OUT.mkdir(parents=True,exist_ok=True)
START='2026-04-01'; END='2026-08-31'

def main():
    cx=cand.rebuild(); cx=cx[(cx.date>=START)&(cx.date<=END)].copy()
    codes=set(cx.race_code.astype(str).str.zfill(12)); assert len(cx)==164
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
        p2=score_second(sr,art)
        cr=audit.conditional_rows(g,sf,cf)
        pc=score_conditional_third(cr,art)
        crdf=pd.DataFrame(cr)
        a2,a3=actual[1],actual[2]
        sorder=sorted(BOATS,key=lambda s:(-float(p2[s]),s)); second_rank=sorder.index(a2)+1
        torder=sorted((t for t in BOATS if t!=a2),key=lambda t:(-float(pc[(a2,t)]),t)); third_rank=torder.index(a3)+1
        actual_p=float(pc[(a2,a3)]); top2_p=float(pc[(a2,torder[1])]); margin=actual_p-top2_p
        row={'date':str(g.date.iloc[0]),'month':str(g.date.iloc[0])[:7],'race_code':str(code),'actual_second':a2,'actual_third':a3,
             'second_rank':second_rank,'third_rank':third_rank,'actual_third_p':actual_p,'third_top2_boundary_p':top2_p,'p_margin_vs_top2':margin,
             'third_order':'|'.join(map(str,torder)),'second_pass':int(second_rank<=2),'third_hit':int(third_rank<=2)}
        # Preserve frozen conditional feature values for the actual s>t row.
        rr=crdf[(crdf.second_boat==a2)&(crdf.third_boat==a3)]
        assert len(rr)==1
        for f in cf: row[f]=rr.iloc[0][f]
        rec.append(row)
    r=pd.DataFrame(rec).sort_values(['date','race_code']); assert len(r)==70
    r.to_csv(OUT/'head4_70r_cond_third_detail.csv',index=False)
    passed=r[r.second_pass==1].copy(); assert len(passed)==40
    summaries=[]
    for label,g in [('Apr-Jun',passed[passed.month<='2026-06']),('July',passed[passed.month=='2026-07']),('August',passed[passed.month=='2026-08'])]:
        summaries.append({'period':label,'second_pass_R':len(g),'third_hit_R':int(g.third_hit.sum()),'third_hit_pct':100*g.third_hit.mean(),
                          'rank1':int((g.third_rank==1).sum()),'rank2':int((g.third_rank==2).sum()),'rank3':int((g.third_rank==3).sum()),'rank4':int((g.third_rank==4).sum()),
                          'miss_rank3':int(((g.third_hit==0)&(g.third_rank==3)).sum()),'miss_rank4':int(((g.third_hit==0)&(g.third_rank==4)).sum()),
                          'miss_median_margin':float(g.loc[g.third_hit==0,'p_margin_vs_top2'].median()) if (g.third_hit==0).any() else np.nan})
    pd.DataFrame(summaries).to_csv(OUT/'period_summary.csv',index=False)
    pd.crosstab([passed.month,passed.actual_second],passed.third_hit).to_csv(OUT/'by_second.csv')
    pd.crosstab([passed.month,passed.actual_third],passed.third_hit).to_csv(OUT/'by_third.csv')
    st=art['v283_COND_THIRD']; mean=np.asarray(st['scaler_mean'],float); scale=np.asarray(st['scaler_scale'],float); beta=np.asarray(st['beta'],float); med=np.asarray(st['imputer_median'],float)
    X=passed[cf].apply(pd.to_numeric,errors='coerce').to_numpy(float); X=np.where(np.isnan(X),med,X); Z=(X-mean)/scale; C=Z*beta
    groups={'AprJun_hit':(passed.month<='2026-06')&(passed.third_hit==1),'AprJun_miss':(passed.month<='2026-06')&(passed.third_hit==0),'July_hit':(passed.month=='2026-07')&(passed.third_hit==1),'July_miss':(passed.month=='2026-07')&(passed.third_hit==0),'August':passed.month=='2026-08'}
    fr=[]
    for j,f in enumerate(cf):
        q={'feature':f,'beta':float(beta[j])}
        for name,mask in groups.items():
            a=np.asarray(mask); q[name+'_zmean']=float(np.mean(Z[a,j])) if a.any() else np.nan; q[name+'_contrib_mean']=float(np.mean(C[a,j])) if a.any() else np.nan
        q['july_miss_vs_aprjun_hit_contrib_delta']=q['July_miss_contrib_mean']-q['AprJun_hit_contrib_mean']
        fr.append(q)
    fd=pd.DataFrame(fr).sort_values('july_miss_vs_aprjun_hit_contrib_delta',key=lambda s:s.abs(),ascending=False); fd.to_csv(OUT/'feature_shift.csv',index=False)
    jm=passed[(passed.month=='2026-07')&(passed.third_hit==0)].copy(); assert len(jm)==7
    jm.to_csv(OUT/'july_7_misses.csv',index=False)
    meta={'status':'RETROSPECTIVE_JULY_COND_THIRD_MISS_ANALYSIS','july_miss_R':7,'frozen_v283':'unchanged','production':'HEAD4_V291_COMP7 unchanged','formal_prospective_roi':'NOT_COMPUTABLE','september':'UNREAD','v96_used':False}
    (OUT/'meta.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
    print('HEAD4_V283_JULY_COND_THIRD_MISS_ANALYSIS_OK')
    print(pd.DataFrame(summaries).to_string(index=False))
    print('\nJULY_7_MISSES'); print(jm[['date','race_code','actual_second','actual_third','third_rank','actual_third_p','third_top2_boundary_p','p_margin_vs_top2','third_order']].to_string(index=False))
    print('\nTOP_FEATURE_SHIFTS'); print(fd[['feature','beta','July_miss_zmean','AprJun_hit_zmean','july_miss_vs_aprjun_hit_contrib_delta']].head(20).to_string(index=False))
    print('SEPTEMBER_UNREAD'); print('PRODUCTION_UNCHANGED')

if __name__=='__main__': main()
