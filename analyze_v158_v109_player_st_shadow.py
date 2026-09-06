from __future__ import annotations
import csv
from collections import defaultdict
from datetime import date, timedelta
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score,brier_score_loss
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from backtest import rows

SRC='analysis_v108_1head_feasibility.csv'
OUT='analysis_v158_v109_player_st_shadow.csv'
SUMMARY='summary_v158_v109_player_st_shadow.md'
S_CUT=.72
MONTHS=['2026-07','2026-08']
VENUES=[f'{i:02d}' for i in range(1,25)]
BASE=[
 'one_grade','one_wr','one_local','one_motor','one_waku_wr','one_nst_strength',
 'one_waku_sr_strength','one_past_win','one_meet_st_strength',
 'one_ex','one_st','one_lap','one_turn','one_straight','one_orig_avg','one_direct','one_score',
 'threat2','threat3','threat4','threat5','threat6','threat23_max','threat_all_max',
 'margin2','margin3','margin23','margin_all','st_margin2','st_margin3','st_margin23',
 'ex_margin23','turn_margin23','straight_margin23']

def ff(x,d=0.0):
    try:return float(x)
    except:return d

def ii(x,d=0):
    try:return int(float(x))
    except:return d

def pct(n,d):return 100*n/d if d else 0.0

def read_csv(path):
    with open(path,encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def bycode(rs):return {r.get('レースコード',''):r for r in rs if r.get('レースコード')}

def actual_map(rr):
    z={}
    for c in range(1,7):
        b=ii(rr.get(f'{c}コース_艇番')); st=ff(rr.get(f'{c}コース_スタートタイミング'),999)
        if b in range(1,7) and st<2:z[b]=(c,st)
    return z

def ex_map(sr):
    z={}
    for b in range(1,7):
        c=ii(sr.get(f'艇{b}_コース')); st=ff(sr.get(f'艇{b}_スタート展示'),999)
        if c in range(1,7) and st<2:z[b]=(c,st)
    return z

def build_player_features():
    # Build strictly prior-day player exhibition->actual bias and predicted actual ST.
    start=date(2026,5,1); end=date(2026,8,31); hist=defaultdict(list); gh=[]; out={}; d=start
    while d<=end:
        ymd=d.strftime('%Y/%m/%d'); cards=bycode(rows(f'data/programs/race_cards/{ymd}.csv')); stt=bycode(rows(f'data/previews/stt/{ymd}.csv'))
        frozen=[]
        for code,sr in stt.items():
            card=cards.get(code)
            if not card:continue
            em=ex_map(sr)
            if 1 not in em:continue
            ec,exst=em[1]
            rid=card.get('艇1_登録番号','') or card.get('艇1_選手名','')
            gm=float(np.mean(gh)) if gh else .07; ph=hist[rid]; bias=(sum(ph)+10*gm)/(len(ph)+10)
            out[code]={'player_pred_actual_st':exst+bias,'player_st_bias':bias,'player_st_hist_n':len(ph),'global_st_bias':gm}
            for b,(c,s) in em.items():
                rrid=card.get(f'艇{b}_登録番号','') or card.get(f'艇{b}_選手名','')
                frozen.append((code,b,c,s,rrid))
        # results only after day's feature freeze
        res=bycode(rows(f'data/results/realtime/{ymd}.csv')); updates=[]
        for code,b,ec,exst,rid in frozen:
            am=actual_map(res.get(code,{}))
            if b in am and am[b][0]==ec:updates.append((rid,am[b][1]-exst))
        for rid,delta in updates:hist[rid].append(delta);gh.append(delta)
        d+=timedelta(days=1)
    return out

def xm(rs,features):
    a=[]
    for r in rs:
        z=[ff(r.get(k)) for k in features];v=str(r.get('venue','')).zfill(2);z += [1.0 if v==q else 0.0 for q in VENUES];a.append(z)
    return np.asarray(a,float)
def fit(tr,fs):
    p=Pipeline([('s',StandardScaler()),('m',LogisticRegression(C=.5,max_iter=1800,solver='lbfgs'))]);p.fit(xm(tr,fs),[ii(r.get('head_hit')) for r in tr]);return p

def met(test,p):
    y=np.array([ii(r['head_hit']) for r in test]);sel=[(r,q) for r,q in zip(test,p) if q>=S_CUT];h=sum(ii(r['head_hit']) for r,q in sel)
    return len(test),roc_auc_score(y,p),brier_score_loss(y,p),len(sel),pct(h,len(sel)),float(np.mean([q for r,q in sel])*100 if sel else 0)

def main():
    pf=build_player_features();src=[dict(r) for r in read_csv(SRC) if ii(r.get('valid_result'))==1]
    merged=[]
    for r in src:
        q=pf.get(r.get('race_code',''))
        if q:
            r.update(q);merged.append(r)
    variants=[('CURRENT',BASE),('PLAYER_PRED',BASE+['player_pred_actual_st']),('PLAYER_BIAS',BASE+['player_st_bias']),('PLAYER_BOTH',BASE+['player_pred_actual_st','player_st_bias'])]
    allout=[]; stats=[]
    for mo in MONTHS:
        first=date.fromisoformat(mo+'-01');tr=[r for r in merged if date.fromisoformat(r['date'])<first];te=[r for r in merged if r.get('month')==mo]
        for name,fs in variants:
            model=fit(tr,fs);p=model.predict_proba(xm(te,fs))[:,1];m=met(te,p);stats.append((mo,name,*m))
            for r,q in zip(te,p):allout.append({'month':mo,'variant':name,'race_code':r['race_code'],'p':q,'head_hit':r['head_hit'],'hist_n':r['player_st_hist_n'],'player_st_bias':r['player_st_bias'],'player_pred_actual_st':r['player_pred_actual_st']})
    with open(OUT,'w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(allout[0]));w.writeheader();w.writerows(allout)
    L=['# v158 v109 + player-corrected ST shadow','',
       '- v157で固定した「過去日だけの選手展示→本番ST bias」をv109へshadow追加。','- 同日結果は特徴生成後にのみ履歴更新。対象レースの結果は予測特徴に不使用。','- v109本体の特徴・C=.5・S=72%は固定。追加特徴の有無だけ比較。','- Jul/Augは各月strict monthly walk-forward。productionは未変更。','',
       '|月|variant|R|AUC|Brier|S件数|S頭率|S平均p|','|---|---|---:|---:|---:|---:|---:|---:|']
    for mo,nm,n,a,b,sn,shr,smp in stats:L.append(f'|{mo}|{nm}|{n}|{a:.4f}|{b:.5f}|{sn}|{shr:.2f}%|{smp:.2f}%|')
    L+=['','## aggregate Jul-Aug','|variant|R|AUC|Brier|S件数|S頭率|S平均p|','|---|---:|---:|---:|---:|---:|---:|']
    for nm,fs in variants:
        rr=[r for r in allout if r['variant']==nm]; y=np.array([ii(r['head_hit']) for r in rr]);p=np.array([ff(r['p']) for r in rr]);sel=[r for r in rr if ff(r['p'])>=S_CUT];h=sum(ii(r['head_hit']) for r in sel)
        L.append(f'|{nm}|{len(rr)}|{roc_auc_score(y,p):.4f}|{brier_score_loss(y,p):.5f}|{len(sel)}|{pct(h,len(sel)):.2f}%|{np.mean([ff(r["p"]) for r in sel])*100:.2f}%|')
    L += ['','## 判定','- PLAYER系がCURRENTよりAUC/BrierとS頭率の両方で改善し、Jul/Aug両月で方向が崩れない場合のみ次段階へ。','- 改善が小さい/不安定なら現行v109を維持し、選手補正STは説明用・補助用に留める。']
    open(SUMMARY,'w',encoding='utf-8').write('\n'.join(L)+'\n');print('\n'.join(L))
if __name__=='__main__':main()
