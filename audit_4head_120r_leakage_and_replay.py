#!/usr/bin/env python3
"""HEAD4 120R frozen research candidate: independent replay + leakage audit.

This audit separates four different concepts that are often conflated as "leakage":

1) OUTCOME LEAKAGE
   Same-race result / finish / payout fields entering the selection inputs.
2) TEMPORAL FEATURE LEAKAGE
   Future or same-day results entering prior aggregates or frozen models.
3) MARKET-TIMING LEAKAGE / PROXY MISMATCH
   Historical closing odds being used where a real live decision requires an
   immutable pre-deadline snapshot.
4) MODEL-SELECTION LEAKAGE
   Apr-Aug outcomes being used to choose the 120R rule and then reporting ROI
   on the same Apr-Aug window.

Expected conclusion:
- Outcome leakage: PASS
- Temporal feature leakage: PASS under the audited builders / frozen artifact contracts
- Closing-odds timing: WARN / NOT prospective
- Apr-Aug selection leakage: PRESENT by design, so Apr-Aug ROI is NON-PRISTINE
- September outcomes: UNREAD
- Production: unchanged
"""
from __future__ import annotations

from pathlib import Path
import hashlib
import inspect
import json
import re

import numpy as np
import pandas as pd

import audit_4head_julaug_roi_collapse_attribution as src
import audit_4head_boatracecsv_headprob_leakage as hp
import audit_4head_headprob_pass_rescue as hprescue
import audit_4head_86r_v283_closing_odds as oddsmod
import analyze_4head_b4_minus_b3_motor_win_2ren as motor
import analyze_4head_headrate_3ren_player_st as prior
import analyze_4head_exhibition_original_trainonly as exhib
import head4_v291_downstream_inference as frozen

OUT=Path('/tmp/head4_120r_leakage_replay'); OUT.mkdir(parents=True,exist_ok=True)

EXPECTED_MEMBERSHIP_SHA256='37057b43e344309e3fd06dfa1f2b519cfaad16379e92bfda51166da42834844c'
EXPECTED_R=120

FORBIDDEN_FEATURE_TOKENS=(
    'winner','result','payout','payoff','finish','着順','払戻',
    'actual_second','actual_third','head4','raw_hit','hit_ticket',
)
ODDS_TOKENS=('odds','オッズ')


def sha_codes(codes):
    s='\n'.join(sorted(map(str,codes)))+'\n'
    return hashlib.sha256(s.encode('utf-8')).hexdigest()


def independent_mask(rd):
    # Intentionally re-expressed here rather than importing the search script.
    cur=rd['composite_odds'].ge(7.0)
    base77=(
        (cur & rd['opponent_mass'].ge(.425)) |
        ((~cur) & rd['head_prob'].ge(.22) &
         rd['opponent_mass'].ge(.375) & rd['composite_odds'].ge(3.0))
    )
    score=rd['head_prob'] + 1.50*rd['opponent_mass']
    selected=base77 | ((~base77) & rd['composite_odds'].ge(2.5) & score.ge(.82))
    return cur,base77,selected,score


def scan_frozen_artifact():
    a=frozen.load_artifact()
    feature_map={}
    bad=[]
    odds_named=[]
    for state_name in ('POST','ENV_ENTRY','v283_SECOND','v283_COND_THIRD'):
        fs=list(a[state_name]['features'])
        feature_map[state_name]=fs
        for f in fs:
            lo=str(f).lower()
            if any(tok.lower() in lo for tok in FORBIDDEN_FEATURE_TOKENS):
                bad.append((state_name,f))
            if any(tok.lower() in lo for tok in ODDS_TOKENS):
                odds_named.append((state_name,f))
    parity=a['parity']
    train_dates=[
        str(parity['POST']['max_training_date']),
        str(parity['ENV_ENTRY']['max_training_date']),
        str(parity['v283']['max_training_date']),
    ]
    if any(x>'2026-06-30' for x in train_dates):
        raise RuntimeError(f'frozen artifact training cutoff escaped: {train_dates}')
    if a.get('jul_aug_labels_used') is not False or a.get('september_labels_used') is not False:
        raise RuntimeError('frozen artifact metadata reports holdout/future labels used')
    if bad:
        raise RuntimeError(f'forbidden outcome-like frozen feature names: {bad[:20]}')
    return a,feature_map,odds_named,train_dates


def audit_headprob_contract():
    # Static source-contract checks on the exact scorer used in the 164R rebuild.
    s=inspect.getsource(hprescue.headprob_scores)
    required=[
        "tr=z[z.month.isin(hp.TRAIN_MONTHS)]",
        "va=z[z.month.isin(hp.VALID_MONTHS)]",
        "m.fit(tr[feats],tr.head4)",
        "va['head_prob']=m.predict_proba(va[feats])[:,1]",
    ]
    miss=[x for x in required if x not in s]
    if miss:
        raise RuntimeError(f'headprob train/validation contract drift: {miss}')

    hs=inspect.getsource(hp.main)
    if "forbidden=[c for c in feats" not in hs or "結果列の学習混入" not in hs:
        raise RuntimeError('headprob leakage guard contract missing')
    return {
      'train_months':sorted(hp.TRAIN_MONTHS),
      'validation_months':sorted(hp.VALID_MONTHS),
      'fit_scope':'Apr-Jun only',
      'JulAug_usage':'predict only in headprob model itself',
      'note':'Apr-Jun predictions are in-sample; Jul-Aug predictions are model-OOS, but 120R rule selection later uses Apr-Aug outcomes.'
    }


def audit_prior_causality_contracts():
    out={}

    sm=inspect.getsource(motor.build_motor_features)
    p_feat=sm.find("if d>=START")
    p_result=sm.find("result_map=bycode(rows(f'data/results/realtime")
    if p_feat<0 or p_result<0 or p_feat>=p_result:
        raise RuntimeError('motor feature/result ordering contract failed')
    if "result read occurs only after the entire day's features are frozen" not in sm:
        raise RuntimeError('motor causal guard comment/contract missing')
    out['motor_prior']='PASS: same-day features frozen before daily results are ingested'

    sp=inspect.getsource(prior.build_prior_features)
    p_rec=sp.find("rec.append")
    p_res=sp.find("rm=bycode(rows(f'data/results/realtime")
    if p_rec<0 or p_res<0 or p_rec>=p_res:
        raise RuntimeError('player/motor prior feature/result ordering contract failed')
    if "freeze all same-day inputs before ingesting results" not in sp:
        raise RuntimeError('prior causal guard missing')
    out['player_motor_prior']='PASS: all same-day prior features emitted before result ingestion'

    se=inspect.getsource(exhib.build_ex)
    p_bias=se.find("bias=st_bias")
    p_update=se.find("update_st(strows,sums,allv)")
    if p_bias<0 or p_update<0 or p_bias>=p_update:
        raise RuntimeError('exhibition ST bias chronology contract failed')
    out['exhibition_bias']='PASS: historical ST bias computed before current-day ST rows update history'

    return out


def market_timing_contract():
    s=inspect.getsource(oddsmod.odds_for_date)
    req=[
        "source_type.astype(str)=='official_closing'",
        "snapshot_type.astype(str)=='closing_displayed'",
    ]
    miss=[x for x in req if x not in s]
    if miss:
        raise RuntimeError(f'closing-odds source contract drift: {miss}')
    return {
      'status':'WARN_NOT_PROSPECTIVE',
      'source':'official_closing / closing_displayed',
      'meaning':'retrospective closing-odds proxy; not proof of immutable pre-deadline availability',
      'production_requirement':'timestamped immutable pre-deadline odds snapshot'
    }


def main():
    rd=src.rebuild()
    rd['race_code']=rd.race_code.astype(str).str.zfill(12)
    if len(rd)!=164 or int(rd.head4.sum())!=70 or int(rd.raw_hit.sum())!=35:
        raise RuntimeError('fixed 164R replay drift')
    if rd.month.astype(str).ge('2026-09').any():
        raise RuntimeError('September outcome access blocked')

    cur,base77,sel120,quality=independent_mask(rd)
    if int(base77.sum())!=77:
        raise RuntimeError(f'base77 independent replay drift: {int(base77.sum())}')
    if int(sel120.sum())!=EXPECTED_R:
        raise RuntimeError(f'120R independent replay drift: {int(sel120.sum())}')
    membership_sha=sha_codes(rd.loc[sel120,'race_code'])
    if membership_sha!=EXPECTED_MEMBERSHIP_SHA256:
        raise RuntimeError(f'membership hash drift {membership_sha}')

    # Selection-mask dependency is explicit and independently re-expressed above.
    selection_inputs=['head_prob','opponent_mass','composite_odds']
    forbidden_in_mask=[x for x in selection_inputs if any(t.lower() in x.lower() for t in FORBIDDEN_FEATURE_TOKENS)]
    if forbidden_in_mask:
        raise RuntimeError(f'outcome-like selection input: {forbidden_in_mask}')

    artifact,feature_map,artifact_odds_named,train_dates=scan_frozen_artifact()
    hp_contract=audit_headprob_contract()
    prior_contracts=audit_prior_causality_contracts()
    market=market_timing_contract()

    # Candidate reconstruction starts from settled historical rows.
    settle_src=inspect.getsource(__import__('analyze_4head_b4_minus_b3_motor_full_universe').settle_all)
    sample_warn=(
      "valid historical result and archived-odds coverage are required by the retrospective "
      "settle_all universe; this is coverage/sample-selection bias risk, not same-row target leakage"
      if ("actual=v251.actual_map" in settle_src and "load_odds()" in settle_src)
      else "retrospective universe contract not recognized"
    )

    # Retrospective ROI for parity only.
    b=rd[sel120]
    roi=100*float(b.payout_if_bet.sum())/(10000*len(b))
    monthly=[]
    for mo,g in b.groupby('month'):
        monthly.append({
          'month':mo,'R':len(g),
          'ROI':100*float(g.payout_if_bet.sum())/(10000*len(g))
        })

    statuses=[
      {
        'class':'OUTCOME_LEAKAGE',
        'status':'PASS',
        'detail':'120R membership formula uses only head_prob, opponent_mass, composite_odds/current_bet; result/payout fields are used only for retrospective evaluation after membership.'
      },
      {
        'class':'TEMPORAL_FEATURE_LEAKAGE',
        'status':'PASS_WITH_CONTRACTS',
        'detail':'head_prob fit is Apr-Jun only; frozen downstream artifact cutoff <=2026-06-30; causal prior builders freeze same-day features before ingesting results.'
      },
      {
        'class':'MARKET_TIMING_LEAKAGE',
        'status':'WARN_NOT_PROSPECTIVE',
        'detail':'historical composite_odds/current_bet are reconstructed from official closing_displayed odds, not immutable timestamped pre-deadline snapshots.'
      },
      {
        'class':'MODEL_SELECTION_LEAKAGE',
        'status':'PRESENT_NON_PRISTINE',
        'detail':'Apr-Aug outcomes/ROI were used to choose the 120R thresholds and then summarize Apr-Aug ROI. Those ROI numbers are development/model-selection evidence, not independent holdout evidence.'
      },
      {
        'class':'RETROSPECTIVE_SAMPLE_SELECTION',
        'status':'WARN',
        'detail':sample_warn
      },
      {
        'class':'SEPTEMBER_CONTAMINATION',
        'status':'PASS',
        'detail':'September 2026 outcomes remain UNREAD by audited paths.'
      },
    ]

    summary={
      'candidate':'HEAD4_RESEARCH_NESTED_LINEAR_120R_20260918',
      'independent_replay':{
        'population_R':len(rd),
        'base77_R':int(base77.sum()),
        'selected_R':int(sel120.sum()),
        'membership_sha256':membership_sha,
        'expected_membership_sha256':EXPECTED_MEMBERSHIP_SHA256,
        'retrospective_ROI_pct':roi,
        'monthly':monthly,
      },
      'selection_formula':{
        'base77':'(comp>=7 & mass>=.425) OR (comp<7 & head_prob>=.22 & mass>=.375 & comp>=3.0)',
        'extra':'outside base77 AND comp>=2.5 AND head_prob + 1.50*opponent_mass >= .82',
        'same_race_result_fields_in_membership':False,
      },
      'headprob_contract':hp_contract,
      'frozen_downstream':{
        'cutoff':artifact['frozen_training_cutoff'],
        'training_max_dates':train_dates,
        'jul_aug_labels_used':artifact['jul_aug_labels_used'],
        'september_labels_used':artifact['september_labels_used'],
        'parity_status':artifact['parity']['status'],
        'feature_counts':{k:len(v) for k,v in feature_map.items()},
        'outcome_like_feature_names':[],
        'odds_named_features':artifact_odds_named,
      },
      'prior_causality':prior_contracts,
      'market_timing':market,
      'audit_statuses':statuses,
      'overall_conclusion':'RESEARCH_REPLAY_PASS__PRODUCTION_BLOCKED_BY_NONPRISTINE_SELECTION_AND_CLOSING_ODDS_PROXY',
      'formal_prospective_roi':'NOT_COMPUTABLE',
      'september_2026':'UNREAD',
      'production_changed':False,
    }

    pd.DataFrame(statuses).to_csv(OUT/'leakage_status.csv',index=False)
    pd.DataFrame(monthly).to_csv(OUT/'monthly_parity.csv',index=False)
    pd.DataFrame({
      'race_code':rd.race_code,
      'base77':base77.astype(int),
      'selected120':sel120.astype(int),
      'head_prob':rd.head_prob,
      'opponent_mass':rd.opponent_mass,
      'composite_odds':rd.composite_odds,
      'quality':quality,
    }).to_csv(OUT/'membership_replay.csv',index=False)
    (OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2,default=float)+'\n')

    print('HEAD4_120R_INDEPENDENT_REPLAY_OK',EXPECTED_R,membership_sha)
    print('HEAD4_120R_OUTCOME_LEAKAGE_PASS')
    print('HEAD4_120R_TEMPORAL_LEAKAGE_PASS')
    print('HEAD4_120R_MARKET_TIMING_WARN_CLOSING_ODDS_PROXY')
    print('HEAD4_120R_MODEL_SELECTION_NON_PRISTINE')
    print('HEAD4_120R_PRODUCTION_NOT_APPROVED')
    print('9月_UNREAD')
    print('本番変更なし')

if __name__=='__main__':
    main()
