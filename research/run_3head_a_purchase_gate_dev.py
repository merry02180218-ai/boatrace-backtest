from __future__ import annotations
import json, numpy as np, pandas as pd
from run_3head_wave20_manual_gate import build_gates, cond_mask, prep_month, prefetch_sources, build_motor_exhibition, build_pre_enhanced, make_pre_scores

DEV={'oct':('2025-10-01','2025-10-31'),'nov':('2025-11-01','2025-11-30'),'dec':('2025-12-01','2025-12-31'),'jan':('2026-01-01','2026-01-31'),'feb':('2026-02-01','2026-02-28')}
A={'band':[1,12],'bq':.925,'conds':[['post_motor_rank_edge2','>=',.20],['post_ex_rank3','<=',1.0]]}

def mask(df,conds):
    m=pd.Series(True,index=df.index)
    for c in conds:m &= cond_mask(df,c).fillna(False)
    return m

def main():
    raw={}
    for k,(a,b) in DEV.items():
        x,r,audit=build_pre_enhanced(a,b,True);raw[k]=(x,r,audit)
    frames={k:prep_month(x,r) for k,(x,r,_) in raw.items()}
    scores,_=make_pre_scores(frames)
    days,cache=prefetch_sources();post,pa=build_motor_exhibition(days,cache)
    gates=build_gates()
    rows=[]
    for k in ['nov','dec','jan']:
        d=scores[k].merge(post,on=['rc','date'],how='left',validate='one_to_one')
        rn=pd.to_numeric(d.race_no,errors='coerce');pre=pd.to_numeric(d.pre_score,errors='coerce')
        am=(rn>=1)&(rn<=12)&(pre>=.925)&mask(d,A['conds'])
        da=d.loc[am].copy()
        for g in gates:
            gm=mask(da,g['conds'])
            n=int(gm.sum());h=int(da.loc[gm,'y'].sum()) if n else 0
            rows.append({'month':k,'gate':g['name'],'family':g['family'],'n':n,'heads':h,'head_rate':h/n if n else None})
    z=pd.DataFrame(rows)
    agg=z.groupby(['gate','family'],as_index=False).agg(n=('n','sum'),heads=('heads','sum'),min_month_n=('n','min'),max_month_n=('n','max'))
    agg['head_rate']=agg.heads/agg.n
    # Volume-preserving candidates only: at least 25 A races each dev month.
    agg=agg[agg.min_month_n>=25].sort_values(['head_rate','n'],ascending=[False,False])
    out={'policy':{'A_frozen':True,'selection_months':['2025-11','2025-12','2026-01'],'march_used':False,'september_2026_used':False,'production_changed':False},
         'A':A,'candidate_count':int(len(agg)),'top30':agg.head(30).to_dict('records'),'monthly':z.to_dict('records'),'post_audit':pa}
    open('research_3head_a_purchase_gate_dev_result.json','w').write(json.dumps(out,ensure_ascii=False,indent=2,default=str))
    print(json.dumps(out,ensure_ascii=False,indent=2,default=str))
if __name__=='__main__':main()
