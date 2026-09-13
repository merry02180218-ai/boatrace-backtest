from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
import research_v289_3head_wave36_lda_stable_gate as w36
import research_v289_3head_wave31_nonlinear_gate as base

SRC=Path('analysis_v289_3head_wave21_allrace_feature_settled.csv')
BASEC=Path('v288_operational_pre_replay_94_baseline_codes.csv')
OUT=Path('analysis_v289_3head_wave36_top5_miss_rank_audit.csv')
OUTJ=Path('research_v289_3head_wave36_top5_miss_rank_audit.json')
CUT=0.365448


def main():
    d=pd.read_csv(SRC,dtype=str).fillna('')
    if d.date.max()>'2026-08-31': raise RuntimeError('September forbidden')
    ex=set(pd.read_csv(BASEC,dtype=str).race_code.astype(str))
    if len(ex)!=94: raise RuntimeError('exact v288 exclusion required')
    d=d[~d.race_code.astype(str).isin(ex)].copy()
    d=d[(d.settle__usable=='1')&(d.closing_odds__ok=='1')].reset_index(drop=True)
    d['month']=d.date.str[:7]
    X=base.build_static(d); y=d.settle__actual_combo.astype(str)
    n=len(d); p=np.full(n,np.nan); sc=np.full((n,len(base.COMBOS)),np.nan)
    def run(trm,tem):
        tr=np.flatnonzero(trm.to_numpy()); te=np.flatnonzero(tem.to_numpy())
        a,b=w36.fit_predict(X.iloc[tr],y.iloc[tr],X.iloc[te]); p[te]=a; sc[te,:]=b
    run(d.month=='2026-02',d.month=='2026-03')
    for mo in ['2026-04','2026-05','2026-06']: run(d.month<mo,d.month==mo)
    d['p3']=p
    ranks=[]; top5=[]
    for i in range(n):
        if not np.isfinite(sc[i]).any(): ranks.append(np.nan); top5.append(''); continue
        order=np.argsort(-np.nan_to_num(sc[i],nan=-1)); combos=[base.COMBOS[j] for j in order]
        ac=str(y.iloc[i]); ranks.append(combos.index(ac)+1 if ac in combos else np.nan); top5.append(';'.join(combos[:5]))
    d['actual_rank']=ranks; d['top5_rebuilt']=top5
    hold=d[d.month.isin(['2026-04','2026-05','2026-06']) & (d.p3>=CUT)].copy()
    head=hold[hold.settle__actual_combo.str.startswith('3-')].copy()
    miss=head[head.actual_rank>5].copy()
    if len(hold)!=391 or len(head)!=160 or len(miss)!=73:
        raise RuntimeError(f'parity mismatch hold={len(hold)} head={len(head)} miss={len(miss)}')
    miss['actual_odds']=pd.to_numeric(miss.settle__trifecta_payout_100_yen,errors='coerce')/100.0
    miss['actual_rank']=miss.actual_rank.astype(int)
    keep=['race_code','date','month','venue','race_no','settle__actual_combo','actual_rank','actual_odds','p3','top5_rebuilt']
    miss[keep].sort_values(['actual_rank','actual_odds'],ascending=[True,False]).to_csv(OUT,index=False,encoding='utf-8-sig')
    rank_counts={str(k):int((miss.actual_rank==k).sum()) for k in range(6,21)}
    cum={}
    for k in [6,7,8,10,15,20]:
        q=miss[miss.actual_rank<=k]
        cum[str(k)]={'recovered':len(q),'of_73_pct':100*len(q)/73,'extra_tickets_per_race':k-5,
                     'odds_50plus':int((q.actual_odds>=50).sum()),'odds_100plus':int((q.actual_odds>=100).sum()),
                     'median_odds':float(q.actual_odds.median()) if len(q) else None,'max_odds':float(q.actual_odds.max()) if len(q) else None}
    bands={'lt10':miss.actual_odds<10,'10to20':(miss.actual_odds>=10)&(miss.actual_odds<20),'20to50':(miss.actual_odds>=20)&(miss.actual_odds<50),'ge50':miss.actual_odds>=50}
    bandrank={name:{'races':int(mask.sum()),'median_rank':float(miss.loc[mask,'actual_rank'].median()) if mask.sum() else None,
                    'rank6to8':int((mask & miss.actual_rank.le(8)).sum()),'rank6to10':int((mask & miss.actual_rank.le(10)).sum())} for name,mask in bands.items()}
    high=miss.sort_values('actual_odds',ascending=False).head(15)[['race_code','settle__actual_combo','actual_odds','actual_rank']].to_dict('records')
    out={'wave':'36-top5-miss-rank-audit','frozen_cut':CUT,'holdout_candidates':len(hold),'boat3_head':len(head),'top5_hits':len(head)-len(miss),'top5_misses':len(miss),
         'rank_counts_6_to_20':rank_counts,'cumulative_recovery':cum,'odds_band_rank_summary':bandrank,'highest_odds_misses':high,
         'v288_overlap':int(miss.race_code.astype(str).isin(ex).sum()),'september_forbidden':True,
         'note':'Descriptive Apr-Jun audit only; not valid for choosing a new live TopN.'}
    OUTJ.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(out,ensure_ascii=False,indent=2),flush=True)
if __name__=='__main__': main()
