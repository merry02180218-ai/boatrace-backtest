from __future__ import annotations
import csv
from datetime import date
from collections import Counter
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

import analyze_v141_integrated_pre_scenario as v141
import analyze_v142_balanced_pre_scenario as v142
import analyze_v143_two_stage_pre_scenario as v143
import backtest_v51_lane_corrected_tickets as v51

CLASSES=v141.CLASSES
DEV0=date(2026,6,1); TRAIN_END=date(2026,7,31); TEST0=date(2026,8,1); TEST1=date(2026,8,31)
SUMMARY='summary_v144_pre_final_scenario.md'
OUT='analysis_v144_pre_final_scenario.csv'
TODAY_OUT='pred_v144_20260906_kiryu_final.csv'


def pmap(model,x):
    p=model.predict_proba(np.asarray([x],float))[0]; cs=list(model.named_steps['lr'].classes_)
    return {c:(float(p[cs.index(c)]) if c in cs else 0.0) for c in CLASSES}


def get_v143_threshold(rs):
    # Same policy as v143: threshold selected on June only.
    m141=v141.fit_integrated(rs,v141.TRAIN_END)
    m142=v142.fit_mode(rs,v141.TRAIN_END,'capped2')
    june=[z for z in rs if date.fromisoformat(z['date']).year==2026 and date.fromisoformat(z['date']).month==6]
    scored=[]
    for z in june:
        a=pmap(m141,z['x']); b=pmap(m142,z['x'])
        q=dict(z);q['p141_probs']=a;q['p142_probs']=b;scored.append(q)
    best=None
    for th in v143.THRESHOLDS:
        st=v143.stats(v143.apply_two_stage(scored,th));obj=.45*st['top']+.35*st['head']+.20*st['non1_macro']
        if best is None or obj>best[0]:best=(obj,th)
    return best[1]


def pre_probs_for_rows(rs,th,fit_end):
    m141=v141.fit_integrated(rs,fit_end);m142=v142.fit_mode(rs,fit_end,'capped2')
    out={}
    for z in rs:
        d=date.fromisoformat(z['date'])
        if d<DEV0:continue
        a=pmap(m141,z['x']);b=pmap(m142,z['x'])
        if a['1逃げ']>=th:pred='1逃げ';source=1
        else:
            non1=[c for c in CLASSES if c!='1逃げ'];pred=max(non1,key=lambda c:b[c]);source=0
        out[(z['date'],z['race_code'])]=(a,b,pred,source)
    return out


def direct_vec(z,stbias,cache):
    d=z['date'];ymd=d.replace('-','/');code=z['race_code']
    if d not in cache:
        cache[d]=(v51.by_code(f'data/previews/tkz/{ymd}.csv'),v51.by_code(f'data/previews/stt/{ymd}.csv'),v51.by_code(f'data/previews/original_exhibition/{ymd}.csv'))
    tkz,stt,orig=cache[d]
    if code not in tkz or code not in stt:return None
    ex,st,os=v51.corrected_direct(code,tkz,stt,orig,stbias)
    # Require display + start exhibition for all six; original metrics may validly default to .5 when absent.
    tr=tkz[code];sr=stt[code]
    for b in range(1,7):
        if v51.ff(tr.get(f'艇{b}_展示タイム')) is None or v51.ff(sr.get(f'艇{b}_スタート展示')) is None:return None
    one=.35*ex[1]+.20*st[1]+.25*os[1]['turn']+.20*os[1]['avg']
    m3=.28*ex[3]+.28*st[3]+.22*os[3]['straight']+.17*os[3]['avg']+.025
    m3s=.17*ex[3]+.22*st[3]+.17*os[3]['lap']+.27*os[3]['turn']+.12*os[3]['avg']+.025
    m4=.28*ex[4]+.28*st[4]+.22*os[4]['straight']+.17*os[4]['avg']+.025
    a4=.32*ex[4]+.38*st[4]+.18*os[4]['straight']+.12*os[4]['avg']
    t5=.22*ex[5]+.17*st[5]+.27*os[5]['lap']+.27*os[5]['turn']+.07*os[5]['avg']
    m5=.43*a4+.52*t5+.025
    raw=[]
    for b in range(1,7):raw += [ex[b],st[b],os[b]['lap'],os[b]['turn'],os[b]['straight'],os[b]['avg']]
    return [one,m3,m3s,m4,m5]+raw


def build_final_rows(rs,th,fit_end):
    pp=pre_probs_for_rows(rs,th,fit_end);stbias=v51.learn_st_frame_bias();cache={};out=[]
    for z in rs:
        d=date.fromisoformat(z['date'])
        if not (DEV0<=d<=TEST1):continue
        key=(z['date'],z['race_code'])
        if key not in pp:continue
        dv=direct_vec(z,stbias,cache)
        if dv is None:continue
        a,b,pred,src=pp[key]
        # PRE probabilities + PRE stage decision + actual direct/exhibition metrics.
        x=list(z['x'])+[a[c] for c in CLASSES]+[b[c] for c in CLASSES]+[1.0 if pred==c else 0.0 for c in CLASSES]+[float(src)]+dv
        out.append({'date':z['date'],'race_code':z['race_code'],'actual':z['actual'],'pre143':pred,'x_final':x})
    return out


def fit_final(rows,end):
    q=[z for z in rows if date.fromisoformat(z['date'])<=end]
    X=np.asarray([z['x_final'] for z in q],float);y=np.asarray([z['actual'] for z in q])
    m=Pipeline([('scale',StandardScaler()),('lr',LogisticRegression(C=.25,max_iter=3000,solver='lbfgs',class_weight=None))]);m.fit(X,y);return m


def stats(rows,model):
    if not rows:return {'n':0,'top':0,'head':0,'rec':{c:0 for c in CLASSES},'bins':[]}
    X=np.asarray([z['x_final'] for z in rows],float);p=model.predict_proba(X);cs=list(model.named_steps['lr'].classes_)
    for z,pr in zip(rows,p):
        probs={c:(float(pr[cs.index(c)]) if c in cs else 0.0) for c in CLASSES};z['probs']=probs;z['pred']=max(CLASSES,key=lambda c:probs[c]);z['conf']=probs[z['pred']]
    def head(c):return {'1逃げ':1,'3まくり':3,'3まくり差し':3,'4カド':4,'5頭':5}.get(c,0)
    n=len(rows);top=sum(z['pred']==z['actual'] for z in rows)/n;hh=sum(head(z['pred']) and head(z['pred'])==head(z['actual']) for z in rows)/n
    rec={}
    for c in CLASSES:
        q=[z for z in rows if z['actual']==c];rec[c]=sum(z['pred']==c for z in q)/len(q) if q else 0
    bins=[]
    for th in [.30,.35,.40,.45,.50,.55,.60]:
        q=[z for z in rows if z['conf']>=th];bins.append((th,len(q),sum(z['pred']==z['actual'] for z in q)/len(q) if q else 0))
    return {'n':n,'top':top,'head':hh,'rec':rec,'bins':bins}


def current_kiryu(rs,th,final_model):
    # FINAL is emitted only where today's direct/exhibition CSV is already available.
    base=v141.current_kiryu(v141.fit_integrated(rs,v141.END)); cards=v141.rows(f'data/programs/race_cards/{v141.TODAY}.csv')
    cards={r.get('レースコード',''):r for r in cards if str(r.get('レース場コード','')).zfill(2)==v141.KIRYU}
    # Rebuild current PRE with models fitted through Aug.
    m141=v141.fit_integrated(rs,v141.END);m142=v142.fit_mode(rs,v141.END,'capped2');one=v141.v138.fit_legacy();w10={r.get('レースコード',''):r for r in v141.rows(f'data/programs/waku10/{v141.TODAY}.csv')}
    stbias=v51.learn_st_frame_bias();cache={};arr=[]
    for code,card in cards.items():
        rn=v141.rno(card.get('レース回'))
        if not 1<=rn<=12:continue
        x=v141.race_features(card,w10.get(code,{}));op=float(one.predict_proba(np.asarray([v141.v138.legacy_row_from_x(x,v141.KIRYU)],float))[0,1]);sc=v141.structural(x);fv=v141.feature_vec(op,sc,v141.KIRYU)
        a=pmap(m141,fv);b=pmap(m142,fv)
        if a['1逃げ']>=th:pre='1逃げ';src=1
        else:
            non1=[c for c in CLASSES if c!='1逃げ'];pre=max(non1,key=lambda c:b[c]);src=0
        z={'date':'2026-09-06','race_code':code};dv=direct_vec(z,stbias,cache)
        if dv is None:continue
        xf=list(fv)+[a[c] for c in CLASSES]+[b[c] for c in CLASSES]+[1.0 if pre==c else 0.0 for c in CLASSES]+[float(src)]+dv
        probs=pmap(final_model,xf);pred=max(CLASSES,key=lambda c:probs[c])
        arr.append({'race':rn,'pre143':pre,'final':pred,'confidence':100*probs[pred],**{f'p_{c}':100*probs[c] for c in CLASSES}})
    arr.sort(key=lambda z:z['race']);return arr


def main():
    rs=v141.build_history();th=get_v143_threshold(rs)
    rows=build_final_rows(rs,th,v141.TRAIN_END)
    tr=[z for z in rows if date.fromisoformat(z['date'])<=TRAIN_END];te=[z for z in rows if TEST0<=date.fromisoformat(z['date'])<=TEST1]
    model=fit_final(tr,TRAIN_END);st=stats(te,model)
    with open(OUT,'w',newline='',encoding='utf-8-sig') as f:
        fs=['date','race_code','actual','pre143','pred','conf']+[f'p_{c}' for c in CLASSES];w=csv.DictWriter(f,fieldnames=fs);w.writeheader()
        for z in te:
            row={k:z.get(k,'') for k in fs};row.update({f'p_{c}':100*z['probs'][c] for c in CLASSES});w.writerow(row)
    # Prospective refit after untouched Aug evaluation, using all available history through Aug31.
    allrows=build_final_rows(rs,th,v141.END);pros=fit_final(allrows,v141.END);today=current_kiryu(rs,th,pros)
    with open(TODAY_OUT,'w',newline='',encoding='utf-8-sig') as f:
        fs=list(today[0].keys()) if today else ['race'];w=csv.DictWriter(f,fieldnames=fs);w.writeheader();w.writerows(today)
    L=['# v144 v143 PRE + 直前情報 FINAL展開モデル','',f'- v143採用閾値: {th:.2f}','- PRE段階はv143。FINALで枠補正済み展示タイム・展示ST・オリジナル展示（一周/回り足/直線）を追加。','- 同レース結果/払戻/締切後オッズはFINAL特徴に不使用。','- FINAL学習: 6〜7月、完全ホールドアウト: 8月。8月評価後のみ、9/6予測用に8/31までで再学習。','',f"## Aug holdout: {st['n']}R / 展開Top1 {st['top']*100:.1f}% / 頭一致 {st['head']*100:.1f}%",'','### 実クラス別 recall','|実展開|recall|','|---|---:|']
    for c in CLASSES:L.append(f"|{c}|{st['rec'][c]*100:.1f}%|")
    L += ['','### FINAL確信度別','|条件|R|Top1|','|---|---:|---:|']
    for thh,n,a in st['bins']:L.append(f'|p>={thh:.2f}|{n}|{a*100:.1f}%|')
    L += ['','## 2026-09-06 桐生 FINAL（直前データ取得済みRのみ）','|R|PRE v143|FINAL|確率|1逃げ|3まくり|3まくり差し|4カド|5頭|その他|','|---:|---|---|---:|---:|---:|---:|---:|---:|---:|']
    for z in today:L.append(f"|{z['race']}R|{z['pre143']}|{z['final']}|{z['confidence']:.1f}%|{z['p_1逃げ']:.1f}%|{z['p_3まくり']:.1f}%|{z['p_3まくり差し']:.1f}%|{z['p_4カド']:.1f}%|{z['p_5頭']:.1f}%|{z['p_その他']:.1f}%|")
    L += ['','## 運用','- PREで監視候補を固定 → 展示後にv144 FINAL更新 → FINAL展開クラスと確信度でBUY/SKIP → その後に既存相手選び/買い目を接続。','- 8月ホールドアウトで確信度が単調に精度上昇しない場合は本番採用しない。']
    open(SUMMARY,'w',encoding='utf-8').write('\n'.join(L)+'\n')

if __name__=='__main__':main()
