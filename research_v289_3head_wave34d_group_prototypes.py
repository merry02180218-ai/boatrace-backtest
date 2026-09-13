from __future__ import annotations
import json,re
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
import research_v289_3head_wave31_nonlinear_gate as base
import research_v289_3head_wave34b_prototype_stability as w34b
SRC=Path('analysis_v289_3head_wave21_allrace_feature_settled.csv'); B=Path('v288_operational_pre_replay_94_baseline_codes.csv')
OUT=Path('analysis_v289_3head_wave34d_group_prototypes.csv'); OUTJ=Path('research_v289_3head_wave34d_group_prototypes.json'); OUTM=Path('research_v289_3head_wave34d_group_prototypes.md')
BASE={'races':94,'hits':52,'stake_yen':940000,'payout_yen':1622070,'roi_pct':172.560638}; KS=[3,5,7]

def groups(cols):
 g={
  'global':list(cols),
  'boat3_abs':[c for c in cols if c.startswith('b3_') and not c.startswith('b3_minus_')],
  'mean_advantage':[c for c in cols if c.startswith('b3_minus_mean_')],
  'inner12':[c for c in cols if c.startswith('b3_minus_b1_') or c.startswith('b3_minus_b2_')],
  'outer456':[c for c in cols if c.startswith('b3_minus_b4_') or c.startswith('b3_minus_b5_') or c.startswith('b3_minus_b6_')],
 }
 expected={'global':63,'boat3_abs':9,'mean_advantage':9,'inner12':18,'outer456':27}
 got={k:len(v) for k,v in g.items()}
 if got!=expected: raise RuntimeError(f'group layout mismatch: {got} expected {expected}')
 return g

def proto(A,y,B,idx):
 imp=SimpleImputer(strategy='median'); a=imp.fit_transform(A[:,idx]); b=imp.transform(B[:,idx]); sc=StandardScaler().fit(a); a=sc.transform(a); b=sc.transform(b)
 p=a[y==1].mean(0); n=a[y==0].mean(0); return np.sqrt(((b-n)**2).mean(1))-np.sqrt(((b-p)**2).mean(1))
def ev(q,k):
 q=q.copy(); q['variant_return']=[base.dutch_return(r,str(r[f'top{k}']).split(';')) for _,r in q.iterrows()]; m=base.block(q); mm={mo:base.block(g) for mo,g in q.groupby('month')}; m.update(monthly=mm,min_month_roi_pct=min((z['roi_pct'] for z in mm.values()),default=None),red_months=sum(z['roi_pct']<100 for z in mm.values()),max_drawdown_yen=base.maxdd(q.sort_values(['date','race_code']))); return q,m
def main():
 df=pd.read_csv(SRC,dtype=str).fillna(''); assert df.date.max()<='2026-08-31'; bd=pd.read_csv(B,dtype=str).fillna(''); ex=set(bd.race_code); assert len(ex)==94 and bd.route.value_counts().to_dict()=={'S':55,'A':21,'B':18}
 df=df[~df.race_code.isin(ex)]; df=df[(df.settle__usable=='1')&(df.closing_odds__ok=='1')].copy().reset_index(drop=True); df['month']=df.date.str[:7]
 X=base.build_static(df); assert X.shape[1]==63; G=groups(list(X.columns)); pos={c:i for i,c in enumerate(X.columns)}; gi={k:[pos[c] for c in v] for k,v in G.items()}; y=df.settle__actual_combo.str.startswith('3-').astype(int).to_numpy(); combo=df.settle__actual_combo.astype(str); n=len(df); gs={k:np.full(n,np.nan) for k in G}; scores=np.full((n,len(base.COMBOS)),np.nan)
 def run(tm,sm,seed):
  tr=np.flatnonzero(tm.to_numpy()); te=np.flatnonzero(sm.to_numpy()); imp=SimpleImputer(strategy='median'); A=imp.fit_transform(X.iloc[tr]); C=imp.transform(X.iloc[te])
  for k,idx in gi.items():gs[k][te]=proto(A,y[tr],C,idx)
  _,_,_,_,e=w34b.fit_predict(X.iloc[tr],combo.iloc[tr],X.iloc[te],seed); scores[te]=e
 run(df.month=='2026-02',df.month=='2026-03',3440)
 for i,mo in enumerate(['2026-04','2026-05','2026-06'],1):run(df.month<mo,df.month==mo,3440+i)
 frozen=df.month<='2026-06'
 for i,mo in enumerate(['2026-07','2026-08'],4):run(frozen,df.month==mo,3440+i)
 for k,v in gs.items():df['g_'+k]=v
 for K in KS:df[f'top{K}']=['' if not np.isfinite(scores[i]).any() else ';'.join(base.COMBOS[j] for j in np.argsort(-np.nan_to_num(scores[i],nan=-1))[:K]) for i in range(n)]
 march=df[df.month=='2026-03'].copy(); cuts={k:[float(march['g_'+k].quantile(q)) for q in [.85,.90,.93,.95,.97]] for k in G}; cand=[]
 for primary in G:
  for cut in cuts[primary]:
   for need in [1,2,3]:
    for K in KS:
     flags=np.column_stack([(march['g_'+k]>=march['g_'+k].quantile(.75)).to_numpy() for k in G]); q=march[(march['g_'+primary]>=cut)&(flags.sum(1)>=min(need,len(G)))]; _,m=ev(q,K)
     if 30<=m['races']<=300:m.update(primary=primary,cut=cut,consensus=need,k=K);cand.append(m)
 if not cand:raise RuntimeError('no March candidates')
 ch=max(cand,key=lambda z:(z['roi_pct'],-z['races'])); primary=ch['primary']; cut=ch['cut']; need=ch['consensus']; K=ch['k']; q75={k:float(march['g_'+k].quantile(.75)) for k in G}
 def select(ms):
  q=df[df.month.isin(ms)].copy(); flags=np.column_stack([(q['g_'+k]>=q75[k]).to_numpy() for k in G]); return q[(q['g_'+primary]>=cut)&(flags.sum(1)>=min(need,len(G)))]
 sh,hm=ev(select(['2026-04','2026-05','2026-06']),K); ss,sm=ev(select(['2026-07','2026-08']),K); assert not pd.concat([sh,ss]).race_code.isin(ex).any(); pd.concat([sh.assign(period='holdout'),ss.assign(period='shadow')]).to_csv(OUT,index=False,encoding='utf-8-sig')
 cmb={'races':94+hm['races'],'stake_yen':940000+hm['stake_yen'],'payout_yen':1622070+hm['payout_yen']}; cmb['profit_yen']=cmb['payout_yen']-cmb['stake_yen']; cmb['roi_pct']=100*cmb['payout_yen']/cmb['stake_yen']; dec='RESEARCH_CANDIDATE' if hm['races']>=30 and hm['roi_pct']>=110 and hm['red_months']<=1 else 'NO_ADOPTION'
 out={'wave':'34d-group-prototypes','groups':{k:len(v) for k,v in G.items()},'march_selection':ch,'holdout':hm,'shadow':sm,'combined':cmb,'overlap':0,'decision':dec}; OUTJ.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
 lines=['# Wave34d grouped prototypes','',f"- groups: {out['groups']}",f"- March: {ch['races']}R / ROI {ch['roi_pct']:.3f}% / primary {primary} / consensus {need} / top{K}",f"- Apr-Jun: {hm['races']}R / {hm['hits']} hits / ROI {hm['roi_pct']:.3f}% / profit {hm['profit_yen']:+,} yen",f"- min month {hm['min_month_roi_pct']:.3f}% / red {hm['red_months']} / DD {hm['max_drawdown_yen']:,.0f}",f"- Jul-Aug shadow ROI {sm['roi_pct']:.3f}%",f"- combined ROI {cmb['roi_pct']:.3f}% / profit {cmb['profit_yen']:+,}",f"- decision {dec}",'','## Monthly']+[f"- {mo}: {z['races']}R / ROI {z['roi_pct']:.3f}% / profit {z['profit_yen']:+,}" for mo,z in hm['monthly'].items()]; OUTM.write_text('\n'.join(lines)+'\n'); print('\n'.join(lines))
if __name__=='__main__':main()
