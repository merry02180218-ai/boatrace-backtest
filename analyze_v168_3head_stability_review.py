#!/usr/bin/env python3
"""v168: stability review for the v167 candidate p3>=0.30 / v166 top10.

Candidate is frozen before this review. No optimization on Jun-Aug outcomes.
Reports month, venue, p3-band and payout concentration diagnostics.
Predictive ranking remains frozen v165 p3head + v166 direct pair; payout is settlement-only.
"""
from __future__ import annotations
import csv
from collections import defaultdict
from analyze_v166_3head_pair_direct import read, ff, ii, combo, choose, score_month, SRC, HEADSRC, TEST_MONTHS

OUT='analysis_v168_3head_stability_review.csv'
SUMMARY='summary_v168_3head_stability_review.md'
CUT=.30
N=10

def venue(r):
    rc=str(r.get('race_code') or '')
    return rc[:2] if len(rc)>=2 else 'NA'

def metric(rs,label,group,value):
    q=[r for r in rs if ff(r.get('p3head'))>=CUT]
    h=[r for r in q if combo(r.get('actual_combo'))[:1]==[3]]
    settled=[r for r in q if ii(r.get('valid_payout'))==1]
    wins=[r for r in settled if 0<ii(r.get('v166_rank20'))<=N]
    ret=sum(ff(r.get('payout100')) for r in wins)
    inv=len(settled)*N*100
    payouts=sorted((ff(r.get('payout100')) for r in wins),reverse=True)
    top1=payouts[0] if payouts else 0
    top3=sum(payouts[:3])
    return dict(label=label,group=group,value=value,races=len(q),head3=len(h),head_rate=100*len(h)/len(q) if q else 0,hits=len(wins),hit_rate=100*len(wins)/len(q) if q else 0,coverage=100*sum(1 for r in h if 0<ii(r.get('v166_rank20'))<=N)/len(h) if h else 0,investment=inv,return_yen=ret,roi=100*ret/inv if inv else 0,top1_return_share=100*top1/ret if ret else 0,top3_return_share=100*top3/ret if ret else 0)

def main():
    src=read(SRC); hp={int(r['source_index']):ff(r.get('p3head')) for r in read(HEADSRC)}
    for i,r in enumerate(src):r['p3head']=hp.get(i,'')
    lam,_=choose(src); out=[]
    for mo in TEST_MONTHS:out+=score_month(src,mo,lam)
    keyp={(r['date'],r.get('race_code')):hp.get(i,'') for i,r in enumerate(src)}
    for r in out:r['p3head']=keyp.get((r['date'],r.get('race_code')),'')

    rows=[metric(out,'ALL','all','ALL')]
    for mo in TEST_MONTHS:
        rows.append(metric([r for r in out if r.get('v166_month')==mo],mo,'month',mo))
    vs=sorted(set(venue(r) for r in out if ff(r.get('p3head'))>=CUT))
    for v in vs:
        rows.append(metric([r for r in out if venue(r)==v],f'venue_{v}','venue',v))
    bands=[(.30,.35),(.35,.40),(.40,.50),(.50,2.0)]
    for lo,hi in bands:
        rows.append(metric([r for r in out if lo<=ff(r.get('p3head'))<hi],f'p3_{lo:.2f}_{hi:.2f}','p3_band',f'{lo:.2f}-{hi:.2f}'))

    fields=list(rows[0].keys())
    with open(OUT,'w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
    overall=rows[0]; months=[r for r in rows if r['group']=='month']; venues=[r for r in rows if r['group']=='venue' and r['races']>=5]; bandsr=[r for r in rows if r['group']=='p3_band']
    L=['# v168 3号艇 stability review','',f'- Frozen candidate: p3 >= {CUT:.2f}, v166 top {N} tickets.','- v165 p3head and v166 direct-pair ranking are unchanged.','- Jun-Aug is diagnostic only; no retuning from these outcomes.','- payout is settlement-only.','', '## Overall', '|R|③頭率|hit|coverage|ROI|top1 return share|top3 return share|','|---:|---:|---:|---:|---:|---:|---:|',f"|{overall['races']}|{overall['head_rate']:.2f}%|{overall['hit_rate']:.2f}%|{overall['coverage']:.2f}%|{overall['roi']:.1f}%|{overall['top1_return_share']:.1f}%|{overall['top3_return_share']:.1f}%|",'', '## Monthly','|month|R|hit|coverage|ROI|','|---|---:|---:|---:|---:|']
    for r in months:L.append(f"|{r['value']}|{r['races']}|{r['hit_rate']:.2f}%|{r['coverage']:.2f}%|{r['roi']:.1f}%|")
    L += ['','## p3 bands','|band|R|③頭率|hit|coverage|ROI|','|---|---:|---:|---:|---:|---:|']
    for r in bandsr:L.append(f"|{r['value']}|{r['races']}|{r['head_rate']:.2f}%|{r['hit_rate']:.2f}%|{r['coverage']:.2f}%|{r['roi']:.1f}%|")
    L += ['','## Venue diagnostics (>=5 candidate races)','|venue|R|hit|ROI|','|---|---:|---:|---:|']
    for r in venues:L.append(f"|{r['value']}|{r['races']}|{r['hit_rate']:.2f}%|{r['roi']:.1f}%|")
    minm=min((r['roi'] for r in months),default=0); lowvenues=sum(1 for r in venues if r['roi']<70); nvenues=len(venues)
    concentration=overall['top3_return_share']
    L += ['','## Stability flags',f'- Minimum monthly ROI: **{minm:.1f}%**.',f'- Venues with >=5 races and ROI <70%: **{lowvenues}/{nvenues}**.',f'- Top-3 winning payouts share of total return: **{concentration:.1f}%**.','', 'This review is diagnostic. Production adoption should be decided only after checking these stability flags and the predeclared v167 candidate; do not search a new threshold on Jun-Aug here.']
    open(SUMMARY,'w',encoding='utf-8').write('\n'.join(L)+'\n');print('\n'.join(L))
if __name__=='__main__':main()
