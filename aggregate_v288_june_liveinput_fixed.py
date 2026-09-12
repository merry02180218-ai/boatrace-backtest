#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from collections import Counter
from pathlib import Path
import pandas as pd

EXPECTED=[f'2026-06-{d:02d}' for d in range(1,31)]
CANDIDATE_DATES={
'2026-06-01','2026-06-02','2026-06-04','2026-06-05','2026-06-06','2026-06-07',
'2026-06-09','2026-06-10','2026-06-12','2026-06-14','2026-06-17','2026-06-18',
'2026-06-19','2026-06-23','2026-06-24','2026-06-26','2026-06-28','2026-06-29'}

def loadj(p):return json.loads(p.read_text(encoding='utf-8'))

def collect(root):
    root=Path(root); out={}
    for p in root.rglob('day_summary.json'):
        z=loadj(p);d=str(z['date'])
        if d in out:raise RuntimeError(f'duplicate summary {d}: {out[d][0]} and {p}')
        csvp=p.with_name('day_replay.csv')
        out[d]=(p,z,csvp if csvp.exists() else None)
    return out

def num(row,k,default=0):
    try:
        v=row.get(k,default)
        if pd.isna(v):return default
        return float(v)
    except:return default

def iv(row,k):return int(round(num(row,k,0)))

def classify_no_bet(row):
    if str(row.get('v242_action',''))!='bet':return 'v242_not_buyable'
    v243=iv(row,'v243_pass');s=iv(row,'S_condition');a=iv(row,'A_condition');b=iv(row,'B_condition')
    if not v243 and not a and not b:return 'v243_fail_no_A_or_B_rescue'
    if v243 and not s and not a and not b:return 'v243_pass_but_S_fail_no_rescue'
    return 'route_none_other'

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--baseline',required=True);ap.add_argument('--corrected',required=True);ap.add_argument('--outdir',required=True);a=ap.parse_args()
    base=collect(a.baseline);fix=collect(a.corrected)
    missing_fix=sorted(CANDIDATE_DATES-set(fix))
    if missing_fix:raise RuntimeError(f'corrected candidate days missing: {missing_fix}')
    chosen={}
    for d in EXPECTED:
        src=fix.get(d) if d in CANDIDATE_DATES else base.get(d)
        if src is None:raise RuntimeError(f'missing final day {d}')
        chosen[d]=src

    frames=[]; daily=[]; pre=0;live_eval=0;errs=0;genuine_nb=0
    for d in EXPECTED:
        p,s,csvp=chosen[d]
        if str(s.get('history_cutoff'))!='2026-05-31':raise RuntimeError(f'{d} cutoff drift: {s.get("history_cutoff")}')
        if s.get('result_or_payout_used_for_decision') is not False or s.get('results_joined_only_after_freeze') is not True:
            raise RuntimeError(f'{d} leakage guard failed')
        pc=int(s.get('pre_candidates',0));pre+=pc
        le=int(s.get('live_evaluable',0) or 0) if d in CANDIDATE_DATES else 0
        er=int(s.get('input_or_decision_errors',0) or 0) if d in CANDIDATE_DATES else 0
        nb=int(s.get('genuine_no_bets',0) or 0) if d in CANDIDATE_DATES else 0
        live_eval+=le;errs+=er;genuine_nb+=nb
        if csvp and csvp.stat().st_size:
            try:q=pd.read_csv(csvp,dtype={'race_code':str})
            except pd.errors.EmptyDataError:q=pd.DataFrame()
            if len(q):frames.append(q)
        daily.append({'date':d,'pre_candidates':pc,'live_evaluable':le,'errors':er,'genuine_no_bets':nb,'bets':int(s.get('bets',0) or 0),'hits':int(s.get('hits',0) or 0),'stake':float(s.get('stake',0) or 0),'payout':float(s.get('payout',0) or 0),'profit':float(s.get('profit',0) or 0)})

    q=pd.concat(frames,ignore_index=True,sort=False) if frames else pd.DataFrame()
    if len(q):q['date']=q['date'].astype(str)
    cand=q[q['date'].isin(CANDIDATE_DATES)].copy() if len(q) else pd.DataFrame()
    if len(cand)!=18:raise RuntimeError(f'expected 18 candidate rows, got {len(cand)}')
    if int((cand['result_or_payout_used_for_decision']!=False).sum()):raise RuntimeError('candidate decision leakage flag')

    evaluable=cand[cand['evaluation_status'].eq('EVALUABLE')].copy()
    errors=cand[~cand['evaluation_status'].eq('EVALUABLE')].copy()
    bets=evaluable[evaluable['decision'].eq('BET')].copy();nobets=evaluable[evaluable['decision'].eq('NO_BET')].copy()
    B=len(bets);H=int(pd.to_numeric(bets.get('hit',0),errors='coerce').fillna(0).sum()) if B else 0
    stake=float(pd.to_numeric(bets.get('total_stake',0),errors='coerce').fillna(0).sum()) if B else 0
    payout=float(pd.to_numeric(bets.get('return_yen',0),errors='coerce').fillna(0).sum()) if B else 0

    route={}
    if B:
        for r,g in bets.groupby('route',dropna=False):
            st=float(pd.to_numeric(g.total_stake,errors='coerce').fillna(0).sum());rv=float(pd.to_numeric(g.return_yen,errors='coerce').fillna(0).sum());h=int(pd.to_numeric(g.hit,errors='coerce').fillna(0).sum())
            route[str(r)]={'bets':len(g),'hits':h,'hit_rate_pct':100*h/len(g),'stake':st,'payout':rv,'profit':rv-st,'roi_pct':100*rv/st if st else None}

    nb_reasons=Counter(classify_no_bet(r) for _,r in nobets.iterrows())
    err_reasons=Counter(str(x) for x in errors.get('error',pd.Series(dtype=str)).fillna('unknown'))
    conditions={
      'v242_buyable':int((evaluable.get('v242_action',pd.Series(dtype=str))=='bet').sum()),
      'v243_pass':int(pd.to_numeric(evaluable.get('v243_pass',0),errors='coerce').fillna(0).sum()) if len(evaluable) else 0,
      'S_condition':int(pd.to_numeric(evaluable.get('S_condition',0),errors='coerce').fillna(0).sum()) if len(evaluable) else 0,
      'A_condition':int(pd.to_numeric(evaluable.get('A_condition',0),errors='coerce').fillna(0).sum()) if len(evaluable) else 0,
      'B_condition':int(pd.to_numeric(evaluable.get('B_condition',0),errors='coerce').fillna(0).sum()) if len(evaluable) else 0,
    }
    source_counts={
      'odds':dict(Counter(str(x) for x in cand.get('odds_source',pd.Series(dtype=str)).fillna(''))),
      'original_exhibition':dict(Counter(str(x) for x in cand.get('orig_source',pd.Series(dtype=str)).fillna(''))),
    }
    curve=peak=mdd=0.0
    for x in daily:
        curve+=x['profit'];peak=max(peak,curve);mdd=max(mdd,peak-curve)

    detail_cols=['date','race_code','pre_grade','pre_score','pre_pct','pre_p3','evaluation_status','error_type','error','orig_source','odds_source','decision','route','p3_live','v242_action','raw_top_n','top_n','comp_odds','v243_pass','S_condition','A_condition','B_condition','b3_minus_b4_waku_st','b3_minus_b4_st','b3_meetst','wall12_weak','b3_minus_b2_motor','b3_inside_nst','total_stake','actual_combo','hit','return_yen','profit']
    for c in detail_cols:
        if c not in cand:cand[c]=''
    cand[detail_cols].sort_values(['date','race_code']).to_csv(Path(a.outdir)/'june_v288_candidate_details.csv',index=False)

    summary={'period':'2026-06-01..2026-06-30','policy':'3HEAD_V288_OPERATIONAL_MONTH_REPLAY_LIVEINPUT_FIXED','history_cutoff':'2026-05-31','pre_candidates':pre,
      'live_evaluable':len(evaluable),'input_or_decision_errors':len(errors),'genuine_no_bets':len(nobets),'bets':B,'hits':H,'hit_rate_pct':100*H/B if B else None,
      'stake':stake,'payout':payout,'profit':payout-stake,'roi_pct':100*payout/stake if stake else None,'max_drawdown_yen':mdd,
      'result_or_payout_used_for_decision':False,'results_joined_only_after_freeze':True,'route_breakdown':route,'no_bet_reason_breakdown':dict(nb_reasons),
      'input_error_breakdown':dict(err_reasons),'condition_pass_counts':conditions,'source_counts':source_counts,'daily':daily,
      'odds_caveat':'official closing odds snapshot used where legacy od3 unavailable; not exact historical purchase-time fill'}
    out=Path(a.outdir);out.mkdir(parents=True,exist_ok=True)
    (out/'summary_v288_june_liveinput_fixed.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    L=['# v288 June operational replay — LIVE inputs repaired','',f"- PRE candidates: {pre}",f"- LIVE evaluable: {len(evaluable)}",f"- Input/decision errors: {len(errors)}",f"- Genuine NO_BET: {len(nobets)}",f"- BET: {B}",f"- Hits: {H}",f"- Stake: {stake:.0f}",f"- Payout: {payout:.0f}",f"- Profit: {payout-stake:+.0f}",f"- ROI: {100*payout/stake:.2f}%" if stake else '- ROI: -',f"- Max drawdown: {mdd:.0f}",'','## Gate pass counts']
    for k,v in conditions.items():L.append(f'- {k}: {v}/{len(evaluable)}')
    L+=['','## Genuine NO_BET reasons']+[f'- {k}: {v}' for k,v in nb_reasons.items()]
    L+=['','## Input errors']+[f'- {k}: {v}' for k,v in err_reasons.items()]
    L+=['','## Route results']
    for k,v in route.items():L.append(f"- {k}: {v['bets']} bets / {v['hits']} hits / ROI {v['roi_pct']:.2f}%")
    L+=['','> Official closing odds are a closing snapshot, not an exact historical purchase-time fill.','> Target-day results/payouts are joined only after decisions are frozen.']
    (out/'summary_v288_june_liveinput_fixed.md').write_text('\n'.join(L)+'\n',encoding='utf-8')
    print('\n'.join(L));print('V288_JUNE_LIVEINPUT_FIXED_OK',json.dumps(summary,ensure_ascii=False))
if __name__=='__main__':main()
