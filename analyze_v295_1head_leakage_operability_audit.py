#!/usr/bin/env python3
"""v295: audit the suspicious v294 1-head PRE tail and operational feasibility.

Hard rules
- No Jul/Aug model selection/evaluation.
- No September outcomes are read.
- Feb-Jun expanding walk-forward only.
- Historical race-card current-day/future meeting slots are explicitly audited.
- Main diagnostic is monthly OOF-fixed tail precision, not pooled fixed p>=0.98 alone.
- Research only; no production adoption.
"""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

import analyze_v294_1head_verified_prepost_research as v294
import analyze_v293_1head_direct_history_research as v293
from backtest import rows

ROOT=Path(__file__).resolve().parent
PREFIX=ROOT/'analysis_v295_1head_leakage_operability'
SUMMARY=ROOT/'summary_v295_1head_leakage_operability.md'
TEST_MONTHS=list(v294.TEST_MONTHS)
DAYNUM={'初日':1,'２日目':2,'３日目':3,'４日目':4,'５日目':5,'６日目':6,'７日目':7,'８日目':8,'９日目':9}
Q_LEVELS=[.90,.95,.975]


def norm_code(x):
    s=str(x or '').strip()
    if s.endswith('.0') and s[:-2].isdigit():s=s[:-2]
    return s.zfill(12) if s.isdigit() else ''


def bycode(rs):
    return {norm_code(r.get('レースコード','')):r for r in rs if norm_code(r.get('レースコード',''))}


def slot_day_audit():
    days=[]
    for mon in TEST_MONTHS:
        first=pd.Timestamp(mon+'-01'); nxt=first+pd.offsets.MonthBegin(1)
        d=first.date()
        while d<nxt.date():days.append(d);d+=timedelta(days=1)
    def one(d):
        y=d.strftime('%Y/%m/%d')
        return d,rows(f'data/programs/race_cards/{y}.csv'),rows(f'data/programs/title/{y}.csv')
    fetched=[]
    with ThreadPoolExecutor(max_workers=10) as ex:
        fs=[ex.submit(one,d) for d in days]
        for j,f in enumerate(as_completed(fs),1):
            fetched.append(f.result())
            if j%40==0:print('slot audit fetch',j,'/',len(days),flush=True)
    out=[]
    for d,cards,titles in sorted(fetched,key=lambda z:z[0]):
        tm=bycode(titles); labelled=bad=cur=cur_result=cur_st=future=0
        for card in cards:
            code=norm_code(card.get('レースコード','')); t=tm.get(code,{})
            dn=DAYNUM.get(str(t.get('日次','')).strip())
            if not dn or dn>7:continue
            labelled+=1; row_bad=False;row_cur=False;row_res=False;row_st=False;row_fut=False
            for b in range(1,7):
                for dd in range(dn,8):
                    vals=[]
                    for ss in (1,2):
                        pre=f'艇{b}_節D{dd}走{ss}_'
                        vals += [str(card.get(pre+'R番号','') or '').strip(),str(card.get(pre+'進入','') or '').strip(),str(card.get(pre+'枠','') or '').strip(),str(card.get(pre+'ST','') or '').strip(),str(card.get(pre+'着順','') or '').strip()]
                        if dd==dn:
                            if str(card.get(pre+'ST','') or '').strip():row_st=True
                            if str(card.get(pre+'着順','') or '').strip():row_res=True
                    if any(vals):
                        row_bad=True
                        if dd==dn:row_cur=True
                        if dd>dn:row_fut=True
            bad+=int(row_bad);cur+=int(row_cur);cur_result+=int(row_res);cur_st+=int(row_st);future+=int(row_fut)
        out.append({'date':str(d),'month':d.strftime('%Y-%m'),'labelled_races':labelled,
                    'current_or_future_nonempty_races':bad,'current_day_nonempty_races':cur,
                    'current_day_result_nonempty_races':cur_result,'current_day_st_nonempty_races':cur_st,
                    'future_day_nonempty_races':future})
    z=pd.DataFrame(out)
    return z


def group_cols(d,keys):
    cols=[]
    for k in keys:
        cols += [f'b{b}_{k}' for b in range(1,7) if f'b{b}_{k}' in d.columns]
        cols += [c for c in d.columns if c.startswith(f'rel_{k}_')]
        c=f'attack23_{k}'
        if c in d.columns:cols.append(c)
    return list(dict.fromkeys(cols))


def family_manifest(d):
    safe6=['grade','wr','local','motor','nst_strength','f_safety']
    meeting=['meet_st_strength','meet_win','meet_p2']
    static6=group_cols(d,safe6)
    static9=group_cols(d,safe6+meeting)
    player=[c for c in d.columns if ('_pl_' in c or c.startswith('rel_pl_'))]
    prior=[c for c in d.columns if ('_vh_' in c or '_gh_' in c or c.startswith('rel_vh_') or c.startswith('rel_gh_'))]
    fam={
      'HGB_STATIC6':v293.available(d,static6,.55),
      'HGB_STATIC9':v293.available(d,static9,.55),
      'HGB_STATIC9_PLAYER':v293.available(d,static9+player,.55),
      'HGB_FULL_PRE':v293.available(d,static9+player+prior,.55),
    }
    return fam


def run_ablation(d,fams):
    preds=[];folds=[]
    for name,fs0 in fams.items():
        for tm in TEST_MONTHS:
            tr=d[d.month<tm].copy();te=d[d.month==tm].copy();fs=v293.available(tr,fs0,.55)
            if len(fs)<10 or te.empty:raise RuntimeError(f'bad fold {name} {tm} f={len(fs)} te={len(te)}')
            oo=v293.oof('hgb',fs,tr);cc=v293.calfit(oo);oop=v293.cal(cc,oo.p)
            raw=v293.fitpred('hgb',fs,tr,te);pc=v293.cal(cc,raw)
            q=te[['date','month','race_code','venue','race','head_hit']].copy();q['variant']=name;q['test_month']=tm;q['p_raw']=raw;q['p_cal']=pc
            for lev in Q_LEVELS:
                cut=float(np.quantile(oop,lev));q[f'q{lev}_sel']=(pc>=cut).astype(int);q[f'q{lev}_cut']=cut
            preds.append(q);folds.append({'variant':name,'month':tm,'features':len(fs),'train':len(tr),'test':len(te),'oof':len(oo)})
            print(name,tm,'features',len(fs),'train',len(tr),'test',len(te),flush=True)
    return pd.concat(preds,ignore_index=True),pd.DataFrame(folds)


def tail_monthly(p):
    out=[]
    for (name,tm),g in p.groupby(['variant','test_month']):
        for lev in Q_LEVELS:
            s=g[g[f'q{lev}_sel']==1]
            out.append({'variant':name,'month':tm,'selector':f'OOF_q{lev:.3f}','cut':float(g[f'q{lev}_cut'].iloc[0]),
                        'R':len(s),'heads':int(s.head_hit.sum()),'head_rate':float(s.head_hit.mean()) if len(s) else np.nan})
        for c in [.90,.94,.95,.96,.97,.98]:
            s=g[g.p_cal>=c]
            out.append({'variant':name,'month':tm,'selector':f'p_cal>={c:.2f}','cut':c,
                        'R':len(s),'heads':int(s.head_hit.sum()),'head_rate':float(s.head_hit.mean()) if len(s) else np.nan})
    return pd.DataFrame(out)


def univariate_screen(d,features):
    z=d[d.month.isin(TEST_MONTHS)&(d.valid_result==1)].copy();out=[]
    y=z.head_hit.astype(int).to_numpy()
    for c in features:
        x=pd.to_numeric(z[c],errors='coerce');m=x.notna().to_numpy()
        if m.sum()<500 or x[m].nunique()<2:continue
        try:a=float(roc_auc_score(y[m],x[m].to_numpy()))
        except Exception:continue
        out.append({'feature':c,'coverage':float(m.mean()),'auc':a,'auc_abs':max(a,1-a),
                    'mean_head':float(x[y==1].mean()),'mean_loss':float(x[y==0].mean())})
    return pd.DataFrame(out).sort_values('auc_abs',ascending=False)


def make_summary(slot,folds,monthly,uni,fams):
    agg=slot.groupby('month')[['labelled_races','current_or_future_nonempty_races','current_day_nonempty_races','current_day_result_nonempty_races','current_day_st_nonempty_races','future_day_nonempty_races']].sum().reset_index()
    bad=int(slot.current_or_future_nonempty_races.sum())
    L=['# v295 1HEAD leakage + operability audit','',
       '- Research only. v294 is NOT production-approved by this audit.','- Jul/Aug are not used for selection/evaluation; September outcomes are not read.',
       '- The suspicious v294 99% tail is decomposed by source family and month.','',
       '## 1. Historical race-card slot leakage audit','',
       'For explicit day labels (day1..day7), a true pre-race snapshot must have no values in the current-day or future-day meeting slots.','',
       '|month|labelled R|current/future nonempty|current result|current ST|future day|','|---|---:|---:|---:|---:|---:|']
    for _,r in agg.iterrows():L.append(f"|{r.month}|{int(r.labelled_races)}|{int(r.current_or_future_nonempty_races)}|{int(r.current_day_result_nonempty_races)}|{int(r.current_day_st_nonempty_races)}|{int(r.future_day_nonempty_races)}|")
    L += ['',f'- Total structurally contaminated rows: **{bad}**.']
    L += ['','## 2. Ablation feature counts','|variant|features|','|---|---:|']
    for n,fs in fams.items():L.append(f'|{n}|{len(fs)}|')
    L += ['','## 3. Monthly OOF-tail precision','',
          'OOF_q selectors are preferred for diagnosis because a global p_cal cutoff can disappear in a later month.','',
          '|variant|month|selector|R|head rate|cut|','|---|---|---|---:|---:|---:|']
    show=monthly[monthly.selector.isin(['OOF_q0.900','OOF_q0.950','OOF_q0.975'])]
    for _,r in show.iterrows():
        rate='-' if pd.isna(r.head_rate) else f'{100*r.head_rate:.2f}%'
        L.append(f'|{r.variant}|{r.month}|{r.selector}|{int(r.R)}|{rate}|{r.cut:.4f}|')
    L += ['','## 4. Top univariate signals','|feature|coverage|direction-free AUC|mean head|mean loss|','|---|---:|---:|---:|---:|']
    for _,r in uni.head(30).iterrows():L.append(f'|{r.feature}|{100*r.coverage:.1f}%|{r.auc_abs:.4f}|{r.mean_head:.4f}|{r.mean_loss:.4f}|')
    L += ['','## 5. Operability assessment','',
          '- `HGB_STATIC6`: immediately reproducible from the morning race-card only; no stateful preview history is required.',
          '- `HGB_STATIC9`: also morning-available if the meeting-slot audit is clean; it adds prior-meeting ST/results from the race-card.',
          '- `HGB_STATIC9_PLAYER`: operationally reproducible, but requires a maintained prior-day player-result state.',
          '- `HGB_FULL_PRE`: operationally reproducible only with maintained prior-exhibition state (`tkz/original exhibition`). It is more complex and must not be promoted if simpler families retain the precision.',
          '- A fixed `p_cal>=0.98` rule is operationally rejected if it fails to produce selections every evaluation month. Prefer a frozen OOF-derived policy with explicit no-bet behavior and minimum monthly volume.',
          '- Production adoption requires a result-blind live scorer, immutable model artifact, source-availability checks, and prospective September logging before outcomes are inspected.','',
          '## Decision rule','- If current/future slot leakage is nonzero, discard any family using meeting-slot features and rebuild.',
          '- If only FULL_PRE creates the extreme tail, treat v294 as complexity-sensitive and require an independent prospective replay before use.',
          '- If STATIC6/STATIC9 also retain >=90% monthly tail precision with useful R, prioritize the simplest reproducible family for production.']
    return '\n'.join(L)+'\n'


def main():
    slot=slot_day_audit();slot.to_csv(str(PREFIX)+'_slot_audit.csv',index=False,encoding='utf-8-sig')
    pre,a=v294.freeze_true_pre();pre=v294.add_prior_history(pre);pre=v294.add_rel(pre)
    print('PRE FEATURES FROZEN',len(pre),'-- results join starts now',flush=True)
    pre=v294.settle_after_freeze(pre)
    pre=pre[pre.valid_result==1].copy()
    fams=family_manifest(pre)
    p,folds=run_ablation(pre,fams);monthly=tail_monthly(p)
    union=list(dict.fromkeys(sum(fams.values(),[])));uni=univariate_screen(pre,union)
    folds.to_csv(str(PREFIX)+'_folds.csv',index=False,encoding='utf-8-sig')
    monthly.to_csv(str(PREFIX)+'_monthly.csv',index=False,encoding='utf-8-sig')
    uni.to_csv(str(PREFIX)+'_univariate.csv',index=False,encoding='utf-8-sig')
    SUMMARY.write_text(make_summary(slot,folds,monthly,uni,fams),encoding='utf-8')
    print(SUMMARY.read_text(),flush=True)

if __name__=='__main__':main()
