#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import json, os
import numpy as np
import pandas as pd

OUT=Path('/tmp/head4_156r_expansion_rerank'); OUT.mkdir(parents=True,exist_ok=True)
DEV=('2026-04','2026-05','2026-06'); SUP=('2026-07','2026-08'); MONTHS=DEV+SUP
COMPS=(1.5,2.0,2.25,2.5,2.75,3.0,3.5,4.0,5.0)
BETAS=(.5,.75,1.0,1.25,1.5,1.75,2.0,2.25,2.5)
QCUTS=tuple(round(x,3) for x in np.arange(.55,1.401,.025))
HFS=(.08,.12,.16,.20,.24,.28); MFS=(.20,.25,.30,.325,.35,.375,.40)
SFS=(-.80,-.70,-.60,-.50); OFS=(-.35,-.25,-.15,-.057777777777777706)

def fullmet(z,mask):
    q=z[mask]; out={'R':int(len(q)),'head4':int(q.head4.sum()),'head4_rate':100*float(q.head4.mean()),
                    'exact3':int(q.raw_hit.sum()),'ROI':100*float(q.payout_if_bet.sum())/(10000*len(q))}
    rois=[]
    for mon in MONTHS:
        g=q[q.month.eq(mon)]; roi=100*float(g.payout_if_bet.sum())/(10000*len(g))
        out[f'{mon}_R']=int(len(g));out[f'{mon}_head4']=int(g.head4.sum())
        out[f'{mon}_head4_rate']=100*float(g.head4.mean());out[f'{mon}_ROI']=roi;rois.append(roi)
    out['monthly_floor_ROI']=min(rois)
    for name,mons in [('dev',DEV),('support',SUP)]:
        g=q[q.month.isin(mons)]
        out[f'{name}_R']=int(len(g));out[f'{name}_head4']=int(g.head4.sum())
        out[f'{name}_head4_rate']=100*float(g.head4.mean());out[f'{name}_exact3']=int(g.raw_hit.sum())
        out[f'{name}_ROI']=100*float(g.payout_if_bet.sum())/(10000*len(g))
    return out

def main():
    p=os.environ.get('RACE_DETAIL_226')
    if not p: raise RuntimeError('RACE_DETAIL_226 missing')
    z=pd.read_csv(p,dtype={'race_code':str});z['race_code']=z.race_code.astype(str).str.zfill(12)
    if any(z.month.astype(str).str.startswith('2026-09')):raise RuntimeError('SEPTEMBER ACCESS')
    base77=z.is_old164.eq(1)&(((z.composite_odds>=7)&(z.opponent_mass>=.425))|((z.composite_odds<7)&(z.head_prob>=.22)&(z.opponent_mass>=.375)&(z.composite_odds>=3)))
    base120=base77 | (z.is_old164.eq(1)&(~base77)&(z.composite_odds>=2.5)&(z.quality>=.82))
    if int(base120.sum())!=120:raise RuntimeError('base120 drift')
    current_add=(~base120)&z.composite_odds.ge(3.5)&z.quality.ge(.75)&z.head_prob.ge(.16)&z.opponent_mass.ge(.30)&z.st4_adv_inside.ge(-.80)&z.orig4_adv_inside.ge(-.35)
    if int(current_add.sum())!=36:raise RuntimeError('current add drift')
    current=fullmet(z,base120|current_add)
    rows=[];nonbase=~base120
    for beta in BETAS:
      score=z.head_prob+beta*z.opponent_mass
      for qc in QCUTS:
       m0=nonbase&score.ge(qc)
       if int(m0.sum())<36:continue
       for cf in COMPS:
        m1=m0&z.composite_odds.ge(cf)
        if int(m1.sum())<36:continue
        for hf in HFS:
         m2=m1&z.head_prob.ge(hf)
         if int(m2.sum())<36:continue
         for mf in MFS:
          m3=m2&z.opponent_mass.ge(mf)
          if int(m3.sum())<36:continue
          for sf in SFS:
           m4=m3&z.st4_adv_inside.ge(sf)
           if int(m4.sum())<36:continue
           for of in OFS:
            add=m4&z.orig4_adv_inside.ge(of)
            if int(add.sum())!=36:continue
            rows.append({'beta':beta,'quality_cut':qc,'comp_floor':cf,'head_floor':hf,'mass_floor':mf,'st_floor':sf,'orig_floor':of,'added_R':36,**fullmet(z,base120|add)})
    g=pd.DataFrame(rows)
    if g.empty:raise RuntimeError('no exact156 rerank cells')
    roi_ok=g[g.ROI>=current['ROI']-1e-9].copy().sort_values(['head4_rate','ROI','monthly_floor_ROI','support_ROI'],ascending=False)
    best=roi_ok.iloc[0]
    robust=g[(g.ROI>=current['ROI']-1e-9)&(g.monthly_floor_ROI>=current['monthly_floor_ROI']-1e-9)].copy().sort_values(['head4_rate','ROI'],ascending=False)
    floor80=g[(g.ROI>=current['ROI']-1e-9)&(g.monthly_floor_ROI>=80)].copy().sort_values(['head4_rate','ROI'],ascending=False)
    devok=g[g.dev_ROI>=current['dev_ROI']-1e-9].copy().sort_values(['dev_head4_rate','dev_ROI','support_head4_rate','support_ROI'],ascending=False)
    g.to_csv(OUT/'rerank_grid_exact156.csv',index=False);roi_ok.head(500).to_csv(OUT/'roi_preserving_ranked.csv',index=False)
    result={'current156':current,'grid_cells':int(len(g)),'roi_preserving_cells':int(len(roi_ok)),
      'best_headrate_exact156_roi_preserving':best.to_dict(),'best_headrate_gain_pp':float(best.head4_rate-current['head4_rate']),
      'best_head_count_gain':int(best.head4-current['head4']),'best_exact3_gain':int(best.exact3-current['exact3']),
      'best_roi_gain_pp':float(best.ROI-current['ROI']),'best_floor_change_pp':float(best.monthly_floor_ROI-current['monthly_floor_ROI']),
      'best_support_roi_change_pp':float(best.support_ROI-current['support_ROI']),
      'roi_and_current_floor_preserving_cells':int(len(robust)),
      'best_full_robust':robust.iloc[0].to_dict() if len(robust) else None,
      'roi_and_floor80_cells':int(len(floor80),'') if False else int(len(floor80)),
      'best_floor80':floor80.iloc[0].to_dict() if len(floor80) else None,
      'development_first_candidate':devok.iloc[0].to_dict() if len(devok) else None,
      'SEPTEMBER_OUTCOMES_READ':False,'PRODUCTION_CHANGED':False,'AUDIT_OK':True}
    (OUT/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,default=str)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2,default=str))
    print('HEAD4_156R_EXPANSION_RERANK_OK');print('SEPTEMBER_UNREAD')
if __name__=='__main__':main()
