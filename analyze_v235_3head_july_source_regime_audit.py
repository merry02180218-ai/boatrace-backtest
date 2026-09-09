#!/usr/bin/env python3
"""v235: audit the residual July regime/source shift after restored Waku10.

AUDIT ONLY. No threshold/rule/model tuning.
- Reuses v234's validated historical Waku10 reconstruction.
- Rebuilds the frozen v224-like feature pipeline through Aug 2026.
- Jul/Aug are NON-PRISTINE and are descriptive/shadow context only.
- Separates grade, national/local/recent form, Waku10, exhibition/current-state,
  player-history, relative/race-shape and other feature families.
- Reports both selected-race monthly calibration and all-race Jun30->Jul1 boundary shifts.
- Audits missingness/population changes as a source-definition warning signal.
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd

import analyze_v223_3head_unused_feature_audit as v223
import analyze_v234_3head_waku10_restored_replay as v234

ROOT=Path(__file__).resolve().parent
SEL=ROOT/'analysis_v235_selected_calibration.csv'
SHIFT=ROOT/'analysis_v235_selected_feature_shifts.csv'
MISS=ROOT/'analysis_v235_feature_missingness.csv'
BOUND=ROOT/'analysis_v235_boundary_feature_shifts.csv'
FAM=ROOT/'analysis_v235_family_summary.csv'
SUM=ROOT/'summary_v235_3head_july_source_regime_audit.md'
MONTHS=['2026-05','2026-06','2026-07','2026-08']


def family(c:str)->str:
    s=c.lower()
    if 'waku_' in s or 'pastwin' in s:
        return 'waku10'
    if 'grade' in s:
        return 'grade_class'
    if s.startswith('f_b3_') or s.startswith('f_rel_'):
        return 'national_recent_form'
    if s.startswith('b3_vh_') or s.startswith('b3_pl_'):
        return 'player_history'
    if any(k in s for k in ['_wr','_local','_nst']):
        return 'national_local_stats'
    if any(k in s for k in ['_ex','_st','_lap','_turn','_straight','_origavg','_motor','_meetst','_tilt']):
        return 'current_exhibition_motor'
    if s.startswith(('c_b3_minus_','c_b3_inside_','c_b3_outside_','c_wall','c_attack3','c_outer','c_')):
        return 'relative_race_shape'
    return 'base_other'


def numeric_series(df,c):
    return pd.to_numeric(df[c],errors='coerce') if c in df.columns else pd.Series(index=df.index,dtype=float)


def standardized_shift(a,b):
    a=a.dropna(); b=b.dropna()
    if len(a)<10 or len(b)<10:return (np.nan,np.nan,np.nan,len(a),len(b))
    pool=pd.concat([a,b],ignore_index=True); sd=float(pool.std(ddof=1))
    delta=float(b.mean()-a.mean()); z=delta/sd if sd>1e-12 else np.nan
    return delta,z,sd,len(a),len(b)


def select_months(d,vc,basefs,fs):
    out=[]
    for mon in MONTHS:
        first=pd.Timestamp(mon+'-01'); nextm=first+pd.offsets.MonthBegin(1)
        base_te,_=v223.fit_head(d,list(basefs),vc,first,nextm)
        k=max(1,int((base_te._p>=.30).sum()))
        te,nfeat=v223.fit_head(d,fs,vc,first,nextm)
        s=te.nlargest(k,'_p').copy(); s['_month']=mon; s['_nfeat']=nfeat
        out.append(s)
    return pd.concat(out,ignore_index=True)


def main():
    cov=v234.reconstruct()
    checked=v234.validate_parser()
    if (cov.source=='missing').any():
        raise RuntimeError('v235 refuses arbitrary Waku10 imputation; missing restored dates remain')
    d,dc,vc,basefs=v234.build_restored()
    fs=v234.full_features(d,basefs)
    fs=[c for c in fs if c in d.columns]

    s=select_months(d,vc,basefs,fs)
    keep=['_month','_date','race_code','_p','_y','_nfeat']+fs
    s[keep].to_csv(SEL,index=False)

    # Selected-race feature shifts, contextualized with May/Aug but focused on Jun->Jul.
    rec=[]
    for c in fs:
        vals={m:numeric_series(s[s._month==m],c) for m in MONTHS}
        delta,z,sd,jn,jln=standardized_shift(vals['2026-06'],vals['2026-07'])
        if jn<10 or jln<10:continue
        rec.append({
            'feature':c,'family':family(c),
            'may_mean':vals['2026-05'].mean(),'jun_mean':vals['2026-06'].mean(),
            'jul_mean':vals['2026-07'].mean(),'aug_mean':vals['2026-08'].mean(),
            'jun_jul_delta':delta,'jun_jul_std_shift':z,'abs_shift':abs(z) if pd.notna(z) else np.nan,
            'jun_n':jn,'jul_n':jln,
        })
    sh=pd.DataFrame(rec).sort_values('abs_shift',ascending=False)
    sh.to_csv(SHIFT,index=False)

    # Missingness/population audit on all eligible rows per month, not just selected rows.
    d2=d[(d._date>=pd.Timestamp('2026-05-01'))&(d._date<pd.Timestamp('2026-09-01'))].copy()
    d2['_month']=d2._date.dt.strftime('%Y-%m')
    mr=[]
    for c in fs:
        row={'feature':c,'family':family(c)}
        rates={}
        for m in MONTHS:
            q=numeric_series(d2[d2._month==m],c)
            rates[m]=float(q.notna().mean()) if len(q) else np.nan
            row[m+'_coverage']=rates[m]
        row['jun_jul_coverage_delta']=rates['2026-07']-rates['2026-06']
        row['abs_coverage_delta']=abs(row['jun_jul_coverage_delta']) if pd.notna(row['jun_jul_coverage_delta']) else np.nan
        mr.append(row)
    miss=pd.DataFrame(mr).sort_values('abs_coverage_delta',ascending=False)
    miss.to_csv(MISS,index=False)

    # Tight boundary window: last 7 June days vs first 7 July days, ALL eligible rows.
    pre=d[(d._date>=pd.Timestamp('2026-06-24'))&(d._date<pd.Timestamp('2026-07-01'))]
    post=d[(d._date>=pd.Timestamp('2026-07-01'))&(d._date<pd.Timestamp('2026-07-08'))]
    br=[]
    for c in fs:
        a=numeric_series(pre,c); b=numeric_series(post,c)
        delta,z,sd,an,bn=standardized_shift(a,b)
        if an<10 or bn<10:continue
        br.append({'feature':c,'family':family(c),'jun24_30_mean':a.mean(),'jul01_07_mean':b.mean(),
                   'delta':delta,'std_shift':z,'abs_shift':abs(z) if pd.notna(z) else np.nan,
                   'pre_n':an,'post_n':bn,'pre_coverage':a.notna().mean(),'post_coverage':b.notna().mean()})
    bound=pd.DataFrame(br).sort_values('abs_shift',ascending=False)
    bound.to_csv(BOUND,index=False)

    # Family summary combines selected distribution shift, boundary shift, and missingness break.
    fr=[]
    families=sorted(set(sh.family)|set(bound.family)|set(miss.family))
    for f in families:
        a=sh[sh.family==f]; b=bound[bound.family==f]; c=miss[miss.family==f]
        fr.append({
            'family':f,'features':max(len(a),len(b),len(c)),
            'selected_median_abs_shift':a.abs_shift.median() if len(a) else np.nan,
            'selected_max_abs_shift':a.abs_shift.max() if len(a) else np.nan,
            'boundary_median_abs_shift':b.abs_shift.median() if len(b) else np.nan,
            'boundary_max_abs_shift':b.abs_shift.max() if len(b) else np.nan,
            'max_abs_coverage_delta':c.abs_coverage_delta.max() if len(c) else np.nan,
        })
    fam=pd.DataFrame(fr).sort_values(['boundary_max_abs_shift','selected_max_abs_shift'],ascending=False)
    fam.to_csv(FAM,index=False)

    L=['# v235 residual July source/regime audit after Waku10 restoration','',
       '- AUDIT ONLY: no threshold/rule/model tuning.',
       '- Jul/Aug 2026 remain NON-PRISTINE and are descriptive/shadow context only.',
       f'- Waku10 parser cross-check: {checked} races, 0 mismatches required; missing restored dates: {int((cov.source=="missing").sum())}.','',
       '## Selected-race head calibration','|month|R|avg p3|actual 3-head|gap pp|','|---|---:|---:|---:|---:|']
    for mon,g in s.groupby('_month',sort=True):
        L.append(f'|{mon}|{len(g)}|{100*g._p.mean():.2f}%|{100*g._y.mean():.2f}%|{100*(g._p.mean()-g._y.mean()):+.2f}|')
    L += ['', '## Feature-family source/regime signals','|family|selected median |z||selected max |z||boundary median |z||boundary max |z||max coverage jump|','|---|---:|---:|---:|---:|---:|']
    for _,r in fam.iterrows():
        L.append(f"|{r.family}|{r.selected_median_abs_shift:.3f}|{r.selected_max_abs_shift:.3f}|{r.boundary_median_abs_shift:.3f}|{r.boundary_max_abs_shift:.3f}|{100*r.max_abs_coverage_delta:.1f}pp|")
    L += ['', '## Largest tight-boundary shifts (Jun24-30 vs Jul1-7)','|feature|family|Jun mean|Jul mean|std shift|','|---|---|---:|---:|---:|']
    for _,r in bound.head(30).iterrows():
        L.append(f"|{r.feature}|{r.family}|{r.jun24_30_mean:.5g}|{r.jul01_07_mean:.5g}|{r.std_shift:+.3f}|")
    L += ['', '## Largest June->July coverage/population changes','|feature|family|Jun coverage|Jul coverage|delta|','|---|---|---:|---:|---:|']
    for _,r in miss.head(25).iterrows():
        L.append(f"|{r.feature}|{r.family}|{100*r['2026-06_coverage']:.1f}%|{100*r['2026-07_coverage']:.1f}%|{100*r.jun_jul_coverage_delta:+.1f}pp|")
    L += ['', '## Interpretation protocol',
          '- A large coverage jump is treated first as a source/schema/population-definition warning, not a racer-skill change.',
          '- A large boundary distribution shift with stable coverage is consistent with either a genuine half-year racer/regime change or a source value-definition reset; inspect the named source fields before causal claims.',
          '- No feature/rule is promoted from July/August performance. Any redesign requires a separate no-leak validation protocol.']
    SUM.write_text('\n'.join(L)+'\n',encoding='utf-8')
    print('\n'.join(L),flush=True)


if __name__=='__main__':
    main()
