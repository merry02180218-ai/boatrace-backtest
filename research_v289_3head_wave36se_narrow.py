from pathlib import Path
import json,numpy as np,pandas as pd
import research_v289_3head_wave36sc_motor_robustness as sc
import research_v289_3head_wave31_nonlinear_gate as base
SRC=Path('analysis_v289_3head_wave21_allrace_feature_settled.csv');BC=Path('v288_operational_pre_replay_94_baseline_codes.csv');OUT=Path('research_v289_3head_wave36se_narrow.json')

def main():
 d=pd.read_csv(SRC,dtype=str).fillna('');
 if d.date.max()>'2026-08-31':raise RuntimeError('September forbidden')
 ex=set(pd.read_csv(BC,dtype=str).race_code.astype(str));d=d[~d.race_code.astype(str).isin(ex)].copy();d=d[(d.settle__usable=='1')&(d.closing_odds__ok=='1')].reset_index(drop=True);d['month']=d.date.str[:7];d['actual']=d.settle__actual_combo.astype(str);d['actual3']=d.actual.str.startswith('3-').astype(int);X=base.build_static(d);y=d.actual
 feb=d.month=='2026-02';mar=d.month=='2026-03';march=sc.predict_block(d,X,y,feb,mar);mc=sc.fit_cal(march);march['cal_p3']=sc.apply_cal(march,mc);cal_cut=float(1/(1+np.exp(-(float(mc.coef_[0][0])*sc.RAW_CUT+float(mc.intercept_[0])))))
 racer_cols=[c for c in X.columns if c.startswith('b3_minus_') and any(k in c for k in ['全国勝率','全国2連対率','全国3連対率','当地勝率','当地2連対率','当地3連対率'])];motor_cols=[c for c in X.columns if c.startswith('b3_minus_') and any(k in c for k in ['モーター2連対率','モーター3連対率'])]
 rz=[];mz=[]
 for c in racer_cols:
  z,_,_=sc.zfit(pd.to_numeric(X[c],errors='coerce').fillna(pd.to_numeric(X.loc[feb,c],errors='coerce').median()),pd.to_numeric(X.loc[feb,c],errors='coerce').dropna());rz.append(z)
 for c in motor_cols:
  z,_,_=sc.zfit(pd.to_numeric(X[c],errors='coerce').fillna(pd.to_numeric(X.loc[feb,c],errors='coerce').median()),pd.to_numeric(X.loc[feb,c],errors='coerce').dropna());mz.append(z)
 d['racer_adv']=pd.concat(rz,axis=1).mean(axis=1);d['motor_adv']=pd.concat(mz,axis=1).mean(axis=1);march['racer_adv']=d.loc[march.index,'racer_adv'];march['motor_adv']=d.loc[march.index,'motor_adv']
 rcut=float(d.loc[feb,'racer_adv'].quantile(.5));mcut=float(d.loc[feb,'motor_adv'].quantile(.5));march['mod_p3']=march.cal_p3-.08*((march.racer_adv>=rcut)&(march.motor_adv<=mcut)).astype(float);ms=march[march.mod_p3>=cal_cut].copy()
 # Narrowing gates are frozen from March only. Use confidence margin quantiles; no payout/ROI is used for selection.
 margins=ms.mod_p3-cal_cut
 candidates=[]
 for keep in [1.0,.80,.65,.50,.40,.33]:
  margin_cut=float(margins.quantile(max(0,1-keep))) if keep<1 else 0.0;sel=ms[(ms.mod_p3-cal_cut)>=margin_cut];candidates.append({'target_keep':keep,'margin_cut':margin_cut,'march_races':len(sel),'march_head_rate':float(sel.actual3.mean()) if len(sel) else 0})
 # Prefer improved March head rate; tie -> larger sample. Require >= one third of baseline selected March volume.
 viable=[c for c in candidates if c['march_races']>=max(20,int(len(ms)/3))];best=sorted(viable,key=lambda c:(c['march_head_rate'],c['march_races']),reverse=True)[0]
 oos={'2026-03':march};chosen=[];scbase=[]
 for mo in ['2026-04','2026-05','2026-06','2026-07','2026-08']:
  q=sc.predict_block(d,X,y,d.month<mo,d.month==mo);prior=sorted(oos.keys())[-3:];pool=pd.concat([oos[p] for p in prior],ignore_index=True);c=sc.fit_cal(pool);q['cal_p3']=sc.apply_cal(q,c);q['racer_adv']=d.loc[q.index,'racer_adv'];q['motor_adv']=d.loc[q.index,'motor_adv'];q['mod_p3']=q.cal_p3-.08*((q.racer_adv>=rcut)&(q.motor_adv<=mcut)).astype(float);b=q[q.mod_p3>=cal_cut].copy();scbase.append(b);chosen.append(b[(b.mod_p3-cal_cut)>=best['margin_cut']].copy());oos[mo]=q
 cd=pd.concat(chosen,ignore_index=True);bd=pd.concat(scbase,ignore_index=True);pr=['2026-04','2026-05','2026-06'];sh=['2026-07','2026-08']
 def agg(z,ms):return sc.metrics(z[z.month.isin(ms)])
 out={'wave':'36S-E-narrow','selection_basis':'March OOS head rate only; no payout/ROI','cal_cut':cal_cut,'march_sc_races':len(ms),'candidates':candidates,'chosen':best,'monthly':{mo:sc.metrics(g) for mo,g in cd.groupby('month')},'apr_jun':agg(cd,pr),'jul_aug_non_pristine':agg(cd,sh),'wave36sc_apr_jun':agg(bd,pr),'v288_overlap':int(cd.race_code.astype(str).isin(ex).sum()),'september_forbidden':True}
 if out['v288_overlap']:raise RuntimeError('v288 overlap')
 OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
