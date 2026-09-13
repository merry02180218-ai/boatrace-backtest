from pathlib import Path
import json, numpy as np, pandas as pd
import research_v289_3head_wave39v_combined_odds as w39v
import research_v289_3head_wave31_nonlinear_gate as base
import research_v289_3head_wave37_orderer as w37

SRC=Path('analysis_v289_3head_wave21_allrace_feature_settled.csv')
BC=Path('v288_operational_pre_replay_94_baseline_codes.csv')
OUT=Path('research_v289_3head_wave39c_confidence_k.json')
CUT=.365448
RULES=[('p40_k3_f35',.40,3,3.5),('p45_k4_f35',.45,4,3.5),('p50_k5_f35',.50,5,3.5),('p45_k4_f40',.45,4,4.0)]

def choose(row, ranked, rule):
    _,pcut,hk,floor=rule
    if float(row.p3)>=pcut:
        ts=ranked[:hk]
        try:
            od=json.loads(row['closing_odds__json'])
            eff=w39v.effective_odds([float(od[t]) for t in ts])
        except:
            eff=np.nan
        return ts,eff
    return w39v.choose_variable(row,ranked,floor)

def settle(q,rule=None,fixedk=None):
    x=q.copy();rets=[];ks=[]
    for _,r in x.iterrows():
        ranked=r['ranked']
        if fixedk is not None:
            ts=ranked[:fixedk]
        else:
            ts,_=choose(r,ranked,rule)
        ks.append(len(ts));rets.append(base.dutch_return(r,ts))
    x['variant_return']=rets;x['k']=ks
    m=base.block(x)
    m['avg_k']=float(np.mean(ks)) if ks else None
    m['median_k']=float(np.median(ks)) if ks else None
    m['k_distribution']={str(k):int(sum(np.asarray(ks)==k)) for k in sorted(set(ks))}
    m['max_drawdown_yen']=base.maxdd(x.sort_values(['date','race_code'])) if len(x) else 0
    return x,m

def main():
    d=pd.read_csv(SRC,dtype=str).fillna('')
    if d.date.max()>'2026-08-31': raise RuntimeError('September forbidden')
    ex=set(pd.read_csv(BC,dtype=str).race_code.astype(str))
    d=d[~d.race_code.astype(str).isin(ex)].copy()
    d=d[(d.settle__usable=='1')&(d.closing_odds__ok=='1')].reset_index(drop=True)
    d['month']=d.date.str[:7]
    X=base.build_static(d);y=d.settle__actual_combo.astype(str)
    p=np.full(len(d),np.nan);score=np.full((len(d),len(base.COMBOS)),np.nan)
    specs=[('2026-03',d.month=='2026-02'),('2026-04',d.month<'2026-04'),('2026-05',d.month<'2026-05'),('2026-06',d.month<'2026-06'),('2026-07',d.month<='2026-06'),('2026-08',d.month<='2026-06')]
    for mo,trm in specs:
        te=d.month==mo;ti=np.flatnonzero(trm.to_numpy());ei=np.flatnonzero(te.to_numpy());yt=y.iloc[ti];mask=yt.str.startswith('3-').to_numpy()
        p[ei]=w37.head_fit(X.iloc[ti],yt.str.startswith('3-').astype(int).to_numpy(),X.iloc[ei])
        score[ei]=w37.score_combo_logit(X.iloc[ti].iloc[np.flatnonzero(mask)],yt.iloc[np.flatnonzero(mask)],X.iloc[ei])
    d['p3']=p;d['ranked']=[w39v.ranked_tickets(r) if np.isfinite(r).any() else [] for r in score]
    sel=d[d.p3>=CUT].copy();march=sel[sel.month=='2026-03'].sort_values(['date','race_code']).reset_index(drop=True);h=len(march)//2
    cand=[]
    for rule in RULES:
        _,f=settle(march,rule);_,e=settle(march.iloc[:h],rule);_,l=settle(march.iloc[h:],rule)
        cand.append({'rule':rule[0],'full':f,'early':e,'late':l,'worst_half_roi':min(e['roi_pct'],l['roi_pct'])})
    chosen=max(cand,key=lambda z:(z['worst_half_roi'],z['full']['roi_pct']))
    rule=next(r for r in RULES if r[0]==chosen['rule'])
    months={}
    for mo in ['2026-04','2026-05','2026-06','2026-07','2026-08']:
        _,months[mo]=settle(sel[sel.month==mo],rule)
    hold=sel[sel.month.isin(['2026-04','2026-05','2026-06'])];shadow=sel[sel.month.isin(['2026-07','2026-08'])]
    _,hm=settle(hold,rule);_,sm=settle(shadow,rule);_,fixed5=settle(hold,fixedk=5)
    hm['min_month_roi_pct']=min(months[m]['roi_pct'] for m in ['2026-04','2026-05','2026-06'])
    hm['red_months']=sum(months[m]['roi_pct']<100 for m in ['2026-04','2026-05','2026-06'])
    out={'chosen':chosen,'months':months,'apr_jun':hm,'fixed_top5_apr_jun':fixed5,'jul_aug_shadow':sm,'overlap':int(hold.race_code.astype(str).isin(ex).sum())}
    OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(out,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
