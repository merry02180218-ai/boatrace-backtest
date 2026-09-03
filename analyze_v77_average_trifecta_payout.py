from __future__ import annotations
import csv, statistics
from collections import defaultdict

SRC='analysis_v74_ten_month_strict_flow.csv'
OUT='summary_v77_average_trifecta_payout.md'

MODELS=['3まくり','3まくり差し','4カドまくり','5頭展開']

def f(x,default=0.0):
    try:return float(x)
    except:return default

def i(x,default=0):
    try:return int(float(x))
    except:return default

def pct(a,b): return 100*a/b if b else 0.0

def summarize(rs,grade):
    key='approved_S' if grade=='S' else 'approved_A'
    q=[r for r in rs if i(r.get(key)) and i(r.get('valid_result'))]
    head=[r for r in q if i(r.get('head_hit')) and i(r.get('valid_payout')) and i(r.get('payout100'))>0]
    pays=[i(r.get('payout100')) for r in head]
    n=len(q); h=len(head)
    avg=sum(pays)/len(pays) if pays else 0
    med=statistics.median(pays) if pays else 0
    p25=statistics.quantiles(pays,n=4,method='inclusive')[0] if len(pays)>=2 else (pays[0] if pays else 0)
    p75=statistics.quantiles(pays,n=4,method='inclusive')[2] if len(pays)>=2 else (pays[0] if pays else 0)
    mn=min(pays) if pays else 0; mx=max(pays) if pays else 0
    # if all 20 fixed-head trifectas were bought at 100 yen each, exactly one wins whenever head wins and payout is valid
    invest20=2000*n
    ret20=sum(pays)
    roi20=pct(ret20,invest20)
    # payout-only expected return per candidate = head rate * conditional avg payout; this should match ret/n absent missing payouts
    exp_per_r=ret20/n if n else 0
    return dict(n=n,h=h,head_rate=pct(h,n),avg=avg,med=med,p25=p25,p75=p75,mn=mn,mx=mx,roi20=roi20,exp=exp_per_r)

def main():
    with open(SRC,encoding='utf-8-sig') as fp: rows=list(csv.DictReader(fp))
    by=defaultdict(list)
    for r in rows:
        m=r.get('model')
        if m in MODELS: by[m].append(r)
    L=['# v77 10か月 モデル別・頭的中時の3連単配当','',
       '期間: 2025-11-01〜2026-08-31。v74で結果を見る前に固定した候補だけを使用。',
       '「平均配当」は、そのモデルがA/S候補になり、実際にその頭が1着になったレースの3連単払戻（100円あたり）の平均。',
       '20点ROIは頭固定20通りを各100円買った診断値。実運用の手動絞りとは別。','']
    for grade in ['A','S']:
        L += [f'## {grade}以上','|モデル|候補R|頭的中|頭率|平均3連単|中央値|25%点|75%点|最高配当|20点ROI|1R平均払戻|',
              '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
        for m in MODELS:
            z=summarize(by[m],grade)
            L.append(f"|{m}|{z['n']}|{z['h']}|{z['head_rate']:.1f}%|{z['avg']:,.0f}円|{z['med']:,.0f}円|{z['p25']:,.0f}円|{z['p75']:,.0f}円|{z['mx']:,}円|{z['roi20']:.1f}%|{z['exp']:,.0f}円|")
        L.append('')
    # head group aggregates: 3 routes merged? v74 has already one route per race/head, but split rows by model. aggregate selected head3 rows across both models.
    L += ['## 頭別集約（A以上）','|頭|候補R|頭的中|頭率|平均3連単|中央値|20点ROI|1R平均払戻|','|---:|---:|---:|---:|---:|---:|---:|---:|']
    groups={'3号艇':by['3まくり']+by['3まくり差し'],'4号艇':by['4カドまくり'],'5号艇':by['5頭展開']}
    for name,rs in groups.items():
        z=summarize(rs,'A')
        L.append(f"|{name}|{z['n']}|{z['h']}|{z['head_rate']:.1f}%|{z['avg']:,.0f}円|{z['med']:,.0f}円|{z['roi20']:.1f}%|{z['exp']:,.0f}円|")
    L += ['','## 読み方','- 平均は高配当に引っ張られるので、主軸判断では中央値も同時に見る。','- 「1R平均払戻」は候補1Rあたりの実払戻総額÷候補数。20点総流しなら投資2,000円/Rなので、2,000円を超えればROI100%超。','- 主軸は頭率だけでなく、頭率×頭的中時配当の組み合わせで判断する。']
    open(OUT,'w',encoding='utf-8').write('\n'.join(L)+'\n')

if __name__=='__main__':main()
