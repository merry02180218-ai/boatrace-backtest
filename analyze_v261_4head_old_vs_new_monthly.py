#!/usr/bin/env python3
"""v261: compare old 4-corner candidate head rate with current v250 gate monthly.
Research audit only. Jul/Aug non-pristine.
"""
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parent
NEW=ROOT/'analysis_v250_4head_rebuild_baseline.csv'
OUT=ROOT/'summary_v261_4head_old_vs_new_monthly.md'

def new_rows():
 p=pd.read_csv(NEW,dtype={'race_code':str}); p.race_code=p.race_code.str.zfill(12)
 w=p.pivot_table(index=['date','month','race_code'],columns='variant',values=['p4head','y4head'],aggfunc='last')
 w.columns=['_'.join(x) for x in w.columns]; w=w.reset_index()
 # y is same label across variants; use PRE copy.
 q=w[(w.p4head_PRE>=.28)&(w.p4head_POST>=.25)].copy()
 q['head4']=q.y4head_PRE
 return q.groupby('month').agg(R=('race_code','size'),head4=('head4','sum')).reset_index()

def old_rows():
 # Prefer legacy v20/v18 result artifacts if present. Accept common candidate columns.
 candidates=[ROOT/'analysis_v20_week.csv',ROOT/'analysis_v18_core45.csv',ROOT/'analysis_v34_tilt_compare.csv',ROOT/'analysis_v35_tilt_interaction.csv']
 for f in candidates:
  if not f.exists(): continue
  d=pd.read_csv(f,dtype={'race_code':str})
  cols=set(d.columns)
  # Only use a file when it exposes race-level candidate and winner/head label.
  cand=next((c for c in ['bet','candidate','selected','is_candidate','pick'] if c in cols),None)
  head=next((c for c in ['head4','y4head','winner4','hit_head','win4'] if c in cols),None)
  month='month' if 'month' in cols else None
  if cand and head and month:
   q=d[pd.to_numeric(d[cand],errors='coerce').fillna(0)>0].copy()
   return f.name,q.groupby(month).agg(R=(cand,'size'),head4=(head,'sum')).reset_index()
 return None,None

def main():
 n=new_rows(); name,o=old_rows()
 L=['# v261 old vs new 4-head monthly head-rate comparison','', '- Current: v250 PRE>=0.28 / POST>=0.25.','- Jul/Aug are NON-PRISTINE.','']
 if o is None:
  L += ['## Legacy comparison','Legacy race-level output with an explicit candidate flag and 4-head label was not found in the checked legacy CSVs; no legacy rates are invented.','']
 else:
  L += [f'## Legacy source: {name}','|month|R|4-head|head rate|','|---|---:|---:|---:|']
  for _,r in o.iterrows(): L.append(f'|{r.iloc[0]}|{int(r.R)}|{int(r.head4)}|{100*r.head4/r.R:.2f}%|')
  L.append('')
 L += ['## Current v250 gate','|month|R|4-head|head rate|','|---|---:|---:|---:|']
 for _,r in n.iterrows(): L.append(f'|{r.month}|{int(r.R)}|{int(r.head4)}|{100*r.head4/r.R:.2f}%|')
 L += ['',f'Feb-Jun total: {int(n[n.month<="2026-06"].R.sum())} R / {int(n[n.month<="2026-06"].head4.sum())} heads / {100*n[n.month<="2026-06"].head4.sum()/n[n.month<="2026-06"].R.sum():.2f}%']
 OUT.write_text('\n'.join(L)+'\n',encoding='utf-8'); print('\n'.join(L))
if __name__=='__main__': main()
