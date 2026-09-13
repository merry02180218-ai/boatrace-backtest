#!/usr/bin/env python3
from pathlib import Path
import json, os
import numpy as np
import pandas as pd
import research_v289_3head_addon as w1

SRC=Path('analysis_v289_3head_wave19_full_universe_payout_enriched.csv')
OUTJ=Path('research_v289_3head_wave19b_full584_walkforward.json')
OUTM=Path('research_v289_3head_wave19b_full584_walkforward.md')
FRACTIONS=(0.02,0.04,0.06,0.08,0.12,0.15)

def num(df,c):
 return pd.to_numeric(df[c],errors='coerce') if c in df.columns else pd.Series(np.nan,index=df.index)

def metric(df):
 if len(df)==0:return {'races':0,'hits':0,'hit_rate_pct':None,'stake_yen':0,'payout_yen':0,'profit_yen':0,'roi_pct':None}
 stake=10000*len(df); payout=float(num(df,'equal20_return_yen').fillna(0).sum()); hits=int((num(df,'head3_actual').fillna(0)>0).sum())
 return {'races':int(len(df)),'hits':hits,'hit_rate_pct':100*hits/len(df),'stake_yen':stake,'payout_yen':payout,'profit_yen':payout-stake,'roi_pct':100*payout/stake}

def maxdd(df):
 if len(df)==0:return 0.0
 pnl=num(df,'equal20_return_yen').fillna(0)-10000
 eq=pnl.cumsum(); peak=eq.cummax().clip(lower=0); return float((peak-eq).max())

def monthly(df):
 by={m:metric(g) for m,g in df.groupby('month')}; rois=[v['roi_pct'] for v in by.values() if v['roi_pct'] is not None]
 return by,(min(rois) if rois else None),sum(r<100 for r in rois)

def feature_weights(tr,cols,target):
 y=num(tr,target).fillna(0); out=[]
 for c in cols:
  x=num(tr,c); ok=x.notna() & y.notna()
  if ok.sum()<80 or x[ok].std(ddof=0)==0: continue
  corr=x[ok].corr(y[ok])
  if pd.notna(corr): out.append((abs(float(corr)),float(corr),c))
 return [(sgn,c) for _,sgn,c in sorted(out,reverse=True)[:32]]

def score(tr,te,weights):
 if not weights:return pd.Series(np.nan,index=te.index),pd.Series(False,index=te.index)
 cols=[c for _,c in weights]; valid=te[cols].apply(pd.to_numeric,errors='coerce').notna().all(axis=1)
 s=pd.Series(np.nan,index=te.index,dtype=float)
 for sign,c in weights:
  mu=num(tr,c).mean(); sd=num(tr,c).std(ddof=0)
  if not pd.notna(sd) or sd<=0: continue
  s.loc[valid]=s.loc[valid].fillna(0)+np.sign(sign)*(num(te.loc[valid],c)-mu)/sd
 return s/len(weights),valid

def main():
 q=pd.read_csv(SRC,dtype={'race_code':str}); q['date']=q.date.astype(str); q['month']=q.date.str[:7]
 if q.date.max()>'2026-08-31': raise RuntimeError('September outcomes forbidden')
 # Rebuild unchanged v288 baseline solely to exclude overlap and retain floor.
 q['_target']=w1.v243_target(q).astype(int)
 replay,_=w1.replay_operational_pre(q); w1.add_v288_route(replay)
 oldpre=replay[replay.grade.isin(['S','A'])].copy(); baseline=oldpre[oldpre.route!='NO_BET'].copy()
 if len(baseline)!=94: raise RuntimeError(f'baseline drift {len(baseline)}')
 basecodes=set(baseline.race_code.astype(str)); universe=q[~q.race_code.astype(str).isin(basecodes)].drop_duplicates('race_code').copy()
 if len(universe)!=584: raise RuntimeError(f'full universe drift {len(universe)}')
 # transparent equal-20 ticket settlement: 20 combos x 500 yen; winning 3-head combo returns official payout *5
 if 'trifecta_payout_yen' not in universe.columns: raise RuntimeError('missing payout')
 universe['equal20_return_yen']=np.where(num(universe,'head3_actual').fillna(0)>0,num(universe,'trifecta_payout_yen').fillna(0)*5,0)
 allcols=w1.safe_live_cols(universe); livecols=w1.current_exhibition_cols(allcols)
 months=sorted(universe.month.unique()); picks={f:[] for f in FRACTIONS}; audit={}
 for m in months:
  tr=universe[universe.month<m].copy(); te=universe[universe.month==m].copy()
  if len(tr)<100 or te.empty: continue
  hitw=feature_weights(tr,allcols,'head3_actual'); val=tr.copy(); val['_value_target']=num(val,'equal20_return_yen').fillna(0)/10000; valw=feature_weights(val,allcols,'_value_target')
  livew=feature_weights(tr,livecols,'head3_actual')
  sh,vh=score(tr,te,hitw); sv,vv=score(val,te,valw); sl,vl=score(tr,te,livew)
  valid=vh&vv&vl; sc=(sh+sv+sl)/3
  trh,_=score(tr,tr,hitw); trv,_=score(val,tr,valw); trl,_=score(tr,tr,livew); trsc=(trh+trv+trl)/3
  audit[m]={'train':len(tr),'test':len(te),'valid':int(valid.sum()),'hit_features':len(hitw),'value_features':len(valw),'live_features':len(livew)}
  for f in FRACTIONS:
   thr=float(trsc.quantile(1-f)); picks[f].append(te.loc[valid & (sc>=thr)].copy())
 rows=[]
 for f,parts in picks.items():
  g=pd.concat(parts,ignore_index=True) if parts else universe.iloc[:0].copy(); g=g.drop_duplicates('race_code'); overlap=len(set(g.race_code.astype(str))&basecodes)
  a=metric(g); a['max_drawdown_yen']=maxdd(g); by,mn,red=monthly(g)
  # combined uses immutable published baseline payout, plus transparent addon settlement
  combined_r=94+a['races']; combined_stake=940000+a['stake_yen']; combined_payout=1622070+a['payout_yen']; combined_roi=100*combined_payout/combined_stake
  rows.append({'fraction':f,'addon':a,'monthly':by,'min_monthly_roi_pct':mn,'red_months':red,'overlap_with_v288':overlap,'combined':{'races':combined_r,'stake_yen':combined_stake,'payout_yen':combined_payout,'roi_pct':combined_roi}})
 rows.sort(key=lambda x:((x['addon']['roi_pct'] or -1),x['addon']['races']),reverse=True)
 passers=[x for x in rows if x['addon']['races']>=20 and (x['addon']['roi_pct'] or 0)>=100 and (x['min_monthly_roi_pct'] or 0)>=60 and x['red_months']<=3 and x['overlap_with_v288']==0]
 decision='SHADOW_CANDIDATE_WAVE19B' if passers else 'NO_ADOPTION_WAVE19B'
 out={'run_id':os.getenv('GITHUB_RUN_ID'),'source_max_date':q.date.max(),'universe_races':len(universe),'baseline_races':94,'rules':{'candidate_universe':'full 584R non-baseline','september_outcomes_used':False,'july_august':'NON-PRISTINE','predeadline_only':True,'required_current_missing':'FAIL_CLOSED','stake_per_race_yen':10000,'ticket_benchmark':'3-head all 20 combos x 500 yen'},'methods':rows,'passers':passers,'decision':decision,'audit':audit}
 OUTJ.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 L=['# 3号艇 Wave19b — full 584R walk-forward','',f'- research universe: **{len(universe)}R**','- ticket benchmark: **3頭20通り × 500円 = 10,000円/R**','', '|frac|add R|hits|ROI|profit|min month|red|max DD|combined R|combined ROI|','|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
 for x in rows:
  a=x['addon']; c=x['combined']; mn=x['min_monthly_roi_pct'];L.append(f"|{x['fraction']:.2f}|{a['races']}|{a['hits']}|{a['roi_pct']:.2f}%|{a['profit_yen']:+,.0f}|{mn if mn is not None else float('nan'):.2f}%|{x['red_months']}|{a['max_drawdown_yen']:,.0f}|{c['races']}|{c['roi_pct']:.2f}%|")
 L+=['','## Decision',f'**{decision}**']; OUTM.write_text('\n'.join(L)+'\n',encoding='utf-8'); print('\n'.join(L))
if __name__=='__main__': main()
