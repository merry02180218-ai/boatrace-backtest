import csv, statistics

SRC='analysis_v74_ten_month_strict_flow.csv'

def i(v):
    try:return int(float(v or 0))
    except:return 0

def combo_parts(s):
    try:return [int(x) for x in (s or '').strip().split('-')]
    except:return []

def pct(n,d):return 100*n/d if d else 0.0

def stats(rs):
    vals=[i(r.get('payout100')) for r in rs if i(r.get('payout100'))>0]
    if not vals:return (0,0,0,0,0)
    return len(vals),sum(vals)/len(vals),statistics.median(vals),min(vals),max(vals)

with open(SRC,encoding='utf-8-sig') as f: rows=list(csv.DictReader(f))

for r in rows:
    r['_head']=i(r.get('head')); r['_winner']=i(r.get('winner')); r['_parts']=combo_parts(r.get('actual_combo'))
    r['_second']=r['_parts'][1] if len(r['_parts'])==3 else 0
    r['_validp']=bool(len(r['_parts'])==3 and i(r.get('payout100'))>0)

models=['3まくり','3まくり差し','4カドまくり','5頭展開']
L=['# v81 頭外れ・予想頭2着残り時の3連単配当','',
   '期間: 2025-11-01〜2026-08-31。v74の結果前固定候補のみ。',
   '対象: A/S候補で予想頭が1着を外したが、実際の2着にその予想頭が残ったレース。払戻は100円あたり。','']

for grade in ['A','S']:
    key='approved_A' if grade=='A' else 'approved_S'
    L += [f'## {grade}以上','',
          '|モデル|該当R|平均3連単|中央値|最小|最大|',
          '|---|---:|---:|---:|---:|---:|']
    for m in models:
        q=[r for r in rows if r.get('model')==m and i(r.get(key))==1 and r['_validp'] and r['_winner']!=r['_head'] and r['_second']==r['_head']]
        n,av,med,mn,mx=stats(q)
        L.append(f'|{m}|{n}|{av:,.0f}円|{med:,.0f}円|{mn:,}円|{mx:,}円|')
    L += ['', '### 主要な裏シナリオ','',
          '|シナリオ|該当R|平均3連単|中央値|最小|最大|',
          '|---|---:|---:|---:|---:|---:|']
    cases=[
        ('3まくり 1-3-◯','3まくり',1,3),
        ('3まくり差し 1-3-◯','3まくり差し',1,3),
        ('4カド 1-4-◯','4カドまくり',1,4),
        ('4カド 2-4-◯','4カドまくり',2,4),
        ('5頭 1-5-◯','5頭展開',1,5),
        ('5頭 4-5-◯','5頭展開',4,5),
    ]
    for label,m,w,s in cases:
        q=[r for r in rows if r.get('model')==m and i(r.get(key))==1 and r['_validp'] and r['_winner']==w and r['_second']==s]
        n,av,med,mn,mx=stats(q)
        L.append(f'|{label}|{n}|{av:,.0f}円|{med:,.0f}円|{mn:,}円|{mx:,}円|')
    L.append('')

open('summary_v81_second_place_payouts.md','w',encoding='utf-8').write('\n'.join(L)+'\n')
print('\n'.join(L))
