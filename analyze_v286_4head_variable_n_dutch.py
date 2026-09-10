#!/usr/bin/env python3
"""v286: pre-result variable Top-N (4/6/8/10) for independent 4-head opponent models.

Key discipline
--------------
* N is decided before result/odds settlement from the independent SECOND model's
  probability concentration only. It is available for every S/A BET race,
  including races where boat 4 later loses.
* SECOND is the frozen PLAYER_START / L2=10 listwise model trained only on prior
  boat-4-win races for each evaluation month.
* Candidate confidence metric / quantile cut-set / opponent model (v283 or v284)
  are selected on Feb-Mar only using archived-odds development ROI.
* Apr-Jun are untouched holdout-like evaluation for that frozen policy.
* Every BET race costs exactly 10,000 yen. Boat-4 loss => payout 0.
* Archived odds are settlement proxy only; this is not formal prospective OOS.
* Jul/Aug excluded; September not read. v96 is not used for ranking/N selection.
"""
from pathlib import Path
import math
import numpy as np
import pandas as pd

import analyze_v270_4head_win_feature_importance as v270
import analyze_v274_4head_opponent_feature_audit as v274
import analyze_v278_4head_opponent_current_exhibition_audit as v278
import analyze_v279_4head_opponent_listwise_rebuild as v279
import analyze_v282_4head_conditional_third as v282
import analyze_v283_4head_conditional_pair_order as v283
import analyze_v284_4head_conditional_third_regime as v284
import analyze_v285_4head_independent_newroi_topn as v285
import analyze_v96_4corner_monthly_walkforward_tiebreak as v96
import analyze_v251_4head_newroi_bridge as v251
from analyze_v205_3head_operational_replay import load_odds

ROOT=Path(__file__).resolve().parent
OUT_GRID=ROOT/'analysis_v286_4head_variable_n_tune_grid.csv'
OUT_CONF=ROOT/'analysis_v286_4head_variable_n_confidence.csv'
OUT_HOLD=ROOT/'analysis_v286_4head_variable_n_holdout.csv'
OUT_MONTH=ROOT/'analysis_v286_4head_variable_n_monthly.csv'
OUT_DETAIL=ROOT/'analysis_v286_4head_variable_n_detail.csv'
SUM=ROOT/'summary_v286_4head_variable_n_dutch.md'
BANK=10000
TUNE=('2026-02','2026-03')
HOLD=('2026-04','2026-05','2026-06')
MONTHS=TUNE+HOLD
NS=(4,6,8,10)
CUTSETS={
    'Q25_50_75':(.25,.50,.75),
    'Q20_50_80':(.20,.50,.80),
    'Q20_45_70':(.20,.45,.70),
    'Q30_55_80':(.30,.55,.80),
    'Q15_40_70':(.15,.40,.70),
}
METRICS=('p2_top1','p2_top2mass','p2_ratio','p2_margin','p2_concentration')


def ii(x,d=0):
    try:return int(float(x))
    except:return d


def portfolio():
    s=pd.read_csv(v274.SEL,dtype={'race_code':str});s['race_code']=s.race_code.astype(str).str.zfill(12)
    for c in ('PRE','POST','a_score'):s[c]=pd.to_numeric(s[c],errors='coerce')
    is_s=s['is_S'].astype(str).str.lower().isin(('true','1'))
    is_a=(~is_s)&(s.PRE>=.18)&(s.POST>=.18)&(s.a_score>=.28)
    q=s[s.month.isin(MONTHS)&(is_s|is_a)].copy();q['layer']=np.where(is_s.loc[q.index],'S','A')
    return q[['date','month','race_code','layer','PRE','POST','a_score']].drop_duplicates('race_code')


def actual_map():
    out={}
    for r in v96.read():
        out[str(r.get('race_code','')).zfill(12)]=(ii(r.get('winner')),ii(r.get('second')),ii(r.get('third')),ii(r.get('valid_result')))
    return out


def keep_specs(d):
    specs=v274.feature_specs(d);out={}
    for n,s in specs.items():
        if n in v279.ABILITY or n in v279.POSITION or n.startswith('pref_pl_') or n.startswith('pref_vh_') or n.startswith('pref_gh_') or n.startswith('suf_st_'):
            out[n]=s
    return out


def allrace_long(d,port):
    codes=set(port.race_code.astype(str));specs=keep_specs(d);recs=[]
    for _,r in d.iterrows():
        code=str(r.get('race_code','')).zfill(12)
        if code not in codes:continue
        ds=str(r.get('date',''));base={'date':ds,'month':ds[:7],'race_code':code}
        for b in v279.BOATS:
            z=dict(base);z['boat']=b
            for n,s in specs.items():z[n]=v274.fval(r,b,s)
            recs.append(z)
    z=pd.DataFrame(recs)
    if z.empty:raise RuntimeError('no all-race opponent rows for portfolio')
    return v278.add_current(z)


def confidence_all_races(port):
    d,trainz=v279.build_source();d=d[d._date<pd.Timestamp('2026-07-01')].copy();d['date']=d.date.astype(str)
    test=allrace_long(d,port);fs=v279.family_map(trainz)['PLAYER_START'];rec=[]
    for mon in MONTHS:
        tr=trainz[trainz.month<mon].copy();te=test[test.month==mon].copy()
        if tr.race_code.nunique()<v279.MIN_TRAIN or te.empty:continue
        use=v279.good_features(tr,fs);m=v279.ListwiseSoftmax(10.0).fit(tr,use,'y2');te=te.copy();te['s2']=m.score(te)
        for code,g in te.groupby('race_code'):
            if len(g)!=5:continue
            p=v279.probs_within_race(g,'s2');vals=sorted(p.values(),reverse=True);p1,p2=vals[:2]
            ent=-sum(x*math.log(max(x,1e-12)) for x in vals)/math.log(5.0)
            rec.append({'month':mon,'date':str(g.date.iloc[0]),'race_code':str(code).zfill(12),
                        'p2_top1':p1,'p2_top2mass':p1+p2,'p2_ratio':p1/max(p2,1e-12),
                        'p2_margin':p1-p2,'p2_concentration':1.0-ent,
                        'p2_probs':'|'.join(f'{b}:{p[b]:.12g}' for b in v279.BOATS),'nfeat2':len(use)})
    c=pd.DataFrame(rec);c=c.merge(port[['race_code','layer','PRE','POST','a_score']],on='race_code',how='inner')
    if c.race_code.nunique()!=port.race_code.nunique():
        miss=set(port.race_code)-set(c.race_code);raise RuntimeError(f'missing pre-result confidence rows: {len(miss)}')
    c.to_csv(OUT_CONF,index=False);return c


def load_model_rows(path):
    z=pd.read_csv(path,dtype={'race_code':str});z['race_code']=z.race_code.astype(str).str.zfill(12)
    return {str(r.race_code):r for _,r in z.iterrows()}


def order_v283(r):
    return v283.order_policy(v282.parse_p2(r.p2),v282.parse_cond(r['cond']),.60,'TOP2XTOP2',1.50)


def order_v284(r):
    return v284.order_policy(v284.parse_p2(r.p2),v284.parse_cond(r['cond']),.60,'TOP2XTOP2')


def odds_row(oi,code):
    if code not in oi.index:return None
    r=oi.loc[code]
    return r.iloc[-1] if isinstance(r,pd.DataFrame) else r


def thresholds(c,metric,cutname):
    q=c[c.month.isin(TUNE)][metric].dropna();qs=CUTSETS[cutname]
    if len(q)<20:raise RuntimeError('too few tune confidence rows')
    return tuple(float(q.quantile(x)) for x in qs)


def choose_n(x,ths):
    lo,mid,hi=ths
    if x>=hi:return 4
    if x>=mid:return 6
    if x>=lo:return 8
    return 10


def settle_rows(c,months,model_name,lookup,orderfn,metric=None,ths=None,fixed_n=None):
    am=actual_map();od=load_odds();oi=od.set_index('race_code',drop=False) if not od.empty else pd.DataFrame();rows=[]
    miss_actual=miss_model=miss_odds=0
    for _,r in c[c.month.isin(months)].iterrows():
        code=str(r.race_code);a=am.get(code)
        if not a or a[3]!=1:miss_actual+=1;continue
        n=int(fixed_n) if fixed_n else choose_n(float(r[metric]),ths)
        hit=0;ret=0.0;comp=np.nan;tickets=''
        if a[0]==4:
            mr=lookup.get(code)
            if mr is None:miss_model+=1;continue
            odr=odds_row(oi,code)
            if odr is None:miss_odds+=1;continue
            order=orderfn(mr);ts=[f'4-{x}-{y}' for x,y in order[:n]];st=v251.settle('',ts,odr,a)
            if st is None:miss_odds+=1;continue
            hit,ret,comp=st;tickets='|'.join(ts)
        rows.append({'date':r.date,'month':r.month,'race_code':code,'layer':r.layer,'model':model_name,'n':n,
                     'metric':metric if metric else 'FIXED','winner':a[0],'head4_win':int(a[0]==4),'hit':int(hit),
                     'return_yen':float(ret),'profit_yen':float(ret-BANK),'comp_odds':comp,'tickets':tickets})
    if miss_actual or miss_model or miss_odds:
        raise RuntimeError(f'settlement missing actual={miss_actual} model={miss_model} odds={miss_odds}')
    return pd.DataFrame(rows)


def agg(g):
    cost=len(g)*BANK;ret=float(g.return_yen.sum())
    return {'R':len(g),'avg_n':g.n.mean(),'head4_wins':int(g.head4_win.sum()),'hits':int(g.hit.sum()),
            'hit_rate_pct':100*g.hit.mean(),'cost_yen':cost,'return_yen':ret,'profit_yen':ret-cost,
            'roi_pct':100*ret/cost if cost else np.nan}


def monthly_floor(z):
    vals=[]
    for _,g in z.groupby('month'):vals.append(agg(g)['roi_pct'])
    return min(vals) if vals else np.nan


def main():
    port=portfolio();c=confidence_all_races(port)
    p283=load_model_rows(v283.OUT);p284=load_model_rows(v284.OUT)
    models={'v283':(p283,order_v283),'v284':(p284,order_v284)}
    grid=[];tune_detail={}
    for model,(lookup,ofn) in models.items():
        for metric in METRICS:
            for cutname in CUTSETS:
                th=thresholds(c,metric,cutname);z=settle_rows(c,TUNE,model,lookup,ofn,metric,th,None);a=agg(z);floor=monthly_floor(z)
                obj=.70*a['roi_pct']+.30*floor
                grid.append({'model':model,'metric':metric,'cutset':cutname,'t_lo':th[0],'t_mid':th[1],'t_hi':th[2],
                             **a,'monthly_floor_roi':floor,'objective':obj,
                             'n4':int((z.n==4).sum()),'n6':int((z.n==6).sum()),'n8':int((z.n==8).sum()),'n10':int((z.n==10).sum())})
                tune_detail[(model,metric,cutname)]=z
    G=pd.DataFrame(grid).sort_values(['objective','roi_pct','monthly_floor_roi'],ascending=False);G.to_csv(OUT_GRID,index=False)
    b=G.iloc[0];model=str(b.model);metric=str(b.metric);cutname=str(b.cutset);ths=(float(b.t_lo),float(b.t_mid),float(b.t_hi));lookup,ofn=models[model]
    hold=settle_rows(c,HOLD,model,lookup,ofn,metric,ths,None);hold['policy']='VARIABLE';
    # Fixed benchmarks chosen before v286 from v285 diagnostics; neither enters variable-N tuning.
    f283=settle_rows(c,HOLD,'v283',p283,order_v283,fixed_n=4);f283['policy']='FIXED_v283_N4'
    f284=settle_rows(c,HOLD,'v284',p284,order_v284,fixed_n=10);f284['policy']='FIXED_v284_N10'
    detail=pd.concat([hold,f283,f284],ignore_index=True);detail.to_csv(OUT_DETAIL,index=False)

    rows=[]
    for pol,g in detail.groupby('policy'):
        rows.append({'scope':'S+A','policy':pol,**agg(g)})
        for layer,gg in g.groupby('layer'):rows.append({'scope':layer,'policy':pol,**agg(gg)})
    H=pd.DataFrame(rows);H.to_csv(OUT_HOLD,index=False)
    mr=[]
    for (pol,mon),g in detail.groupby(['policy','month']):mr.append({'policy':pol,'month':mon,'scope':'S+A',**agg(g)})
    M=pd.DataFrame(mr);M.to_csv(OUT_MONTH,index=False)

    hv=H[(H.scope=='S+A')&(H.policy=='VARIABLE')].iloc[0]
    L=['# v286 pre-result variable-N / exact 10k Dutch','',
       '- N in {4,6,8,10} is chosen from pre-result SECOND-model probability concentration for every BET race.',
       '- Metric / quantile cut-set / v283-v284 model choice are selected on Feb-Mar only; Apr-Jun are untouched holdout-like evaluation.',
       '- Every race costs exactly 10,000 yen; boat-4 loss is payout 0 / profit -10,000 yen.',
       '- Archived odds are retrospective settlement proxy only; not formal prospective OOS.',
       '- Jul/Aug excluded; September not read; v96 is not used in ranking or N selection.','',
       '## Frozen policy selected on Feb-Mar','',
       f'- opponent model: **{model}**',f'- confidence metric: **{metric}**',f'- quantile cut-set: **{cutname}**',
       f'- thresholds low/mid/high: **{ths[0]:.6f} / {ths[1]:.6f} / {ths[2]:.6f}**',
       f'- rule: confidence >= high => N4; >= mid => N6; >= low => N8; else N10.',
       f'- Feb-Mar tune ROI: **{b.roi_pct:.2f}%**, monthly floor **{b.monthly_floor_roi:.2f}%**, avg N **{b.avg_n:.2f}**.','',
       '### Top tune policies','',
       '|model|metric|cutset|R|avg N|hits|ROI|monthly floor|objective|N4/N6/N8/N10|',
       '|---|---|---|---:|---:|---:|---:|---:|---:|---|']
    for _,r in G.head(15).iterrows():
        L.append(f'|{r.model}|{r.metric}|{r.cutset}|{int(r.R)}|{r.avg_n:.2f}|{int(r.hits)}|{r.roi_pct:.2f}%|{r.monthly_floor_roi:.2f}%|{r.objective:.2f}|{int(r.n4)}/{int(r.n6)}/{int(r.n8)}/{int(r.n10)}|')
    L += ['','## Apr-Jun untouched holdout-like economics','',
          '|scope|policy|R|avg N|4-head wins|hits|return|profit|ROI|','|---|---|---:|---:|---:|---:|---:|---:|---:|']
    for _,r in H.sort_values(['scope','policy']).iterrows():
        L.append(f'|{r.scope}|{r.policy}|{int(r.R)}|{r.avg_n:.2f}|{int(r.head4_wins)}|{int(r.hits)}|{r.return_yen:.0f}|{r.profit_yen:+.0f}|{r.roi_pct:.2f}%|')
    L += ['','## Apr-Jun monthly S+A','',
          '|policy|month|R|avg N|hits|profit|ROI|','|---|---|---:|---:|---:|---:|---:|']
    for _,r in M.sort_values(['policy','month']).iterrows():
        L.append(f'|{r.policy}|{r.month}|{int(r.R)}|{r.avg_n:.2f}|{int(r.hits)}|{r.profit_yen:+.0f}|{r.roi_pct:.2f}%|')
    # Adoption criterion stated before looking at holdout result: variable policy must beat 100% aggregate and not be clearly worse than both fixed references.
    fixed=H[(H.scope=='S+A')&H.policy.str.startswith('FIXED')]
    bestfix=float(fixed.roi_pct.max())
    decision='PROMISING CANDIDATE' if hv.roi_pct>100 and hv.roi_pct>=bestfix else 'DO NOT PROMOTE'
    L += ['','## Decision','',f'- **{decision}**.',
          '- Treat Apr-Jun as holdout-like development evidence only; archived odds still prevent a formal prospective/OOS claim.',
          '- If promoted, freeze this exact N rule and reproduce it in live inference before reading September outcomes.']
    SUM.write_text('\n'.join(L)+'\n',encoding='utf-8');print('\n'.join(L))

if __name__=='__main__':main()
