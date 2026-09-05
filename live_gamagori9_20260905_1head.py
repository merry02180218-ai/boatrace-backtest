"""One-off no-leak live judgment for 2026-09-05 Gamagori 9R.
Uses user-provided pre-race exhibition/ST/original-exhibition only.
No result, payout, or odds files are read.
"""
from datetime import date
import math
import numpy as np
from predict_v116_20260905_1head_live import read_csv, fit_model, pred, grade, exact_prior_st_bias
from analyze_v108_1head_feasibility import feature_row, bycode
from analyze_v110b_1head_role_tickets import fit_roles, second_vec, third_vec, rankof, zmap
from backtest import rows

HD=date(2026,9,5); DS='2026-09-05'; Y='2026/09/05'; CODE='202609050709'
SRC='analysis_v108_1head_feasibility.csv'
OUT='live_gamagori9_20260905_1head.md'

# Screenshot values frozen before race result.
EX=[6.78,6.83,6.86,6.81,6.68,6.78]
ST=[.01,-.15,-.08,.27,.08,.13]
LAP=[36.96,37.66,37.88,37.67,37.22,37.48]
TURN=[4.92,5.03,5.10,5.12,5.25,4.97]
STRAIGHT=[6.32,6.35,6.54,6.58,6.45,6.35]

def main():
    src=read_csv(SRC)
    train=[r for r in src if int(float(r.get('valid_result') or 0))==1 and r.get('date','')<DS]
    model=fit_model(train)
    bias,days=exact_prior_st_bias()
    cards=bycode(rows(f'data/programs/race_cards/{Y}.csv'))
    waku=bycode(rows(f'data/programs/waku10/{Y}.csv'))
    card=cards[CODE]; w=waku[CODE]
    tkz={CODE:{**{f'艇{i+1}_展示タイム':EX[i] for i in range(6)}}}
    strow={f'艇{i+1}_スタート展示':ST[i] for i in range(6)}; strow['艇1_コース']=1
    stt={CODE:strow}
    orow={'計測項目1':'一周','計測項目2':'まわり足','計測項目3':'直線'}
    for i in range(6):
        orow[f'艇{i+1}_値1']=LAP[i]; orow[f'艇{i+1}_値2']=TURN[i]; orow[f'艇{i+1}_値3']=STRAIGHT[i]
    orig={CODE:orow}
    r=feature_row(DS,card,w,tkz,stt,orig,bias)
    p=pred(model,r); g=grade(p)

    role_train=[x for x in src if x.get('date','')<DS]
    m2,m3,ntrain=fit_roles(role_train)
    sec={b:float(m2.predict_proba(np.asarray([second_vec(r,b)],dtype=float))[0,1]) for b in range(2,7)}
    ssum=sum(sec.values()) or 1.0
    p2={b:max(sec[b]/ssum,1e-12) for b in range(2,7)}
    pairs_role={}; pairs_cur={}
    for s in range(2,7):
        rem=[t for t in range(2,7) if t!=s]
        vals={t:float(m3.predict_proba(np.asarray([third_vec(r,s,t)],dtype=float))[0,1]) for t in rem}
        den=sum(vals.values()) or 1.0
        for t in rem:
            pairs_role[(s,t)]=math.log(p2[s])+math.log(max(vals[t]/den,1e-12))
            pairs_cur[(s,t)]=-(rankof(r,s)+.7*rankof(r,t))
    rz=zmap(pairs_role); cz=zmap(pairs_cur); lam=.50
    arr=sorted(pairs_cur,key=lambda k:(-((1-lam)*cz[k]+lam*rz[k]),k[0],k[1]))
    order=[f'1-{s}-{t}' for s,t in arr]
    top7=order[:7]
    L=['# 2026-09-05 蒲郡9R 1号艇 live','',
       '- No result / payout / odds read.',f'- prior ST-bias days: {days}',f'- role train head-win rows: {ntrain}',
       f'- p109: **{100*p:.1f}%**',f'- grade: **{g}**',f'- BUY(S-only operation): **{"BUY" if g=="S" else "SKIP"}**','',
       '## v110 top7']
    for i,t in enumerate(top7,1):L.append(f'{i}. **{t}**')
    open(OUT,'w',encoding='utf-8').write('\n'.join(L)+'\n')
    print('\n'.join(L))
if __name__=='__main__':main()
