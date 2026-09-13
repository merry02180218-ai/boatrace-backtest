from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
import research_v289_3head_wave31_nonlinear_gate as base
import research_v289_3head_wave34b_prototype_stability as w34b
SRC=Path('analysis_v289_3head_wave21_allrace_feature_settled.csv'); B=Path('v288_operational_pre_replay_94_baseline_codes.csv')
OUTJ=Path('research_v289_3head_wave34f_may_diagnosis.json'); OUTM=Path('research_v289_3head_wave34f_may_diagnosis.md'); OUTC=Path('analysis_v289_3head_wave34f_may_diagnosis.csv')
CUT=0.2332210614000265; AG=0.55; K=3

def main():
 df=pd.read_csv(SRC,dtype=str).fillna(''); assert df.date.max()<='2026-08-31'; bd=pd.read_csv(B,dtype=str).fillna(''); ex=set(bd.race_code); assert len(ex)==94 and bd.race_code.nunique()==94; df=df[~df.race_code.isin(ex)]; df=df[(df.settle__usable=='1')&(df.closing_odds__ok=='1')].copy().reset_index(drop=True); df['month']=df.date.str[:7]; X=base.build_static(df); assert X.shape[1]==63; combo=df.settle__actual_combo.astype(str); n=len(df); pm=np.full(n,np.nan); ps=np.full(n,np.nan); ag=np.full(n,np.nan); sc=np.full((n,len(base.COMBOS)),np.nan)
 def run(tm,sm,seed):
  tr=np.flatnonzero(tm.to_numpy()); te=np.flatnonzero(sm.to_numpy()); a,b,c,d,e=w34b.fit_predict(X.iloc[tr],combo.iloc[tr],X.iloc[te],seed); pm[te]=a; ps[te]=b; ag[te]=c; sc[te]=e
 run(df.month=='2026-02',df.month=='2026-03',3403)
 for i,mo in enumerate(['2026-04','2026-05','2026-06'],1):run(df.month<mo,df.month==mo,3403+i)
 df['prototype_mean']=pm; df['prototype_sd']=ps; df['agreement']=ag
 df['top3']=['' if not np.isfinite(sc[i]).any() else ';'.join(base.COMBOS[j] for j in np.argsort(-np.nan_to_num(sc[i],nan=-1))[:3]) for i in range(n)]
 sel=df[(df.month.isin(['2026-04','2026-05','2026-06']))&(df.prototype_mean>=CUT)&(df.agreement>=AG)].copy(); sel['variant_return']=[base.dutch_return(r,str(r.top3).split(';')) for _,r in sel.iterrows()]; sel['hit']=(sel.variant_return>0).astype(int)
 # attach static features
 XF=X.loc[sel.index].copy(); diag=pd.concat([sel[['race_code','date','month','prototype_mean','prototype_sd','agreement','top3','variant_return','hit']].reset_index(drop=True),XF.reset_index(drop=True)],axis=1); diag.to_csv(OUTC,index=False,encoding='utf-8-sig')
 feats=list(X.columns); ref=diag[diag.month.isin(['2026-04','2026-06'])]; may=diag[diag.month=='2026-05']; shifts=[]
 for c in feats:
  a=pd.to_numeric(ref[c],errors='coerce'); b=pd.to_numeric(may[c],errors='coerce'); pooled=np.nanstd(pd.concat([a,b]).to_numpy(dtype=float)); z=(np.nanmedian(b)-np.nanmedian(a))/(pooled+1e-9); shifts.append((c,float(z),float(np.nanmedian(b)),float(np.nanmedian(a))))
 shifts=sorted(shifts,key=lambda x:abs(x[1]),reverse=True)
 mh=may[may.hit==1]; mm=may[may.hit==0]; clusters=[]
 for c in feats:
  a=pd.to_numeric(mh[c],errors='coerce'); b=pd.to_numeric(mm[c],errors='coerce'); pooled=np.nanstd(pd.concat([a,b]).to_numpy(dtype=float)); z=(np.nanmedian(a)-np.nanmedian(b))/(pooled+1e-9); clusters.append((c,float(z),float(np.nanmedian(a)),float(np.nanmedian(b))))
 clusters=sorted(clusters,key=lambda x:abs(x[1]),reverse=True)
 months={mo:base.block(g) for mo,g in sel.groupby('month')}; proto={mo:{'mean':float(g.prototype_mean.mean()),'sd_mean':float(g.prototype_sd.mean()),'agreement_mean':float(g.agreement.mean()),'hit_rate':float(g.hit.mean())} for mo,g in sel.groupby('month')}
 out={'wave':'34f-may-diagnosis','fixed_gate':{'prototype_mean_cut':CUT,'agreement_cut':AG,'topk':3},'monthly':months,'prototype_summary':proto,'top_feature_shifts_may_vs_aprjun':[{'feature':c,'std_median_shift':z,'may_median':m,'aprjun_median':r} for c,z,m,r in shifts[:15]],'top_may_hit_vs_miss_separators':[{'feature':c,'std_median_diff_hit_minus_miss':z,'hit_median':h,'miss_median':m} for c,z,h,m in clusters[:15]],'note':'Retrospective diagnosis only; May outcomes must not tune future production thresholds.'}; OUTJ.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
 lines=['# Wave34f May failure diagnosis','',f"- fixed Wave34b/c prototype gate: mean>={CUT:.6f}, agreement>={AG}, top3",'','## Monthly']
 for mo,m in months.items(): lines.append(f"- {mo}: {m['races']}R / {m['hits']} hits / ROI {m['roi_pct']:.3f}% / profit {m['profit_yen']:+,}")
 lines+=['','## Prototype summary']
 for mo,p in proto.items(): lines.append(f"- {mo}: mean={p['mean']:.4f}, sd={p['sd_mean']:.4f}, agreement={p['agreement_mean']:.3f}, hit_rate={p['hit_rate']:.3f}")
 lines+=['','## Largest May vs Apr+Jun pre-deadline feature shifts']+[f"- {c}: zmed={z:+.3f} (May {m:.3f} vs Apr+Jun {r:.3f})" for c,z,m,r in shifts[:10]]
 lines+=['','## Largest May hit-vs-miss pre-deadline separators (diagnostic only)']+[f"- {c}: zmed={z:+.3f} (hit {h:.3f} vs miss {m:.3f})" for c,z,h,m in clusters[:10]]
 OUTM.write_text('\n'.join(lines)+'\n'); print('\n'.join(lines))
if __name__=='__main__':main()
