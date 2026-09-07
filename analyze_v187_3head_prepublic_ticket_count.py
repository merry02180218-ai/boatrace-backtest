#!/usr/bin/env python3
"""v187: dynamic 3-head ticket count using exact pre-close market popularity of boat 3.

Why this revision
- The first v187 tried to rebuild a pure PRE card+waku10 proxy for Mar-May, but the public
  historical card/waku10 archive used by this repo does not cover enough of Mar-May 2026.
- We therefore test the user's market-popularity hypothesis directly with the stored official
  pre-close trifecta odds (`data/previews/od3/YYYY/MM/DD.csv`).

No-leak
- Candidate universe = strict monthly-WF v165/base p3>=0.30.
- Ticket ordering = v166 direct ordered-pair lambda=1.00.
- Ticket-count signal = PRE-CLOSE trifecta odds only, loaded before any result/payout use.
- Mar-May tunes thresholds; Jun-Aug is frozen OOS.
- Results/payouts are settlement-only after selection/ranking/count are fixed.
"""
from __future__ import annotations
from datetime import date
import csv, io, itertools, urllib.request
import numpy as np
import pandas as pd
from analyze_v165_3head_monthly_walkforward import load,target,feats,model,pc
from analyze_v166_3head_pair_direct import read,fit,order,ff,ii,SRC

RAW='https://raw.githubusercontent.com/BoatraceCSV/boatracecsv.github.io/main/'
OUT='analysis_v187_3head_prepublic_ticket_count.csv'
SUMMARY='summary_v187_3head_prepublic_ticket_count.md'
VAL_MONTHS=['2026-03','2026-04','2026-05']
TEST_MONTHS=['2026-06','2026-07','2026-08']
BASE_CUT=.30


def build_base_probs():
    src,df=load(); dc=pc(df,['date','race_date','ymd']); vc=pc(df,['venue','jcd','stadium','place'])
    y,_=target(df); fs=feats(df)
    d=df.copy(); d['_date']=pd.to_datetime(d[dc].astype(str),errors='coerce'); d['_y']=y
    d=d[d._date.notna()&d._y.notna()].copy(); out=[]
    for mon in VAL_MONTHS+TEST_MONTHS:
        m=pd.Timestamp(mon+'-01'); e=m+pd.offsets.MonthBegin(1)
        tr=d[d._date<m].copy(); te=d[(d._date>=m)&(d._date<e)].copy()
        nums=[]
        for c in fs:
            q=pd.to_numeric(d[c],errors='coerce')
            if q.notna().mean()>=.8:
                tr[c]=pd.to_numeric(tr[c],errors='coerce'); te[c]=pd.to_numeric(te[c],errors='coerce'); nums.append(c)
        cats=[vc] if vc and vc not in nums else []
        mo=model(nums,cats); mo.fit(tr[nums+cats],tr._y.astype(int)); p=mo.predict_proba(te[nums+cats])[:,1]
        for ix,pr in zip(te.index,p):
            out.append({'source_index':int(ix),'date':te.loc[ix,'_date'].strftime('%Y-%m-%d'),'month':mon,'pbase':float(pr)})
    return pd.DataFrame(out)


def fetch_csv(path):
    try:
        req=urllib.request.Request(RAW+path,headers={'User-Agent':'Mozilla/5.0'})
        with urllib.request.urlopen(req,timeout=30) as r:
            s=r.read().decode('utf-8-sig')
        return list(csv.DictReader(io.StringIO(s)))
    except Exception as e:
        print('od3 fetch fail',path,e,flush=True); return []


def odds_map(dates):
    out={}; cov=0
    for k,ds in enumerate(sorted(set(dates)),1):
        ymd=ds.replace('-','/')
        rows=fetch_csv(f'data/previews/od3/{ymd}.csv')
        for r in rows:
            code=(r.get('レースコード') or '').strip()
            if not code: continue
            inv_all=0.0; inv3=0.0; valid=0
            for h in range(1,7):
                for s in range(1,7):
                    if s==h: continue
                    for t in range(1,7):
                        if t in (h,s): continue
                        o=ff(r.get(f'3連単_{h}-{s}-{t}'),0)
                        if o>1e-9:
                            inv=1.0/o; inv_all+=inv; valid+=1
                            if h==3: inv3+=inv
            if inv_all>0 and valid>=100:
                # Share of total market implied probability allocated to 3-head combinations.
                out[(ds,code)]={'market3_share':inv3/inv_all,'odds_valid':valid,
                                'odds_acquired':r.get('取得日時',''),'deadline':r.get('締切時刻','')}
                cov+=1
        if k%30==0: print('od3 days',k,'races',cov,flush=True)
    return out


def build_eval(raw,probs):
    pm=probs.set_index('source_index').to_dict('index'); om=odds_map(probs.date.tolist()); out=[]; misses=0
    for mon in VAL_MONTHS+TEST_MONTHS:
        first=date.fromisoformat(mon+'-01'); tr=[r for r in raw if date.fromisoformat(r['date'])<first]
        pairm,n=fit(tr)
        for i,r in enumerate(raw):
            p=pm.get(i)
            if not p or p['month']!=mon or ii(r.get('valid_result'))!=1: continue
            ds=r.get('date',''); code=(r.get('race_code') or '').strip(); od=om.get((ds,code))
            if not od: misses+=1; continue
            ranking=order(r,pairm,1.0); act=(r.get('actual_combo') or '').strip()
            out.append({'source_index':i,'date':ds,'month':mon,'race_code':code,'pbase':p['pbase'],
                        'pre_public':float(od['market3_share']),'odds_valid':od['odds_valid'],
                        'odds_acquired':od['odds_acquired'],'deadline':od['deadline'],'pair_train':n,
                        'rank':ranking.index(act)+1 if act in ranking else 0,'actual_combo':act,
                        'payout100':ff(r.get('payout100')),'valid_payout':ii(r.get('valid_payout'))})
    print('joined',len(out),'misses',misses,flush=True)
    return pd.DataFrame(out)


def pts_for(v,hi,mid,small,medium):
    if v>=hi:return small
    if v>=mid:return medium
    return 10


def metric(q,pol):
    if len(q)==0:return {'R':0,'head':0,'hit':0,'avg_pts':0,'roi':0}
    hi,mid,small,medium=pol
    pts=np.array([pts_for(v,hi,mid,small,medium) for v in q.pre_public],int)
    rank=q['rank'].to_numpy(); settled=q.valid_payout.to_numpy()==1
    head=np.mean(q.actual_combo.astype(str).str.startswith('3-'))*100
    hit=np.mean((rank>0)&(rank<=pts))*100
    cost=float(np.sum(pts[settled]*100)); wins=settled&(rank>0)&(rank<=pts)
    ret=float(np.sum(q.payout100.to_numpy()[wins])); roi=100*ret/cost if cost else 0
    return {'R':len(q),'head':head,'hit':hit,'avg_pts':float(np.mean(pts)),'roi':roi}


def fixed10(q): return metric(q,(9,8,10,10))


def main():
    probs=build_base_probs(); raw=read(SRC); d=build_eval(raw,probs)
    if d.empty: raise SystemExit('v187 no joined pre-close odds rows')
    d=d[d.pbase>=BASE_CUT].copy(); val=d[d.month.isin(VAL_MONTHS)].copy(); test=d[d.month.isin(TEST_MONTHS)].copy()
    print('candidate rows val/test',len(val),len(test),flush=True)
    if val.empty or test.empty: raise SystemExit(f'v187 insufficient candidate rows val={len(val)} test={len(test)}')
    qs=sorted(set(float(x) for x in np.quantile(val.pre_public,[.40,.50,.60,.70,.80,.90])))
    if len(qs)<2: raise SystemExit(f'v187 insufficient distinct thresholds: {qs}')
    base=fixed10(val); cands=[]
    for mid,hi in itertools.combinations(qs,2):
        for small in [5,7]:
            for medium in [7,10]:
                if small>medium: continue
                pol=(hi,mid,small,medium); m=metric(val,pol)
                if m['hit']>=.92*base['hit'] and m['avg_pts']<=9.5:
                    cands.append((m['roi'],m['hit'],-m['avg_pts'],pol,m))
    if not cands:
        for mid,hi in itertools.combinations(qs,2):
            pol=(hi,mid,7,10); m=metric(val,pol); cands.append((m['roi'],m['hit'],-m['avg_pts'],pol,m))
    best=max(cands,key=lambda x:(x[0],x[1],x[2])); pol=best[3]
    rows=[]
    for scope,q in [('VAL',val),('TEST',test)]:
        rows.append({'scope':scope,'policy':'dynamic',**metric(q,pol)}); rows.append({'scope':scope,'policy':'fixed10',**fixed10(q)})
    for mon in TEST_MONTHS:
        q=test[test.month==mon]; rows.append({'scope':mon,'policy':'dynamic',**metric(q,pol)}); rows.append({'scope':mon,'policy':'fixed10',**fixed10(q)})
    pd.DataFrame(rows).to_csv(OUT,index=False)
    hi,mid,small,medium=pol
    L=['# v187 ③頭 PRE-CLOSE market-popularity dynamic ticket OOS','',
       '- 初版のcard+waku10代理はMar-Mayの公開履歴不足で検証不能だったため、保存済み公式締切前od3で市場人気を直接計測。',
       '- 候補母集団: strict monthly-WF v165/base p3>=0.30。','- 買い目順位: v166 direct ordered-pair λ=1.00。',
       '- pre_public = 全120組の1/odds合計に対する③頭20組の1/odds合計シェア。結果・払戻は不使用。',
       '- Mar-Mayで閾値・点数を固定、Jun-Aug完全OOS。払戻はsettlementのみ。','',
       f'- fixed rule: market3_share>={hi:.4f} → {small}点, >={mid:.4f} → {medium}点, else 10点','',
       '## Results','|scope|policy|R|③頭率|hit|平均点数|ROI|','|---|---|---:|---:|---:|---:|---:|']
    for r in rows:L.append(f'|{r["scope"]}|{r["policy"]}|{r["R"]}|{r["head"]:.2f}%|{r["hit"]:.2f}%|{r["avg_pts"]:.2f}|{r["roi"]:.1f}%|')
    L += ['','## Decision','- Jun-Aug合算でfixed10のROIを上回り、hit低下が小さく月別も崩れなければ採用候補。','- 上回らなければ「③が市場で売れている時だけ点数削減」仮説は不採用。']
    open(SUMMARY,'w',encoding='utf-8').write('\n'.join(L)+'\n'); print('\n'.join(L))

if __name__=='__main__':main()
