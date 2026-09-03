from __future__ import annotations
import csv
from collections import defaultdict
from datetime import date,timedelta
from backtest import rows

START=date(2025,11,1); END=date(2026,8,31)
ANALYSIS='analysis_v74_ten_month_strict_flow.csv'


def ii(x,d=0):
    try:return int(float(x))
    except:return d

def normkim(x):return (x or '').replace(' ','').replace('　','')

def pct(n,d):return 100*n/d if d else 0.0


def load_candidates():
    aset=defaultdict(set); sset=defaultdict(set); model_a=defaultdict(set)
    with open(ANALYSIS,encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            ds=r.get('date',''); code=r.get('race_code',''); h=ii(r.get('head')); m=r.get('model','')
            if not ds or not code or h not in (3,4,5):continue
            k=(ds,code)
            if ii(r.get('approved_A')):
                aset[h].add(k); model_a[m].add(k)
            if ii(r.get('approved_S')):sset[h].add(k)
    return aset,sset,model_a


def main():
    aset,sset,model_a=load_candidates()
    allr=[];d=START
    while d<=END:
        ds=str(d);ymd=d.strftime('%Y/%m/%d')
        for r in rows(f'data/results/realtime/{ymd}.csv'):
            code=r.get('レースコード','');win=ii(r.get('1着_艇番'));kim=normkim(r.get('決まり手'))
            if code and 1<=win<=6:allr.append((ds,code,win,kim))
        d+=timedelta(days=1)
    total=len(allr)

    L=['# v76 10か月 候補 vs 非候補の実頭率', '',
       f'期間: {START}〜{END} / 有効結果 **{total:,}R**',
       'A以上=最終候補。3頭は3まくり/3まくり差しのどちらかがA以上なら候補。4頭=4カドA以上、5頭=5頭展開A以上。非候補はその艇についてA以上に選ばれなかった全レース。', '',
       '## 頭別',
       '|頭|区分|R|1着|1着率|素の全レース率|倍率|',
       '|---:|---|---:|---:|---:|---:|---:|']

    raw={h:sum(win==h for _,_,win,_ in allr) for h in (3,4,5)}
    detail={}
    for h in (3,4,5):
        for label,keys in [('A以上候補',aset[h]),('S候補',sset[h]),('A以上非候補',None)]:
            if keys is None:
                q=[z for z in allr if (z[0],z[1]) not in aset[h]]
            else:q=[z for z in allr if (z[0],z[1]) in keys]
            n=len(q);w=sum(z[2]==h for z in q);rate=pct(w,n);base=pct(raw[h],total);lift=rate/base if base else 0
            L.append(f'|{h}|{label}|{n:,}|{w:,}|{rate:.2f}%|{base:.2f}%|{lift:.2f}x|')
            detail[(h,label)]=(n,w,rate)

    L+=['','## 決まり手込みの選別力','|事象|A以上候補での発生率|非候補での発生率|倍率|','|---|---:|---:|---:|']
    # head3: either 3-model A candidate, event 3 wins by makuri/MS
    for h,event_name,eventfn in [
        (3,'3号艇 まくり+まくり差し',lambda w,k:w==3 and k in ('まくり','まくり差し')),
        (4,'4号艇 まくり+まくり差し',lambda w,k:w==4 and k in ('まくり','まくり差し')),
        (5,'5号艇 1着',lambda w,k:w==5),
    ]:
        qa=[z for z in allr if (z[0],z[1]) in aset[h]];qn=[z for z in allr if (z[0],z[1]) not in aset[h]]
        ra=pct(sum(eventfn(z[2],z[3]) for z in qa),len(qa));rn=pct(sum(eventfn(z[2],z[3]) for z in qn),len(qn));lift=ra/rn if rn else 0
        L.append(f'|{event_name}|{ra:.2f}%|{rn:.2f}%|{lift:.2f}x|')

    L+=['','## 3号艇ルート別 A以上候補 vs 非候補','|モデル|候補R|対象決まり手成立|成立率|非候補成立率|倍率|','|---|---:|---:|---:|---:|---:|']
    specs=[('3まくり',lambda w,k:w==3 and k=='まくり'),('3まくり差し',lambda w,k:w==3 and k=='まくり差し'),('4カドまくり',lambda w,k:w==4 and k=='まくり')]
    for m,fn in specs:
        keys=model_a[m];qa=[z for z in allr if (z[0],z[1]) in keys];qn=[z for z in allr if (z[0],z[1]) not in keys]
        ha=sum(fn(z[2],z[3]) for z in qa);hn=sum(fn(z[2],z[3]) for z in qn);ra=pct(ha,len(qa));rn=pct(hn,len(qn));lift=ra/rn if rn else 0
        L.append(f'|{m}|{len(qa):,}|{ha:,}|{ra:.2f}%|{rn:.2f}%|{lift:.2f}x|')

    L+=['','## 補足','- 比較はモデルを使わない全レースの実結果を母集団にし、v74で結果を見る前に固定されたA/S候補フラグだけで分割。','- 同一レースで3まくり/3まくり差しが重複した場合、v74は頭3で事前score上位の1ルートに統合済み。','- 非候補率が素の率より低く、候補率が高いほど選別能力がある。']
    open('summary_v76_candidate_vs_noncandidate.md','w',encoding='utf-8').write('\n'.join(L)+'\n')

if __name__=='__main__':main()
