#!/usr/bin/env python3
"""Retrospective production-rule replay for one day.

Decision phase reads only the frozen daily cache plus archived/direct pre-race
exhibition data and pre-settlement trifecta odds. Results/payouts are deliberately
loaded only after every decision and ticket allocation has been frozen in memory.

Historical input policy:
- tkz/stt: BoatraceCSV pre-race archive (required; fail closed if absent).
- original exhibition: BoatraceCSV archive, with direct historical BOATCAST
  original-exhibition endpoint as a result-blind fallback.
- trifecta odds: BoatraceCSV od3 archive when complete; otherwise the repository's
  official BOAT RACE closing-odds3t archive (120/120 required).
Input failures remain ERROR_NO_BET and are never counted as genuine model NO_BET.
"""
from __future__ import annotations
import argparse,csv,hashlib,json
from datetime import datetime
from pathlib import Path
import joblib,numpy as np,pandas as pd
from backtest import rows
import analyze_v242_3head_target_comp3_min5_max10 as v242
import run_20260911_3head_v288_live as prod

BANK=10000


def bycode(rs):return {str(r.get('レースコード','')).zfill(12):r for r in rs if r.get('レースコード')}
def ff(x):
    try:
        v=float(x);return v if np.isfinite(v) else None
    except:return None


def odds_map(row):
    out={}
    for k,v in row.items():
        s=str(k)
        if s.startswith('3連単_'):
            combo=s[len('3連単_'):].strip()
            if combo.count('-')==2:
                q=ff(v)
                if q is not None and q>0:out[combo]=q
    return out


def _local_csv_rows(path):
    p=Path(path)
    if not p.exists():return []
    with p.open('r',encoding='utf-8-sig',newline='') as f:
        return list(csv.DictReader(f))


def official_closing_odds(day):
    """Return race_code -> combo map from the repo's official odds archive.

    This archive belongs to boatrace-backtest itself, not the external
    BoatraceCSV repository used by backtest.rows(), so it must be read locally.
    June files are wide (one race per row, 120 combo columns); the older long
    schema remains supported for compatibility.
    """
    ymd=day.strftime('%Y/%m/%d');day8=day.strftime('%Y%m%d')
    out={}
    for r in _local_csv_rows(f'data/official_closing_odds3t/{ymd}.csv'):
        jcd=str(r.get('jcd','')).strip().zfill(2)
        rno=str(r.get('rno','')).strip()
        if jcd and rno:
            try:code=f'{day8}{int(float(jcd)):02d}{int(float(rno)):02d}'
            except:code=''
            if code:
                om={}
                for k,v in r.items():
                    key=str(k).strip()
                    if key.count('-')==2:
                        parts=key.split('-')
                        if all(x in {'1','2','3','4','5','6'} for x in parts) and len(set(parts))==3:
                            q=ff(v)
                            if q is not None and q>0:om[key]=q
                if om:out[code]=om
                continue
        code=str(r.get('レースコード','')).zfill(12)
        if len(code)!=12:continue
        try:
            a=int(float(r.get('1着')));b=int(float(r.get('2着')));c=int(float(r.get('3着')))
        except:continue
        q=ff(r.get('オッズ'))
        if q is None or q<=0:continue
        out.setdefault(code,{})[f'{a}-{b}-{c}']=q
    return out


def direct_historical_orig(day8,code):
    """Result-blind fallback to the same BOATCAST original-exhibition feed used LIVE."""
    jo=code[8:10];rr=code[10:12]
    url=f'https://race.boatcast.jp/txt/{jo}/bc_oriten_{day8}_{jo}_{rr}.txt'
    body=prod.get_text(url)
    parsed=prod.parse_orig(body,code)
    if code not in parsed:raise RuntimeError('BOATCAST original parse produced no race row')
    return parsed[code],url,hashlib.sha256(body.encode('utf-8')).hexdigest()


def write_csv(path,rs):
    if not rs:
        path.write_text('',encoding='utf-8');return
    fs=[];seen=set()
    for r in rs:
        for k in r:
            if k not in seen:seen.add(k);fs.append(k)
    with path.open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=fs);w.writeheader();w.writerows(rs)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--date',required=True);ap.add_argument('--cache',required=True);ap.add_argument('--outdir',required=True);a=ap.parse_args()
    day=datetime.strptime(a.date,'%Y-%m-%d').date();day8=day.strftime('%Y%m%d');ymd=day.strftime('%Y/%m/%d')
    z=joblib.load(a.cache)
    if str(z.get('date'))!=day8:raise RuntimeError(f'cache date mismatch {z.get("date")} != {day8}')
    if str(z.get('history_cutoff'))!='2026-08-31':raise RuntimeError('history cutoff drift')
    if z.get('target_result_or_payout_used') is not False:raise RuntimeError('cache leakage guard failed')

    # DECISION PHASE: no result/payout reads are allowed above the DECISIONS_FROZEN marker.
    tkzm=bycode(rows(f'data/previews/tkz/{ymd}.csv'))
    sttm=bycode(rows(f'data/previews/stt/{ymd}.csv'))
    origm=bycode(rows(f'data/previews/original_exhibition/{ymd}.csv'))
    odm=bycode(rows(f'data/previews/od3/{ymd}.csv'))
    official_odm=official_closing_odds(day)
    decisions=[]
    cur=z['current_rows']
    for code,pc in sorted(z.get('pre_candidates',{}).items()):
        code=str(code).zfill(12)
        q=cur[cur.race_code.astype(str).str.zfill(12)==code]
        rec={'date':a.date,'race_code':code,'pre_grade':pc.get('pre_grade'),'pre_score':pc.get('pre_score'),'pre_pct':pc.get('pre_pct'),'pre_p3':pc.get('pre_p3'),
             'decision':'ERROR_NO_BET','evaluation_status':'ERROR','error_type':'','error':'','route':'','total_stake':0,'tickets_json':'[]',
             'tkz_source':'boatracecsv_archive' if code in tkzm else '',
             'stt_source':'boatracecsv_archive' if code in sttm else '',
             'orig_source':'boatracecsv_archive' if code in origm else '',
             'odds_source':'','result_or_payout_used_for_decision':False}
        if len(q)!=1:
            rec['error_type']='cache_error';rec['error']=f'cached row count {len(q)}';decisions.append(rec);continue
        missing=[k for k,m in [('tkz',tkzm),('stt',sttm)] if code not in m]
        if missing:
            rec['error_type']='input_missing';rec['error']='missing archived pre-race '+','.join(missing);decisions.append(rec);continue

        # Original exhibition: archived row first, then direct historical BOATCAST.
        origrow=origm.get(code)
        if origrow is None:
            try:
                origrow,url,sha=direct_historical_orig(day8,code)
                rec['orig_source']='boatcast_direct_historical_fallback';rec['orig_url']=url;rec['orig_sha256']=sha
            except Exception as e:
                rec['error_type']='input_missing';rec['error']=f'original exhibition unavailable: {e}';decisions.append(rec);continue

        # Odds: complete legacy archive first, then official BOAT RACE closing archive.
        odds={}
        if code in odm:
            odds=odds_map(odm[code])
            if len(odds)==120:rec['odds_source']='boatracecsv_od3_archive'
        if len(odds)!=120:
            odds=official_odm.get(code,{})
            if len(odds)==120:rec['odds_source']='boatrace_official_closing_odds3t_archive'
        if len(odds)!=120:
            rec['error_type']='input_missing';rec['error']=f'archived odds incomplete {len(odds)}/120';decisions.append(rec);continue

        try:
            r=prod.update_current_features(q.iloc[0],{code:tkzm[code]},{code:sttm[code]},{code:origrow},z['st_bias'])
            X=pd.DataFrame([r]);hfs=z['head_features'];cats=z['head_cats']
            for c in hfs:X[c]=pd.to_numeric(X[c],errors='coerce')
            p3=float(z['head_model'].predict_proba(X[hfs+cats])[:,1][0]);ts=v242.safe_order(r,z['pair_model'])
            if ts is None:raise RuntimeError('pair-rank-invalid')
            ch=v242.choose_n(ts,odds);action=ch.get('action');raw_n=ch.get('raw_n');top_n=ch.get('top_n');comp=ch.get('comp_odds')
            minus=float(r['c_b3_minus_b5_st']);attack=float(r['c_attack3_stretch']);buyable=action=='bet'
            base=bool(buyable and p3>=.45 and raw_n is not None and 7<=raw_n<=18 and comp is not None and 3.05<=comp<=4.0)
            keep=minus>=prod.KEEP;rescue=attack<=prod.RESCUE
            v243pass=bool(buyable and ((base and keep) or ((not base) and rescue)))
            scond=bool(r['c_b3_minus_b4_waku_st']<=prod.S_WAKU_MAX and r['c_b3_minus_b4_st']>=prod.S_ST_MIN and r['c_b3_meetst']<=prod.S_MEET_MAX)
            acond=bool(r['c_b3_minus_b4_st']>=prod.A_ST_MIN and r['c_wall12_weak']<=prod.A_WALL_MAX)
            bcond=bool(r['c_b3_minus_b2_motor']>=prod.B_MOTOR_MIN and r['c_b3_inside_nst']<=prod.B_NST_MAX)
            route,S,A,B=prod.select_v288_route(v243pass,buyable,scond,acond,bcond)
            tickets=[]
            if route:
                vals=[float(odds[x]) for x in ts[:int(top_n)]];tickets=prod.dutch(ts[:int(top_n)],vals)
            rec.update({'decision':'BET' if route else 'NO_BET','evaluation_status':'EVALUABLE','error_type':'','error':'','route':route or '','p3_live':p3,'v242_action':action,
                'raw_top_n':raw_n,'raw_comp_odds':ch.get('raw_comp'),'top_n':top_n,'comp_odds':comp,
                'v243_pass':int(v243pass),'v243_base':int(base),'v243_keep':int(keep),'v243_rescue':int(rescue),
                'S_condition':int(scond),'A_condition':int(acond),'B_condition':int(bcond),
                'b3_minus_b4_waku_st':float(r['c_b3_minus_b4_waku_st']),'b3_minus_b4_st':float(r['c_b3_minus_b4_st']),
                'b3_meetst':float(r['c_b3_meetst']),'wall12_weak':float(r['c_wall12_weak']),
                'b3_minus_b2_motor':float(r['c_b3_minus_b2_motor']),'b3_inside_nst':float(r['c_b3_inside_nst']),
                'total_stake':sum(int(x['stake']) for x in tickets),'tickets_json':json.dumps(tickets,ensure_ascii=False)})
        except Exception as e:
            rec['error_type']='decision_error';rec['error']=str(e)
        decisions.append(rec)

    # Audit boundary: all decisions/tickets are immutable before outcome reads.
    frozen_json=json.dumps(decisions,ensure_ascii=False,sort_keys=True)
    decision_sha=hashlib.sha256(frozen_json.encode()).hexdigest()
    print('DECISIONS_FROZEN_BEFORE_RESULTS',a.date,'candidates',len(decisions),'sha256',decision_sha,flush=True)

    # EVALUATION PHASE ONLY.
    paym=bycode(rows(f'data/results/payouts/{ymd}.csv'));resm=bycode(rows(f'data/results/realtime/{ymd}.csv'))
    settled=[]
    for rec in decisions:
        x=dict(rec);code=x['race_code'];x.update({'valid_result':0,'actual_combo':'','payout100':0,'hit':0,'return_yen':0.0,'profit':0.0,'result_joined_after_freeze':True})
        pr=paym.get(code,{});rr=resm.get(code,{})
        actual=str(pr.get('3連単_組番') or '').strip();p100=int(float(pr.get('3連単_払戻金') or 0)) if str(pr.get('3連単_払戻金') or '').strip() else 0
        x['valid_result']=int(bool(rr));x['actual_combo']=actual;x['payout100']=p100
        if x['decision']=='BET':
            tickets=json.loads(x['tickets_json']);ret=0.0;hit=0
            for t in tickets:
                if t['combo']==actual and int(t['stake'])>0:
                    hit=1;ret=float(t['stake'])*float(t['odds']);break
            x['hit']=hit;x['return_yen']=ret;x['profit']=ret-BANK
        settled.append(x)

    bets=[r for r in settled if r['decision']=='BET'];stake=sum(r['total_stake'] for r in bets);ret=sum(r['return_yen'] for r in bets);hits=sum(r['hit'] for r in bets)
    evaluable=[r for r in settled if r.get('evaluation_status')=='EVALUABLE'];errors=[r for r in settled if r.get('evaluation_status')!='EVALUABLE']
    summary={'date':a.date,'policy':'3HEAD_V288_PRODUCTION_RETROSPECTIVE_REPLAY','history_cutoff':'2026-08-31','pre_candidates':len(decisions),
             'live_evaluable':len(evaluable),'input_or_decision_errors':len(errors),'genuine_no_bets':sum(r['decision']=='NO_BET' for r in evaluable),
             'bets':len(bets),'hits':hits,'hit_rate':hits/len(bets) if bets else None,'stake':stake,'payout':ret,'profit':ret-stake,'roi':100*ret/stake if stake else None,
             'decision_sha256_before_results':decision_sha,'result_or_payout_used_for_decision':False,'results_joined_only_after_freeze':True,
             'odds_source_note':'official closing odds are a historical closing snapshot, not an exact purchase-time fill'}
    out=Path(a.outdir);out.mkdir(parents=True,exist_ok=True);write_csv(out/'day_replay.csv',settled);(out/'day_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
