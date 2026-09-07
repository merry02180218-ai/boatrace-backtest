#!/usr/bin/env python3
"""v187: dynamic 3-head ticket count using exact pre-close market popularity.

Revision: official od3 archive is only available for part of Jun-Aug 2026, so do not
pretend Mar-May odds exist. Build the current v165 candidate universe for Jun-Aug,
join only races with stored pre-close od3, then make one strict chronological split
inside the actually available odds sample: first 50% by date/race order = rule tuning,
last 50% = untouched OOS. Result/payout is settlement-only.
"""
from __future__ import annotations
from datetime import date
import csv, io, itertools, urllib.request
import numpy as np
import pandas as pd
from analyze_v165_3head_monthly_walkforward import load,target,feats,model,pc
from analyze_v166_3head_pair_direct import read,fit,order,ff,ii,SRC
RAW='https://raw.githubusercontent.com/BoatraceCSV/boatracecsv.github.io/main/'
OUT='analysis_v187_3head_prepublic_ticket_count.csv'; SUMMARY='summary_v187_3head_prepublic_ticket_count.md'
MONTHS=['2026-06','2026-07','2026-08']; BASE_CUT=.30

def build_base_probs():
    src,df=load(); dc=pc(df,['date','race_date','ymd']); vc=pc(df,['venue','jcd','stadium','place']); y,_=target(df); fs=feats(df)
    d=df.copy(); d['_date']=pd.to_datetime(d[dc].astype(str),errors='coerce'); d['_y']=y; d=d[d._date.notna()&d._y.notna()].copy(); out=[]
    for mon in MONTHS:
        m=pd.Timestamp(mon+'-01'); e=m+pd.offsets.MonthBegin(1); tr=d[d._date<m].copy(); te=d[(d._date>=m)&(d._date<e)].copy(); nums=[]
        for c in fs:
            q=pd.to_numeric(d[c],errors='coerce')
            if q.notna().mean()>=.8: tr[c]=pd.to_numeric(tr[c],errors='coerce'); te[c]=pd.to_numeric(te[c],errors='coerce'); nums.append(c)
        cats=[vc] if vc and vc not in nums else []; mo=model(nums,cats); mo.fit(tr[nums+cats],tr._y.astype(int)); p=mo.predict_proba(te[nums+cats])[:,1]
        for ix,pr in zip(te.index,p): out.append({'source_index':int(ix),'date':te.loc[ix,'_date'].strftime('%Y-%m-%d'),'month':mon,'pbase':float(pr)})
    return pd.DataFrame(out)

def fetch_csv(path):
    try:
        req=urllib.request.Request(RAW+path,headers={'User-Agent':'Mozilla/5.0'}); s=urllib.request.urlopen(req,timeout=30).read().decode('utf-8-sig'); return list(csv.DictReader(io.StringIO(s)))
    except Exception: return []

def odds_map(dates):
    out={}
    for ds in sorted(set(dates)):
        rows=fetch_csv(f'data/previews/od3/{ds.replace("-","/")}.csv')
        for r in rows:
            code=(r.get('レースコード') or '').strip(); inv_all=inv3=0.; valid=0
            if not code: continue
            for h in range(1,7):
                for s in range(1,7):
                    if s==h: continue
                    for t in range(1,7):
                        if t in (h,s): continue
                        o=ff(r.get(f'3連単_{h}-{s}-{t}'),0)
                        if o>0: inv=1/o; inv_all+=inv; valid+=1; inv3 += inv if h==3 else 0
            if inv_all>0 and valid>=100: out[(ds,code)]={'pre_public':inv3/inv_all,'odds_acquired':r.get('取得日時',''),'deadline':r.get('締切時刻','')}
    return out

def build_eval(raw,probs):
    pm=probs.set_index('source_index').to_dict('index'); om=odds_map(probs.date.tolist()); out=[]
    for mon in MONTHS:
        first=date.fromisoformat(mon+'-01'); pairm,n=fit([r for r in raw if date.fromisoformat(r['date'])<first])
        for i,r in enumerate(raw):
            p=pm.get(i)
            if not p or p['month']!=mon or p['pbase']<BASE_CUT or ii(r.get('valid_result'))!=1: continue
            ds=r.get('date',''); code=(r.get('race_code') or '').strip(); od=om.get((ds,code))
            if not od: continue
            ranking=order(r,pairm,1.0); act=(r.get('actual_combo') or '').strip()
            out.append({'source_index':i,'date':ds,'month':mon,'race_code':code,'pbase':p['pbase'],'pre_public':od['pre_public'],'odds_acquired':od['odds_acquired'],'deadline':od['deadline'],'pair_train':n,'rank':ranking.index(act)+1 if act in ranking else 0,'actual_combo':act,'payout100':ff(r.get('payout100')),'valid_payout':ii(r.get('valid_payout'))})
    return pd.DataFrame(out).sort_values(['date','race_code']).reset_index(drop=True)

def pts_for(v,hi,mid,small,medium): return small if v>=hi else medium if v>=mid else 10
def metric(q,pol):
    if q.empty:return {'R':0,'head':0,'hit':0,'avg_pts':0,'roi':0}
    hi,mid,small,medium=pol; pts=np.array([pts_for(v,hi,mid,small,medium) for v in q.pre_public]); rank=q['rank'].to_numpy(); settled=q.valid_payout.to_numpy()==1
    wins=settled&(rank>0)&(rank<=pts); cost=float(np.sum(pts[settled]*100)); ret=float(np.sum(q.payout100.to_numpy()[wins]))
    return {'R':len(q),'head':100*np.mean(q.actual_combo.astype(str).str.startswith('3-')),'hit':100*np.mean((rank>0)&(rank<=pts)),'avg_pts':float(np.mean(pts)),'roi':100*ret/cost if cost else 0}
def fixed10(q): return metric(q,(9,8,10,10))

def main():
    raw=read(SRC); d=build_eval(raw,build_base_probs())
    if len(d)<40: raise SystemExit(f'v187 too few available od3 candidate races: {len(d)}')
    split=len(d)//2; val=d.iloc[:split].copy(); test=d.iloc[split:].copy(); split_date=test.iloc[0]['date']
    qs=sorted(set(float(x) for x in np.quantile(val.pre_public,[.40,.50,.60,.70,.80,.90]))); base=fixed10(val); cands=[]
    for mid,hi in itertools.combinations(qs,2):
        for small in [5,7]:
            for medium in [7,10]:
                if small>medium: continue
                pol=(hi,mid,small,medium); m=metric(val,pol)
                if m['hit']>=.92*base['hit'] and m['avg_pts']<=9.5: cands.append((m['roi'],m['hit'],-m['avg_pts'],pol))
    if not cands:
        for mid,hi in itertools.combinations(qs,2):
            pol=(hi,mid,7,10); m=metric(val,pol); cands.append((m['roi'],m['hit'],-m['avg_pts'],pol))
    pol=max(cands,key=lambda x:(x[0],x[1],x[2]))[3]; rows=[]
    for scope,q in [('TUNE_FIRST_HALF',val),('OOS_SECOND_HALF',test)]: rows += [{'scope':scope,'policy':'dynamic',**metric(q,pol)},{'scope':scope,'policy':'fixed10',**fixed10(q)}]
    for mon in MONTHS:
        q=test[test.month==mon]
        if len(q): rows += [{'scope':'OOS_'+mon,'policy':'dynamic',**metric(q,pol)},{'scope':'OOS_'+mon,'policy':'fixed10',**fixed10(q)}]
    pd.DataFrame(rows).to_csv(OUT,index=False); hi,mid,small,medium=pol
    L=['# v187 ③頭 締切前市場人気 dynamic ticket chronological OOS','',f'- od3結合候補: {len(d)}R。実在od3期間内を時系列で前半{len(val)}R=ルール決定、後半{len(test)}R=完全OOS。',f'- OOS開始日: {split_date}','- 候補母集団: strict monthly-WF v165 p3>=0.30。順位: v166 λ=1.00。','- pre_public = 全120組の1/odds合計に対する③頭20組の1/oddsシェア。','- 結果・払戻は点数決定後のsettlementのみ。','',f'- fixed rule: share>={hi:.4f} → {small}点, >={mid:.4f} → {medium}点, else 10点','','|scope|policy|R|③頭率|hit|平均点数|ROI|','|---|---|---:|---:|---:|---:|---:|']
    for r in rows:L.append(f'|{r["scope"]}|{r["policy"]}|{r["R"]}|{r["head"]:.2f}%|{r["hit"]:.2f}%|{r["avg_pts"]:.2f}|{r["roi"]:.1f}%|')
    open(SUMMARY,'w',encoding='utf-8').write('\n'.join(L)+'\n'); print('\n'.join(L))
if __name__=='__main__': main()
