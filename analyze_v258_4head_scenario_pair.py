#!/usr/bin/env python3
"""v258: 4-head scenario-aware direct ordered-pair model, inspired by 3-head v221.

Research protocol
- Primary evaluation: 2026-02..06 only. Jul/Aug are not used for pair-model improvement evidence.
- For each target month, pair model trains only on earlier valid races won by boat 4.
- All 20 ordered pairs among [1,2,3,5,6] are scored directly (not second+third score addition).
- Features: frozen v93 opponent ability, candidate-vs-candidate interactions, prior1/prior2
  corrected exhibition/original-exhibition state, prior-only player/frame traits, and explicit
  inside-survival / outside-follow topology around attacking boat 4.
- Same-day result is label-only after feature freeze. Historical odds are settlement-only.
- Head gates are frozen diagnostics from v254: PRE>=.28/POST>=.25 and PRE>=.25/POST>=.25.
- Exact 10,000-yen inverse-odds Hamilton Dutch.
"""
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

import analyze_v96_4corner_monthly_walkforward_tiebreak as c4
import analyze_v221_3head_scenario_pair as v221
import analyze_v251_4head_newroi_bridge as v251
from analyze_v205_3head_operational_replay import load_odds

ROOT=Path(__file__).resolve().parent
PRED=ROOT/'analysis_v250_4head_rebuild_baseline.csv'
OUT=ROOT/'analysis_v258_4head_scenario_pair.csv'
SUM=ROOT/'summary_v258_4head_scenario_pair.md'
BANK=10000
BOATS=(1,2,3,5,6)
MONTHS=[f'2026-{m:02d}' for m in range(2,7)]
TOPS=(2,3,5,10)
GATES=((.28,.25,'GATE_123R'),(.25,.25,'GATE_156R'))


def ff(x,d=0.0):
    try:
        y=float(x)
        return y if np.isfinite(y) else d
    except:return d

def ii(x,d=0):
    try:return int(float(x))
    except:return d

def zextra(r,b,k,d=.5):return ff(r.get(f'b{b}_{k}'),d)

def basevec(r,b):
    # v93 frozen opponent features: grade/national/local/motor/waku/nst/direct.
    return [ff(x,.5) for x in c4.rawfeat(r,b)]

def oscore(r,b):return ff(r.get(f'opp_score_b{b}_v93'),0.0)

def pairvec(r,s,t):
    hs=basevec(r,4); xs=basevec(r,s); xt=basevec(r,t)
    x=[]
    x += xs+xt+hs
    x += [a-b for a,b in zip(xs,xt)]
    x += [a-b for a,b in zip(xs,hs)]
    x += [a-b for a,b in zip(xt,hs)]
    ss,tt,hh=oscore(r,s),oscore(r,t),oscore(r,4)
    x += [ss,tt,hh,ss-tt,ss-hh,tt-hh,ss+tt,min(ss,tt),max(ss,tt)]
    # v221-style prior state and player/frame traits for second, third and attacking head.
    hist=['vh_p12_display','vh_p12_overall','vh_p12_turn','vh_p12_straight',
          'vh_delta_display','vh_delta_turn','vh_delta_straight',
          'pl_all_win','pl_all_p2','pl_frame_win','pl_frame_p2','pl_recent_p2']
    for b in (s,t,4):
        for k in hist:x.append(zextra(r,b,k,.5 if 'vh_' in k else 0.0))
    for k in ['vh_p12_display','vh_p12_turn','vh_p12_straight','pl_all_win','pl_frame_p2','pl_recent_p2']:
        a=zextra(r,s,k);b=zextra(r,t,k);h=zextra(r,4,k)
        x += [a-b,a-h,b-h]
    # Explicit 4-attack topology: 1/2/3 may survive inside, 5/6 may follow outside.
    sin=float(s<4); tin=float(t<4); sout=float(s>4); tout=float(t>4)
    x += [sin,tin,sout,tout,sin*tout,sout*tin,sin*tin,sout*tout,
          float(s==3),float(t==3),float(s==5),float(t==5),
          float(abs(s-4)),float(abs(t-4)),float(abs(s-t)),float(s<t)]
    # Race-level attack-strength proxies only as interactions, so they can alter topology preference.
    attack=ff(r.get('score_CORR20_v91'),ff(r.get('score_4corner'),.5))
    x += [attack,attack*sin,attack*tin,attack*sout,attack*tout,
          attack*float(s==3),attack*float(t==3),attack*float(s==5),attack*float(t==5)]
    # Pair identity one-hots.
    x += [float(s==b) for b in BOATS]+[float(t==b) for b in BOATS]
    return x


def valid_head4(r):
    return ii(r.get('valid_result'))==1 and ii(r.get('winner'))==4 and ii(r.get('second')) in BOATS and ii(r.get('third')) in BOATS and ii(r.get('second'))!=ii(r.get('third'))

def fit_pair(train):
    X=[];y=[];nr=0
    for _,r in train.iterrows():
        if not valid_head4(r):continue
        s0,t0=ii(r.get('second')),ii(r.get('third'));nr+=1
        for s in BOATS:
            for t in BOATS:
                if s==t:continue
                X.append(pairvec(r,s,t));y.append(int(s==s0 and t==t0))
    if nr<40:raise RuntimeError(f'pair training too small: {nr}')
    m=Pipeline([('scale',StandardScaler()),('lr',LogisticRegression(C=.35,max_iter=1800,solver='lbfgs'))])
    m.fit(np.asarray(X,float),np.asarray(y,int))
    return m,nr

def new_order(r,m):
    q=[]
    for s in BOATS:
        for t in BOATS:
            if s==t:continue
            p=float(m.predict_proba(np.asarray([pairvec(r,s,t)],float))[0,1])
            q.append((p,s,t))
    q.sort(key=lambda z:(-z[0],z[1],z[2]))
    return [(s,t) for _,s,t in q]

def old_orders(rs):return v251.pair_orders(rs)

def rank_of(order,s,t):
    try:return order.index((s,t))+1
    except:return 0

def settle(order,n,odrow,actual):
    ts=[f'4-{s}-{t}' for s,t in order[:n]]
    return v251.settle('',ts,odrow,actual)

def variable10(order,odrow,actual):
    ch=[]
    for n in range(2,21):
        z=settle(order,n,odrow,actual)
        if z is not None:ch.append((n,*z))
    if not ch:return None
    return min(ch,key=lambda z:(abs(z[3]-10.0),z[0]))

def main():
    rs=c4.read();d=pd.DataFrame(rs)
    if d.empty:raise RuntimeError('empty v93 source')
    if 'date' not in d.columns or 'race_code' not in d.columns:raise RuntimeError('v93 missing date/race_code')
    d['race_code']=d.race_code.astype(str).str.zfill(12);d['_date']=pd.to_datetime(d.date,errors='coerce');d=d[d._date.notna()& (d._date<pd.Timestamp('2026-07-01'))].copy()
    # Reuse the proven v221 prior-history builder. It freezes player/history state before each day's results.
    d=v221.build(d,'date')
    pred=pd.read_csv(PRED,dtype={'race_code':str});pred.race_code=pred.race_code.str.zfill(12)
    pw=pred.pivot_table(index=['date','month','race_code'],columns='variant',values='p4head',aggfunc='last').reset_index()
    pw['date']=pw.date.astype(str);d['date']=d.date.astype(str)
    d=d.merge(pw[['date','race_code','PRE','POST']],on=['date','race_code'],how='left')
    old=old_orders(rs);od=load_odds();oi=od.set_index('race_code',drop=False)
    rows=[]
    for mon in MONTHS:
        first=pd.Timestamp(mon+'-01');tr=d[d._date<first];te=d[d._date.dt.strftime('%Y-%m')==mon]
        m,ntrain=fit_pair(tr)
        for _,r in te.iterrows():
            if ii(r.get('valid_result'))!=1:continue
            code=str(r.race_code).zfill(12);key=(str(r.date),code);oo=old.get(key)
            if not oo:continue
            no=new_order(r,m);s,t=ii(r.get('second')),ii(r.get('third'))
            actual=(ii(r.get('winner')),s,t,ii(r.get('valid_result')))
            rec={'date':r.date,'month':mon,'race_code':code,'PRE':ff(r.get('PRE'),np.nan),'POST':ff(r.get('POST'),np.nan),
                 'head4':int(ii(r.get('winner'))==4),'train_head4':ntrain,
                 'old_rank':rank_of(oo,s,t) if ii(r.get('winner'))==4 else 0,
                 'v258_rank':rank_of(no,s,t) if ii(r.get('winner'))==4 else 0,
                 'old_order':' '.join(f'4-{a}-{b}' for a,b in oo),'v258_order':' '.join(f'4-{a}-{b}' for a,b in no)}
            if code in oi.index:
                o=oi.loc[code];o=o.iloc[-1] if isinstance(o,pd.DataFrame) else o
                for label,order in [('old',oo),('v258',no)]:
                    for npt in TOPS:
                        z=settle(order,npt,o,actual)
                        if z is not None:rec[f'{label}_hit_n{npt}'],rec[f'{label}_ret_n{npt}'],rec[f'{label}_comp_n{npt}']=z
                    z=variable10(order,o,actual)
                    if z is not None:
                        rec[f'{label}_var10_n'],rec[f'{label}_var10_hit'],rec[f'{label}_var10_ret'],rec[f'{label}_var10_comp']=z
            rows.append(rec)
    z=pd.DataFrame(rows);z.to_csv(OUT,index=False)
    L=['# v258 4-head scenario-aware direct ordered-pair','',
       '- 3-head v221 design transferred structurally to boat-4: direct 20-pair logistic ranking, not separate role-score addition.',
       '- Pair training is strict monthly prior-only and uses only prior boat-4 wins.',
       '- Prior1/prior2 corrected exhibition/original-exhibition and player/frame traits are frozen before current-day results.',
       '- Primary evaluation is Feb-Jun only. Jul/Aug are excluded from improvement evidence.',
       '- Historical odds are settlement-only; exact 10,000-yen Hamilton Dutch.',
       '- This is research/model-selection evidence, not production adoption.','']
    for pc,qc,gname in GATES:
        q=z[(z.PRE>=pc)&(z.POST>=qc)].copy();h=q[q.head4==1]
        L += [f'## {gname}: PRE>={pc:.2f} / POST>={qc:.2f}',f'- races: **{len(q)}**, boat4 wins: **{len(h)}**','',
              '|TopN|old coverage|v258 coverage|old hit|v258 hit|old ROI|v258 ROI|','|---:|---:|---:|---:|---:|---:|---:|']
        for npt in TOPS:
            oc=100*((h.old_rank>0)&(h.old_rank<=npt)).mean() if len(h) else 0;nc=100*((h.v258_rank>0)&(h.v258_rank<=npt)).mean() if len(h) else 0
            oh=100*q.get(f'old_hit_n{npt}',pd.Series(dtype=float)).mean() if len(q) else 0;nh=100*q.get(f'v258_hit_n{npt}',pd.Series(dtype=float)).mean() if len(q) else 0
            oroi=100*q.get(f'old_ret_n{npt}',pd.Series(dtype=float)).sum()/(len(q)*BANK) if len(q) else 0; nroi=100*q.get(f'v258_ret_n{npt}',pd.Series(dtype=float)).sum()/(len(q)*BANK) if len(q) else 0
            L.append(f'|{npt}|{oc:.2f}%|{nc:.2f}%|{oh:.2f}%|{nh:.2f}%|{oroi:.2f}%|{nroi:.2f}%|')
        L += ['','### Variable TopN target composite 10.0','|ranker|R|avg N|hit|avg comp|ROI|','|---|---:|---:|---:|---:|---:|']
        for label in ['old','v258']:
            qq=q[q[f'{label}_var10_n'].notna()] if f'{label}_var10_n' in q else q.iloc[:0]
            if len(qq):L.append(f"|{label}|{len(qq)}|{qq[f'{label}_var10_n'].mean():.2f}|{100*qq[f'{label}_var10_hit'].mean():.2f}%|{qq[f'{label}_var10_comp'].mean():.3f}|{100*qq[f'{label}_var10_ret'].sum()/(len(qq)*BANK):.2f}%|")
        L += ['','### Monthly variable10','|month|ranker|R|hit|ROI|','|---|---|---:|---:|---:|']
        for mon in MONTHS:
            qm=q[q.month==mon]
            for label in ['old','v258']:
                if f'{label}_var10_n' not in qm:continue
                qq=qm[qm[f'{label}_var10_n'].notna()]
                if len(qq):L.append(f"|{mon}|{label}|{len(qq)}|{100*qq[f'{label}_var10_hit'].mean():.2f}%|{100*qq[f'{label}_var10_ret'].sum()/(len(qq)*BANK):.2f}%|")
        L.append('')
    SUM.write_text('\n'.join(L)+'\n',encoding='utf-8');print('\n'.join(L))

if __name__=='__main__':main()
