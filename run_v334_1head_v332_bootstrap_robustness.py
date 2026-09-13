#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import json
import numpy as np
import pandas as pd
import run_v332_1head_attack_first_redesign as v332

OUT=Path('/tmp/v334'); OUT.mkdir(parents=True,exist_ok=True)
CFG={'family':'ATTACK_ENV_SOFT','env_w':0.1,'q':0.65}
MONTHS=v332.MONTHS_DEV+[v332.AUG]
SEED=33420260914
NBOOT=20000

def met(z):
    n=len(z); h=int(z.head_hit.sum()) if n else 0; e=int(z.hit.sum()) if n else 0
    return {'R':n,'head':h,'head_rate':100*h/n if n else np.nan,'exact3':e,'exact3_rate':100*e/n if n else np.nan}

def reconstruct():
    y=v332.load_all(); pp=[]; rows=[]
    for m in MONTHS:
        if m==v332.AUG: tr=y[y.month.isin(v332.MONTHS_DEV)].copy()
        else: tr=y[y.month.isin([x for x in v332.MONTHS_DEV if x!=m])].copy()
        z=y[y.month.eq(m)].copy(); p,_=v332.fit_apply(tr,z,CFG)
        pp.append(p.assign(audit_month=m)); b=met(z); q=met(p)
        rows.append({'month':m,**{f'base_{k}':v for k,v in b.items()},**{f'pass_{k}':v for k,v in q.items()},
                     'head_lift_pp':q['head_rate']-b['head_rate'],'exact3_lift_pp':q['exact3_rate']-b['exact3_rate']})
    p=pd.concat(pp,ignore_index=True)
    dev=p[p.audit_month!='2026-08']; aug=p[p.audit_month=='2026-08']
    if len(dev)!=86 or int(dev.head_hit.sum())!=76 or int(dev.hit.sum())!=41: raise AssertionError('Feb-Jul identity mismatch')
    if len(aug)!=10 or int(aug.head_hit.sum())!=7 or int(aug.hit.sum())!=4: raise AssertionError('August identity mismatch')
    if len(p)!=96: raise AssertionError('pooled PASS identity mismatch')
    return y,p,pd.DataFrame(rows)

def qs(x):
    a=np.asarray(x,float)
    return {'p2_5':float(np.quantile(a,.025)),'p50':float(np.quantile(a,.5)),'p97_5':float(np.quantile(a,.975))}

def summarize(draws):
    df=pd.DataFrame(draws)
    out={c:qs(df[c]) for c in ['pass_head_rate','pass_exact3_rate','head_lift_pp','exact3_lift_pp']}
    out.update({
        'P_head_lift_gt0':float((df.head_lift_pp>0).mean()),
        'P_exact3_lift_gt0':float((df.exact3_lift_pp>0).mean()),
        'P_both_lift_gt0':float(((df.head_lift_pp>0)&(df.exact3_lift_pp>0)).mean()),
        'P_head_lift_le_m5':float((df.head_lift_pp<=-5).mean()),
        'P_exact3_lift_le_m5':float((df.exact3_lift_pp<=-5).mean()),
    })
    return out,df

def main():
    y,p,monthly=reconstruct(); rng=np.random.default_rng(SEED)
    race_draws=[]
    grouped={m:(y[y.month.eq(m)].copy(),p[p.audit_month.eq(m)].copy()) for m in MONTHS}
    # paired race bootstrap within month; baseline and PASS sampled independently from their empirical sets, month weights fixed.
    for _ in range(NBOOT):
        br=bh=be=pr=ph=pe=0
        for m,(b,q) in grouped.items():
            bi=rng.integers(0,len(b),len(b)); qi=rng.integers(0,len(q),len(q)) if len(q) else np.array([],int)
            bs=b.iloc[bi]; qsamp=q.iloc[qi] if len(q) else q
            br+=len(bs); bh+=int(bs.head_hit.sum()); be+=int(bs.hit.sum())
            pr+=len(qsamp); ph+=int(qsamp.head_hit.sum()); pe+=int(qsamp.hit.sum())
        phr=100*ph/pr; per=100*pe/pr; bhr=100*bh/br; ber=100*be/br
        race_draws.append({'pass_head_rate':phr,'pass_exact3_rate':per,'head_lift_pp':phr-bhr,'exact3_lift_pp':per-ber})
    race_sum,race_df=summarize(race_draws)
    # month-block bootstrap using original month aggregate totals.
    md=monthly.set_index('month')
    block=[]
    for _ in range(NBOOT):
        picks=rng.choice(MONTHS,size=len(MONTHS),replace=True)
        br=bh=be=pr=ph=pe=0
        for m in picks:
            r=md.loc[m]; br+=int(r.base_R); bh+=int(r.base_head); be+=int(r.base_exact3); pr+=int(r.pass_R); ph+=int(r.pass_head); pe+=int(r.pass_exact3)
        phr=100*ph/pr; per=100*pe/pr; bhr=100*bh/br; ber=100*be/br
        block.append({'pass_head_rate':phr,'pass_exact3_rate':per,'head_lift_pp':phr-bhr,'exact3_lift_pp':per-ber})
    block_sum,block_df=summarize(block)
    # leave-one-month-out pooled summaries.
    loo=[]
    for drop in MONTHS:
        ms=[m for m in MONTHS if m!=drop]; bz=y[y.month.isin(ms)]; pz=p[p.audit_month.isin(ms)]; b=met(bz); q=met(pz)
        loo.append({'drop_month':drop,**{f'base_{k}':v for k,v in b.items()},**{f'pass_{k}':v for k,v in q.items()},
                    'head_lift_pp':q['head_rate']-b['head_rate'],'exact3_lift_pp':q['exact3_rate']-b['exact3_rate']})
    label='ROBUST_PROVISIONAL' if (block_sum['P_head_lift_gt0']>=.70 and block_sum['P_exact3_lift_gt0']>=.70 and block_sum['P_head_lift_le_m5']<=.25 and block_sum['P_exact3_lift_le_m5']<=.25) else ('FRAGILE' if (block_sum['P_head_lift_le_m5']>.50 or block_sum['P_exact3_lift_le_m5']>.50) else 'MIXED_UNCERTAIN')
    monthly.to_csv(OUT/'analysis_v334_monthly.csv',index=False); pd.DataFrame(loo).to_csv(OUT/'analysis_v334_leave_one_month_out.csv',index=False)
    race_df.to_csv(OUT/'analysis_v334_race_bootstrap.csv',index=False); block_df.to_csv(OUT/'analysis_v334_month_block_bootstrap.csv',index=False)
    result={'seed':SEED,'nboot':NBOOT,'identity':{'all_R':len(y),'pass_R':len(p),'pass_head':int(p.head_hit.sum()),'pass_exact3':int(p.hit.sum())},'race_bootstrap':race_sum,'month_block_bootstrap':block_sum,'diagnostic_label':label,'SEPTEMBER_OUTCOMES_READ':False}
    (OUT/'result_v334.json').write_text(json.dumps(result,indent=2,sort_keys=True),encoding='utf-8')
    lines=['# v334 v332 bootstrap robustness audit','',f'- identity PASS 96R / head {int(p.head_hit.sum())} / exact3 {int(p.hit.sum())}',f'- race bootstrap: {json.dumps(race_sum,sort_keys=True)}',f'- month-block bootstrap: {json.dumps(block_sum,sort_keys=True)}',f'- DIAGNOSTIC_LABEL={label}','- September outcomes unread. No retuning.']
    (OUT/'summary_v334.md').write_text('\n'.join(lines)+'\n',encoding='utf-8'); print('\n'.join(lines))
if __name__=='__main__': main()
