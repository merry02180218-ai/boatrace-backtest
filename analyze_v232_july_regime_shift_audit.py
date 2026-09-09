#!/usr/bin/env python3
"""v232: June->July regime-shift audit for the frozen v224 head feature family.
Audit only: no rule/threshold discovery. Jul/Aug remain NON-PRISTINE.
Builds the same feature pipeline used by v229 extension and compares selected v224-like
races across May, June, July, August. Reports head calibration and standardized feature shifts.
"""
from pathlib import Path
import numpy as np, pandas as pd
import analyze_v165_3head_monthly_walkforward as v165
import analyze_v221_3head_scenario_pair as v221
import analyze_v222_3head_broad_feature_audit as v222
import analyze_v223_3head_unused_feature_audit as v223
import analyze_v224_3head_national_form_decompose as v224
import analyze_v229_3head_jul_aug_shadow as v229

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'analysis_v232_july_regime_shift_features.csv'; SEL=ROOT/'analysis_v232_july_regime_shift_selected.csv'; SUM=ROOT/'summary_v232_july_regime_shift_audit.md'
MONTHS=['2026-05','2026-06','2026-07','2026-08']

def main():
 # use v229's extended builder so Jul/Aug are actually constructed
 raw=pd.read_csv(v224.SRC,dtype={'race_code':str}); dc=v165.pc(raw,['date','race_date','ymd']); vc=v165.pc(raw,['venue','jcd','stadium','place']); y,_=v165.target(raw); basefs=v165.feats(raw)
 raw['_date']=pd.to_datetime(raw[dc].astype(str),errors='coerce'); raw['_y']=y; raw=raw[raw._date.notna()&raw._y.notna()&(raw._date<pd.Timestamp('2026-09-01'))].copy()
 # locally extend frozen builders, as audited/fixed in v229
 endts=pd.Timestamp('2026-09-01'); v221.CONTAM=endts; v221.END=pd.Timestamp('2026-08-31').date(); v222.CONTAM=endts; v222.END=pd.Timestamp('2026-08-31').date(); v223.CONTAM=endts; v224.CONTAM=endts
 d=v221.build(raw,dc); d=v222.build_current(d,dc); d=v223.build_unused(d,dc); d=v224.add_decomp(d,dc)
 hist=v222.cols(d,'b3_vh_'); rel=[c for c in d.columns if c.startswith(('c_b3_minus_','c_b3_inside_','c_b3_outside_'))]; cur=[c for c in v222.cols(d,'c_b3_') if not c.startswith(('c_b3_minus_','c_b3_inside_','c_b3_outside_'))]; cur += [c for c in d.columns if c.startswith(('c_wall','c_attack3','c_outer','c_ex_spread','c_st_spread','c_turn_spread','c_straight_spread'))]
 best=v223.uniq(list(basefs)+hist+cur+rel); fs=v223.uniq(best+[c for c in d.columns if c.startswith(('f_b3_m1_','f_b3_m12_','f_b3_m35_','f_b3_trend_','f_rel_'))]+['f_b3_layoff','f_b3_grade','f_b3_m1_grade'])
 selected=[]
 for mon in MONTHS:
  first=pd.Timestamp(mon+'-01'); nextm=first+pd.offsets.MonthBegin(1)
  base_te,_=v223.fit_head(d,list(basefs),vc,first,nextm); k=max(1,int((base_te._p>=.30).sum()))
  te,_=v223.fit_head(d,fs,vc,first,nextm); s=te.nlargest(k,'_p').copy(); s['_month']=mon; selected.append(s)
 s=pd.concat(selected,ignore_index=True); keep=['_month','_date','race_code','_p','_y']+[c for c in fs if c in s.columns]; s[keep].to_csv(SEL,index=False)
 # standardized June->July shift, using pooled Jun/Jul SD. Include May/Aug means for context.
 rec=[]
 for c in fs:
  x=pd.to_numeric(s[c],errors='coerce'); g={m:x[s._month==m].dropna() for m in MONTHS}
  if len(g['2026-06'])<10 or len(g['2026-07'])<10: continue
  pool=pd.concat([g['2026-06'],g['2026-07']]); sd=float(pool.std(ddof=1)); delta=float(g['2026-07'].mean()-g['2026-06'].mean()); z=delta/sd if sd>1e-12 else np.nan
  rec.append({'feature':c,'may_mean':g['2026-05'].mean(),'jun_mean':g['2026-06'].mean(),'jul_mean':g['2026-07'].mean(),'aug_mean':g['2026-08'].mean(),'jun_jul_delta':delta,'jun_jul_std_shift':z,'jun_n':len(g['2026-06']),'jul_n':len(g['2026-07'])})
 f=pd.DataFrame(rec); f['abs_shift']=f.jun_jul_std_shift.abs(); f=f.sort_values('abs_shift',ascending=False); f.to_csv(OUT,index=False)
 L=['# v232 June→July regime-shift audit','', '- frozen v224 head feature family; no tuning or rule discovery', '- May/Jun are historical audit context; Jul/Aug are NON-PRISTINE shadow only','', '## Selected-race head calibration','|month|R|avg p3|actual 3-head|gap pp|','|---|---:|---:|---:|---:|']
 for mon,g in s.groupby('_month',sort=True): L.append(f'|{mon}|{len(g)}|{100*g._p.mean():.2f}%|{100*g._y.mean():.2f}%|{100*(g._p.mean()-g._y.mean()):+.2f}|')
 L += ['', '## Largest June→July feature distribution shifts','|feature|Jun mean|Jul mean|std shift|','|---|---:|---:|---:|']
 for _,r in f.head(30).iterrows(): L.append(f"|{r.feature}|{r.jun_mean:.5g}|{r.jul_mean:.5g}|{r.jun_jul_std_shift:+.3f}|")
 # family summary: max and median abs standardized shift
 fam={'national_form':'f_b3_','relative_form':'f_rel_','player_history':'b3_vh_','current_state':'c_'}
 L += ['', '## Feature-family shift summary','|family|features|median abs shift|max abs shift|','|---|---:|---:|---:|']
 for name,prefix in fam.items():
  q=f[f.feature.str.startswith(prefix)]
  if len(q): L.append(f'|{name}|{len(q)}|{q.abs_shift.median():.3f}|{q.abs_shift.max():.3f}|')
 SUM.write_text('\n'.join(L)+'\n',encoding='utf-8'); print('\n'.join(L))
if __name__=='__main__': main()
