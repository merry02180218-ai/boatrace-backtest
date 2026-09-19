#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import joblib,pandas as pd

import analyze_v242_3head_target_comp3_min5_max10 as v242
import run_20260911_3head_v288_live as prod
import replay_v288_historical_day as base
from backtest import rows

BANK=10000
PURCHASE_GATE_COL='post_motor_inner_rank_edge'
PURCHASE_GATE_MIN=0.60

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--date',required=True);ap.add_argument('--cache',required=True);ap.add_argument('--outdir',required=True);a=ap.parse_args()
    day=pd.Timestamp(a.date).date();day8=day.strftime('%Y%m%d');ymd=day.strftime('%Y/%m/%d')
    z=joblib.load(a.cache)
    if str(z.get('date'))!=day8 or z.get('target_result_or_payout_used') is not False:raise RuntimeError('cache guard failed')
    spec=json.loads(Path('research/3head_a_march_parity_codes.json').read_text(encoding='utf-8'))
    codes=[str(x).zfill(12) for x in spec['race_codes'] if str(x).zfill(12).startswith(day8)]

    tkzm=base.bycode(rows(f'data/previews/tkz/{ymd}.csv'))
    sttm=base.bycode(rows(f'data/previews/stt/{ymd}.csv'))
    origm=base.bycode(rows(f'data/previews/original_exhibition/{ymd}.csv'))
    odm=base.bycode(rows(f'data/previews/od3/{ymd}.csv'))
    official=base.official_closing_odds(day)
    cur=z['current_rows'];decisions=[]

    for code in codes:
        q=cur[cur.race_code.astype(str).str.zfill(12)==code]
        rec={'date':a.date,'race_code':code,'decision':'ERROR_NO_BET','evaluation_status':'ERROR','error_type':'','error':'','route':'','total_stake':0,'tickets_json':'[]','pair_order_json':'[]','result_or_payout_used_for_decision':False}
        if len(q)!=1:
            rec['error_type']='cache_error';rec['error']=f'cached row count {len(q)}';decisions.append(rec);continue
        if code not in tkzm or code not in sttm:
            rec['error_type']='input_missing';rec['error']='missing tkz/stt';decisions.append(rec);continue
        origrow=origm.get(code)
        if origrow is None:
            try:origrow,_,_=base.direct_historical_orig(day8,code)
            except Exception as e:
                rec['error_type']='input_missing';rec['error']=f'original exhibition unavailable: {e}';decisions.append(rec);continue
        odds=base.odds_map(odm[code]) if code in odm else {}
        if len(odds)!=120:odds=official.get(code,{})
        if len(odds)!=120:
            rec['error_type']='input_missing';rec['error']=f'odds incomplete {len(odds)}/120';decisions.append(rec);continue
        try:
            r=prod.update_current_features(q.iloc[0],{code:tkzm[code]},{code:sttm[code]},{code:origrow},z['st_bias'])
            gate_val=pd.to_numeric(pd.Series([r.get(PURCHASE_GATE_COL)]),errors='coerce').iloc[0]
            rec['purchase_gate_col']=PURCHASE_GATE_COL
            rec['purchase_gate_min']=PURCHASE_GATE_MIN
            rec['purchase_gate_value']=None if pd.isna(gate_val) else float(gate_val)
            rec['purchase_gate_pass']=bool(pd.notna(gate_val) and gate_val>=PURCHASE_GATE_MIN)
            if not rec['purchase_gate_pass']:
                rec.update({'decision':'NO_BET','evaluation_status':'EVALUABLE','error_type':'','error':'','route':'A_PURCHASE_GATE_SKIP'})
                decisions.append(rec);continue
            ts=v242.safe_order(r,z['pair_model'])
            if ts is None:raise RuntimeError('pair-rank-invalid')
            ch=v242.choose_n(ts,odds);action=ch.get('action');top_n=ch.get('top_n');comp=ch.get('comp_odds')
            buyable=action=='bet';tickets=[]
            if buyable:
                vals=[float(odds[x]) for x in ts[:int(top_n)]]
                tickets=prod.dutch(ts[:int(top_n)],vals)
            rec.update({'decision':'BET' if buyable else 'NO_BET','evaluation_status':'EVALUABLE','error_type':'','error':'','route':'PAIR_ONLY' if buyable else '',
                        'v242_action':action,'raw_top_n':ch.get('raw_n'),'top_n':top_n,'raw_comp_odds':ch.get('raw_comp'),'comp_odds':comp,
                        'total_stake':sum(int(x['stake']) for x in tickets),'tickets_json':json.dumps(tickets,ensure_ascii=False),'pair_order_json':json.dumps(ts,ensure_ascii=False)})
        except Exception as e:
            rec['error_type']='decision_error';rec['error']=str(e)
        decisions.append(rec)

    frozen=json.dumps(decisions,ensure_ascii=False,sort_keys=True);sha=hashlib.sha256(frozen.encode()).hexdigest()
    print('PAIR_ONLY_DECISIONS_FROZEN_BEFORE_RESULTS',a.date,sha,flush=True)

    paym=base.bycode(rows(f'data/results/payouts/{ymd}.csv'));resm=base.bycode(rows(f'data/results/realtime/{ymd}.csv'))
    settled=[]
    for rec in decisions:
        x=dict(rec);code=x['race_code'];pr=paym.get(code,{});rr=resm.get(code,{})
        actual=str(pr.get('3連単_組番') or '').strip();p100=int(float(pr.get('3連単_払戻金') or 0)) if str(pr.get('3連単_払戻金') or '').strip() else 0
        x.update({'valid_result':int(bool(rr)),'actual_combo':actual,'payout100':p100,'head3_actual':int(actual.startswith('3-')),'hit':0,'return_yen':0.0,'profit':0.0,'result_joined_after_freeze':True})
        if x['decision']=='BET':
            ret=0.;hit=0
            for t in json.loads(x['tickets_json']):
                if t['combo']==actual and int(t['stake'])>0:hit=1;ret=float(t['stake'])*float(t['odds']);break
            x['hit']=hit;x['return_yen']=ret;x['profit']=ret-BANK
        settled.append(x)
    out=Path(a.outdir);out.mkdir(parents=True,exist_ok=True);base.write_csv(out/'day_replay.csv',settled)
    bets=[x for x in settled if x['decision']=='BET'];ev=[x for x in settled if x['evaluation_status']=='EVALUABLE']
    summary={'date':a.date,'policy':'3HEAD_A_PURCHASE_GATE_MARCH_FROZEN_DIAGNOSTIC','pre_candidates':len(decisions),'live_evaluable':len(ev),'input_or_decision_errors':len(decisions)-len(ev),
             'genuine_no_bets':sum(x['decision']=='NO_BET' for x in ev),'bets':len(bets),'hits':sum(x['hit'] for x in bets),'stake':sum(x['total_stake'] for x in bets),
             'payout':sum(x['return_yen'] for x in bets),'decision_sha256_before_results':sha,'result_or_payout_used_for_decision':False,'results_joined_only_after_freeze':True}
    (out/'day_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
