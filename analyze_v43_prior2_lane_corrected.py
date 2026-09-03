"""v43: pre-race candidate test using lane-corrected exhibition/original exhibition from prior 1 and prior 2 starts.
No current-race exhibition, actual entry, or result-derived feature is used for candidate scoring.
"""
import csv
from collections import defaultdict,deque
from datetime import date,timedelta
from backtest_v20_week import *
from backtest_v3 import CORR, EW, expo_rows_to_records
from backtest_v4 import clean_name, rank_strength
from backtest_v34_tilt_compare import target34

TR0=date(2026,6,1);TR1=date(2026,7,15);VA0=date(2026,7,16);VA1=date(2026,8,2);TE0=date(2026,8,3);TE1=date(2026,9,2)
MODELS=['3まくり','3まくり差し','4カドまくり','5頭展開']
BOAT={'3まくり':3,'3まくり差し':3,'4カドまくり':4,'5頭展開':5}

def preview_records(day):
    ymd=day.strftime('%Y/%m/%d'); cards={r['レースコード']:r for r in rows(f'data/programs/race_cards/{ymd}.csv')}; orig={r['レースコード']:r for r in rows(f'data/previews/original_exhibition/{ymd}.csv')}; tk={r['レースコード']:r for r in rows(f'data/previews/tkz/{ymd}.csv')}; out=[]
    for code,card in cards.items():
        oo=orig.get(code); tr=tk.get(code); om={}
        if oo:
            for z in expo_rows_to_records([oo]): om[clean_name(z['name'])]=z
        dr={}
        if tr:
            vals=[]
            for b in range(1,7):
                v=tr.get(f'艇{b}_展示タイム','')
                if v!='': vals.append((b,f(v,99)+CORR[b]['展示']))
            rs=rank_strength(vals) if vals else {}
            for b,s in rs.items():dr[clean_name(card.get(f'艇{b}_選手名'))]=s
        for b in range(1,7):
            name=clean_name(card.get(f'艇{b}_選手名')); z=om.get(name,{})
            if name: out.append((code,b,name,{'display':dr.get(name,.5),'overall':z.get('overall',.5),'turn':z.get('turn',.5),'straight':z.get('straight',.5)}))
    return out

def hist_feature(hist,venue,name,nprev):
    a=list(hist.get((venue,name),[]))[-nprev:]
    if not a:return {'display':.5,'overall':.5,'turn':.5,'straight':.5}
    # recency weighting: previous race 60%, previous-previous 40%.
    ws=([1.] if len(a)==1 else [.4,.6])
    return {k:sum(w*z[k] for w,z in zip(ws,a))/sum(ws) for k in ['display','overall','turn','straight']}

def prior_score(z,m):
    if m in ('3まくり','4カドまくり'): return .35*z['display']+.15*z['overall']+.15*z['turn']+.35*z['straight']
    if m=='3まくり差し': return .15*z['display']+.15*z['overall']+.40*z['turn']+.30*z['straight']
    return .10*z['display']+.20*z['overall']+.45*z['turn']+.25*z['straight']

def main():
    # Existing process_features supplies baseline pre-race eligibility. Separate history below tracks exactly prior two starts and their historical frame corrections.
    cache={};mh=defaultdict(list);seen=set();ph=defaultdict(lambda:deque(maxlen=2));d=PRELOAD_START
    allrows=[]
    while d<=TE1:
        if d>=TR0-timedelta(days=12):
            # features for this day see only records ingested before this day
            feats=process_features(d,cache,mh) if d>=TR0 else []
            if d>=TR0:
                ymd=d.strftime('%Y/%m/%d'); res={r['レースコード']:r for r in rows(f'data/results/realtime/{ymd}.csv')}; cards={r['レースコード']:r for r in rows(f'data/programs/race_cards/{ymd}.csv')}
                period='train' if d<=TR1 else 'validation' if d<=VA1 else 'latest_month'
                for r,x,s4,s5,dc in feats:
                    s3=score3v4(x); venue=str(r.get('レース場コード','')).zfill(2)
                    for m in MODELS:
                        fr=features(x,s3,s4,dc,m)
                        if not passes(fr,RULES[m]):continue
                        b=BOAT[m]; name=clean_name(r.get(f'艇{b}_選手名'))
                        p1=hist_feature(ph,venue,name,1);p2=hist_feature(ph,venue,name,2)
                        allrows.append({'period':period,'date':str(d),'race_code':r['レースコード'],'model':m,'target':target34(res.get(r['レースコード'],{}),m),'prior1':prior_score(p1,m),'prior2':prior_score(p2,m),'has2':int(len(ph.get((venue,name),[]))>=2)})
            # ingest after scoring => no same/future race leakage. Same-day prior races intentionally not used because this is a daily pre-race candidate model.
            for code,b,name,z in preview_records(d):
                cardrows=rows(f'data/programs/race_cards/{d.strftime("%Y/%m/%d")}.csv'); venue=str(next((c.get('レース場コード','') for c in cardrows if c['レースコード']==code),'')).zfill(2);ph[(venue,name)].append(z)
            ingest_prior_day_preview(cache,d)
        ingest_motor(mh,seen,d);d+=timedelta(days=1)
    # Train-only thresholds: top 40% of prior score for each model/variant.
    cuts={}
    for m in MODELS:
        for v in ['prior1','prior2']:
            a=sorted(z[v] for z in allrows if z['period']=='train' and z['model']==m and (v=='prior1' or z['has2']))
            cuts[(m,v)]=a[int(.60*(len(a)-1))] if a else .5
    L=['# v43 前走・前々走 枠補正展示の事前候補検証','', '過去走の当時枠で展示/オリジナル展示を補正。前走のみ vs 前走+前々走(前走60%,前々走40%)。当日展示・実進入・艇N_コース不使用。同日走は日次事前候補では使わない。','', '|期間|モデル|基準候補R/率|前走上位R/率|前走+前々走上位R/率|2走化差|','|---|---|---:|---:|---:|---:|']
    for p in ['train','validation','latest_month']:
      for m in MODELS:
        a=[z for z in allrows if z['period']==p and z['model']==m]; b=[z for z in a if z['prior1']>=cuts[(m,'prior1')]]; c=[z for z in a if z['has2'] and z['prior2']>=cuts[(m,'prior2')]]
        rate=lambda q:100*sum(z['target'] for z in q)/len(q) if q else 0
        L.append(f'|{p}|{m}|{len(a)}R/{rate(a):.1f}%|{len(b)}R/{rate(b):.1f}%|{len(c)}R/{rate(c):.1f}%|{rate(c)-rate(b):+.1f}pt|')
    L+=['','判定: validationを最優先。latest_monthは反復検証済みなので参考。前々走追加が学習だけ改善する場合は採用しない。']
    with open('analysis_v43_prior2_lane_corrected.csv','w',newline='',encoding='utf-8-sig') as fo:
        w=csv.DictWriter(fo,fieldnames=allrows[0].keys());w.writeheader();w.writerows(allrows)
    open('summary_v43_prior2_lane_corrected.md','w',encoding='utf-8').write('\n'.join(L)+'\n')
if __name__=='__main__':main()
