#!/usr/bin/env python3
"""v321 Jul/Aug 2026 NON-PRISTINE reference validation.

Frozen stack only: v308 head gate, v317 SECOND, v318 THIRD, v320 HYBRID alpha=.70.
Jul/Aug are reference-only. September outcomes stay unread. meet_* forbidden.
Month M trains strictly on < M; missing p3/p4 are never future-backfilled.
"""
from datetime import date
from pathlib import Path
import argparse, gc, pickle
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
SECOND_PKL=ROOT/'cache_v321_julaug_second.pkl'
BASE_PC_PKL=ROOT/'cache_v321_julaug_base_pc.pkl'
THIRD_PKL=ROOT/'cache_v321_julaug_third.pkl'
TARGET_MONTHS=['2026-07','2026-08']
Q=.98
OPP_MASS_CUT=.375
POLICY='HYBRID'
ALPHA=.70


def _load_slim():
    if not PREP_SLIM.exists(): raise RuntimeError('v321 prepare slim cache missing')
    slim=pd.read_csv(PREP_SLIM,dtype={'race_code':str})
    if any(str(m).startswith('2026-09') for m in slim.month.astype(str).unique()):
        raise RuntimeError('v321 cache contains September')
    return slim


def prepare():
    dev=pd.read_csv(DEV_PRED,dtype={'race_code':str})
    if any(str(m).startswith(('2026-07','2026-08','2026-09')) for m in dev.test_month.astype(str).unique()):
        raise RuntimeError('v321 DEV_PRED unexpectedly contains Jul/Aug/Sep')
    hcut=float(pd.to_numeric(dev.p_head,errors='coerce').quantile(Q))
    v300.setup_v298(); old_end=v298.v294.END
    try:
        v298.v294.END=date(2026,8,31); d,_=v298.v294.freeze_true_pre()
    finally:
        v298.v294.END=old_end
    d=v298.v294.add_prior_history(d); d=v298.v294.add_rel(d); d,th=v298.add_threat(d)
    fam=v298.v296.clean_manifest(d); d,tf=v303.add_transfer_features(d); d,ca=v307.add_causal(d)
    safe=list(dict.fromkeys(v305.safe_transfer(tf['TURN_FORM'])+v305.safe_transfer(tf['STMOTOR'])+ca))
    if any('meet_' in str(c).lower() for c in safe): raise RuntimeError('v321 unsafe head feature')
    d,_=v298.v297.settle_full_after_freeze(d); d=d[(d.valid_result==1)&(d.combo_valid==1)].copy()
    if any(str(m).startswith('2026-09') for m in d.month.astype(str).unique()): raise RuntimeError('v321 September present')
    if any('meet_' in str(c).lower() for c in d.columns):
        d=d.drop(columns=[c for c in d.columns if 'meet_' in str(c).lower()]).copy()
    core=list(dict.fromkeys(fam['CLEAN_STATIC6_PLAYER']+th))
    guard=[c for c in core if c.startswith(('b1_','b2_','b3_','b4_','rel_','attack23_','v298_'))]
    v300.setup_v298(); sufs=v298.suffixes(d)
    if any('meet_' in str(x).lower() for x in sufs): raise RuntimeError('v321 forbidden meet suffix')
    slim_meta=['date','month','race_code','head_hit','actual_combo']
    sym=[f'b{b}_{k}' for k in sufs for b in range(1,7) if f'b{b}_{k}' in d.columns]
    slim=d[list(dict.fromkeys(slim_meta+sym))].copy(); slim.race_code=slim.race_code.astype(str).str.zfill(12)
    if any(str(m).startswith('2026-09') for m in slim.month.astype(str).unique()): raise RuntimeError('v321 slim contains September')
    head_meta=['date','month','race_code','venue','race','head_hit','actual_combo']
    head_cols=list(dict.fromkeys(head_meta+core+safe)); missing=[c for c in head_cols if c not in d.columns]
    if missing: raise RuntimeError(f'v321 required head columns missing n={len(missing)} sample={missing[:8]}')
    hd=d[head_cols].copy(); del d; gc.collect()
    print(f'v321 narrowed head frame rows={len(hd)} cols={len(hd.columns)}; opponent slim cols={len(slim.columns)}',flush=True)
    out=[]
    for tm in TARGET_MONTHS:
        print(f'v321 head fold start {tm}',flush=True)
        tr=hd.loc[hd.month<tm].copy(); te=hd.loc[hd.month==tm].copy()
        if te.empty: raise RuntimeError(f'v321 no source rows for {tm}')
        bc=v298.v293.available(tr,core,.55); bg=v298.v293.available(tr,guard,.55); ex=v303.available(tr,safe)
        ph,_,_,_,_,_=v298.head_fold(tr,te,list(dict.fromkeys(bc+ex)),bg)
        z=te[['date','month','race_code','venue','race','head_hit','actual_combo']].copy(); z.race_code=z.race_code.astype(str).str.zfill(12); z['p_head']=ph
        out.append(z); print(f'v321 head fold done {tm} train={len(tr)} test={len(te)} features={len(set(bc+ex))}',flush=True)
        del tr,te; gc.collect()
    head=pd.concat(out,ignore_index=True); head.to_csv(PREP_HEAD,index=False); slim.to_csv(PREP_SLIM,index=False,compression='gzip')
    pd.DataFrame([{'hcut':hcut}]).to_csv(PREP_META,index=False)
    print(f'prepared head={len(head)} slim={len(slim)} cols={len(slim.columns)} hcut={hcut:.8f}',flush=True)


def second_stage():
    slim=_load_slim(); _,p3,p4=v312.load_cache(); v300.setup_v298(); sufs=v298.suffixes(slim)
    print(f'v321 SECOND build rows={len(slim)} cols={len(slim.columns)}',flush=True)
    sl=v300.augment_second(v298.second_long(slim,sufs))
    base_p2={tm:v300.p2_predict(sl,tm,10.0,False)[0] for tm in TARGET_MONTHS}
    sl_hr=v310.add_headrisk(sl,p3,p4); sx,_=v317.add_engineered(sl_hr,'OUTER'); del sl,sl_hr; gc.collect()
    p2={tm:v311.p2_predict_explicit(sx,tm,1.0,None,{'START'})[0] for tm in TARGET_MONTHS}; del sx; gc.collect()
    with SECOND_PKL.open('wb') as f: pickle.dump({'base_p2':base_p2,'p2':p2},f,pickle.HIGHEST_PROTOCOL)
    print(f'v321 SECOND artifact ready {SECOND_PKL.name}',flush=True)


def base_third_stage():
    slim=_load_slim(); v300.setup_v298(); sufs=v298.suffixes(slim)
    print(f'v321 BASE THIRD build rows={len(slim)} cols={len(slim.columns)}',flush=True)
    cl=v300.augment_third(v298.conditional_long(slim,sufs))
    base_pc={tm:v300.pc_predict(cl,tm,.3,False)[0] for tm in TARGET_MONTHS}
    with BASE_PC_PKL.open('wb') as f: pickle.dump(base_pc,f,pickle.HIGHEST_PROTOCOL)
    print(f'v321 BASE THIRD artifact ready {BASE_PC_PKL.name}',flush=True)


def third_stage():
    slim=_load_slim(); v300.setup_v298(); sufs=v298.suffixes(slim)
    print(f'v321 FROZEN THIRD build rows={len(slim)} cols={len(slim.columns)}',flush=True)
    cl=v300.augment_third(v298.conditional_long(slim,sufs))
    pc={tm:v318.pc_predict(cl,tm,.1,'DROP_START')[0] for tm in TARGET_MONTHS}
    with THIRD_PKL.open('wb') as f: pickle.dump(pc,f,pickle.HIGHEST_PROTOCOL)
    print(f'v321 FROZEN THIRD artifact ready {THIRD_PKL.name}',flush=True)


def score_stage():
    req=(PREP_HEAD,PREP_META,SECOND_PKL,BASE_PC_PKL,THIRD_PKL)
    if not all(x.exists() for x in req): raise RuntimeError('v321 scoring artifact missing')
    head=pd.read_csv(PREP_HEAD,dtype={'race_code':str}); hcut=float(pd.read_csv(PREP_META).hcut.iloc[0])
    if any(str(m).startswith('2026-09') for m in head.month.astype(str).unique()): raise RuntimeError('v321 head cache contains September')
    with SECOND_PKL.open('rb') as f: sec=pickle.load(f)
    with BASE_PC_PKL.open('rb') as f: base_pc=pickle.load(f)
    with THIRD_PKL.open('rb') as f: pc=pickle.load(f)
    base_p2=sec['base_p2']; p2=sec['p2']; masses={}
    for tm in TARGET_MONTHS:
        codes=head.loc[head.month.astype(str)==tm,'race_code'].astype(str).str.zfill(12).unique()
        for code in codes:
            if code in base_p2[tm] and code in base_pc[tm]: masses[code]=v300.base5(base_p2[tm][code],base_pc[tm][code])[1]
    head['opp_mass']=[masses.get(str(x).zfill(12),np.nan) for x in head.race_code]
    if head.opp_mass.isna().all(): raise RuntimeError('v321 Jul/Aug opponent mass unavailable')
    head['selected']=((pd.to_numeric(head.p_head,errors='coerce')>=hcut)&(pd.to_numeric(head.opp_mass,errors='coerce')>=OPP_MASS_CUT)).astype(int)
    selected=head[head.selected==1].copy()
    if selected.empty: raise RuntimeError('v321 no selected races')
    rows=[]; fn=v299.STRATEGIES[POLICY]
    for _,r in selected.iterrows():
        tm=str(r.month); code=str(r.race_code).zfill(12)
        if code not in p2[tm] or code not in pc[tm]: raise RuntimeError(f'v321 frozen opponent prediction missing {tm} {code}')
        probs=v299.pair_prob(p2[tm][code],pc[tm][code],ALPHA); top3=fn(p2[tm][code],pc[tm][code],probs)[:3]
        if len(top3)!=3 or len(set(top3))!=3: raise RuntimeError(f'invalid ticket set {code}')
        tickets=[f'1-{s}-{t}' for s,t in top3]; actual=str(r.actual_combo)
        rows.append({'month':tm,'race_code':code,'head_hit':int(r.head_hit),'actual_combo':actual,'p_head':float(r.p_head),'opp_mass':float(r.opp_mass),'tickets':';'.join(tickets),'hit':int(actual in tickets)})
    z=pd.DataFrame(rows); gm=z.groupby('month').agg(R=('race_code','size'),head_hits=('head_hit','sum'),hits=('hit','sum')).reset_index(); gm['head_rate']=gm.head_hits/gm.R; gm['hit_rate']=gm.hits/gm.R
    R=len(z); hh=int(z.head_hit.sum()); hits=int(z.hit.sum()); z.to_csv(str(P)+'_race.csv',index=False); gm.to_csv(str(P)+'_monthly.csv',index=False)
    L=['# v321 Jul/Aug 2026 NON-PRISTINE validation','', '- **Reference only; NOT pristine and NOT eligible for promotion.**', f'- Frozen v308 head gate: development-only q=.98 cutoff **p_head>={hcut:.8f}**, opponent mass >= {OPP_MASS_CUT:.3f}.','- Jul/Aug opponent mass is reconstructed with the frozen v308 BASE opponent model, month M trained only on < M.','- Frozen opponent ranking: v317 SECOND + v318 DROP_START THIRD.',f'- Frozen ticket policy: **{POLICY} alpha={ALPHA:.2f}**, exactly 3 tickets.','- `meet_*` forbidden; missing p3/p4 never future-backfilled; September outcomes untouched.','',f'## Result\n- Jul+Aug: R **{R}**, head **{hh}/{R}={100*hh/R:.2f}%**, exact3 **{hits}/{R}={100*hits/R:.2f}%**.','','## Monthly','|month|R|head|head rate|exact3|exact3 rate|','|---|---:|---:|---:|---:|---:|']
    for _,r in gm.iterrows(): L.append(f'|{r.month}|{int(r.R)}|{int(r.head_hits)}|{100*r.head_rate:.2f}%|{int(r.hits)}|{100*r.hit_rate:.2f}%|')
    L += ['','## Interpretation','- Contamination-aware stress check only; do not tune or promote from Jul/Aug.']
    S.write_text('\n'.join(L)+'\n',encoding='utf-8'); print(S.read_text(),flush=True)


if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--stage',choices=['prepare','second','base-third','third','score'],required=True); a=ap.parse_args()
    {'prepare':prepare,'second':second_stage,'base-third':base_third_stage,'third':third_stage,'score':score_stage}[a.stage]()
