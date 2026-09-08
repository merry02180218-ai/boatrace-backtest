#!/usr/bin/env python3
"""v225: combine clean national-form decomposition with weight/entry features.
Strict monthly prior-only Dec2025-Jun2026. Jul/Aug excluded. v221 pair fixed; Top10; exact 10k Dutch.
"""
from pathlib import Path
import numpy as np,pandas as pd
from sklearn.metrics import brier_score_loss
import analyze_v165_3head_monthly_walkforward as v165
import analyze_v205_3head_operational_replay as v205
import analyze_v221_3head_scenario_pair as v221
import analyze_v222_3head_broad_feature_audit as v222
import analyze_v223_3head_unused_feature_audit as v223
import analyze_v224_3head_national_form_decompose as v224
ROOT=Path(__file__).resolve().parent;SRC=ROOT/'analysis_v108_1head_feasibility.csv';OUT=ROOT/'analysis_v225_3head_form_weight_combo.csv';SUM=ROOT/'summary_v225_3head_form_weight_combo.md';EVAL=v223.EVAL_MONTHS;CONTAM=v223.CONTAM;BANK=10000

def main():
 raw=pd.read_csv(SRC,dtype={'race_code':str});dc=v165.pc(raw,['date','race_date','ymd']);vc=v165.pc(raw,['venue','jcd','stadium','place']);y,_=v165.target(raw);basefs=v165.feats(raw);raw['_date']=pd.to_datetime(raw[dc].astype(str),errors='coerce');raw['_y']=y;raw=raw[raw._date.notna()&raw._y.notna()&(raw._date<CONTAM)].copy()
 d=v221.build(raw,dc);d=v222.build_current(d,dc);d=v223.build_unused(d,dc);d=v224.add_decomp(d,dc)
 if (d._date>=CONTAM).any():raise RuntimeError('CONTAMINATION')
 hist=v222.cols(d,'b3_vh_');rel=[c for c in d if c.startswith(('c_b3_minus_','c_b3_inside_','c_b3_outside_'))];cur=[c for c in v222.cols(d,'c_b3_') if not c.startswith(('c_b3_minus_','c_b3_inside_','c_b3_outside_'))]+[c for c in d if c.startswith(('c_wall','c_attack3','c_outer','c_ex_spread','c_st_spread','c_turn_spread','c_straight_spread'))];best=v223.uniq(list(basefs)+hist+cur+rel)
 nat=[c for c in d if c.startswith('u_nat')];weight=[c for c in d if c.startswith(('u_b1_weight','u_b2_weight','u_b3_weight','u_b4_weight','u_b5_weight','u_b6_weight','u_b1_adjust','u_b2_adjust','u_b3_adjust','u_b4_adjust','u_b5_adjust','u_b6_adjust','u_b1_totalweight','u_b2_totalweight','u_b3_totalweight','u_b4_totalweight','u_b5_totalweight','u_b6_totalweight','u_adjust_total','u_b3_weight_rel'))];entry=[c for c in d if c.startswith(('u_b1_course','u_b2_course','u_b3_course','u_b4_course','u_b5_course','u_b6_course','u_course3','u_entry'))]
 m1=[c for c in d if c.startswith('f_b3_m1_')];m12=[c for c in d if c.startswith('f_b3_m12_')];m35=[c for c in d if c.startswith('f_b3_m35_')];trend=[c for c in d if c.startswith('f_b3_trend_')];lay=['f_b3_layoff'];grade=['f_b3_grade','f_b3_m1_grade'];rctx=[c for c in d if c.startswith('f_rel_')];form=v223.uniq(m1+m12+m35+trend+lay+grade+rctx)
 # Fixed interactions; no threshold/weight tuning.
 for c in ['u_b3_weight_relmean','u_b3_weight_relmin']:
  if c in d:
   for f in ['f_b3_m1_win','f_b3_m12_win','f_b3_m12_top2','f_b3_trend_win','f_b3_grade']:
    if f in d:d['ix_'+c+'__'+f]=pd.to_numeric(d[c],errors='coerce')*pd.to_numeric(d[f],errors='coerce')
 inter=[c for c in d if c.startswith('ix_')]
 groups={'V222_BEST':best,'V223_NATIONAL':v223.uniq(best+nat),'V224_FORM':v223.uniq(best+form),'NATIONAL+WEIGHT':v223.uniq(best+nat+weight),'V224+WEIGHT':v223.uniq(best+form+weight),'V224+ENTRY':v223.uniq(best+form+entry),'V224+WEIGHT+ENTRY':v223.uniq(best+form+weight+entry),'V224+WEIGHT_INTERACTIONS':v223.uniq(best+form+weight+inter)}
 odds=v205.load_odds();oi=odds.set_index('race_code',drop=False);out=[]
 for mon in EVAL:
  first=pd.Timestamp(mon+'-01');nxt=first+pd.offsets.MonthBegin(1);pair=v222.fit_pair(d[d._date<first],'V221');bte,_=v223.fit_head(d,list(basefs),vc,first,nxt);k=max(1,int((bte._p>=.30).sum()))
  for name,fs in groups.items():
   te,nf=v223.fit_head(d,fs,vc,first,nxt);sel=te.nlargest(k,'_p');rv=[]
   for _,r in sel.iterrows():
    if v223.ii(r.get('valid_result'))!=1 or v223.ii(r.get('course3'),3)!=3:continue
    act=v222.v166.combo(r.get('actual_combo'));actual='-'.join(map(str,act)) if len(act)==3 else '';code=str(r.get('race_code','')).zfill(12)
    if not actual or code not in oi.index:continue
    od=oi.loc[code];od=od.iloc[-1] if isinstance(od,pd.DataFrame) else od;ts=v222.order(r,pair,'V221');s=v222.settle(ts,od,actual)
    if s is None:continue
    rank=ts.index(actual)+1 if actual in ts else 0;rv.append({'date':r._date.strftime('%Y-%m-%d'),'race_code':code,'y3':int(r._y),'rank':rank,'hit':s[0],'ret':s[1],'profit':s[2]})
   g=pd.DataFrame(rv)
   if g.empty:continue
   h=g[g.y3==1];cov=100*((h['rank']>0)&(h['rank']<=10)).mean() if len(h) else 0;roi,md,rm1,rm3,rm5=v223.robust(g);out.append({'variant':name,'month':mon,'R':len(g),'head_rate':100*g.y3.mean(),'coverage10':cov,'hit10':100*g.hit.mean(),'roi':roi,'maxdd':md,'roi_rm1':rm1,'roi_rm3':rm3,'roi_rm5':rm5,'auc':v223.safe_auc(te._y.astype(int),te._p),'brier':float(brier_score_loss(te._y.astype(int),te._p)),'nfeat':nf})
 z=pd.DataFrame(out);z.to_csv(OUT,index=False)
 if z.empty or set(z.month)-set(EVAL):raise RuntimeError('bad/contam')
 L=['# v225 form + weight/entry combination audit','','- Dec2025-Jun2026 only; Jul/Aug excluded','- v221 pair fixed; historical odds settlement-only; fixed Top10 exact 10k Dutch','', '|variant|R|3-head|cov10|hit|ROI|min month|prof months|rm5|AUC|Brier|features|','|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|'];agg=[]
 for v,g in z.groupby('variant'):
  R=int(g.R.sum());agg.append((v,R,np.average(g.head_rate,weights=g.R),np.average(g.coverage10,weights=np.maximum(g.R*g.head_rate/100,1e-9)),np.average(g.hit10,weights=g.R),np.average(g.roi,weights=g.R),g.roi.min(),int((g.roi>=100).sum()),np.average(g.roi_rm5,weights=g.R),g.auc.mean(),g.brier.mean(),int(g.nfeat.max())))
 agg.sort(key=lambda x:(-x[5],-x[8],-x[9]))
 for a in agg:L.append(f'|{a[0]}|{a[1]}|{a[2]:.2f}%|{a[3]:.2f}%|{a[4]:.2f}%|{a[5]:.2f}%|{a[6]:.2f}%|{a[7]}/7|{a[8]:.2f}%|{a[9]:.4f}|{a[10]:.5f}|{a[11]}|')
 L+=['','## Rule','- Combination discovery only; no automatic production adoption.','- Prefer replicated monthly/rm5 gains; reject payout-spike-only gains.'];SUM.write_text('\n'.join(L)+'\n',encoding='utf-8');print('\n'.join(L))
if __name__=='__main__':main()
