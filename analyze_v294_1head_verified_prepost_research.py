#!/usr/bin/env python3
"""v294: verified 1-head >=90% PRE/POST research.

This version deliberately rebuilds the research universe from raw source instead of
joining direct features back onto v108.  The v293 join could silently leave every
current-race direct feature missing, so v294 is fail-closed.

No-leak rules
- Model selection/evaluation ends 2026-06-30.
- Jul/Aug are never fetched. Sep outcomes are never read.
- PRE contains only race-card/waku information known before current exhibition.
- POST adds current exhibition/original exhibition only after actual course1 is known.
- All feature rows for the complete period are frozen before result files are fetched.
- Monthly expanding walk-forward; Platt calibration and quantile cuts use training OOF only.
- Goal is realized boat1 head rate, not ROI.
"""
from __future__ import annotations
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta
from pathlib import Path
import time
import numpy as np
import pandas as pd

import analyze_v108_1head_feasibility as v108
import analyze_v293_1head_direct_history_research as v293
from backtest import rows, race_features
from backtest_v51_lane_corrected_tickets import corrected_direct, ii

ROOT=Path(__file__).resolve().parent
PREFIX=ROOT/'analysis_v294_1head_verified_prepost'
SUMMARY=ROOT/'summary_v294_1head_verified_prepost_research.md'
PRELOAD=date(2025,10,1)
START=date(2025,11,1)
END=date(2026,6,30)
TEST_MONTHS=['2026-02','2026-03','2026-04','2026-05','2026-06']
STATIC_KEYS=list(v293.STATIC_KEYS)
POST_KEYS=list(v293.POST_KEYS)
CUTS=list(v293.CUTS)
QS=list(v293.QS)


def norm_code(x):
    s=str(x or '').strip()
    if s.endswith('.0') and s[:-2].isdigit():s=s[:-2]
    if s.isdigit():return s.zfill(12)
    return ''


def bycode(rs):
    out={}
    for r in rs:
        c=norm_code(r.get('レースコード',''))
        if c:out[c]=r
    return out


def fetch_feature_day(d,tries=3):
    last=None
    for n in range(tries):
        last=v108.fetch_feature_day(d)[1]
        if last.get('cards'):
            return d,last,n
        time.sleep(.25*(n+1))
    return d,last or {'cards':[],'waku':[],'tkz':[],'stt':[],'orig':[]},tries


def freeze_features():
    days=[];d=PRELOAD
    while d<=END:
        days.append(d);d+=timedelta(days=1)
    fetched={};retry_days=0;empty_days=[]
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs=[ex.submit(fetch_feature_day,d) for d in days]
        for j,f in enumerate(as_completed(futs),1):
            dd,z,n=f.result();fetched[dd]=z
            retry_days+=int(n>0)
            if not z.get('cards'):empty_days.append(str(dd))
            if j%40==0:print('feature fetch',j,'/',len(days),flush=True)

    sums=defaultdict(list);allv=[];frozen=[]
    audit=defaultdict(int);audit['days']=len(days);audit['retry_days']=retry_days;audit['empty_days']=len(empty_days)
    for d in sorted(fetched):
        z=fetched[d];bias=v108.st_bias(sums,allv)
        if d>=START:
            wm=bycode(z['waku']);tm=bycode(z['tkz']);sm=bycode(z['stt']);om=bycode(z['orig'])
            audit['cards']+=len(z['cards']);audit['waku']+=len(wm);audit['tkz']+=len(tm);audit['stt']+=len(sm);audit['orig']+=len(om)
            for card in z['cards']:
                code=norm_code(card.get('レースコード',''))
                if not code:
                    audit['bad_code']+=1;continue
                w=wm.get(code)
                if not w:
                    audit['missing_waku']+=1;continue
                try:
                    x=race_features(card,w)
                    exs,sts,oss=corrected_direct(code,tm,sm,om,bias)
                    for b in range(1,7):
                        exs.setdefault(b,.5);sts.setdefault(b,.5);oss.setdefault(b,{'lap':.5,'turn':.5,'straight':.5,'avg':.5})
                        for k in ('lap','turn','straight','avg'):oss[b].setdefault(k,.5)
                    q={'date':str(d),'month':d.strftime('%Y-%m'),'race_code':code,
                       'venue':str(card.get('レース場コード','')).zfill(2),'race':ii(card.get('レース回'),0),
                       'has_tkz':int(code in tm),'has_stt':int(code in sm),'has_orig':int(code in om)}
                    sr=sm.get(code,{})
                    course1=ii(sr.get('艇1_コース'),0)
                    q['entry_course1']=course1
                    q['post_eligible']=int(course1==1)
                    for b in range(1,7):
                        p=v293.boat_parts(x,b,exs,sts,oss)
                        for k,val in p.items():q[f'b{b}_{k}']=val
                    frozen.append(q);audit['frozen']+=1
                    audit['post_eligible']+=q['post_eligible'];audit['frozen_tkz']+=q['has_tkz'];audit['frozen_stt']+=q['has_stt'];audit['frozen_orig']+=q['has_orig']
                except Exception as e:
                    audit['feature_error']+=1
                    if audit['feature_error']<=5:print('feature error',d,code,type(e).__name__,e,flush=True)
        # current date is already frozen; only now may its ST contribute to future dates
        v108.update_st(z.get('stt',[]),sums,allv)
    audit['empty_day_list']=';'.join(empty_days[:20])
    return pd.DataFrame(frozen),dict(audit)


def settle_after_all_features_frozen(d):
    days=sorted({date.fromisoformat(x) for x in d.date.astype(str)})
    fetched={}
    def one(day):
        y=day.strftime('%Y/%m/%d')
        return day,bycode(rows(f'data/results/realtime/{y}.csv'))
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs=[ex.submit(one,x) for x in days]
        for j,f in enumerate(as_completed(futs),1):
            day,r=f.result();fetched[day]=r
            if j%40==0:print('result fetch',j,'/',len(days),flush=True)
    wins=[];valid=[]
    for _,r in d.iterrows():
        rr=fetched.get(date.fromisoformat(str(r.date)),{}).get(norm_code(r.race_code),{})
        w=ii(rr.get('1着_艇番'),0)
        wins.append(w);valid.append(int(w in range(1,7)))
    z=d.copy();z['winner']=wins;z['valid_result']=valid;z['head_hit']=(z.winner==1).astype(int)
    return z


def add_rel(d):
    d=d.copy()
    for k in STATIC_KEYS+POST_KEYS:
        a=f'b1_{k}'
        if a not in d:continue
        av=pd.to_numeric(d[a],errors='coerce')
        opp=[]
        for b in range(2,7):
            c=f'b{b}_{k}'
            if c in d:
                cv=pd.to_numeric(d[c],errors='coerce');d[f'rel_{k}_1v{b}']=av-cv;opp.append(c)
        if opp:
            om=d[opp].apply(pd.to_numeric,errors='coerce')
            d[f'rel_{k}_1vbest']=av-om.max(axis=1)
            d[f'rel_{k}_1vavg']=av-om.mean(axis=1)
    # Explicit attack/wall risks; larger means opponents 2/3 are stronger than boat1.
    for k in ['nst_strength','waku_sr_strength','meet_st_strength','motor','st','direct','straight','turn','lap']:
        a=f'b1_{k}'
        cs=[f'b2_{k}',f'b3_{k}']
        if a in d and all(c in d for c in cs):
            d[f'attack23_{k}']=d[cs].apply(pd.to_numeric,errors='coerce').max(axis=1)-pd.to_numeric(d[a],errors='coerce')
    return d


def feature_sets(d):
    static=[f'b{b}_{k}' for b in range(1,7) for k in STATIC_KEYS]
    staticrel=[c for c in d if c.startswith('rel_') and any(c.startswith('rel_'+k+'_') for k in STATIC_KEYS)]
    preattack=[c for c in d if c.startswith('attack23_') and any(c=='attack23_'+k for k in STATIC_KEYS)]
    post=[f'b{b}_{k}' for b in range(1,7) for k in POST_KEYS]
    postrel=[c for c in d if c.startswith('rel_') and any(c.startswith('rel_'+k+'_') for k in POST_KEYS)]
    postattack=[c for c in d if c.startswith('attack23_') and any(c=='attack23_'+k for k in POST_KEYS)]
    pre=v293.available(d,static+staticrel+preattack,.55)
    postfs=v293.available(d,static+staticrel+preattack+post+postrel+postattack,.55)
    forbidden=set(post+postrel+postattack+['entry_course1','post_eligible','has_tkz','has_stt','has_orig'])
    leak=[c for c in pre if c in forbidden]
    if leak:raise RuntimeError('PRE leakage '+','.join(leak[:10]))
    if len(pre)<40:raise RuntimeError(f'PRE feature set too small: {len(pre)}')
    if len(postfs)<=len(pre)+20:raise RuntimeError(f'POST did not add enough features PRE={len(pre)} POST={len(postfs)}')
    return {
      'PRE_LR_DIRECT':('lr',pre,False),
      'PRE_HGB_DIRECT':('hgb',pre,False),
      'POST_LR_DIRECT':('lr',postfs,True),
      'POST_HGB_DIRECT':('hgb',postfs,True),
    }


def run_variants(d,fams):
    preds=[];folds=[]
    for name,(kind,fs0,ispost) in fams.items():
        universe=d[(d.valid_result==1)&((d.post_eligible==1) if ispost else True)].copy()
        for tm in TEST_MONTHS:
            tr=universe[universe.month<tm].copy();te=universe[universe.month==tm].copy();fs=v293.available(tr,fs0,.55)
            if len(fs)<5 or te.empty:raise RuntimeError(f'empty fold {name} {tm} features={len(fs)} test={len(te)}')
            oo=v293.oof(kind,fs,tr);cc=v293.calfit(oo);oop=v293.cal(cc,oo.p)
            raw=v293.fitpred(kind,fs,tr,te);pc=v293.cal(cc,raw)
            z=te[['date','month','race_code','venue','race','head_hit','post_eligible']].copy();z['variant']=name;z['test_month']=tm;z['p_raw']=raw;z['p_cal']=pc
            for q in QS:
                ct=float(np.quantile(oop,q));z[f'q{q}_sel']=(pc>=ct).astype(int);z[f'q{q}_cut']=ct
            preds.append(z);folds.append({'variant':name,'month':tm,'features':len(fs),'train':len(tr),'test':len(te),'oof':len(oo)})
            print(name,tm,'f',len(fs),'tr',len(tr),'te',len(te),flush=True)
    return pd.concat(preds,ignore_index=True),pd.DataFrame(folds)


def audit_frame(a,d,fams):
    n=max(1,int(a.get('cards',0)))
    f=max(1,int(a.get('frozen',0)))
    rows_out=[
      {'metric':'cards','value':a.get('cards',0)},
      {'metric':'frozen','value':a.get('frozen',0)},
      {'metric':'frozen_per_card','value':a.get('frozen',0)/n},
      {'metric':'missing_waku','value':a.get('missing_waku',0)},
      {'metric':'feature_error','value':a.get('feature_error',0)},
      {'metric':'empty_days','value':a.get('empty_days',0)},
      {'metric':'retry_days','value':a.get('retry_days',0)},
      {'metric':'tkz_coverage','value':a.get('frozen_tkz',0)/f},
      {'metric':'stt_coverage','value':a.get('frozen_stt',0)/f},
      {'metric':'orig_coverage','value':a.get('frozen_orig',0)/f},
      {'metric':'post_eligible_rate','value':a.get('post_eligible',0)/f},
      {'metric':'valid_result_rate','value':float(d.valid_result.mean())},
    ]
    for name,(_,fs,ispost) in fams.items():rows_out.append({'metric':'features_'+name,'value':len(fs)})
    return pd.DataFrame(rows_out)


def make_summary(audit,folds,met,sel,fams):
    def pct(x):return '-' if pd.isna(x) else f'{100*float(x):.2f}%'
    av=dict(zip(audit.metric,audit.value))
    L=['# v294 1HEAD verified PRE/POST research','',
       '- Research only; production unchanged.','- Raw-source rebuild; v293 silent direct-feature join failure is not reused.',
       '- Feature/model selection ends 2026-06-30. Jul/Aug are not fetched; Sep outcomes are unread.',
       '- PRE is true pre-exhibition scheduled-lane1 universe. POST is a separate actual-course1-confirmed universe.',
       '- All current-race features are frozen for the full period before target results are fetched.',
       '- Calibration and score-quantile gates use training temporal OOF only.','',
       '## Source / leakage audit','|metric|value|','|---|---:|']
    for _,r in audit.iterrows():L.append(f'|{r.metric}|{r.value}|')
    L+=['','## Feature sets','|variant|family|features|universe|','|---|---|---:|---|']
    for n,(k,fs,post) in fams.items():L.append(f'|{n}|{k}|{len(fs)}|{"actual course1 POST" if post else "scheduled lane1 PRE"}|')
    L+=['','## Pooled Feb-Jun metrics','|variant|score|R|AUC|Brier|LogLoss|','|---|---|---:|---:|---:|---:|']
    for _,r in met.sort_values(['score','brier']).iterrows():L.append(f'|{r.variant}|{r.score}|{int(r.R)}|{r.auc:.4f}|{r.brier:.4f}|{r.logloss:.4f}|')
    good=sel[(sel.R>=100)&(sel.head_rate>=.90)].sort_values(['wilson_lo','R'],ascending=False)
    L+=['','## >=90% realized zones, R>=100']
    if good.empty:L.append('- None.')
    else:
        L+=['|variant|score|source|rule|R|heads|rate|Wilson low|worst month|min month R|','|---|---|---|---|---:|---:|---:|---:|---:|---:|']
        for _,r in good.head(40).iterrows():L.append(f'|{r.variant}|{r.score}|{r.source}|{r.rule}|{int(r.R)}|{int(r.heads)}|{pct(r.head_rate)}|{pct(r.wilson_lo)}|{pct(r.worst_month_head_rate)}|{int(r.min_month_R)}|')
    best=sel[sel.R>=100].sort_values(['head_rate','wilson_lo','R'],ascending=False).head(25)
    L+=['','## Best zones with R>=100','|variant|score|source|rule|R|rate|Wilson low|worst month|min month R|','|---|---|---|---|---:|---:|---:|---:|---:|']
    for _,r in best.iterrows():L.append(f'|{r.variant}|{r.score}|{r.source}|{r.rule}|{int(r.R)}|{pct(r.head_rate)}|{pct(r.wilson_lo)}|{pct(r.worst_month_head_rate)}|{int(r.min_month_R)}|')
    L+=['','## Next decision rule','- Do not promote to production merely because a pooled row reaches 90%. Require adequate R, monthly floor, Wilson interval, and untouched prospective validation.',
        '- If no robust 90% zone exists, the next research step is prior-only player/course history plus an independent boat1-loss-risk gate / PRE-POST consensus.']
    return '\n'.join(L)+'\n'


def main():
    d,a=freeze_features()
    if d.empty:raise RuntimeError('no frozen features')
    if pd.to_datetime(d.date).max()>=pd.Timestamp('2026-07-01'):raise RuntimeError('Jul/Aug leakage')
    cardcov=a.get('frozen',0)/max(1,a.get('cards',0))
    if cardcov<.85:raise RuntimeError(f'raw source freeze coverage too low {cardcov:.3f}')
    if a.get('frozen_tkz',0)/max(1,a.get('frozen',0))<.50:raise RuntimeError('current exhibition source coverage too low')
    print('ALL FEATURES FROZEN:',len(d),'-- only now results are fetched',flush=True)
    d=settle_after_all_features_frozen(d)
    if d.valid_result.mean()<.85:raise RuntimeError(f'result coverage too low {d.valid_result.mean():.3f}')
    d=add_rel(d);fams=feature_sets(d)
    p,folds=run_variants(d,fams);met,sel=v293.evaluate(p)
    audit=audit_frame(a,d,fams)
    # Fail closed on the exact v293 pathology.
    counts={n:len(fs) for n,(_,fs,_) in fams.items()}
    if counts['POST_LR_DIRECT']<=counts['PRE_LR_DIRECT']:raise RuntimeError('PRE/POST feature manifests did not separate')
    audit.to_csv(str(PREFIX)+'_source_audit.csv',index=False,encoding='utf-8-sig')
    folds.to_csv(str(PREFIX)+'_folds.csv',index=False,encoding='utf-8-sig')
    met.to_csv(str(PREFIX)+'_metrics.csv',index=False,encoding='utf-8-sig')
    sel.to_csv(str(PREFIX)+'_selection.csv',index=False,encoding='utf-8-sig')
    p.to_csv(str(PREFIX)+'_predictions.csv',index=False,encoding='utf-8-sig')
    SUMMARY.write_text(make_summary(audit,folds,met,sel,fams),encoding='utf-8')
    print(SUMMARY.read_text(),flush=True)

if __name__=='__main__':main()
