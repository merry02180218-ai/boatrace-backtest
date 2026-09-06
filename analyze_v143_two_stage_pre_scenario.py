from __future__ import annotations
import csv
from datetime import date
from collections import defaultdict
import numpy as np

import analyze_v141_integrated_pre_scenario as v141
import analyze_v142_balanced_pre_scenario as v142

TRAIN_END=date(2026,5,31)
TEST_START=date(2026,6,1)
END=date(2026,8,31)
THRESHOLDS=[0.45,0.50,0.55,0.60,0.65,0.70]
CLASSES=v141.CLASSES
SUMMARY='summary_v143_two_stage_pre_scenario.md'
TODAY_OUT='pred_v143_20260906_kiryu_scenario.csv'


def head(cl):
    return {'1逃げ':1,'3まくり':3,'3まくり差し':3,'4カド':4,'5頭':5}.get(cl,0)


def apply_two_stage(rows,th):
    out=[]
    for z in rows:
        p1=z['p141_probs']['1逃げ']
        if p1>=th:
            pred='1逃げ'; conf=p1; source='v141'
        else:
            # v142 is only used among non-1 classes
            non1=[c for c in CLASSES if c!='1逃げ']
            pred=max(non1,key=lambda c:z['p142_probs'][c]); conf=z['p142_probs'][pred]; source='v142'
        q=dict(z);q.update(pred143=pred,conf143=conf,source143=source);out.append(q)
    return out


def stats(rows):
    n=len(rows)
    top=sum(z['pred143']==z['actual'] for z in rows)
    hh=sum(head(z['pred143']) and head(z['pred143'])==head(z['actual']) for z in rows)
    recalls={}
    for c in CLASSES:
        q=[z for z in rows if z['actual']==c]
        recalls[c]=(sum(z['pred143']==c for z in q)/len(q) if q else 0)
    non1=np.mean([recalls[c] for c in CLASSES if c!='1逃げ'])
    return {'n':n,'top':top/n if n else 0,'head':hh/n if n else 0,'recalls':recalls,'non1_macro':float(non1)}


def build_joined_history():
    rs=v141.build_history()
    m141=v141.fit_integrated(rs,TRAIN_END)
    # v142 helper should expose selected capped2-like balanced model
    m142=v142.fit_mode(rs,TRAIN_END,'capped2')
    te=[z for z in rs if date.fromisoformat(z['date'])>=TEST_START]
    X=np.asarray([z['x'] for z in te],float)
    p141=m141.predict_proba(X); c141=list(m141.named_steps['lr'].classes_)
    p142=m142.predict_proba(X); c142=list(m142.named_steps['lr'].classes_)
    out=[]
    for z,a,b in zip(te,p141,p142):
        q=dict(z)
        q['p141_probs']={c:(float(a[c141.index(c)]) if c in c141 else 0.0) for c in CLASSES}
        q['p142_probs']={c:(float(b[c142.index(c)]) if c in c142 else 0.0) for c in CLASSES}
        out.append(q)
    return rs,out


def tune_threshold(te):
    # select threshold on June only; evaluate Jul-Aug separately to reduce direct overfit
    june=[z for z in te if date.fromisoformat(z['date']).month==6]
    later=[z for z in te if date.fromisoformat(z['date']).month in (7,8)]
    rows=[]
    for th in THRESHOLDS:
        st=stats(apply_two_stage(june,th))
        # prioritize top/head stability while preserving non1 sensitivity
        obj=.45*st['top']+.35*st['head']+.20*st['non1_macro']
        rows.append((th,obj,st))
    best=max(rows,key=lambda x:x[1])[0]
    return best,rows,later


def today_predictions(rs,best_th):
    m141=v141.fit_integrated(rs,END)
    m142=v142.fit_mode(rs,END,'capped2')
    cards=v141.rows(f'data/programs/race_cards/{v141.TODAY}.csv')
    w10={r.get('レースコード',''):r for r in v141.rows(f'data/programs/waku10/{v141.TODAY}.csv')}
    one=v141.v138.fit_legacy()
    arr=[]
    for card in cards:
        if str(card.get('レース場コード','')).zfill(2)!=v141.KIRYU: continue
        rn=v141.rno(card.get('レース回'))
        if not 1<=rn<=12: continue
        x=v141.race_features(card,w10.get(card.get('レースコード',''),{}))
        op=float(one.predict_proba(np.asarray([v141.v138.legacy_row_from_x(x,v141.KIRYU)],float))[0,1])
        sc=v141.structural(x);fv=v141.feature_vec(op,sc,v141.KIRYU)
        a=m141.predict_proba(np.asarray([fv],float))[0];ca=list(m141.named_steps['lr'].classes_)
        b=m142.predict_proba(np.asarray([fv],float))[0];cb=list(m142.named_steps['lr'].classes_)
        p1={c:(float(a[ca.index(c)]) if c in ca else 0.0) for c in CLASSES}
        p2={c:(float(b[cb.index(c)]) if c in cb else 0.0) for c in CLASSES}
        if p1['1逃げ']>=best_th:
            pred='1逃げ';source='v141';conf=p1['1逃げ']
        else:
            non1=[c for c in CLASSES if c!='1逃げ'];pred=max(non1,key=lambda c:p2[c]);source='v142';conf=p2[pred]
        arr.append({'race':rn,'best':pred,'source':source,'confidence':100*conf,'v141_p1':100*p1['1逃げ'],**{f'v142_{c}':100*p2[c] for c in CLASSES if c!='1逃げ'}})
    arr.sort(key=lambda z:z['race'])
    return arr


def main():
    rs,te=build_joined_history();best,tune_rows,later=tune_threshold(te)
    later_ap=apply_two_stage(later,best);st=stats(later_ap)
    today=today_predictions(rs,best)

    with open(TODAY_OUT,'w',newline='',encoding='utf-8-sig') as f:
        fs=list(today[0].keys()) if today else ['race'];w=csv.DictWriter(f,fieldnames=fs);w.writeheader();w.writerows(today)

    L=['# v143 二段階PRE展開モデル','',
       '- Stage1: v141の①逃げ確率が閾値以上なら①逃げ。','- Stage2: それ未満だけv142へ回し、非①5クラスから最大確率を採用。',
       '- 閾値は6月だけで選択。7〜8月は未使用ホールドアウト評価。','',
       '## 6月 閾値チューニング','|th|Top1|頭一致|非①macro recall|objective|','|---:|---:|---:|---:|---:|']
    for th,obj,s in tune_rows:
        L.append(f"|{th:.2f}|{s['top']*100:.1f}%|{s['head']*100:.1f}%|{s['non1_macro']*100:.1f}%|{obj*100:.1f}%|")
    L += ['',f'**採用閾値: v141 ①逃げ p >= {best:.2f}**','',
          f"## Jul-Aug holdout: {st['n']}R / Top1 {st['top']*100:.1f}% / 頭一致 {st['head']*100:.1f}% / 非①macro recall {st['non1_macro']*100:.1f}%",'',
          '### 実クラス別 recall','|実展開|recall|','|---|---:|']
    for c in CLASSES:L.append(f"|{c}|{st['recalls'][c]*100:.1f}%|")
    L += ['','## 2026-09-06 桐生12R v143','|R|最有力|採用段階|確信度|v141①逃げ|v142③ま|v142③差|v142④|v142⑤|v142その他|','|---:|---|---|---:|---:|---:|---:|---:|---:|---:|']
    for z in today:
        L.append(f"|{z['race']}R|{z['best']}|{z['source']}|{z['confidence']:.1f}%|{z['v141_p1']:.1f}%|{z['v142_3まくり']:.1f}%|{z['v142_3まくり差し']:.1f}%|{z['v142_4カド']:.1f}%|{z['v142_5頭']:.1f}%|{z['v142_その他']:.1f}%|")
    open(SUMMARY,'w',encoding='utf-8').write('\n'.join(L)+'\n')

if __name__=='__main__':main()
