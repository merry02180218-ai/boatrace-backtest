#!/usr/bin/env python3
"""v296: clean 1-head operational rebuild after v295 exposed meeting-slot leakage.

Never uses meet_st_strength / meet_win / meet_p2.  Tests whether genuinely prior-only
player and exhibition history can recover >=90% realized head precision on Feb-Jun WF.
Jul/Aug excluded; September outcomes unread.
"""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import date,timedelta
from pathlib import Path
import numpy as np
import pandas as pd

import analyze_v294_1head_verified_prepost_research as v294
import analyze_v293_1head_direct_history_research as v293
from backtest import rows
from backtest_v51_lane_corrected_tickets import ii

ROOT=Path(__file__).resolve().parent
PREFIX=ROOT/'analysis_v296_1head_clean_operational'
SUMMARY=ROOT/'summary_v296_1head_clean_operational.md'
TEST_MONTHS=list(v294.TEST_MONTHS)
Q=[.90,.95,.975]
SAFE=['grade','wr','local','motor','nst_strength','f_safety']


def clean_manifest(d):
    base=[]
    for k in SAFE:
        base += [f'b{b}_{k}' for b in range(1,7) if f'b{b}_{k}' in d]
        base += [c for c in d if c.startswith(f'rel_{k}_')]
        if f'attack23_{k}' in d:base.append(f'attack23_{k}')
    player=[c for c in d if ('_pl_' in c or c.startswith('rel_pl_'))]
    prior=[c for c in d if ('_vh_' in c or '_gh_' in c or c.startswith('rel_vh_') or c.startswith('rel_gh_'))]
    fam={
      'CLEAN_STATIC6':base,
      'CLEAN_STATIC6_PLAYER':base+player,
      'CLEAN_STATIC6_PRIOR_EX':base+prior,
      'CLEAN_STATIC6_PLAYER_PRIOR_EX':base+player+prior,
    }
    out={k:v293.available(d,list(dict.fromkeys(v)),.55) for k,v in fam.items()}
    for k,fs in out.items():
        leak=[c for c in fs if 'meet_' in c]
        if leak:raise RuntimeError(f'meeting leak in {k}: {leak[:5]}')
    return out


def coherent_self_audit():
    days=[]
    for mon in TEST_MONTHS:
        a=pd.Timestamp(mon+'-01');b=a+pd.offsets.MonthBegin(1);d=a.date()
        while d<b.date():days.append(d);d+=timedelta(days=1)
    def one(d):return d,rows(f"data/programs/race_cards/{d.strftime('%Y/%m/%d')}.csv")
    fetched=[]
    with ThreadPoolExecutor(max_workers=10) as ex:
        fs=[ex.submit(one,d) for d in days]
        for j,f in enumerate(as_completed(fs),1):
            fetched.append(f.result())
            if j%40==0:print('self audit fetch',j,'/',len(days),flush=True)
    out=[]
    for d,cards in fetched:
        races=coherent=all6=0
        for card in cards:
            rno=ii(str(card.get('レース回','')).replace('R',''),0)
            if not rno:continue
            races+=1;best=0;best_result=0
            for dd in range(1,8):
                matched=matched_result=0
                for boat in range(1,7):
                    ok=res=False
                    for ss in (1,2):
                        pre=f'艇{boat}_節D{dd}走{ss}_'
                        rr=ii(card.get(pre+'R番号'),0);frame=ii(card.get(pre+'枠'),0)
                        if rr==rno and frame==boat:
                            if str(card.get(pre+'ST','') or '').strip():ok=True
                            if str(card.get(pre+'着順','') or '').strip():res=True
                    matched+=int(ok or res);matched_result+=int(res)
                best=max(best,matched);best_result=max(best_result,matched_result)
            coherent+=int(best>=4);all6+=int(best_result==6)
        out.append({'date':str(d),'month':d.strftime('%Y-%m'),'races':races,'coherent_self_slot_ge4':coherent,'all6_self_result_slot':all6})
    return pd.DataFrame(out)


def run(d,fams):
    preds=[];folds=[]
    for name,fs0 in fams.items():
        for tm in TEST_MONTHS:
            tr=d[d.month<tm].copy();te=d[d.month==tm].copy();fs=v293.available(tr,fs0,.55)
            oo=v293.oof('hgb',fs,tr);cal=v293.calfit(oo);oop=v293.cal(cal,oo.p)
            raw=v293.fitpred('hgb',fs,tr,te);pc=v293.cal(cal,raw)
            z=te[['date','month','race_code','venue','race','head_hit']].copy();z['variant']=name;z['test_month']=tm;z['p_cal']=pc
            for q in Q:
                cut=float(np.quantile(oop,q));z[f'q{q}_sel']=(pc>=cut).astype(int);z[f'q{q}_cut']=cut
            preds.append(z);folds.append({'variant':name,'month':tm,'features':len(fs),'train':len(tr),'test':len(te),'oof':len(oo)})
            print(name,tm,len(fs),len(te),flush=True)
    return pd.concat(preds,ignore_index=True),pd.DataFrame(folds)


def monthly(p):
    a=[]
    for (v,m),g in p.groupby(['variant','test_month']):
        for q in Q:
            s=g[g[f'q{q}_sel']==1];a.append({'variant':v,'month':m,'selector':f'OOF_q{q:.3f}','cut':float(g[f'q{q}_cut'].iloc[0]),'R':len(s),'heads':int(s.head_hit.sum()),'head_rate':float(s.head_hit.mean()) if len(s) else np.nan})
    return pd.DataFrame(a)


def pooled(m):
    a=[]
    for (v,s),g in m.groupby(['variant','selector']):
        R=int(g.R.sum());H=int(g.heads.sum());valid=g[g.R>0]
        a.append({'variant':v,'selector':s,'R':R,'heads':H,'head_rate':H/R if R else np.nan,'months_with_bets':int((g.R>0).sum()),'worst_month':float(valid.head_rate.min()) if len(valid) else np.nan,'min_month_R':int(valid.R.min()) if len(valid) else 0})
    return pd.DataFrame(a)


def summary(selfa,fams,m,pool):
    sa=selfa.groupby('month')[['races','coherent_self_slot_ge4','all6_self_result_slot']].sum().reset_index()
    L=['# v296 clean operational 1HEAD rebuild','',
       '- v295-contaminated meeting-slot features (`meet_st_strength`, `meet_win`, `meet_p2`) are completely excluded.',
       '- Jul/Aug excluded from research; September outcomes unread.','- Feb-Jun expanding walk-forward; selection thresholds from training temporal OOF only.','',
       '## Current-race self-slot audit','|month|R|coherent current-race-like slot >=4 boats|all 6 result slots|','|---|---:|---:|---:|']
    for _,r in sa.iterrows():L.append(f'|{r.month}|{int(r.races)}|{int(r.coherent_self_slot_ge4)}|{int(r.all6_self_result_slot)}|')
    L += ['','## Clean feature families','|variant|features|operational requirement|','|---|---:|---|']
    req={'CLEAN_STATIC6':'morning race-card only','CLEAN_STATIC6_PLAYER':'race-card + maintained prior-day result state','CLEAN_STATIC6_PRIOR_EX':'race-card + maintained prior-day exhibition state','CLEAN_STATIC6_PLAYER_PRIOR_EX':'race-card + both prior-day states'}
    for v,fs in fams.items():L.append(f'|{v}|{len(fs)}|{req[v]}|')
    L += ['','## Monthly OOF-tail precision','|variant|month|selector|R|head rate|cut|','|---|---|---|---:|---:|---:|']
    for _,r in m.iterrows():L.append(f"|{r.variant}|{r.month}|{r.selector}|{int(r.R)}|{('-' if pd.isna(r.head_rate) else f'{100*r.head_rate:.2f}%')}|{r.cut:.4f}|")
    L += ['','## Pooled / stability','|variant|selector|R|head rate|months with bets|worst month|min month R|','|---|---|---:|---:|---:|---:|---:|']
    for _,r in pool.sort_values(['worst_month','head_rate','R'],ascending=False).iterrows():L.append(f"|{r.variant}|{r.selector}|{int(r.R)}|{100*r.head_rate:.2f}%|{int(r.months_with_bets)}|{100*r.worst_month:.2f}%|{int(r.min_month_R)}|")
    good=pool[(pool.months_with_bets==5)&(pool.worst_month>=.90)&(pool.R>=100)]
    L += ['','## Operational decision']
    if good.empty:L.append('- **No clean rule currently qualifies for production at the requested >=90% monthly floor.**')
    else:
        L.append('- Clean candidates meeting 5/5 months, worst-month >=90%, pooled R>=100 exist:')
        for _,r in good.iterrows():L.append(f"  - {r.variant} / {r.selector}: R={int(r.R)}, rate={100*r.head_rate:.2f}%, worst={100*r.worst_month:.2f}%")
    L += ['- Do not use v294 fixed p_cal>=0.98 in production; its scale drifted and June had no selections.',
          '- A production candidate must be frozen and replayed prospectively result-blind on September input snapshots before any outcome inspection.',
          '- Prefer the simplest qualifying clean family; prior-exhibition/player state is only justified if it materially improves the all-month floor.']
    return '\n'.join(L)+'\n'


def main():
    selfa=coherent_self_audit();selfa.to_csv(str(PREFIX)+'_self_audit.csv',index=False,encoding='utf-8-sig')
    d,a=v294.freeze_true_pre();d=v294.add_prior_history(d);d=v294.add_rel(d)
    print('features frozen; settlement now',flush=True);d=v294.settle_after_freeze(d);d=d[d.valid_result==1].copy()
    fams=clean_manifest(d);pred,folds=run(d,fams);m=monthly(pred);pool=pooled(m)
    folds.to_csv(str(PREFIX)+'_folds.csv',index=False,encoding='utf-8-sig');m.to_csv(str(PREFIX)+'_monthly.csv',index=False,encoding='utf-8-sig');pool.to_csv(str(PREFIX)+'_pooled.csv',index=False,encoding='utf-8-sig')
    SUMMARY.write_text(summary(selfa,fams,m,pool),encoding='utf-8');print(SUMMARY.read_text(),flush=True)

if __name__=='__main__':main()
