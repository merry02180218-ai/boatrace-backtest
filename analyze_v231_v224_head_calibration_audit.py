#!/usr/bin/env python3
"""v231: audit v224 FULL_DECOMP head calibration on its original Dec2025-Jun2026 evaluation.
No rule discovery. Jul/Aug excluded. Reproduces v224 monthly prior-only selection and decomposes
final Top10 hit into actual boat-3 head rate and conditional Top10 pair coverage.
"""
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.metrics import brier_score_loss
import analyze_v165_3head_monthly_walkforward as v165
import analyze_v221_3head_scenario_pair as v221
import analyze_v222_3head_broad_feature_audit as v222
import analyze_v223_3head_unused_feature_audit as v223
import analyze_v224_3head_national_form_decompose as v224

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'analysis_v231_v224_head_calibration_audit.csv'
SUM=ROOT/'summary_v231_v224_head_calibration_audit.md'

def main():
 raw=pd.read_csv(v224.SRC,dtype={'race_code':str}); dc=v165.pc(raw,['date','race_date','ymd']); vc=v165.pc(raw,['venue','jcd','stadium','place']); y,_=v165.target(raw); basefs=v165.feats(raw)
 raw['_date']=pd.to_datetime(raw[dc].astype(str),errors='coerce'); raw['_y']=y; raw=raw[raw._date.notna()&raw._y.notna()&(raw._date<v224.CONTAM)].copy()
 d=v221.build(raw,dc); d=v222.build_current(d,dc); d=v223.build_unused(d,dc); d=v224.add_decomp(d,dc)
 hist=v222.cols(d,'b3_vh_'); rel=[c for c in d.columns if c.startswith(('c_b3_minus_','c_b3_inside_','c_b3_outside_'))]
 cur=[c for c in v222.cols(d,'c_b3_') if not c.startswith(('c_b3_minus_','c_b3_inside_','c_b3_outside_'))]
 cur += [c for c in d.columns if c.startswith(('c_wall','c_attack3','c_outer','c_ex_spread','c_st_spread','c_turn_spread','c_straight_spread'))]
 best=v223.uniq(list(basefs)+hist+cur+rel)
 m1=[c for c in d.columns if c.startswith('f_b3_m1_')]; m12=[c for c in d.columns if c.startswith('f_b3_m12_')]; m35=[c for c in d.columns if c.startswith('f_b3_m35_')]; trend=[c for c in d.columns if c.startswith('f_b3_trend_')]; lay=['f_b3_layoff']; grade=['f_b3_grade','f_b3_m1_grade']; rctx=v224.cols(d,'f_rel_')
 fs=v223.uniq(best+m1+m12+m35+trend+lay+grade+rctx)
 rows=[]
 for mon in v224.EVAL_MONTHS:
  first=pd.Timestamp(mon+'-01'); nextm=first+pd.offsets.MonthBegin(1); tr=d[d._date<first]; pair=v222.fit_pair(tr,'V221')
  base_te,_=v223.fit_head(d,list(basefs),vc,first,nextm); k=max(1,int((base_te._p>=.30).sum()))
  te,nfeat=v223.fit_head(d,fs,vc,first,nextm); sel=te.nlargest(k,'_p').copy()
  for _,r in sel.iterrows():
   if v223.ii(r.get('valid_result'))!=1 or v223.ii(r.get('course3'),3)!=3: continue
   act=v222.v166.combo(r.get('actual_combo')); actual='-'.join(map(str,act)) if len(act)==3 else ''
   if not actual: continue
   ts=v222.order(r,pair,'V221'); rank=ts.index(actual)+1 if actual in ts else 0
   rows.append({'month':mon,'date':r._date.strftime('%Y-%m-%d'),'race_code':str(r.get('race_code','')).zfill(12),'p3':float(r._p),'y3':int(r._y),'rank':rank,'pair_top10_given_y3':int(r._y==1 and 1<=rank<=10),'final_top10_hit':int(r._y==1 and 1<=rank<=10)})
 z=pd.DataFrame(rows); z.to_csv(OUT,index=False)
 L=['# v231 v224 head calibration audit','', '- exact v224 FULL_DECOMP feature family; original Dec2025-Jun2026 monthly prior-only evaluation', '- Jul/Aug excluded; audit only, no threshold/rule discovery','', '|month|R|avg p3|actual 3-head|gap pp|pair Top10 cov given 3-head|final Top10 hit|','|---|---:|---:|---:|---:|---:|---:|']
 for mon,g in z.groupby('month',sort=True):
  h=g[g.y3==1]; cov=100*h.pair_top10_given_y3.mean() if len(h) else 0
  L.append(f'|{mon}|{len(g)}|{100*g.p3.mean():.2f}%|{100*g.y3.mean():.2f}%|{100*(g.p3.mean()-g.y3.mean()):+.2f}|{cov:.2f}%|{100*g.final_top10_hit.mean():.2f}%|')
 h=z[z.y3==1]; cov=100*h.pair_top10_given_y3.mean() if len(h) else 0
 L += ['',f'**Overall:** R={len(z)}, avg p3={100*z.p3.mean():.2f}%, actual 3-head={100*z.y3.mean():.2f}%, gap={100*(z.p3.mean()-z.y3.mean()):+.2f}pp, conditional Top10 coverage={cov:.2f}%, final Top10 hit={100*z.final_top10_hit.mean():.2f}%.','', '## Calibration bins','|p3 bin|R|avg p3|actual 3-head|gap pp|','|---|---:|---:|---:|---:|']
 z['bin']=pd.cut(z.p3,[0,.3,.4,.5,.6,.7,.8,1],include_lowest=True)
 for b,g in z.groupby('bin',observed=True): L.append(f'|{b}|{len(g)}|{100*g.p3.mean():.2f}%|{100*g.y3.mean():.2f}%|{100*(g.p3.mean()-g.y3.mean()):+.2f}|')
 SUM.write_text('\n'.join(L)+'\n',encoding='utf-8'); print('\n'.join(L))
if __name__=='__main__': main()
