"""v124: frozen v121+v123 confirmation on 2026-09-01..04.

Rule is fixed BEFORE target-period settlement:
PRE: daily top5 by pre-exhibition logistic score trained only through 2026-08-31.
LIVE: within PRE top5 only, require p109>=0.72, boat1 exhibition course1,
      and frozen v123 ex_margin23 >= -0.235.
Tickets: frozen v110 lambda=.50 top7.
All target results/payouts are read only after all four days are frozen.
No odds are used.
"""
from __future__ import annotations
import csv
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from backtest import rows
from analyze_v108_1head_feasibility import feature_row, bycode, st_bias, update_st
from analyze_v109_1head_monthly_walkforward import fit as fit109, xmatrix, ii, ff
from analyze_v110_1head_role_tickets import fit_roles, pair_order

DAYS=[date(2026,9,d) for d in range(1,5)]
TRAIN_END='2026-08-31'
SRC='analysis_v108_1head_feasibility.csv'
OUT='replay_v124_20260901_04_v123_frozen.csv'
SUMMARY='summary_v124_20260901_04_v123_frozen.md'
S_CUT=.72; V123_EX_MARGIN23=-.235; LAMBDA=.50
PRE_FEATURES=['one_grade','one_wr','one_local','one_motor','one_waku_wr','one_nst_strength','one_waku_sr_strength','one_past_win','one_meet_st_strength']
VENUES=[f'{i:02d}' for i in range(1,25)]
VENUE_NAMES={'01':'桐生','02':'戸田','03':'江戸川','04':'平和島','05':'多摩川','06':'浜名湖','07':'蒲郡','08':'常滑','09':'津','10':'三国','11':'びわこ','12':'住之江','13':'尼崎','14':'鳴門','15':'丸亀','16':'児島','17':'宮島','18':'徳山','19':'下関','20':'若松','21':'芦屋','22':'福岡','23':'唐津','24':'大村'}

def read_csv(path):
    with open(path,encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def xpre(rs):
    out=[]
    for r in rs:
        row=[ff(r.get(k),0) for k in PRE_FEATURES]
        vv=str(r.get('venue','')).zfill(2); row.extend(1.0 if vv==v else 0.0 for v in VENUES); out.append(row)
    return np.asarray(out,dtype=float)
def fit_pre(train):
    p=Pipeline([('scale',StandardScaler()),('lr',LogisticRegression(C=.5,max_iter=1500,solver='lbfgs'))])
    p.fit(xpre(train),[ii(r.get('head_hit')) for r in train]); return p
def pct(a,b):return 100*a/b if b else 0.0
def fetch_st_day(d):
    try:return d,rows(f"data/previews/stt/{d.strftime('%Y/%m/%d')}.csv")
    except Exception:return d,[]
def metric(rs):
    n=len(rs); h=sum(r['head_hit'] for r in rs); t=sum(r['ticket7_hit'] for r in rs); inv=n*700; ret=sum(r['return7'] for r in rs)
    return n,pct(h,n),pct(t,n),pct(ret,inv)

def main():
    src=read_csv(SRC)
    train=[r for r in src if ii(r.get('valid_result'))==1 and r.get('date','')<=TRAIN_END]
    pre_model=fit_pre(train); live_model=fit109(train)
    m2,m3,_=fit_roles([r for r in src if r.get('date','')<'2026-09-01'])

    # Prior-only ST-bias snapshots.
    st_days=[]; d=date(2025,10,1)
    while d<DAYS[-1]: st_days.append(d); d+=timedelta(days=1)
    got={}
    with ThreadPoolExecutor(max_workers=14) as ex:
        fs=[ex.submit(fetch_st_day,d) for d in st_days]
        for f in as_completed(fs): dd,z=f.result(); got[dd]=z
    sums={b:[] for b in range(1,7)}; allv=[]; bias_by_day={}
    for d in sorted(got):
        if d in DAYS:bias_by_day[d]=st_bias(sums,allv)
        if got[d]:update_st(got[d],sums,allv)
    if DAYS[-1] not in bias_by_day:bias_by_day[DAYS[-1]]=st_bias(sums,allv)

    frozen=[]; stage=[]
    for HD in DAYS:
        y=HD.strftime('%Y/%m/%d')
        cards=rows(f'data/programs/race_cards/{y}.csv'); waku=bycode(rows(f'data/programs/waku10/{y}.csv'))
        tkz=bycode(rows(f'data/previews/tkz/{y}.csv')); stt=bycode(rows(f'data/previews/stt/{y}.csv')); orig=bycode(rows(f'data/previews/original_exhibition/{y}.csv'))
        pool=[]
        for card in cards:
            code=card.get('レースコード','')
            if not code or code not in waku or code not in tkz or code not in stt or code not in orig:continue
            feat=feature_row(HD.isoformat(),card,waku[code],tkz,stt,orig,bias_by_day[HD])
            if feat is None:continue
            pp=float(pre_model.predict_proba(xpre([feat]))[0,1]); lp=float(live_model.predict_proba(xmatrix([feat]))[0,1]); course=ii(stt[code].get('艇1_コース'))
            tickets=pair_order(feat,m2,m3,LAMBDA)[:7]
            venue=str(card.get('レース場コード','')).zfill(2); race=str(card.get('レース回','')).replace('R','')
            pool.append({'date':HD.isoformat(),'race_code':code,'venue':venue,'venue_name':VENUE_NAMES.get(venue,venue),'race':race,
                         'boat1_name':(card.get('艇1_選手名') or '').strip(),'pre_p':pp,'p109':lp,'entry_course':course,
                         'ex_margin23':ff(feat.get('ex_margin23')),'top7':';'.join(tickets)})
        watch=sorted(pool,key=lambda r:(-r['pre_p'],r['race_code']))[:5]
        for r in watch:
            base=int(r['p109']>=S_CUT and r['entry_course']==1)
            v123=int(base and r['ex_margin23']>=V123_EX_MARGIN23)
            q=dict(r); q.update({'pre_selected':1,'baseline_buy':base,'v123_buy':v123}); stage.append(q)
        frozen.extend([r for r in stage if r['date']==HD.isoformat() and r['v123_buy']==1])

    # Settlement boundary.
    res={}; pay={}
    for HD in DAYS:
        y=HD.strftime('%Y/%m/%d'); res[HD]=bycode(rows(f'data/results/realtime/{y}.csv')); pay[HD]=bycode(rows(f'data/results/payouts/{y}.csv'))
    settled=[]
    for r in stage:
        HD=date.fromisoformat(r['date']); rr=res[HD].get(r['race_code'],{}); pr=pay[HD].get(r['race_code'],{})
        win=ii(rr.get('1着_艇番')); combo=(pr.get('3連単_組番') or '').strip(); payout=ii(pr.get('3連単_払戻金'))
        hit=int(combo in (r['top7'].split(';') if r['top7'] else []) and payout>0)
        q=dict(r); q.update({'winner':win,'head_hit':int(win==1),'actual_combo':combo,'payout100':payout,'ticket7_hit':hit,'return7':payout if hit else 0}); settled.append(q)
    with open(OUT,'w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(settled[0].keys()));w.writeheader();w.writerows(settled)

    base=[r for r in settled if r['baseline_buy']==1]; v123=[r for r in settled if r['v123_buy']==1]
    bm=metric(base); vm=metric(v123)
    L=['# v124 frozen Sep1-4 confirmation of v123','',
       '- PRE: daily top5 by pre-exhibition-only score trained through Aug31.',
       '- LIVE baseline: p109>=72% and boat1 course1.',
       '- Frozen v123 extra gate: **ex_margin23 >= -0.235**.',
       '- v110 lambda=.50 fixed top7. No odds.',
       '- All four days frozen before Sep1-4 result/payout files are read.','',
       '## Aggregate','|rule|BUY R|BUY/day|①頭率|7点的中率|7点ROI|','|---|---:|---:|---:|---:|---:|',
       f'|baseline|{bm[0]}|{bm[0]/len(DAYS):.2f}|{bm[1]:.1f}%|{bm[2]:.1f}%|{bm[3]:.1f}%|',
       f'|v123 frozen|{vm[0]}|{vm[0]/len(DAYS):.2f}|{vm[1]:.1f}%|{vm[2]:.1f}%|{vm[3]:.1f}%|','',
       '## Daily v123','|date|BUY R|①頭率|7点的中率|7点ROI|','|---|---:|---:|---:|---:|']
    for HD in DAYS:
        z=[r for r in v123 if r['date']==HD.isoformat()]; m=metric(z); L.append(f'|{HD.isoformat()}|{m[0]}|{m[1]:.1f}%|{m[2]:.1f}%|{m[3]:.1f}%|')
    L+=['','## Interpretation','- This is a frozen-rule confirmation only. No Sep threshold tuning is allowed.',
        '- Because the historical reconstruction requires complete LIVE data to build the row, it may under-represent PRE watches that later lacked preview data; do not treat this as a perfect prospective log.']
    open(SUMMARY,'w',encoding='utf-8').write('\n'.join(L)+'\n')
if __name__=='__main__':main()
