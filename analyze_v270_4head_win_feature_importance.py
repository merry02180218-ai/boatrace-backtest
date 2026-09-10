#!/usr/bin/env python3
"""v270: research what matters in historical boat-4 wins.

Goal
----
Compare races won by boat 4 against all other races and identify features that
are useful, stable across months, and still add information after PRE/POST.

Discipline
----------
* 2026-07/08 are excluded completely.
* Outcome/payout/ticket/actual-result columns are excluded from candidate inputs.
* This is retrospective research/model selection, NOT pristine validation.
* Incremental tests use month walk-forward: each evaluation month is predicted
  only from earlier races.

Outputs
-------
analysis_v270_4head_win_feature_importance.csv
analysis_v270_4head_win_feature_categories.csv
summary_v270_4head_win_feature_importance.md
"""
from __future__ import annotations
from pathlib import Path
import math
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, log_loss

import analyze_v264_4head_feature_exhaustive as v264
import analyze_v96_4corner_monthly_walkforward_tiebreak as c4
import analyze_v221_3head_scenario_pair as v221

ROOT = Path(__file__).resolve().parent
PRED = ROOT / 'analysis_v250_4head_rebuild_baseline.csv'
OUT = ROOT / 'analysis_v270_4head_win_feature_importance.csv'
CAT = ROOT / 'analysis_v270_4head_win_feature_categories.csv'
SUM = ROOT / 'summary_v270_4head_win_feature_importance.md'
MONTHS = [f'2026-{m:02d}' for m in range(2, 7)]
TOP_FOR_INCREMENTAL = 100


def num(s):
    return pd.to_numeric(s, errors='coerce')


def category(c: str) -> str:
    if c in ('PRE', 'POST', 'p4_joint', 'post_x_entry_same'):
        return 'PRE_POST総合'
    if c.startswith('rel_pl_') and '_4v1' in c:
        return '4号艇vs1号艇_選手力差'
    if c.startswith('b1_pl_'):
        return '1号艇_選手力弱さ'
    if c.startswith('b4_pl_'):
        return '4号艇_選手力'
    if c.startswith('rel_pl_'):
        return '4号艇vs他艇_選手力差'
    if c.startswith('opp_') or c.startswith('rank_b'):
        return '相手構成_v93'
    if c.startswith('rel_vh_') and '_4v1' in c:
        return '4号艇vs1号艇_過去展示差'
    if c.startswith('rel_vh_'):
        return '4号艇vs他艇_過去展示差'
    if c.startswith('b4_vh_') or c.startswith('b4_gh_'):
        return '4号艇_過去展示機力'
    if c.startswith('b1_vh_') or c.startswith('b1_gh_'):
        return '1号艇_過去展示機力'
    if c.startswith('st_') or c.startswith('rel_st_') or c.startswith('attack4_'):
        return 'ST攻撃力_壁'
    if c.startswith('score_') or c.startswith('v91_') or c in ('preview_comp','relative_deg','relative_wind','wind_speed','wind_adjust_points','tilt','tilt_bonus'):
        return '当日展示_風_環境'
    if c.startswith('entry_') or c in ('has_orig','has_stt','has_tkz'):
        return '進入_データ確定度'
    return 'その他'


def prepare():
    d = pd.DataFrame(c4.read())
    d['race_code'] = d.race_code.astype(str).str.zfill(12)
    d['_date'] = pd.to_datetime(d.date, errors='coerce')
    d = d[d._date < pd.Timestamp('2026-07-01')].copy()
    d = v221.build(d, 'date')
    d['y4'] = (num(d['winner']) == 4).astype(int)

    p = pd.read_csv(PRED, dtype={'race_code': str})
    p['race_code'] = p.race_code.astype(str).str.zfill(12)
    pw = p.pivot_table(index=['date','race_code'], columns='variant', values='p4head', aggfunc='last').reset_index()
    pw['date'] = pw.date.astype(str)
    d['date'] = d.date.astype(str)
    d = d.merge(pw[['date','race_code','PRE','POST']], on=['date','race_code'], how='left')
    d = v264.add_rel(d)
    groups = v264.families(d)
    fs = list(dict.fromkeys(groups['ALL_SAFE_LINEAR']))
    return d, groups, fs


def oriented_stats(ev: pd.DataFrame, c: str):
    x = num(ev[c])
    z = ev.loc[x.notna(), ['month','y4']].copy()
    z['x'] = x.loc[x.notna()].to_numpy()
    if len(z) < 300 or z.x.nunique() < 4 or z.y4.nunique() < 2:
        return None
    try:
        auc_raw = roc_auc_score(z.y4, z.x)
    except Exception:
        return None
    direction = 'high' if auc_raw >= 0.5 else 'low'
    auc_oriented = max(auc_raw, 1-auc_raw)
    sign = 1.0 if direction == 'high' else -1.0
    z['ox'] = sign*z.x

    win = z[z.y4 == 1].ox
    lose = z[z.y4 == 0].ox
    sd = z.ox.std(ddof=1)
    smd = (win.mean()-lose.mean())/sd if sd and np.isfinite(sd) else np.nan

    q10 = z.ox.quantile(.90)
    q20 = z.ox.quantile(.80)
    top10 = z[z.ox >= q10]
    top20 = z[z.ox >= q20]
    overall = z.y4.mean()

    month_good = 0
    month_seen = 0
    month_detail = []
    for m, g in z.groupby('month'):
        if g.y4.nunique() < 2:
            continue
        w = g[g.y4 == 1].ox.mean()
        l = g[g.y4 == 0].ox.mean()
        good = bool(w > l)
        month_seen += 1
        month_good += int(good)
        month_detail.append(f'{m}:{"+" if good else "-"}')

    return {
        'feature': c,
        'category': category(c),
        'n': len(z),
        'overall_head_rate': overall,
        'direction': direction,
        'auc_oriented': auc_oriented,
        'std_mean_diff': smd,
        'top10_n': len(top10),
        'top10_head_rate': top10.y4.mean(),
        'top10_lift_pt': 100*(top10.y4.mean()-overall),
        'top20_n': len(top20),
        'top20_head_rate': top20.y4.mean(),
        'top20_lift_pt': 100*(top20.y4.mean()-overall),
        'month_direction_good': month_good,
        'month_direction_seen': month_seen,
        'month_consistency': month_good/month_seen if month_seen else np.nan,
        'month_direction_detail': ';'.join(month_detail),
    }


def walkforward_incremental(d: pd.DataFrame, feature: str):
    base_preds, ext_preds, ys, mons = [], [], [], []
    for mon in MONTHS:
        first = pd.Timestamp(mon+'-01')
        nxt = first + pd.offsets.MonthBegin(1)
        tr = d[d._date < first].copy()
        te = d[(d._date >= first) & (d._date < nxt)].copy()
        if len(tr) < 500 or te.empty:
            continue
        bcols = [c for c in ['PRE','POST'] if c in d.columns]
        if len(bcols) < 2:
            continue
        ecols = bcols + [feature] if feature not in bcols else bcols
        try:
            mb = v264.lr_model(); me = v264.lr_model()
            mb.fit(tr[bcols].apply(num), tr.y4)
            me.fit(tr[ecols].apply(num), tr.y4)
            pb = mb.predict_proba(te[bcols].apply(num))[:,1]
            pe = me.predict_proba(te[ecols].apply(num))[:,1]
        except Exception:
            continue
        base_preds.extend(pb.tolist()); ext_preds.extend(pe.tolist())
        ys.extend(te.y4.astype(int).tolist()); mons.extend([mon]*len(te))
    if len(set(ys)) < 2 or len(ys) < 100:
        return None
    auc_b = roc_auc_score(ys, base_preds)
    auc_e = roc_auc_score(ys, ext_preds)
    ll_b = log_loss(ys, base_preds, labels=[0,1])
    ll_e = log_loss(ys, ext_preds, labels=[0,1])

    month_auc_delta = []
    yy = np.asarray(ys); pb = np.asarray(base_preds); pe = np.asarray(ext_preds); mm = np.asarray(mons)
    for mon in sorted(set(mons)):
        ix = mm == mon
        if len(set(yy[ix])) < 2:
            continue
        month_auc_delta.append(roc_auc_score(yy[ix],pe[ix]) - roc_auc_score(yy[ix],pb[ix]))
    return {
        'oof_n': len(ys),
        'base_oof_auc': auc_b,
        'plus_feature_oof_auc': auc_e,
        'delta_oof_auc': auc_e-auc_b,
        'delta_logloss': ll_e-ll_b,  # negative is better
        'incremental_months_positive': int(sum(x > 0 for x in month_auc_delta)),
        'incremental_months_seen': len(month_auc_delta),
        'incremental_month_floor_auc_delta': min(month_auc_delta) if month_auc_delta else np.nan,
        'incremental_month_mean_auc_delta': float(np.mean(month_auc_delta)) if month_auc_delta else np.nan,
    }


def main():
    d, groups, fs = prepare()
    d['month'] = d['_date'].dt.strftime('%Y-%m')
    ev = d[(d._date >= pd.Timestamp('2026-02-01')) & (d._date < pd.Timestamp('2026-07-01'))].copy()

    rows = []
    for c in fs:
        if c in ev.columns and v264.goodcol(ev, c, .55):
            r = oriented_stats(ev, c)
            if r:
                rows.append(r)
    u = pd.DataFrame(rows)
    if u.empty:
        raise RuntimeError('no eligible features')

    # Only strongest univariates go through the more expensive incremental
    # month-walk-forward test. Ranking here is descriptive and the entire audit
    # remains retrospective/model-selection evidence.
    candidates = u.sort_values(['auc_oriented','top20_lift_pt'], ascending=False).head(TOP_FOR_INCREMENTAL).feature.tolist()
    inc = []
    for c in candidates:
        r = walkforward_incremental(d, c)
        if r:
            inc.append({'feature': c, **r})
    ii = pd.DataFrame(inc)
    o = u.merge(ii, on='feature', how='left')

    # Importance score rewards discrimination, lift, cross-month direction, and
    # incremental value beyond PRE/POST. It is for ranking research priorities,
    # not a calibrated probability or production threshold.
    o['importance_score'] = (
        100*(o.auc_oriented-.5).clip(lower=0)
        + .20*o.top20_lift_pt.clip(lower=0)
        + 5*o.month_consistency.fillna(0)
        + 200*o.delta_oof_auc.fillna(0).clip(lower=0)
        + 2*(o.incremental_months_positive.fillna(0)/o.incremental_months_seen.replace(0,np.nan)).fillna(0)
    )
    o = o.sort_values(['importance_score','auc_oriented','top20_lift_pt'], ascending=False)
    o.to_csv(OUT, index=False)

    cat = o.groupby('category').agg(
        features=('feature','count'),
        best_auc=('auc_oriented','max'),
        mean_top20_lift_pt=('top20_lift_pt','mean'),
        best_delta_oof_auc=('delta_oof_auc','max'),
        mean_month_consistency=('month_consistency','mean'),
        max_importance_score=('importance_score','max'),
    ).reset_index().sort_values(['max_importance_score','best_auc'], ascending=False)
    cat.to_csv(CAT, index=False)

    base_rate = ev.y4.mean()
    wins = int(ev.y4.sum())
    L = [
        '# v270 4-head historical win feature importance', '',
        f'- Research sample: Feb-Jun 2026, {len(ev)} races, boat-4 wins={wins}, base head rate={100*base_rate:.2f}%.',
        '- July/August 2026 excluded completely.',
        '- Leakage/result/payout/ticket fields excluded from candidate inputs using v264 safe-feature rules.',
        '- `top10/top20 lift` is descriptive; `delta OOF AUC` asks whether the feature adds information beyond PRE+POST in month walk-forward predictions.',
        '- This is retrospective feature research/model selection, not pristine validation.', '',
        '## Feature-family priority',
        '|category|features|best AUC|mean top20 lift|best +OOF AUC|mean month consistency|',
        '|---|---:|---:|---:|---:|---:|',
    ]
    for _, r in cat.iterrows():
        da = '--' if pd.isna(r.best_delta_oof_auc) else f'{r.best_delta_oof_auc:+.4f}'
        L.append(f'|{r.category}|{int(r.features)}|{r.best_auc:.4f}|{r.mean_top20_lift_pt:+.2f}pt|{da}|{100*r.mean_month_consistency:.1f}%|')

    L += ['', '## Most important individual features',
          '|rank|feature|category|direction|AUC|top10 head|top20 head|month consistency|+OOF AUC vs PRE/POST|OOF months +|score|',
          '|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|']
    for rank, (_, r) in enumerate(o.head(50).iterrows(), 1):
        da = '--' if pd.isna(r.delta_oof_auc) else f'{r.delta_oof_auc:+.4f}'
        im = '--' if pd.isna(r.incremental_months_seen) else f'{int(r.incremental_months_positive)}/{int(r.incremental_months_seen)}'
        L.append(f'|{rank}|{r.feature}|{r.category}|{r.direction}|{r.auc_oriented:.4f}|{100*r.top10_head_rate:.2f}%|{100*r.top20_head_rate:.2f}%|{100*r.month_consistency:.0f}%|{da}|{im}|{r.importance_score:.2f}|')

    stable = o[(o.month_consistency >= .75) & (o.delta_oof_auc.fillna(-1) > 0) & (o.incremental_months_positive.fillna(0) >= 2)].head(25)
    L += ['', '## Stable add-on candidates for expanding race count',
          'These are candidates to rescue A-rank races outside frozen v268; they are **not** new thresholds yet.',
          '|feature|direction|AUC|top20 lift|+OOF AUC|month consistency|',
          '|---|---|---:|---:|---:|---:|']
    if stable.empty:
        L.append('|--|--|--|--|--|--|')
    else:
        for _, r in stable.iterrows():
            L.append(f'|{r.feature}|{r.direction}|{r.auc_oriented:.4f}|{r.top20_lift_pt:+.2f}pt|{r.delta_oof_auc:+.4f}|{100*r.month_consistency:.0f}%|')

    L += ['', '## Interpretation rule',
          '- Prioritize features that are strong in **relative 4-vs-1 terms**, stable across months, and positive after PRE/POST—not merely features with one large top-decile hit rate.',
          '- Use these results to build a separate A-rank expansion layer; keep HEAD4_V268 unchanged as S-rank.', '']
    SUM.write_text('\n'.join(L), encoding='utf-8')
    print('\n'.join(L))


if __name__ == '__main__':
    main()
