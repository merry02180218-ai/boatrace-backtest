#!/usr/bin/env python3
"""v201: exploratory 3-head strong-condition discovery with locked late validation.

Data:
- v198 frozen strict walk-forward production predictions/settlement
- v108 same-race exhibition feature table, joined by race_code

Protocol:
- DISCOVERY: 2025-12..2026-02 only
- LOCKED TEST: 2026-03..2026-06 only
- Search is performed ONLY on DISCOVERY.
- Selected rules are then evaluated unchanged on LOCKED TEST.
- This is exploratory evidence, not production adoption evidence.
"""
from pathlib import Path
from itertools import product
import pandas as pd, numpy as np

ROOT=Path(__file__).resolve().parent
BASE=ROOT/'analysis_v198_3head_long_history_base.csv'
FEAT=ROOT/'analysis_v108_1head_feasibility.csv'
OUT=ROOT/'analysis_v201_3head_combo_discovery.csv'
SUM=ROOT/'summary_v201_3head_combo_discovery.md'

P3=[.30,.325,.35,.375,.40]
TURN=[None,-.4,-.2,0.0]
ST=[None,-.2,0.0,.2]
STRAIGHT=[None,-.2,0.0,.2]
EX=[None,-.2,0.0,.2]
MIN_DISC_R=15
TOPK=10
CAP=10000


def metr(g, cap=None):
    s=g[g.valid_payout==1].copy()
    cost=float(s.cost_yen.sum())
    ret=s.return_yen.astype(float)
    if cap is not None:
        ret=np.where(ret>0,np.minimum(ret,cap),0.0)
    total=float(np.sum(ret))
    h=g[g.y3head==1]
    return {
        'R':len(g),'head':100*g.y3head.mean() if len(g) else 0,
        'hit':100*g.hit.mean() if len(g) else 0,
        'cov':100*h.hit.mean() if len(h) else 0,
        'cost':cost,'ret':total,'roi':100*total/cost if cost else 0,
    }

def apply_rule(d,r):
    q=d[d.p3head>=r['p3']]
    for col,key in [('turn_margin23','turn'),('st_margin23','st'),('straight_margin23','straight'),('ex_margin23','ex')]:
        if r[key] is not None:
            q=q[pd.to_numeric(q[col],errors='coerce')>=r[key]]
    return q

def rule_text(r):
    a=[f"p3>={r['p3']:.3f}"]
    for k,label in [('turn','turn'),('st','ST'),('straight','straight'),('ex','EX')]:
        if r[k] is not None:a.append(f"{label}>={r[k]:.1f}")
    return ' & '.join(a)

def main():
    b=pd.read_csv(BASE,dtype={'race_code':str})
    f=pd.read_csv(FEAT,dtype={'race_code':str},usecols=['race_code','ex_margin23','st_margin23','straight_margin23','turn_margin23'])
    f=f.drop_duplicates('race_code',keep='last')
    d=b.merge(f,on='race_code',how='left',suffixes=('','_feat'))
    # v198 already carries turn_margin23; prefer feature-source columns for all four when duplicate.
    if 'turn_margin23_feat' in d.columns:d['turn_margin23']=d['turn_margin23_feat'].combine_first(d['turn_margin23'])
    disc=d[(d.month>='2025-12')&(d.month<='2026-02')].copy()
    test=d[(d.month>='2026-03')&(d.month<='2026-06')].copy()
    rows=[]
    for p3,turn,st,straight,ex in product(P3,TURN,ST,STRAIGHT,EX):
        r={'p3':p3,'turn':turn,'st':st,'straight':straight,'ex':ex}
        g=apply_rule(disc,r)
        if len(g)<MIN_DISC_R:continue
        m=metr(g); c=metr(g,CAP)
        # robustness-first score: capped ROI, then ordinary ROI, then sample size/head rate.
        score=c['roi'] + .20*m['roi'] + .03*min(len(g),100) + .05*m['head']
        rows.append({**r,'rule':rule_text(r),'disc_R':len(g),'disc_head':m['head'],'disc_hit':m['hit'],'disc_roi':m['roi'],'disc_cap10k_roi':c['roi'],'score':score})
    z=pd.DataFrame(rows).sort_values(['score','disc_cap10k_roi','disc_R'],ascending=False)
    # avoid near-duplicate top rules: keep unique selected race sets
    selected=[]; seen=set()
    for _,rr in z.iterrows():
        r=rr.to_dict(); g=apply_rule(disc,r); key=tuple(sorted(g.race_code.tolist()))
        if key in seen:continue
        seen.add(key); selected.append(r)
        if len(selected)>=TOPK:break
    out=[]
    for rank,r in enumerate(selected,1):
        gd=apply_rule(disc,r); gt=apply_rule(test,r)
        md,cd=metr(gd),metr(gd,CAP); mt,ct=metr(gt),metr(gt,CAP)
        out.append({'rank':rank,'rule':r['rule'],
                    'disc_R':md['R'],'disc_head':md['head'],'disc_hit':md['hit'],'disc_roi':md['roi'],'disc_cap10k_roi':cd['roi'],
                    'test_R':mt['R'],'test_head':mt['head'],'test_hit':mt['hit'],'test_roi':mt['roi'],'test_cap10k_roi':ct['roi']})
    od=pd.DataFrame(out); od.to_csv(OUT,index=False)
    bd,bt=metr(disc),metr(test)
    L=['# v201 3号艇 combo discovery -> locked late validation','',
       '- discovery: 2025-12..2026-02 only','- locked test: 2026-03..2026-06 only',
       '- joined features: ex_margin23 / st_margin23 / straight_margin23 / turn_margin23',
       '- search ranking emphasizes 10,000-yen capped ROI to reduce jackpot dependence',
       '- minimum discovery sample: 15 races','- exploratory only; production is unchanged','',
       '## Baseline','|segment|R|3-head|hit|ROI|','|---|---:|---:|---:|---:|',
       f"|DISCOVERY BASE|{bd['R']}|{bd['head']:.2f}%|{bd['hit']:.2f}%|{bd['roi']:.1f}%|",
       f"|LOCKED TEST BASE|{bt['R']}|{bt['head']:.2f}%|{bt['hit']:.2f}%|{bt['roi']:.1f}%|",'',
       '## Top locked rules','|rank|rule|Disc R|Disc ROI|Disc cap10k|Test R|Test head|Test hit|Test ROI|Test cap10k|',
       '|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for x in out:
        L.append(f"|{x['rank']}|{x['rule']}|{x['disc_R']}|{x['disc_roi']:.1f}%|{x['disc_cap10k_roi']:.1f}%|{x['test_R']}|{x['test_head']:.2f}%|{x['test_hit']:.2f}%|{x['test_roi']:.1f}%|{x['test_cap10k_roi']:.1f}%|")
    # candidate flag only when test sample is nontrivial and both raw/capped ROI clear 100.
    good=[x for x in out if x['test_R']>=20 and x['test_roi']>=100 and x['test_cap10k_roi']>=100]
    L += ['','## Interpretation']
    if good:
        L.append(f'- {len(good)} rule(s) cleared the provisional locked-test screen (R>=20, raw ROI>=100%, capped ROI>=100%).')
        L.append('- These become SHADOW candidates only; they are not production-adopted because the feature family/grid was designed after prior historical inspection.')
    else:
        L.append('- No rule cleared the provisional locked-test screen (R>=20, raw ROI>=100%, capped ROI>=100%).')
        L.append('- Keep v165/v166 production unchanged; do not force a combo filter from this search.')
    SUM.write_text('\n'.join(L)+'\n',encoding='utf-8')
    print('\n'.join(L))
if __name__=='__main__':main()
