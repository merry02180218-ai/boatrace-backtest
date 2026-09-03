"""v43: prior 1/2 starts lane-corrected exhibition test, optimized.
No current-race exhibition, actual entry/course, or result-derived scoring feature.
"""
import csv
from collections import defaultdict,deque
from datetime import date,timedelta
from backtest_v20_week import *
from backtest_v3 import CORR, expo_rows_to_records
from backtest_v4 import clean_name, rank_strength
from backtest_v34_tilt_compare import target34

TR0=date(2026,6,1);TR1=date(2026,7,15);VA1=date(2026,8,2);TE1=date(2026,9,2)
MODELS=['3まくり','3まくり差し','4カドまくり','5頭展開']
BOAT={'3まくり':3,'3まくり差し':3,'4カドまくり':4,'5頭展開':5}

def day_preview(day):
    ymd=day.strftime('%Y/%m/%d')
    card_rows=rows(f'data/programs/race_cards/{ymd}.csv')
    cards={r['レースコード']:r for r in card_rows}
    orig={r['レースコード']:r for r in rows(f'data/previews/original_exhibition/{ymd}.csv')}
    tk={r['レースコード']:r for r in rows(f'data/previews/tkz/{ymd}.csv')}
    out=[]
    for code,card in cards.items():
        venue=str(card.get('レース場コード','')).zfill(2)
        om={}
        if code in orig:
            for z in expo_rows_to_records([orig[code]]): om[clean_name(z['name'])]=z
        vals=[]
        tr=tk.get(code,{})
        for b in range(1,7):
            v=tr.get(f'艇{b}_展示タイム','')
            if v!='': vals.append((b,f(v,99)+CORR[b]['展示']))
        dr=rank_strength(vals) if vals else {}
        for b in range(1,7):
            name=clean_name(card.get(f'艇{b}_選手名'))
            if not name: continue
            z=om.get(name,{})
            out.append((venue,name,{'display':dr.get(b,.5),'overall':z.get('overall',.5),'turn':z.get('turn',.5),'straight':z.get('straight',.5)}))
    return out

def hf(hist,key,n):
    a=list(hist.get(key,[]))[-n:]
    if not a:return {'display':.5,'overall':.5,'turn':.5,'straight':.5}
    ws=[1.] if len(a)==1 else [.4,.6]
    return {k:sum(w*z[k] for w,z in zip(ws,a))/sum(ws) for k in ['display','overall','turn','straight']}

def ps(z,m):
    if m in ('3まくり','4カドまくり'): return .35*z['display']+.15*z['overall']+.15*z['turn']+.35*z['straight']
    if m=='3まくり差し': return .15*z['display']+.15*z['overall']+.40*z['turn']+.30*z['straight']
    return .10*z['display']+.20*z['overall']+.45*z['turn']+.25*z['straight']

def main():
    cache={};mh=defaultdict(list);seen=set();ph=defaultdict(lambda:deque(maxlen=2));allrows=[];d=PRELOAD_START
    while d<=TE1:
        active=d>=TR0-timedelta(days=12)
        if active:
            feats=process_features(d,cache,mh) if d>=TR0 else []
            if d>=TR0:
                ymd=d.strftime('%Y/%m/%d');res={r['レースコード']:r for r in rows(f'data/results/realtime/{ymd}.csv')}
                period='train' if d<=TR1 else 'validation' if d<=VA1 else 'latest_month'
                for r,x,s4,s5,dc in feats:
                    s3=score3v4(x);venue=str(r.get('レース場コード','')).zfill(2)
                    for m in MODELS:
                        if not passes(features(x,s3,s4,dc,m),RULES[m]):continue
                        name=clean_name(r.get(f'艇{BOAT[m]}_選手名'));key=(venue,name)
                        allrows.append({'period':period,'date':str(d),'race_code':r['レースコード'],'model':m,'target':target34(res.get(r['レースコード'],{}),m),'prior1':ps(hf(ph,key,1),m),'prior2':ps(hf(ph,key,2),m),'has2':int(len(ph.get(key,[]))>=2)})
            # Critical optimization: cards are read once/day, not once for every boat record.
            for venue,name,z in day_preview(d): ph[(venue,name)].append(z)
            ingest_prior_day_preview(cache,d)
        ingest_motor(mh,seen,d);d+=timedelta(days=1)
    cuts={}
    for m in MODELS:
      for v in ['prior1','prior2']:
        a=sorted(z[v] for z in allrows if z['period']=='train' and z['model']==m and (v=='prior1' or z['has2']))
        cuts[(m,v)]=a[int(.60*(len(a)-1))] if a else .5
    rate=lambda q:100*sum(z['target'] for z in q)/len(q) if q else 0
    L=['# v43 前走・前々走 枠補正展示の事前候補検証','','過去走の当時枠で展示/オリジナル展示を補正。前走のみ vs 前走+前々走(前走60%,前々走40%)。当日展示・実進入・艇N_コース不使用。同日走は日次事前候補では使わない。','','|期間|モデル|基準候補R/率|前走上位R/率|前走+前々走上位R/率|2走化差|','|---|---|---:|---:|---:|---:|']
    for p in ['train','validation','latest_month']:
      for m in MODELS:
        a=[z for z in allrows if z['period']==p and z['model']==m];b=[z for z in a if z['prior1']>=cuts[(m,'prior1')]];c=[z for z in a if z['has2'] and z['prior2']>=cuts[(m,'prior2')]]
        L.append(f'|{p}|{m}|{len(a)}R/{rate(a):.1f}%|{len(b)}R/{rate(b):.1f}%|{len(c)}R/{rate(c):.1f}%|{rate(c)-rate(b):+.1f}pt|')
    L+=['','判定: validationを最優先。latest_monthは反復検証済みなので参考。前々走追加が学習だけ改善する場合は採用しない。']
    with open('analysis_v43_prior2_lane_corrected.csv','w',newline='',encoding='utf-8-sig') as fo:
      w=csv.DictWriter(fo,fieldnames=allrows[0].keys());w.writeheader();w.writerows(allrows)
    open('summary_v43_prior2_lane_corrected.md','w',encoding='utf-8').write('\n'.join(L)+'\n')
if __name__=='__main__':main()
