from pathlib import Path
import json,numpy as np,pandas as pd
import research_v289_3head_wave31_nonlinear_gate as base
import research_v289_3head_wave36s_smooth_calibration as s
SRC=Path('analysis_v289_3head_wave21_allrace_feature_settled.csv');BC=Path('v288_operational_pre_replay_94_baseline_codes.csv');OUT=Path('research_v289_3head_wave36sa_audit.json')
def enrich(q):
 x=q.copy();x['ret']=[base.dutch_return(r,str(r.top5).split(';')) for _,r in x.iterrows()];x['profit']=x.ret-10000;return x
def met(x):
 if not len(x):return {'races':0,'hits':0,'roi_pct':0,'profit_yen':0,'head_rate':0,'conversion':0}
 z=enrich(x);hh=int(z.actual3.sum());hits=int((z.ret>0).sum());return {'races':len(z),'hits':hits,'roi_pct':float(z.ret.sum()/len(z)/100),'profit_yen':int(z.profit.sum()),'head_hits':hh,'head_rate':hh/len(z),'conversion':hits/hh if hh else 0,'max_drawdown_yen':float(base.maxdd(z.sort_values(['date','race_code'])))}
def concentration(x):
 z=enrich(x);wins=z[z.ret>0].sort_values('ret',ascending=False);tot=float(z.ret.sum());out={'winning_races':len(wins),'median_win_return_yen':float(wins.ret.median()) if len(wins) else 0}
 for n in [1,3,5]:
  share=float(wins.head(n).ret.sum()/tot) if tot else 0;left=z.drop(wins.head(n).index);out[f'top{n}_payout_share']=share;out[f'roi_without_top{n}_wins']=float(left.ret.sum()/len(z)/100);out[f'profit_without_top{n}_wins_yen']=int(left.ret.sum()-len(z)*10000)
 return out
def main():
 d=pd.read_csv(SRC,dtype=str).fillna('');
 if d.date.max()>'2026-08-31':raise RuntimeError('September forbidden')
 ex=set(pd.read_csv(BC,dtype=str).race_code.astype(str));d=d[~d.race_code.astype(str).isin(ex)].copy();d=d[(d.settle__usable=='1')&(d.closing_odds__ok=='1')].reset_index(drop=True);d['month']=d.date.str[:7];d['actual']=d.settle__actual_combo.astype(str);d['actual3']=d.actual.str.startswith('3-').astype(int);X=base.build_static(d);y=d.actual
 if X.shape[1]!=63:raise RuntimeError('feature guard')
 march=s.predict_block(d,X,y,d.month=='2026-02',d.month=='2026-03');mc=s.fit_cal(march);mcoef=float(mc.coef_[0][0]);mint=float(mc.intercept_[0]);cut=float(s.apply_params(pd.DataFrame({'raw_p3':[s.RAW_CUT]}),mcoef,mint)[0]);oos={'2026-03':march};roll=[];raw=[]
 for mo in ['2026-04','2026-05','2026-06','2026-07','2026-08']:
  q=s.predict_block(d,X,y,d.month<mo,d.month==mo);prior=sorted(oos)[-3:];c=s.fit_cal(pd.concat([oos[p] for p in prior],ignore_index=True));q['roll_p3']=s.apply_params(q,float(c.coef_[0][0]),float(c.intercept_[0]));roll.append(q[q.roll_p3>=cut].copy());raw.append(q[q.raw_p3>=s.RAW_CUT].copy());oos[mo]=q
 rd=pd.concat(roll);rw=pd.concat(raw);delta={}
 for mo in sorted(rd.month.unique()):
  a=rd[rd.month==mo];b=rw[rw.month==mo];ak=set(a.race_code);bk=set(b.race_code);delta[mo]={'kept':met(a[a.race_code.isin(bk)]),'removed_from_raw':met(b[~b.race_code.isin(ak)]),'added_by_roll':met(a[~a.race_code.isin(bk)])}
 def halves(x,months):
  z=x[x.month.isin(months)].sort_values(['date','race_code']);mid=len(z)//2;return {'first_half':met(z.iloc[:mid]),'second_half':met(z.iloc[mid:])}
 out={'wave':'36S-A-audit','rules_unchanged':True,'delta_by_month':delta,'apr_jun':met(rd[rd.month.isin(['2026-04','2026-05','2026-06'])]),'jul_aug_nonpristine':met(rd[rd.month.isin(['2026-07','2026-08'])]),'concentration_apr_jun':concentration(rd[rd.month.isin(['2026-04','2026-05','2026-06'])]),'concentration_by_month':{m:concentration(g) for m,g in rd.groupby('month')},'stability_apr_jun':halves(rd,['2026-04','2026-05','2026-06']),'stability_jul_aug':halves(rd,['2026-07','2026-08']),'feature_count':X.shape[1],'v288_overlap':int(rd.race_code.astype(str).isin(ex).sum()),'september_forbidden':True}
 if out['v288_overlap']:raise RuntimeError('v288 overlap')
 OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
