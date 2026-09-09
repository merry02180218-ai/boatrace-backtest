#!/usr/bin/env python3
"""v244: pre-selection audit for the v243 expanded 3-head policy.

Purpose
- Separate features known before current-race exhibition from exhibition/just-before-start features.
- Measure how well PRE-only rules can capture the v243 expanded final-selection races.
- Produce S/A/B-style preselection candidates and report recall, precision, final hit rate and ROI.

Important
- Dec2025-Aug2026 is intentionally IN-SAMPLE / selection-contaminated. Jul/Aug are included by user request.
- This is an operational audit, not pristine validation.
- Final settlement remains exact 10,000-yen inverse-odds Dutch as exported by v243/v242.
"""
from pathlib import Path
import numpy as np
import pandas as pd

SRC=Path('analysis_v243_3head_expand_feature_audit.csv')
RULES=Path('analysis_v243_3head_expand_rule_search.csv')
OUT=Path('analysis_v244_3head_preselection_audit.csv')
SUM=Path('summary_v244_3head_preselection_audit.md')
BANK=10000

# Current-race / post-exhibition tokens. Conservative: anything plausibly dependent on
# current exhibition, current ST, live odds, pair-ranker output, or settlement is excluded from PRE.
POST_TOKENS=(
    'exh','exhibition','tenji','display','stretch','turn','around','mawari','ashi',
    '_st','st_','start','attack','direct','pair_','odds','top_n','comp_','capped',
    'positive_tickets','ret','profit','trifecta_hit','y3','actual','result','course3'
)
ID_COLS={'month','date','race_code','bet','pair_rank_invalid','odds_available'}


def ff(s):
    return pd.to_numeric(s,errors='coerce')


def metrics(g):
    n=len(g)
    if n==0:return {'R':0,'hits':0,'hit':np.nan,'roi':np.nan}
    h=int(ff(g['trifecta_hit']).fillna(0).sum())
    ret=float(ff(g['ret']).fillna(0).sum())
    return {'R':n,'hits':h,'hit':h/n,'roi':ret/(n*BANK)}


def is_pre(c):
    lc=c.lower()
    if c in ID_COLS or c in {'p3'}: return False
    if not c.startswith('f__'): return False
    return not any(t in lc for t in POST_TOKENS)


def zscore_from_train(x):
    med=x.median(); sd=x.std()
    if not np.isfinite(sd) or sd==0:return pd.Series(np.nan,index=x.index)
    return (x-med)/sd


def main():
    if not SRC.exists():
        raise RuntimeError(f'{SRC} missing; run/copy v243 artifact first')
    q=pd.read_csv(SRC)
    rr=pd.read_csv(RULES) if RULES.exists() else pd.DataFrame()

    # Reconstruct the reported 182R v243 policy from the rule-search table itself.
    cand=rr[(rr.R==182)] if len(rr) and 'R' in rr else pd.DataFrame()
    if len(cand)==0:
        raise RuntimeError('182R v243 policy not found in rule-search CSV')
    # Prefer the exact 38.46% / 119.73% row if present.
    cand=cand.assign(_d=(cand.hit-.3846153846).abs()+(cand.roi-1.1973).abs())
    best=cand.sort_values('_d').iloc[0]

    base=(ff(q.bet)==1)&(ff(q.p3)>=.45)&ff(q.raw_top_n).between(7,18)&ff(q.comp_odds).between(3.05,4.0)
    final=base.copy()

    # Apply v243 chosen exclusion/rescue rule using saved columns.
    ef=str(best.get('exclude_feature','')) if pd.notna(best.get('exclude_feature','')) else ''
    eo=str(best.get('exclude_op','')) if pd.notna(best.get('exclude_op','')) else ''
    et=best.get('exclude_thr',np.nan)
    if ef and ef in q.columns and np.isfinite(float(et)):
        x=ff(q[ef]); keep=(x>=float(et)) if eo=='>=' else (x<=float(et))
        final=base & keep.fillna(False)
    rf=str(best.get('rescue_feature','')) if pd.notna(best.get('rescue_feature','')) else ''
    ro=str(best.get('rescue_op','')) if pd.notna(best.get('rescue_op','')) else ''
    rt=best.get('rescue_thr',np.nan)
    pool=(ff(q.bet)==1)&(~base)
    rescue=pd.Series(False,index=q.index)
    if rf and rf in q.columns and np.isfinite(float(rt)):
        x=ff(q[rf]); rescue=pool & (((x>=float(rt)) if ro=='>=' else (x<=float(rt))).fillna(False))
    final=final|rescue

    # Target operational final selections only; PRE candidates are generated among the same
    # model-scored race universe, before current-exhibition filters.
    universe=q[(ff(q.pair_rank_invalid)==0)].copy()
    universe['_final']=final.loc[universe.index].astype(int)

    pre=[c for c in universe.columns if is_pre(c)]
    pre=[c for c in pre if ff(universe[c]).notna().sum()>=100 and ff(universe[c]).nunique()>=3]
    if not pre: raise RuntimeError('no conservative PRE features available')

    # Single-feature discriminative audit final-vs-nonfinal, outcomes NOT used here.
    audits=[]
    for c in pre:
        a=ff(universe.loc[universe._final==1,c]); b=ff(universe.loc[universe._final==0,c])
        sd=ff(universe[c]).std()
        eff=(a.mean()-b.mean())/sd if np.isfinite(sd) and sd>0 else np.nan
        audits.append((c,a.mean(),b.mean(),eff))
    audits=sorted(audits,key=lambda z:abs(z[3]) if np.isfinite(z[3]) else -1,reverse=True)
    top=[x[0] for x in audits[:12]]

    # Rank-score using direction learned only from FINAL membership, not race result/payout.
    # This answers operational feasibility: can pre-known variables identify races that later
    # pass the final v243 rule? Thresholds are retrospective/in-sample and must not be called validated.
    score=pd.Series(0.0,index=universe.index)
    used=[]
    for c,am,bm,e in audits[:8]:
        x=ff(universe[c]); ranks=x.rank(pct=True)
        if not np.isfinite(e) or abs(e)<.03: continue
        score += ranks if e>0 else (1-ranks)
        used.append((c,'high' if e>0 else 'low',e))
    if not used: raise RuntimeError('no usable PRE score features')
    score/=len(used)
    universe['_pre_score']=score

    final_n=int(universe._final.sum())
    rows=[]
    # candidate volume multipliers around final R: 1.0x ... 4.0x
    for mult in [1.0,1.25,1.5,1.75,2.0,2.5,3.0,3.5,4.0]:
        n=min(len(universe),max(1,int(round(final_n*mult))))
        idx=universe.nlargest(n,'_pre_score').index
        pick=universe.loc[idx]
        captured=int(pick._final.sum())
        recall=captured/final_n if final_n else np.nan
        precision=captured/n if n else np.nan
        # Operational final performance among captured final selections.
        settled=pick[pick._final==1]
        mm=metrics(settled)
        rows.append({'mult':mult,'pre_R':n,'captured_final_R':captured,'final_recall':recall,
                     'pre_precision':precision,'captured_final_hit':mm['hit'],'captured_final_roi':mm['roi']})
    res=pd.DataFrame(rows)

    # S/A/B: S top 1.5x final volume, A next to 2.5x, B next to 4.0x.
    order=universe.sort_values('_pre_score',ascending=False).copy()
    nS=min(len(order),int(round(final_n*1.5)))
    nA=min(len(order),int(round(final_n*2.5)))
    nB=min(len(order),int(round(final_n*4.0)))
    order['pre_grade']='OUT'
    order.iloc[:nB,order.columns.get_loc('pre_grade')]='B'
    order.iloc[:nA,order.columns.get_loc('pre_grade')]='A'
    order.iloc[:nS,order.columns.get_loc('pre_grade')]='S'
    keepcols=['month','date','race_code','_pre_score','pre_grade','_final']+[c for c in top if c in order.columns]
    order[keepcols].to_csv(OUT,index=False)

    fm=metrics(q[final])
    L=['# v244 3-head PRE-selection audit','',
       '- Dec2025-Aug2026 IN-SAMPLE / selection-contaminated operational audit; not pristine validation.',
       '- PRE feature set conservatively excludes current exhibition/ST, live odds, pair-ranker outputs, settlement/result fields.',
       f'- Reconstructed v243 final policy: R={fm["R"]}, hit={100*fm["hit"]:.2f}%, ROI={100*fm["roi"]:.2f}%.',
       f'- v243 rule: exclude `{ef} {eo} {et}`; rescue `{rf} {ro} {rt}`.','',
       '## PRE features used in rank score','|feature|direction|effect final-vs-other|','|---|---|---:|']
    for c,d,e in used:L.append(f'|{c}|{d}|{e:.3f}|')
    L += ['', '## PRE candidate-volume vs capture of v243 final races',
          '|PRE candidates|captured final|recall|precision|captured-final hit|captured-final ROI|','|---:|---:|---:|---:|---:|---:|']
    for _,r in res.iterrows():
        L.append(f'|{int(r.pre_R)}|{int(r.captured_final_R)}|{100*r.final_recall:.2f}%|{100*r.pre_precision:.2f}%|{100*r.captured_final_hit:.2f}%|{100*r.captured_final_roi:.2f}%|')
    L += ['', '## Operational interpretation',
          f'- S: top {nS} PRE candidates; A: ranks {nS+1}-{nA}; B: ranks {nA+1}-{nB}.',
          '- The key feasibility measure is final_recall: how many races that later satisfy v243 can already be flagged before exhibition.',
          '- Because PRE-score feature directions and cut sizes were selected retrospectively, use this only to design the live two-stage workflow; validate prospectively before production claims.']
    SUM.write_text('\n'.join(L)+'\n',encoding='utf-8')
    print('\n'.join(L))

if __name__=='__main__':main()
