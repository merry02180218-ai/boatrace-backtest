#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

import run_1head_v351_live_current_odds_shadow as sh
import run_1head_v351_live_finalize as fin

T=['1-2-3','1-2-4','1-3-2']

def base_final(probs=True):
    x={
      'race_code':'202609191101','status':'PASS','tickets':T,
      'wall3_ticket_applied':False,'five6_ticket_applied':False,
      'deadline_jst':'2026-09-19T12:00:00+09:00',
      'evaluated_at_jst':'2026-09-19T11:50:00+09:00',
      'minutes_to_deadline':10.0,
      'result_or_payout_used':False,'chronology_guard':True,
    }
    if probs:x['ticket_pair_probs']={T[0]:.12,T[1]:.11,T[2]:.09}
    return x

def main():
    cases=[]
    # Odds ratio is below existing soft 3.5 threshold, so legacy output remains equal.
    o1={T[0]:12.0,T[1]:9.0,T[2]:7.0}
    z1=sh.allocate(base_final(True),o1,'2026-09-19T11:50:01+09:00','synthetic')
    assert z1['stakes_yen']==[100,100,100],z1
    assert z1['value_gate_scenarios']['D20']['status']=='READY'
    assert z1['value_gate_scenarios']['D20']['active'] is True,z1
    assert z1['value_gate_scenarios']['D30']['active'] is False,z1
    assert z1['value_gate_scenarios']['D20']['stakes_yen']==[200,200,200],z1
    cases.append({'case':'D20_ONLY','legacy_stakes':z1['stakes_yen'],
                  'D20':z1['value_gate_scenarios']['D20'],'D30':z1['value_gate_scenarios']['D30']})

    o2={T[0]:15.0,T[1]:10.0,T[2]:8.0}
    f2=base_final(True);f2['ticket_pair_probs']={T[0]:.15,T[1]:.10,T[2]:.08}
    z2=sh.allocate(f2,o2,'2026-09-19T11:50:02+09:00','synthetic')
    assert z2['stakes_yen']==[100,100,100],z2
    assert z2['value_gate_scenarios']['D20']['active'] is True
    assert z2['value_gate_scenarios']['D30']['active'] is True
    assert z2['value_gate_scenarios']['D20']['stakes_yen']==[300,200,100],z2
    assert z2['value_gate_scenarios']['D30']['stakes_yen']==[300,200,100],z2
    cases.append({'case':'D20_D30','legacy_stakes':z2['stakes_yen'],
                  'D20':z2['value_gate_scenarios']['D20'],'D30':z2['value_gate_scenarios']['D30']})

    z3=sh.allocate(base_final(False),o1,'2026-09-19T11:50:03+09:00','synthetic')
    assert z3['stakes_yen']==[100,100,100],z3
    assert z3['value_gate_scenarios']['D20']['status']=='UNAVAILABLE_NO_PAIR_PROBS'
    assert z3['value_gate_scenarios']['D30']['status']=='UNAVAILABLE_NO_PAIR_PROBS'
    cases.append({'case':'BACKWARD_COMPAT_NO_PROBS','legacy_stakes':z3['stakes_yen'],
                  'D20_status':z3['value_gate_scenarios']['D20']['status']})

    # Direct helper sanity: formal ticket probability export is positive and keyed by tickets.
    p2={2:.28,3:.24,4:.20,5:.16,6:.12}
    pc={}
    for s in (2,3,4,5,6):
        others=[t for t in (2,3,4,5,6) if t!=s]
        den=sum(1.0/t for t in others)
        for t in others:pc[(s,t)]=(1.0/t)/den
    tt=fin.ticket_list(p2,pc)
    pm=fin.ticket_pair_probs(p2,pc,tt)
    assert list(pm)==tt and len(pm)==3 and all(v>0 for v in pm.values()),(tt,pm)
    cases.append({'case':'FINAL_PAIR_PROB_HELPER','tickets':tt,'ticket_pair_probs':pm})

    out={'cases':cases,'RESULT_OR_PAYOUT_USED':False,'SEPTEMBER_OUTCOMES_READ':False,
         'FORMAL_STAKES_CHANGED':False,'AUDIT_OK':True}
    od=Path('/tmp/v374-value-gate-live-regression');od.mkdir(parents=True,exist_ok=True)
    (od/'result.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
    print(json.dumps(out,indent=2))

if __name__=='__main__':main()
