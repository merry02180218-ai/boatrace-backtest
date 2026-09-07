#!/usr/bin/env python3
"""v170: pre-holdout -> Jun-Aug OOS venue stability test for frozen 3-head policy.

Purpose: test whether venue differences seen in v169 persist out of sample, without
selecting venues from Jun-Aug. Venue groups are classified using PRE-HOLDOUT months only.
Frozen production candidate remains p3>=0.30 / v166 top10. No Jun-Aug tuning.
"""
from __future__ import annotations
import csv
from collections import defaultdict
from analyze_v166_3head_pair_direct import read, ff, ii, combo, choose, score_month, SRC, HEADSRC

OUT='analysis_v170_3head_venue_oos.csv'; SUMMARY='summary_v170_3head_venue_oos.md'
CUT=.30; N=10
PRE=['2026-03','2026-04','2026-05']; TEST=['2026-06','2026-07','2026-08']

def vc(r):
    try:return f"{int(float(r.get('venue',''))):02d}"
    except:return str(r.get('venue') or 'NA')

def metric(rs):
    q=[r for r in rs if ff(r.get('p3head'))>=CUT]
    h=[r for r in q if combo(r.get('actual_combo'))[:1]==[3]]
    s=[r for r in q if ii(r.get('valid_payout'))==1]
    w=[r for r in s if 0<ii(r.get('v166_rank20'))<=N]
    ret=sum(ff(r.get('payout100')) for r in w); inv=len(s)*N*100
    return {'R':len(q),'head_rate':100*len(h)/len(q) if q else 0,'hit_rate':100*len(w)/len(q) if q else 0,'coverage':100*sum(1 for r in h if 0<ii(r.get('v166_rank20'))<=N)/len(h) if h else 0,'roi':100*ret/inv if inv else 0}

def main():
    src=read(SRC); hp={int(r['source_index']):ff(r.get('p3head')) for r in read(HEADSRC)}
    for i,r in enumerate(src):r['p3head']=hp.get(i,'')
    lam,_=choose(src)
    scored=[]
    for mo in PRE+TEST: scored += score_month(src,mo,lam)
    keyp={(r['date'],r.get('race_code')):hp.get(i,'') for i,r in enumerate(src)}
    for r in scored:r['p3head']=keyp.get((r['date'],r.get('race_code')),'')
    pre=[r for r in scored if r.get('v166_month') in PRE]; test=[r for r in scored if r.get('v166_month') in TEST]
    venues=sorted(set(vc(r) for r in pre+test))
    rows=[]
    # Pre classifications are descriptive, fixed before reading test outcomes.
    classes={}
    for v in venues:
        pm=metric([r for r in pre if vc(r)==v])
        if pm['R']<5: c='pre_sparse'
        elif pm['roi']>=100: c='pre_roi100plus'
        elif pm['roi']>=70: c='pre_roi70_100'
        else: c='pre_roi_under70'
        classes[v]=c
        tm=metric([r for r in test if vc(r)==v])
        rows.append({'venue':v,'pre_class':c,**{'pre_'+k:x for k,x in pm.items()},**{'test_'+k:x for k,x in tm.items()}})
    fields=list(rows[0].keys())
    with open(OUT,'w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
    groups=[]
    for c in ['pre_roi100plus','pre_roi70_100','pre_roi_under70','pre_sparse']:
        vs={v for v,x in classes.items() if x==c}; groups.append((c,len(vs),metric([r for r in test if vc(r) in vs])))
    allm=metric(test)
    L=['# v170 3号艇 venue OOS stability','', '- Venue groups are determined from Mar-May only; Jun-Aug is OOS evaluation only.',f'- Frozen policy: p3 >= {CUT:.2f}, v166 top {N}.','- No venue exclusion/adoption rule is created from Jun-Aug.','', '## OOS overall',f"- Jun-Aug: R {allm['R']}, ③頭率 {allm['head_rate']:.2f}%, hit {allm['hit_rate']:.2f}%, coverage {allm['coverage']:.2f}%, ROI {allm['roi']:.1f}%.",'','## Pre-period venue class -> OOS result','|pre class|venues|OOS R|③頭率|hit|coverage|ROI|','|---|---:|---:|---:|---:|---:|---:|']
    for c,n,m in groups:L.append(f"|{c}|{n}|{m['R']}|{m['head_rate']:.2f}%|{m['hit_rate']:.2f}%|{m['coverage']:.2f}%|{m['roi']:.1f}%|")
    L += ['','## Interpretation guardrail','If pre-period strong/weak venue classes preserve meaningful separation OOS, venue suitability may be structural. If separation collapses or reverses, v169 dispersion is more consistent with sampling noise. Do not optimize a new venue filter on Jun-Aug.']
    open(SUMMARY,'w',encoding='utf-8').write('\n'.join(L)+'\n'); print('\n'.join(L))
if __name__=='__main__':main()
