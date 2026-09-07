#!/usr/bin/env python3
"""v186: dynamic 3-head ticket count from v166 ordered-pair probability concentration.

Keep production candidate universe fixed at v165/base p3>=0.30.
Do NOT use v180 p3 as the ticket-count gate. Instead use concentration of the
v166 ordered-pair model itself: if probability mass is concentrated in the top
few 3-s-t pairs, buy fewer tickets; if diffuse, keep 10.

Tune only on Mar-May, freeze, evaluate Jun-Aug OOS. Result/payout are settlement-only.
"""
from __future__ import annotations
from datetime import date
import itertools, math
import numpy as np
import pandas as pd

from analyze_v165_3head_monthly_walkforward import load,target,feats,model,pc
from analyze_v166_3head_pair_direct import read,fit,pvec,combo,ff,ii,SRC,OPP

OUT='analysis_v186_3head_pair_concentration_ticket_count.csv'
SUMMARY='summary_v186_3head_pair_concentration_ticket_count.md'
VAL_MONTHS=['2026-03','2026-04','2026-05']
TEST_MONTHS=['2026-06','2026-07','2026-08']
BASE_CUT=.30
QUANTILES=[.50,.60,.70,.80,.90]
SMALL_PTS=[5,7]
MID_PTS=[7,10]


def build_base_probs():
    src,df=load(); dc=pc(df,['date','race_date','ymd']); vc=pc(df,['venue','jcd','stadium','place'])
    y,_=target(df); fs=feats(df)
    d=df.copy(); d['_date']=pd.to_datetime(d[dc].astype(str),errors='coerce'); d['_y']=y
    rows=[]
    for mon in VAL_MONTHS+TEST_MONTHS:
        m=pd.Timestamp(mon+'-01'); e=m+pd.offsets.MonthBegin(1)
        tr=d[d._date<m].copy(); te=d[(d._date>=m)&(d._date<e)].copy(); nums=[]
        for c in fs:
            q=pd.to_numeric(d[c],errors='coerce')
            if q.notna().mean()>=.8:
                tr[c]=pd.to_numeric(tr[c],errors='coerce');te[c]=pd.to_numeric(te[c],errors='coerce');nums.append(c)
        cats=[vc] if vc and vc not in nums else []
        mo=model(nums,cats); mo.fit(tr[nums+cats],tr._y.astype(int)); p=mo.predict_proba(te[nums+cats])[:,1]
        for ix,pr in zip(te.index,p): rows.append({'source_index':int(ix),'month':mon,'pbase':float(pr)})
    return pd.DataFrame(rows),read(str(src))


def pair_info(raw, probs):
    pm=probs.set_index('source_index').to_dict('index'); out=[]
    for mon in VAL_MONTHS+TEST_MONTHS:
        first=date.fromisoformat(mon+'-01'); tr=[r for r in raw if date.fromisoformat(r['date'])<first]
        pairm,n=fit(tr)
        for i,r in enumerate(raw):
            if i not in pm or pm[i]['month']!=mon or ii(r.get('valid_result'))!=1: continue
            pairs=[]
            for s in OPP:
                for t in OPP:
                    if s==t: continue
                    q=float(pairm.predict_proba(np.asarray([pvec(r,s,t)],float))[0,1]); pairs.append((q,s,t))
            pairs.sort(key=lambda z:(-z[0],z[1],z[2]))
            qs=np.asarray([max(z[0],1e-12) for z in pairs],float); w=qs/qs.sum()
            act=(r.get('actual_combo') or '').strip(); labels=[f'3-{s}-{t}' for _,s,t in pairs]
            rank=labels.index(act)+1 if act in labels else 0
            ent=float(-np.sum(w*np.log(w))/math.log(len(w)))
            z=dict(pm[i]); z.update({'source_index':i,'pair_train':n,'rank':rank,'actual_combo':act,
                'payout100':ff(r.get('payout100')),'valid_payout':ii(r.get('valid_payout')),
                'c3':float(w[:3].sum()),'c5':float(w[:5].sum()),'c7':float(w[:7].sum()),
                'top1':float(w[0]),'gap15':float(w[0]-w[4]),'entropy':ent})
            out.append(z)
    return pd.DataFrame(out)


def pts_for(c5,hi,mid,small,medium):
    if c5>=hi:return small
    if c5>=mid:return medium
    return 10


def metric(q,pol):
    if len(q)==0:return {'R':0,'head':0,'hit':0,'roi':0,'avg_pts':0}
    hi,mid,small,medium=pol
    pts=np.asarray([pts_for(x,hi,mid,small,medium) for x in q.c5],int)
    rank=q['rank'].to_numpy(); settled=q.valid_payout.to_numpy()==1
    head=float(np.mean(q.actual_combo.astype(str).str.startswith('3-'))*100)
    hit=float(np.mean((rank>0)&(rank<=pts))*100)
    cost=float(np.sum(pts[settled]*100)); wins=settled&(rank>0)&(rank<=pts)
    ret=float(np.sum(q.payout100.to_numpy()[wins])); roi=100*ret/cost if cost else 0
    return {'R':len(q),'head':head,'hit':hit,'roi':roi,'avg_pts':float(np.mean(pts))}


def main():
    probs,raw=build_base_probs(); d=pair_info(raw,probs); d=d[d.pbase>=BASE_CUT].copy()
    val=d[d.month.isin(VAL_MONTHS)].copy(); test=d[d.month.isin(TEST_MONTHS)].copy()
    base10=metric(val,(9,8,10,10))
    qs=sorted(set(float(val.c5.quantile(q)) for q in QUANTILES))
    cand=[]
    for mid,hi in itertools.combinations(qs,2):
        for small in SMALL_PTS:
            for medium in MID_PTS:
                if small>medium:continue
                pol=(hi,mid,small,medium); m=metric(val,pol)
                # guard: retain >=92% of fixed10 validation hit and at least 25 races in reduced-ticket bins
                reduced=sum(1 for x in val.c5 if x>=mid)
                if reduced<25:continue
                cand.append((m['roi'],m['hit'],-m['avg_pts'],pol,m))
    eligible=[x for x in cand if x[4]['hit']>=.92*base10['hit']]
    best=max(eligible or cand,key=lambda x:(x[0],x[1],x[2])); pol=best[3]
    rows=[]
    for label,q in [('VAL',val),('TEST',test)]:
        rows.append({'scope':label,'policy':'dynamic',**metric(q,pol)})
        rows.append({'scope':label,'policy':'fixed10',**metric(q,(9,8,10,10))})
    for mon in TEST_MONTHS:
        q=test[test.month==mon]
        rows.append({'scope':mon,'policy':'dynamic',**metric(q,pol)})
        rows.append({'scope':mon,'policy':'fixed10',**metric(q,(9,8,10,10))})
    pd.DataFrame(rows).to_csv(OUT,index=False)
    hi,mid,small,medium=pol
    L=['# v186 ③頭 v166 pair-concentration dynamic ticket OOS','',
       '- 候補母集団は現行productionと同じ v165/base p3>=0.30。',
       '- 点数判断にはv180を使わず、v166 ordered-pair予測20組の確率集中度だけを使用。',
       '- 各レースの20組pair確率を正規化し、top5累積確率(c5)で5/7/10点を切替。',
       '- Mar-Mayだけで閾値・点数を固定。Jun-Augは完全OOS。結果・払戻はsettlementのみ。','',
       f'- 固定ルール: c5>={hi:.4f} → {small}点, c5>={mid:.4f} → {medium}点, それ未満 → 10点','',
       '## Mar-May tuning','|policy|R|③頭率|hit|平均点数|ROI|','|---|---:|---:|---:|---:|---:|']
    vm=metric(val,pol)
    L.append(f'|dynamic|{vm["R"]}|{vm["head"]:.2f}%|{vm["hit"]:.2f}%|{vm["avg_pts"]:.2f}|{vm["roi"]:.1f}%|')
    L.append(f'|fixed10|{base10["R"]}|{base10["head"]:.2f}%|{base10["hit"]:.2f}%|{base10["avg_pts"]:.2f}|{base10["roi"]:.1f}%|')
    L += ['','## Jun-Aug fixed OOS','|scope|policy|R|③頭率|hit|平均点数|ROI|','|---|---|---:|---:|---:|---:|---:|']
    for r in rows:
        if r['scope']=='VAL':continue
        L.append(f'|{r["scope"]}|{r["policy"]}|{r["R"]}|{r["head"]:.2f}%|{r["hit"]:.2f}%|{r["avg_pts"]:.2f}|{r["roi"]:.1f}%|')
    L += ['','## Decision','- dynamicがJun-Aug合算ROIでfixed10を上回り、月別安定性とhitを維持できれば採用候補。','- 合算ROIが下がる、または月別崩れが大きければ固定10点を維持。']
    open(SUMMARY,'w',encoding='utf-8').write('\n'.join(L)+'\n');print('\n'.join(L))

if __name__=='__main__':main()
