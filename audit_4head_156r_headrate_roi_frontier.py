#!/usr/bin/env python3
"""Exact-volume 4HEAD head-rate optimization under ROI constraints.

Consumes the frozen Stage2 38,808-cell grid.
September is not present. This audit does not change production.
"""
from __future__ import annotations
from pathlib import Path
import json, os
import pandas as pd

OUT=Path('/tmp/head4_156r_headrate_roi_frontier'); OUT.mkdir(parents=True,exist_ok=True)

CURRENT={
  'comp_floor':3.5,'quality_cut':.75,'head_floor':.16,'mass_floor':.30,
  'st_floor':-.80,'orig_floor':-.35,
}
TOL=1e-9

def main():
    p=os.environ.get('EXPANDED_GRID')
    if not p: raise RuntimeError('EXPANDED_GRID missing')
    g=pd.read_csv(p)

    cur=g[
      (g.comp_floor==CURRENT['comp_floor']) &
      (g.quality_cut==CURRENT['quality_cut']) &
      (g.head_floor==CURRENT['head_floor']) &
      (g.mass_floor==CURRENT['mass_floor']) &
      (g.st_floor==CURRENT['st_floor']) &
      (g.orig_floor==CURRENT['orig_floor'])
    ].copy()
    if len(cur)!=1: raise RuntimeError(f'current156 row count {len(cur)}')
    c=cur.iloc[0]
    if int(c.all_R)!=156 or int(c.all_head4)!=65:
        raise RuntimeError('current156 parity failed')

    exact=g[(g.all_R==156)&(g.all_ROI>=float(c.all_ROI)-TOL)].copy()
    exact=exact.sort_values(
      ['all_head4_rate','all_ROI','monthly_floor_ROI','support_ROI'],
      ascending=[False,False,False,False]
    )
    best=exact.iloc[0]

    robust_floor=exact[exact.monthly_floor_ROI>=float(c.monthly_floor_ROI)-TOL].copy()
    robust_support=exact[exact.support_ROI>=float(c.support_ROI)-TOL].copy()
    robust_both=exact[
      (exact.monthly_floor_ROI>=float(c.monthly_floor_ROI)-TOL) &
      (exact.support_ROI>=float(c.support_ROI)-TOL)
    ].copy()

    near=g[
      g.all_R.between(150,162) &
      (g.all_ROI>=float(c.all_ROI)-TOL) &
      (g.monthly_floor_ROI>=float(c.monthly_floor_ROI)-TOL)
    ].copy().sort_values(
      ['all_head4_rate','all_ROI','all_R'],ascending=[False,False,False]
    )

    cols=[
      'comp_floor','quality_cut','head_floor','mass_floor','st_floor','orig_floor',
      'added_R','all_R','all_head4','all_head4_rate','all_exact3','all_ROI',
      'support_R','support_head4','support_head4_rate','support_ROI','monthly_floor_ROI',
      '2026-04_ROI','2026-05_ROI','2026-06_ROI','2026-07_ROI','2026-08_ROI'
    ]
    exact[cols].to_csv(OUT/'exact156_roi_ge_current.csv',index=False)
    near[cols].to_csv(OUT/'near_volume_robust.csv',index=False)

    result={
      'current156':c[cols].to_dict(),
      'exact156_roi_ge_current_cells':int(len(exact)),
      'best_exact156_headrate':best[cols].to_dict(),
      'headrate_gain_pp':float(best.all_head4_rate-c.all_head4_rate),
      'head_count_gain':int(best.all_head4-c.all_head4),
      'exact3_gain':int(best.all_exact3-c.all_exact3),
      'roi_gain_pp':float(best.all_ROI-c.all_ROI),
      'monthly_floor_change_pp':float(best.monthly_floor_ROI-c.monthly_floor_ROI),
      'support_roi_change_pp':float(best.support_ROI-c.support_ROI),
      'exact156_roi_and_floor_ge_current_cells':int(len(robust_floor)),
      'best_exact156_roi_and_floor_ge_current':(
          robust_floor.iloc[0][cols].to_dict() if len(robust_floor) else None),
      'exact156_roi_and_support_ge_current_cells':int(len(robust_support)),
      'best_exact156_roi_and_support_ge_current':(
          robust_support.iloc[0][cols].to_dict() if len(robust_support) else None),
      'exact156_roi_floor_support_all_ge_current_cells':int(len(robust_both)),
      'best_exact156_full_robust':(
          robust_both.iloc[0][cols].to_dict() if len(robust_both) else None),
      'near150_162_roi_floor_ge_current_cells':int(len(near)),
      'best_near150_162_robust':near.iloc[0][cols].to_dict() if len(near) else None,
      'SEPTEMBER_OUTCOMES_READ':False,
      'PRODUCTION_CHANGED':False,
      'AUDIT_OK':True,
    }
    (OUT/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,default=str)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2,default=str))
    print('HEAD4_156R_HEADRATE_ROI_FRONTIER_OK')
    print('SEPTEMBER_UNREAD')

if __name__=='__main__': main()
