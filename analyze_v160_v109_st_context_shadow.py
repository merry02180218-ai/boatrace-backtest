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
OUT='analysis_v160_v109_st_context_shadow.csv'
SUMMARY='summary_v160_v109_st_context_shadow.md'
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

def shrink(vals, prior, pseudo=6):
    return (sum(vals)+pseudo*prior)/(len(vals)+pseudo) if vals else prior

def build_context_features():
    # Exact v159-style strictly-prior-day histories. Freeze every boat for the date,
    # then read that date's result and update histories only afterward.
    start=date(2026,5,1); end=date(2026,8,31)
    player=defaultdict(list); pfstate=defaultdict(list); pneigh=defaultdict(list); gh=[]; out={}; d=start
    while d<=end:
        ymd=d.strftime('%Y/%m/%d')
        cards=bycode(rows(f'data/programs/race_cards/{ymd}.csv'))
        stt=bycode(rows(f'data/previews/stt/{ymd}.csv'))
        frozen=[]
        for code,sr in stt.items():
            card=cards.get(code)
            if not card:continue
            em=ex_map(sr); c2b={c:b for b,(c,st) in em.items()}
            for b,(ec,exst) in em.items():
                rid=card.get(f'艇{b}_登録番号','') or card.get(f'艇{b}_選手名','')
                gm=float(np.mean(gh)) if gh else .07
                pvals=player[rid]; pbase=(sum(pvals)+10*gm)/(len(pvals)+10) if pvals else gm
                fs='F' if exst<0 else 'N'
                ib=c2b.get(ec-1); ob=c2b.get(ec+1)
                ist=em.get(ib,(None,None))[1] if ib else None
                ost=em.get(ob,(None,None))[1] if ob else None
                if ist is None or ost is None:nc='EDGE'
                else:
                    a,bn=ist-exst,ost-exst
                    nc='BOTH_SLOWER' if a>=.03 and bn>=.03 else ('BOTH_FASTER' if a<=-.03 and bn<=-.03 else 'MIXED')
                fv=pfstate[(rid,fs)]; nv=pneigh[(rid,nc)]
                fbias=shrink(fv,pbase,6); nbias=shrink(nv,pbase,6)
                if b==1:
                    out[code]={
                      'ctx_player_bias':pbase,
                      'ctx_fstate_bias':fbias,'ctx_fstate_pred_st':exst+fbias,'ctx_fstate_n':len(fv),
                      'ctx_neighbor_bias':nbias,'ctx_neighbor_pred_st':exst+nbias,'ctx_neighbor_n':len(nv),
                      'ctx_ex_f':1.0 if fs=='F' else 0.0,
                      'ctx_neighbor_both_slower':1.0 if nc=='BOTH_SLOWER' else 0.0,
                      'ctx_neighbor_both_faster':1.0 if nc=='BOTH_FASTER' else 0.0,
                      'ctx_neighbor_mixed':1.0 if nc=='MIXED' else 0.0,
                      'ctx_neighbor_edge':1.0 if nc=='EDGE' else 0.0,
                    }
                frozen.append((code,b,rid,ec,exst,fs,nc))
        res=bycode(rows(f'data/results/realtime/{ymd}.csv')); upd=[]
        for code,b,rid,ec,exst,fs,nc in frozen:
            am=actual_map(res.get(code,{}))
            if b in am and am[b][0]==ec:upd.append((rid,fs,nc,am[b][1]-exst))
        for rid,fs,nc,delta in upd:
            player[rid].append(delta);pfstate[(rid,fs)].append(delta);pneigh[(rid,nc)].append(delta);gh.append(delta)
        d+=timedelta(days=1)
    return out

def xm(rs,features):
    a=[]
    for r in rs:
        z=[ff(r.get(k)) for k in features]
        v=str(r.get('venue','')).zfill(2);z += [1.0 if v==q else 0.0 for q in VENUES];a.append(z)
    return np.asarray(a,float)
def fit(tr,fs):
    p=Pipeline([('s',StandardScaler()),('m',LogisticRegression(C=.5,max_iter=1800,solver='lbfgs'))])
    p.fit(xm(tr,fs),[ii(r.get('head_hit')) for r in tr]);return p

def met(test,p):
    y=np.array([ii(r['head_hit']) for r in test]);sel=[(r,q) for r,q in zip(test,p) if q>=S_CUT];h=sum(ii(r['head_hit']) for r,q in sel)
    return len(test),roc_auc_score(y,p),brier_score_loss(y,p),len(sel),pct(h,len(sel)),float(np.mean([q for r,q in sel])*100 if sel else 0)

def main():
    cf=build_context_features();src=[dict(r) for r in read_csv(SRC) if ii(r.get('valid_result'))==1]
    merged=[]
    for r in src:
        q=cf.get(r.get('race_code',''))
        if q:r.update(q);merged.append(r)
    F=['ctx_fstate_bias','ctx_fstate_pred_st','ctx_ex_f','ctx_fstate_n']
    N=['ctx_neighbor_bias','ctx_neighbor_pred_st','ctx_neighbor_n','ctx_neighbor_both_slower','ctx_neighbor_both_faster','ctx_neighbor_mixed','ctx_neighbor_edge']
    variants=[('CURRENT',BASE),('FSTATE',BASE+F),('NEIGHBOR',BASE+N),('FSTATE_NEIGHBOR',BASE+F+N)]
    allout=[];stats=[]
    for mo in MONTHS:
        first=date.fromisoformat(mo+'-01');tr=[r for r in merged if date.fromisoformat(r['date'])<first];te=[r for r in merged if r.get('month')==mo]
        for name,fs in variants:
            model=fit(tr,fs);p=model.predict_proba(xm(te,fs))[:,1];m=met(te,p);stats.append((mo,name,*m))
            for r,q in zip(te,p):
                allout.append({'month':mo,'variant':name,'race_code':r['race_code'],'p':q,'head_hit':r['head_hit'],'fstate_n':r['ctx_fstate_n'],'neighbor_n':r['ctx_neighbor_n']})
    with open(OUT,'w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(allout[0]));w.writeheader();w.writerows(allout)
    L=['# v160 v109 + ST context shadow','',
       '- v159で改善した **選手×展示F/正常** と **選手×隣艇文脈** だけをv109 shadowへ追加。',
       '- 各日の全予測をfreeze後に同日結果で履歴更新。同日リークなし。',
       '- v109本体のBASE特徴、C=.5、S=72%は固定。productionは未変更。',
       '- Jul/Aug strict monthly walk-forward。', '',
       '|月|variant|R|AUC|Brier|S件数|S頭率|S平均p|','|---|---|---:|---:|---:|---:|---:|---:|']
    for mo,nm,n,a,b,sn,shr,smp in stats:L.append(f'|{mo}|{nm}|{n}|{a:.4f}|{b:.5f}|{sn}|{shr:.2f}%|{smp:.2f}%|')
    L+=['','## aggregate Jul-Aug','|variant|R|AUC|Brier|S件数|S頭率|S平均p|','|---|---:|---:|---:|---:|---:|---:|']
    agg={}
    for nm,fs in variants:
        rr=[r for r in allout if r['variant']==nm];y=np.array([ii(r['head_hit']) for r in rr]);p=np.array([ff(r['p']) for r in rr]);sel=[r for r in rr if ff(r['p'])>=S_CUT];h=sum(ii(r['head_hit']) for r in sel)
        vals=(len(rr),roc_auc_score(y,p),brier_score_loss(y,p),len(sel),pct(h,len(sel)),np.mean([ff(r['p']) for r in sel])*100 if sel else 0)
        agg[nm]=vals;L.append(f'|{nm}|{vals[0]}|{vals[1]:.4f}|{vals[2]:.5f}|{vals[3]}|{vals[4]:.2f}%|{vals[5]:.2f}%|')
    cur=agg['CURRENT']
    L+=['','## CURRENT比','|variant|ΔAUC|ΔBrier|ΔS頭率|ΔS件数|','|---|---:|---:|---:|---:|']
    for nm in ('FSTATE','NEIGHBOR','FSTATE_NEIGHBOR'):
        v=agg[nm];L.append(f'|{nm}|{v[1]-cur[1]:+.4f}|{v[2]-cur[2]:+.5f}|{v[4]-cur[4]:+.2f}pt|{v[3]-cur[3]:+d}|')
    L+=['','## 判定ルール',
        '- production採用候補は **CURRENTよりAUC上昇・Brier低下・S頭率上昇を同時に満たす** こと。',
        '- さらにJul/Augの両月でS頭率の改善方向が崩れないこと。',
        '- 条件を満たさなければv109は現状維持し、context STは補助情報に留める。']
    open(SUMMARY,'w',encoding='utf-8').write('\n'.join(L)+'\n');print('\n'.join(L))
if __name__=='__main__':main()
