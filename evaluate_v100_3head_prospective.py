"""Evaluate v100 prospective shadow records without contaminating pre-result freezes.

Pre-race and result logs are separate files and joined only here by (date,race_code).
Formal production adoption criteria were frozen before the prospective period.
"""
from __future__ import annotations
import csv
from pathlib import Path

PRE=Path('prospective/v100_3head_pre.csv')
RES=Path('prospective/v100_3head_results.csv')
OUT=Path('summary_v100_3head_prospective.md')
START='2026-09-05'


def read(p):
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def ii(x,d=0):
    try:return int(float(x))
    except Exception:return d
def parse_tickets(s):return {x.strip() for x in (s or '').split(';') if x.strip()}
def pct(n,d):return 100*n/d if d else 0.

def main():
    pre=[r for r in read(PRE) if r.get('date','')>=START]
    res={(r.get('date',''),r.get('race_code','')):r for r in read(RES)}
    joined=[]
    for p in pre:
        rr=res.get((p.get('date',''),p.get('race_code','')))
        if not rr:continue
        z=dict(p);z.update({f'res_{k}':v for k,v in rr.items()});joined.append(z)
    def stat(k,mode):
        ticket_field=('current' if mode=='CURRENT' else 'v100_')+str(k)
        if mode=='CURRENT':ticket_field=f'current{k}'
        q=[r for r in joined if r.get('grade') in ('A','S')]
        heads=[r for r in q if ii(r.get('res_winner'))==3]
        hits=ret=0
        for r in q:
            ts=parse_tickets(r.get(ticket_field,''))
            combo=f"3-{ii(r.get('res_second'))}-{ii(r.get('res_third'))}"
            if ii(r.get('res_winner'))==3 and combo in ts:
                hits+=1;ret+=ii(r.get('res_payout100'))
        inv=100*k*len(q)
        return len(q),len(heads),hits,pct(hits,len(heads)),pct(ret,inv)
    L=['# v100 3頭 prospective shadow evaluation','',f'- prospective start: **{START}**',f'- pre-result frozen rows: **{len(pre)}**',f'- settled rows joined after freeze: **{len(joined)}**','',
       '|点数|CURRENT coverage|V100 coverage|差|CURRENT ROI|V100 ROI|差|','|---:|---:|---:|---:|---:|---:|---:|']
    results={}
    for k in (4,6):
        c=stat(k,'CURRENT');v=stat(k,'V100');results[k]=(c,v)
        L.append(f'|{k}|{c[2]}/{c[1]} ({c[3]:.1f}%)|{v[2]}/{v[1]} ({v[3]:.1f}%)|{v[3]-c[3]:+.1f}pt|{c[4]:.1f}%|{v[4]:.1f}%|{v[4]-c[4]:+.1f}pt|')
    a_n=results[4][0][0] if results else 0;heads=results[4][0][1] if results else 0
    enough=a_n>=100 and heads>=30
    cov_ok=all(v[3]>=c[3] for c,v in results.values()) if results else False
    improve=any(v[3]-c[3]>=3.0 for c,v in results.values()) if results else False
    roi_ok=all(v[4]-c[4]>=-5.0 for c,v in results.values()) if results else False
    passed=enough and cov_ok and improve and roi_ok
    L+=['','## 事前固定した正式採用条件',
        f'- A以上100Rかつ3頭的中30R以上: **{"OK" if enough else "未達"}** ({a_n}R / {heads} head hits)',
        f'- 4点・6点coverageとも非悪化: **{"OK" if cov_ok else "未達"}**',
        f'- どちらかcoverage +3.0pt以上: **{"OK" if improve else "未達"}**',
        f'- ROI差が4点・6点とも-5pt以内: **{"OK" if roi_ok else "未達"}**','',
        f'### 判定: **{"PRODUCTION ADOPT CANDIDATE" if passed else "SHADOW継続"}**']
    OUT.write_text('\n'.join(L)+'\n',encoding='utf-8')
    print('\n'.join(L))
if __name__=='__main__':main()
