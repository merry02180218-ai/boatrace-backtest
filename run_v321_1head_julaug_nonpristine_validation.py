#!/usr/bin/env python3
"""v321 Jul/Aug 2026 NON-PRISTINE reference validation.

Frozen stack only: v308 head gate, v317 SECOND, v318 THIRD, v320 HYBRID alpha=.70.
Jul/Aug are reference-only. September outcomes stay unread. meet_* forbidden.
Month M trains strictly on < M; missing p3/p4 are never future-backfilled.
"""
from datetime import date
from pathlib import Path
import argparse, gc
import numpy as np
import pandas as pd
import analyze_v298_1head_threat_listwise_trifecta5 as v298
import run_v300_1head_trifecta3_feature_upgrade as v300
import run_v303_1head_headmodel_transfer_ablation as v303
import run_v305_1head_leakage_audit as v305
import run_v307_1head_causal_turn_form as v307
import run_v310_1head_opponent_headrisk_second as v310
import run_v311_1head_opponent_second_family_autoresearch as v311
import run_v312_1head_opponent_outer_gate as v312
import run_v317_1head_opponent_error_features as v317
import run_v318_1head_opponent_third_rebuild as v318
import run_v299_1head_trifecta3_policy_search as v299

ROOT=Path(__file__).resolve().parent
DEV_PRED=ROOT/'analysis_v308_1head_volume_opponent_joint_pred.csv'
P=ROOT/'analysis_v321_1head_julaug_nonpristine_validation'
S=ROOT/'summary_v321_1head_julaug_nonpristine_validation.md'
PREP_SLIM=ROOT/'cache_v321_julaug_nonpristine_slim.csv.gz'
PREP_HEAD=ROOT/'cache_v321_julaug_nonpristine_head.csv'
PREP_META=ROOT/'cache_v321_julaug_nonpristine_meta.csv'
TARGET_MONTHS=['2026-07','2026-08']; Q=.98; OPP_MASS_CUT=.375; POLICY='HYBRID'; ALPHA=.70


def prepare():
    dev=pd.read_csv(DEV_PRED,dtype={'race_code':str})
    if any(str(m).startswith(('2026-07','2026-08','2026-09')) for m in dev.test_month.astype(str).unique()):
        raise RuntimeError('v321 DEV_PRED unexpectedly contains Jul/Aug/Sep')
    hcut=float(pd.to_numeric(dev.p_head,errors='coerce').quantile(Q))
    v300.setup_v298(); old_end=v298.v294.END
    try:
        v298.v294.END=date(2026,8,31); d,_=v298.v294.freeze_true_pre()
    finally: v298.v294.END=old_end
    d=v298.v294.add_prior_history(d); d=v298.v294.add_rel(d)
    d,th=v298.add_threat(d); fam=v298.v296.clean_manifest(d); d,tf=v303.add_transfer_features(d); d,ca=v307.add_causal(d)
    safe=list(dict.fromkeys(v305.safe_transfer(tf['TURN_FORM'])+v305.safe_transfer(tf['STMOTOR'])+ca))
    if any('meet_' in str(c).lower() for c in safe): raise RuntimeError('v321 unsafe head feature')
    d,_=v298.v297.settle_full_after_freeze(d); d=d[(d.valid_result==1)&(d.combo_valid==1)].copy()
    if any(str(m).startswith('2026-09') for m in d.month.astype(str).unique()): raise RuntimeError('v321 September present')
    masses=v303.opponent_mass(d); core=list(dict.fromkeys(fam['CLEAN_STATIC6_PLAYER']+th))
    guard=[c for c in core if c.startswith(('b1_','b2_','b3_','b4_','rel_','attack23_','v298_'))]
    out=[]
    for tm in TARGET_MONTHS:
        tr=d[d.month<tm].copy(); te=d[d.month==tm].copy()
        if te.empty: raise RuntimeError(f'v321 no source rows for {tm}')
        bc=v298.v293.available(tr,core,.55); bg=v298.v293.available(tr,guard,.55); ex=v303.available(tr,safe)
        ph,_,_,_,_,_=v298.head_fold(tr,te,list(dict.fromkeys(bc+ex)),bg)
        z=te[['date','month','race_code','venue','race','head_hit','actual_combo']].copy(); z.race_code=z.race_code.astype(str).str.zfill(12)
        z['p_head']=ph; z['opp_mass']=[masses.get(x,np.nan) for x in z.race_code]
        z['selected']=((z.p_head>=hcut)&(z.opp_mass>=OPP_MASS_CUT)).astype(int); out.append(z)
        del tr,te; gc.collect()
    head=pd.concat(out,ignore_index=True)
    if any('meet_' in str(c) for c in d.columns): d=d.drop(columns=[c for c in d.columns if 'meet_' in str(c)]).copy()
    v300.setup_v298(); sufs=v298.suffixes(d)
    if any('meet_' in str(x) for x in sufs): raise RuntimeError('v321 forbidden meet suffix')
    meta=['date','month','race_code','head_hit','actual_combo']; sym=[f'b{b}_{k}' for k in sufs for b in range(1,7) if f'b{b}_{k}' in d.columns]
    slim=d[list(dict.fromkeys(meta+sym))].copy(); slim.race_code=slim.race_code.astype(str).str.zfill(12)
    if any(str(m).startswith('2026-09') for m in slim.month.astype(str).unique()): raise RuntimeError('v321 slim contains September')
    head.to_csv(PREP_HEAD,index=False); slim.to_csv(PREP_SLIM,index=False,compression='gzip'); pd.DataFrame([{'hcut':hcut}]).to_csv(PREP_META,index=False)
    print(f'prepared head={len(head)} slim={len(slim)} cols={len(slim.columns)} hcut={hcut:.8f}',flush=True)


def evaluate():
    if not (PREP_SLIM.exists() and PREP_HEAD.exists() and PREP_META.exists()): raise RuntimeError('v321 prepare cache missing')
    slim=pd.read_csv(PREP_SLIM,dtype={'race_code':str}); head=pd.read_csv(PREP_HEAD,dtype={'race_code':str}); hcut=float(pd.read_csv(PREP_META).hcut.iloc[0])
    if any(str(m).startswith('2026-09') for m in slim.month.astype(str).unique()): raise RuntimeError('v321 cache contains September')
    _,p3,p4=v312.load_cache(); v300.setup_v298(); sufs=v298.suffixes(slim)
    sl=v310.add_headrisk(v300.augment_second(v298.second_long(slim,sufs)),p3,p4); sx,_=v317.add_engineered(sl,'OUTER'); del sl; gc.collect()
    p2={tm:v311.p2_predict_explicit(sx,tm,1.0,None,{'START'})[0] for tm in TARGET_MONTHS}; del sx; gc.collect()
    cl=v300.augment_third(v298.conditional_long(slim,sufs)); pc={tm:v318.pc_predict(cl,tm,.1,'DROP_START')[0] for tm in TARGET_MONTHS}; del cl; gc.collect()
    selected=head[head.selected==1].copy()
    if selected.empty: raise RuntimeError('v321 no selected races')
    rows=[]; fn=v299.STRATEGIES[POLICY]
    for _,r in selected.iterrows():
        tm=str(r.month); code=str(r.race_code).zfill(12); probs=v299.pair_prob(p2[tm][code],pc[tm][code],ALPHA); top3=fn(p2[tm][code],pc[tm][code],probs)[:3]
        if len(top3)!=3 or len(set(top3))!=3: raise RuntimeError(f'invalid ticket set {code}')
        tickets=[f'1-{s}-{t}' for s,t in top3]; actual=str(r.actual_combo)
        rows.append({'month':tm,'race_code':code,'head_hit':int(r.head_hit),'actual_combo':actual,'p_head':float(r.p_head),'opp_mass':float(r.opp_mass),'tickets':';'.join(tickets),'hit':int(actual in tickets)})
    z=pd.DataFrame(rows); gm=z.groupby('month').agg(R=('race_code','size'),head_hits=('head_hit','sum'),hits=('hit','sum')).reset_index(); gm['head_rate']=gm.head_hits/gm.R; gm['hit_rate']=gm.hits/gm.R
    R=len(z); hh=int(z.head_hit.sum()); hits=int(z.hit.sum()); z.to_csv(str(P)+'_race.csv',index=False); gm.to_csv(str(P)+'_monthly.csv',index=False)
    L=['# v321 Jul/Aug 2026 NON-PRISTINE validation','', '- **Reference only; NOT pristine and NOT eligible for promotion.**', f'- Frozen v308 head gate: development-only q=.98 cutoff **p_head>={hcut:.8f}**, opponent mass >= {OPP_MASS_CUT:.3f}.','- Frozen opponent ranking: v317 SECOND + v318 DROP_START THIRD.',f'- Frozen ticket policy: **{POLICY} alpha={ALPHA:.2f}**, exactly 3 tickets.','- Month M trains only on < M; `meet_*` forbidden; missing p3/p4 never future-backfilled; September outcomes untouched.','',f'## Result\n- Jul+Aug: R **{R}**, head **{hh}/{R}={100*hh/R:.2f}%**, exact3 **{hits}/{R}={100*hits/R:.2f}%**.','','## Monthly','|month|R|head|head rate|exact3|exact3 rate|','|---|---:|---:|---:|---:|---:|']
    for _,r in gm.iterrows(): L.append(f'|{r.month}|{int(r.R)}|{int(r.head_hits)}|{100*r.head_rate:.2f}%|{int(r.hits)}|{100*r.hit_rate:.2f}%|')
    L += ['','## Interpretation','- Contamination-aware stress check only; do not tune or promote from Jul/Aug.']
    S.write_text('\n'.join(L)+'\n',encoding='utf-8'); print(S.read_text(),flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--stage',choices=['prepare','evaluate','all'],default='all'); a=ap.parse_args()
    if a.stage in ('prepare','all'): prepare()
    if a.stage in ('evaluate','all'): evaluate()
