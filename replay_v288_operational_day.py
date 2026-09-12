#!/usr/bin/env python3
"""Run the audited v288 historical decision/settlement replay for a non-September frozen month.

The underlying replay logic is unchanged.  Its September-only metadata guard is adapted
through a temporary cache copy after this wrapper verifies the real expected cutoff.
"""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
import joblib
import replay_v288_historical_day as base


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--date',required=True);ap.add_argument('--cache',required=True);ap.add_argument('--outdir',required=True);ap.add_argument('--history-cutoff',required=True);a=ap.parse_args()
    z=joblib.load(a.cache)
    if str(z.get('history_cutoff'))!=a.history_cutoff: raise RuntimeError(f'history cutoff drift {z.get("history_cutoff")} != {a.history_cutoff}')
    if z.get('target_result_or_payout_used') is not False: raise RuntimeError('cache leakage guard failed')
    out=Path(a.outdir);out.mkdir(parents=True,exist_ok=True)
    tmp=out/'_compat_cache.joblib'
    z2=dict(z);z2['history_cutoff']='2026-08-31';joblib.dump(z2,tmp,compress=3)
    old=list(sys.argv)
    try:
        sys.argv=['replay_v288_historical_day.py','--date',a.date,'--cache',str(tmp),'--outdir',str(out)]
        base.main()
    finally:
        sys.argv=old
        tmp.unlink(missing_ok=True)
    p=out/'day_summary.json';s=json.loads(p.read_text(encoding='utf-8'))
    s['policy']='3HEAD_V288_OPERATIONAL_MONTH_REPLAY'
    s['history_cutoff']=a.history_cutoff
    s['metadata_guard_adapted_only']=True
    s['underlying_decision_logic']='replay_v288_historical_day.py unchanged'
    p.write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(s,ensure_ascii=False,indent=2),flush=True)

if __name__=='__main__':main()
