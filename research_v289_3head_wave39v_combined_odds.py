from pathlib import Path
import json, numpy as np, pandas as pd
import research_v289_3head_wave31_nonlinear_gate as base
import research_v289_3head_wave37_orderer as w37

SRC=Path('analysis_v289_3head_wave21_allrace_feature_settled.csv')
BC=Path('v288_operational_pre_replay_94_baseline_codes.csv')
OUT=Path('research_v289_3head_wave39v_combined_odds.json')
CUT=.365448
FLOORS=[2.5,3.0,3.5,4.0,4.5,5.0,6.0,7.5,10.0]
MAXK=10

def effective_odds(odds):
    a=np.asarray(odds,dtype=float)
    if len(a)==0 or np.any(~np.isfinite(a)) or np.any(a<=1): return np.nan
    return float(1.0/np.sum(1.0/a))

def ranked_tickets(score):
    return [base.COMBOS[j] for j in np.argsort(-np.nan_to_num(score,nan=-1))[:MAXK]]

def choose_variable(row, ranked, floor):
    try: od=json.loads(row['closing_odds__json'])
    except: return ranked[:1],np.nan
    best=1; best_eff=np.nan
    for k in range(1,min(MAXK,len(ranked))+1):
        try: vals=[float(od[t]) for t in ranked[:k]]
        except: break
        eff=effective_odds(vals)
        if np.isfinite(eff) and eff>=floor:
            best=k; best_eff=eff
        else:
            break
    if not np.isfinite(best_eff):
        try: best_eff=effective_odds([float(od[ranked[0]])])
        except: best_eff=np.nan
    return ranked[:best],best_eff

def settle(q, floor=None, fixedk=None):
    x=q.copy(); rets=[]; ks=[]; effs=[]; tss=[]
    for _,r in x.iterrows():
        ranked=r['ranked']
        if fixedk is not None:
            ts=ranked[:fixedk]
            try: od=json.loads(r['closing_odds__json']); eff=effective_odds([float(od[t]) for t in ts])
            except: eff=np.nan
        else:
            ts,eff=choose_variable(r,ranked,floor)
        tss.append(';'.join(ts));ks.append(len(ts));effs.append(eff);rets.append(base.dutch_return(r,ts))
    x['tickets']=tss;x['k']=ks;x['effective_odds']=effs;x['variant_return']=rets
    m=base.block(x);m['avg_k']=float(np.mean(ks)) if ks else None;m['median_k']=float(np.median(ks)) if ks else None
    m['k_distribution']={str(k):int(sum(np.array(ks)==k)) for k in sorted(set(ks))}
    m['mean_effective_odds']=float(np.nanmean(effs)) if len(effs) else None
    m['max_drawdown_yen']=base.maxdd(x.sort_values(['date','race_code'])) if len(x) else 0
    return x,m

def main():
    d=pd.read_csv(SRC,dtype=str).fillna('')
    if d.date.max()>'2026-08-31': raise RuntimeError('September forbidden')
    ex=set(pd.read_csv(BC,dtype=str).race_code.astype(str)); d=d[~d.race_code.astype(str).isin(ex)].copy()
    d=d[(d.settle__usable=='1')&(d.closing_odds__ok=='1')].reset_index(drop=True);d['month']=d.date.str[:7]
    X=base.build_static(d);y=d.settle__actual_combo.astype(str);p=np.full(len(d),np.nan);score=np.full((len(d),len(base.COMBOS)),np.nan)
    specs=[('2026-03',d.month=='2026-02'),('2026-04',d.month<'2026-04'),('2026-05',d.month<'2026-05'),('2026-06',d.month<'2026-06'),('2026-07',d.month<='2026-06'),('2026-08',d.month<='2026-06')]
    for mo,trm in specs:
        te=d.month==mo;ti=np.flatnonzero(trm.to_numpy());ei=np.flatnonzero(te.to_numpy());yt=y.iloc[ti];mask=yt.str.startswith('3-').to_numpy()
        p[ei]=w37.head_fit(X.iloc[ti],yt.str.startswith('3-').astype(int).to_numpy(),X.iloc[ei])
        score[ei]=w37.score_combo_logit(X.iloc[ti].iloc[np.flatnonzero(mask)],yt.iloc[np.flatnonzero(mask)],X.iloc[ei])
    d['p3']=p;d['ranked']=[ranked_tickets(r) if np.isfinite(r).any() else [] for r in score]
    sel=d[d.p3>=CUT].copy()
    march=sel[sel.month=='2026-03'].sort_values(['date','race_code']).reset_index(drop=True);h=len(march)//2
    candidates=[]
    for floor in FLOORS:
        _,f=settle(march,floor=floor);_,e=settle(march.iloc[:h],floor=floor);_,l=settle(march.iloc[h:],floor=floor)
        candidates.append({'floor':floor,'full':f,'early':e,'late':l,'worst_half_roi':min(e['roi_pct'],l['roi_pct'])})
    chosen=max(candidates,key=lambda z:(z['worst_half_roi'],z['full']['roi_pct']))
    fixed={};months={}
    for mo in ['2026-04','2026-05','2026-06','2026-07','2026-08']:
        q=sel[sel.month==mo];_,months[mo]=settle(q,floor=chosen['floor'])
    hold=sel[sel.month.isin(['2026-04','2026-05','2026-06'])];shadow=sel[sel.month.isin(['2026-07','2026-08'])]
    _,hm=settle(hold,floor=chosen['floor']);_,sm=settle(shadow,floor=chosen['floor']);_,fixed5=settle(hold,fixedk=5)
    monthly_h=[months[m] for m in ['2026-04','2026-05','2026-06']]
    hm['min_month_roi_pct']=min(z['roi_pct'] for z in monthly_h);hm['red_months']=sum(z['roi_pct']<100 for z in monthly_h)
    out={'rule':'largest ranked K<=10 with combined_odds=1/sum(1/odds) >= floor; JPY10k Dutch','march_candidates':candidates,'chosen_floor':chosen['floor'],'fixed_top5_apr_jun':fixed5,'months':months,'apr_jun_variable':hm,'jul_aug_shadow_variable':sm,'overlap':int(hold.race_code.astype(str).isin(ex).sum())}
    OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
