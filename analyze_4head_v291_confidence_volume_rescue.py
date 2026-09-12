#!/usr/bin/env python3
"""Leakage-safe confidence/variable-N rescue research for HEAD4_V291_COMP7.

Key point: analysis_v283_* prediction rows are outcome-conditioned boat-4-win
rows, so they MUST NOT be used as a candidate-confidence table.  This script
instead reuses v287's outcome-independent all-portfolio inference path to score
all 100 frozen S+A candidates month-walk-forward, regardless of eventual winner.

BASE remains immutable: v283 N4, composite>=7.0.  Research only adds BASE-PASS
races. Candidate rule inputs are frozen v283 probabilities/order and odds only.
Jul/Aug/Sep outcomes are rejected/not read. No v96 input is used.
"""
from pathlib import Path
import json, math
import numpy as np
import pandas as pd

import analyze_v279_4head_opponent_listwise_rebuild as v279
import analyze_v282_4head_conditional_third as v282
import analyze_v283_4head_conditional_pair_order as v283
import analyze_v286_4head_variable_n_dutch as v286
import analyze_v287_4head_composite_odds_variable_n as v287

ROOT=Path(__file__).resolve().parent
SRC=ROOT/'analysis_v288_4head_composite_odds_alln_detail.csv'
OUTCONF=ROOT/'analysis_4head_v291_confidence_all_candidates.csv'
OUT=ROOT/'analysis_4head_v291_confidence_rescue_grid.csv'
MONTH=ROOT/'analysis_4head_v291_confidence_rescue_monthly.csv'
LOMO=ROOT/'analysis_4head_v291_confidence_rescue_lomo.csv'
SUM=ROOT/'summary_4head_v291_confidence_volume_rescue.md'
CAND=ROOT/'head4_v291_confidence_rescue_candidate.json'
MONTHS=('2026-04','2026-05','2026-06');BANK=10000
FLOORS=(4.5,5.0,5.5,6.0,6.5,7.0)
FIXNS=(2,3,4,5,6,8,10)
P2R=(1.25,1.50,1.75,2.00)
JM4=(.30,.35,.40,.45,.50,.55)
ENT=(.70,.75,.80,.85,.90)
MASST=(.45,.55,.65,.75)


def metric(g):
    if len(g)==0:return {'R':0,'return_yen':0.,'profit_yen':0.,'roi_pct':np.nan,'head_rate_pct':np.nan,'hit_rate_pct':np.nan}
    ret=float(g.return_yen.sum());cost=len(g)*BANK
    return {'R':len(g),'return_yen':ret,'profit_yen':ret-cost,'roi_pct':100*ret/cost,
            'head_rate_pct':100*float(g.head4_win.mean()),'hit_rate_pct':100*float(g.hit.mean())}


def confidence_table():
    port=v286.hold_portfolio().copy();port['race_code']=port.race_code.astype(str).str.zfill(12)
    if set(port.month.astype(str).unique())!=set(MONTHS) or port.race_code.nunique()!=100:
        raise RuntimeError('expected frozen Apr-Jun 100-race portfolio')
    trainz,base=v282.prep();trainpairs,fams=v282.make_pairs(trainz,base)
    d,_=v279.build_source();d=d[d._date<pd.Timestamp('2026-07-01')].copy();d['date']=d.date.astype(str)
    test,testpairs=v287.test_long_for_portfolio(d,port,base)
    rows=[]
    for mon in MONTHS:
        p2all=v287.second_prob_for_month(trainz,test,base,mon)
        pcall=v287.cond283_for_month(trainpairs,testpairs,fams,mon)
        codes=set(port.loc[port.month==mon,'race_code'].astype(str))
        for code in sorted(codes):
            if code not in p2all or code not in pcall:raise RuntimeError(f'missing all-candidate inference {code}')
            p2=p2all[code];pc=pcall[code]
            sr=sorted(v279.BOATS,key=lambda b:(-p2[b],b));p1,p2v=p2[sr[0]],p2[sr[1]]
            order=v283.order_policy(p2,pc,.60,'TOP2XTOP2',1.50)
            weights={(s,t):(max(p2[s],1e-12)**.60)*(max(pc[(s,t)],1e-12)**.40)
                     for s in v279.BOATS for t in v279.BOATS if s!=t}
            den=sum(weights.values());pn={k:v/den for k,v in weights.items()}
            cum={};z=0.
            for i,pair in enumerate(order,1):z+=pn[pair];cum[i]=z
            probs=np.array(list(pn.values()),float);ent=-float(np.sum(probs*np.log(np.maximum(probs,1e-15))))/math.log(20)
            cr={s:sorted([t for t in v279.BOATS if t!=s],key=lambda t:(-pc[(s,t)],t)) for s in v279.BOATS}
            cond_rat=[]
            for s in sr[:2]:
                a,b=cr[s][:2];cond_rat.append(pc[(s,a)]/max(pc[(s,b)],1e-12))
            rows.append({'month':mon,'race_code':code,'p2_top1':p1,'p2_top2':p2v,'p2_ratio':p1/max(p2v,1e-12),
                         'p2_top2_mass':p1+p2v,'joint_mass2':cum[2],'joint_mass4':cum[4],'joint_mass6':cum[6],
                         'joint_mass8':cum[8],'joint_mass10':cum[10],'joint_entropy':ent,
                         'cond_ratio_mean_top2second':float(np.mean(cond_rat)),
                         'full_order':'|'.join(f'4-{s}-{t}' for s,t in order)})
    C=pd.DataFrame(rows)
    if C.race_code.nunique()!=100 or len(C)!=100:raise RuntimeError('confidence coverage must be 100/100')
    C.to_csv(OUTCONF,index=False);return port,C


def source_alln():
    q=pd.read_csv(SRC,dtype={'race_code':str});q['race_code']=q.race_code.astype(str).str.zfill(12)
    if set(q.month.astype(str).unique())!=set(MONTHS) or q.race_code.nunique()!=100 or len(q)!=1900:
        raise RuntimeError('all-N source must be Apr-Jun 100 x 19 only')
    return q


def base(q,scope,months=MONTHS):
    z=q[(q.month.isin(months))&(q.n==4)&(q.comp_odds>=7.0)]
    if scope=='S':z=z[z.layer=='S']
    return z.copy()


def rescue_universe(q,C,scope,months=MONTHS):
    z=q[q.month.isin(months)].copy()
    if scope=='S':z=z[z.layer=='S']
    bc=set(base(q,scope,months).race_code)
    z=z[~z.race_code.isin(bc)].merge(C,on=['month','race_code'],how='left',validate='many_to_one')
    if z[['p2_ratio','joint_mass4','joint_entropy']].isna().any().any():raise RuntimeError('missing confidence join')
    return z


def one_per_race(z,family,nparam,floor,conf):
    # All families return zero or one live-computable selected N per race.
    if family=='P2R_FIXED':
        x=z[(z.n==int(nparam))&(z.comp_odds>=floor)&(z.p2_ratio>=conf)]
    elif family=='JM4_FIXED':
        x=z[(z.n==int(nparam))&(z.comp_odds>=floor)&(z.joint_mass4>=conf)]
    elif family=='ENT_FIXED':
        x=z[(z.n==int(nparam))&(z.comp_odds>=floor)&(z.joint_entropy<=conf)]
    elif family=='MASS_TARGET':
        # Smallest N in 2..10 whose frozen model prefix reaches target mass.
        rec=[]
        for code,g in z.groupby('race_code'):
            r0=g.iloc[0];chosen=None
            for n in range(2,11):
                mass=float(r0[f'joint_mass{n}']) if f'joint_mass{n}' in r0 else np.nan
                # only even masses are stored; interpolate by checking true order
                if n not in (2,4,6,8,10):continue
                if mass>=conf:
                    h=g[g.n==n]
                    if len(h) and float(h.iloc[0].comp_odds)>=floor:chosen=h.iloc[0]
                    break
            if chosen is not None:rec.append(chosen)
        x=pd.DataFrame(rec,columns=z.columns) if rec else z.iloc[0:0]
    else:raise ValueError(family)
    if x.race_code.duplicated().any():raise RuntimeError('duplicate rescue selection')
    return x.copy()


def grid_defs():
    g=[]
    for n in FIXNS:
        for fl in FLOORS:
            for c in P2R:g.append(('P2R_FIXED',n,fl,c))
            for c in JM4:g.append(('JM4_FIXED',n,fl,c))
            for c in ENT:g.append(('ENT_FIXED',n,fl,c))
    for fl in FLOORS:
        for c in MASST:g.append(('MASS_TARGET',10,fl,c))
    return g


def eval_rule(q,C,scope,f,n,fl,c,months=MONTHS):
    b=base(q,scope,months);u=rescue_universe(q,C,scope,months);r=one_per_race(u,f,n,fl,c);comb=pd.concat([b,r],ignore_index=True)
    ba,ra,ca=metric(b),metric(r),metric(comb);mr=[]
    for m in months:
        bm,rm,cm=b[b.month==m],r[r.month==m],comb[comb.month==m]
        xb,xr,xc=metric(bm),metric(rm),metric(cm)
        mr.append({'scope':scope,'family':f,'nparam':n,'floor':fl,'conf':c,'month':m,
                   'base_R':xb['R'],'base_roi_pct':xb['roi_pct'],'added_R':xr['R'],'added_return_yen':xr['return_yen'],
                   'added_profit_yen':xr['profit_yen'],'added_roi_pct':xr['roi_pct'],'R':xc['R'],'return_yen':xc['return_yen'],
                   'profit_yen':xc['profit_yen'],'roi_pct':xc['roi_pct']})
    md=pd.DataFrame(mr);valid=md[md.added_R>0]
    s={'scope':scope,'family':f,'nparam':int(n),'floor':float(fl),'conf':float(c),
       'base_R':ba['R'],'base_roi_pct':ba['roi_pct'],'added_R':ra['R'],'added_roi_pct':ra['roi_pct'],
       'added_profit_yen':ra['profit_yen'],'R':ca['R'],'roi_pct':ca['roi_pct'],'profit_yen':ca['profit_yen'],
       'head_rate_pct':ca['head_rate_pct'],'hit_rate_pct':ca['hit_rate_pct'],
       'min_added_month_R':int(md.added_R.min()),
       'min_added_month_roi_pct':float(valid.added_roi_pct.min()) if len(valid) else np.nan,
       'min_combined_month_roi_pct':float(md.roi_pct.min())}
    return s,mr


def choose(tab,scope):
    common=(tab.added_R>=9)&(tab.min_added_month_R>=2)
    if scope=='S+A':
        tiers=[('STRICT',common&(tab.added_roi_pct>=140)&(tab.min_added_month_roi_pct>=120)&(tab.min_combined_month_roi_pct>=150)),
               ('BALANCED',common&(tab.added_roi_pct>=125)&(tab.min_added_month_roi_pct>=110)&(tab.min_combined_month_roi_pct>=140)),
               ('POSITIVE',common&(tab.added_roi_pct>=115)&(tab.min_added_month_roi_pct>=100)&(tab.min_combined_month_roi_pct>=130))]
    else:
        tiers=[('STRICT',common&(tab.added_roi_pct>=130)&(tab.min_added_month_roi_pct>=110)&(tab.min_combined_month_roi_pct>=120)),
               ('POSITIVE',common&(tab.added_roi_pct>=115)&(tab.min_added_month_roi_pct>=100)&(tab.min_combined_month_roi_pct>=110))]
    for name,mask in tiers:
        z=tab[mask].sort_values(['R','min_added_month_roi_pct','added_roi_pct'],ascending=False)
        if len(z):return name,z.iloc[0]
    return 'NO_SAFE_CANDIDATE',None


def lomo(q,C,scope,defs):
    out=[]
    for hold in MONTHS:
        train=tuple(m for m in MONTHS if m!=hold);rec=[]
        for f,n,fl,c in defs:rec.append(eval_rule(q,C,scope,f,n,fl,c,train)[0])
        tier,ch=choose(pd.DataFrame(rec),scope)
        if ch is None:out.append({'scope':scope,'holdout_month':hold,'status':'NO_TRAIN_CANDIDATE'});continue
        s,_=eval_rule(q,C,scope,str(ch.family),int(ch.nparam),float(ch.floor),float(ch.conf),(hold,))
        out.append({'scope':scope,'holdout_month':hold,'status':'OK','train_tier':tier,'family':ch.family,
                    'nparam':int(ch.nparam),'floor':float(ch.floor),'conf':float(ch.conf),'hold_added_R':int(s['added_R']),
                    'hold_added_roi_pct':float(s['added_roi_pct']) if pd.notna(s['added_roi_pct']) else np.nan,
                    'hold_R':int(s['R']),'hold_roi_pct':float(s['roi_pct'])})
    return out


def main():
    _,C=confidence_table();q=source_alln();defs=grid_defs();allr=[];allm=[];selected={};lrows=[]
    for scope in ('S+A','S'):
        rec=[]
        for f,n,fl,c in defs:
            s,m=eval_rule(q,C,scope,f,n,fl,c);rec.append(s);allr.append(s);allm.extend(m)
        tab=pd.DataFrame(rec);tier,ch=choose(tab,scope);selected[scope]=(tier,ch);lrows.extend(lomo(q,C,scope,defs))
    A=pd.DataFrame(allr);M=pd.DataFrame(allm);L=pd.DataFrame(lrows)
    A.to_csv(OUT,index=False);M.to_csv(MONTH,index=False);L.to_csv(LOMO,index=False)
    payload={'schema':'head4_v291_confidence_rescue_research_v1','all_candidate_inference':True,
             'outcome_conditioned_v283_csv_used_as_confidence':False,'jul_aug_outcomes_used':False,'september_outcomes_used':False,
             'v96_used':False,'base':{'policy':'HEAD4_V291_COMP7','immutable':True},'scopes':{}}
    lines=['# HEAD4 v291 leakage-safe confidence / variable-N rescue','',
      '- Confidence is recomputed for all 100 candidates through v287 outcome-independent monthly inference.',
      '- The outcome-conditioned v283 prediction CSV is explicitly NOT used as a confidence source.',
      '- BASE HEAD4_V291_COMP7 is immutable; rescue only acts on BASE PASS races.',
      '- Inputs are frozen v283 p2/conditional-third/order + archived odds only. No v96. Jul/Aug/Sep outcomes excluded.','']
    for scope in ('S+A','S'):
        tier,ch=selected[scope];lines += [f'## {scope}','',f'- selection tier: **{tier}**'];d={'selection_tier':tier}
        if ch is not None:
            d['candidate']={'family':str(ch.family),'nparam':int(ch.nparam),'floor':float(ch.floor),'conf':float(ch.conf),
              'added_R':int(ch.added_R),'added_roi_pct':float(ch.added_roi_pct),'combined_R':int(ch.R),
              'combined_roi_pct':float(ch.roi_pct),'min_added_month_roi_pct':float(ch.min_added_month_roi_pct),
              'min_combined_month_roi_pct':float(ch.min_combined_month_roi_pct),'status':'RESEARCH_CANDIDATE_NOT_FROZEN'}
            lines += [f'- rule: **{ch.family}, N={int(ch.nparam)}, floor={ch.floor:.1f}, conf={ch.conf:.2f}**',
                      f'- rescue standalone: **{int(ch.added_R)}R / ROI {ch.added_roi_pct:.2f}% / monthly floor {ch.min_added_month_roi_pct:.2f}%**',
                      f'- combined: **{int(ch.R)}R / ROI {ch.roi_pct:.2f}% / monthly floor {ch.min_combined_month_roi_pct:.2f}%**','',
                      '|month|added R|added ROI|combined R|combined ROI|','|---|---:|---:|---:|---:|']
            mm=M[(M.scope==scope)&(M.family==ch.family)&(M.nparam==ch.nparam)&(M.floor==ch.floor)&(M.conf==ch.conf)].sort_values('month')
            for _,r in mm.iterrows():lines.append(f'|{r.month}|{int(r.added_R)}|{r.added_roi_pct:.2f}%|{int(r.R)}|{r.roi_pct:.2f}%|')
        payload['scopes'][scope]=d
        lines += ['','### LOMO','','|holdout|train rule|added R|added ROI|combined ROI|','|---|---|---:|---:|---:|']
        for _,r in L[L.scope==scope].iterrows():
            if r.status!='OK':lines.append(f'|{r.holdout_month}|NO_TRAIN_CANDIDATE|-|-|-|')
            else:lines.append(f'|{r.holdout_month}|{r.family} N{int(r.nparam)} f{r.floor:.1f} c{r.conf:.2f}|{int(r.hold_added_R)}|{r.hold_added_roi_pct:.2f}%|{r.hold_roi_pct:.2f}%|')
        lines.append('')
    for scope in ('S+A','S'):
        g=L[L.scope==scope];ok=bool(len(g)==3 and g.status.eq('OK').all() and (g.hold_added_R>=1).all() and (g.hold_added_roi_pct>=100).all())
        payload['scopes'][scope]['lomo_all_holdout_rescue_profitable']=ok
    lines += ['## Promotion guard','',
      '- A candidate is not production until its LOMO rescue is profitable in all held-out months and a new version is frozen.',
      '- S is the only immediately operational head layer; S+A still requires the frozen A_SCORE LIVE-scale mapping.',
      '- Formal OOS starts only after immutable official pre-deadline odds capture + audit persistence are wired.']
    CAND.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    SUM.write_text('\n'.join(lines)+'\n',encoding='utf-8');print('\n'.join(lines))

if __name__=='__main__':main()
