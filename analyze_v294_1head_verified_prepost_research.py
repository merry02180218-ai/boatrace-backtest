#!/usr/bin/env python3
"""v294: verified 1-head >=90% PRE/POST research, recovered-source edition.

Why this edition exists
- BoatraceCSV/main currently retains historical race_cards/results but its waku10/current
  preview history is rolling; pre-Jul waku10 is no longer available.
- v293 silently continued after those joins vanished. v294 is fail-closed instead.
- True PRE is rebuilt from historical race cards + strictly prior-day player history.
- POST is a separate actual-course1 universe using the already-frozen v108 feature ledger;
  target/result columns from v108 are deliberately not loaded.

No-leak rules
- Selection/evaluation ends 2026-06-30. Jul/Aug are never used. Sep outcomes are unread.
- PRE universe is every scheduled lane-1 race; no actual-entry/current-exhibition gate.
- POST universe is the v108 actual-course1 frozen ledger, kept separate from PRE.
- Player history freezes day D before ingesting day-D results (v221.build invariant).
- Current target winners are joined only after PRE/POST/history feature construction.
- Monthly expanding walk-forward; Platt calibration and quantile cuts use training OOF only.
- Goal is realized boat1 head rate, not ROI.
"""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta
from pathlib import Path
import math
import numpy as np
import pandas as pd

import analyze_v221_3head_scenario_pair as v221
import analyze_v293_1head_direct_history_research as v293
from backtest import rows, grade_score, clamp, pct_motor, recent_meeting_st
from backtest_v51_lane_corrected_tickets import ff, ii

ROOT=Path(__file__).resolve().parent
V108=ROOT/'analysis_v108_1head_feasibility.csv'
PREFIX=ROOT/'analysis_v294_1head_verified_prepost'
SUMMARY=ROOT/'summary_v294_1head_verified_prepost_research.md'
START=date(2025,11,1); END=date(2026,6,30)
TEST_MONTHS=['2026-02','2026-03','2026-04','2026-05','2026-06']

RAW_KEYS=['grade','wr','local','motor','nst_strength','meet_st_strength','meet_win','meet_p2','f_safety']
PLAYER_KEYS=['all_win','all_p2','frame_win','frame_p2','recent_p2']
PRIOR_KEYS=['p12_display','p12_overall','p12_turn','p12_straight','delta_display','delta_overall','delta_turn','delta_straight']
POST_FROZEN=[
 'one_grade','one_wr','one_local','one_motor','one_waku_wr','one_nst_strength',
 'one_waku_sr_strength','one_past_win','one_meet_st_strength',
 'one_ex','one_st','one_lap','one_turn','one_straight','one_orig_avg','one_direct','one_score',
 'threat2','threat3','threat4','threat5','threat6','threat23_max','threat_all_max',
 'margin2','margin3','margin23','margin_all','st_margin2','st_margin3','st_margin23',
 'ex_margin23','turn_margin23','straight_margin23'
]


def norm_code(x):
    s=str(x or '').strip()
    if s.endswith('.0') and s[:-2].isdigit():s=s[:-2]
    return s.zfill(12) if s.isdigit() else ''

def bycode(rs):return {norm_code(r.get('レースコード','')):r for r in rs if norm_code(r.get('レースコード',''))}

def meet_finish(card,b):
    vals=[]
    for d in range(1,8):
        for s in range(1,3):
            z=str(card.get(f'艇{b}_節D{d}走{s}_着順','') or '').strip()
            if z.isdigit():vals.append(int(z))
    if not vals:return .0,.0
    return sum(x==1 for x in vals)/len(vals),sum(x<=2 for x in vals)/len(vals)

def raw_parts(card,b):
    nst=ff(card.get(f'艇{b}_全国平均ST'),.20)
    m2=ff(card.get(f'艇{b}_モーター2連対率'),0);m3=ff(card.get(f'艇{b}_モーター3連対率'),0)
    mst=recent_meeting_st(card,b);mw,mp=meet_finish(card,b)
    return {
      'grade':grade_score(card.get(f'艇{b}_級別','')),
      'wr':clamp((ff(card.get(f'艇{b}_全国勝率'),3)-3)/5),
      'local':clamp((ff(card.get(f'艇{b}_当地勝率'),2.5)-2.5)/5.5),
      'motor':.62*pct_motor(m2)+.38*pct_motor(m3),
      'nst_strength':clamp((.24-nst)/.14),
      'meet_st_strength':.5 if mst is None else clamp((.22-mst)/.12),
      'meet_win':mw,'meet_p2':mp,
      'f_safety':clamp(1-ff(card.get(f'艇{b}_F本数'),0)/2),
    }

def fetch_cards(d):
    y=d.strftime('%Y/%m/%d');return d,rows(f'data/programs/race_cards/{y}.csv')

def freeze_true_pre():
    days=[];d=START
    while d<=END:days.append(d);d+=timedelta(days=1)
    fetched={}
    with ThreadPoolExecutor(max_workers=10) as ex:
        fs=[ex.submit(fetch_cards,d) for d in days]
        for j,f in enumerate(as_completed(fs),1):
            dd,z=f.result();fetched[dd]=z
            if j%40==0:print('race-card fetch',j,'/',len(days),flush=True)
    out=[];cards=bad=0
    for d in sorted(fetched):
        for card in fetched[d]:
            cards+=1;code=norm_code(card.get('レースコード',''))
            if not code:bad+=1;continue
            q={'date':str(d),'month':d.strftime('%Y-%m'),'race_code':code,'venue':str(card.get('レース場コード','')).zfill(2),
               'race':ii(str(card.get('レース回','')).replace('R',''),0),'universe':'PRE'}
            for b in range(1,7):
                for k,v in raw_parts(card,b).items():q[f'b{b}_{k}']=v
            out.append(q)
    if len(out)<15000:raise RuntimeError(f'PRE source unexpectedly small {len(out)} cards={cards} bad={bad}')
    return pd.DataFrame(out),{'pre_cards':cards,'pre_frozen':len(out),'bad_code':bad}

def load_frozen_post(pre):
    # Never load any v108 result/target/payout columns here.
    meta=['date','race_code','venue','race','entry_course','entry_status','has_tkz','has_stt','has_orig']
    wanted=set(meta+POST_FROZEN)
    d=pd.read_csv(V108,encoding='utf-8-sig',dtype={'race_code':str},usecols=lambda c:c in wanted)
    d['date']=pd.to_datetime(d.date,errors='coerce');d=d[(d.date>=pd.Timestamp(START))&(d.date<=pd.Timestamp(END))].copy()
    d['race_code']=d.race_code.astype(str).str.replace('.0','',regex=False).str.zfill(12);d['date']=d.date.dt.strftime('%Y-%m-%d');d['month']=d.date.str[:7]
    if 'entry_course' in d and not (pd.to_numeric(d.entry_course,errors='coerce')==1).all():raise RuntimeError('v108 POST ledger contains non-course1 rows')
    basecols=['date','race_code']+[c for c in pre.columns if c.startswith('b')]
    static=pre[basecols].drop_duplicates(['date','race_code'])
    d=d.merge(static,on=['date','race_code'],how='left',validate='one_to_one')
    cov=float(d[[c for c in d if c.startswith('b1_')]].notna().any(axis=1).mean())
    if cov<.98:raise RuntimeError(f'POST to race-card static coverage too low {cov:.3f}')
    d['venue']=d.venue.astype(str).str.replace('.0','',regex=False).str.zfill(2);d['universe']='POST'
    return d,cov

def add_prior_history(d):
    # v221 freezes day D traits before ingesting day-D preview/results.
    z=v221.build(d.copy(),'date')
    return z

def add_rel(d):
    d=d.copy()
    for k in RAW_KEYS:
        a=f'b1_{k}';av=pd.to_numeric(d[a],errors='coerce');opp=[]
        for b in range(2,7):
            c=f'b{b}_{k}';cv=pd.to_numeric(d[c],errors='coerce');d[f'rel_{k}_1v{b}']=av-cv;opp.append(c)
        om=d[opp].apply(pd.to_numeric,errors='coerce');d[f'rel_{k}_1vbest']=av-om.max(axis=1);d[f'rel_{k}_1vavg']=av-om.mean(axis=1)
    for fam,keys in [('pl',PLAYER_KEYS),('vh',PRIOR_KEYS),('gh',PRIOR_KEYS)]:
        for k in keys:
            a=f'b1_{fam}_{k}'
            if a not in d:continue
            av=pd.to_numeric(d[a],errors='coerce');opp=[]
            for b in range(2,7):
                c=f'b{b}_{fam}_{k}'
                if c in d:d[f'rel_{fam}_{k}_1v{b}']=av-pd.to_numeric(d[c],errors='coerce');opp.append(c)
            if opp:
                om=d[opp].apply(pd.to_numeric,errors='coerce');d[f'rel_{fam}_{k}_1vbest']=av-om.max(axis=1);d[f'rel_{fam}_{k}_1vavg']=av-om.mean(axis=1)
    # Explicit attack risk by 2/3. Positive = attack pair stronger than boat1.
    for k in ['grade','wr','local','motor','nst_strength','meet_st_strength','meet_win','meet_p2']:
        d[f'attack23_{k}']=d[[f'b2_{k}',f'b3_{k}']].apply(pd.to_numeric,errors='coerce').max(axis=1)-pd.to_numeric(d[f'b1_{k}'],errors='coerce')
    return d

def settle_after_freeze(d):
    days=sorted({date.fromisoformat(str(x)) for x in d.date})
    fetched={}
    def one(day):return day,bycode(rows(f"data/results/realtime/{day.strftime('%Y/%m/%d')}.csv"))
    with ThreadPoolExecutor(max_workers=10) as ex:
        fs=[ex.submit(one,x) for x in days]
        for j,f in enumerate(as_completed(fs),1):
            dd,z=f.result();fetched[dd]=z
            if j%40==0:print('result fetch',j,'/',len(days),flush=True)
    w=[];valid=[]
    for _,r in d.iterrows():
        rr=fetched.get(date.fromisoformat(str(r.date)),{}).get(norm_code(r.race_code),{});x=ii(rr.get('1着_艇番'),0)
        w.append(x);valid.append(int(x in range(1,7)))
    z=d.copy();z['winner']=w;z['valid_result']=valid;z['head_hit']=(z.winner==1).astype(int)
    return z

def feature_manifest(d,universe):
    x=d[d.universe==universe]
    raw=[f'b{b}_{k}' for b in range(1,7) for k in RAW_KEYS]
    rawrel=[c for c in d if c.startswith('rel_') and any(c.startswith('rel_'+k+'_') for k in RAW_KEYS)]
    attack=[c for c in d if c.startswith('attack23_')]
    player=[c for c in d if '_pl_' in c or c.startswith('rel_pl_')]
    prior=[c for c in d if '_vh_' in c or '_gh_' in c or c.startswith('rel_vh_') or c.startswith('rel_gh_')]
    pre=v293.available(x,raw+rawrel+attack+player+prior,.55)
    if universe=='PRE':return pre
    post=v293.available(x,pre+POST_FROZEN,.55)
    return post

def run_variants(d):
    fams={}
    pre=feature_manifest(d,'PRE');post=feature_manifest(d,'POST')
    if len(pre)<80:raise RuntimeError(f'PRE feature set too small {len(pre)}')
    if len(post)<=len(pre)+15:raise RuntimeError(f'POST did not add frozen exhibition block PRE={len(pre)} POST={len(post)}')
    for u,fs in [('PRE',pre),('POST',post)]:
        fams[f'{u}_LR_RECOVERED']=('lr',fs,u);fams[f'{u}_HGB_RECOVERED']=('hgb',fs,u)
    preds=[];folds=[]
    for name,(kind,fs0,u) in fams.items():
        z=d[(d.universe==u)&(d.valid_result==1)].copy()
        for tm in TEST_MONTHS:
            tr=z[z.month<tm].copy();te=z[z.month==tm].copy();fs=v293.available(tr,fs0,.55)
            if len(fs)<20 or te.empty:raise RuntimeError(f'bad fold {name} {tm} f={len(fs)} te={len(te)}')
            oo=v293.oof(kind,fs,tr);cc=v293.calfit(oo);oop=v293.cal(cc,oo.p);rawp=v293.fitpred(kind,fs,tr,te);pc=v293.cal(cc,rawp)
            q=te[['date','month','race_code','venue','race','head_hit']].copy();q['variant']=name;q['test_month']=tm;q['p_raw']=rawp;q['p_cal']=pc
            for cut in v293.QS:
                ct=float(np.quantile(oop,cut));q[f'q{cut}_sel']=(pc>=ct).astype(int);q[f'q{cut}_cut']=ct
            preds.append(q);folds.append({'variant':name,'month':tm,'features':len(fs),'train':len(tr),'test':len(te),'oof':len(oo)})
            print(name,tm,'features',len(fs),'train',len(tr),'test',len(te),flush=True)
    return pd.concat(preds,ignore_index=True),pd.DataFrame(folds),fams

def summary(audit,folds,met,sel,fams):
    def pct(x):return '-' if pd.isna(x) else f'{100*float(x):.2f}%'
    L=['# v294 1HEAD verified PRE/POST research — recovered source','',
       '- Research only; production unchanged.','- Selection/evaluation ends 2026-06-30. Jul/Aug are excluded; Sep outcomes are unread.',
       '- Historical waku10/current-preview files are no longer retained pre-Jul on BoatraceCSV/main; v294 therefore does not pretend they are available.',
       '- PRE = true scheduled-lane1 race-card + prior-day history universe. POST = separate v108 actual-course1 frozen feature ledger.',
       '- v108 result/target/payout columns are not loaded into the POST feature frame. Current winners are joined after feature construction.',
       '- Monthly expanding walk-forward; Platt calibration and quantile gates are training-OOF only.','',
       '## Source / leakage audit','|metric|value|','|---|---:|']
    for k,v in audit.items():L.append(f'|{k}|{v}|')
    L+=['','## Feature sets','|variant|family|features|universe|','|---|---|---:|---|']
    for n,(kind,fs,u) in fams.items():L.append(f'|{n}|{kind}|{len(fs)}|{u}|')
    L+=['','## Pooled Feb-Jun metrics','|variant|score|R|AUC|Brier|LogLoss|','|---|---|---:|---:|---:|---:|']
    for _,r in met.sort_values(['score','brier']).iterrows():L.append(f'|{r.variant}|{r.score}|{int(r.R)}|{r.auc:.4f}|{r.brier:.4f}|{r.logloss:.4f}|')
    good=sel[(sel.R>=100)&(sel.head_rate>=.90)].sort_values(['wilson_lo','R'],ascending=False)
    L+=['','## >=90% realized zones, R>=100']
    if good.empty:L.append('- None.')
    else:
        L+=['|variant|score|source|rule|R|heads|rate|Wilson low|Wilson high|worst month|min month R|','|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|']
        for _,r in good.head(40).iterrows():L.append(f'|{r.variant}|{r.score}|{r.source}|{r.rule}|{int(r.R)}|{int(r.heads)}|{pct(r.head_rate)}|{pct(r.wilson_lo)}|{pct(r.wilson_hi)}|{pct(r.worst_month_head_rate)}|{int(r.min_month_R)}|')
    best=sel[sel.R>=100].sort_values(['head_rate','wilson_lo','R'],ascending=False).head(25)
    L+=['','## Best zones with R>=100','|variant|score|source|rule|R|heads|rate|Wilson low|worst month|min month R|','|---|---|---|---|---:|---:|---:|---:|---:|---:|']
    for _,r in best.iterrows():L.append(f'|{r.variant}|{r.score}|{r.source}|{r.rule}|{int(r.R)}|{int(r.heads)}|{pct(r.head_rate)}|{pct(r.wilson_lo)}|{pct(r.worst_month_head_rate)}|{int(r.min_month_R)}|')
    L+=['','## Decision','- A pooled 90% row alone is not production evidence. Require monthly stability, Wilson interval, adequate volume, then untouched prospective validation.',
       '- If 90% is still not robust, next step is an independently trained boat1-loss-risk gate and PRE/POST consensus; no rescue rule may lower precision.']
    return '\n'.join(L)+'\n'

def main():
    pre,a=freeze_true_pre();post,postcov=load_frozen_post(pre)
    # Combine feature-only frames; history is frozen before each current day result is ingested.
    d=pd.concat([pre,post],ignore_index=True,sort=False)
    if pd.to_datetime(d.date).max()>=pd.Timestamp('2026-07-01'):raise RuntimeError('Jul/Aug contamination')
    d=add_prior_history(d);d=add_rel(d)
    print('FEATURES FROZEN PRE/POST/HISTORY',len(d),'-- target settlement starts now',flush=True)
    d=settle_after_freeze(d)
    rcov=float(d.valid_result.mean())
    if rcov<.95:raise RuntimeError(f'result coverage too low {rcov:.3f}')
    p,folds,fams=run_variants(d);met,sel=v293.evaluate(p)
    audit={**a,'post_frozen':int((d.universe=='POST').sum()),'post_static_join_coverage':postcov,
           'result_coverage':rcov,'history_player_features':sum('_pl_' in c for c in d.columns),
           'history_prior_exhibition_features':sum(('_vh_' in c or '_gh_' in c) for c in d.columns)}
    aud=pd.DataFrame([{'metric':k,'value':v} for k,v in audit.items()])
    aud.to_csv(str(PREFIX)+'_source_audit.csv',index=False,encoding='utf-8-sig');folds.to_csv(str(PREFIX)+'_folds.csv',index=False,encoding='utf-8-sig')
    met.to_csv(str(PREFIX)+'_metrics.csv',index=False,encoding='utf-8-sig');sel.to_csv(str(PREFIX)+'_selection.csv',index=False,encoding='utf-8-sig');p.to_csv(str(PREFIX)+'_predictions.csv',index=False,encoding='utf-8-sig')
    SUMMARY.write_text(summary(audit,folds,met,sel,fams),encoding='utf-8');print(SUMMARY.read_text(),flush=True)

if __name__=='__main__':main()
