#!/usr/bin/env python3
"""v185: dynamic ticket count for current 3-head production candidates.

Idea
- Keep the production candidate universe fixed at v165/base p3>=0.30.
- Use v180/style probability only to decide HOW MANY v166 tickets to buy.
- Stronger pre-race 3-head signals may be more public/shorter-priced, so spend fewer points.
- Never use current/future result or payout in features/ranking.
- Tune only on Mar-May; freeze policy; evaluate Jun-Aug OOS.

This directly tests the user's idea: when pre-race information already makes boat3 a strong/obvious head,
reduce ticket count rather than filtering the race out.
"""
from __future__ import annotations
from datetime import date
import itertools
import numpy as np
import pandas as pd

from analyze_v165_3head_monthly_walkforward import load,target,feats,model,pc
from analyze_v166_3head_pair_direct import read,fit,order,combo,ff,ii,SRC
from analyze_v177_3head_historical_web_enrichment import reconstruct

OUT='analysis_v185_3head_dynamic_ticket_count.csv'
SUMMARY='summary_v185_3head_dynamic_ticket_count.md'
VAL_MONTHS=['2026-03','2026-04','2026-05']
TEST_MONTHS=['2026-06','2026-07','2026-08']
BASE_CUT=.30
STYLE=['b1_hist_starts','b1_makurare_rate','b1_sasare_rate','b1_escape_rate','b3_hist_starts','b3_makuri_rate','b3_makuri_sashi_rate','b3_head_rate','style_makuri_edge','style_makurisashi_edge']
THS=[.30,.325,.35,.375,.40,.425,.45]
LOW_PTS=[3,5,7]
MID_PTS=[5,7,10]


def build_probs():
    src,df=load(); dc=pc(df,['date','race_date','ymd']); vc=pc(df,['venue','jcd','stadium','place'])
    y,_=target(df); basefs=feats(df)
    raw=read(str(src)); extra,cov=reconstruct(raw)
    d=df.copy(); d['_date']=pd.to_datetime(d[dc].astype(str),errors='coerce'); d['_y']=y
    for k in STYLE:d[k]=[float(extra[i].get(k,0.0)) for i in range(len(df))]
    d=d[d._date.notna()&d._y.notna()].copy()
    rows=[]
    for mon in VAL_MONTHS+TEST_MONTHS:
        m=pd.Timestamp(mon+'-01'); e=m+pd.offsets.MonthBegin(1)
        tr=d[d._date<m].copy(); te=d[(d._date>=m)&(d._date<e)].copy()
        probs={}
        for name,fs in [('base',basefs),('style',basefs+STYLE)]:
            nums=[]
            for c in fs:
                q=pd.to_numeric(d[c],errors='coerce')
                if q.notna().mean()>=.8:
                    tr[c]=pd.to_numeric(tr[c],errors='coerce'); te[c]=pd.to_numeric(te[c],errors='coerce'); nums.append(c)
            cats=[vc] if vc and vc not in nums else []
            mo=model(nums,cats); mo.fit(tr[nums+cats],tr._y.astype(int)); probs[name]=mo.predict_proba(te[nums+cats])[:,1]
        for ix,pb,ps in zip(te.index,probs['base'],probs['style']):
            rows.append({'source_index':int(ix),'date':te.loc[ix,'_date'].strftime('%Y-%m-%d'),'month':mon,'pbase':float(pb),'pstyle':float(ps)})
    return pd.DataFrame(rows),raw,cov


def pair_ranks(raw, probs):
    pm=probs.set_index('source_index').to_dict('index'); out=[]
    for mon in VAL_MONTHS+TEST_MONTHS:
        first=date.fromisoformat(mon+'-01')
        tr=[r for r in raw if date.fromisoformat(r['date'])<first]
        pairm,n=fit(tr)
        for i,r in enumerate(raw):
            if i not in pm or pm[i]['month']!=mon or ii(r.get('valid_result'))!=1: continue
            ranking=order(r,pairm,1.0); act=(r.get('actual_combo') or '').strip()
            z=dict(pm[i]); z.update({'source_index':i,'pair_train':n,'rank':ranking.index(act)+1 if act in ranking else 0,
                                    'actual_combo':act,'payout100':ff(r.get('payout100')),'valid_payout':ii(r.get('valid_payout'))})
            out.append(z)
    return pd.DataFrame(out)


def pts_for(p,hi,mid,small,medium):
    if p>=hi:return small
    if p>=mid:return medium
    return 10


def metric(q,policy):
    if len(q)==0:return {'R':0,'head':0,'hit':0,'roi':0,'avg_pts':0,'cost':0,'ret':0}
    hi,mid,small,medium=policy
    pts=np.array([pts_for(p,hi,mid,small,medium) for p in q.pstyle],int)
    head=np.mean(q.actual_combo.astype(str).str.startswith('3-'))*100
    hit=np.mean((q['rank'].to_numpy()>0)&(q['rank'].to_numpy()<=pts))*100
    settled=q.valid_payout.to_numpy()==1
    cost=float(np.sum(pts[settled]*100))
    wins=settled&(q['rank'].to_numpy()>0)&(q['rank'].to_numpy()<=pts)
    ret=float(np.sum(q.payout100.to_numpy()[wins]))
    roi=100*ret/cost if cost else 0
    return {'R':len(q),'head':head,'hit':hit,'roi':roi,'avg_pts':float(np.mean(pts)),'cost':cost,'ret':ret}


def main():
    probs,raw,cov=build_probs(); d=pair_ranks(raw,probs); d=d[d.pbase>=BASE_CUT].copy()
    val=d[d.month.isin(VAL_MONTHS)].copy(); test=d[d.month.isin(TEST_MONTHS)].copy()
    policies=[]
    for mid,hi in itertools.combinations(THS,2):
        for small in LOW_PTS:
            for medium in MID_PTS:
                if small>medium:continue
                pol=(hi,mid,small,medium); m=metric(val,pol)
                # protect against collapsing coverage too much: require validation hit >= 90% of fixed-10 hit
                policies.append((m['roi'],m['hit'], -m['avg_pts'],pol,m))
    base10=metric(val,(9,8,10,10))
    eligible=[x for x in policies if x[4]['hit']>=.90*base10['hit']]
    best=max(eligible or policies,key=lambda x:(x[0],x[1],x[2]))
    pol=best[3]
    rows=[]
    for label,q in [('VAL',val),('TEST',test)]:
        m=metric(q,pol); b=metric(q,(9,8,10,10)); rows.append({'scope':label,'policy':'dynamic',**m}); rows.append({'scope':label,'policy':'fixed10',**b})
    for mon in TEST_MONTHS:
        q=test[test.month==mon]; rows.append({'scope':mon,'policy':'dynamic',**metric(q,pol)}); rows.append({'scope':mon,'policy':'fixed10',**metric(q,(9,8,10,10))})
    pd.DataFrame(rows).to_csv(OUT,index=False)
    hi,mid,small,medium=pol
    L=['# v185 ③頭 dynamic ticket count OOS','',
       '- 候補母集団は現行productionと同じ v165/base p3>=0.30。','- v180/styleはレース除外に使わず、v166上位何点を買うかだけに使用。','- Mar-Mayだけで点数ルールを固定し、Jun-Augは完全OOS。','- 直前展示・結果・払戻は予測/順位/点数決定に不使用。','',
       f'- reconstruction matched: {cov["matched_src"]}',f'- 固定ルール: style>={hi:.3f} → {small}点, style>={mid:.3f} → {medium}点, それ未満 → 10点','',
       '## Mar-May tuning result','|policy|R|③頭率|hit|平均点数|ROI|','|---|---:|---:|---:|---:|---:|']
    vm=metric(val,pol); L.append(f'|dynamic|{vm["R"]}|{vm["head"]:.2f}%|{vm["hit"]:.2f}%|{vm["avg_pts"]:.2f}|{vm["roi"]:.1f}%|')
    L.append(f'|fixed10|{base10["R"]}|{base10["head"]:.2f}%|{base10["hit"]:.2f}%|{base10["avg_pts"]:.2f}|{base10["roi"]:.1f}%|')
    L += ['','## Jun-Aug fixed OOS','|scope|policy|R|③頭率|hit|平均点数|ROI|','|---|---|---:|---:|---:|---:|---:|']
    for r in rows:
        if r['scope']=='VAL':continue
        L.append(f'|{r["scope"]}|{r["policy"]}|{r["R"]}|{r["head"]:.2f}%|{r["hit"]:.2f}%|{r["avg_pts"]:.2f}|{r["roi"]:.1f}%|')
    L += ['','## Decision','- dynamicがJun-Aug合算でfixed10のROIを上回り、月別でも極端に崩れず、hit低下が許容範囲なら採用候補。','- ROIが上がらない、またはhitが大きく落ちるなら「v180で点数削減」は不採用。']
    open(SUMMARY,'w',encoding='utf-8').write('\n'.join(L)+'\n'); print('\n'.join(L))

if __name__=='__main__':main()
