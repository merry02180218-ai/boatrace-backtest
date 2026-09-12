#!/usr/bin/env python3
"""v313 infrastructure: build the reusable causal cache for 1-head opponent research.

This intentionally performs the expensive reconstruction once.  Later SECOND / THIRD /
ordered-pair / ticket experiments must load these cache files instead of reconstructing
p3, p4, PRE history, race cards, and settlement data on every run.

Causal contract
---------------
- PRE/prior feature state is frozen before settlement joins.
- p3 is rebuilt month-by-month with the existing causal walk-forward pipeline.
- p4 comes from the already-audited PRE monthly walk-forward output.
- meet_* columns are removed from the reusable cache.
- outcome/settlement columns may exist only as labels/evaluation fields; downstream
  month-M fitting must train strictly on rows before M and must never use them as model
  features.
- Jul/Aug remain NON-PRISTINE; September outcomes remain unread in research scoring.
"""
from pathlib import Path
import pandas as pd

import analyze_v298_1head_threat_listwise_trifecta5 as v298
import run_v300_1head_trifecta3_feature_upgrade as v300
import run_v310_1head_opponent_headrisk_second as v310

ROOT=Path(__file__).resolve().parent
SEL=ROOT/'analysis_v308_1head_volume_opponent_joint_best_selected.csv'
CACHE_D=ROOT/'cache_v313_1head_opponent_pre.csv.gz'
CACHE_P3=ROOT/'cache_v313_1head_opponent_p3.csv.gz'
CACHE_P4=ROOT/'cache_v313_1head_opponent_p4.csv.gz'
MANIFEST=ROOT/'CACHE_V313_1HEAD_OPPONENT_CAUSAL.md'


def main():
    print('v313 cache: rebuilding causal p3/p4 once',flush=True)
    p3=v310.causal_p3_map()
    p4=v310.causal_p4_map()

    print('v313 cache: rebuilding frozen PRE/prior opponent universe once',flush=True)
    v300.setup_v298()
    d,_=v298.v294.freeze_true_pre()
    d=v298.v294.add_prior_history(d)
    d=v298.v294.add_rel(d)
    d,_=v298.add_threat(d)
    # Settlement is joined only after PRE/prior construction. These columns are labels /
    # evaluation fields and are never admitted to downstream feature lists.
    d,_=v298.v297.settle_full_after_freeze(d)
    d=d[(d.valid_result==1)&(d.combo_valid==1)].copy()
    d['race_code']=d.race_code.astype(str).str.zfill(12)
    d['month']=d.month.astype(str)

    sufs=v298.suffixes(d)
    if any('meet_' in x for x in sufs):
        raise RuntimeError('v313 cache refused: meet_* suffix entered opponent feature set')

    # Fail closed: reusable table itself should not carry forbidden meet_* columns,
    # preventing a later experiment from accidentally enabling them.
    drop=[c for c in d.columns if 'meet_' in str(c)]
    if drop:
        d=d.drop(columns=drop)

    frozen=pd.read_csv(SEL,dtype={'race_code':str})
    frozen['race_code']=frozen.race_code.astype(str).str.zfill(12)
    ids=set(frozen.race_code)
    q=d[d.race_code.isin(ids)].copy()
    if len(q)!=345 or int(q.head_hit.sum())!=290:
        raise RuntimeError(f'v313 frozen cohort mismatch R={len(q)} head={int(q.head_hit.sum())}')

    pd.DataFrame(sorted(p3.items()),columns=['race_code','p3head']).to_csv(CACHE_P3,index=False,compression='gzip')
    pd.DataFrame(sorted(p4.items()),columns=['race_code','p4head']).to_csv(CACHE_P4,index=False,compression='gzip')
    d.to_csv(CACHE_D,index=False,compression='gzip')

    lines=[
        '# v313 1-head opponent causal cache',
        '',
        '## Purpose',
        '- Expensive historical reconstruction is performed once and committed as reusable cache files.',
        '- All subsequent 1-head opponent auto-research should load this cache by default instead of rebuilding historical sources.',
        '- Rebuild only when upstream causal feature logic/data provenance changes, the frozen cohort changes explicitly, or a cache audit fails.',
        '',
        '## Files',
        f'- `{CACHE_D.name}`: frozen PRE/prior opponent universe plus settlement labels, {len(d)} rows / {len(d.columns)} columns.',
        f'- `{CACHE_P3.name}`: causal monthly walk-forward p3 map, {len(p3)} races.',
        f'- `{CACHE_P4.name}`: audited PRE monthly walk-forward p4 map, {len(p4)} races.',
        '',
        '## Causal contract',
        '- PRE/prior features are constructed before settlement joins.',
        '- `meet_*` columns are removed and `meet_*` suffixes are forbidden.',
        '- Outcome / settlement fields are labels only, never model features.',
        '- Month M models train only on rows strictly before M.',
        '- Missing p3/p4 are never future-backfilled; downstream uses availability flags + neutral sentinel.',
        '- Fixed opponent evaluation cohort remains 345 races / 290 boat-1 wins.',
        '- Jul/Aug 2026 remain NON-PRISTINE; September outcomes remain unread.',
        '',
        '## Cache-first rule',
        '- Research scripts MUST prefer these cache files when present.',
        '- A research workflow must not repeat the full causal reconstruction merely to test a new model formulation.',
        '- If the cache is missing/stale, build it once, commit it, then continue the queued experiment.',
    ]
    MANIFEST.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(MANIFEST.read_text(),flush=True)

if __name__=='__main__':
    main()
