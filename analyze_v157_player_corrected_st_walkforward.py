from __future__ import annotations
import csv
from collections import defaultdict
from datetime import date, timedelta
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error
from backtest import rows

START=date(2026,5,1); END=date(2026,9,5)
TEST_START=date(2026,7,1)
OUT='analysis_v157_player_corrected_st_walkforward.csv'
SUMMARY='summary_v157_player_corrected_st_walkforward.md'

def ff(x):
    try:return float(x)
    except:return None

def ii(x):
    try:return int(float(x))
    except:return None

def bycode(rs):return {r.get('レースコード',''):r for r in rs if r.get('レースコード')}

def actual_map(rr):
    z={}
    for c in range(1,7):
        b=ii(rr.get(f'{c}コース_艇番')); st=ff(rr.get(f'{c}コース_スタートタイミング'))
        if b in range(1,7) and st is not None:z[b]=(c,st)
    return z

def ex_map(sr):
    z={}
    for b in range(1,7):
        c=ii(sr.get(f'艇{b}_コース')); st=ff(sr.get(f'艇{b}_スタート展示'))
        if c in range(1,7) and st is not None:z[b]=(c,st)
    return z

def main():
    hist=defaultdict(list); global_hist=[]; out=[]; d=START
    while d<=END:
        ymd=d.strftime('%Y/%m/%d'); cards=bycode(rows(f'data/programs/race_cards/{ymd}.csv')); stt=bycode(rows(f'data/previews/stt/{ymd}.csv'))
        # freeze predictions before today's results
        frozen=[]
        for code,sr in stt.items():
            if code not in cards:continue
            em=ex_map(sr); card=cards[code]
            for b,(ec,exst) in em.items():
                rid=card.get(f'艇{b}_登録番号','') or card.get(f'艇{b}_選手名','')
                ph=hist[rid]; gm=float(np.mean(global_hist)) if global_hist else .07
                # only prior races. shrink player delta toward prior global delta with 10 pseudo-races
                bias=(sum(ph)+10*gm)/(len(ph)+10)
                pred_raw=exst+gm
                pred_player=exst+bias
                frozen.append((code,b,rid,ec,exst,pred_raw,pred_player,len(ph),bias))
        res=bycode(rows(f'data/results/realtime/{ymd}.csv'))
        todays=[]
        for code,b,rid,ec,exst,pr,pp,n,bias in frozen:
            am=actual_map(res.get(code,{}))
            if b not in am:continue
            ac,ast=am[b]
            if ac!=ec:continue
            delta=ast-exst
            if d>=TEST_START:
                out.append({'date':str(d),'race_code':code,'boat':b,'racer_id':rid,'course':ec,'ex_st':exst,'actual_st':ast,'hist_n':n,'prior_bias':bias,'pred_global':pr,'pred_player':pp,'abs_err_global':abs(ast-pr),'abs_err_player':abs(ast-pp)})
            todays.append((rid,delta))
        # update only after all predictions for the date are frozen/evaluated
        for rid,delta in todays:
            hist[rid].append(delta); global_hist.append(delta)
        d+=timedelta(days=1)
    if out:
        with open(OUT,'w',encoding='utf-8-sig',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(out[0]));w.writeheader();w.writerows(out)
    y=np.array([r['actual_st'] for r in out]); g=np.array([r['pred_global'] for r in out]); p=np.array([r['pred_player'] for r in out])
    def met(a):return mean_absolute_error(y,a),mean_squared_error(y,a)**.5
    gmae,grmse=met(g); pmae,prmse=met(p)
    L=['# v157 player-corrected exhibition ST walk-forward','',f'- 学習開始: {START} / untouched逐日評価: {TEST_START}〜{END}', '- 各日の予測を全艇freezeしてから、その日の結果で履歴更新。同日リークなし。','- GLOBAL: 展示ST + 過去日だけの全体平均(本番-展示)','- PLAYER: 展示ST + 過去日だけの選手bias（全体平均へ10走shrink）','',f'- 評価艇: **{len(out):,}**',f'- GLOBAL MAE **{gmae:.4f}** / RMSE **{grmse:.4f}**',f'- PLAYER MAE **{pmae:.4f}** / RMSE **{prmse:.4f}**',f'- ΔMAE **{pmae-gmae:+.4f}** / ΔRMSE **{prmse-grmse:+.4f}**','']
    for nmin in (0,3,6,12,20):
        z=[r for r in out if r['hist_n']>=nmin]
        if not z:continue
        yy=np.array([r['actual_st'] for r in z]);gg=np.array([r['pred_global'] for r in z]);pp=np.array([r['pred_player'] for r in z])
        L.append(f"- prior n>={nmin}: {len(z):,}艇 / GLOBAL MAE {mean_absolute_error(yy,gg):.4f} / PLAYER MAE {mean_absolute_error(yy,pp):.4f} / Δ {mean_absolute_error(yy,pp)-mean_absolute_error(yy,gg):+.4f}")
    L += ['','## 判定','- PLAYERのMAE/RMSEがGLOBALより改善し、履歴数が増えるほど改善が安定するなら、選手固有展示→本番補正を次のv109 shadow特徴へ追加する。','- 改善しない場合はv156の相関が説明的であって予測的ではないため採用しない。']
    open(SUMMARY,'w',encoding='utf-8').write('\n'.join(L)+'\n');print('\n'.join(L))
if __name__=='__main__':main()
