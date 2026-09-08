#!/usr/bin/env python3
"""v220: pre-Jul 3-head audit of prior exhibitions + player traits.

Rules:
- 2026-07/08 are hard excluded from training, tuning and evaluation.
- Evaluation months: 2025-12..2026-06, strict monthly prior-only refit.
- Prior exhibition/original-exhibition features are frozen before the current day's result is loaded.
- Same-day earlier races are deliberately NOT used (conservative day-level freeze, matching v43).
- Historical odds are settlement-only. They never choose model/features/races/point count.
- Final ROI diagnostic uses fixed Top10 v166 ranking and exact 10,000-yen Hamilton Dutch.
- Feature variants are ablations; no variant is auto-adopted from this script.
"""
from __future__ import annotations
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta
from pathlib import Path
import math
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, brier_score_loss, log_loss

import analyze_v165_3head_monthly_walkforward as v165
import analyze_v166_3head_pair_direct as v166
import analyze_v205_3head_operational_replay as v205
from backtest import rows
from backtest_v3 import CORR, expo_rows_to_records
from backtest_v4 import clean_name, rank_strength

ROOT=Path(__file__).resolve().parent
SRC=ROOT/'analysis_v108_1head_feasibility.csv'
OUT=ROOT/'analysis_v220_3head_history_player.csv'
DETAIL=ROOT/'analysis_v220_3head_history_player_predictions.csv'
SUM=ROOT/'summary_v220_3head_history_player.md'
EVAL_MONTHS=['2025-12','2026-01','2026-02','2026-03','2026-04','2026-05','2026-06']
PRELOAD=date(2025,10,1)
END=date(2026,6,30)
CONTAM=pd.Timestamp('2026-07-01')
BANK=10000


def ff(x,d=None):
    try:return float(x)
    except:return d

def ii(x,d=0):
    try:return int(float(x))
    except:return d

def normkim(x):return (x or '').replace(' ','').replace('　','')
def safe_auc(y,p):
    try:return float(roc_auc_score(y,p)) if len(set(map(int,y)))>1 else float('nan')
    except:return float('nan')
def safe_logloss(y,p):
    try:return float(log_loss(y,np.clip(p,1e-6,1-1e-6),labels=[0,1]))
    except:return float('nan')

def bycode(rs):return {str(r.get('レースコード','')).zfill(12):r for r in rs if r.get('レースコード')}

def day_fetch(d):
    ymd=d.strftime('%Y/%m/%d')
    return d,{
      'cards':rows(f'data/programs/race_cards/{ymd}.csv'),
      'tkz':rows(f'data/previews/tkz/{ymd}.csv'),
      'orig':rows(f'data/previews/original_exhibition/{ymd}.csv'),
      'res':rows(f'data/results/realtime/{ymd}.csv'),
    }

def preview_records(cards,tkz,orig):
    tm=bycode(tkz);om=bycode(orig);out=[]
    for card in cards:
        code=str(card.get('レースコード','')).zfill(12);venue=str(card.get('レース場コード','')).zfill(2)
        orow=om.get(code,{});name_orig={}
        if orow:
            for z in expo_rows_to_records([orow]):name_orig[clean_name(z.get('name',''))]=z
        tr=tm.get(code,{});vals=[]
        for b in range(1,7):
            v=ff(tr.get(f'艇{b}_展示タイム'))
            if v is not None:vals.append((b,v+CORR[b]['展示']))
        dr=rank_strength(vals) if vals else {}
        for b in range(1,7):
            name=clean_name(card.get(f'艇{b}_選手名',''))
            if not name:continue
            z=name_orig.get(name,{})
            out.append((code,venue,b,name,{
              'display':float(dr.get(b,.5)),'overall':float(z.get('overall',.5)),
              'turn':float(z.get('turn',.5)),'straight':float(z.get('straight',.5))}))
    return out

def histvals(dq):
    a=list(dq)
    p1=a[-1] if len(a)>=1 else None;p2=a[-2] if len(a)>=2 else None
    def g(z,k):return float(z[k]) if z is not None else .5
    o={'hist_has1':int(p1 is not None),'hist_has2':int(p2 is not None)}
    for k in ('display','overall','turn','straight'):
        o[f'prior1_{k}']=g(p1,k);o[f'prior2_{k}']=g(p2,k)
        o[f'prior12_{k}']=.6*g(p1,k)+.4*g(p2,k) if p2 is not None else g(p1,k)
        o[f'prior_delta_{k}']=g(p1,k)-g(p2,k) if p1 is not None and p2 is not None else 0.0
    return o

def stfeat(s,prefix):
    n=s['n'];w=s['w'];n3=s['n3'];w3=s['w3'];a3=s['a3']
    r3=list(s['r3']);ra=list(s['ra'])
    return {
      f'{prefix}_races':n,
      f'{prefix}_win_sm':(w+2*(1/6))/(n+2),
      f'{prefix}_b3_races':n3,
      f'{prefix}_b3_win_sm':(w3+3*.125)/(n3+3),
      f'{prefix}_b3_attack_sm':(a3+3*.08)/(n3+3),
      f'{prefix}_recent_b3_win':sum(x[0] for x in r3)/len(r3) if r3 else .125,
      f'{prefix}_recent_b3_attack':sum(x[1] for x in r3)/len(r3) if r3 else .08,
      f'{prefix}_recent_win':sum(ra)/len(ra) if ra else 1/6,
    }

def blankstat():return {'n':0,'w':0,'n3':0,'w3':0,'a3':0,'r3':deque(maxlen=20),'ra':deque(maxlen=30)}

def build_extras(base,dc):
    # Only dates needed for prior history and clean pre-Jul rows.
    idx_by_code=defaultdict(list)
    for ix,r in base.iterrows():
        dt=pd.to_datetime(r[dc],errors='coerce')
        if pd.notna(dt) and dt<CONTAM:
            idx_by_code[str(r.get('race_code','')).zfill(12)].append(ix)
    days=[];d=PRELOAD
    while d<=END:days.append(d);d+=timedelta(days=1)
    fetched={}
    with ThreadPoolExecutor(max_workers=10) as ex:
        futs=[ex.submit(day_fetch,d) for d in days]
        for j,f in enumerate(as_completed(futs),1):
            try:dd,z=f.result();fetched[dd]=z
            except Exception as e:print('fetch fail',e,flush=True)
            if j%30==0:print('days fetched',j,'/',len(days),flush=True)
    vh=defaultdict(lambda:deque(maxlen=2));gh=defaultdict(lambda:deque(maxlen=2))
    ps=defaultdict(blankstat);pvs=defaultdict(blankstat)
    extras={}
    for d in sorted(fetched):
        z=fetched[d];cards=z['cards'];cm=bycode(cards);rm=bycode(z['res'])
        prs=preview_records(cards,z['tkz'],z['orig'])
        # Freeze all current-day features BEFORE ingesting today's preview/result.
        for code,card in cm.items():
            if code not in idx_by_code:continue
            venue=str(card.get('レース場コード','')).zfill(2);name=clean_name(card.get('艇3_選手名',''))
            if not name:continue
            q={}
            hv=histvals(vh[(venue,name)]);hg=histvals(gh[name])
            q.update({f'venue_{k}':v for k,v in hv.items()});q.update({f'global_{k}':v for k,v in hg.items()})
            q.update(stfeat(ps[name],'player'));q.update(stfeat(pvs[(venue,name)],'player_venue'))
            for ix in idx_by_code[code]:extras[ix]=q
        # After freeze, ingest today's preview into histories.
        for code,venue,b,name,p in prs:
            vh[(venue,name)].append(p);gh[name].append(p)
        # Results update only after all current-day features are frozen.
        for code,card in cm.items():
            rr=rm.get(code,{});win=ii(rr.get('1着_艇番'));kim=normkim(rr.get('決まり手'))
            venue=str(card.get('レース場コード','')).zfill(2)
            for b in range(1,7):
                name=clean_name(card.get(f'艇{b}_選手名',''))
                if not name:continue
                for s in (ps[name],pvs[(venue,name)]):
                    s['n']+=1;s['w']+=int(win==b);s['ra'].append(int(win==b))
                    if b==3:
                        w3=int(win==3);atk=int(win==3 and kim in ('まくり','まくり差し'))
                        s['n3']+=1;s['w3']+=w3;s['a3']+=atk;s['r3'].append((w3,atk))
    exdf=pd.DataFrame.from_dict(extras,orient='index')
    return base.join(exdf,how='left')

def pair_probs(r,m):
    score={}
    for s in v166.OPP:
        for t in v166.OPP:
            if s==t:continue
            q=float(m.predict_proba(np.asarray([v166.pvec(r,s,t)],float))[0,1]);score[f'3-{s}-{t}']=max(q,1e-12)
    return sorted(score,key=lambda k:(-score[k],k))

def parse_actual(x):
    a=v166.combo(x);return '-'.join(map(str,a)) if len(a)==3 else ''

def settle10(ordered,odrow,actual):
    ts=ordered[:10];vals=[]
    for t in ts:
        try:v=float(odrow[t])
        except:return None
        if not np.isfinite(v) or v<=0:return None
        vals.append(v)
    stakes=np.asarray(v205.round_dutch(vals,BANK),int)
    if int(stakes.sum())!=BANK:raise RuntimeError('Dutch invariant')
    ret=0.;hit=0
    if actual in ts:
        i=ts.index(actual)
        if stakes[i]>0:ret=float(stakes[i]*vals[i]);hit=1
    return hit,ret,ret-BANK

def variants(basefs,cols):
    prior1=[c for c in cols if c.startswith('venue_prior1_')]+['venue_hist_has1']
    prior12=[c for c in cols if c.startswith('venue_prior') or c.startswith('venue_hist_')]
    globalh=[c for c in cols if c.startswith('global_prior') or c.startswith('global_hist_')]
    player=[c for c in cols if c.startswith('player_')]
    return {
      'BASE':list(basefs),
      'BASE+PRIOR1':list(basefs)+prior1,
      'BASE+PRIOR12':list(basefs)+prior12,
      'BASE+PLAYER':list(basefs)+player,
      'BASE+ALL_HISTORY':list(basefs)+prior12+globalh,
      'BASE+ALL':list(basefs)+prior12+globalh+player,
    }

def main():
    if not SRC.exists():raise SystemExit(f'missing {SRC}')
    raw=pd.read_csv(SRC,dtype={'race_code':str})
    dc=v165.pc(raw,['date','race_date','ymd']);vc=v165.pc(raw,['venue','jcd','stadium','place'])
    if not dc:raise SystemExit('no date col')
    y,td=v165.target(raw);basefs=v165.feats(raw)
    raw['_date']=pd.to_datetime(raw[dc].astype(str),errors='coerce');raw['_y']=y
    raw=raw[raw._date.notna()&raw._y.notna()&(raw._date<CONTAM)].copy()
    if raw.empty:raise SystemExit('no clean rows')
    d=build_extras(raw,dc)
    if (d._date>=CONTAM).any():raise RuntimeError('CONTAMINATION GUARD')
    vv=variants(basefs,list(d.columns));pred=[]
    raw_records=raw.to_dict('records')
    odds=v205.load_odds();oi=odds.set_index('race_code',drop=False) if not odds.empty else None
    for mon in EVAL_MONTHS:
        first=pd.Timestamp(mon+'-01');nextm=first+pd.offsets.MonthBegin(1)
        if first>=CONTAM:raise RuntimeError('CONTAMINATION MONTH')
        tr0=d[d._date<first].copy();te0=d[(d._date>=first)&(d._date<nextm)].copy()
        if len(tr0)<200 or te0.empty:continue
        # Pair model is prior-only and shared by all head variants.
        hist=[r for r in raw_records if pd.to_datetime(r.get(dc),errors='coerce')<first]
        pm,pair_n=v166.fit(hist)
        settle_cache={}
        if oi is not None:
            for ix,r in te0.iterrows():
                rr=raw.loc[ix].to_dict();code=str(rr.get('race_code','')).zfill(12)
                if code not in oi.index or v166.ii(rr.get('valid_result'))!=1 or v166.ii(rr.get('course3'),3)!=3:continue
                actual=parse_actual(rr.get('actual_combo'))
                if not actual:continue
                od=oi.loc[code];od=od.iloc[-1] if isinstance(od,pd.DataFrame) else od
                s=settle10(pair_probs(rr,pm),od,actual)
                if s:settle_cache[ix]=s
        for name,fs0 in vv.items():
            fs=[]
            for c in fs0:
                if c not in d.columns:continue
                q=pd.to_numeric(d[c],errors='coerce')
                if q.notna().mean()>=.70:fs.append(c)
            tr=tr0.copy();te=te0.copy()
            for c in fs:
                tr[c]=pd.to_numeric(tr[c],errors='coerce');te[c]=pd.to_numeric(te[c],errors='coerce')
            cats=[vc] if vc and vc not in fs else []
            mo=v165.model(fs,cats);mo.fit(tr[fs+cats],tr._y.astype(int));p=mo.predict_proba(te[fs+cats])[:,1]
            for ix,pr in zip(te.index,p):
                s=settle_cache.get(ix)
                pred.append({'variant':name,'month':mon,'date':te.loc[ix,'_date'].strftime('%Y-%m-%d'),
                             'race_code':str(te.loc[ix].get('race_code','')).zfill(12),'p3head':float(pr),
                             'y3head':int(te.loc[ix,'_y']),'train_rows':len(tr),'n_features':len(fs),
                             'settled':int(s is not None),'hit10':s[0] if s else np.nan,
                             'return_yen':s[1] if s else np.nan,'profit':s[2] if s else np.nan})
    pz=pd.DataFrame(pred)
    if pz.empty:raise SystemExit('no predictions')
    if (pd.to_datetime(pz.date)>=CONTAM).any():raise RuntimeError('CONTAMINATION OUTPUT')
    pz.to_csv(DETAIL,index=False)
    # Baseline p>=.30 selected count per month is used only to volume-match ranking diagnostics.
    base=pz[pz.variant=='BASE'];base_k={m:int((g.p3head>=.30).sum()) for m,g in base.groupby('month')}
    summary=[]
    for (v,m),g in pz.groupby(['variant','month']):
        k=base_k.get(m,0);sel=g.nlargest(k,'p3head') if k>0 else g.iloc[0:0]
        ss=sel[sel.settled==1]
        summary.append({'variant':v,'month':m,'R':len(g),'actual_3head':g.y3head.mean(),
                        'auc':safe_auc(g.y3head,g.p3head),'brier':brier_score_loss(g.y3head,g.p3head),
                        'logloss':safe_logloss(g.y3head,g.p3head),'selected_volume':len(sel),
                        'selected_head_rate':sel.y3head.mean() if len(sel) else np.nan,
                        'settled_selected':len(ss),'roi_top10':100*ss.return_yen.sum()/(BANK*len(ss)) if len(ss) else np.nan,
                        'profit_top10':ss.profit.sum() if len(ss) else np.nan})
    sz=pd.DataFrame(summary);sz.to_csv(OUT,index=False)
    L=['# v220 3-head prior-exhibition + player-trait audit','',
       '- clean evaluation only: **2025-12 through 2026-06**; Jul/Aug hard excluded',
       '- strict monthly prior-only head-model refit',
       '- prior exhibition/original exhibition uses the old v43 idea: frame-corrected historical display + original turn/straight/overall',
       '- conservative daily freeze: same-day earlier races are not used; current day preview/results are ingested only after all races for that day are frozen',
       '- player traits are cumulative prior-only: overall win, boat-3 win, boat-3 makuri/makuri-sashi, recent versions, plus same-venue versions',
       '- historical odds are settlement-only; ROI diagnostic is fixed Top10 + exact 10k Hamilton Dutch',
       '- selection for ROI is **volume-matched** to BASE p>=0.30 count each month; no new threshold is tuned here',
       '- variants are diagnostics, not automatic adoption','',
       '## Aggregate model quality','|variant|R|AUC|Brier|LogLoss|selected R|selected 3-head|Top10 ROI|profit|','|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for v,g in pz.groupby('variant'):
        s=sz[sz.variant==v];sels=[]
        for m,gm in g.groupby('month'):
            k=base_k.get(m,0);sels.append(gm.nlargest(k,'p3head'))
        sel=pd.concat(sels) if sels else g.iloc[0:0];ss=sel[sel.settled==1]
        roi=100*ss.return_yen.sum()/(BANK*len(ss)) if len(ss) else float('nan');profit=ss.profit.sum() if len(ss) else float('nan')
        L.append(f"|{v}|{len(g)}|{safe_auc(g.y3head,g.p3head):.4f}|{brier_score_loss(g.y3head,g.p3head):.5f}|{safe_logloss(g.y3head,g.p3head):.5f}|{len(sel)}|{100*sel.y3head.mean():.2f}%|{roi:.1f}%|{profit:+.0f}|")
    L+=['','## Monthly detail','|variant|month|R|AUC|Brier|selected R|selected 3-head|Top10 ROI|profit|','|---|---|---:|---:|---:|---:|---:|---:|---:|']
    for _,r in sz.iterrows():
        L.append(f"|{r['variant']}|{r['month']}|{int(r['R'])}|{r['auc']:.4f}|{r['brier']:.5f}|{int(r['selected_volume'])}|{100*r['selected_head_rate']:.2f}%|{r['roi_top10']:.1f}%|{r['profit_top10']:+.0f}|")
    L+=['','## Interpretation','- Prefer improvements that repeat across months in AUC/Brier/log loss and selected head rate; ROI is secondary settlement evidence.',
        '- A feature family that improves aggregate ROI but worsens calibration or only works in one month should not be adopted.',
        '- Jul/Aug are not consulted by this audit. After rules are fixed, they may only be shown as descriptive shadow output.',
        '- If history/player features help discrimination but ROI remains below 100%, keep them as head-model candidates and move value selection to prospective live-odds validation rather than tuning on closing odds.']
    SUM.write_text('\n'.join(L)+'\n',encoding='utf-8');print('\n'.join(L))

if __name__=='__main__':main()
