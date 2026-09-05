"""v137: optimize the existing Legacy PRE daily top-N without changing features.

Design
- Source is v136 audit CSV, which contains monthly walk-forward legacy_pre_p, p109,
  entry_course, v110 rank_l50 and settlement fields.
- PRE remains the existing boat1-only 9-feature model + venue.
- Stage2 remains fixed: v109 S >= .72 and course1.
- Tickets remain v110 lambda=.50 top7.
- Sweep daily top1..top15 on Mar-May validation only.
- Choose N by a conservative score prioritizing ROI, then hit/head stability, with
  a minimum BUY sample. Freeze that N and report Jun-Aug holdout and monthly stability.
- Results/payouts are evaluation only; no target-race result/odds enters PRE/LIVE selection.
"""
from __future__ import annotations
import csv
from collections import defaultdict

SRC='analysis_v136_1head_preselection_inner_threats.csv'
OUT='analysis_v137_1head_legacy_pre_topn_opt.csv'
SUMMARY='summary_v137_1head_legacy_pre_topn_opt.md'
VAL={'2026-03','2026-04','2026-05'}
HOLD={'2026-06','2026-07','2026-08'}
S_CUT=.72
TOPS=list(range(1,16))

def ff(x,d=0.0):
    try:return float(x)
    except Exception:return d

def ii(x,d=0):
    try:return int(float(x))
    except Exception:return d

def pct(a,b):return 100*a/b if b else 0.0

def read_csv(path):
    with open(path,encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def select(rs,n):
    by=defaultdict(list)
    for r in rs:by[r['date']].append(r)
    pre=[];buy=[]
    for d in sorted(by):
        w=sorted(by[d],key=lambda r:(-ff(r.get('legacy_pre_p')),(r.get('race_code') or '')))[:n]
        pre+=w
        buy += [r for r in w if ff(r.get('p109'))>=S_CUT and ii(r.get('entry_course'))==1]
    return pre,buy

def metric(rs):
    q=list(rs);n=len(q)
    heads=sum(ii(r.get('head_hit'))==1 for r in q)
    hits=sum(0<ii(r.get('rank_l50'))<=7 for r in q)
    headrows=[r for r in q if ii(r.get('head_hit'))==1]
    cov=sum(0<ii(r.get('rank_l50'))<=7 for r in headrows)
    ret=sum(ii(r.get('payout100')) for r in q if 0<ii(r.get('rank_l50'))<=7)
    return {'n':n,'head':pct(heads,n),'hit':pct(hits,n),'cov':pct(cov,len(headrows)),'roi':pct(ret,n*700)}

def by_month(rs):
    out={}
    for mo in sorted({r['month'] for r in rs}):out[mo]=[r for r in rs if r['month']==mo]
    return out

def main():
    src=read_csv(SRC)
    val=[r for r in src if r.get('month') in VAL]
    hold=[r for r in src if r.get('month') in HOLD]
    vdays=len({r['date'] for r in val});hdays=len({r['date'] for r in hold})

    sweep=[]
    for n in TOPS:
        p,b=select(val,n);m=metric(b)
        # No 5/day target. Sample guard only; selection objective is outcome quality.
        eligible=m['n']>=180
        sweep.append((n,eligible,len(p)/vdays if vdays else 0,m['n']/vdays if vdays else 0,m))
    good=[x for x in sweep if x[1]] or sweep
    # Validation choice: ROI first, then hit, then head; fewer PRE races wins exact ties.
    chosen=max(good,key=lambda x:(x[4]['roi'],x[4]['hit'],x[4]['head'],-x[0]))[0]

    hs=[]
    for n in TOPS:
        p,b=select(hold,n);m=metric(b)
        hs.append((n,len(p)/hdays if hdays else 0,m['n']/hdays if hdays else 0,m))

    cp,cb=select(hold,chosen);cm=metric(cb)
    bp,bb=select(hold,5);bm=metric(bb)

    L=['# v137 1号艇 Legacy PRE top-N再最適化','',
       '- PRE特徴は変更せず **Legacy（1号艇9特徴 + 場）** を維持。',
       '- Stage2固定: **v109 S(p>=72%) + 1コース維持**。ticketsは **v110 λ=.50 top7**。',
       '- 日次top1〜top15を比較。**1日5R目標は評価基準から完全に除外**。',
       '- NはMar-Mayだけで選び、Jun-Augへ固定。結果・払戻・オッズは選定入力に使わない。','',
       '## Mar-May validation top-N sweep','|PRE topN|PRE/day|BUY/day|BUY R|①頭率|7点的中率|coverage|7点ROI|eligible|','|---:|---:|---:|---:|---:|---:|---:|---:|---|']
    for n,ok,pd,bd,m in sweep:
        L.append(f'|{n}|{pd:.2f}|{bd:.2f}|{m["n"]}|{m["head"]:.1f}%|{m["hit"]:.1f}%|{m["cov"]:.1f}%|{m["roi"]:.1f}%|{"YES" if ok else "NO"}|')
    L += ['',f'Frozen PRE size = **top {chosen}/day**（Mar-Mayで固定）','',
          '## Jun-Aug holdout top-N reference','|PRE topN|PRE/day|BUY/day|BUY R|①頭率|7点的中率|coverage|7点ROI|','|---:|---:|---:|---:|---:|---:|---:|---:|']
    for n,pd,bd,m in hs:
        L.append(f'|{n}|{pd:.2f}|{bd:.2f}|{m["n"]}|{m["head"]:.1f}%|{m["hit"]:.1f}%|{m["cov"]:.1f}%|{m["roi"]:.1f}%|')

    L += ['','## Frozen choice vs current top5 on Jun-Aug','|方式|PRE R|BUY R|①頭率|7点的中率|coverage|7点ROI|','|---|---:|---:|---:|---:|---:|---:|']
    L.append(f'|現行 top5|{len(bp)}|{bm["n"]}|{bm["head"]:.1f}%|{bm["hit"]:.1f}%|{bm["cov"]:.1f}%|{bm["roi"]:.1f}%|')
    L.append(f'|v137 frozen top{chosen}|{len(cp)}|{cm["n"]}|{cm["head"]:.1f}%|{cm["hit"]:.1f}%|{cm["cov"]:.1f}%|{cm["roi"]:.1f}%|')

    L += ['','## Monthly stability of frozen choice','|月|PRE R|BUY R|①頭率|7点的中率|coverage|ROI|','|---|---:|---:|---:|---:|---:|---:|']
    for mo in ['2026-03','2026-04','2026-05','2026-06','2026-07','2026-08']:
        mr=[r for r in src if r.get('month')==mo];p,b=select(mr,chosen);m=metric(b)
        L.append(f'|{mo}|{len(p)}|{m["n"]}|{m["head"]:.1f}%|{m["hit"]:.1f}%|{m["cov"]:.1f}%|{m["roi"]:.1f}%|')

    better=(cm['roi']>bm['roi'] and cm['hit']>=bm['hit']-1.0 and cm['head']>=bm['head']-1.0)
    L += ['','## v137判定',
          f'- Holdout ROI: top5 **{bm["roi"]:.1f}%** → frozen top{chosen} **{cm["roi"]:.1f}%**.',
          f'- Holdout 7点的中率: top5 **{bm["hit"]:.1f}%** → frozen top{chosen} **{cm["hit"]:.1f}%**.',
          f'- Holdout ①頭率: top5 **{bm["head"]:.1f}%** → frozen top{chosen} **{cm["head"]:.1f}%**.',
          f'- **V137 LEGACY TOP-N = {"PROMISING" if better else "KEEP TOP5"}**',
          '- Holdout表の全Nは診断用。Jun-Augを見てNを再選択しない。']
    open(SUMMARY,'w',encoding='utf-8').write('\n'.join(L)+'\n')

    rec=[]
    for n,ok,pd,bd,m in sweep:
        rec.append({'phase':'VALIDATION','topn':n,'eligible':int(ok),'pre_per_day':pd,'buy_per_day':bd,**m,'chosen':int(n==chosen)})
    for n,pd,bd,m in hs:
        rec.append({'phase':'HOLDOUT','topn':n,'eligible':'','pre_per_day':pd,'buy_per_day':bd,**m,'chosen':int(n==chosen)})
    with open(OUT,'w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rec[0].keys()));w.writeheader();w.writerows(rec)

if __name__=='__main__':main()
