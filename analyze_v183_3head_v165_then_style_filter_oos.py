#!/usr/bin/env python3
"""v183: keep production v165 p3>=0.30 candidate universe, use v180/style only as a removal filter.

NO-LEAK:
- v165 and v180/style probabilities rebuilt by strict monthly walk-forward;
- candidate universe is fixed at v165 >= .30;
- style minimum cut is selected using Mar-May only;
- Jun-Aug is completely fixed OOS;
- v166 ordered-pair lambda uses its existing Mar-May selection rule;
- payout is settlement-only after selection is fixed.
"""
import csv
from analyze_v182_3head_style_then_v165_filter_oos import build_probs, stat, month_stats
from analyze_v166_3head_pair_direct import read,ff,combo,choose,score_month

OUT='analysis_v183_3head_v165_then_style_filter_oos.csv'
SUMMARY='summary_v183_3head_v165_then_style_filter_oos.md'
VAL=['2026-03','2026-04','2026-05']; TEST=['2026-06','2026-07','2026-08']
BASE_CUT=.30
# 0 means no style filtering; all cuts are tuned on Mar-May only.
STYLE_CUTS=[0,.15,.175,.20,.225,.25,.275,.30,.325,.35,.375,.40,.425,.45]

def main():
    src,stylep,basep,cov=build_probs(); lam,_=choose(src); allrows=[]
    for mon in VAL+TEST: allrows += score_month(src,mon,lam)
    keyidx={(r['date'],r.get('race_code')):i for i,r in enumerate(src)}
    for r in allrows:
        i=keyidx.get((r['date'],r.get('race_code')),-1)
        r['p3style']=stylep.get(i,''); r['p3base']=basep.get(i,'')
    val=[r for r in allrows if r.get('v166_month') in VAL]
    tune=[]
    for sc in STYLE_CUTS:
        n,hr,hit,cv,roi=stat(val,sc,BASE_CUT); ms=month_stats(val,sc,BASE_CUT,VAL)
        min_r=min(x[0] for x in ms); worst_roi=min(x[4] for x in ms)
        tune.append((sc,n,hr,hit,cv,roi,min_r,worst_roi))
    # Protect against tiny overfit subsets. Keep at least 60% of the Mar-May production-candidate sample
    # and at least 15 races in every validation month; then ROI first.
    base_n=next(x[1] for x in tune if x[0]==0)
    eligible=[x for x in tune if x[1]>=max(60,int(base_n*.60)) and x[6]>=15]
    if not eligible: eligible=[x for x in tune if x[1]>0]
    best=max(eligible,key=lambda x:(x[5],x[7],x[3],x[2],x[1])); sc=best[0]
    test=[r for r in allrows if r.get('v166_month') in TEST]
    fs=sorted(set().union(*(r.keys() for r in test)))
    with open(OUT,'w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fs); w.writeheader(); w.writerows(test)
    ranked=sorted(tune,key=lambda x:(x[5],x[7],x[3],x[2]),reverse=True)
    L=['# v183 v165>=0.30候補 → v180/style除外フィルター → v166 top10','',
       '- 候補母集団は現行productionの v165 p3>=0.30 から一切広げない。',
       '- v180/styleは候補を増やさず、低style候補を落とす用途だけに使用。',
       '- style cutはMar-Mayだけで固定。Jun-Augは完全OOS。',
       f'- v166 pair lambda = {lam:.2f}',f"- reconstruction matched: {cov['matched_src']}",'',
       '## Mar-May style filter tuning','|style cut|R|③頭率|top10 hit|coverage|ROI|月最小R|月最悪ROI|',
       '|---:|---:|---:|---:|---:|---:|---:|---:|']
    for x in ranked:
        L.append(f'|{x[0]:.3f}|{x[1]}|{x[2]:.2f}%|{x[3]:.2f}%|{x[4]:.2f}%|{x[5]:.1f}%|{x[6]}|{x[7]:.1f}%|')
    L += ['',f'固定条件 = **v165 >= {BASE_CUT:.2f} AND v180/style >= {sc:.3f}**','','## Jun-Aug fixed OOS',
          '|month|R|③頭率|top10 hit|coverage|ROI|','|---|---:|---:|---:|---:|---:|']
    for mo in TEST:
        x=stat([r for r in test if r.get('v166_month')==mo],sc,BASE_CUT)
        L.append(f'|{mo}|{x[0]}|{x[1]:.2f}%|{x[2]:.2f}%|{x[3]:.2f}%|{x[4]:.1f}%|')
    x=stat(test,sc,BASE_CUT); L.append(f'|ALL|{x[0]}|{x[1]:.2f}%|{x[2]:.2f}%|{x[3]:.2f}%|{x[4]:.1f}%|')
    L += ['','## Current production reference','- v165 p3>=0.30 + v166 top10: Jun-Aug R270, ③頭率38.52%, hit29.26%, coverage75.96%, ROI103.2%.','',
          '## Decision rule','- ROI最優先。現行103.2%を上回るか、同等ROIでhit/③頭率/月別安定性が改善する場合のみ採用。Jun-Augを見てcutは変更しない。']
    open(SUMMARY,'w',encoding='utf-8').write('\n'.join(L)+'\n'); print('\n'.join(L))
if __name__=='__main__': main()
