#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path
import pandas as pd

EXPECTED=[f'2026-06-{d:02d}' for d in range(1,31)]

def load_json(p): return json.loads(p.read_text(encoding='utf-8'))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',default='june_all');ap.add_argument('--outdir',default='.')
    a=ap.parse_args();root=Path(a.root);out=Path(a.outdir);out.mkdir(parents=True,exist_ok=True)
    summaries={};inputs={};productions={};frames=[]
    for p in root.rglob('day_summary.json'):
        z=load_json(p);d=z['date']
        if d in summaries:raise RuntimeError(f'duplicate day summary {d}: {p}')
        summaries[d]=z
    for p in root.rglob('input_manifest.json'):
        z=load_json(p);d=z['target_date']
        if d in inputs:raise RuntimeError(f'duplicate input manifest {d}: {p}')
        inputs[d]=z
    for p in root.rglob('production_manifest.json'):
        z=load_json(p);d=z['target_date']
        if d in productions:raise RuntimeError(f'duplicate production manifest {d}: {p}')
        productions[d]=z
    for p in root.rglob('day_replay.csv'):
        try:q=pd.read_csv(p,dtype={'race_code':str})
        except pd.errors.EmptyDataError:continue
        if len(q):frames.append(q)
    for name,m in [('summary',summaries),('input',inputs),('production',productions)]:
        miss=[d for d in EXPECTED if d not in m];extra=[d for d in m if d not in EXPECTED]
        if miss or extra:raise RuntimeError(f'{name} coverage miss={miss} extra={extra}')
    for d in EXPECTED:
        s=summaries[d];p=productions[d];i=inputs[d]
        if str(s.get('history_cutoff'))!='2026-05-31':raise RuntimeError(f'{d} summary cutoff drift')
        if str(p.get('history_cutoff'))!='2026-05-31':raise RuntimeError(f'{d} production cutoff drift')
        if s.get('result_or_payout_used_for_decision') is not False or s.get('results_joined_only_after_freeze') is not True:
            raise RuntimeError(f'{d} settlement leakage guard failed')
        if p.get('result_or_payout_used') is not False or p.get('evaluation_month_rows_removed_from_training_frame') is not True or p.get('pre_score_training_filtered_before_month_first') is not True:
            raise RuntimeError(f'{d} production leakage guard failed')
        if i.get('result_or_payout_used') is not False or i.get('current_exhibition_used') is not False:
            raise RuntimeError(f'{d} PRE input leakage guard failed')
    q=pd.concat(frames,ignore_index=True,sort=False) if frames else pd.DataFrame()
    if len(q):
        q['date']=q['date'].astype(str)
        if any(~q.date.isin(EXPECTED)):raise RuntimeError('replay CSV contains out-of-period rows')
        q.to_csv(out/'analysis_v288_june_operational_replay.csv',index=False)
    else:(out/'analysis_v288_june_operational_replay.csv').write_text('',encoding='utf-8')
    bets=q[q.decision.eq('BET')].copy() if len(q) else pd.DataFrame()
    B=len(bets);H=int(bets.hit.sum()) if B else 0
    stake=float(bets.total_stake.sum()) if B else 0.;ret=float(bets.return_yen.sum()) if B else 0.
    candidates=sum(int(summaries[d].get('pre_candidates',0)) for d in EXPECTED)
    route={}
    if B:
        for r,g in bets.groupby('route',sort=True):
            n=len(g);h=int(g.hit.sum());st=float(g.total_stake.sum());rv=float(g.return_yen.sum())
            route[str(r)]={'bets':n,'hits':h,'hit_rate_pct':100*h/n,'stake':st,'payout':rv,'profit':rv-st,'roi_pct':100*rv/st if st else None}
    curve=0.;peak=0.;mdd=0.
    daily=[]
    for d in EXPECTED:
        s=summaries[d];profit=float(s.get('profit',0));curve+=profit;peak=max(peak,curve);mdd=max(mdd,peak-curve)
        daily.append({'date':d,'pre_candidates':int(s.get('pre_candidates',0)),'bets':int(s.get('bets',0)),'hits':int(s.get('hits',0)),'stake':float(s.get('stake',0)),'payout':float(s.get('payout',0)),'profit':profit,'roi_pct':s.get('roi')})
    coverage={}
    for d in EXPECTED:
        i=inputs[d]
        coverage[d]={'source':i.get('race_card_source','boatracecsv_archive'),'cards':int(i.get('race_cards_seen',0)),'complete':int(i.get('complete_rows',0)),'fallback':len(i.get('boatcast_fallback_recovered',[])),'excluded':len(i.get('excluded_missing_waku',[]))}
    summary={'period':'2026-06-01..2026-06-30','policy':'3HEAD_V288_OPERATIONAL_MONTH_REPLAY','month_first':'2026-06-01','history_cutoff':'2026-05-31','rule_version_note':'v288 fixed later; operational replay, not pristine model-selection evidence','pre_candidates':candidates,'bets':B,'hits':H,'hit_rate_pct':100*H/B if B else None,'stake':stake,'payout':ret,'profit':ret-stake,'roi_pct':100*ret/stake if stake else None,'max_drawdown_yen':mdd,'result_or_payout_used_for_decision':False,'results_joined_only_after_freeze':True,'route_breakdown':route,'daily':daily,'coverage':coverage}
    (out/'summary_v288_june_operational_replay.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    L=['# v288 operational month replay: 2026-06','', '- Frozen at 2026-05-31; PRE score training strictly before 2026-06-01.','- Target-day result/payout not used for PRE/LIVE decisions; settlement occurs only after decision freeze.','- v288 rules were finalized later, so this is operational-process replay rather than pristine model-selection evidence.','',f'- PRE candidates: {candidates}',f'- BET: {B}',f'- Hits: {H}',f'- Hit rate: {100*H/B:.2f}%' if B else '- Hit rate: -',f'- Stake: {stake:.0f}',f'- Payout: {ret:.0f}',f'- Profit: {ret-stake:+.0f}',f'- ROI: {100*ret/stake:.2f}%' if stake else '- ROI: -',f'- Max drawdown: {mdd:.0f}','','## Route breakdown','|route|bets|hits|hit rate|stake|payout|profit|ROI|','|---|---:|---:|---:|---:|---:|---:|---:|']
    for r,x in route.items():L.append(f"|{r}|{x['bets']}|{x['hits']}|{x['hit_rate_pct']:.2f}%|{x['stake']:.0f}|{x['payout']:.0f}|{x['profit']:+.0f}|{x['roi_pct']:.2f}%|")
    L+=['','## Daily','|date|PRE|bets|hits|stake|payout|profit|ROI|','|---|---:|---:|---:|---:|---:|---:|---:|']
    for x in daily:
        roi=f"{100*x['payout']/x['stake']:.2f}%" if x['stake'] else '-'
        L.append(f"|{x['date']}|{x['pre_candidates']}|{x['bets']}|{x['hits']}|{x['stake']:.0f}|{x['payout']:.0f}|{x['profit']:+.0f}|{roi}|")
    L+=['','## Input coverage','|date|source|cards|complete|fallback|excluded|','|---|---|---:|---:|---:|---:|']
    for d,x in coverage.items():L.append(f"|{d}|{x['source']}|{x['cards']}|{x['complete']}|{x['fallback']}|{x['excluded']}|")
    (out/'summary_v288_june_operational_replay.md').write_text('\n'.join(L)+'\n',encoding='utf-8')
    print('\n'.join(L));print('V288_JUNE_30DAY_REPAIR_OK',json.dumps(summary,ensure_ascii=False))

if __name__=='__main__':main()
