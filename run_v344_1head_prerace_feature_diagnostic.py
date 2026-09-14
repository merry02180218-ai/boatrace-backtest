#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import json
import math

import numpy as np
import pandas as pd

import onehead_production_profile as prod
import run_v337_1head_head_cutoff_volume as v337
import run_v340_1head_adaptive_odds_dutch as v340

OUT = Path('/tmp/v344out')
OUT.mkdir(parents=True, exist_ok=True)
RACE = Path('/tmp/v344/race_level.csv')
PRISTINE = ['2026-02','2026-03','2026-04','2026-05','2026-06']
BROAD_MIN = 2.20
BROAD_MAX = 3.00
FEATURES = [
    'p_head','opp_mass','attack_core','env_pair',
    'one_ex','one_st','one_straight','one_orig_avg',
    'sec_ex_mean_margin','sec_st_mean_margin',
    'third_turn_mean_margin','third_straight_mean_margin',
]


def safe_corr(a: pd.Series, b: pd.Series) -> float | None:
    z = pd.concat([pd.to_numeric(a, errors='coerce'), pd.to_numeric(b, errors='coerce')], axis=1).dropna()
    if len(z) < 8 or z.iloc[:,0].nunique() < 3 or z.iloc[:,1].nunique() < 2:
        return None
    return float(z.iloc[:,0].corr(z.iloc[:,1], method='spearman'))


def roi(g: pd.DataFrame) -> float | None:
    st = float(g.baseline_stake_yen.sum())
    return 100.0 * float(g.baseline_return_yen.sum()) / st if st else None


def feature_quintiles(df: pd.DataFrame, feature: str) -> list[dict]:
    x = df[['month','race_code','baseline_hit','baseline_stake_yen','baseline_return_yen',feature]].copy()
    x[feature] = pd.to_numeric(x[feature], errors='coerce')
    x = x.dropna(subset=[feature])
    if len(x) < 20 or x[feature].nunique() < 5:
        return []
    try:
        x['bucket'] = pd.qcut(x[feature], 5, labels=False, duplicates='drop')
    except ValueError:
        return []
    out=[]
    for b,g in x.groupby('bucket', observed=True):
        out.append({
            'feature': feature,
            'bucket': int(b),
            'R': len(g),
            'feature_min': float(g[feature].min()),
            'feature_max': float(g[feature].max()),
            'feature_mean': float(g[feature].mean()),
            'hits': int(g.baseline_hit.sum()),
            'hit_rate_pct': 100.0*float(g.baseline_hit.mean()),
            'roi_pct': roi(g),
            'profit_yen': float(g.baseline_return_yen.sum()-g.baseline_stake_yen.sum()),
        })
    return out


def main() -> None:
    if not prod.SEPTEMBER_OUTCOMES_MUST_REMAIN_UNREAD:
        raise AssertionError('September outcomes permitted')

    race = pd.read_csv(RACE, dtype={'race_code':str})
    race.race_code = race.race_code.astype(str).str.zfill(12)
    assert len(race) == prod.EXPECTED_PASS_R
    assert int(race.head_hit.sum()) == prod.EXPECTED_HEAD
    assert int(race.baseline_hit.sum()) == prod.EXPECTED_EXACT3
    assert not race.month.astype(str).str.startswith('2026-09').any()

    base = v337.load_candidate_base()
    y, _, _ = v337.build_exhibition(base)
    v337.validate_no_sep(y)
    _, selected, _, _ = v337.eval_cut(y, prod.HEAD_CUTOFF)
    selected.race_code = selected.race_code.astype(str).str.zfill(12)
    got = (len(selected), int(selected.head_hit.sum()), int(selected.hit.sum()), v340.identity_hash(selected))
    exp = (prod.EXPECTED_PASS_R, prod.EXPECTED_HEAD, prod.EXPECTED_EXACT3, prod.EXPECTED_PASS_ID_SHA256)
    if got != exp:
        raise AssertionError(f'production identity drift got={got} expected={exp}')

    keep = ['month','race_code'] + [c for c in FEATURES if c in selected.columns]
    feat = selected[keep].drop_duplicates('race_code')
    d = race.merge(feat, on=['month','race_code'], how='left', validate='one_to_one')
    d['return_multiple'] = d.baseline_return_yen / d.baseline_stake_yen
    d['profit_yen_top3'] = d.baseline_return_yen - d.baseline_stake_yen

    pr = d[d.month.isin(PRISTINE)].copy()
    broad = pr[(pr.top3_combined >= BROAD_MIN) & (pr.top3_combined < BROAD_MAX)].copy()
    broad_all = d[(d.top3_combined >= BROAD_MIN) & (d.top3_combined < BROAD_MAX)].copy()

    summary=[]
    lomo=[]
    quant=[]
    for f in [c for c in FEATURES if c in broad.columns]:
        x = pd.to_numeric(broad[f], errors='coerce')
        valid = broad[x.notna()].copy()
        if len(valid) < 12:
            continue
        summary.append({
            'feature': f,
            'R': len(valid),
            'spearman_hit': safe_corr(valid[f], valid.baseline_hit),
            'spearman_return_multiple': safe_corr(valid[f], valid.return_multiple),
            'mean_hit': float(valid.loc[valid.baseline_hit.eq(1),f].mean()) if valid.baseline_hit.eq(1).any() else None,
            'mean_miss': float(valid.loc[valid.baseline_hit.eq(0),f].mean()) if valid.baseline_hit.eq(0).any() else None,
        })
        quant += feature_quintiles(broad, f)
        for m in PRISTINE:
            z = broad[broad.month.ne(m)].copy()
            lomo.append({
                'feature': f,
                'excluded_month': m,
                'R': int(pd.to_numeric(z[f], errors='coerce').notna().sum()),
                'spearman_hit': safe_corr(z[f], z.baseline_hit),
                'spearman_return_multiple': safe_corr(z[f], z.return_multiple),
            })

    sm = pd.DataFrame(summary)
    lm = pd.DataFrame(lomo)
    qt = pd.DataFrame(quant)
    sm.to_csv(OUT/'feature_association_summary.csv', index=False)
    lm.to_csv(OUT/'feature_association_lomo.csv', index=False)
    qt.to_csv(OUT/'feature_quintiles.csv', index=False)

    if len(sm):
        def sign_stable(feature: str, col: str) -> dict:
            a = lm[lm.feature.eq(feature)][col].dropna()
            if len(a)==0:
                return {'n':0,'same_sign_frac':None,'min':None,'max':None}
            med = float(a.median())
            s = 1 if med>0 else (-1 if med<0 else 0)
            frac = float(np.mean(np.sign(a)==s)) if s else 0.0
            return {'n':len(a),'same_sign_frac':frac,'min':float(a.min()),'max':float(a.max())}
        stability={}
        for f in sm.feature:
            stability[f]={
                'hit': sign_stable(f,'spearman_hit'),
                'return': sign_stable(f,'spearman_return_multiple'),
            }
    else:
        stability={}

    res={
        'production_identity': {'R':got[0],'head':got[1],'exact3_top3':got[2],'sha256':got[3]},
        'scope': {'pristine_months':PRISTINE,'broad_combined_min':BROAD_MIN,'broad_combined_max_exclusive':BROAD_MAX,
                  'pristine_population_R':len(pr),'broad_pristine_R':len(broad),'broad_all_feb_aug_R':len(broad_all)},
        'feature_stability': stability,
        'production_modified': False,
        'SEPTEMBER_OUTCOMES_READ': False,
    }
    (OUT/'result_v344.json').write_text(json.dumps(res,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
    print(json.dumps(res,ensure_ascii=False,indent=2,default=str),flush=True)

if __name__=='__main__':
    main()
