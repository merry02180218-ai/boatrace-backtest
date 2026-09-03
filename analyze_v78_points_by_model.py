import csv, math
from collections import defaultdict

SRC='analysis_v74_ten_month_strict_flow.csv'
OUT='summary_v78_points_by_model.md'
MODELS=['3まくり','3まくり差し','4カドまくり','5頭展開']

def ii(x,default=0):
    try:return int(float(x))
    except:return default

def ff(x,default=0.0):
    try:return float(x)
    except:return default

with open(SRC,encoding='utf-8-sig') as f:
    rows=list(csv.DictReader(f))

L=['# v78 10か月 モデル別・上位N点ROI','',
   '期間: 2025-11-01〜2026-08-31。v74で結果を見る前に固定した20通り表示順位をそのまま使用。',
   '各候補で表示順位1位からN位までを各100円購入したと仮定。結果を見て買い目を変えていない。',
   'ROI=実際にそのN点内へ入った3連単払戻合計 ÷ (候補R×N×100円)。','']

for grade in ['A','S']:
    L += [f'## {grade}以上','', '|モデル|候補R|頭率|理論BE点数*|実測ベストN|ベストROI|ROI100%以上のN|',
          '|---|---:|---:|---:|---:|---:|---|']
    detailed={}
    for m in MODELS:
        q=[]
        for r in rows:
            if r.get('model')!=m:continue
            approved=ii(r.get('approved_S')) if grade=='S' else ii(r.get('approved_A'))
            if not approved or not ii(r.get('valid_payout')):continue
            q.append(r)
        n=len(q); hh=sum(ii(r.get('head_hit')) for r in q)
        # average realized payout per candidate if all 20 covered
        total_head_return=sum(ii(r.get('payout100')) for r in q if ii(r.get('head_hit')))
        avg_return=total_head_return/n if n else 0
        theoretical=avg_return/100 if n else 0
        vals=[]
        for N in range(1,21):
            hits=[r for r in q if 1<=ii(r.get('actual_rank20'))<=N]
            ret=sum(ii(r.get('payout100')) for r in hits)
            inv=n*N*100
            roi=100*ret/inv if inv else 0
            vals.append((N,len(hits),100*len(hits)/n if n else 0,ret,roi))
        detailed[m]=vals
        best=max(vals,key=lambda z:z[4]) if vals else (0,0,0,0,0)
        pos=[str(N) for N,_,_,_,roi in vals if roi>=100]
        # compact contiguous ranges
        ranges=[]
        nums=[int(x) for x in pos]
        if nums:
            s=p=nums[0]
            for x in nums[1:]:
                if x==p+1:p=x
                else:ranges.append(str(s) if s==p else f'{s}-{p}');s=p=x
            ranges.append(str(s) if s==p else f'{s}-{p}')
        L.append(f'|{m}|{n}|{100*hh/n if n else 0:.1f}%|{theoretical:.1f}点|{best[0]}点|{best[4]:.1f}%|{", ".join(ranges) if ranges else "なし"}|')
    L += ['', '### 点数別ROI', '', '|N点|3まくり|3まくり差し|4カドまくり|5頭展開|', '|---:|---:|---:|---:|---:|']
    for N in range(1,21):
        xs=[]
        for m in MODELS:
            v=detailed[m][N-1] if m in detailed and len(detailed[m])>=N else (N,0,0,0,0)
            xs.append(f'{v[4]:.1f}%')
        L.append(f'|{N}|'+ '|'.join(xs)+'|')
    L += ['', '### 点数別的中率', '', '|N点|3まくり|3まくり差し|4カドまくり|5頭展開|', '|---:|---:|---:|---:|---:|']
    for N in [1,2,3,4,5,6,8,10,12,15,20]:
        xs=[]
        for m in MODELS:
            v=detailed[m][N-1] if m in detailed and len(detailed[m])>=N else (N,0,0,0,0)
            xs.append(f'{v[2]:.1f}%')
        L.append(f'|{N}|'+ '|'.join(xs)+'|')
    L += ['']

L += ['*理論BE点数 = 頭的中時の実払戻を全候補で平均した「1R平均払戻」÷100円。これは全的中組を必ず拾える理想上限で、実際の順位付けでその点数まで利益が出ることを保証しない。',
      '実運用判断では「実測ROI」と「的中率」を優先する。']
open(OUT,'w',encoding='utf-8').write('\n'.join(L))
print('\n'.join(L))
