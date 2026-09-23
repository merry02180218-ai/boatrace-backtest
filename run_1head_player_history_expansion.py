#!/usr/bin/env python3
from __future__ import annotations
"""1HEAD expansion PLAYER_HISTORY research scaffold.

Safety contract:
- production LIVE165/v351 is untouched;
- research population is expansion band only: H078_M375 - LIVE165;
- PLAYER_HISTORY is causal state built from races strictly before each target date;
- selection/tuning must use Feb-Jun DEV only;
- Jul-Aug is SUPPORT only;
- September outcomes/payouts remain unread.

This first stage audits coverage and emits causal player-history features for the
frozen expansion population. It intentionally does not promote any rule.
"""
from pathlib import Path
import argparse,json,pickle
import pandas as pd
import onehead_production_profile as prod
from build_4head_player_history_live import build, REQUIRED

DEV=('2026-02','2026-03','2026-04','2026-05','2026-06')
SUP=('2026-07','2026-08')
OUT=Path('/tmp/1head-player-history-expansion'); OUT.mkdir(parents=True,exist_ok=True)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--prepared',required=True,type=Path,
                    help='Frozen prepared pickle containing rows[LIVE165] and rows[H078_M375].')
    ap.add_argument('--history-start',default='2025-10-01')
    a=ap.parse_args()
    if not prod.SEPTEMBER_OUTCOMES_MUST_REMAIN_UNREAD:
        raise RuntimeError('September guard disabled')
    x=pickle.load(a.prepared.open('rb')); rr=x['rows']
    if len(rr['LIVE165'])!=165 or len(rr['H078_M375'])!=236:
        raise RuntimeError('frozen universe drift')
    live={str(r['race_code']).zfill(12) for r in rr['LIVE165']}
    added=[r for r in rr['H078_M375'] if str(r['race_code']).zfill(12) not in live]
    if len(added)!=71: raise RuntimeError(f'expansion band drift {len(added)}')
    if any(str(r['race_code']).zfill(12)[:8]>='20260901' for r in added):
        raise RuntimeError('September entered expansion research population')

    # The prepared rows must carry the six target player names/card fields. We
    # deliberately fail closed if they do not, rather than silently joining by
    # future/result-bearing data.
    out=[]; missing=[]
    from datetime import date
    for r in added:
        code=str(r['race_code']).zfill(12)
        card={'レースコード':code}
        ok=True
        for b in range(1,7):
            v=r.get(f'艇{b}_選手名')
            if not v: ok=False
            card[f'艇{b}_選手名']=v or ''
        if not ok:
            missing.append(code); continue
        td=date.fromisoformat(f'{code[:4]}-{code[4:6]}-{code[6:8]}')
        z=build(card,td,date.fromisoformat(a.history_start))
        row={'race_code':code,'month':f'{code[:4]}-{code[4:6]}',
             'p_head':float(r['p_head']),'opp_mass':float(r['opp_mass'])}
        row.update(z['player_flat'])
        # Relative primitives: lane1 minus strongest opponent and lane1 minus
        # mean opponents. These are result-free at target time.
        for k in REQUIRED:
            one=float(row[f'b1_pl_{k}'])
            opp=[float(row[f'b{b}_pl_{k}']) for b in range(2,7)]
            row[f'pl1_minus_oppmax_{k}']=one-max(opp)
            row[f'pl1_minus_oppmean_{k}']=one-sum(opp)/len(opp)
        out.append(row)

    df=pd.DataFrame(out)
    if len(df): df.to_csv(OUT/'features.csv',index=False)
    meta={
      'population':'H078_M375_MINUS_LIVE165','expected_R':71,
      'feature_R':int(len(df)),'missing_card_R':len(missing),
      'missing_codes':missing,
      'dev_months':DEV,'support_months':SUP,
      'player_history_features':list(REQUIRED),
      'selection_used_support_outcomes':False,
      'september_outcomes_read':False,
      'production_changed':False,
      'result_or_payout_used_as_score_input':False,
      'stage':'COVERAGE_AND_CAUSAL_FEATURE_AUDIT',
      'audit_ok':len(missing)==0 and len(df)==71,
    }
    (OUT/'result.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(meta,ensure_ascii=False,indent=2))
    if not meta['audit_ok']:
        raise RuntimeError('PLAYER_HISTORY coverage audit failed; fix causal card source before scoring')

if __name__=='__main__': main()
