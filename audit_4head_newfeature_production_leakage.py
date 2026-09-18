#!/usr/bin/env python3
"""Production leakage + feasibility audit for HEAD4_NEWFEATURE_FIXED156_V1."""
from __future__ import annotations
from pathlib import Path
import inspect, json, math
import pandas as pd

import run_4head_120r_lastminute_fast as live

OUT=Path('/tmp/head4_newfeature_production_leakage'); OUT.mkdir(parents=True,exist_ok=True)
PROD=Path('artifacts/head4_newfeature_fixed156_production.json')
RUNNER=Path('run_4head_120r_lastminute_fast.py')
STATE=Path('prepare_4head_120r_daily_state.py')
STRICT=Path('.github/workflows/live-4head-120r-true-monitor.yml')
WATCH=Path('.github/workflows/live-4head-120r-watchdog.yml')
PRE=Path('scan_4head_120r_pre_live.py')

FORBIDDEN_SCORE_TOKENS=(
    'result','winner','payout','payoff','finish','着順','払戻',
    'raw_hit','head4','actual_second','actual_third','hit_ticket',
)

def must(cond,msg):
    if not cond: raise RuntimeError(msg)

def source_of(fn):
    return inspect.getsource(fn)

def scan_score_contract():
    art=json.loads(PROD.read_text(encoding='utf-8'))
    must(art.get('profile')=='HEAD4_NEWFEATURE_FIXED156_V1','profile drift')
    must(art.get('production_applied') is True,'production flag false')
    must(art.get('fit_period')==['2026-04','2026-05','2026-06'],'fit period drift')
    must(art.get('september_outcomes_used') is False,'artifact says September outcomes used')
    must(art.get('target_result_used') is False,'artifact says target result used')
    must(art.get('payout_used_for_live_score') is False,'artifact says payout used in score')
    must(abs(float(art.get('production_threshold'))-12.293333333333333)<1e-12,'threshold drift')
    refs=art.get('ecdf_sorted_reference') or {}
    weights=art.get('weights') or {}
    expected={'hp','mass','st','orig','market_conf','motor_win_rev','motor_2ren_rev','attack4','stwall_center','wall_rev'}
    must(set(weights)==expected,f'weight feature drift: {set(weights)}')
    must(set(refs)==expected,f'ECDF feature drift: {set(refs)}')
    for k,v in refs.items():
        must(len(v)==50,f'{k} ECDF expected 50 Apr-Jun refs, got {len(v)}')
        must(all(math.isfinite(float(x)) for x in v),f'{k} ECDF nonfinite')
        must(list(v)==sorted(v),f'{k} ECDF not sorted')

    score_src=source_of(live.score_newfeature_raw)
    decision_src=source_of(live.newfeature_decide)
    combined=(score_src+'\n'+decision_src).lower()
    bad=[t for t in FORBIDDEN_SCORE_TOKENS if t.lower() in combined]
    must(not bad,f'forbidden outcome-like token in score/decision source: {bad}')
    must("load_newfeature_artifact()" in decision_src,'decision not bound to frozen artifact')
    must("score>=threshold" in decision_src,'fixed threshold missing')
    must("legacy['base120_selected']" in decision_src,'base120 preservation missing')
    must("s['st4_adv_inside']>=st_min" in decision_src,'ST gate missing')
    must("s['orig4_adv_inside']>=orig_min" in decision_src,'ORIG gate missing')

    return {
      'profile':art['profile'],
      'fit_period':art['fit_period'],
      'threshold':art['production_threshold'],
      'feature_count':len(weights),
      'ecdf_reference_rows_per_feature':{k:len(v) for k,v in refs.items()},
      'outcome_like_tokens_in_score_source':bad,
      'status':'PASS',
    }

def scan_state_contract():
    src=STATE.read_text(encoding='utf-8')
    must("NEWFEATURE_MOTOR_START=date(2025,11,1)" in src,'newfeature motor start drift')
    must("while d<target:" in src,'daily state no target-date exclusion loop')
    must("'target_date_results_used':False" in src,'target result false marker missing')
    must("'history_end':str(target-timedelta(days=1))" in src,'history_end target-1 missing')
    must("'newfeature_motor_history_start':NEWFEATURE_MOTOR_START.isoformat()" in src,'newfeature history marker missing')

    motor_src=source_of(live.newfeature_motor_raw)
    must("'motors_newfeature_nov2025' not in state" in motor_src,'stale-state fail-close missing')
    must("raise Fast120NotReady" in motor_src,'stale-state not fail-closed')

    return {
      'target_date_excluded':True,
      'history_end':'target_date-1',
      'newfeature_motor_start':'2025-11-01',
      'stale_state_behavior':'NO_BET_DATA_NOT_READY via Fast120NotReady',
      'status':'PASS',
    }

def scan_live_deadline_contract():
    rsrc=RUNNER.read_text(encoding='utf-8')
    must("require_before_deadline(deadline,'fast120 startup')" in rsrc,'startup deadline guard missing')
    must("require_before_deadline(deadline,'before fast120 persist')" in rsrc,'persist deadline guard missing')
    must("wait_odds_ready" in rsrc,'official odds wait path missing')
    must("'predeadline_odds_used':(not a.performance_benchmark)" in rsrc,'predeadline odds marker missing')
    must("'target_race_result_used':False" in rsrc,'target result contract marker missing')
    must("'payout_used':False" in rsrc,'payout contract marker missing')

    strict=STRICT.read_text(encoding='utf-8')
    watch=WATCH.read_text(encoding='utf-8')
    marker="head4-newfeature-daily-state-${TARGET_DATE}"
    for name,src in [('strict',strict),('watchdog',watch)]:
        must(marker in src,f'{name}: new state preference missing')
        must("HEAD4_NEWFEATURE_FIXED156_V1" in src,f'{name}: production profile contract missing')
        must("z.get('target_race_result_used') is False" in src,f'{name}: result contract missing')
        must("z.get('payout_used') is False" in src,f'{name}: payout contract missing')
    return {
      'startup_before_deadline_guard':True,
      'persist_before_deadline_guard':True,
      'predeadline_odds_contract':True,
      'strict_profile_contract':True,
      'watchdog_profile_contract':True,
      'status':'PASS',
    }

def scan_pre_contract():
    src=PRE.read_text(encoding='utf-8')
    must("'target_day_results_read':False" in src,'PRE target result marker missing')
    must("'current_exhibition_used':False" in src,'PRE exhibition marker missing')
    must("'current_odds_used':False" in src,'PRE odds marker missing')
    must("parent_state_cutoff=daily_meta.get('history_end')" in src,'PRE daily state cutoff not used')
    return {
      'target_day_results_used':False,
      'current_exhibition_used':False,
      'current_odds_used':False,
      'daily_state_cutoff_used':True,
      'status':'PASS',
    }

def unit_fail_closed():
    try:
        live.newfeature_motor_raw({}, {}, 1)
    except live.Fast120NotReady as e:
        return {'status':'PASS','exception':type(e).__name__,'message':str(e)}
    raise RuntimeError('missing new-feature state did not fail closed')

def audit_research_selection():
    art=json.loads(PROD.read_text(encoding='utf-8'))
    diag=art.get('historical_diagnostic') or {}
    must(diag.get('non_pristine') is True,'historical diagnostic must remain marked non-pristine')
    return {
      'status':'WARN_NON_PRISTINE',
      'detail':'Apr-Aug outcomes/ROI were used during research and threshold/model selection. Historical ROI/head-rate are development evidence, not independent prospective performance.',
      'historical_diagnostic':diag,
    }

def main():
    score=scan_score_contract()
    state=scan_state_contract()
    livec=scan_live_deadline_contract()
    pre=scan_pre_contract()
    stale=unit_fail_closed()
    research=audit_research_selection()

    statuses=[
      {'class':'SAME_RACE_OUTCOME_LEAKAGE','status':'PASS','detail':'LIVE score/decision source has no result/payout/finish target fields; output contract marks result/payout unused.'},
      {'class':'TEMPORAL_STATE_LEAKAGE','status':'PASS','detail':'Daily state loops only through target_date-1; new motor history starts 2025-11-01; stale state fails closed.'},
      {'class':'FROZEN_TRANSFORM_LEAKAGE','status':'PASS','detail':'Weights, threshold and 50-row ECDF references per feature are frozen in the production artifact from Apr-Jun fit period.'},
      {'class':'JULAUG_LABELS_IN_LIVE_SCORE','status':'PASS','detail':'LIVE score uses only frozen artifact references and current/predecision features; Jul-Aug outcomes are not inputs to live transforms.'},
      {'class':'SEPTEMBER_TARGET_OUTCOME_CONTAMINATION','status':'PASS','detail':'Production artifact marks September outcomes unused; audited LIVE/PRE paths do not read target-race results.'},
      {'class':'MARKET_TIMING','status':'PASS_OPERATIONAL','detail':'Official decision path guards startup/persist before deadline and marks predeadline_odds_used; performance benchmark path is explicitly non-decision.'},
      {'class':'MODEL_SELECTION_CONTAMINATION','status':'WARN_NON_PRISTINE','detail':research['detail']},
    ]

    summary={
      'profile':'HEAD4_NEWFEATURE_FIXED156_V1',
      'operational_feasibility_static_contract':'PASS',
      'score_contract':score,
      'daily_state_contract':state,
      'live_deadline_contract':livec,
      'pre_contract':pre,
      'stale_state_fail_closed':stale,
      'research_selection':research,
      'audit_statuses':statuses,
      'overall_conclusion':'PASS_WITH_NONPRISTINE_RESEARCH_WARNING',
      'prospective_profitability_proven':False,
      'september_outcomes_read':False,
      'production_threshold_changed':False,
      'AUDIT_OK':True,
    }
    pd.DataFrame(statuses).to_csv(OUT/'leakage_status.csv',index=False)
    (OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    print('HEAD4_NEWFEATURE_PRODUCTION_LEAKAGE_AUDIT_OK')
    print('HEAD4_OPERATIONAL_LEAKAGE_PASS')
    print('HEAD4_MODEL_SELECTION_NONPRISTINE_WARN')
    print('SEPTEMBER_UNREAD')

if __name__=='__main__':
    main()
