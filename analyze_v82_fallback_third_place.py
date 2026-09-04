import csv
from collections import Counter

SRC='analysis_v74_ten_month_strict_flow.csv'

def i(v):
    try:return int(float(v or 0))
    except:return 0

def combo_parts(s):
    try:return [int(x) for x in (s or '').strip().split('-')]
    except:return []

def pct(n,d):return 100*n/d if d else 0.0

with open(SRC,encoding='utf-8-sig') as f: rows=list(csv.DictReader(f))
for r in rows:
    p=combo_parts(r.get('actual_combo'))
    r['_p']=p
    r['_winner']=p[0] if len(p)==3 else 0
    r['_second']=p[1] if len(p)==3 else 0
    r['_third']=p[2] if len(p)==3 else 0

cases=[
    ('3まくり 1-3-◯','3まくり',1,3),
    ('3まくり差し 1-3-◯','3まくり差し',1,3),
    ('4カド 1-4-◯','4カドまくり',1,4),
    ('4カド 2-4-◯','4カドまくり',2,4),
    ('5頭 1-5-◯','5頭展開',1,5),
    ('5頭 4-5-◯','5頭展開',4,5),
]

L=['# v82 裏シナリオ別・3着艇分布','',
   '期間: 2025-11-01〜2026-08-31。v74の結果前固定候補のみ。',
   '対象: 指定した裏シナリオ（例 1-3-◯）が実際に成立したレース。3着艇の条件付き分布を集計。','']

for grade in ['A','S']:
    key='approved_A' if grade=='A' else 'approved_S'
    L += [f'## {grade}以上','']
    for label,m,w,s in cases:
        q=[r for r in rows if r.get('model')==m and i(r.get(key))==1 and len(r['_p'])==3 and r['_winner']==w and r['_second']==s]
        c=Counter(r['_third'] for r in q if r['_third'])
        n=sum(c.values())
        L += [f'### {label} — {n}R','', '|順位|3着艇|回数|構成比|累積|', '|---:|---:|---:|---:|---:|']
        cum=0
        for idx,(boat,cnt) in enumerate(sorted(c.items(), key=lambda kv:(-kv[1],kv[0])),1):
            cum += cnt
            L.append(f'|{idx}|{boat}号艇|{cnt}|{pct(cnt,n):.1f}%|{pct(cum,n):.1f}%|')
        if n==0:
            L.append('|-|該当なし|0|0.0%|0.0%|')
        L.append('')

open('summary_v82_fallback_third_place.md','w',encoding='utf-8').write('\n'.join(L)+'\n')
print('\n'.join(L))
