from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
import research_v289_3head_wave47_head_condition_zoning as w47
import research_v289_3head_wave31_nonlinear_gate as base

SRC=Path('analysis_v289_3head_wave21_allrace_feature_settled.csv')
BASE=Path('v288_operational_pre_replay_94_baseline_codes.csv')
OUT=Path('research_v289_3head_wave50_motor_edge_regimes.json')
CUT=.365448

def num(s): return pd.to_numeric(s.astype(str).str.replace('%','',regex=False),errors='coerce')
def col(d,b,m): return num(d[f'card__艇{b}_{m}'])
def summarize(q):
    n=len(q); h=int(q['head3'].sum()); t=int(q['top5_hit'].sum()); cap=(t/h if h else None)
    return {'races':n,'head_hits':h,'head_rate':h/n if n else None,'ticket_hits':t,'ticket_rate':t/n if n else None,'conditional_top5_capture_given_head3':cap}

def main():
    d=pd.read_csv(SRC,dtype=str).fillna('')
    if (d.date>='2026-09-01').any(): d=d[d.date<'2026-09-01'].copy()
    d['month']=d.date.str[:7]
    ex=set(pd.read_csv(BASE,dtype=str).race_code.astype(str)); assert len(ex)==94
    d=d[~d.race_code.astype(str).isin(ex)]
    d=d[(d.settle__usable=='1')&(d.closing_odds__ok=='1')].reset_index(drop=True)
    feb=d[d.month=='2026-02'].copy().reset_index(drop=True)
    mar=d[d.month=='2026-03'].copy().reset_index(drop=True)
    # thresholds are feature-only February quantiles; no outcome fitting.
    f2=col(feb,3,'モーター2連対率')-col(feb,2,'モーター2連対率')
    f3=col(feb,3,'モーター3連対率')-col(feb,2,'モーター3連対率')
    q2_lo,q2_hi=[float(x) for x in f2.quantile([1/3,2/3])]
    q3_lo,q3_hi=[float(x) for x in f3.quantile([1/3,2/3])]
    # Conservative joint regime: strong only when both gaps are in top tercile; weak only when both in bottom tercile; else medium.
    m2=col(mar,3,'モーター2連対率')-col(mar,2,'モーター2連対率')
    m3=col(mar,3,'モーター3連対率')-col(mar,2,'モーター3連対率')
    Xf=base.build_static(feb); Xm=base.build_static(mar)
    p3,tops=w47.wave36(Xf,feb.settle__actual_combo.astype(str),Xm)
    q=mar[['date','race_code','settle__actual_combo']].copy(); q['p3']=p3; q['top5']=tops; q=q[q.p3>=CUT].copy().reset_index(drop=True)
    gaps=pd.DataFrame({'race_code':mar.race_code,'m2gap':m2,'m3gap':m3})
    q=q.merge(gaps,on='race_code',how='left')
    q['head3']=q.settle__actual_combo.str.startswith('3-').astype(int)
    q['top5_hit']=[a in t.split(';') for a,t in zip(q.settle__actual_combo,q.top5)]
    q['regime']=np.where((q.m2gap>=q2_hi)&(q.m3gap>=q3_hi),'strong',np.where((q.m2gap<=q2_lo)&(q.m3gap<=q3_lo),'weak','medium'))
    q=q.sort_values(['date','race_code']).reset_index(drop=True)
    mid=len(q)//2; boundary=q.iloc[mid-1].date+'|'+q.iloc[mid-1].race_code
    key=q.date+'|'+q.race_code
    regimes={}
    for r in ['strong','medium','weak']:
        z=q[q.regime==r].copy(); kz=z.date+'|'+z.race_code
        regimes[r]={'full':summarize(z),'early':summarize(z[kz<=boundary]),'late':summarize(z[kz>boundary]),'mean_m2gap':float(z.m2gap.mean()) if len(z) else None,'mean_m3gap':float(z.m3gap.mean()) if len(z) else None}
    out={'wave':'50-explicit-3v2-motor-edge-regimes','february_feature_only_cuts':{'motor2_gap_low':q2_lo,'motor2_gap_high':q2_hi,'motor3_gap_low':q3_lo,'motor3_gap_high':q3_hi},'march_baseline':summarize(q),'regimes':regimes,'september_outcomes_read':False,'jul_aug_used':False,'production_changed':False,'status':'DIAGNOSTIC_ONLY'}
    OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(out,ensure_ascii=False),flush=True)
if __name__=='__main__': main()
