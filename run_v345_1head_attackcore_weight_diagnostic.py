#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import json

import numpy as np
import pandas as pd

import onehead_production_profile as prod
import run_v337_1head_head_cutoff_volume as v337
import run_v340_1head_adaptive_odds_dutch as v340

OUT = Path('/tmp/v345out')
OUT.mkdir(parents=True, exist_ok=True)
RACE = Path('/tmp/v345/race_level.csv')
PRISTINE = ['2026-02','2026-03','2026-04','2026-05','2026-06']
BROAD_MIN = 2.20
BROAD_MAX = 3.00
COMP = ['one_ex','one_st','one_straight','one_orig_avg']
CURRENT = (0.30,0.30,0.23,0.17)


def corr(a: pd.Series, b: pd.Series) -> float | None:
    z = pd.concat([pd.to_numeric(a, errors='coerce'), pd.to_numeric(b, errors='coerce')], axis=1).dropna()
    if len(z) < 8 or z.iloc[:,0].nunique() < 3 or z.iloc[:,1].nunique() < 2:
        return None
    return float(z.iloc[:,0].corr(z.iloc[:,1], method='spearman'))


def grid05():
    # nonnegative weights in 0.05 steps summing exactly to 1.0
    for a in range(21):
        for b in range(21-a):
            for c in range(21-a-b):
                d = 20-a-b-c
                yield (a/20.0,b/20.0,c/20.0,d/20.0)


def score(df: pd.DataFrame, w: tuple[float,float,float,float]) -> pd.Series:
    return sum(float(x) * pd.to_numeric(df[c], errors='coerce') for x,c in zip(w,COMP))


def eval_weights(df: pd.DataFrame, w: tuple[float,float,float,float], label: str) -> dict:
    z = df.copy()
    z['s'] = score(z,w)
    full_hit = corr(z.s,z.baseline_hit)
    full_ret = corr(z.s,z.return_multiple)
    folds=[]
    for m in PRISTINE:
        q=z[z.month.ne(m)].copy()
        folds.append({
            'excluded_month':m,
            'R':len(q),
            'hit_corr':corr(q.s,q.baseline_hit),
            'return_corr':corr(q.s,q.return_multiple),
        })
    hc=[x['hit_corr'] for x in folds if x['hit_corr'] is not None]
    rc=[x['return_corr'] for x in folds if x['return_corr'] is not None]
    return {
        'label':label,
        'w_ex':w[0],'w_st':w[1],'w_straight':w[2],'w_orig_avg':w[3],
        'R':len(z),
        'full_hit_corr':full_hit,'full_return_corr':full_ret,
        'lomo_hit_min':min(hc) if hc else None,
        'lomo_hit_median':float(np.median(hc)) if hc else None,
        'lomo_hit_max':max(hc) if hc else None,
        'lomo_return_min':min(rc) if rc else None,
        'lomo_return_median':float(np.median(rc)) if rc else None,
        'lomo_return_max':max(rc) if rc else None,
        'lomo_hit_all_positive':bool(hc) and all(x>0 for x in hc),
        'lomo_return_all_positive':bool(rc) and all(x>0 for x in rc),
        'robust_floor':min(min(hc),min(rc)) if hc and rc else None,
        'robust_median':float(np.mean([np.median(hc),np.median(rc)])) if hc and rc else None,
        'folds':folds,
    }


def main() -> None:
    if not prod.SEPTEMBER_OUTCOMES_MUST_REMAIN_UNREAD:
        raise AssertionError('September outcomes permitted')

    race=pd.read_csv(RACE,dtype={'race_code':str})
    race.race_code=race.race_code.astype(str).str.zfill(12)
    assert len(race)==prod.EXPECTED_PASS_R
    assert int(race.head_hit.sum())==prod.EXPECTED_HEAD
    assert int(race.baseline_hit.sum())==prod.EXPECTED_EXACT3
    assert not race.month.astype(str).str.startswith('2026-09').any()

    base=v337.load_candidate_base()
    y,_,_=v337.build_exhibition(base)
    v337.validate_no_sep(y)
    _,selected,_,_=v337.eval_cut(y,prod.HEAD_CUTOFF)
    selected.race_code=selected.race_code.astype(str).str.zfill(12)
    got=(len(selected),int(selected.head_hit.sum()),int(selected.hit.sum()),v340.identity_hash(selected))
    exp=(prod.EXPECTED_PASS_R,prod.EXPECTED_HEAD,prod.EXPECTED_EXACT3,prod.EXPECTED_PASS_ID_SHA256)
    if got!=exp:
        raise AssertionError(f'production identity drift got={got} expected={exp}')

    feat=selected[['month','race_code']+COMP].drop_duplicates('race_code')
    d=race.merge(feat,on=['month','race_code'],how='left',validate='one_to_one')
    d['return_multiple']=d.baseline_return_yen/d.baseline_stake_yen
    pr=d[d.month.isin(PRISTINE)].copy()
    broad=pr[(pr.top3_combined>=BROAD_MIN)&(pr.top3_combined<BROAD_MAX)].copy()
    broad=broad.dropna(subset=COMP).copy()

    rows=[]
    fold_rows=[]

    current=eval_weights(broad,CURRENT,'current_exact')
    rows.append({k:v for k,v in current.items() if k!='folds'})
    for f in current['folds']:
        fold_rows.append({'label':'current_exact',**{k:current[k] for k in ['w_ex','w_st','w_straight','w_orig_avg']},**f})

    seen={CURRENT}
    for w in grid05():
        if w in seen: continue
        seen.add(w)
        r=eval_weights(broad,w,'grid05')
        rows.append({k:v for k,v in r.items() if k!='folds'})
        for f in r['folds']:
            fold_rows.append({'label':'grid05',**{k:r[k] for k in ['w_ex','w_st','w_straight','w_orig_avg']},**f})

    tab=pd.DataFrame(rows)
    folds=pd.DataFrame(fold_rows)
    tab['distance_from_current']=np.sqrt(
        (tab.w_ex-CURRENT[0])**2+(tab.w_st-CURRENT[1])**2+
        (tab.w_straight-CURRENT[2])**2+(tab.w_orig_avg-CURRENT[3])**2
    )
    stable=tab[tab.lomo_hit_all_positive & tab.lomo_return_all_positive].copy()
    stable=stable.sort_values(['robust_floor','robust_median','full_return_corr','full_hit_corr'],ascending=False)
    top=stable.head(50).copy()

    refs=[]
    for name,w in [
        ('EX_ONLY',(1.0,0.0,0.0,0.0)),
        ('ST_ONLY',(0.0,1.0,0.0,0.0)),
        ('STRAIGHT_ONLY',(0.0,0.0,1.0,0.0)),
        ('ORIGAVG_ONLY',(0.0,0.0,0.0,1.0)),
        ('EQUAL',(0.25,0.25,0.25,0.25)),
        ('CURRENT',CURRENT),
    ]:
        r=eval_weights(broad,w,name)
        refs.append({k:v for k,v in r.items() if k!='folds'})

    tab.to_csv(OUT/'weight_grid_all.csv',index=False)
    folds.to_csv(OUT/'weight_grid_lomo.csv',index=False)
    top.to_csv(OUT/'weight_grid_top_stable.csv',index=False)
    pd.DataFrame(refs).to_csv(OUT/'reference_formulas.csv',index=False)
    broad[['month','race_code','baseline_hit','return_multiple']+COMP].to_csv(OUT/'diagnostic_rows.csv',index=False)

    current_row=tab[tab.label.eq('current_exact')].iloc[0].to_dict()
    best_row=top.iloc[0].to_dict() if len(top) else None
    result={
        'production_identity':{'R':got[0],'head':got[1],'exact3_top3':got[2],'sha256':got[3]},
        'scope':{'months':PRISTINE,'combined_min':BROAD_MIN,'combined_max_exclusive':BROAD_MAX,'R':len(broad)},
        'grid':{'step':0.05,'n_formulas':len(tab),'n_all_positive_lomo':len(stable)},
        'current':current_row,
        'best_by_robust_floor':best_row,
        'production_modified':False,
        'SEPTEMBER_OUTCOMES_READ':False,
    }
    (OUT/'result_v345.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2,default=str),flush=True)

if __name__=='__main__':
    main()
