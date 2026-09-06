from __future__ import annotations
from datetime import date
from collections import Counter
import csv, math
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

import analyze_v141_integrated_pre_scenario as v141

CLASSES=v141.CLASSES
START=date(2026,3,1); TUNE_TRAIN_END=date(2026,4,30); VALID_START=date(2026,5,1); VALID_END=date(2026,5,31)
TRAIN_END=date(2026,5,31); TEST_START=date(2026,6,1); END=date(2026,8,31)
OUT='analysis_v142_balanced_pre_scenario.csv'
SUMMARY='summary_v142_balanced_pre_scenario.md'
TODAY_OUT='pred_v142_20260906_kiryu_scenario.csv'


def make_weights(y, mode):
    c=Counter(y); n=len(y); k=len(c)
    bal={cl:n/(k*c[cl]) for cl in c}
    if mode=='none': return None
    if mode=='sqrt': return {cl:math.sqrt(w) for cl,w in bal.items()}
    if mode=='balanced': return bal
    if mode=='capped2': return {cl:min(2.0,w) for cl,w in bal.items()}
    if mode=='capped3': return {cl:min(3.0,w) for cl,w in bal.items()}
    raise ValueError(mode)


def fit_model(rs, through, mode):
    tr=[z for z in rs if date.fromisoformat(z['date'])<=through]
    X=np.asarray([z['x'] for z in tr],float); y=np.asarray([z['actual'] for z in tr])
    cw=make_weights(y,mode)
    m=Pipeline([('scale',StandardScaler()),('lr',LogisticRegression(C=.35,max_iter=3000,solver='lbfgs',class_weight=cw))])
    m.fit(X,y); return m


def predict_rows(model, rows):
    X=np.asarray([z['x'] for z in rows],float); pro=model.predict_proba(X); classes=list(model.named_steps['lr'].classes_)
    out=[]
    for src,q in zip(rows,pro):
        z=dict(src); probs={cl:(float(q[classes.index(cl)]) if cl in classes else 0.0) for cl in CLASSES}; best=max(CLASSES,key=lambda c:probs[c])
        z['pred']=best;z['confidence']=probs[best];z['probs']=probs;out.append(z)
    return out


def score(rows):
    n=len(rows); top=sum(z['pred']==z['actual'] for z in rows)
    recalls=[]
    by={}
    for c in CLASSES:
        q=[z for z in rows if z['actual']==c]
        rec=sum(z['pred']==c for z in q)/len(q) if q else 0.0
        by[c]=(len(q),rec); recalls.append(rec)
    macro=sum(recalls)/len(recalls)
    # non-1 macro is the central v142 objective, with some overall accuracy retained.
    non1=sum(by[c][1] for c in CLASSES if c!='1逃げ')/5
    objective=.70*non1+.30*(top/n if n else 0)
    return {'n':n,'acc':top/n if n else 0,'macro':macro,'non1_macro':non1,'objective':objective,'by':by}


def current_kiryu(model):
    # reuse v141's prospective feature path but score with the selected balanced model
    cards=v141.rows(f'data/programs/race_cards/{v141.TODAY}.csv'); w10={r.get('レースコード',''):r for r in v141.rows(f'data/programs/waku10/{v141.TODAY}.csv')}
    one=v141.v138.fit_legacy(); arr=[]
    for card in cards:
        if str(card.get('レース場コード','')).zfill(2)!=v141.KIRYU: continue
        rn=v141.rno(card.get('レース回'))
        if not 1<=rn<=12: continue
        x=v141.race_features(card,w10.get(card.get('レースコード',''),{})); op=float(one.predict_proba(np.asarray([v141.v138.legacy_row_from_x(x,v141.KIRYU)],float))[0,1]); sc=v141.structural(x)
        fv=v141.feature_vec(op,sc,v141.KIRYU); q=model.predict_proba(np.asarray([fv],float))[0]; classes=list(model.named_steps['lr'].classes_)
        probs={cl:(float(q[classes.index(cl)]) if cl in classes else 0.0) for cl in CLASSES}; best=max(CLASSES,key=lambda c:probs[c])
        arr.append({'race':rn,'one_pre':100*op,**sc,'best':best,'confidence':100*probs[best],**{f'p_{c}':100*probs[c] for c in CLASSES}})
    return sorted(arr,key=lambda z:z['race'])


def main():
    rs=v141.build_history()
    # tune class-weight strength only on May; Jun-Aug remains untouched holdout.
    tune_train=[z for z in rs if date.fromisoformat(z['date'])<=TUNE_TRAIN_END]
    val=[z for z in rs if VALID_START<=date.fromisoformat(z['date'])<=VALID_END]
    modes=['none','sqrt','capped2','capped3','balanced']
    trials=[]
    for mode in modes:
        m=fit_model(tune_train,TUNE_TRAIN_END,mode); pred=predict_rows(m,val); s=score(pred); trials.append((mode,s))
    best_mode=max(trials,key=lambda t:t[1]['objective'])[0]

    model=fit_model(rs,TRAIN_END,best_mode)
    test=[z for z in rs if date.fromisoformat(z['date'])>=TEST_START]
    te=predict_rows(model,test); st=score(te)

    final_model=fit_model(rs,END,best_mode); today=current_kiryu(final_model)

    fields=['date','race_code','venue','race','actual','pred','confidence','one_pre','m3','m3s','m4','m5','g3','g3s','g4','g5']+[f'p_{c}' for c in CLASSES]
    with open(OUT,'w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for z in te:
            row={k:z.get(k,'') for k in fields};row.update({f'p_{c}':100*z['probs'][c] for c in CLASSES});w.writerow(row)
    if today:
        with open(TODAY_OUT,'w',newline='',encoding='utf-8-sig') as f:
            fs=list(today[0].keys());w=csv.DictWriter(f,fieldnames=fs);w.writeheader();w.writerows(today)

    L=['# v142 クラス不均衡補正 全モデル統合PRE展開モデル','',
       '- v141と同じPRE特徴のみ。展示・実進入・当日オッズ不使用。',
       '- 3〜4月で学習、5月だけでclass_weight方式を選択。6〜8月は完全ホールドアウト。',
       '- 選択目的: 非①5クラスのmacro recall 70% + 全体Top1精度30%。Jun-Augを見て重みは選ばない。','',
       '## 5月チューニング比較','|mode|全体Top1|非①macro recall|macro recall|objective|','|---|---:|---:|---:|---:|']
    for mode,s in trials:L.append(f"|{mode}|{100*s['acc']:.1f}%|{100*s['non1_macro']:.1f}%|{100*s['macro']:.1f}%|{100*s['objective']:.1f}%|")
    L += ['',f'**採用: {best_mode}**','',f"## Jun-Aug holdout: {st['n']}R / Top1 {100*st['acc']:.1f}% / 非①macro recall {100*st['non1_macro']:.1f}% / macro recall {100*st['macro']:.1f}%",'',
          '### 実クラス別','|実展開|R|Top1 recall|','|---|---:|---:|']
    for c in CLASSES:
        n,rec=st['by'][c];L.append(f'|{c}|{n}|{100*rec:.1f}%|')
    L += ['','### 確信度別','|条件|R|Top1|','|---|---:|---:|']
    for th in [.30,.35,.40,.45,.50,.55,.60]:
        q=[z for z in te if z['confidence']>=th]; ss=score(q) if q else {'n':0,'acc':0};L.append(f"|p>={th:.2f}|{ss['n']}|{100*ss['acc']:.1f}%|")
    if today:
        L += ['','## 2026-09-06 桐生12R v142展開確率','|R|最有力|確率|1逃げ|3まくり|3まくり差し|4カド|5頭|その他|','|---:|---|---:|---:|---:|---:|---:|---:|---:|']
        for z in today:L.append(f"|{z['race']}R|{z['best']}|{z['confidence']:.1f}%|{z['p_1逃げ']:.1f}%|{z['p_3まくり']:.1f}%|{z['p_3まくり差し']:.1f}%|{z['p_4カド']:.1f}%|{z['p_5頭']:.1f}%|{z['p_その他']:.1f}%|")
    L += ['','## 判定','- v141より非①展開の識別が改善するかを最優先で確認。','- 本番採用条件は、Jun-Augで非①recall改善だけでなく、確信度帯のTop1精度と後続3連単ROI検証でも悪化しないこと。']
    open(SUMMARY,'w',encoding='utf-8').write('\n'.join(L)+'\n')

if __name__=='__main__': main()
