"""v121: six-month Mar-Aug 2026 retrospective walk-forward diagnostic for 1-head top5/day.

Design
- Source: v108 frozen pre-result feature table.
- Refit v109 monthly using only dates strictly before each evaluated month.
- Refit v110 role models monthly using only dates strictly before each evaluated month.
- v110 lambda fixed at 0.50; never tuned here.
- Rank races using p109 only; no result/payout/odds in race selection.
- Evaluate fixed top7/top8/top10 v110 tickets after selection is frozen.

Caveat
- Mar-May overlap the historical v108/v110 development period, so they are retrospective diagnostics,
  not untouched holdout. Jun-Aug remain the clean holdout months for the frozen architecture/lambda.
"""
from __future__ import annotations
import csv
from collections import defaultdict, Counter
from datetime import date

from analyze_v109_1head_monthly_walkforward import fit as fit109, xmatrix, ii, ff
from analyze_v110b_1head_role_tickets import prepare_month

SRC='analysis_v108_1head_feasibility.csv'
OUT='summary_v121_1head_six_month_top5.md'
DETAIL='analysis_v121_1head_six_month_top5.csv'
MONTHS=['2026-03','2026-04','2026-05','2026-06','2026-07','2026-08']
S_CUT=.72
CENTER=.775

def read_csv(path):
    with open(path,encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def pct(a,b):return 100*a/b if b else 0.0

def rank_center(rs):return sorted(rs,key=lambda r:(abs(ff(r.get('p109'))-CENTER),-ff(r.get('p109')),r.get('race_code','')))
def rank_high(rs):return sorted(rs,key=lambda r:(-ff(r.get('p109')),r.get('race_code','')))

def metric(rs,npt=7):
    q=[r for r in rs if ii(r.get('valid_payout'))==1]
    n=len(q);h=sum(ii(r.get('head_hit')) for r in q)
    hits=[r for r in q if 0<ii(r.get('rank_l50'))<=npt]
    heads=[r for r in q if ii(r.get('head_hit'))==1]
    cov=sum(1 for r in heads if 0<ii(r.get('rank_l50'))<=npt)
    inv=n*npt*100;ret=sum(ii(r.get('payout100')) for r in hits)
    return n,h,pct(h,n),len(hits),pct(len(hits),n),pct(cov,len(heads)),inv,ret,pct(ret,inv)

def main():
    src=[r for r in read_csv(SRC) if ii(r.get('valid_result'))==1]

    # Strict month-before p109 for every Mar-Aug race.
    wf={}
    for mo in MONTHS:
        first=date.fromisoformat(mo+'-01')
        train=[r for r in src if date.fromisoformat(r['date'])<first]
        test=[r for r in src if r.get('month')==mo]
        model=fit109(train);pp=model.predict_proba(xmatrix(test))[:,1]
        for r,p in zip(test,pp):
            r['p109']=round(float(p),8);r['v121_train_n109']=len(train)
        wf[mo]=(len(train),len(test))

    # v110 monthly pre-month role refit, lambda fixed at .50.
    bymo={}
    for mo in MONTHS:
        print('v121 prepare',mo,flush=True)
        bymo[mo]=prepare_month(src,mo)

    allrows=sum((bymo[m] for m in MONTHS),[])
    S=[r for r in allrows if ff(r.get('p109'))>=S_CUT and ii(r.get('valid_payout'))==1]
    days=sorted(set(r['date'] for r in S))

    # freeze daily selections for two rules and N choices
    selected={}
    for rule,fn in [('P75-center',rank_center),('P-high',rank_high)]:
        for N in [3,5,7,10]:
            z=[]
            for d in days:
                q=[r for r in S if r['date']==d]
                z.extend(fn(q)[:N])
            selected[(rule,N)]=z

    # miss decomposition across all S, fixed top7
    miss=[r for r in S if ii(r.get('head_hit'))==1 and not (0<ii(r.get('rank_l50'))<=7)]
    miss_type=Counter()
    for r in miss:
        act=(r.get('actual_combo') or '').split('-')
        order=(r.get('order_l50') or '').split(';')[:7]
        if len(act)!=3:continue
        pairs=[x.split('-') for x in order if x]
        sec={x[1] for x in pairs if len(x)==3};third={x[2] for x in pairs if len(x)==3}
        s2=act[1] in sec;s3=act[2] in third
        if s2 and s3:miss_type['both_roles_present_wrong_pair']+=1
        elif not s2 and not s3:miss_type['both_out']+=1
        elif not s2:miss_type['2nd_out']+=1
        else:miss_type['3rd_out']+=1

    L=['# v121 1-head six-month top5/day diagnostic','',
       '- Period: **2026-03-01..2026-08-31**.',
       '- v109 p109 is refit month-by-month using only strictly earlier dates.',
       '- v110 role model is also refit month-by-month using only strictly earlier dates; lambda is fixed at **0.50**.',
       '- Race selection uses p109 only. Current/final odds and current-race results are not selection inputs.',
       '- **Important:** Mar-May overlap the original development/tuning period, so treat them as retrospective diagnostics. Jun-Aug are the clean holdout block.','',
       '## Monthly model volume','|month|v109 train R|eval R|S candidates|','|---|---:|---:|---:|']
    for mo in MONTHS:
        sc=sum(1 for r in S if r.get('month')==mo)
        L.append(f'|{mo}|{wf[mo][0]:,}|{wf[mo][1]:,}|{sc:,}|')

    L+=['','## Daily top-N aggregate: six months','|rule|N/day|selected R|①頭率|7点的中率|7点coverage|7点ROI|8点ROI|10点ROI|','|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for rule in ['P75-center','P-high']:
        for N in [3,5,7,10]:
            z=selected[(rule,N)]
            a=metric(z,7);b=metric(z,8);c=metric(z,10)
            L.append(f'|{rule}|{N}|{a[0]}|{a[2]:.1f}%|{a[4]:.1f}%|{a[5]:.1f}%|{a[8]:.1f}%|{b[8]:.1f}%|{c[8]:.1f}%|')

    L+=['','## Top-5/day by month','|month|rule|R|①頭率|7点的中率|7点ROI|8点ROI|10点ROI|','|---|---|---:|---:|---:|---:|---:|---:|']
    for mo in MONTHS:
        mdays=sorted(set(r['date'] for r in S if r.get('month')==mo))
        for rule,fn in [('P75-center',rank_center),('P-high',rank_high)]:
            z=[]
            for d in mdays:z.extend(fn([r for r in S if r['date']==d])[:5])
            a=metric(z,7);b=metric(z,8);c=metric(z,10)
            L.append(f'|{mo}|{rule}|{a[0]}|{a[2]:.1f}%|{a[4]:.1f}%|{a[8]:.1f}%|{b[8]:.1f}%|{c[8]:.1f}%|')

    # clean holdout only Jun-Aug
    hold=[r for r in selected[('P75-center',5)] if r.get('month') in ('2026-06','2026-07','2026-08')]
    ha=metric(hold,7);hb=metric(hold,8);hc=metric(hold,10)
    L+=['','## Clean holdout focus: Jun-Aug, P75-center top5/day',
        f'- selected: **{ha[0]}R**',f'- ①頭率: **{ha[2]:.1f}%**',f'- 7点的中率: **{ha[4]:.1f}%** / coverage **{ha[5]:.1f}%** / ROI **{ha[8]:.1f}%**',
        f'- 8点 ROI: **{hb[8]:.1f}%**',f'- 10点 ROI: **{hc[8]:.1f}%**','',
        '## S head-hit but fixed7 miss decomposition',
        f'- S valid-payout races: **{len(S):,}R**',f'- ①頭的中かつ7点外れ: **{len(miss):,}R**',
        '- '+', '.join(f'{k}={v}' for k,v in sorted(miss_type.items()))+'.','',
        '## Interpretation guardrail',
        '- P75-center (77.5%付近) was suggested from the later Sep-01..04 diagnostic, so the six-month check is a retrospective robustness test, not a time-forward rule discovery test.',
        '- Do not replace the frozen production/shadow rule from this result alone. Use the Jun-Aug clean block plus Sep prospective results to decide whether a top5/day selector deserves adoption.']
    open(OUT,'w',encoding='utf-8').write('\n'.join(L)+'\n')

    # compact selected detail for audit
    detail=[]
    for rule in ['P75-center','P-high']:
        for r in selected[(rule,5)]:
            detail.append({'rule':rule,'date':r['date'],'month':r['month'],'race_code':r['race_code'],'venue':r['venue'],'race':r['race'],'p109':r['p109'],'head_hit':r['head_hit'],'rank_l50':r['rank_l50'],'actual_combo':r['actual_combo'],'payout100':r['payout100']})
    with open(DETAIL,'w',encoding='utf-8-sig',newline='') as f:
        fs=list(detail[0].keys());w=csv.DictWriter(f,fieldnames=fs);w.writeheader();w.writerows(detail)

if __name__=='__main__':main()
