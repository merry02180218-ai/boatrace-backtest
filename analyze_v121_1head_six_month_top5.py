"""v121: six-month Mar-Aug 2026 two-stage 1-head operational diagnostic.

Operational design to match real use:
1) PRE stage: choose a limited watch-list using ONLY pre-exhibition features.
2) LIVE stage: after current exhibition/original-entry info exists, apply the frozen v109
   full probability gate (S >= 72%) to decide BUY / SKIP.
3) BUY races use v110 lambda=.50 opponent ranking; evaluate 7/8/10 tickets after selection freeze.

No-leak
- v108 source rows were frozen before result/payout settlement.
- PRE model for each month is fit only on strictly earlier dates.
- v109 full model for each month is fit only on strictly earlier dates.
- v110 role model for each month is fit only on strictly earlier dates; lambda is fixed .50.
- PRE ranking excludes current exhibition/ST/original/direct/threat/margin features.
- Current/final odds and result/payout are never selection inputs.

Caveat
- v108 itself drops races where boat1 exhibited outside course1, so historical PRE pool slightly
  under-represents races that would have been watched pre-race and later excluded by entry change.
- Mar-May overlap the historical development block; Jun-Aug are the clean holdout focus.
"""
from __future__ import annotations
import csv
from collections import defaultdict
from datetime import date

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from analyze_v109_1head_monthly_walkforward import fit as fit109, xmatrix, ii, ff
from analyze_v110b_1head_role_tickets import prepare_month

SRC='analysis_v108_1head_feasibility.csv'
OUT='summary_v121_1head_six_month_top5.md'
DETAIL='analysis_v121_1head_six_month_top5.csv'
MONTHS=['2026-03','2026-04','2026-05','2026-06','2026-07','2026-08']
HOLDOUT={'2026-06','2026-07','2026-08'}
S_CUT=.72
PRE_TOPS=[5,8,10,12,15,20,25]
VENUES=[f'{i:02d}' for i in range(1,25)]

# Only information available before current exhibition.
PRE_FEATURES=[
 'one_grade','one_wr','one_local','one_motor','one_waku_wr','one_nst_strength',
 'one_waku_sr_strength','one_past_win','one_meet_st_strength'
]

def read_csv(path):
    with open(path,encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def pct(a,b):return 100*a/b if b else 0.0

def xpre(rs):
    out=[]
    for r in rs:
        row=[ff(r.get(k),0) for k in PRE_FEATURES]
        vv=str(r.get('venue','')).zfill(2)
        row.extend(1.0 if vv==v else 0.0 for v in VENUES)
        out.append(row)
    return np.asarray(out,dtype=float)

def fit_pre(train):
    p=Pipeline([('scale',StandardScaler()),('lr',LogisticRegression(C=.5,max_iter=1500,solver='lbfgs'))])
    p.fit(xpre(train),[ii(r.get('head_hit')) for r in train])
    return p

def ticket_metric(rs,npt):
    q=[r for r in rs if ii(r.get('valid_payout'))==1]
    n=len(q);h=sum(ii(r.get('head_hit')) for r in q)
    hits=[r for r in q if 0<ii(r.get('rank_l50'))<=npt]
    heads=[r for r in q if ii(r.get('head_hit'))==1]
    cov=sum(1 for r in heads if 0<ii(r.get('rank_l50'))<=npt)
    inv=n*npt*100;ret=sum(ii(r.get('payout100')) for r in hits)
    return {'n':n,'head':h,'head_rate':pct(h,n),'hit':len(hits),'hit_rate':pct(len(hits),n),
            'coverage':pct(cov,len(heads)),'inv':inv,'ret':ret,'roi':pct(ret,inv)}

def daily_select(rows_by_day,topn):
    pre=[];buy=[]
    for d in sorted(rows_by_day):
        q=sorted(rows_by_day[d],key=lambda r:(-ff(r.get('pre_p')),r.get('race_code','')))
        watch=q[:topn]
        pre.extend(watch)
        # LIVE decision only inside the pre-selected watch list.
        buy.extend([r for r in watch if ff(r.get('p109'))>=S_CUT and ii(r.get('entry_course'))==1])
    return pre,buy

def stage_counts(pre,buy,days):
    pby=defaultdict(int);bby=defaultdict(int)
    for r in pre:pby[r['date']]+=1
    for r in buy:bby[r['date']]+=1
    avp=sum(pby[d] for d in days)/len(days) if days else 0
    avb=sum(bby[d] for d in days)/len(days) if days else 0
    d3_7=sum(1 for d in days if 3<=bby[d]<=7)
    d4_6=sum(1 for d in days if 4<=bby[d]<=6)
    zero=sum(1 for d in days if bby[d]==0)
    return avp,avb,d3_7,d4_6,zero

def main():
    src=[r for r in read_csv(SRC) if ii(r.get('valid_result'))==1]
    month_stats={};prepared={}

    # Strict monthly walk-forward for PRE and LIVE models.
    for mo in MONTHS:
        first=date.fromisoformat(mo+'-01')
        train=[r for r in src if date.fromisoformat(r['date'])<first]
        test=[r for r in src if r.get('month')==mo]

        pre_model=fit_pre(train)
        pp=pre_model.predict_proba(xpre(test))[:,1]
        live_model=fit109(train)
        lp=live_model.predict_proba(xmatrix(test))[:,1]
        for r,p0,p1 in zip(test,pp,lp):
            r['pre_p']=round(float(p0),8)
            r['p109']=round(float(p1),8)
            r['v121_pre_train_n']=len(train)
            r['v121_live_train_n']=len(train)

        # prepare_month copies the rows but preserves pre_p/p109 already attached to src.
        print('v121 prepare role',mo,flush=True)
        prepared[mo]=prepare_month(src,mo)
        month_stats[mo]=(len(train),len(test))

    allrows=sum((prepared[m] for m in MONTHS),[])
    byday=defaultdict(list)
    for r in allrows:
        if ii(r.get('valid_payout'))==1:byday[r['date']].append(r)
    days=sorted(byday)

    scenarios={}
    for topn in PRE_TOPS:
        pre,buy=daily_select(byday,topn)
        scenarios[topn]=(pre,buy)

    L=['# v121 1-head six-month TWO-STAGE operational diagnostic','',
       '- Period: **2026-03-01..2026-08-31**.',
       '- Stage 1 PRE: pre-exhibition features only -> daily watch-list.',
       '- Stage 2 LIVE: only those PRE races are judged by full v109; **BUY = p109 >=72% and boat1 remains course1**.',
       '- BUY races use frozen v110 role blend **lambda=.50** for 7/8/10-ticket evaluation.',
       '- No current/final odds, result, or payout is used for PRE or LIVE selection.',
       '- Goal is not to force exactly 5 races/day after exhibition; it is to choose PRE candidates first and have the LIVE BUY count average around 5/day.','',
       '## PRE features used',
       '- '+', '.join(PRE_FEATURES),
       '- Explicitly excluded from PRE: current exhibition time/ST/original exhibition, direct score, threat/margin variables, current entry course, odds.','',
       '## Six-month candidate-size comparison',
       '|PRE top/day|PRE R/day|BUY R/day|BUY R|①頭率|7点的中率|7点coverage|7点ROI|8点ROI|10点ROI|BUY 3-7R days|BUY 4-6R days|0 BUY days|',
       '|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']

    for topn in PRE_TOPS:
        pre,buy=scenarios[topn];a=ticket_metric(buy,7);b=ticket_metric(buy,8);c=ticket_metric(buy,10)
        avp,avb,d37,d46,z=stage_counts(pre,buy,days)
        L.append(f'|{topn}|{avp:.2f}|{avb:.2f}|{a["n"]}|{a["head_rate"]:.1f}%|{a["hit_rate"]:.1f}%|{a["coverage"]:.1f}%|{a["roi"]:.1f}%|{b["roi"]:.1f}%|{c["roi"]:.1f}%|{d37}/{len(days)}|{d46}/{len(days)}|{z}|')

    # Pick the scenario whose BUY/day is closest to 5; tie -> fewer PRE watches.
    chosen=min(PRE_TOPS,key=lambda n:(abs(stage_counts(*scenarios[n],days)[1]-5.0),n))
    pre,buy=scenarios[chosen]
    L+=['',f'## Mechanical target-count choice: PRE top {chosen}/day',
        '- This choice uses only closeness of average BUY count to 5/day, **not ROI or race outcomes**.',
        f'- Six-month PRE watch count: **{len(pre)}R**; LIVE BUY count: **{len(buy)}R**.','',
        '## Monthly results for the chosen PRE size',
        '|month|days|PRE R|BUY R|BUY/day|①頭率|7点的中率|7点ROI|8点ROI|10点ROI|',
        '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for mo in MONTHS:
        mdays=sorted(d for d in days if d.startswith(mo))
        mp=[r for r in pre if r.get('month')==mo];mb=[r for r in buy if r.get('month')==mo]
        a=ticket_metric(mb,7);b=ticket_metric(mb,8);c=ticket_metric(mb,10)
        L.append(f'|{mo}|{len(mdays)}|{len(mp)}|{a["n"]}|{a["n"]/len(mdays) if mdays else 0:.2f}|{a["head_rate"]:.1f}%|{a["hit_rate"]:.1f}%|{a["roi"]:.1f}%|{b["roi"]:.1f}%|{c["roi"]:.1f}%|')

    hbuy=[r for r in buy if r.get('month') in HOLDOUT]
    ha=ticket_metric(hbuy,7);hb=ticket_metric(hbuy,8);hc=ticket_metric(hbuy,10)
    hdays=sorted(d for d in days if d[:7] in HOLDOUT)
    L+=['','## Clean holdout focus: Jun-Aug',
        f'- Chosen PRE size: **top {chosen}/day**.',
        f'- LIVE BUY: **{ha["n"]}R / {len(hdays)} days = {ha["n"]/len(hdays) if hdays else 0:.2f}R/day**.',
        f'- ①頭率 **{ha["head_rate"]:.1f}%**.',
        f'- 7点: hit **{ha["hit_rate"]:.1f}%**, coverage **{ha["coverage"]:.1f}%**, ROI **{ha["roi"]:.1f}%**.',
        f'- 8点 ROI **{hb["roi"]:.1f}%** / 10点 ROI **{hc["roi"]:.1f}%**.','',
        '## Guardrails',
        '- Do not reinterpret this as “pick the best five after exhibition.” PRE races are frozen first.',
        '- LIVE p109 is only a BUY/SKIP gate inside that PRE list.',
        '- Mar-May are retrospective development-overlap diagnostics; Jun-Aug matter more for adoption.',
        '- Because v108 historically excludes entry-changed boat1 races before settlement, prospective operation should still keep the explicit LIVE course1 gate and count those PRE watches as SKIP when they occur.']
    open(OUT,'w',encoding='utf-8').write('\n'.join(L)+'\n')

    detail=[]
    chosen_pre_codes={r['race_code'] for r in pre}
    chosen_buy_codes={r['race_code'] for r in buy}
    for r in allrows:
        if r['race_code'] not in chosen_pre_codes:continue
        detail.append({
          'date':r['date'],'month':r['month'],'race_code':r['race_code'],'venue':r['venue'],'race':r['race'],
          'pre_rank_pool':chosen,'pre_p':r.get('pre_p'),'pre_selected':1,
          'p109_live':r.get('p109'),'live_buy':int(r['race_code'] in chosen_buy_codes),
          'entry_course':r.get('entry_course'),'head_hit':r.get('head_hit'),'rank_l50':r.get('rank_l50'),
          'actual_combo':r.get('actual_combo'),'payout100':r.get('payout100')})
    if detail:
        with open(DETAIL,'w',encoding='utf-8-sig',newline='') as f:
            fs=list(detail[0].keys());w=csv.DictWriter(f,fieldnames=fs);w.writeheader();w.writerows(detail)

if __name__=='__main__':main()
