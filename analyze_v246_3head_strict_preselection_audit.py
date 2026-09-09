#!/usr/bin/env python3
from pathlib import Path
import numpy as np
import pandas as pd

SRC=Path('analysis_v243_3head_expand_feature_audit.csv')
RULES=Path('analysis_v243_3head_expand_rule_search.csv')
OUT=Path('analysis_v246_3head_strict_preselection_audit.csv')
SUM=Path('summary_v246_3head_strict_preselection_audit.md')
BANK=10000


def ff(s): return pd.to_numeric(s,errors='coerce')

def metrics(g):
    n=len(g)
    if not n:return 0,np.nan,np.nan
    h=float(ff(g.trifecta_hit).fillna(0).sum())/n
    roi=float(ff(g.ret).fillna(0).sum())/(n*BANK)
    return n,h,roi

# STRICT PRE: only information known before current-race exhibition.
# Historical exhibition (b3_vh_*) is allowed because it is from PRIOR races.
# National/recent-form decomposition is allowed.
# Current-program features are allowed only for race-card/Waku10/history metrics.
PRE_CURRENT_METRICS=('wr','local','motor','waku_wr','nst','waku_st','waku_sr','pastwin','meetst','grade')
POST_CURRENT_METRICS=('ex','st','lap','turn','straight','origavg','tilt')

def strict_pre(c):
    if not c.startswith('f__'):return False
    z=c[3:]
    if z.startswith('b3_vh_'):return True
    if z.startswith('f_b3_') or z.startswith('f_rel_'):return True
    if not z.startswith('c_'):return False
    # composites such as wall/attack/outer/spreads use current exhibition => reject.
    if z.startswith(('c_wall','c_attack','c_outer','c_ex_','c_st_','c_turn_','c_straight_')):return False
    # reject any explicit current exhibition/preview metric token.
    toks=z.split('_')
    if any(t in POST_CURRENT_METRICS for t in toks):return False
    # accept only if at least one explicitly PRE current metric is represented.
    # Handles c_b3_motor and c_b3_minus_bN_motor, inside/outside variants.
    return any(z.endswith('_'+m) or ('_'+m+'_') in z for m in PRE_CURRENT_METRICS)


def main():
    q=pd.read_csv(SRC); rr=pd.read_csv(RULES)
    cand=rr[rr.R==182].copy()
    cand['_d']=(cand.hit-.3846153846).abs()+(cand.roi-1.1973).abs()
    best=cand.sort_values('_d').iloc[0]
    base=(ff(q.bet)==1)&(ff(q.p3)>=.45)&ff(q.raw_top_n).between(7,18)&ff(q.comp_odds).between(3.05,4.0)
    ef,eo,et=str(best.exclude_feature),str(best.exclude_op),float(best.exclude_thr)
    x=ff(q[ef]); keep=(x>=et) if eo=='>=' else (x<=et)
    final=base&keep.fillna(False)
    rf,ro,rt=str(best.rescue_feature),str(best.rescue_op),float(best.rescue_thr)
    pool=(ff(q.bet)==1)&(~base); x=ff(q[rf])
    rescue=pool&(((x>=rt) if ro=='>=' else (x<=rt)).fillna(False))
    final|=rescue

    u=q[(ff(q.pair_rank_invalid)==0)].copy(); u['_final']=final.loc[u.index].astype(int)
    pre=[c for c in u.columns if strict_pre(c) and ff(u[c]).notna().sum()>=100 and ff(u[c]).nunique()>=3]
    audits=[]
    for c in pre:
        a=ff(u.loc[u._final==1,c]);b=ff(u.loc[u._final==0,c]);sd=ff(u[c]).std()
        e=(a.mean()-b.mean())/sd if np.isfinite(sd) and sd>0 else np.nan
        audits.append((c,e))
    audits=sorted(audits,key=lambda z:abs(z[1]) if np.isfinite(z[1]) else -1,reverse=True)
    score=pd.Series(0.,index=u.index);used=[]
    for c,e in audits[:8]:
        if not np.isfinite(e) or abs(e)<.03:continue
        r=ff(u[c]).rank(pct=True);score+=r if e>0 else 1-r;used.append((c,e))
    if not used:raise RuntimeError('no strict PRE features')
    u['_pre_score']=score/len(used)
    nfinal=int(u._final.sum()); rows=[]
    for mult in [1,1.25,1.5,1.75,2,2.5,3,3.5,4]:
        n=min(len(u),max(1,round(nfinal*mult)));p=u.nlargest(n,'_pre_score');cap=p[p._final==1]
        R,h,roi=metrics(cap)
        rows.append({'mult':mult,'pre_R':n,'captured_final_R':R,'final_recall':R/nfinal,'pre_precision':R/n,'captured_final_hit':h,'captured_final_roi':roi})
    res=pd.DataFrame(rows)
    order=u.sort_values('_pre_score',ascending=False).copy();nS=min(len(order),round(nfinal*1.5));nA=min(len(order),round(nfinal*2.5));nB=min(len(order),round(nfinal*4))
    order['pre_grade']='OUT';order.iloc[:nB,order.columns.get_loc('pre_grade')]='B';order.iloc[:nA,order.columns.get_loc('pre_grade')]='A';order.iloc[:nS,order.columns.get_loc('pre_grade')]='S'
    order[['month','date','race_code','_pre_score','pre_grade','_final']+[c for c,_ in audits[:12]]].to_csv(OUT,index=False)
    fm=metrics(q[final])
    L=['# v246 strict PRE-exhibition audit','',
       '- STRICT PRE means before current-race exhibition. Current EX/ST/lap/turn/straight/original exhibition/tilt and composites using them are excluded.',
       '- Prior-race exhibition history is allowed because it is already known before the target race.',
       '- Dec2025-Aug2026 remains IN-SAMPLE / selection-contaminated; this measures operational feasibility, not pristine validation.',
       f'- Canonical v243 final: R={fm[0]}, hit={100*fm[1]:.2f}%, ROI={100*fm[2]:.2f}%.','',
       '## Strict PRE features used','|feature|direction|effect|','|---|---|---:|']
    for c,e in used:L.append(f'|{c}|{"high" if e>0 else "low"}|{e:.3f}|')
    L += ['','## Candidate volume vs final capture','|PRE R|captured|recall|precision|captured hit|captured ROI|','|---:|---:|---:|---:|---:|---:|']
    for _,r in res.iterrows():L.append(f'|{int(r.pre_R)}|{int(r.captured_final_R)}|{100*r.final_recall:.2f}%|{100*r.pre_precision:.2f}%|{100*r.captured_final_hit:.2f}%|{100*r.captured_final_roi:.2f}%|')
    L += ['',f'- S top {nS}; A {nS+1}-{nA}; B {nA+1}-{nB}.']
    SUM.write_text('\n'.join(L)+'\n',encoding='utf-8');print('\n'.join(L))

if __name__=='__main__':main()
