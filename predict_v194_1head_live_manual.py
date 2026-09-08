#!/usr/bin/env python3
from __future__ import annotations
import csv,json
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import date,timedelta
from pathlib import Path
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from backtest import rows
from analyze_v108_1head_feasibility import feature_row,bycode,st_bias,update_st
from analyze_v162_1head_pair_direct import fit_pair,pair_order

ROOT=Path(__file__).resolve().parent
INPUT=ROOT/'live_input_1head.json'; SRC=ROOT/'analysis_v108_1head_feasibility.csv'
OUT=ROOT/'prediction_v194_1head_live_manual.json'; SUMMARY=ROOT/'summary_v194_1head_live_manual.md'
NUM_FEATURES=['one_grade','one_wr','one_local','one_motor','one_waku_wr','one_nst_strength','one_waku_sr_strength','one_past_win','one_meet_st_strength','one_ex','one_st','one_lap','one_turn','one_straight','one_orig_avg','one_direct','one_score','threat2','threat3','threat4','threat5','threat6','threat23_max','threat_all_max','margin2','margin3','margin23','margin_all','st_margin2','st_margin3','st_margin23','ex_margin23','turn_margin23','straight_margin23']
VENUES=[f'{i:02d}' for i in range(1,25)]; S_CUT=.72

def ff(x,d=0.0):
    try:return float(x)
    except:return d

def ii(x,d=0):
    try:return int(float(x))
    except:return d

def read_csv(p):
    with open(p,encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def xmatrix(rs):
    out=[]
    for r in rs:
        z=[ff(r.get(k),0) for k in NUM_FEATURES]; vv=str(r.get('venue','')).zfill(2)
        z.extend(1.0 if vv==v else 0.0 for v in VENUES); out.append(z)
    return np.asarray(out,float)
def fit_head(train):
    m=Pipeline([('scale',StandardScaler()),('lr',LogisticRegression(C=.5,max_iter=1500,solver='lbfgs'))])
    m.fit(xmatrix(train),[ii(r.get('head_hit')) for r in train]);return m

def exact_prior_bias(hd):
    ds=[];d=date(2025,10,1)
    while d<hd:ds.append(d);d+=timedelta(days=1)
    got={}
    def one(dd):return dd,rows(f"data/previews/stt/{dd.strftime('%Y/%m/%d')}.csv")
    with ThreadPoolExecutor(max_workers=14) as ex:
        fs=[ex.submit(one,d) for d in ds]
        for f in as_completed(fs):
            try:dd,z=f.result();got[dd]=z
            except:pass
    sums=defaultdict(list);allv=[]
    for d in sorted(got):update_st(got[d],sums,allv)
    return st_bias(sums,allv),len(got)
def manual_maps(code,j):
    ex,st,lap,turn,straight=j['exhibition'],j['st'],j['lap'],j['turn'],j['straight']; courses=j.get('courses',[1,2,3,4,5,6])
    tk={code:{f'艇{b}_展示タイム':ex[b-1] for b in range(1,7)}}
    sr={f'艇{b}_スタート展示':st[b-1] for b in range(1,7)}; sr.update({f'艇{b}_コース':courses[b-1] for b in range(1,7)})
    o={'計測項目1':'一周','計測項目2':'まわり足','計測項目3':'直線'}
    for b in range(1,7):o[f'艇{b}_値1']=lap[b-1];o[f'艇{b}_値2']=turn[b-1];o[f'艇{b}_値3']=straight[b-1]
    return tk,{code:sr},{code:o}

def main():
    j=json.loads(INPUT.read_text());hd=date.fromisoformat(j['date']);venue=str(j['venue']).zfill(2);rno=int(j['race']);code=f"{hd:%Y%m%d}{venue}{rno:02d}"; y=hd.strftime('%Y/%m/%d')
    cards=bycode(rows(f'data/programs/race_cards/{y}.csv'));waku=bycode(rows(f'data/programs/waku10/{y}.csv'))
    if code not in cards or code not in waku:raise RuntimeError('card/waku missing')
    if int(j.get('courses',[1])[0])!=1:raise RuntimeError('boat1 not course1')
    bias,bias_days=exact_prior_bias(hd);tk,stt,orig=manual_maps(code,j);row=feature_row(hd.isoformat(),cards[code],waku[code],tk,stt,orig,bias)
    if row is None:raise RuntimeError('entry changed/excluded')
    src=read_csv(SRC);train=[r for r in src if ii(r.get('valid_result'))==1 and r.get('date','')<hd.isoformat()]
    hm=fit_head(train);p=float(hm.predict_proba(xmatrix([row]))[0,1]);decision='BUY' if p>=S_CUT else 'SKIP'
    pm,pair_n=fit_pair(train);top7=pair_order(row,pm,1.0)[:7] if decision=='BUY' else []
    res={'date':hd.isoformat(),'venue':venue,'race':rno,'race_code':code,'boat1':cards[code].get('艇1_選手名',''),'p109':p,'grade':'S' if p>=.72 else ('A' if p>=.65 else 'B'),'decision':decision,'v162_lambda':1.0,'top7':top7,'head_train_rows':len(train),'pair_train_headwins':pair_n,'prior_st_bias_days':bias_days,'manual_input':j}
    OUT.write_text(json.dumps(res,ensure_ascii=False,indent=2));L=[f"# v194 live 1-head {hd} {venue} {rno}R",'',f"- boat1: **{res['boat1']}**",f"- v109 p1head: **{100*p:.2f}%**",f"- grade: **{res['grade']}**",f"- decision: **{decision}** (S-only cut 72%)",f"- v162 lambda: **1.00**",'','## Top7']
    L += [f"{i}. {t}" for i,t in enumerate(top7,1)] if top7 else ['- SKIP: no tickets']
    SUMMARY.write_text('\n'.join(L)+'\n');print('\n'.join(L))
if __name__=='__main__':main()
