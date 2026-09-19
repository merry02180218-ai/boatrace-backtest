#!/usr/bin/env python3
"""Descriptive loss-pattern diagnostics for adopted 3HEAD A + purchase gate.
March is evaluation/diagnosis only. This script MUST NOT tune A or purchase .60.
September 2026 outcomes are not read.
"""
from pathlib import Path
import json, pandas as pd, numpy as np

ROOT=Path(__file__).resolve().parents[1]
DETAIL=ROOT/'research_3head_a_purchase_gate_march_detail.csv'
OUT=ROOT/'analysis_3head_a_adopted_loss_patterns.csv'
SUM=ROOT/'summary_3head_a_adopted_loss_patterns.md'

def rate(g):
    return {'R':len(g),'H':int(g.head3_actual.sum()),'head_rate':float(g.head3_actual.mean()) if len(g) else None}

def main():
    if not DETAIL.exists(): raise RuntimeError(f'missing {DETAIL}')
    z=pd.read_csv(DETAIL,dtype={'race_code':str})
    z['race_code']=z.race_code.astype(str).str.zfill(12)
    if z.race_code.str.startswith('202609').any(): raise RuntimeError('SEPTEMBER ACCESS')
    z=z[(z.purchase_gate_pass==True)|(z.purchase_gate_pass.astype(str).str.lower()=='true')].copy()
    if len(z)!=33: raise RuntimeError(f'adopted March BET drift {len(z)} != 33')
    z['head3_actual']=pd.to_numeric(z.head3_actual,errors='coerce').fillna(0).astype(int)
    z['winner']=z.actual_combo.astype(str).str.split('-').str[0]
    z['jcd']=z.race_code.str[8:10].astype(int)
    z['race_no']=z.race_code.str[10:12].astype(int)
    rows=[]
    def add(fam,label,g):
        q=rate(g);rows.append({'family':fam,'segment':label,**q})
    add('ALL','BET33',z)
    add('RESULT','HEAD3',z[z.head3_actual==1]);add('RESULT','LOSS',z[z.head3_actual==0])
    for w,g in z[z.head3_actual==0].groupby('winner'): add('LOSS_WINNER',f'winner_{w}',g)
    for j,g in z.groupby('jcd'):
        if len(g)>=2:add('VENUE',f'jcd_{j:02d}',g)
    for c in ['purchase_gate_value']:
        if c in z:
            q=pd.to_numeric(z[c],errors='coerce')
            for lo,hi in [(0.60,0.80),(0.80,1.00),(1.00,1.50),(1.50,np.inf)]:
                g=z[(q>=lo)&(q<hi)]; 
                if len(g):add('GATE_BAND',f'{c}_{lo:.2f}_{hi if np.isfinite(hi) else "inf"}',g)
    out=pd.DataFrame(rows)
    out.to_csv(OUT,index=False)
    losses=z[z.head3_actual==0].copy()
    losses.to_csv(ROOT/'analysis_3head_a_adopted_losses17.csv',index=False)
    L=['# Adopted 3HEAD loss-pattern diagnosis','',
       '- Frozen head gate and purchase >=0.60 are NOT retuned here.',
       '- March is descriptive diagnosis only; any new filter requires development-side derivation + new forward validation.',
       '- September 2026 outcomes used: false','',
       f'- BET: {len(z)} / HEAD3: {int(z.head3_actual.sum())} / LOSS: {int((z.head3_actual==0).sum())}','',
       '## Segments',out.to_markdown(index=False),'',
       '## 17 losses',losses[['race_code','actual_combo','winner','purchase_gate_value']].to_markdown(index=False)]
    SUM.write_text('\n'.join(L)+'\n',encoding='utf-8')
    print('\n'.join(L))
if __name__=='__main__':main()
