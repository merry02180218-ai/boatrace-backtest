#!/usr/bin/env python3
"""Execution wrapper for v294.

The archived v108 ledger contains all frozen races, including entry shifts.  For the
POST research universe we explicitly gate to actual entry_course == 1 instead of
requiring the whole ledger to already be course1-only.
"""
from __future__ import annotations
import pandas as pd
import analyze_v294_1head_verified_prepost_research as v


def load_frozen_post_course1(pre):
    meta=['date','race_code','venue','race','entry_course','entry_status','has_tkz','has_stt','has_orig']
    wanted=set(meta+v.POST_FROZEN)
    d=pd.read_csv(v.V108,encoding='utf-8-sig',dtype={'race_code':str},usecols=lambda c:c in wanted)
    d['date']=pd.to_datetime(d.date,errors='coerce')
    d=d[(d.date>=pd.Timestamp(v.START))&(d.date<=pd.Timestamp(v.END))].copy()
    n_before=len(d)
    course=pd.to_numeric(d['entry_course'],errors='coerce')
    d=d[course.eq(1)].copy()
    gate_rate=len(d)/max(1,n_before)
    if len(d)<15000:
        raise RuntimeError(f'v108 POST course1 universe too small {len(d)} / {n_before}')
    if gate_rate<.80:
        raise RuntimeError(f'v108 POST course1 gate rate implausibly low {gate_rate:.3f}')
    d['race_code']=d.race_code.astype(str).str.replace('.0','',regex=False).str.zfill(12)
    d['date']=d.date.dt.strftime('%Y-%m-%d');d['month']=d.date.str[:7]
    basecols=['date','race_code']+[c for c in pre.columns if c.startswith('b')]
    static=pre[basecols].drop_duplicates(['date','race_code'])
    d=d.merge(static,on=['date','race_code'],how='left',validate='one_to_one')
    cov=float(d[[c for c in d if c.startswith('b1_')]].notna().any(axis=1).mean())
    if cov<.98:
        raise RuntimeError(f'POST to race-card static coverage too low {cov:.3f}')
    d['venue']=d.venue.astype(str).str.replace('.0','',regex=False).str.zfill(2)
    d['universe']='POST'
    return d,cov,n_before,gate_rate


def main():
    pre,a=v.freeze_true_pre()
    post,postcov,post_before,post_gate_rate=load_frozen_post_course1(pre)
    d=pd.concat([pre,post],ignore_index=True,sort=False)
    if pd.to_datetime(d.date).max()>=pd.Timestamp('2026-07-01'):
        raise RuntimeError('Jul/Aug contamination')
    d=v.add_prior_history(d);d=v.add_rel(d)
    print('FEATURES FROZEN PRE/POST/HISTORY',len(d),'-- target settlement starts now',flush=True)
    d=v.settle_after_freeze(d)
    rcov=float(d.valid_result.mean())
    if rcov<.95:
        raise RuntimeError(f'result coverage too low {rcov:.3f}')
    p,folds,fams=v.run_variants(d);met,sel=v.v293.evaluate(p)
    audit={**a,
           'post_v108_before_course1_gate':post_before,
           'post_course1_gate_rate':post_gate_rate,
           'post_frozen':int((d.universe=='POST').sum()),
           'post_static_join_coverage':postcov,
           'result_coverage':rcov,
           'history_player_features':sum('_pl_' in c for c in d.columns),
           'history_prior_exhibition_features':sum(('_vh_' in c or '_gh_' in c) for c in d.columns)}
    aud=pd.DataFrame([{'metric':k,'value':val} for k,val in audit.items()])
    aud.to_csv(str(v.PREFIX)+'_source_audit.csv',index=False,encoding='utf-8-sig')
    folds.to_csv(str(v.PREFIX)+'_folds.csv',index=False,encoding='utf-8-sig')
    met.to_csv(str(v.PREFIX)+'_metrics.csv',index=False,encoding='utf-8-sig')
    sel.to_csv(str(v.PREFIX)+'_selection.csv',index=False,encoding='utf-8-sig')
    p.to_csv(str(v.PREFIX)+'_predictions.csv',index=False,encoding='utf-8-sig')
    v.SUMMARY.write_text(v.summary(audit,folds,met,sel,fams),encoding='utf-8')
    print(v.SUMMARY.read_text(),flush=True)


if __name__=='__main__':
    main()
