from __future__ import annotations
import csv
from collections import Counter

SRC='analysis_v74_ten_month_strict_flow.csv'
OUT='summary_v79_miss_winner_distribution.md'
MODELS=['3まくり','3まくり差し','4カドまくり','5頭展開']

with open(SRC,encoding='utf-8-sig') as f:
    rows=list(csv.DictReader(f))

def ii(x):
    try:return int(float(x))
    except:return 0

def flag(r,k): return ii(r.get(k))==1

def pct(n,d): return 100*n/d if d else 0.0

L=['# v79 10か月・頭予測が外れた時の実1着艇分布','',
   '期間: 2025-11-01〜2026-08-31。v74で結果を見る前に固定された候補だけを使用。',
   '「外れ」は候補頭と実際の1着艇が異なるレース。割合は外れレースを100%とした条件付き確率。','']

for grade,key in [('A以上','approved_A'),('S以上','approved_S')]:
    L += [f'## {grade}','','|モデル|候補R|頭的中|外れR|外れ時1号艇|2号艇|3号艇|4号艇|5号艇|6号艇|',
          '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for m in MODELS:
        q=[r for r in rows if r.get('model')==m and flag(r,key) and flag(r,'valid_result')]
        hit=sum(flag(r,'head_hit') for r in q)
        miss=[r for r in q if not flag(r,'head_hit')]
        c=Counter(ii(r.get('winner')) for r in miss)
        vals=[f'{c[b]} ({pct(c[b],len(miss)):.1f}%)' for b in range(1,7)]
        L.append(f'|{m}|{len(q)}|{hit} ({pct(hit,len(q)):.1f}%)|{len(miss)}|'+'|'.join(vals)+'|')
    L+=['']

# Head-aggregated 3 / 4 / 5 views. For head3, v74 has only the selected winning-score route per race/head.
for grade,key in [('A以上','approved_A'),('S以上','approved_S')]:
    L += [f'## {grade}・頭別集約','','|予測頭|候補R|頭的中率|外れR|外れ時の実1着1位|2位|3位|',
          '|---:|---:|---:|---:|---|---|---|']
    for h in (3,4,5):
        q=[r for r in rows if ii(r.get('head'))==h and flag(r,key) and flag(r,'valid_result')]
        # Safety: unique race/head in v74 already, but dedupe again.
        d={r['race_code']:r for r in q}; q=list(d.values())
        hit=sum(flag(r,'head_hit') for r in q); miss=[r for r in q if not flag(r,'head_hit')]
        c=Counter(ii(r.get('winner')) for r in miss)
        order=sorted(((n,b) for b,n in c.items() if 1<=b<=6),reverse=True)
        top=[]
        for n,b in order[:3]: top.append(f'{b}号艇 {n}R ({pct(n,len(miss)):.1f}%)')
        while len(top)<3:top.append('-')
        L.append(f'|{h}号艇|{len(q)}|{pct(hit,len(q)):.1f}%|{len(miss)}|{top[0]}|{top[1]}|{top[2]}|')
    L+=['']

# For each model, compare miss winner distribution with unconditional raw winner rates from v75.
raw={1:55.09,2:13.45,3:12.64,4:9.90,5:5.90,6:3.02}
L += ['## A以上・外れ時の1着率 / 全レース素の1着率','','|モデル|艇|外れ時1着率|全レース素率|差|','|---|---:|---:|---:|---:|']
for m in MODELS:
    q=[r for r in rows if r.get('model')==m and flag(r,'approved_A') and flag(r,'valid_result') and not flag(r,'head_hit')]
    c=Counter(ii(r.get('winner')) for r in q)
    ranked=sorted(range(1,7), key=lambda b:c[b], reverse=True)
    for b in ranked[:3]:
        p=pct(c[b],len(q)); L.append(f'|{m}|{b}号艇|{p:.1f}%|{raw[b]:.2f}%|{p-raw[b]:+.1f}pt|')

open(OUT,'w',encoding='utf-8').write('\n'.join(L)+'\n')
print('wrote',OUT,'rows',len(rows))
