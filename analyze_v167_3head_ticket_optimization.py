#!/usr/bin/env python3
"""v167: optimize v166 3-head ticket count / p3 threshold without leakage.

Uses frozen v165 p3head and v166 direct ordered-pair ranking. Jun-Aug 2026 only.
Payout is settlement-only after rankings and ticket-count policy are fixed.
"""
from __future__ import annotations
import csv
from analyze_v166_3head_pair_direct import read, ff, ii, combo, choose, score_month, SRC, HEADSRC, TEST_MONTHS

OUT='analysis_v167_3head_ticket_optimization.csv'
SUMMARY='summary_v167_3head_ticket_optimization.md'
CUTS=[.20,.25,.30,.35,.40]
POINTS=[7,10]
SWITCHES=[.25,.30,.35,.40,.45,.50]

def fixed_metric(rs,cut,n):
    q=[r for r in rs if ff(r.get('p3head'))>=cut]
    h=[r for r in q if combo(r.get('actual_combo'))[:1]==[3]]
    hit=[r for r in q if 0<ii(r.get('v166_rank20'))<=n]
    settled=[r for r in q if ii(r.get('valid_payout'))==1]
    ret=sum(ff(r.get('payout100')) for r in settled if 0<ii(r.get('v166_rank20'))<=n)
    inv=len(settled)*n*100
    return dict(policy=f'p3>={cut:.2f}_{n}pt',cut=cut,switch='',races=len(q),head3=len(h),head_rate=100*len(h)/len(q) if q else 0,hits=len(hit),hit_rate=100*len(hit)/len(q) if q else 0,coverage=100*sum(1 for r in h if 0<ii(r.get('v166_rank20'))<=n)/len(h) if h else 0,investment=inv,return_yen=ret,roi=100*ret/inv if inv else 0)

def variable_metric(rs,cut,sw):
    q=[r for r in rs if ff(r.get('p3head'))>=cut]
    h=[r for r in q if combo(r.get('actual_combo'))[:1]==[3]]
    def pts(r): return 10 if ff(r.get('p3head'))>=sw else 7
    hit=[r for r in q if 0<ii(r.get('v166_rank20'))<=pts(r)]
    settled=[r for r in q if ii(r.get('valid_payout'))==1]
    ret=sum(ff(r.get('payout100')) for r in settled if 0<ii(r.get('v166_rank20'))<=pts(r))
    inv=sum(pts(r)*100 for r in settled)
    return dict(policy=f'p3>={cut:.2f}_7to10@{sw:.2f}',cut=cut,switch=sw,races=len(q),head3=len(h),head_rate=100*len(h)/len(q) if q else 0,hits=len(hit),hit_rate=100*len(hit)/len(q) if q else 0,coverage=100*sum(1 for r in h if 0<ii(r.get('v166_rank20'))<=pts(r))/len(h) if h else 0,investment=inv,return_yen=ret,roi=100*ret/inv if inv else 0)

def main():
    src=read(SRC); hp={int(r['source_index']):ff(r.get('p3head')) for r in read(HEADSRC)}
    for i,r in enumerate(src): r['p3head']=hp.get(i,'')
    lam,_=choose(src); out=[]
    for mo in TEST_MONTHS: out+=score_month(src,mo,lam)
    keyp={(r['date'],r.get('race_code')):hp.get(i,'') for i,r in enumerate(src)}
    for r in out:r['p3head']=keyp.get((r['date'],r.get('race_code')),'')
    rows=[]
    for cut in CUTS:
        for n in POINTS:
            x=fixed_metric(out,cut,n);x['month']='ALL';rows.append(x)
        for sw in SWITCHES:
            if sw>cut:
                x=variable_metric(out,cut,sw);x['month']='ALL';rows.append(x)
    # monthly diagnostics for every policy
    allpol=list(rows)
    for base in allpol:
        for mo in TEST_MONTHS:
            q=[r for r in out if r.get('v166_month')==mo]
            if base['switch']=='': x=fixed_metric(q,float(base['cut']),int(base['policy'].split('_')[-1].replace('pt','')))
            else: x=variable_metric(q,float(base['cut']),float(base['switch']))
            x['month']=mo;rows.append(x)
    fields=['policy','month','cut','switch','races','head3','head_rate','hits','hit_rate','coverage','investment','return_yen','roi']
    with open(OUT,'w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
    overall=[r for r in rows if r['month']=='ALL']
    # ranking: ROI first; tie-break hit rate, coverage. Report monthly floor for stability.
    for r in overall:
        ms=[x['roi'] for x in rows if x['policy']==r['policy'] and x['month']!='ALL'];r['min_month_roi']=min(ms) if ms else 0
    ranked=sorted(overall,key=lambda r:(-r['roi'],-r['hit_rate'],-r['coverage']))
    L=['# v167 3号艇 ticket optimization','',f'- v165 p3head frozen / v166 direct-pair λ={lam:.2f}.','- Jun-Aug walk-forward only; no current-race result/payout/final odds in predictive features.','- payout is settlement-only.','- Compare fixed 7/10 tickets and p3-dependent 7→10 switching.','','## Top policies by ROI','|rank|policy|R|③頭率|hit|coverage|ROI|min monthly ROI|','|---:|---|---:|---:|---:|---:|---:|---:|']
    for i,r in enumerate(ranked[:15],1):L.append(f"|{i}|{r['policy']}|{r['races']}|{r['head_rate']:.2f}%|{r['hit_rate']:.2f}%|{r['coverage']:.2f}%|{r['roi']:.1f}%|{r['min_month_roi']:.1f}%|")
    L += ['','## Fixed 7 vs 10','|p3 cut|7pt ROI|7pt hit|10pt ROI|10pt hit|','|---:|---:|---:|---:|---:|']
    for cut in CUTS:
        a=next(r for r in overall if r['policy']==f'p3>={cut:.2f}_7pt');b=next(r for r in overall if r['policy']==f'p3>={cut:.2f}_10pt');L.append(f"|{cut:.2f}|{a['roi']:.1f}%|{a['hit_rate']:.2f}%|{b['roi']:.1f}%|{b['hit_rate']:.2f}%|")
    best=ranked[0]
    L += ['','## Mechanical best by primary objective',f"**{best['policy']}**: ROI {best['roi']:.1f}%, hit {best['hit_rate']:.2f}%, coverage {best['coverage']:.2f}%, min monthly ROI {best['min_month_roi']:.1f}%.",'','This is a backtest selection, not production adoption. Require stability review before freeze.']
    open(SUMMARY,'w',encoding='utf-8').write('\n'.join(L)+'\n');print('\n'.join(L))
if __name__=='__main__':main()
