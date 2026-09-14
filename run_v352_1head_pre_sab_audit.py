#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import json
import os
import pandas as pd

import onehead_production_profile as prod
import run_v337_1head_head_cutoff_volume as v337

OUT=Path('/tmp/v352-pre-sab-audit'); OUT.mkdir(parents=True,exist_ok=True)
DEV=('2026-02','2026-03','2026-04','2026-05','2026-06')
SUP=('2026-07','2026-08')
FROZEN=Path(os.environ.get('V351_FROZEN_RACES','/tmp/v351-fixed/v351_production_races.csv'))


def rank(v: float) -> str:
    if v >= .82: return 'S'
    if v >= .80: return 'A'
    if v >= .78: return 'B'
    return 'OUT'


def stats(pre, final, months):
    p=pre[pre.month.isin(months)].copy()
    f=final[final.month.isin(months)].copy()
    out=[]
    for r in ('S','A','B'):
        pp=p[p.pre_rank.eq(r)]
        ff=f[f.pre_rank.eq(r)]
        out.append({
            'rank':r,
            'pre_R':len(pp),
            'post_v351_PASS_R':len(ff),
            'post_PASS_rate':len(ff)/len(pp) if len(pp) else None,
            'post_drop_R':len(pp)-len(ff),
            'post_drop_rate':(len(pp)-len(ff))/len(pp) if len(pp) else None,
            'HEAD':int(ff.head_hit.sum()),
            'HEAD_rate':float(ff.head_hit.mean()) if len(ff) else None,
            'EXACT3':int(ff.hit.sum()),
            'EXACT3_rate':float(ff.hit.mean()) if len(ff) else None,
        })
    return out


def main():
    if not prod.SEPTEMBER_OUTCOMES_MUST_REMAIN_UNREAD:
        raise AssertionError('September guard disabled')
    if prod.JUL_AUG_STATUS!='NON_PRISTINE_SUPPORT_ONLY':
        raise AssertionError('Jul-Aug status drift')
    if float(prod.HEAD_CUTOFF)!=.78:
        raise AssertionError('production HEAD cutoff drift')
    if not FROZEN.exists():
        raise FileNotFoundError(f'missing frozen v351 production races: {FROZEN}')

    # PRE p_head is determined before the exhibition model. Rebuilding exhibition
    # here is unnecessary and was the source of the very slow first v352 run.
    base=v337.load_candidate_base().copy()
    v337.validate_no_sep(base)
    base['race_code']=base.race_code.astype(str).str.zfill(12)
    base['p_head']=pd.to_numeric(base.p_head,errors='coerce')
    pre=base[base.p_head.ge(prod.HEAD_CUTOFF)].copy()
    pre['pre_rank']=pre.p_head.map(rank)
    if (pre.pre_rank=='OUT').any():
        raise AssertionError('OUT rank leaked into cutoff .78 universe')
    if len(pre)!=1114:
        raise AssertionError(f'production PRE volume drift pre={len(pre)}')

    # The final 276-race identity and v351 HEAD/EXACT3 outcomes come from the
    # already independently audited v351 production-regression artifact.
    frozen=pd.read_csv(FROZEN,dtype={'race_code':str})
    frozen['race_code']=frozen.race_code.astype(str).str.zfill(12)
    frozen['month']=frozen.month.astype(str)
    frozen['head_hit']=pd.to_numeric(frozen.head_hit,errors='raise').astype(int)
    frozen['hit']=pd.to_numeric(frozen.hit,errors='raise').astype(int)
    ranks=pre[['race_code','p_head','pre_rank']].copy()
    final=frozen.merge(ranks,on='race_code',how='left',validate='one_to_one')
    if final.pre_rank.isna().any():
        raise AssertionError(f'frozen PASS outside PRE universe: {int(final.pre_rank.isna().sum())}')
    if len(final)!=276 or int(final.hit.sum())!=131 or int(final.head_hit.sum())!=241:
        raise AssertionError('v351 frozen production sentinel drift')

    result={
        'profile':prod.PROFILE_NAME,
        'thresholds':{'S':'>=.82','A':'>=.80 and <.82','B':'>=.78 and <.80'},
        'all_Feb_Aug':stats(pre,final,DEV+SUP),
        'Feb_Jun_pristine':stats(pre,final,DEV),
        'Jul_Aug_support_only':stats(pre,final,SUP),
        'totals':{'pre_R':len(pre),'post_v351_PASS_R':len(final),'HEAD':int(final.head_hit.sum()),'EXACT3':int(final.hit.sum())},
        'audit_source':'PRE p_head from frozen candidate base; final 276 from independent v351 production-regression artifact 10371394695',
        'SEPTEMBER_OUTCOMES_READ':False,
        'JUL_AUG_STATUS':prod.JUL_AUG_STATUS,
        'PRODUCTION_CHANGED':False,
    }
    (OUT/'result_v352_pre_sab_audit.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    pd.DataFrame(result['all_Feb_Aug']).to_csv(OUT/'v352_sab_all.csv',index=False)
    pd.DataFrame(result['Feb_Jun_pristine']).to_csv(OUT/'v352_sab_pristine.csv',index=False)
    pd.DataFrame(result['Jul_Aug_support_only']).to_csv(OUT/'v352_sab_support.csv',index=False)
    final[['month','race_code','p_head','pre_rank','head_hit','hit']].to_csv(OUT/'v352_final_ranked_races.csv',index=False)
    print(json.dumps(result,indent=2),flush=True)

if __name__=='__main__': main()
