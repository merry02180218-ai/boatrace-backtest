#!/usr/bin/env python3
from pathlib import Path
import json
import pandas as pd
import run_v332_1head_attack_first_redesign as v332

OUT=Path('/tmp/v337_anchor_diag'); OUT.mkdir(parents=True,exist_ok=True)
MONTHS=v332.MONTHS_DEV+[v332.AUG]
CFG={'family':'ATTACK_ENV_SOFT','env_w':0.1,'q':0.65}

def met(z):
    n=len(z); return {'R':n,'head':int(z.head_hit.sum()) if n else 0,'exact3':int(z.hit.sum()) if n else 0}

def main():
    y=v332.load_all().copy()
    y['race_code']=y.race_code.astype(str).str.zfill(12)
    selected=[]; monthly=[]
    for m in MONTHS:
        # Match adopted v332/v336 semantics exactly:
        # Feb-Jul = leave-one-out within Feb-Jul only; Aug = train on all Feb-Jul.
        if m==v332.AUG:
            tr=y[y.month.isin(v332.MONTHS_DEV)].copy()
        else:
            tr=y[y.month.isin([x for x in v332.MONTHS_DEV if x!=m])].copy()
        te=y[y.month.eq(m)].copy()
        p,pars=v332.fit_apply(tr,te,CFG)
        p=p.copy(); p['eval_month']=m; selected.append(p)
        monthly.append({'month':m,**met(p),'threshold':pars.get('threshold')})
    s=pd.concat(selected,ignore_index=True)
    anchor=met(s)
    y.to_csv(OUT/'canonical_v332_base400.csv',index=False)
    s.to_csv(OUT/'canonical_v332_q65_pass.csv',index=False)
    pd.DataFrame(monthly).to_csv(OUT/'canonical_v332_q65_monthly.csv',index=False)
    result={'base':met(y),'anchor':anchor,'monthly':monthly,'SEPTEMBER_OUTCOMES_READ':False}
    (OUT/'result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))
    assert anchor=={'R':96,'head':83,'exact3':45}, f'canonical anchor drift: {anchor}'

if __name__=='__main__': main()
