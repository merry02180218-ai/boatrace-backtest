#!/usr/bin/env python3
"""v286: pre-result variable Top-N (4/6/8/10) for independent 4-head opponent models.

Revised after audit: the frozen S+A/A-score portfolio begins in April, so no
Feb-Mar S+A economic tuning is possible. Therefore v286 uses NO result/odds to
choose the N rule:

* Calibration domain: Feb-Mar broad 4-head candidates with PRE>=.18, POST>=.18.
* Confidence: normalized concentration of the frozen SECOND PLAYER_START/L2=10
  listwise probabilities, predicted month-by-month from prior boat-4-win races.
* Thresholds: Feb-Mar confidence quartiles only (Q25/Q50/Q75).
* Rule: highest-confidence quartile N4, then N6, then N8, lowest quartile N10.
* Apr-Jun frozen S+A is the first economic evaluation of that N rule.
* v283 and v284 rankings are evaluated separately; neither is selected/tuned on
  Apr-Jun inside this script.
* Every BET race costs exactly 10,000 yen. Boat-4 loss => payout 0.
* Archived odds are settlement proxy only, not formal prospective OOS.
* Jul/Aug excluded; September not read; v96 is not used for ranking/N selection.
"""
from pathlib import Path
import math
import numpy as np
import pandas as pd

import analyze_v274_4head_opponent_feature_audit as v274
import analyze_v278_4head_opponent_current_exhibition_audit as v278
import analyze_v279_4head_opponent_listwise_rebuild as v279
import analyze_v282_4head_conditional_third as v282
import analyze_v283_4head_conditional_pair_order as v283
import analyze_v284_4head_conditional_third_regime as v284
import analyze_v96_4corner_monthly_walkforward_tiebreak as v96
import analyze_v251_4head_newroi_bridge as v251
from analyze_v205_3head_operational_replay import load_odds

ROOT=Path(__file__).resolve().parent
OUT_CONF=ROOT/'analysis_v286_4head_variable_n_confidence.csv'
OUT_HOLD=ROOT/'analysis_v286_4head_variable_n_holdout.csv'
OUT_MONTH=ROOT/'analysis_v286_4head_variable_n_monthly.csv'
OUT_DETAIL=ROOT/'analysis_v286_4head_variable_n_detail.csv'
OUT_GRID=ROOT/'analysis_v286_4head_variable_n_tune_grid.csv'
SUM=ROOT/'summary_v286_4head_variable_n_dutch.md'
BANK=10000
CAL=('2026-02','2026-03')
HOLD=('2026-04','2026-05','2026-06')
MONTHS=CAL+HOLD


def ii(x,d=0):
    try:return int(float(x))
    except:return d


def hold_portfolio():
    s=pd.read_csv(v274.SEL,dtype={'race_code':str});s['race_code']=s.race_code.astype(str).str.zfill(12)
    for c in ('PRE','POST','a_score'):s[c]=pd.to_numeric(s[c],errors='coerce')
    is_s=s['is_S'].astype(str).str.lower().isin(('true','1'))
    is_a=(~is_s)&(s.PRE>=.18)&(s.POST>=.18)&(s.a_score>=.28)
    q=s[s.month.isin(HOLD)&(is_s|is_a)].copy();q['layer']=np.where(is_s.loc[q.index],'S','A')
    return q[['date','month','race_code','layer','PRE','POST','a_score']].drop_duplicates('race_code')


def actual_map():
    return {str(r.get('race_code','')).zfill(12):(ii(r.get('winner')),ii(r.get('second')),ii(r.get('third')),ii(r.get('valid_result'))) for r in v96.read()}


def keep_specs(d):
    specs=v274.feature_specs(d);out={}
    for n,s in specs.items():
        if n in v279.ABILITY or n in v279.POSITION or n.startswith('pref_pl_') or n.startswith('pref_vh_') or n.startswith('pref_gh_') or n.startswith('suf_st_'):
            out[n]=s
    return out


def allrace_long(d,codes):
    specs=keep_specs(d);recs=[];codes=set(str(x).zfill(12) for x in codes)
    for _,r in d.iterrows():
        code=str(r.get('race_code','')).zfill(12)
        if code not in codes:continue
        ds=str(r.get('date',''));base={'date':ds,'month':ds[:7],'race_code':code}
        for b in v279.BOATS:
            z=dict(base);z['boat']=b
            for n,s in specs.items():z[n]=v274.fval(r,b,s)
            recs.append(z)
    z=pd.DataFrame(recs)
    if z.empty:raise RuntimeError('no all-race rows')
    return v278.add_current(z)


def confidence_predictions(port):
    d,trainz=v279.build_source();d=d[d._date<pd.Timestamp('2026-07-01')].copy();d['date']=d.date.astype(str)
    for c in ('PRE','POST'):d[c]=pd.to_numeric(d[c],errors='coerce')
    cal=d[d.date.str[:7].isin(CAL)&(d.PRE>=.18)&(d.POST>=.18)].copy()
    cal_codes=set(cal.race_code.astype(str).str.zfill(12));hold_codes=set(port.race_code.astype(str))
    targets=cal_codes|hold_codes
    test=allrace_long(d,targets);fs=v279.family_map(trainz)['PLAYER_START'];rec=[]
    for mon in MONTHS:
        tr=trainz[trainz.month<mon].copy();te=test[test.month==mon].copy()
        if tr.race_code.nunique()<v279.MIN_TRAIN or te.empty:continue
        use=v279.good_features(tr,fs);m=v279.ListwiseSoftmax(10.0).fit(tr,use,'y2');te=te.copy();te['s2']=m.score(te)
        for code,g in te.groupby('race_code'):
            if len(g)!=5:continue
            p=v279.probs_within_race(g,'s2');vals=sorted(p.values(),reverse=True);ent=-sum(x*math.log(max(x,1e-12)) for x in vals)/math.log(5.0)
            rec.append({'month':mon,'date':str(g.date.iloc[0]),'race_code':str(code).zfill(12),
                        'p2_concentration':1.0-ent,'p2_top1':vals[0],'p2_top2mass':vals[0]+vals[1],
                        'p2_ratio':vals[0]/max(vals[1],1e-12),'p2_margin':vals[0]-vals[1],
                        'p2_probs':'|'.join(f'{b}:{p[b]:.12g}' for b in v279.BOATS),'nfeat2':len(use),
                        'calibration_domain':int(str(code).zfill(12) in cal_codes)})
    c=pd.DataFrame(rec);c=c.merge(port[['race_code','layer']],on='race_code',how='left');c['layer']=c.layer.fillna('CAL')
    miss=hold_codes-set(c.race_code)
    if miss:raise RuntimeError(f'missing hold confidence rows: {len(miss)}')
    c.to_csv(OUT_CONF,index=False);return c


def load_model_rows(path):
    z=pd.read_csv(path,dtype={'race_code':str});z['race_code']=z.race_code.astype(str).str.zfill(12)
    return {str(r.race_code):r for _,r in z.iterrows()}


def order_v283(r):return v283.order_policy(v282.parse_p2(r.p2),v282.parse_cond(r['cond']),.60,'TOP2XTOP2',1.50)
def order_v284(r):return v284.order_policy(v284.parse_p2(r.p2),v284.parse_cond(r['cond']),.60,'TOP2XTOP2')

def odds_row(oi,code):
    if code not in oi.index:return None
    r=oi.loc[code];return r.iloc[-1] if isinstance(r,pd.DataFrame) else r


def choose_n(x,ths):
    q25,q50,q75=ths
    if x>=q75:return 4
    if x>=q50:return 6
    if x>=q25:return 8
    return 10


def settle(c,port,model,lookup,orderfn,ths,fixed_n=None):
    am=actual_map();od=load_odds();oi=od.set_index('race_code',drop=False) if not od.empty else pd.DataFrame();rows=[]
    h=c[c.race_code.isin(set(port.race_code))].merge(port[['race_code','date','month','layer']],on='race_code',suffixes=('','_p'))
    miss=[0,0,0]
    for _,r in h.iterrows():
        code=str(r.race_code);a=am.get(code)
        if not a or a[3]!=1:miss[0]+=1;continue
        n=int(fixed_n) if fixed_n else choose_n(float(r.p2_concentration),ths)
        hit=0;ret=0.0;comp=np.nan;tickets=''
        if a[0]==4:
            mr=lookup.get(code)
            if mr is None:miss[1]+=1;continue
            odr=odds_row(oi,code)
            if odr is None:miss[2]+=1;continue
            order=orderfn(mr);ts=[f'4-{x}-{y}' for x,y in order[:n]];st=v251.settle('',ts,odr,a)
            if st is None:miss[2]+=1;continue
            hit,ret,comp=st;tickets='|'.join(ts)
        rows.append({'date':r.date_p,'month':r.month_p,'race_code':code,'layer':r.layer_p,'model':model,'n':n,
                     'winner':a[0],'head4_win':int(a[0]==4),'hit':int(hit),'return_yen':float(ret),
                     'profit_yen':float(ret-BANK),'comp_odds':comp,'p2_concentration':float(r.p2_concentration),'tickets':tickets})
    if any(miss):raise RuntimeError(f'settlement missing actual/model/odds={miss}')
    return pd.DataFrame(rows)


def agg(g):
    cost=len(g)*BANK;ret=float(g.return_yen.sum())
    return {'R':len(g),'avg_n':g.n.mean(),'head4_wins':int(g.head4_win.sum()),'hits':int(g.hit.sum()),
            'hit_rate_pct':100*g.hit.mean(),'return_yen':ret,'profit_yen':ret-cost,'roi_pct':100*ret/cost if cost else np.nan,
            'n4':int((g.n==4).sum()),'n6':int((g.n==6).sum()),'n8':int((g.n==8).sum()),'n10':int((g.n==10).sum())}


def main():
    port=hold_portfolio();c=confidence_predictions(port)
    cal=c[(c.month.isin(CAL))&(c.calibration_domain==1)].p2_concentration.dropna()
    if len(cal)<20:raise RuntimeError(f'too few unsupervised calibration rows: {len(cal)}')
    ths=tuple(float(cal.quantile(q)) for q in (.25,.50,.75))
    # Preserve a small audit CSV despite there being no supervised tune grid now.
    pd.DataFrame([{'calibration':'Feb-Mar PRE>=.18 POST>=.18, no result/odds','metric':'p2_concentration','q25':ths[0],'q50':ths[1],'q75':ths[2],'R':len(cal)}]).to_csv(OUT_GRID,index=False)

    p283=load_model_rows(v283.OUT);p284=load_model_rows(v284.OUT)
    var283=settle(c,port,'v283',p283,order_v283,ths);var283['policy']='VARIABLE_v283'
    var284=settle(c,port,'v284',p284,order_v284,ths);var284['policy']='VARIABLE_v284'
    fix283=settle(c,port,'v283',p283,order_v283,ths,4);fix283['policy']='FIXED_v283_N4'
    fix284=settle(c,port,'v284',p284,order_v284,ths,10);fix284['policy']='FIXED_v284_N10'
    detail=pd.concat([var283,var284,fix283,fix284],ignore_index=True);detail.to_csv(OUT_DETAIL,index=False)

    rows=[]
    for pol,g in detail.groupby('policy'):
        rows.append({'scope':'S+A','policy':pol,**agg(g)})
        for layer,gg in g.groupby('layer'):rows.append({'scope':layer,'policy':pol,**agg(gg)})
    H=pd.DataFrame(rows);H.to_csv(OUT_HOLD,index=False)
    mr=[]
    for (pol,mon),g in detail.groupby(['policy','month']):mr.append({'policy':pol,'month':mon,**agg(g)})
    M=pd.DataFrame(mr);M.to_csv(OUT_MONTH,index=False)

    L=['# v286 pre-result variable-N / exact 10k Dutch','',
       '- **No outcome/odds tuning of N.** Feb-Mar S+A/A-score rows do not exist, so the failed supervised-tune design was discarded.',
       '- Calibration domain: Feb-Mar broad head candidates PRE>=.18 and POST>=.18.',
       '- Metric: SECOND PLAYER_START/L2=10 normalized probability concentration = 1 - entropy/log(5).',
       '- Thresholds are calibration-distribution quartiles only; results and odds are not used.',
       '- Rule: >=Q75 N4; >=Q50 N6; >=Q25 N8; otherwise N10.',
       '- Apr-Jun frozen S+A is the first economic evaluation of this N rule.',
       '- v283 and v284 are reported separately; Apr-Jun is not used here to tune/select between them.',
       '- Every BET race costs exactly 10,000 yen; boat-4 loss => payout 0.',
       '- Archived odds are retrospective settlement proxy only, not formal prospective OOS.',
       '- Jul/Aug excluded; September not read; v96 is not used for ranking/N selection.','',
       '## Pre-Apr frozen N rule','',f'- calibration races: **{len(cal)}**',
       f'- Q25/Q50/Q75: **{ths[0]:.6f} / {ths[1]:.6f} / {ths[2]:.6f}**','',
       '## Apr-Jun S+A economics','',
       '|scope|policy|R|avg N|N4/N6/N8/N10|4-head wins|hits|return|profit|ROI|',
       '|---|---|---:|---:|---|---:|---:|---:|---:|---:|']
    for _,r in H.sort_values(['scope','policy']).iterrows():
        L.append(f'|{r.scope}|{r.policy}|{int(r.R)}|{r.avg_n:.2f}|{int(r.n4)}/{int(r.n6)}/{int(r.n8)}/{int(r.n10)}|{int(r.head4_wins)}|{int(r.hits)}|{r.return_yen:.0f}|{r.profit_yen:+.0f}|{r.roi_pct:.2f}%|')
    L += ['','## Apr-Jun monthly S+A','',
          '|policy|month|R|avg N|N4/N6/N8/N10|hits|profit|ROI|','|---|---|---:|---:|---|---:|---:|---:|']
    for _,r in M.sort_values(['policy','month']).iterrows():
        L.append(f'|{r.policy}|{r.month}|{int(r.R)}|{r.avg_n:.2f}|{int(r.n4)}/{int(r.n6)}/{int(r.n8)}/{int(r.n10)}|{int(r.hits)}|{r.profit_yen:+.0f}|{r.roi_pct:.2f}%|')
    L += ['','## Interpretation','',
          '- This is a cleaner test of variable N than optimizing thresholds on Apr-Jun, because the N thresholds were frozen without any Apr-Jun result or odds.',
          '- Do not choose between v283 and v284 as a formal OOS winner from the same Apr-Jun comparison; treat both as development candidates for prospective/live validation.']
    SUM.write_text('\n'.join(L)+'\n',encoding='utf-8');print('\n'.join(L))

if __name__=='__main__':main()
