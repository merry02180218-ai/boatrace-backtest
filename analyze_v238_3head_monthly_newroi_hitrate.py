#!/usr/bin/env python3
"""v238: monthly canonical 10k-Dutch ROI + trifecta hit + head hit for restored v234 replay.
No tuning. Jul/Aug NON-PRISTINE. Uses v205.round_dutch via v222.settle through v234.replay.
"""
import pandas as pd
import analyze_v234_3head_waku10_restored_replay as v234
OUT='analysis_v238_3head_monthly_newroi_hitrate.csv'; SUM='summary_v238_3head_monthly_newroi_hitrate.md'
def main():
 cov=v234.reconstruct(); common=v234.validate_parser()
 if (cov.source=='missing').any(): raise RuntimeError('missing Waku10; no imputation')
 d,dc,vc,basefs=v234.build_restored();fs=v234.full_features(d,basefs);fs=[x for x in fs if x in d.columns]
 z=v234.replay(d,vc,basefs,fs)
 q=z[['month','R','settled_R','head_rate','top10_hit','roi','non_pristine']].copy()
 q['head_hit_pct']=100*q.head_rate;q['trifecta_hit_pct']=100*q.top10_hit;q['new_roi_pct']=q.roi
 q=q[['month','R','settled_R','head_hit_pct','trifecta_hit_pct','new_roi_pct','non_pristine']]
 q.to_csv(OUT,index=False)
 L=['# v238 monthly 3-head canonical metrics','', '- ROI: exactly 10,000 yen per settled selected race, inverse-odds Dutch, 100-yen Hamilton rounding; losing race return=0.', '- Trifecta hit: actual 3-ren-tan is inside frozen v221 Top10 and receives positive Dutch stake.', '- Head hit: boat 3 actually wins among the same selected races.', '- Jul/Aug are NON-PRISTINE and descriptive only.',f'- Waku10 validation: {common} races, 0 mismatches.','', '|month|R|settled|head hit|3-ren-tan hit|new ROI|status|','|---|---:|---:|---:|---:|---:|---|']
 for _,r in q.iterrows():
  status='NON-PRISTINE' if r.non_pristine else 'research/contaminated'
  L.append(f"|{r.month}|{int(r.R)}|{int(r.settled_R)}|{r.head_hit_pct:.2f}%|{r.trifecta_hit_pct:.2f}%|{r.new_roi_pct:.2f}%|{status}|")
 SUM=open(SUM,'w',encoding='utf-8');SUM.write('\n'.join(L)+'\n');SUM.close();print('\n'.join(L))
if __name__=='__main__':main()
