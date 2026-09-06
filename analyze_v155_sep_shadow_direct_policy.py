from __future__ import annotations
import csv
from datetime import date, timedelta
from collections import defaultdict
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score, brier_score_loss

from backtest import rows, race_features, grade_score, clamp, pct_motor
from backtest_v51_lane_corrected_tickets import corrected_direct, opp_place_score, ff, ii

# v155 shadow validation of the v154 policy on the next unseen calendar slice.
# Design fixed from v154 only: reduce explicit exhibition ST/time emphasis, retain
# historical/meet ST, straight/lap and especially opponent-threat structure.
TRAIN_END=date(2026,8,31)
TEST_START=date(2026,9,1)
TEST_END=date(2026,9,5)
S_CUT=.72
VENUES=[f'{i:02d}' for i in range(1,25)]
BASE_SRC='analysis_v108_1head_feasibility.csv'
OUT='analysis_v155_sep_shadow_direct_policy.csv'
SUMMARY='summary_v155_sep_shadow_direct_policy.md'

CURRENT=[
 'one_grade','one_wr','one_local','one_motor','one_waku_wr','one_nst_strength',
 'one_waku_sr_strength','one_past_win','one_meet_st_strength',
 'one_ex','one_st','one_lap','one_turn','one_straight','one_orig_avg','one_direct','one_score',
 'threat2','threat3','threat4','threat5','threat6','threat23_max','threat_all_max',
 'margin2','margin3','margin23','margin_all','st_margin2','st_margin3','st_margin23',
 'ex_margin23','turn_margin23','straight_margin23']
# Fixed shadow candidate after v154: remove only explicit exhibition ST/time fields.
# ST still can enter opponent/direct composites, so this is a conservative de-emphasis,
# not a retrofitted zero-ST model.
SHADOW=[x for x in CURRENT if x not in {'one_ex','ex_margin23','one_st','st_margin2','st_margin3','st_margin23'}]

def bycode(rs): return {r.get('レースコード',''):r for r in rs if r.get('レースコード')}
def pct(n,d): return 100*n/d if d else 0.0

def st_bias_from_history():
    sums=defaultdict(list);allv=[]
    d=date(2026,8,1)
    while d<=TRAIN_END:
        for r in rows(f"data/previews/stt/{d.strftime('%Y/%m/%d')}.csv"):
            for b in range(1,7):
                v=ff(r.get(f'艇{b}_スタート展示'))
                if v is not None and -.30<v<1.0:
                    sums[b].append(v);allv.append(v)
        d+=timedelta(days=1)
    g=np.mean(allv) if allv else .15
    return {b:(np.mean(sums[b])-g if sums[b] else 0.0) for b in range(1,7)}

def feature_row(ds,card,w,tkz,stt,orig,bias):
    code=card.get('レースコード','')
    if not code:return None
    x=race_features(card,w)
    ex,st,os=corrected_direct(code,tkz,stt,orig,bias)
    for b in range(1,7):
        ex.setdefault(b,.5);st.setdefault(b,.5)
        os.setdefault(b,{'lap':.5,'turn':.5,'straight':.5,'avg':.5})
        for k in ('lap','turn','straight','avg'):os[b].setdefault(k,.5)
    sr=stt.get(code,{})
    course=ii(sr.get('艇1_コース'),0)
    if course in range(2,7):return None
    scores={b:opp_place_score(x,b,ex,st,os) for b in range(1,7)}
    z=x[1]
    motor=.62*pct_motor(z['motor2'])+.38*pct_motor(z['motor3'])
    nst=clamp((.24-z['nst'])/.14);wsr=clamp((6-z['waku_sr'])/5)
    meet=.5 if z['meet_st'] is None else clamp((.22-z['meet_st'])/.12)
    direct=.35*ex[1]+.20*st[1]+.25*os[1]['turn']+.20*os[1]['avg']
    t23=max(scores[2],scores[3]);tall=max(scores[b] for b in range(2,7))
    return {
      'date':ds,'month':ds[:7],'race_code':code,'venue':str(card.get('レース場コード','')).zfill(2),
      'one_grade':grade_score(z['grade']),'one_wr':clamp((z['wr']-3)/5),'one_local':clamp((z['local']-2.5)/5.5),
      'one_motor':motor,'one_waku_wr':clamp(z['waku_wr']/8),'one_nst_strength':nst,'one_waku_sr_strength':wsr,
      'one_past_win':z['past_win'],'one_meet_st_strength':meet,'one_ex':ex[1],'one_st':st[1],
      'one_lap':os[1]['lap'],'one_turn':os[1]['turn'],'one_straight':os[1]['straight'],'one_orig_avg':os[1]['avg'],
      'one_direct':direct,'one_score':scores[1],'threat2':scores[2],'threat3':scores[3],'threat4':scores[4],
      'threat5':scores[5],'threat6':scores[6],'threat23_max':t23,'threat_all_max':tall,
      'margin2':scores[1]-scores[2],'margin3':scores[1]-scores[3],'margin23':scores[1]-t23,'margin_all':scores[1]-tall,
      'st_margin2':st[1]-st[2],'st_margin3':st[1]-st[3],'st_margin23':st[1]-max(st[2],st[3]),
      'ex_margin23':ex[1]-max(ex[2],ex[3]),'turn_margin23':os[1]['turn']-max(os[2]['turn'],os[3]['turn']),
      'straight_margin23':os[1]['straight']-max(os[2]['straight'],os[3]['straight'])}

def fetch_test():
    bias=st_bias_from_history();out=[];d=TEST_START
    while d<=TEST_END:
        ymd=d.strftime('%Y/%m/%d')
        cards=rows(f'data/programs/race_cards/{ymd}.csv');wm=bycode(rows(f'data/programs/waku10/{ymd}.csv'))
        tm=bycode(rows(f'data/previews/tkz/{ymd}.csv'));sm=bycode(rows(f'data/previews/stt/{ymd}.csv'));om=bycode(rows(f'data/previews/original_exhibition/{ymd}.csv'))
        for c in cards:
            code=c.get('レースコード','')
            if code and code in wm:
                try:r=feature_row(str(d),c,wm[code],tm,sm,om,bias)
                except Exception:r=None
                if r:out.append(r)
        d+=timedelta(days=1)
    return out

def settle(test):
    d=TEST_START;rm={}
    while d<=TEST_END:
        for r in rows(f"data/results/realtime/{d.strftime('%Y/%m/%d')}.csv"):
            if r.get('レースコード'):rm[r['レースコード']]=r
        d+=timedelta(days=1)
    q=[]
    for r in test:
        z=dict(r);w=ii(rm.get(r['race_code'],{}).get('1着_艇番'));z['valid_result']=int(w in range(1,7));z['head_hit']=int(w==1);q.append(z)
    return [r for r in q if r['valid_result']]

def read_train():
    with open(BASE_SRC,encoding='utf-8-sig',newline='') as f:
        return [r for r in csv.DictReader(f) if ii(r.get('valid_result'))==1 and date.fromisoformat(r['date'])<=TRAIN_END]
def xm(rs,fs):
    a=[]
    for r in rs:
        z=[float(r.get(k,0) or 0) for k in fs];v=str(r.get('venue','')).zfill(2);z += [1.0 if v==q else 0.0 for q in VENUES];a.append(z)
    return np.asarray(a,float)
def fit(tr,fs):
    p=Pipeline([('s',StandardScaler()),('m',LogisticRegression(C=.5,max_iter=1800,solver='lbfgs'))]);p.fit(xm(tr,fs),[ii(r.get('head_hit')) for r in tr]);return p

def metrics(test,p):
    y=np.asarray([ii(r['head_hit']) for r in test]);sel=[(r,q) for r,q in zip(test,p) if q>=S_CUT];h=sum(ii(r['head_hit']) for r,q in sel)
    auc=roc_auc_score(y,p) if len(set(y))>1 else float('nan');br=brier_score_loss(y,p)
    return len(test),auc,br,len(sel),pct(h,len(sel)),float(np.mean([q for r,q in sel])*100 if sel else 0)
def main():
    tr=read_train();test=settle(fetch_test());rowsout=[];res={}
    for name,fs in [('CURRENT',CURRENT),('SHADOW_DROP_EX_ST',SHADOW)]:
        p=fit(tr,fs).predict_proba(xm(test,fs))[:,1];res[name]=metrics(test,p)
        for r,q in zip(test,p):rowsout.append({'variant':name,'date':r['date'],'race_code':r['race_code'],'p':q,'head_hit':r['head_hit']})
    c=res['CURRENT'];s=res['SHADOW_DROP_EX_ST']
    L=['# v155 Sep1-5 shadow validation','',
       '- v154で決めた方針を数値再調整せず、次のカレンダー区間 2026-09-01..05 に適用。','- 学習は2026-08-31まで。対象レースの結果はfeature生成後にsettlement。','- CURRENT=v109全特徴。SHADOWは明示的な展示タイム/展示STとそのmarginだけを除去。','- S=72%固定。','',
       '|variant|R|AUC|Brier|S件数|S頭率|S平均p|','|---|---:|---:|---:|---:|---:|---:|',
       f'|CURRENT|{c[0]}|{c[1]:.4f}|{c[2]:.5f}|{c[3]}|{c[4]:.2f}%|{c[5]:.2f}%|',
       f'|SHADOW_DROP_EX_ST|{s[0]}|{s[1]:.4f}|{s[2]:.5f}|{s[3]}|{s[4]:.2f}%|{s[5]:.2f}%|','',
       f'- ΔAUC {s[1]-c[1]:+.4f} / ΔBrier {s[2]-c[2]:+.5f} / ΔS頭率 {s[4]-c[4]:+.2f}pt / ΔS件数 {s[3]-c[3]:+d}R',
       '- 5日間だけなのでproduction切替には不足。方向確認用shadow。']
    with open(OUT,'w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['variant','date','race_code','p','head_hit']);w.writeheader();w.writerows(rowsout)
    open(SUMMARY,'w',encoding='utf-8').write('\n'.join(L)+'\n');print('\n'.join(L))
if __name__=='__main__':main()
