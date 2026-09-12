#!/usr/bin/env python3
"""v308: expand leak-free v307 head volume (R>=204) and jointly audit v300 3-ticket opponent picks.
Development only. Jul/Aug NON-PRISTINE; Sep unread. No meet_* transfer features.
"""
from pathlib import Path
import pandas as pd
import numpy as np
import analyze_v298_1head_threat_listwise_trifecta5 as v298
import run_v300_1head_trifecta3_feature_upgrade as v300
import run_v303_1head_headmodel_transfer_ablation as v303
import run_v305_1head_leakage_audit as v305
import run_v307_1head_causal_turn_form as v307
ROOT=Path(__file__).resolve().parent
P=ROOT/'analysis_v308_1head_volume_opponent_joint'; S=ROOT/'summary_v308_1head_volume_opponent_joint.md'; TM=list(v298.TEST_MONTHS)

def main():
 v300.setup_v298(); d,_=v298.v294.freeze_true_pre(); d=v298.v294.add_prior_history(d); d=v298.v294.add_rel(d); d,th=v298.add_threat(d); fam=v298.v296.clean_manifest(d); d,tf=v303.add_transfer_features(d); d,ca=v307.add_causal(d)
 safe=list(dict.fromkeys(v305.safe_transfer(tf['TURN_FORM'])+v305.safe_transfer(tf['STMOTOR'])+ca))
 if any('meet_' in c.lower() for c in safe): raise RuntimeError('unsafe feature')
 d,_=v298.v297.settle_full_after_freeze(d); d=d[(d.valid_result==1)&(d.combo_valid==1)].copy(); masses=v303.opponent_mass(d)
 core=list(dict.fromkeys(fam['CLEAN_STATIC6_PLAYER']+th)); guard=[c for c in core if c.startswith(('b1_','b2_','b3_','b4_','rel_','attack23_','v298_'))]
 out=[]
 for tm in TM:
  tr=d[d.month<tm].copy(); te=d[d.month==tm].copy(); z=te[['date','month','race_code','venue','race','head_hit','actual_combo']].copy(); z['test_month']=tm; z['opp_mass']=[masses[str(x).zfill(12)] for x in z.race_code]
  bc=v298.v293.available(tr,core,.55); bg=v298.v293.available(tr,guard,.55); ex=v303.available(tr,safe); ph,_,_,_,_,_=v298.head_fold(tr,te,list(dict.fromkeys(bc+ex)),bg); z['p_head']=ph
  # v300 best opponent model: augmented features, SECOND L2=3 / THIRD L2=.1, TOP2xTOP2 alpha=.60.
  sl=v300.second_long(tr,True); tl=v300.conditional_long(tr,True); sm=v300.fit_listwise(sl,3); tmod=v300.fit_listwise(tl,.1); ste=v300.second_long_all(te,True); tte=v300.conditional_long_all(te,True); sp=v300.predict_long(sm,ste); tp=v300.predict_long(tmod,tte)
  for i,r in z.iterrows():
   code=str(r.race_code).zfill(12); cand=v300.tickets(code,sp,tp,.60,'TOP2XTOP2')[:3]; z.loc[i,'tickets']='|'.join(cand); z.loc[i,'exact3']=int(str(r.actual_combo) in cand)
  out.append(z); print('v308 fold',tm,flush=True)
 p=pd.concat(out,ignore_index=True)
 # Search global head-probability quantiles and opponent-mass floors; only R>=204 is eligible.
 rows=[]; mon=[]
 for q in np.arange(.70,.981,.01):
  hcut=float(p.p_head.quantile(q))
  for conf in np.arange(.30,.701,.025):
   s=p[(p.p_head>=hcut)&(p.opp_mass>=conf)].copy(); R=len(s)
   if R<204: continue
   gm=s.groupby('test_month').agg(R=('head_hit','size'),head_hits=('head_hit','sum'),exact3=('exact3','sum'))
   rows.append({'q':round(float(q),3),'conf':round(float(conf),3),'R':R,'head_hits':int(s.head_hit.sum()),'head_rate':float(s.head_hit.mean()),'exact3_hits':int(s.exact3.sum()),'exact3_rate':float(s.exact3.mean()),'worst_head_month':float((gm.head_hits/gm.R).min()),'worst_exact3_month':float((gm.exact3/gm.R).min())})
 score=pd.DataFrame(rows)
 if score.empty: raise RuntimeError('no R>=204 configs')
 # Pareto-style preference: maintain >= v307 83.82% if possible, then maximize R, exact3, stability.
 viable=score[score.head_rate>=171/204]
 if len(viable): best=viable.sort_values(['R','exact3_rate','worst_head_month'],ascending=False).iloc[0]
 else: best=score.sort_values(['head_rate','R','exact3_rate'],ascending=False).iloc[0]
 sel=p[(p.p_head>=p.p_head.quantile(float(best.q)))&(p.opp_mass>=float(best.conf))].copy(); gm=sel.groupby('test_month').agg(R=('head_hit','size'),head_hits=('head_hit','sum'),exact3_hits=('exact3','sum')).reset_index(); gm['head_rate']=gm.head_hits/gm.R; gm['exact3_rate']=gm.exact3_hits/gm.R
 p.to_csv(str(P)+'_pred.csv',index=False); score.to_csv(str(P)+'_grid.csv',index=False); gm.to_csv(str(P)+'_best_monthly.csv',index=False); sel.to_csv(str(P)+'_best_selected.csv',index=False)
 top=score.sort_values(['head_rate','R'],ascending=False).head(20)
 L=['# v308 1HEAD volume + opponent joint research','', '- Leak-free v307 head features only; no meet_* transfer features.', '- R<204 configurations are discarded.', '- v300 opponent model is recomputed fold-by-fold; exact 3-ticket misses include boat-1 losses.','', '## Selected operating point',f"- q={best.q:.3f}, opponent mass>={best.conf:.3f}",f"- R=**{int(best.R)}**, head **{int(best.head_hits)}/{int(best.R)} = {100*best.head_rate:.2f}%**",f"- exact 3-ticket **{int(best.exact3_hits)}/{int(best.R)} = {100*best.exact3_rate:.2f}%**",f"- worst monthly head {100*best.worst_head_month:.2f}%; worst monthly exact3 {100*best.worst_exact3_month:.2f}%",'', '## Monthly','|month|R|head|head rate|exact3|exact3 rate|','|---|---:|---:|---:|---:|---:|']
 for _,r in gm.iterrows(): L.append(f"|{r.test_month}|{int(r.R)}|{int(r.head_hits)}|{100*r.head_rate:.2f}%|{int(r.exact3_hits)}|{100*r.exact3_rate:.2f}%|")
 L += ['', '## Highest head-rate R>=204 diagnostics','|q|conf|R|head rate|exact3 rate|worst head|','|---:|---:|---:|---:|---:|---:|']
 for _,r in top.iterrows(): L.append(f"|{r.q:.3f}|{r.conf:.3f}|{int(r.R)}|{100*r.head_rate:.2f}%|{100*r.exact3_rate:.2f}%|{100*r.worst_head_month:.2f}%|")
 S.write_text('\n'.join(L)+'\n',encoding='utf-8'); print(S.read_text(),flush=True)
if __name__=='__main__': main()
