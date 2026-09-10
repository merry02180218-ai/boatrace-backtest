#!/usr/bin/env python3
"""v272: robustness audit of the v271 4-head A-rank expansion.

This does NOT change frozen v268.  It tests the v271-selected BROAD gate
(PRE>=0.18, POST>=0.18) with a narrow A-score neighborhood and a rotating
leave-one-month-out threshold choice.  Jul/Aug are excluded completely.

Because BROAD itself was identified retrospectively in v271, this remains
model-selection evidence, not pristine/OOS evidence.
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
import analyze_v271_4head_arank_expansion as v271

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'analysis_v272_4head_arank_robustness.csv'
CV=ROOT/'analysis_v272_4head_arank_lomo.csv'
SUM=ROOT/'summary_v272_4head_arank_robustness.md'
BANK=10000
MONTHS=('2026-04','2026-05','2026-06')
PRE_CUT=.18
POST_CUT=.18
CUTS=tuple(np.round(np.arange(.24,.331,.01),2))
TARGET_2M=67  # ~100R over three months scaled to two training months


def met(q):
    if q.empty:return {'R':0,'head':np.nan,'hit':np.nan,'roi':np.nan,'floor':np.nan,'months':''}
    ret=float(q.return_yen.sum()); roi=100*ret/(len(q)*BANK)
    mm=[]
    for m,g in q.groupby('month'):
        r=100*float(g.return_yen.sum())/(len(g)*BANK)
        mm.append((m,len(g),r,100*g.actual_head4.mean(),100*g.hit.mean()))
    return {'R':len(q),'head':100*q.actual_head4.mean(),'hit':100*q.hit.mean(),'roi':roi,
            'floor':min(x[2] for x in mm),
            'months':';'.join(f'{m}:{n}R ROI{r:.2f}% head{h:.2f}% hit{hit:.2f}%' for m,n,r,h,hit in mm)}


def select(races,cut,months):
    s=races[races.is_S & races.month.isin(months)].copy()
    a=races[(~races.is_S)&races.month.isin(months)&(races.PRE>=PRE_CUT)&(races.POST>=POST_CUT)&(races.a_score>=cut)].copy()
    c=pd.concat([s,a],ignore_index=True).drop_duplicates('race_code')
    return s,a,c


def main():
    scored=v271.oof_a_scores(); races=v271.settle_all(scored)
    races['is_S']=races.is_S.astype(bool)
    rows=[]
    for cut in CUTS:
        s,a,c=select(races,cut,MONTHS)
        sm,am,cm=met(s),met(a),met(c)
        rows.append({'cut':cut,
                     'a_R':am['R'],'a_head_pct':am['head'],'a_hit_pct':am['hit'],'a_roi_pct':am['roi'],'a_floor_pct':am['floor'],'a_months':am['months'],
                     'combined_R':cm['R'],'combined_head_pct':cm['head'],'combined_hit_pct':cm['hit'],'combined_roi_pct':cm['roi'],'combined_floor_pct':cm['floor'],'combined_months':cm['months']})
    tab=pd.DataFrame(rows);tab.to_csv(OUT,index=False)

    cv=[]
    for hold in MONTHS:
        train=tuple(m for m in MONTHS if m!=hold)
        cand=[]
        for cut in CUTS:
            s,a,c=select(races,cut,train); am,cm=met(a),met(c)
            if am['R']<15 or not (55<=cm['R']<=75):continue
            if cm['roi']<100 or cm['floor']<90:continue
            cand.append((abs(cm['R']-TARGET_2M),-cm['floor'],-cm['roi'],cut,am,cm))
        if not cand:
            cv.append({'holdout':hold,'selected_cut':np.nan,'status':'NO_TRAIN_CELL'});continue
        cand.sort();_,_,_,cut,atr,ctr=cand[0]
        _,aho,cho=select(races,cut,(hold,))
        ah, ch=met(aho),met(cho)
        cv.append({'holdout':hold,'selected_cut':cut,'status':'OK',
                   'train_combined_R':ctr['R'],'train_combined_roi_pct':ctr['roi'],'train_combined_floor_pct':ctr['floor'],
                   'holdout_A_R':ah['R'],'holdout_A_head_pct':ah['head'],'holdout_A_hit_pct':ah['hit'],'holdout_A_roi_pct':ah['roi'],
                   'holdout_combined_R':ch['R'],'holdout_combined_head_pct':ch['head'],'holdout_combined_hit_pct':ch['hit'],'holdout_combined_roi_pct':ch['roi']})
    cvd=pd.DataFrame(cv);cvd.to_csv(CV,index=False)

    fixed=tab.loc[np.isclose(tab.cut,.28)].iloc[0]
    neigh=tab[tab.cut.between(.27,.30)]
    ok=(cvd.status.eq('OK').all() and (cvd.holdout_combined_roi_pct>=100).all())
    L=['# v272 4-head A-rank robustness audit','',
       '- v268 S-rank remains untouched.',
       '- Jul/Aug 2026 excluded completely.',
       '- Gate is fixed from v271 at PRE>=0.18 / POST>=0.18; only the nearby A-score threshold is stress-tested.',
       '- Leave-one-month-out: choose threshold on two months, evaluate the untouched third month.',
       '- BROAD gate itself came from v271, so this is robustness/model-selection evidence, not pristine OOS.','',
       '## Fixed v271 candidate: A-score >= 0.28',
       f"- A={int(fixed.a_R)}R, A head={fixed.a_head_pct:.2f}%, A hit={fixed.a_hit_pct:.2f}%, A ROI={fixed.a_roi_pct:.2f}%.",
       f"- S+A={int(fixed.combined_R)}R, head={fixed.combined_head_pct:.2f}%, hit={fixed.combined_hit_pct:.2f}%, ROI={fixed.combined_roi_pct:.2f}%, monthly floor={fixed.combined_floor_pct:.2f}%.",
       f"- Months: {fixed.combined_months}",'',
       '## Threshold neighborhood','|A cut|A R|A head|A ROI|S+A R|S+A head|S+A ROI|min month ROI|','|---:|---:|---:|---:|---:|---:|---:|---:|']
    for _,r in tab.iterrows():
        L.append(f"|{r.cut:.2f}|{int(r.a_R)}|{r.a_head_pct:.2f}%|{r.a_roi_pct:.2f}%|{int(r.combined_R)}|{r.combined_head_pct:.2f}%|{r.combined_roi_pct:.2f}%|{r.combined_floor_pct:.2f}%|")
    L+=['','## Rotating leave-one-month-out threshold test','|held-out month|cut chosen on other 2 months|train S+A R|train ROI|train floor|holdout A R|holdout A ROI|holdout S+A R|holdout S+A ROI|','|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for _,r in cvd.iterrows():
        if r.status!='OK':L.append(f"|{r.holdout}|--|--|--|--|--|--|--|--|")
        else:L.append(f"|{r.holdout}|{r.selected_cut:.2f}|{int(r.train_combined_R)}|{r.train_combined_roi_pct:.2f}%|{r.train_combined_floor_pct:.2f}%|{int(r.holdout_A_R)}|{r.holdout_A_roi_pct:.2f}%|{int(r.holdout_combined_R)}|{r.holdout_combined_roi_pct:.2f}%|")
    L+=['','## Robustness decision',
        f"- All rotating held-out months keep combined ROI >=100%: {'YES' if ok else 'NO'}.",
        f"- A-score 0.27-0.30 neighborhood combined ROI range: {neigh.combined_roi_pct.min():.2f}% to {neigh.combined_roi_pct.max():.2f}%.",
        f"- Same neighborhood monthly-floor range: {neigh.combined_floor_pct.min():.2f}% to {neigh.combined_floor_pct.max():.2f}%.",
        '- If frozen later, keep A-rank separate from v268 S-rank and map the OOF score threshold to the final live model outcome-blind before prospective use.',
        '- Do not inspect/tune against September results before the A-rank freeze.','']
    SUM.write_text('\n'.join(L),encoding='utf-8');print('\n'.join(L))

if __name__=='__main__':main()
