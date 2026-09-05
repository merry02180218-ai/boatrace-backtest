"""v117: 2026-09-04 v109 + v110 fixed no-leak replay.

Purpose
- Reconstruct the CURRENT frozen 1-head implementation on the unseen day 2026-09-04.
- v109 architecture/cuts are unchanged and fit only on settled v108 rows through 2026-08-31.
- v110 role models are fit only on races strictly before Sep-2026; lambda is frozen at 0.50.
- Sep-4 result/payout files are loaded ONLY after every live feature, p109 grade, and top-7 ticket set is frozen.
- No current/final odds are used.
"""
from __future__ import annotations
import csv
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta
from statistics import mean

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from backtest import rows
from analyze_v108_1head_feasibility import feature_row, bycode, st_bias, update_st
from analyze_v110_1head_role_tickets import fit_roles, pair_order

HD=date(2026,9,4)
TRAIN_END='2026-08-31'
SRC='analysis_v108_1head_feasibility.csv'
OUT='replay_v117_20260904_1head.csv'
SUMMARY='summary_v117_20260904_1head.md'
A_CUT=.65; S_CUT=.72; V110_LAMBDA=.50
VENUE_NAMES={'01':'桐生','02':'戸田','03':'江戸川','04':'平和島','05':'多摩川','06':'浜名湖','07':'蒲郡','08':'常滑','09':'津','10':'三国','11':'びわこ','12':'住之江','13':'尼崎','14':'鳴門','15':'丸亀','16':'児島','17':'宮島','18':'徳山','19':'下関','20':'若松','21':'芦屋','22':'福岡','23':'唐津','24':'大村'}
NUM_FEATURES=['one_grade','one_wr','one_local','one_motor','one_waku_wr','one_nst_strength','one_waku_sr_strength','one_past_win','one_meet_st_strength','one_ex','one_st','one_lap','one_turn','one_straight','one_orig_avg','one_direct','one_score','threat2','threat3','threat4','threat5','threat6','threat23_max','threat_all_max','margin2','margin3','margin23','margin_all','st_margin2','st_margin3','st_margin23','ex_margin23','turn_margin23','straight_margin23']
VENUES=[f'{i:02d}' for i in range(1,25)]

def ff(x,d=0.0):
    try:return float(x)
    except Exception:return d

def ii(x,d=0):
    try:return int(float(x))
    except Exception:return d

def read_csv(path):
    with open(path,encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def write_csv(path,rs):
    if not rs:return
    fs=list(rs[0].keys())
    with open(path,'w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fs);w.writeheader();w.writerows(rs)

def xmatrix(rs):
    out=[]
    for r in rs:
        row=[ff(r.get(k),0) for k in NUM_FEATURES]
        vv=str(r.get('venue','')).zfill(2)
        row.extend(1.0 if vv==v else 0.0 for v in VENUES)
        out.append(row)
    return np.asarray(out,dtype=float)

def fit_v109(train):
    p=Pipeline([('scale',StandardScaler()),('lr',LogisticRegression(C=.5,max_iter=1500,solver='lbfgs'))])
    p.fit(xmatrix(train),[ii(r.get('head_hit')) for r in train]);return p

def grade(p):return 'S' if p>=S_CUT else ('A' if p>=A_CUT else 'B')

def fetch_st_day(d):return d,rows(f"data/previews/stt/{d.strftime('%Y/%m/%d')}.csv")
def prior_st_bias():
    ds=[];d=date(2025,10,1)
    while d<HD:ds.append(d);d+=timedelta(days=1)
    got={}
    with ThreadPoolExecutor(max_workers=14) as ex:
        fs=[ex.submit(fetch_st_day,d) for d in ds]
        for i,f in enumerate(as_completed(fs),1):
            try:dd,z=f.result();got[dd]=z
            except Exception:pass
            if i%50==0:print('prior STT days',i,'/',len(ds),flush=True)
    sums={b:[] for b in range(1,7)};allv=[]
    for d in sorted(got):update_st(got[d],sums,allv)
    return st_bias(sums,allv),len(got)

def pct(n,d):return 100*n/d if d else 0.0

def metric(rs):
    n=len(rs);heads=sum(r['head_hit'] for r in rs);hits=sum(r['ticket7_hit'] for r in rs)
    headrows=[r for r in rs if r['head_hit']==1]
    cov=sum(r['ticket7_hit'] for r in headrows)
    inv=n*700;ret=sum(r['return7'] for r in rs)
    avgp=sum(r['p109'] for r in rs)/n*100 if n else 0
    return n,heads,pct(heads,n),avgp,(pct(heads,n)-avgp),hits,pct(hits,n),pct(cov,len(headrows)),inv,ret,pct(ret,inv)

def main():
    hist=[r for r in read_csv(SRC) if ii(r.get('valid_result'))==1 and r.get('date','')<=TRAIN_END]
    v109=fit_v109(hist)
    # v110 Sep role training: strictly pre-Sep rows only; lambda is frozen, never retuned on Sep-4.
    role_train=[r for r in read_csv(SRC) if r.get('date','')<'2026-09-01']
    m2,m3,role_headwins=fit_roles(role_train)
    bias,bias_days=prior_st_bias()

    y=HD.strftime('%Y/%m/%d')
    cards=rows(f'data/programs/race_cards/{y}.csv')
    waku=bycode(rows(f'data/programs/waku10/{y}.csv'))
    tkz=bycode(rows(f'data/previews/tkz/{y}.csv'))
    stt=bycode(rows(f'data/previews/stt/{y}.csv'))
    orig=bycode(rows(f'data/previews/original_exhibition/{y}.csv'))

    frozen=[];complete_n=0;course1_n=0;changed_n=0;missing_n=0
    for card in cards:
        code=card.get('レースコード','')
        if not code or code not in waku:continue
        complete=(code in tkz and code in stt and code in orig)
        if not complete:
            missing_n+=1;continue
        complete_n+=1
        course=ii(stt[code].get('艇1_コース'))
        if course!=1:
            changed_n+=1;continue
        course1_n+=1
        feat=feature_row(HD.isoformat(),card,waku[code],tkz,stt,orig,bias)
        if feat is None:continue
        p=float(v109.predict_proba(xmatrix([feat]))[0,1]);g=grade(p)
        tickets=pair_order(feat,m2,m3,V110_LAMBDA)[:7]
        venue=str(card.get('レース場コード','')).zfill(2)
        race=str(card.get('レース回','')).replace('R','')
        frozen.append({
            'race_code':code,'venue':venue,'venue_name':VENUE_NAMES.get(venue,venue),'race':race,
            'boat1_name':(card.get('艇1_選手名') or '').strip(),'p109':p,'grade':g,
            'top7':';'.join(tickets),'entry_course':course,
        })

    # SETTLEMENT BOUNDARY: result/payout are intentionally loaded only after freeze above.
    res=bycode(rows(f'data/results/realtime/{y}.csv'))
    pay=bycode(rows(f'data/results/payouts/{y}.csv'))
    settled=[]
    for r in frozen:
        rr=res.get(r['race_code'],{});pr=pay.get(r['race_code'],{})
        win=ii(rr.get('1着_艇番'));combo=(pr.get('3連単_組番') or '').strip();payout=ii(pr.get('3連単_払戻金'))
        ts=r['top7'].split(';') if r['top7'] else []
        hit=int(combo in ts and payout>0)
        q=dict(r);q.update({'winner':win,'head_hit':int(win==1),'actual_combo':combo,'payout100':payout,
                            'ticket7_hit':hit,'invest7':700,'return7':payout if hit else 0})
        settled.append(q)
    write_csv(OUT,settled)

    asrows=[r for r in settled if r['grade'] in ('A','S')]
    aplus=[r for r in settled if r['p109']>=A_CUT]
    sonly=[r for r in settled if r['p109']>=S_CUT]
    aonly=[r for r in settled if A_CUT<=r['p109']<S_CUT]
    L=['# v117 2026-09-04 v109 + v110 fixed no-leak replay','',
       '- v109: architecture fixed, train labels through 2026-08-31, A>=65%, S>=72%.',
       '- v110: role lambda fixed at 0.50; Sep-4 is not used for role fitting or tuning.',
       '- Sep-4 result/payout files are read only after p109 grades and top-7 tickets are frozen.',
       '- No current/final odds are used.','',
       f'- historical v109 train: **{len(hist):,}R**',f'- v110 role training head-wins: **{role_headwins:,}R**',
       f'- prior ST-bias days fetched: **{bias_days}**',f'- Sep-4 cards: **{len(cards)}R**',
       f'- preview complete: **{complete_n}R** / course1 kept: **{course1_n}R** / course changed-excluded: **{changed_n}R** / preview incomplete: **{missing_n}R**',
       f'- formal A/S races: **{len(asrows)}R**','',
       '## Aggregate','|層|R|①1着|頭率|平均p109|乖離|7点的中|3連単的中率|頭的中時coverage|投資|払戻|ROI|','|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for lab,rs in [('A+ (>=65%)',aplus),('S (>=72%)',sonly),('A-only (65-72%)',aonly)]:
        n,h,hr,mp,gap,bh,bhr,cov,inv,ret,roi=metric(rs)
        L.append(f'|{lab}|{n}|{h}|{hr:.1f}%|{mp:.1f}%|{gap:+.1f}pt|{bh}|{bhr:.1f}%|{cov:.1f}%|¥{inv:,}|¥{ret:,}|{roi:.1f}%|')
    L+=['','## Formal A/S race detail','|場|R|①|p109|判定|v110 top7|結果|3連単|払戻|7点|','|---|---:|---|---:|---|---|---:|---|---:|---|']
    for r in asrows:
        L.append(f"|{r['venue_name']}|{r['race']}R|{r['boat1_name']}|{100*r['p109']:.1f}%|{r['grade']}|{r['top7'].replace(';',' / ')}|{r['winner']}着頭|{r['actual_combo']}|¥{r['payout100']:,}|{'的中' if r['ticket7_hit'] else '外れ'}|")
    if not asrows:L.append('|-|-|-|-|-|-|-|-|-|-|')
    open(SUMMARY,'w',encoding='utf-8').write('\n'.join(L)+'\n')

if __name__=='__main__':main()
