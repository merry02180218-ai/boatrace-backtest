#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import math
import numpy as np
import pandas as pd
from scipy.stats import binomtest
import run_v332_1head_attack_first_redesign as v332

OUT=Path('/tmp/v333'); OUT.mkdir(parents=True,exist_ok=True)
CFG={'family':'ATTACK_ENV_SOFT','env_w':0.1,'q':0.65}
MONTHS=v332.MONTHS_DEV+[v332.AUG]

def wilson(k,n,z=1.959963984540054):
    if n==0:return (float('nan'),float('nan'))
    p=k/n; den=1+z*z/n; c=(p+z*z/(2*n))/den
    h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return 100*(c-h),100*(c+h)

def met(z):
    n=len(z); h=int(z.head_hit.sum()); e=int(z.hit.sum())
    hl,hu=wilson(h,n); el,eu=wilson(e,n)
    return dict(R=n,head=h,head_rate=100*h/n if n else np.nan,head_lo=hl,head_hi=hu,
                exact3=e,exact3_rate=100*e/n if n else np.nan,exact3_lo=el,exact3_hi=eu)

def main():
    y=v332.load_all(); rows=[]; passes=[]
    # Exact v332 Feb-Jul OOF; August trained only on Feb-Jul.
    for m in MONTHS:
        if m==v332.AUG: tr=y[y.month.isin(v332.MONTHS_DEV)].copy()
        else: tr=y[y.month.isin([x for x in v332.MONTHS_DEV if x!=m])].copy()
        z=y[y.month.eq(m)].copy(); p,_=v332.fit_apply(tr,z,CFG)
        passes.append(p.assign(audit_month=m))
        b=met(z); q=met(p)
        rows.append({'month':m,**{f'base_{k}':v for k,v in b.items()},**{f'pass_{k}':v for k,v in q.items()},
                     'pass_fraction_pct':100*len(p)/len(z),
                     'head_lift_pp':q['head_rate']-b['head_rate'],'exact3_lift_pp':q['exact3_rate']-b['exact3_rate']})
    tab=pd.DataFrame(rows)
    aug=tab[tab.month.eq('2026-08')].iloc[0]
    if int(aug.pass_R)!=10 or int(aug.pass_head)!=7 or int(aug.pass_exact3)!=4: raise AssertionError('v332 August reproduction failed')
    devp=pd.concat(passes[:6],ignore_index=True); dm=met(devp)
    if dm['R']!=86 or dm['head']!=76 or dm['exact3']!=41: raise AssertionError(f'v332 OOF reproduction failed {dm}')
    # Binomial tests: August sample under preceding pooled OOF rate. Descriptive small-sample diagnostic.
    p_head=dm['head']/dm['R']; p_exact=dm['exact3']/dm['R']
    bh=binomtest(7,10,p_head,alternative='two-sided'); be=binomtest(4,10,p_exact,alternative='two-sided')
    prior=tab.iloc[:6]
    head_lifts=prior.head_lift_pp.to_numpy(); exact_lifts=prior.exact3_lift_pp.to_numpy()
    # Empirical rank: fraction of prior absolute deviations/lifts at least as extreme as August.
    ah=float(aug.head_lift_pp); ae=float(aug.exact3_lift_pp)
    emp_h=(1+int(np.sum(np.abs(head_lifts)>=abs(ah))))/(len(head_lifts)+1)
    emp_e=(1+int(np.sum(np.abs(exact_lifts)>=abs(ae))))/(len(exact_lifts)+1)
    sens=[]
    for dh in [-2,-1,0,1,2]:
        k=max(0,min(10,7+dh)); sens.append({'metric':'head','delta_successes':dh,'successes':k,'R':10,'rate_pct':10*k})
    for de in [-2,-1,0,1,2]:
        k=max(0,min(10,4+de)); sens.append({'metric':'exact3','delta_successes':de,'successes':k,'R':10,'rate_pct':10*k})
    tab.to_csv(OUT/'analysis_v333_monthly.csv',index=False); pd.DataFrame(sens).to_csv(OUT/'analysis_v333_august_sensitivity.csv',index=False)
    prior_head_pos=int((prior.head_lift_pp>=0).sum()); prior_exact_pos=int((prior.exact3_lift_pp>=0).sum())
    # With n=10, require strong evidence before declaring structural break.
    structural=(bh.pvalue<0.05 and ah<0) or (be.pvalue<0.05 and ae<0)
    conclusion='CLEAR_STRUCTURAL_BREAK_EVIDENCE' if structural else 'INSUFFICIENT_EVIDENCE_MONTHLY_VARIANCE_PLAUSIBLE'
    lines=['# v333 v332 monthly variance audit','',
      f'- reproduced v332 Feb-Jul OOF: R={dm["R"]} head={dm["head"]}/{dm["R"]}={dm["head_rate"]:.2f}% exact3={dm["exact3"]}/{dm["R"]}={dm["exact3_rate"]:.2f}%',
      f'- pooled OOF Wilson95: head {dm["head_lo"]:.2f}-{dm["head_hi"]:.2f}%; exact3 {dm["exact3_lo"]:.2f}-{dm["exact3_hi"]:.2f}%',
      f'- August PASS: 10R head 7/10=70.00% Wilson95 {aug.pass_head_lo:.2f}-{aug.pass_head_hi:.2f}%; exact3 4/10=40.00% Wilson95 {aug.pass_exact3_lo:.2f}-{aug.pass_exact3_hi:.2f}%',
      f'- August vs preceding pooled OOF two-sided binomial p: head={bh.pvalue:.4f}, exact3={be.pvalue:.4f}',
      f'- August lifts vs its baseline: head {ah:+.2f}pp, exact3 {ae:+.2f}pp',
      f'- prior Feb-Jul nonnegative monthly lifts: head {prior_head_pos}/6, exact3 {prior_exact_pos}/6',
      f'- empirical small-month extremeness (absolute lift, add-one): head={emp_h:.3f}, exact3={emp_e:.3f}',
      '- sensitivity: with denominator 10, one result changes a rate by exactly 10 percentage points; two results by 20 points.',
      f'- CONCLUSION={conclusion}','- September outcomes unread. No retuning performed.']
    (OUT/'summary_v333.md').write_text('\n'.join(lines)+'\n',encoding='utf-8'); print('\n'.join(lines))
if __name__=='__main__':main()
