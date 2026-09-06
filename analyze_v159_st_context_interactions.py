from __future__ import annotations
import csv
from collections import defaultdict
from datetime import date, timedelta
import numpy as np
from sklearn.metrics import mean_absolute_error
from backtest import rows

START=date(2026,5,1); END=date(2026,9,5); TEST_START=date(2026,7,1)
OUT='analysis_v159_st_context_interactions.csv'; SUMMARY='summary_v159_st_context_interactions.md'

def ff(x):
    try:return float(x)
    except:return None

def ii(x):
    try:return int(float(x))
    except:return None

def bycode(rs):return {r.get('レースコード',''):r for r in rs if r.get('レースコード')}

def actual_map(rr):
    out={}
    for c in range(1,7):
        b=ii(rr.get(f'{c}コース_艇番')); st=ff(rr.get(f'{c}コース_スタートタイミング'))
        if b in range(1,7) and st is not None: out[b]=(c,st)
    return out

def ex_map(sr):
    out={}
    for b in range(1,7):
        c=ii(sr.get(f'艇{b}_コース')); st=ff(sr.get(f'艇{b}_スタート展示'))
        if c in range(1,7) and st is not None: out[b]=(c,st)
    return out

def shrink(vals, global_mean, pseudo=10):
    return (sum(vals)+pseudo*global_mean)/(len(vals)+pseudo) if vals or pseudo else global_mean

def main():
    player=defaultdict(list); pcourse=defaultdict(list); pfstate=defaultdict(list); pneigh=defaultdict(list)
    meet=defaultdict(list); global_hist=[]; out=[]; d=START
    while d<=END:
        ymd=d.strftime('%Y/%m/%d'); cards=bycode(rows(f'data/programs/race_cards/{ymd}.csv')); stt=bycode(rows(f'data/previews/stt/{ymd}.csv'))
        frozen=[]
        for code,sr in stt.items():
            if code not in cards: continue
            em=ex_map(sr); card=cards[code]; c2b={c:b for b,(c,st) in em.items()}
            for b,(ec,exst) in em.items():
                rid=card.get(f'艇{b}_登録番号','') or card.get(f'艇{b}_選手名','')
                gm=float(np.mean(global_hist)) if global_hist else .07
                fs='F' if exst<0 else 'N'
                ib=c2b.get(ec-1); ob=c2b.get(ec+1)
                ist=em.get(ib,(None,None))[1] if ib else None; ost=em.get(ob,(None,None))[1] if ob else None
                # coarse neighbor context: both faster/slower relative to own exhibition ST, or mixed/edge
                if ist is None or ost is None: nc='EDGE'
                else:
                    df=(ist-exst,ost-exst)
                    nc='BOTH_SLOWER' if df[0]>=.03 and df[1]>=.03 else ('BOTH_FASTER' if df[0]<=-.03 and df[1]<=-.03 else 'MIXED')
                base=shrink(player[rid],gm)
                vals_course=pcourse[(rid,ec)]; pred_course=exst+shrink(vals_course,base,6)
                vals_f=pfstate[(rid,fs)]; pred_f=exst+shrink(vals_f,base,6)
                vals_n=pneigh[(rid,nc)]; pred_n=exst+shrink(vals_n,base,6)
                vals_m=meet[rid]; pred_meet=exst+shrink(vals_m,base,4)
                pred_base=exst+base
                frozen.append((code,b,rid,ec,exst,fs,nc,pred_base,pred_course,pred_f,pred_n,pred_meet,len(player[rid]),len(vals_course),len(vals_f),len(vals_n),len(vals_m)))
        res=bycode(rows(f'data/results/realtime/{ymd}.csv')); todays=[]
        for rec in frozen:
            code,b,rid,ec,exst,fs,nc,pb,pc,pf,pn,pm,n0,nc0,nf0,nn0,nm0=rec
            am=actual_map(res.get(code,{}))
            if b not in am: continue
            ac,ast=am[b]
            if ac!=ec: continue
            delta=ast-exst
            if d>=TEST_START:
                out.append({'date':str(d),'race_code':code,'boat':b,'racer_id':rid,'course':ec,'ex_st':exst,'actual_st':ast,'fstate':fs,'neighbor_ctx':nc,'hist_player_n':n0,'hist_course_n':nc0,'hist_fstate_n':nf0,'hist_neighbor_n':nn0,'hist_meet_n':nm0,'pred_player':pb,'pred_player_course':pc,'pred_player_fstate':pf,'pred_player_neighbor':pn,'pred_player_meet':pm})
            todays.append((rid,ec,fs,nc,delta))
        # update only after date frozen
        for rid,ec,fs,nc,delta in todays:
            player[rid].append(delta); pcourse[(rid,ec)].append(delta); pfstate[(rid,fs)].append(delta); pneigh[(rid,nc)].append(delta); meet[rid].append(delta); meet[rid]=meet[rid][-6:]; global_hist.append(delta)
        d+=timedelta(days=1)
    if out:
        with open(OUT,'w',encoding='utf-8-sig',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(out[0]));w.writeheader();w.writerows(out)
    y=np.array([r['actual_st'] for r in out])
    variants=[('PLAYER','pred_player'),('PLAYERxCOURSE','pred_player_course'),('PLAYERxFSTATE','pred_player_fstate'),('PLAYERxNEIGHBOR','pred_player_neighbor'),('PLAYERxRECENT6','pred_player_meet')]
    L=['# v159 ST context interaction audit','',f'- 対象: {TEST_START}〜{END} walk-forward / 評価艇 **{len(out):,}**','- 各日の予測を全艇freeze後、その日の結果で履歴更新。同日リークなし。','- PLAYERを基準に、選手×コース / 選手×展示F正常 / 選手×隣艇文脈 / 選手の直近6走を比較。','', '|variant|MAE|Δ vs PLAYER|','|---|---:|---:|']
    base=None
    for lab,key in variants:
        p=np.array([r[key] for r in out]); mae=mean_absolute_error(y,p)
        if base is None: base=mae
        L.append(f'|{lab}|{mae:.5f}|{mae-base:+.5f}|')
    L += ['','## 履歴量別','|variant|条件|n|MAE|','|---|---|---:|---:|']
    checks=[('PLAYERxCOURSE','pred_player_course','hist_course_n'),('PLAYERxFSTATE','pred_player_fstate','hist_fstate_n'),('PLAYERxNEIGHBOR','pred_player_neighbor','hist_neighbor_n')]
    for lab,key,nkey in checks:
        for nmin in (3,6,12):
            z=[r for r in out if r[nkey]>=nmin]
            if not z: continue
            mae=mean_absolute_error([r['actual_st'] for r in z],[r[key] for r in z])
            L.append(f'|{lab}|prior n>={nmin}|{len(z):,}|{mae:.5f}|')
    L += ['','## 判定','- PLAYERより一貫してMAE改善し、履歴量が増えても改善方向が維持されるinteractionだけ次のv109 shadow候補にする。','- 「展示F」「隣艇が遅い」等は単純ルール化せず、予測改善が確認できた場合のみ採用する。']
    open(SUMMARY,'w',encoding='utf-8').write('\n'.join(L)+'\n'); print('\n'.join(L))
if __name__=='__main__': main()
