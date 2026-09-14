#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import json
import pandas as pd

import onehead_production_profile as prod
import run_v337_1head_head_cutoff_volume as v337
import run_v346_1head_v345_production_regression as v346
import run_v347_1head_opponent_attackcore as legacy

OUT=Path('/tmp/v352-pre-sab-audit'); OUT.mkdir(parents=True,exist_ok=True)
DEV=('2026-02','2026-03','2026-04','2026-05','2026-06')
SUP=('2026-07','2026-08')


def rank(v: float) -> str:
    if v >= .82: return 'S'
    if v >= .80: return 'A'
    if v >= .78: return 'B'
    return 'OUT'


def stats(pre, final, tickets, months):
    p=pre[pre.month.isin(months)].copy()
    f=final[final.month.isin(months)].copy()
    t=tickets[tickets.month.isin(months)].copy()
    out=[]
    for r in ('S','A','B'):
        pp=p[p.pre_rank.eq(r)]; ff=f[f.pre_rank.eq(r)]; tt=t[t.pre_rank.eq(r)]
        out.append({
            'rank':r,
            'pre_R':len(pp),
            'post_v351_PASS_R':len(ff),
            'post_PASS_rate':len(ff)/len(pp) if len(pp) else None,
            'post_drop_R':len(pp)-len(ff),
            'post_drop_rate':(len(pp)-len(ff))/len(pp) if len(pp) else None,
            'HEAD':int(tt.head_hit.sum()),
            'HEAD_rate':float(tt.head_hit.mean()) if len(tt) else None,
            'EXACT3':int(tt.hit.sum()),
            'EXACT3_rate':float(tt.hit.mean()) if len(tt) else None,
        })
    return out


def main():
    if not prod.SEPTEMBER_OUTCOMES_MUST_REMAIN_UNREAD:
        raise AssertionError('September guard disabled')
    if prod.JUL_AUG_STATUS!='NON_PRISTINE_SUPPORT_ONLY':
        raise AssertionError('Jul-Aug status drift')
    if float(prod.HEAD_CUTOFF)!=.78:
        raise AssertionError('production HEAD cutoff drift')

    base=v337.load_candidate_base()
    all_y,_,_=v337.build_exhibition(base)
    v337.validate_no_sep(all_y)
    y=v346.apply_v345_attack_core(all_y)
    pre,sel,_,_=v337.eval_cut(y,prod.HEAD_CUTOFF)
    pre=pre.copy(); sel=sel.copy()
    pre['pre_rank']=pd.to_numeric(pre.p_head,errors='coerce').map(rank)
    sel['pre_rank']=pd.to_numeric(sel.p_head,errors='coerce').map(rank)
    if (pre.pre_rank=='OUT').any() or (sel.pre_rank=='OUT').any():
        raise AssertionError('OUT rank leaked into cutoff .78 universe')
    if len(pre)!=1114 or len(sel)!=276:
        raise AssertionError(f'production volume drift pre={len(pre)} pass={len(sel)}')

    ids=set(sel.race_code.astype(str).str.zfill(12))
    p2dev,pcdev,p2ja,pcja=legacy.opponent_maps()
    cores=legacy.build_opponent_attackcore(ids)
    tz,_,_=legacy.evaluate(sel,cores,p2dev,pcdev,p2ja,pcja,float(prod.OPPONENT_CORE_SECOND_G2),float(prod.OPPONENT_CORE_THIRD_G3))
    ranks=sel[['race_code','pre_rank']].copy(); ranks.race_code=ranks.race_code.astype(str).str.zfill(12)
    tz=tz.merge(ranks,on='race_code',how='left',validate='one_to_one')
    if len(tz)!=276 or int(tz.hit.sum())!=131 or int(tz.head_hit.sum())!=241:
        raise AssertionError('v351 ticket sentinel drift')

    result={
        'profile':prod.PROFILE_NAME,
        'thresholds':{'S':'>=.82','A':'>=.80 and <.82','B':'>=.78 and <.80'},
        'all_Feb_Aug':stats(pre,sel,tz,DEV+SUP),
        'Feb_Jun_pristine':stats(pre,sel,tz,DEV),
        'Jul_Aug_support_only':stats(pre,sel,tz,SUP),
        'totals':{'pre_R':len(pre),'post_v351_PASS_R':len(sel),'HEAD':int(tz.head_hit.sum()),'EXACT3':int(tz.hit.sum())},
        'SEPTEMBER_OUTCOMES_READ':False,
        'JUL_AUG_STATUS':prod.JUL_AUG_STATUS,
        'PRODUCTION_CHANGED':False,
    }
    (OUT/'result_v352_pre_sab_audit.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    pd.DataFrame(result['all_Feb_Aug']).to_csv(OUT/'v352_sab_all.csv',index=False)
    pd.DataFrame(result['Feb_Jun_pristine']).to_csv(OUT/'v352_sab_pristine.csv',index=False)
    pd.DataFrame(result['Jul_Aug_support_only']).to_csv(OUT/'v352_sab_support.csv',index=False)
    print(json.dumps(result,indent=2),flush=True)

if __name__=='__main__': main()
