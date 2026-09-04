"""Evaluate v106 4C exact-7 prospective shadow records.

Pre-race ticket freezes and post-race labels live in separate CSVs and are joined
only here. Formal production criteria are frozen in the v106 model before the
prospective period begins.
"""
from __future__ import annotations

import csv
from pathlib import Path
from statistics import mean

PRE=Path('prospective/v106_4corner_pre.csv')
RES=Path('prospective/v106_4corner_results.csv')
OUT=Path('summary_v106_4corner_prospective.md')
START='2026-09-05'
N=7
A=55.0
S=67.0


def read(p):
    with p.open(encoding='utf-8-sig',newline='') as f: return list(csv.DictReader(f))

def ff(x,d=None):
    try:
        if x is None or str(x).strip()=='': return d
        return float(x)
    except Exception: return d

def ii(x,d=0):
    try: return int(float(x))
    except Exception: return d

def pct(n,d): return 100.0*n/d if d else 0.0

def parse_tickets(s): return {x.strip() for x in (s or '').split(';') if x.strip()}

def pass_entry(v): return str(v or '').strip().upper() in ('PASS','KEEP','OK','1','TRUE')


def metric(q,mode):
    tf={'CURRENT':'current7','ROLE':'role7','V106':'v106_7'}[mode]
    cf={'CURRENT':'res_current7_comp_rate_pct','ROLE':'res_role7_comp_rate_pct','V106':'res_v106_7_comp_rate_pct'}[mode]
    head=hit=ret=0; comps=[]
    for r in q:
        w=ii(r.get('res_winner')); s=ii(r.get('res_second')); t=ii(r.get('res_third'))
        if w==4: head+=1
        combo=f'4-{s}-{t}'
        if w==4 and combo in parse_tickets(r.get(tf,'')):
            hit+=1; ret+=ii(r.get('res_payout100'))
        c=ff(r.get(cf))
        if c is not None and c>0: comps.append(c)
    inv=len(q)*N*100
    return {
      'r':len(q),'head':head,'hit':hit,
      'hitp':pct(hit,len(q)),'covp':pct(hit,head),'roi':pct(ret,inv),
      'comp':mean(comps) if comps else 0.0,'comp_n':len(comps),'comp_cov':pct(len(comps),len(q)),
    }


def cohort(joined,scorefield,cut):
    return [r for r in joined if ff(r.get(scorefield),-999)>=cut]


def line(label,q):
    c=metric(q,'CURRENT'); r=metric(q,'ROLE'); v=metric(q,'V106')
    return {
      'label':label,'q':q,'current':c,'role':r,'v106':v,
      'hit_diff':v['hitp']-c['hitp'],'cov_diff':v['covp']-c['covp'],
      'comp_red':c['comp']-v['comp'] if c['comp_n'] and v['comp_n'] else 0.0,
      'roi_diff':v['roi']-c['roi'],
      'role_hit_diff':v['hitp']-r['hitp'],
      'role_comp_red':r['comp']-v['comp'] if r['comp_n'] and v['comp_n'] else 0.0,
    }


def main():
    pre=[r for r in read(PRE) if r.get('date','')>=START and pass_entry(r.get('entry_status'))]
    res={(r.get('date',''),r.get('race_code','')):r for r in read(RES)}
    joined=[]
    for p in pre:
        rr=res.get((p.get('date',''),p.get('race_code','')))
        if not rr: continue
        if min(len(parse_tickets(p.get(k,''))) for k in ('current7','role7','v106_7'))<N: continue
        z=dict(p); z.update({f'res_{k}':v for k,v in rr.items()}); joined.append(z)

    rows=[
      line('BASE A',cohort(joined,'base_score',A)),
      line('BASE S',cohort(joined,'base_score',S)),
      line('CORR20 A',cohort(joined,'corr20_score',A)),
      line('CORR20 S',cohort(joined,'corr20_score',S)),
    ]

    L=['# v106 4カド7点 prospective shadow evaluation','',
       f'- prospective start: **{START}**',
       f'- pre-result frozen eligible rows: **{len(pre)}**',
       f'- settled rows joined after freeze: **{len(joined)}**',
       '- CURRENT7 / ROLE7 / V106_7 are all fixed before result.',
       '- target-race final odds are settlement labels only and enter only composite-rate columns.','',
       '## CURRENT7 vs ROLE7 vs V106_7','',
       '|cohort|R / 4頭1着|CURRENT hit|ROLE hit|V106 hit|V106-CUR|CURRENT coverage|V106 coverage|差|CURRENT合成率|ROLE合成率|V106合成率|V106低下|odds coverage|CURRENT ROI|V106 ROI|差|',
       '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for x in rows:
        c=x['current'];r=x['role'];v=x['v106']
        compc=f"{c['comp']:.1f}%" if c['comp_n'] else '-'
        compr=f"{r['comp']:.1f}%" if r['comp_n'] else '-'
        compv=f"{v['comp']:.1f}%" if v['comp_n'] else '-'
        L.append(f"|{x['label']}|{c['r']} / {c['head']}|{c['hitp']:.1f}%|{r['hitp']:.1f}%|{v['hitp']:.1f}%|{x['hit_diff']:+.1f}pt|{c['covp']:.1f}%|{v['covp']:.1f}%|{x['cov_diff']:+.1f}pt|{compc}|{compr}|{compv}|{x['comp_red']:+.1f}pt|{v['comp_cov']:.1f}%|{c['roi']:.1f}%|{v['roi']:.1f}%|{x['roi_diff']:+.1f}pt|")

    ba=next(x for x in rows if x['label']=='BASE A')
    bs=next(x for x in rows if x['label']=='BASE S')
    enough=(ba['current']['r']>=100 and ba['current']['head']>=30 and bs['current']['r']>=50 and bs['current']['head']>=15)
    hit_ok=all(x['hit_diff']>=-1e-9 for x in (ba,bs))
    cov_ok=all(x['cov_diff']>=-1e-9 for x in (ba,bs))
    comp_ok=all(x['current']['comp_n']>0 and x['v106']['comp_n']>0 and x['comp_red']>=0.5-1e-9 for x in (ba,bs))
    odds_ok=all(x['v106']['comp_cov']>=80.0-1e-9 for x in (ba,bs))
    roi_ok=all(x['roi_diff']>=-5.0-1e-9 for x in (ba,bs))
    passed=enough and hit_ok and cov_ok and comp_ok and odds_ok and roi_ok

    L += ['','## 事前固定した正式採用条件',
          f"- BASE A 100R/4頭30R + BASE S 50R/4頭15R: **{'OK' if enough else '未達'}** (A {ba['current']['r']}R/{ba['current']['head']} head, S {bs['current']['r']}R/{bs['current']['head']} head)",
          f"- A/Sとも総合的中率がCURRENT7以上: **{'OK' if hit_ok else '未達'}**",
          f"- A/Sとも頭内coverageがCURRENT7以上: **{'OK' if cov_ok else '未達'}**",
          f"- A/Sとも平均確定合成オッズ率を0.5pt以上低下: **{'OK' if comp_ok else '未達'}**",
          f"- final-odds coverage A/Sとも80%以上: **{'OK' if odds_ok else '未達'}**",
          f"- A/SともROI差 -5pt以上: **{'OK' if roi_ok else '未達'}**",'',
          f"### 判定: **{'PRODUCTION ADOPT CANDIDATE' if passed else 'SHADOW継続'}**",'',
          'CORR20 A/Sはv105 lineage確認用。正式production判定は実運用と直接比較できるBASE A/Sを主条件とする。']
    OUT.write_text('\n'.join(L)+'\n',encoding='utf-8')
    print('\n'.join(L),flush=True)

if __name__=='__main__': main()
