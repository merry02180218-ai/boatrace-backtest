"""v109: 1号艇頭モデルのstrict monthly walk-forward operational check.

Source is v108's already no-leak frozen/settled feature table.
Architecture BASE+VENUE and probability cuts A=.65/S=.72 were fixed by v108 before
this v109 holdout replay. For each Jun/Jul/Aug month, fit only on strictly earlier dates.
No current/final odds are used. Payout is settlement-only for equal-stake ticket ROI.
"""
from __future__ import annotations
import csv
from datetime import date

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score,brier_score_loss
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

SRC='analysis_v108_1head_feasibility.csv'
OUT='analysis_v109_1head_monthly_walkforward.csv'
SUMMARY='summary_v109_1head_monthly_walkforward.md'
A_CUT=.65
S_CUT=.72
MONTHS=['2026-06','2026-07','2026-08']
POINTS=[1,2,3,4,5,6,7,8,10,12,15,20]
VENUES=[f'{i:02d}' for i in range(1,25)]
NUM_FEATURES=[
 'one_grade','one_wr','one_local','one_motor','one_waku_wr','one_nst_strength',
 'one_waku_sr_strength','one_past_win','one_meet_st_strength',
 'one_ex','one_st','one_lap','one_turn','one_straight','one_orig_avg','one_direct','one_score',
 'threat2','threat3','threat4','threat5','threat6','threat23_max','threat_all_max',
 'margin2','margin3','margin23','margin_all','st_margin2','st_margin3','st_margin23',
 'ex_margin23','turn_margin23','straight_margin23'
]

def ii(x,d=0):
    try:return int(float(x))
    except Exception:return d

def ff(x,d=0.0):
    try:return float(x)
    except Exception:return d

def pct(n,d):return 100*n/d if d else 0.0

def read_csv(path):
    with open(path,encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def xmatrix(rs):
    out=[]
    for r in rs:
        row=[ff(r.get(k),0) for k in NUM_FEATURES]
        vv=str(r.get('venue','')).zfill(2)
        row.extend(1.0 if vv==v else 0.0 for v in VENUES)
        out.append(row)
    return np.asarray(out,dtype=float)

def fit(train):
    p=Pipeline([('scale',StandardScaler()),('lr',LogisticRegression(C=.5,max_iter=1500,solver='lbfgs'))])
    p.fit(xmatrix(train),[ii(r.get('head_hit')) for r in train])
    return p

def auc(y,p):
    try:return roc_auc_score(y,p) if len(set(y))>1 else float('nan')
    except Exception:return float('nan')

def metrics(rs,cut):
    q=[r for r in rs if ff(r.get('p109'))>=cut]
    n=len(q);h=sum(ii(r.get('head_hit')) for r in q);e=sum(ii(r.get('escape_hit')) for r in q)
    mp=sum(ff(r.get('p109')) for r in q)/n if n else 0
    return q,n,h,pct(h,n),e,pct(e,n),mp*100

def point_metric(rs,npt):
    q=[r for r in rs if ii(r.get('valid_payout'))==1]
    hits=[r for r in q if 0<ii(r.get('actual_ticket_rank20'))<=npt]
    heads=[r for r in q if ii(r.get('head_hit'))==1]
    cov=sum(1 for r in heads if 0<ii(r.get('actual_ticket_rank20'))<=npt)
    inv=len(q)*npt*100
    ret=sum(ii(r.get('payout100')) for r in hits)
    return len(q),len(hits),pct(len(hits),len(q)),pct(cov,len(heads)),pct(ret,inv)

def write_csv(path,rs):
    fs=sorted(set().union(*(r.keys() for r in rs)))
    with open(path,'w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fs);w.writeheader();w.writerows(rs)

def main():
    src=[r for r in read_csv(SRC) if ii(r.get('valid_result'))==1]
    out=[];model_stats=[]
    for mo in MONTHS:
        first=date.fromisoformat(mo+'-01')
        train=[r for r in src if date.fromisoformat(r['date'])<first]
        test=[dict(r) for r in src if r.get('month')==mo]
        model=fit(train);pp=model.predict_proba(xmatrix(test))[:,1]
        for r,p in zip(test,pp):
            r['p109']=round(float(p),8);r['wf_month']=mo;r['train_n109']=len(train)
        y=[ii(r.get('head_hit')) for r in test]
        model_stats.append((mo,len(train),len(test),auc(y,pp),brier_score_loss(y,pp),sum(pp)/len(pp),pct(sum(y),len(y))))
        out.extend(test)
    write_csv(OUT,out)

    all_a=[];all_s=[]
    L=['# v109 1号艇 strict monthly walk-forward','',
       'v108でvalidation選択した **BASE+VENUE** を固定。A=65% / S=72%も固定。',
       'Jun/Jul/Aug各月について、対象月より前の日付だけで毎月refitしてからその月を予測。current/final oddsは不使用。','',
       '## 月次モデル品質','|月|学習R|評価R|AUC|Brier|平均予測p|実1頭率|','|---|---:|---:|---:|---:|---:|---:|']
    for mo,trn,n,a,b,mp,hr in model_stats:
        L.append(f'|{mo}|{trn:,}|{n:,}|{a:.3f}|{b:.4f}|{mp*100:.1f}%|{hr:.1f}%|')

    L+=['','## A/S 月別安定性','|月|層|R|1着|頭率|平均予測p|乖離(実績-p)|逃げ率|','|---|---|---:|---:|---:|---:|---:|---:|']
    monthly_pass=True
    for mo in MONTHS:
        q=[r for r in out if r['wf_month']==mo]
        for lab,cut in [('A',A_CUT),('S',S_CUT)]:
            sel,n,h,hr,e,er,mp=metrics(q,cut)
            L.append(f'|{mo}|{lab}|{n:,}|{h}|{hr:.1f}%|{mp:.1f}%|{hr-mp:+.1f}pt|{er:.1f}%|')
            if lab=='A':
                all_a.extend(sel);monthly_pass &= (n>=500 and hr>=68.0)
            else:
                all_s.extend(sel);monthly_pass &= (n>=300 and hr>=72.0)

    def agg(q):
        n=len(q);h=sum(ii(r.get('head_hit')) for r in q);e=sum(ii(r.get('escape_hit')) for r in q);mp=sum(ff(r.get('p109')) for r in q)/n*100 if n else 0
        return n,h,pct(h,n),e,pct(e,n),mp
    an,ah,ar,ae,aer,amp=agg(all_a);sn,sh,sr,se,ser,smp=agg(all_s)
    agg_pass=(an>=3000 and ar>=70.0 and sn>=1800 and sr>=74.0)
    operational=monthly_pass and agg_pass
    L+=['','## Jun-Aug aggregate','|層|R|1着|頭率|平均予測p|乖離|逃げ率|','|---|---:|---:|---:|---:|---:|---:|',
        f'|A|{an:,}|{ah}|{ar:.1f}%|{amp:.1f}%|{ar-amp:+.1f}pt|{aer:.1f}%|',
        f'|S|{sn:,}|{sh}|{sr:.1f}%|{smp:.1f}%|{sr-smp:+.1f}pt|{ser:.1f}%|']

    L+=['','## 相手v51順位・点数別（monthly WF A/S）','|層|点数|3連単的中率|頭的中時coverage|均等買いROI|','|---|---:|---:|---:|---:|']
    for lab,q in [('A',all_a),('S',all_s)]:
        for p in POINTS:
            _,_,hr,cov,roi=point_metric(q,p)
            L.append(f'|{lab}|{p}|{hr:.1f}%|{cov:.1f}%|{roi:.1f}%|')

    L+=['','## v109 operational-head判定',
        '- 月別条件: A 各月500R以上・68%以上 / S 各月300R以上・72%以上。',
        '- 集計条件: A 3000R以上・70%以上 / S 1800R以上・74%以上。',
        f'- 月別 stability: **{"PASS" if monthly_pass else "FAIL"}**',
        f'- aggregate: **{"PASS" if agg_pass else "FAIL"}**',
        f'- **V109 OPERATIONAL-HEAD = {"PASS" if operational else "FAIL"}**',
        '- PASSは「1号艇を頭に選ぶ層」の運用候補判定。3連単の買い目・資金配分のproduction採用は別判定。',
        '- 均等買いROIが100%未満なら、頭モデルが良くても買い目側はそのまま本番採用しない。']
    open(SUMMARY,'w',encoding='utf-8').write('\n'.join(L)+'\n')

if __name__=='__main__':main()
