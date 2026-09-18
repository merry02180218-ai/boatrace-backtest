#!/usr/bin/env python3
from __future__ import annotations
"""v392 research-only 1HEAD expansion Shadow.

Two modes:
- scan: surface PRE candidates outside formal LIVE HEAD .790 but within .780-.790.
- judge: after exhibition, evaluate the frozen v389 CONSENSUS_MASS confidence gate.

This module never reads results/payouts and never changes formal PASS/DROP.
"""
from pathlib import Path
import argparse,csv,glob,json,math

import onehead_production_profile as prod
import run_v299_1head_trifecta3_policy_search as v299
import run_1head_v351_live_finalize as fin

BOATS=(2,3,4,5,6)

EXP_HEAD_MIN=.780
EXP_HEAD_MAX=prod.LIVE_HEAD_CUTOFF  # exclusive; formal lane begins here
EXP_MASS_MIN=.375

# Frozen from v389 DEV-only CONSENSUS_MASS q=.35.
CONS_MEAN=.7735849056603774
CONS_SD=.05920808296780732
MASS_MEAN=.3101037496572021
MASS_SD=.049786286582581996
CONS_WEIGHT=1.0
FORMAL_MASS_WEIGHT=.75
SCORE_THRESHOLD=-.2340695124317066
ALT=('JOINT','TOP2XTOP2','SECOND1X3','SECOND3X1')
PROFILE='1HEAD_EXPANSION_SHADOW_V392_CONSENSUS_MASS_Q035'


def apply_pair(p2,pc,inner,outer,risk,g2,g3):
    q2={b:float(p2[b]) for b in BOATS}
    if float(g2)>0:
        q2[outer]*=math.exp(float(g2)*float(risk))
        q2[inner]*=math.exp(-float(g2)*float(risk))
        q2=fin.norm(q2)
    q3={}
    for s in BOATS:
        q={t:float(pc[(s,t)]) for t in BOATS if t!=s}
        if float(g3)>0:
            if outer in q:q[outer]*=math.exp(float(g3)*float(risk))
            if inner in q:q[inner]*=math.exp(-float(g3)*float(risk))
        q=fin.norm(q)
        for t,v in q.items():q3[(s,t)]=v
    return q2,q3


def final_expansion_dist(x):
    core=fin.opponent_core(x['corrected_ex'],x['corrected_st'],x['corrected_straight'],x['corrected_orig_avg'])
    p2,pc=fin.adjust(x['p2'],x['pc'],core)

    # Historical expansion-lane formal semantics: wall3 is mass-gated, not
    # dependent on formal HEAD>=.790 because these rows live outside that lane.
    expansion_watch=float(x['opp_mass'])>=prod.WATCH_OPPONENT_MASS_MIN
    wall=fin.wall3_shadow(p2,pc,x,expansion_watch)
    if wall['applied']:
        p2,pc=apply_pair(p2,pc,3,4,float(wall['risk']),
                         prod.WALL3_SHADOW_SECOND_G2,prod.WALL3_SHADOW_THIRD_G3)

    five=fin.five6_shadow(p2,pc,x,True)
    if five['applied']:
        p2,pc=apply_pair(p2,pc,5,6,float(five['st_gap_6_minus_5']),
                         prod.FIVE6_SHADOW_SECOND_G2,prod.FIVE6_SHADOW_THIRD_G3)
    return p2,pc,core,wall,five


def consensus_features(p2,pc):
    pair=v299.pair_prob(p2,pc,prod.TICKET_ALPHA)
    formal_order=v299.STRATEGIES['HYBRID'](p2,pc,pair)
    formal=formal_order[:3]
    if len(formal)!=3 or len(set(formal))!=3:
        raise RuntimeError('invalid formal expansion tickets')
    fset=set(formal)
    overlaps={}
    vals=[]
    for name in ALT:
        order=v299.STRATEGIES[name](p2,pc,pair)
        ov=len(fset & set(order[:3]))/3.0
        overlaps[name]=ov
        vals.append(ov)
    consensus=sum(vals)/len(vals)
    formal_mass=sum(float(pair[x]) for x in formal)
    zc=(consensus-CONS_MEAN)/CONS_SD
    zm=(formal_mass-MASS_MEAN)/MASS_SD
    score=(CONS_WEIGHT*zc+FORMAL_MASS_WEIGHT*zm)/(CONS_WEIGHT+FORMAL_MASS_WEIGHT)
    tickets=[f'1-{s}-{t}' for s,t in formal]
    return {
      'tickets':tickets,
      'ticket_pair_probs':{f'1-{s}-{t}':float(pair[(s,t)]) for s,t in formal},
      'consensus_mean':float(consensus),
      'formal_mass':float(formal_mass),
      'consensus_overlaps':overlaps,
      'z_consensus':float(zc),
      'z_formal_mass':float(zm),
      'score':float(score),
      'threshold':float(SCORE_THRESHOLD),
      'confidence_pass':bool(score>=SCORE_THRESHOLD-1e-12),
    }


def scan_cache(cache_dir:Path,csv_out:Path,json_out:Path):
    rows=[]
    for p in sorted(cache_dir.glob('20*.json')):
        x=json.loads(p.read_text())
        if x.get('result_or_payout_used') is not False or not x.get('chronology_guard'):
            raise RuntimeError(f'unsafe cache file {p}')
        code=str(x.get('race_code','')).zfill(12)
        ph=float(x['final_head_p']); mass=float(x['opp_mass'])
        if ph>=EXP_HEAD_MIN-1e-12 and ph<EXP_HEAD_MAX-1e-12 and mass>=EXP_MASS_MIN-1e-12:
            rows.append({
              'race_code':code,'jcd':int(code[8:10]),'race':int(code[10:12]),
              'final_head_p':ph,'opp_mass':mass,
              'expansion_pre_shadow':True,
              'needs_exhibition':True,
              'research_only':True,
              'result_or_payout_used':False,'chronology_guard':True,
            })
    rows.sort(key=lambda r:(r['jcd'],r['race']))
    csv_out.parent.mkdir(parents=True,exist_ok=True)
    fields=list(rows[0].keys()) if rows else ['race_code','jcd','race','final_head_p','opp_mass','expansion_pre_shadow','needs_exhibition','research_only','result_or_payout_used','chronology_guard']
    with csv_out.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
    meta={
      'profile':PROFILE,'mode':'PRE_SCAN','candidate_R':len(rows),
      'head_min':EXP_HEAD_MIN,'head_max_exclusive':EXP_HEAD_MAX,'mass_min':EXP_MASS_MIN,
      'research_only':True,'result_or_payout_used':False,'chronology_guard':True,
    }
    json_out.write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(meta,ensure_ascii=False))
    return meta


def judge(inp:Path,formal_path:Path,out_path:Path):
    x=json.loads(inp.read_text()); formal=json.loads(formal_path.read_text())
    for name,obj in [('input',x),('formal',formal)]:
        if obj.get('result_or_payout_used') is not False or not obj.get('chronology_guard'):
            raise RuntimeError(f'unsafe {name}')
    code=str(x.get('race_code','')).zfill(12)
    ph=float(x['final_head_p']); mass=float(x['opp_mass'])
    formal_status=str(formal.get('status',''))

    base={
      'profile':PROFILE,'race_code':code,
      'formal_status':formal_status,
      'formal_tickets':list(formal.get('tickets') or []),
      'final_head_p':ph,'opp_mass':mass,
      'head_min':EXP_HEAD_MIN,'head_max_exclusive':EXP_HEAD_MAX,'mass_min':EXP_MASS_MIN,
      'head_exhibition_pass':bool(x.get('head_exhibition_pass')),
      'research_only':True,'result_or_payout_used':False,'chronology_guard':True,
    }

    if formal_status=='PASS':
        out={**base,'status':'BASE_FORMAL_PASS','active':False,'reason':'formal LIVE lane already PASS',
             'tickets':[],'stakes_yen':[],'total_stake_yen':0}
    elif ph<EXP_HEAD_MIN-1e-12 or ph>=EXP_HEAD_MAX-1e-12:
        out={**base,'status':'OUTSIDE_EXPANSION_HEAD_BAND','active':False,
             'reason':'HEAD is outside [.780,.790) expansion band',
             'tickets':[],'stakes_yen':[],'total_stake_yen':0}
    elif mass<EXP_MASS_MIN-1e-12:
        out={**base,'status':'OUTSIDE_EXPANSION_MASS','active':False,
             'reason':'opponent mass below .375',
             'tickets':[],'stakes_yen':[],'total_stake_yen':0}
    elif not bool(x.get('head_exhibition_pass')):
        out={**base,'status':'EXPANSION_EXHIBITION_DROP','active':False,
             'reason':'current causal LIVE exhibition gate failed',
             'tickets':[],'stakes_yen':[],'total_stake_yen':0}
    else:
        p2,pc,core,wall,five=final_expansion_dist(x)
        conf=consensus_features(p2,pc)
        active=bool(conf['confidence_pass'])
        out={**base,
             'status':'EXPANSION_SHADOW_PASS' if active else 'EXPANSION_CONFIDENCE_DROP',
             'active':active,
             'reason':'v389 frozen consensus gate pass' if active else 'v389 frozen consensus gate failed',
             'tickets':conf['tickets'] if active else [],
             'stakes_yen':[100,100,100] if active else [],
             'total_stake_yen':300 if active else 0,
             'candidate_tickets':conf['tickets'],
             'ticket_pair_probs':conf['ticket_pair_probs'],
             'consensus_mean':conf['consensus_mean'],'formal_mass':conf['formal_mass'],
             'consensus_overlaps':conf['consensus_overlaps'],
             'z_consensus':conf['z_consensus'],'z_formal_mass':conf['z_formal_mass'],
             'consensus_score':conf['score'],'consensus_threshold':conf['threshold'],
             'wall3_applied':bool(wall['applied']),'five6_applied':bool(five['applied']),
             'opponent_core':core,
             'historical_reference':{
               'source':'v389 Artifact 10562248620',
               'selected_added_R':42,'combined_with_live_R':207,
               'combined_historical_roi':1.2326892109500804,
               'support_selected_R':8,
               'formal_promotion_ready':False,
             }}
    out_path.parent.mkdir(parents=True,exist_ok=True)
    out_path.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(out,ensure_ascii=False))
    return out


def main():
    ap=argparse.ArgumentParser()
    sub=ap.add_subparsers(dest='mode',required=True)
    s=sub.add_parser('scan')
    s.add_argument('--cache-dir',required=True,type=Path)
    s.add_argument('--csv-out',required=True,type=Path)
    s.add_argument('--json-out',required=True,type=Path)
    j=sub.add_parser('judge')
    j.add_argument('--input',required=True,type=Path)
    j.add_argument('--formal',required=True,type=Path)
    j.add_argument('--out',required=True,type=Path)
    a=ap.parse_args()
    if a.mode=='scan':scan_cache(a.cache_dir,a.csv_out,a.json_out)
    else:judge(a.input,a.formal,a.out)

if __name__=='__main__':main()
