from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
import research_v289_3head_wave36_lda_stable_gate as w36
import research_v289_3head_wave31_nonlinear_gate as base

SRC=Path('analysis_v289_3head_wave21_allrace_feature_settled.csv')
BASEC=Path('v288_operational_pre_replay_94_baseline_codes.csv')
OUT=Path('analysis_v289_3head_wave36sf_two_layer.csv')
OUTJ=Path('research_v289_3head_wave36sf_two_layer.json')
OUTM=Path('research_v289_3head_wave36sf_two_layer.md')
MAIN_UNITS=80
TAIL_UNITS=20


def alloc_units(odds,total_units):
    odds=np.asarray(odds,dtype=float)
    raw=total_units*(1/odds)/(1/odds).sum()
    u=np.floor(raw).astype(int); rem=int(total_units-u.sum())
    if rem>0:
        frac=raw-u
        for i in np.argsort(-frac)[:rem]: u[i]+=1
    return u


def two_layer_return(r):
    ts=str(r['top5']).split(';') if r['top5'] else []
    if len(ts)<5:return 0
    try: od=json.loads(r['closing_odds__json'])
    except:return 0
    main=ts[:3]; tail=ts[3:5]
    try:
        u1=alloc_units([float(od[x]) for x in main],MAIN_UNITS)
        u2=alloc_units([float(od[x]) for x in tail],TAIL_UNITS)
    except:return 0
    ac=str(r['actual']); pay=int(float(r['settle__trifecta_payout_100_yen'] or 0))
    if ac in main:return int(u1[main.index(ac)]*pay)
    if ac in tail:return int(u2[tail.index(ac)]*pay)
    return 0


def hit_rank(r):
    ts=str(r['top5']).split(';') if r['top5'] else []
    ac=str(r['actual'])
    return ts.index(ac)+1 if ac in ts else 0


def actual_odds(r):
    try:return float(json.loads(r['closing_odds__json']).get(str(r['actual']),np.nan))
    except:return np.nan


def metrics(q,retcol):
    x=q.copy(); n=len(x); payout=int(x[retcol].sum()); stake=n*10000
    hits=int((x[retcol]>0).sum())
    pnl=(x[retcol]-10000).cumsum(); dd=float((pnl.cummax()-pnl).max()) if n else 0
    return {'races':n,'hits':hits,'stake_yen':stake,'payout_yen':payout,'profit_yen':payout-stake,'roi_pct':100*payout/stake if stake else None,'max_drawdown_yen':dd}


def bandstats(x,retcol):
    bands=[('lt10',0,10),('10to20',10,20),('20to50',20,50),('ge50',50,float('inf'))]
    out={}
    for name,lo,hi in bands:
        g=x[(x.actual_odds>=lo)&(x.actual_odds<hi)]
        m=metrics(g,retcol); m['head_hits']=int(g.actual3.sum())
        m['ticket_hits']=int((g[retcol]>0).sum())
        out[name]=m
    return out


def main():
    d=pd.read_csv(SRC,dtype=str).fillna('')
    if d.date.max()>'2026-08-31':raise RuntimeError('September forbidden')
    bc=pd.read_csv(BASEC,dtype=str).fillna(''); ex=set(bc.race_code.astype(str))
    if len(ex)!=94:raise RuntimeError('exact v288 94 required')
    d=d[~d.race_code.astype(str).isin(ex)].copy(); d=d[(d.settle__usable=='1')&(d.closing_odds__ok=='1')].reset_index(drop=True); d['month']=d.date.str[:7]
    X=base.build_static(d); y=d.settle__actual_combo.astype(str); d['actual']=y; d['actual3']=y.str.startswith('3-').astype(int)
    n=len(d); p=np.full(n,np.nan); score=np.full((n,len(base.COMBOS)),np.nan)
    def run(trm,tem):
        tr=np.flatnonzero(trm.to_numpy()); te=np.flatnonzero(tem.to_numpy()); a,b=w36.fit_predict(X.iloc[tr],y.iloc[tr],X.iloc[te]); p[te]=a; score[te,:]=b
    run(d.month=='2026-02',d.month=='2026-03')
    for mo in ['2026-04','2026-05','2026-06']:run(d.month<mo,d.month==mo)
    frozen=d.month<='2026-06'
    for mo in ['2026-07','2026-08']:run(frozen,d.month==mo)
    d['p3']=p
    for k in [3,5]:
        vals=[]
        for i in range(n):
            if not np.isfinite(score[i]).any():vals.append('');continue
            idx=np.argsort(-np.nan_to_num(score[i],nan=-1))[:k];vals.append(';'.join(base.COMBOS[j] for j in idx))
        d[f'top{k}']=vals
    march=d[d.month=='2026-03'].sort_values(['date','race_code']).reset_index(drop=True); split=len(march)//2; early=march.iloc[:split]; late=march.iloc[split:]
    cand=[]
    for qv in w36.QS:
        cut=float(march.p3.quantile(qv))
        for k in w36.KS:
            sf=march[march.p3>=cut];se=early[early.p3>=cut];sl=late[late.p3>=cut]
            f=w36.labelstat(sf,k);e=w36.labelstat(se,k);l=w36.labelstat(sl,k)
            if f['races']>=30 and e['races']>=10 and l['races']>=10:cand.append({'q':qv,'cut':cut,'k':k,'full':f,'early':e,'late':l,'worst_half_head_rate':min(e['head_rate'],l['head_rate'])})
    chosen=max(cand,key=lambda z:(z['worst_half_head_rate'],z['full']['head_rate'],z['full']['ticket_rate'],z['full']['races'],-z['q'],-z['k']))
    if chosen['k']!=5:raise RuntimeError('Wave36 expected top5')
    sel=d[d.p3>=chosen['cut']].copy();sel['hit_rank']=sel.apply(hit_rank,axis=1);sel['actual_odds']=sel.apply(actual_odds,axis=1)
    sel['baseline_return']=[base.dutch_return(r,str(r.top5).split(';')) for _,r in sel.iterrows()]
    sel['two_layer_return']=sel.apply(two_layer_return,axis=1)
    hold=sel[sel.month.isin(['2026-04','2026-05','2026-06'])].sort_values(['date','race_code']).copy(); shadow=sel[sel.month.isin(['2026-07','2026-08'])].sort_values(['date','race_code']).copy()
    hm=metrics(hold,'two_layer_return'); bm=metrics(hold,'baseline_return'); sm=metrics(shadow,'two_layer_return')
    hm['monthly']={mo:metrics(g,'two_layer_return') for mo,g in hold.groupby('month')}; bm['monthly']={mo:metrics(g,'baseline_return') for mo,g in hold.groupby('month')}
    hm['bands']=bandstats(hold,'two_layer_return'); bm['bands']=bandstats(hold,'baseline_return')
    tail=hold[(hold.hit_rank>=4)&(hold.hit_rank<=5)&(hold.two_layer_return>0)]
    tail50=tail[tail.actual_odds>=50]
    tailinfo={'rank4_5_hits':len(tail),'rank4_5_payout_yen':int(tail.two_layer_return.sum()),'rank4_5_50x_hits':len(tail50),'rank4_5_50x_payout_yen':int(tail50.two_layer_return.sum()),'rank4_5_50x_races':tail50[['race_code','actual','actual_odds','hit_rank','two_layer_return']].to_dict('records')}
    overlap=int(pd.concat([hold,shadow]).race_code.astype(str).isin(ex).sum())
    if overlap:raise RuntimeError(f'v288 overlap {overlap}')
    pd.concat([hold.assign(period='pristine_holdout'),shadow.assign(period='non_pristine_shadow')]).to_csv(OUT,index=False,encoding='utf-8-sig')
    decision='RESEARCH_CANDIDATE' if hm['roi_pct']>bm['roi_pct'] and hm['profit_yen']>bm['profit_yen'] else 'NO_ADOPTION'
    out={'wave':'36S-F-two-layer','design':'Wave36 frozen gate; Top1-3 JPY8000 Dutch + Top4-5 JPY2000 Dutch','selection_basis':'same Wave36 March non-monetary stable-gate selection; allocation fixed ex ante, not tuned on Apr-Jun','march_gate':chosen,'strict_pristine_apr_jun_two_layer':hm,'strict_pristine_apr_jun_wave36_equal_dutch':bm,'shadow_non_pristine_jul_aug_two_layer':sm,'tail_capture':tailinfo,'v288_overlap':overlap,'september_forbidden':True,'decision':decision}
    OUTJ.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=['# Wave36S-F two-layer opponent allocation','',f"- Frozen gate: p3>={chosen['cut']:.6f}, top5",'- Allocation fixed before holdout inspection: Top1-3 = JPY8,000 Dutch; Top4-5 = JPY2,000 Dutch.',f"- Apr-Jun two-layer: **{hm['races']}R / {hm['hits']} hits / ROI {hm['roi_pct']:.3f}% / profit {hm['profit_yen']:+,} yen**",f"- Same races original Wave36 equal Dutch: **ROI {bm['roi_pct']:.3f}% / profit {bm['profit_yen']:+,} yen**",f"- Rank4-5 captured hits: **{tailinfo['rank4_5_hits']}**, payout {tailinfo['rank4_5_payout_yen']:,} yen; among them 50x+: **{tailinfo['rank4_5_50x_hits']}**, payout {tailinfo['rank4_5_50x_payout_yen']:,} yen",f"- v288 overlap: **{overlap}** / September forbidden: **True**",f"- decision: **{decision}**",'','## Monthly']
    for mo,z in hm['monthly'].items():lines.append(f"- {mo}: {z['races']}R / {z['hits']} hits / ROI {z['roi_pct']:.3f}% / profit {z['profit_yen']:+,} yen")
    lines+=['','## Odds bands (two-layer)']
    for b,z in hm['bands'].items():lines.append(f"- {b}: {z['races']}R / {z['ticket_hits']} hits / ROI {z['roi_pct']:.3f}% / profit {z['profit_yen']:+,} yen")
    OUTM.write_text('\n'.join(lines)+'\n',encoding='utf-8');print('\n'.join(lines),flush=True)
if __name__=='__main__':main()
