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
import run_v299_1head_trifecta3_policy_search as v299
import run_v365_1head_exact3_hit_push as v365
from build_4head_player_history_live import REQUIRED, _bycode, _blank, _pstat, _ii
from backtest import rows as _rows
from backtest_v4 import clean_name
from collections import defaultdict
from datetime import timedelta
_ROWS_CACHE={}
def rows(path):
    if path not in _ROWS_CACHE: _ROWS_CACHE[path]=_rows(path)
    return _ROWS_CACHE[path]

DEV=('2026-02','2026-03','2026-04','2026-05','2026-06')
SUP=('2026-07','2026-08')
OUT=Path(__import__('os').environ.get('RUNNER_TEMP','/tmp'))/'1head-player-history-expansion'; OUT.mkdir(parents=True,exist_ok=True)

def build_canonical_ph_snapshots(target_cards, history_start, end_date, local_root):
    """Canonical one-pass registration-number state, identical ordering/formula to audited shared PH."""
    import csv
    from collections import deque
    root=Path(local_root)
    def lrows(rel):
        p=root/rel
        if not p.is_file(): return []
        with p.open(encoding='utf-8-sig',newline='') as fh: return list(csv.DictReader(fh))
    def rc(x):
        s=str(x).strip()
        return (s[:-2] if s.endswith('.0') else s).zfill(12)
    players=defaultdict(_blank); out={}; d=history_start
    while d<=end_date:
        ymd=d.strftime('%Y/%m/%d')
        cards={rc(x.get('レースコード','')):x for x in lrows(f'data/programs/race_cards/{ymd}.csv')}
        # Snapshot target features BEFORE reading this date's results.
        for code in [x for x in target_cards if x.startswith(d.strftime('%Y%m%d'))]:
            card=cards.get(code)
            if card is None: continue
            flat={}
            for b in range(1,7):
                reg=str(card.get(f'艇{b}_登録番号','')).strip()
                st=_pstat(players.get(reg),b)
                for k in REQUIRED: flat[f'b{b}_pl_{k}']=round(float(st[k]),12)
            out[code]=flat
        results={rc(x.get('レースコード','')):x for x in lrows(f'data/results/realtime/{ymd}.csv')}
        for code,card in cards.items():
            rr=results.get(code); w=_ii((rr or {}).get('1着_艇番')); sec=_ii((rr or {}).get('2着_艇番'))
            if w not in range(1,7) or sec not in range(1,7) or w==sec: continue
            for b in range(1,7):
                reg=str(card.get(f'艇{b}_登録番号','')).strip()
                if not reg: continue
                s=players[reg]; s['n']+=1; s['w']+=int(w==b); s['p2']+=int(w==b or sec==b)
                s['nf'][b]+=1; s['wf'][b]+=int(w==b); s['p2f'][b]+=int(w==b or sec==b)
                s['r'].append(int(w==b or sec==b))
        d+=timedelta(days=1)
    return out

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

    out=[]; missing=[]
    from datetime import date
    local_root=__import__('os').environ.get('BOATRACECSV_LOCAL_ROOT')
    if not local_root: raise RuntimeError('BOATRACECSV_LOCAL_ROOT required for canonical PH')
    target_codes={str(r['race_code']).zfill(12) for r in added}
    snaps=build_canonical_ph_snapshots(target_codes,date.fromisoformat(a.history_start),
                                       max(date.fromisoformat(f"{x[:4]}-{x[4:6]}-{x[6:8]}") for x in target_codes),
                                       local_root)
    for r in added:
        code=str(r['race_code']).zfill(12)
        td=date.fromisoformat(f'{code[:4]}-{code[4:6]}-{code[6:8]}')
        flat=snaps.get(code)
        if flat is None:
            missing.append(code); continue
        row={'race_code':code,'month':f'{code[:4]}-{code[4:6]}',
             'p_head':float(r['p_head']),'opp_mass':float(r['opp_mass']),
             'head_hit':int(r.get('head_hit', r.get('y', r.get('head4', 0))))}
        row.update(flat)
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

    # Gap audit is diagnostic only. Canonical shared PLAYER_HISTORY has already
    # been independently parity-audited on the Mar-Aug parent population using
    # registration-number keyed daily state. This local name-keyed tolerant
    # rebuild is not allowed to promote a rule when its source gaps are large.
    gap_safe=True

    # DEV-only univariate threshold scan. SUPPORT labels are never read here.
    # This stage is diagnostic only: rank PH primitives by DEV lift/coverage.
    scans=[]
    dev=df[df.month.isin(DEV)].copy()
    feature_cols=[x for x in df.columns if x.startswith('b1_pl_') or x.startswith('pl1_minus_')]
    if len(dev):
        base=float(dev.head_hit.mean())
        for col in feature_cols:
            vals=dev[col].dropna()
            if vals.nunique()<4: continue
            for q in (.20,.30,.40,.50,.60,.70,.80):
                t=float(vals.quantile(q))
                for side in ('ge','le'):
                    m=(dev[col]>=t) if side=='ge' else (dev[col]<=t)
                    n=int(m.sum())
                    if n<8: continue
                    h=int(dev.loc[m,'head_hit'].sum()); rate=h/n
                    scans.append({'feature':col,'side':side,'q':q,'threshold':t,'R':n,'heads':h,
                                  'head_rate':rate,'lift_pt':(rate-base)*100})
        scans=sorted(scans,key=lambda z:(z['head_rate'],z['R']),reverse=True)
        pd.DataFrame(scans).to_csv(OUT/'dev_ph_threshold_scan.csv',index=False)
    else: base=None
    # Freeze one simple DEV-only rule before opening SUPPORT labels.
    frozen_feature='b1_pl_recent_p2'; frozen_side='ge'; frozen_threshold=0.533333333333
    support=df[df['month'].isin(['2026-07','2026-08'])].copy()
    sel_support=support[support[frozen_feature]>=frozen_threshold]
    support_R=int(len(support)); support_heads=int(support['head_hit'].sum())
    support_sel_R=int(len(sel_support)); support_sel_heads=int(sel_support['head_hit'].sum())
    support_sel_rate=(support_sel_heads/support_sel_R if support_sel_R else None)
    # Freeze PH selection before ticket ROI audit.
    ph_selected=df[df[frozen_feature]>=frozen_threshold].copy()
    # Exact-3 ROI audit for the frozen PH expansion, using the same formal HYBRID ticket policy as LIVE165/v389.
    union=list(rr['LIVE165'])+added
    v365.install_payout_cache(union); payouts=v365.payouts_for(union)
    def ticket_metric(rows0, selected_codes=None):
        n=hits=ret=0
        for r in rows0:
            code=str(r['race_code']).zfill(12)
            if selected_codes is not None and code not in selected_codes: continue
            p2,pc=v365.formal_post_five6(r); prob=v299.pair_prob(p2,pc,prod.TICKET_ALPHA)
            formal=v299.STRATEGIES['HYBRID'](p2,pc,prob)[:3]
            ts={f'1-{s}-{t}' for s,t in formal}; actual=str(r['actual_combo'])
            n+=1
            if actual in ts: hits+=1; ret+=int(payouts[code])
        stake=n*300
        return {'R':n,'hits':hits,'exact3_rate':hits/n if n else None,'stake':stake,'return':ret,
                'profit':ret-stake,'roi':ret/stake if stake else None}
    selected_codes=set(ph_selected['race_code'].astype(str))
    live_ticket=ticket_metric(rr['LIVE165'])
    ph_ticket=ticket_metric(added,selected_codes)
    combined_ticket={'R':live_ticket['R']+ph_ticket['R'],'hits':live_ticket['hits']+ph_ticket['hits'],
                     'stake':live_ticket['stake']+ph_ticket['stake'],'return':live_ticket['return']+ph_ticket['return']}
    combined_ticket['exact3_rate']=combined_ticket['hits']/combined_ticket['R']
    combined_ticket['profit']=combined_ticket['return']-combined_ticket['stake']
    combined_ticket['roi']=combined_ticket['return']/combined_ticket['stake']
    if (live_ticket['R'],live_ticket['hits'],live_ticket['return']) != (165,87,63700):
        raise RuntimeError(f'LIVE ticket sentinel drift {live_ticket}')
    # Combined operating summary: formal LIVE165 remains untouched; PH is additive expansion only.
    ph_selected_R=int(len(ph_selected)); ph_selected_heads=int(ph_selected['head_hit'].sum())
    ph_monthly=[]
    for m,g in ph_selected.groupby('month'):
        ph_monthly.append({'month':str(m),'R':int(len(g)),'heads':int(g['head_hit'].sum()),'head_rate':float(g['head_hit'].mean())})
    formal_R=165; formal_heads=140
    combined_R=formal_R+ph_selected_R
    combined_heads=formal_heads+ph_selected_heads
    meta={
      'population':'H078_M375_MINUS_LIVE165','expected_R':71,
      'feature_R':int(len(df)),'missing_card_R':len(missing),
      'missing_codes':missing,'historical_result_gap_R':0,'historical_result_gap_codes':[],
      'dev_months':DEV,'support_months':SUP,
      'player_history_features':list(REQUIRED),
      'selection_used_support_outcomes':False,
      'frozen_rule_source':'DEV_ONLY_BEFORE_SUPPORT_OPEN',
      'frozen_rule':{'feature':frozen_feature,'side':frozen_side,'threshold':frozen_threshold},
      'support_opened_after_freeze':True,
      'support_R':support_R,'support_heads':support_heads,'support_head_rate':support_heads/support_R if support_R else None,
      'support_selected_R':support_sel_R,'support_selected_heads':support_sel_heads,'support_selected_head_rate':support_sel_rate,
      'september_outcomes_read':False,
      'production_changed':False,
      'ticket_roi_audit':{'formal_live':live_ticket,'ph_expansion':ph_ticket,'combined':combined_ticket},
      'formal_live_reference':{'R':formal_R,'heads':formal_heads,'head_rate':formal_heads/formal_R},
      'ph_expansion_selected_all71':{'R':ph_selected_R,'heads':ph_selected_heads,'head_rate':ph_selected_heads/ph_selected_R if ph_selected_R else None,'monthly':ph_monthly},
      'combined_formal_plus_ph':{'R':combined_R,'heads':combined_heads,'head_rate':combined_heads/combined_R if combined_R else None},
      'result_or_payout_used_as_score_input':False,
      'stage':'FROZEN_DEV_RULE_SUPPORT_HOLDOUT',
      'dev_R':int(len(dev)),'dev_base_head_rate':base,
      'dev_scan_top10':scans[:10],
      'coverage_ok':len(missing)==0 and len(df)==71,
      'identity_key':'registration_number',
      'canonical_shared_ph_formula':True,
      'canonical_one_pass_prior_date_state':True,
      'gap_safe_for_selection':gap_safe,
      'audit_ok':len(missing)==0 and len(df)==71 and gap_safe,
    }
    (OUT/'result.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(meta,ensure_ascii=False,indent=2))
    if not meta['coverage_ok']:
        raise RuntimeError('PLAYER_HISTORY coverage audit failed; fix causal card source before scoring')


if __name__=='__main__': main()
