#!/usr/bin/env python3
import json
from pathlib import Path
import pandas as pd

ROOT = Path('/tmp/v341')
OUT = Path('/tmp/v341out')
OUT.mkdir(parents=True, exist_ok=True)
RACE = ROOT / 'race_level.csv'

z = pd.read_csv(RACE, dtype={'race_code': str})
z['race_code'] = z['race_code'].astype(str).str.zfill(12)

required = {
    'month','race_code','action','head_hit','baseline_hit','baseline_stake_yen',
    'baseline_return_yen','hit','stake_yen','return_yen','n_tickets'
}
missing = sorted(required - set(z.columns))
assert not missing, f'missing columns: {missing}'
assert len(z) == 276, f'production identity R mismatch: {len(z)}'
assert int(z['head_hit'].sum()) == 241, f'head identity mismatch: {int(z.head_hit.sum())}'
assert int(z['baseline_hit'].sum()) == 119, f'exact3 identity mismatch: {int(z.baseline_hit.sum())}'
assert not z['month'].astype(str).str.startswith('2026-09').any(), 'September rows must remain unread/absent'


def money_block(df, stake_col, return_col, hit_col):
    stake = float(df[stake_col].sum())
    ret = float(df[return_col].sum())
    hits = int(df[hit_col].sum())
    r = int(len(df))
    return {
        'R': r,
        'hits': hits,
        'hit_rate_pct': (100.0 * hits / r) if r else None,
        'stake_yen': stake,
        'return_yen': ret,
        'profit_yen': ret - stake,
        'roi_pct': (100.0 * ret / stake) if stake else None,
    }

# Overall and pristine Feb-Jun only.
pristine_months = {'2026-02','2026-03','2026-04','2026-05','2026-06'}
pr = z[z['month'].astype(str).isin(pristine_months)].copy()
pr_bought = pr[pr['stake_yen'] > 0].copy()

summary = {
    'production_identity': {
        'R': int(len(z)),
        'head': int(z.head_hit.sum()),
        'exact3_top3': int(z.baseline_hit.sum()),
        'expected_sha256': '89e0b32c3ffbed6212f98f0a9b2e230717b8e41010019e3321fb49e70148ba73',
    },
    'pristine_feb_jun': {
        'population_R': int(len(pr)),
        'adaptive': money_block(pr_bought, 'stake_yen', 'return_yen', 'hit'),
        'baseline_top3_all': money_block(pr, 'baseline_stake_yen', 'baseline_return_yen', 'baseline_hit'),
        'actions': {str(k): int(v) for k, v in pr['action'].value_counts().to_dict().items()},
    },
    'SEPTEMBER_OUTCOMES_READ': False,
}

# Action-level contribution table.
rows = []
for action, g in z.groupby('action', sort=True):
    adaptive_stake = float(g['stake_yen'].sum())
    adaptive_return = float(g['return_yen'].sum())
    baseline_stake = float(g['baseline_stake_yen'].sum())
    baseline_return = float(g['baseline_return_yen'].sum())
    rows.append({
        'action': action,
        'R': int(len(g)),
        'head_hits': int(g['head_hit'].sum()),
        'head_rate_pct': 100.0 * float(g['head_hit'].mean()),
        'top3_hits': int(g['baseline_hit'].sum()),
        'top3_hit_rate_pct': 100.0 * float(g['baseline_hit'].mean()),
        'adaptive_hits': int(g['hit'].sum()),
        'adaptive_stake_yen': adaptive_stake,
        'adaptive_return_yen': adaptive_return,
        'adaptive_profit_yen': adaptive_return - adaptive_stake,
        'adaptive_roi_pct': (100.0 * adaptive_return / adaptive_stake) if adaptive_stake else None,
        'baseline_stake_yen': baseline_stake,
        'baseline_return_yen': baseline_return,
        'baseline_profit_yen': baseline_return - baseline_stake,
        'baseline_roi_pct': (100.0 * baseline_return / baseline_stake) if baseline_stake else None,
        'profit_delta_vs_top3_yen': (adaptive_return - adaptive_stake) - (baseline_return - baseline_stake),
    })
action_df = pd.DataFrame(rows)
action_df.to_csv(OUT / 'action_contribution.csv', index=False)
summary['action_contribution'] = action_df.to_dict('records')

# Expand-only pure incremental effect versus keeping the original top3 on the same races.
ex = z[z['action'] == 'expand'].copy()
expand_ad = money_block(ex, 'stake_yen', 'return_yen', 'hit')
expand_base = money_block(ex, 'baseline_stake_yen', 'baseline_return_yen', 'baseline_hit')
summary['expand_incremental'] = {
    'adaptive_expanded': expand_ad,
    'same_races_top3_only': expand_base,
    'hit_delta': expand_ad['hits'] - expand_base['hits'],
    'return_delta_yen': expand_ad['return_yen'] - expand_base['return_yen'],
    'profit_delta_yen': expand_ad['profit_yen'] - expand_base['profit_yen'],
}

# Skip-only avoided result versus hypothetically buying top3 for 10k on every skipped race.
sk = z[z['action'] == 'skip'].copy()
sk_base = money_block(sk, 'baseline_stake_yen', 'baseline_return_yen', 'baseline_hit')
summary['skip_effect'] = {
    'skipped_R': int(len(sk)),
    'hypothetical_top3_if_bought': sk_base,
    'net_profit_improvement_from_skipping_yen': -sk_base['profit_yen'],
}

# Save a compact pristine monthly breakdown for diagnostics.
monthly_rows = []
for month, g in pr.groupby('month', sort=True):
    gb = g[g['stake_yen'] > 0]
    a = money_block(gb, 'stake_yen', 'return_yen', 'hit')
    base = money_block(g, 'baseline_stake_yen', 'baseline_return_yen', 'baseline_hit')
    monthly_rows.append({
        'month': month,
        'population_R': len(g),
        'adaptive_bought_R': len(gb),
        'adaptive_hits': a['hits'],
        'adaptive_profit_yen': a['profit_yen'],
        'adaptive_roi_pct': a['roi_pct'],
        'baseline_profit_yen': base['profit_yen'],
        'baseline_roi_pct': base['roi_pct'],
    })
pd.DataFrame(monthly_rows).to_csv(OUT / 'pristine_monthly.csv', index=False)

(OUT / 'result_v341.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)
