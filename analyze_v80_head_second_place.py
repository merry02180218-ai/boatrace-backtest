import csv
from collections import defaultdict, Counter

SRC='analysis_v74_ten_month_strict_flow.csv'

def pct(n,d): return 100*n/d if d else 0.0

def parse_combo(s):
    try:return [int(x) for x in (s or '').split('-')[:3]]
    except:return []

rows=list(csv.DictReader(open(SRC,encoding='utf-8-sig')))
MODELS=['3まくり','3まくり差し','4カドまくり','5頭展開']
L=['# v80 10か月・頭外れ時に予想頭が2着へ残る率','',
   '期間: 2025-11-01〜2026-08-31。v74の結果前固定候補のみ。',
   '「頭外れ」= 実1着が予想頭以外。そこから予想頭が実2着に残った割合を集計。','']
for grade,key in [('A以上','approved_A'),('S以上','approved_S')]:
    L += [f'## {grade}','','|モデル|候補R|頭外れR|予想頭2着残り|外れ時2着残り率|1着=1号艇の外れR|そのうち1-予想頭|1頭時の残り率|',
          '|---|---:|---:|---:|---:|---:|---:|---:|']
    for m in MODELS:
        q=[r for r in rows if r['model']==m and r.get('valid_result')=='1' and r.get(key)=='1']
        miss=[]; one=[]
        for r in q:
            arr=parse_combo(r.get('actual_combo'))
            if len(arr)<2: continue
            h=int(r['head'])
            if arr[0]==h: continue
            miss.append((r,arr))
            if arr[0]==1: one.append((r,arr))
        sec=sum(arr[1]==int(r['head']) for r,arr in miss)
        one_sec=sum(arr[1]==int(r['head']) for r,arr in one)
        L.append(f'|{m}|{len(q)}|{len(miss)}|{sec}|{pct(sec,len(miss)):.1f}%|{len(one)}|{one_sec}|{pct(one_sec,len(one)):.1f}%|')

    L += ['','### 1着艇別：予想頭が2着へ残る率','','|モデル|実1着|該当R|予想頭2着|残り率|','|---|---:|---:|---:|---:|']
    for m in MODELS:
        q=[r for r in rows if r['model']==m and r.get('valid_result')=='1' and r.get(key)=='1']
        h=int(q[0]['head']) if q else 0
        buckets=defaultdict(list)
        for r in q:
            arr=parse_combo(r.get('actual_combo'))
            if len(arr)<2 or arr[0]==h: continue
            buckets[arr[0]].append(arr)
        for w in sorted(buckets):
            a=buckets[w]; sec=sum(x[1]==h for x in a)
            L.append(f'|{m}|{w}|{len(a)}|{sec}|{pct(sec,len(a)):.1f}%|')

# head-aggregated summary emphasizing examples
L += ['','## 頭別集約（A以上）','','|予想頭|頭外れR|2着残り|外れ時2着残り率|1号艇勝ちR|1-予想頭|1号艇勝ち時の残り率|','|---:|---:|---:|---:|---:|---:|---:|']
for h in (3,4,5):
    q=[r for r in rows if r.get('valid_result')=='1' and r.get('approved_A')=='1' and int(r['head'])==h]
    miss=[];one=[]
    for r in q:
        arr=parse_combo(r.get('actual_combo'))
        if len(arr)<2 or arr[0]==h: continue
        miss.append(arr)
        if arr[0]==1:one.append(arr)
    sec=sum(a[1]==h for a in miss); one_sec=sum(a[1]==h for a in one)
    L.append(f'|{h}号艇|{len(miss)}|{sec}|{pct(sec,len(miss)):.1f}%|{len(one)}|{one_sec}|{pct(one_sec,len(one)):.1f}%|')

open('summary_v80_head_second_place.md','w',encoding='utf-8').write('\n'.join(L)+'\n')
print('\n'.join(L))
