from __future__ import annotations
import csv
from datetime import date
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

import analyze_v141_integrated_pre_scenario as v141
import analyze_v142_balanced_pre_scenario as v142
import analyze_v144_pre_final_scenario as v144

# Compatibility with v144/v143 helpers currently stored in repo.
if not hasattr(v142,'fit_mode'):
    v142.fit_mode=v142.fit_model

CLASSES=v141.CLASSES
NON1=[c for c in CLASSES if c!='1逃げ']
JUNE_END=date(2026,6,30)
JUL0=date(2026,7,1); JUL1=date(2026,7,31)
AUG0=date(2026,8,1); AUG1=date(2026,8,31)
GATES=[.40,.45,.50,.55,.60,.65,.70,.75]
OUT='analysis_v145_one_gate_specialized_non1.csv'
SUMMARY='summary_v145_one_gate_specialized_non1.md'


def pmap(model,x,classes):
    p=model.predict_proba(np.asarray([x],float))[0]
    cs=list(model.named_steps['lr'].classes_)
    return {c:(float(p[cs.index(c)]) if c in cs else 0.0) for c in classes}


def fit_gate(rows,end):
    q=[z for z in rows if date.fromisoformat(z['date'])<=end]
    X=np.asarray([z['x_final'] for z in q],float)
    y=np.asarray([1 if z['actual']=='1逃げ' else 0 for z in q],int)
    m=Pipeline([('scale',StandardScaler()),('lr',LogisticRegression(C=.25,max_iter=3000,solver='lbfgs'))])
    m.fit(X,y);return m


def fit_non1(rows,end):
    q=[z for z in rows if date.fromisoformat(z['date'])<=end and z['actual']!='1逃げ']
    X=np.asarray([z['x_final'] for z in q],float);y=np.asarray([z['actual'] for z in q])
    # Dedicated non-1 selector. x_final already contains PRE structural scores plus
    # model-specific direct scores for 3-makuri/3-makurizashi/4-corner/5-head.
    m=Pipeline([('scale',StandardScaler()),('lr',LogisticRegression(C=.25,max_iter=3000,solver='lbfgs',class_weight='balanced'))])
    m.fit(X,y);return m


def head(c):
    return {'1逃げ':1,'3まくり':3,'3まくり差し':3,'4カド':4,'5頭':5}.get(c,0)


def score_rows(rows,gate,non1,th):
    out=[]
    for src in rows:
        z=dict(src)
        pg=float(gate.predict_proba(np.asarray([z['x_final']],float))[0,1])
        if pg>=th:
            pred='1逃げ';conf=pg;branch='1-gate'
            probs={'1逃げ':pg}
        else:
            pn=pmap(non1,z['x_final'],NON1)
            pred=max(NON1,key=lambda c:pn[c]);conf=(1-pg)*pn[pred];branch='non1-specialized';probs={'1逃げ':pg,**{c:(1-pg)*pn[c] for c in NON1}}
        z.update(pred145=pred,conf145=conf,gate_p1=pg,branch145=branch,probs145=probs)
        out.append(z)
    return out


def stat(rows):
    n=len(rows)
    top=sum(z['pred145']==z['actual'] for z in rows)/n if n else 0
    hh=sum(head(z['pred145']) and head(z['pred145'])==head(z['actual']) for z in rows)/n if n else 0
    rec={}
    for c in CLASSES:
        q=[z for z in rows if z['actual']==c]
        rec[c]=sum(z['pred145']==c for z in q)/len(q) if q else 0
    non1_macro=float(np.mean([rec[c] for c in NON1]))
    return {'n':n,'top':top,'head':hh,'rec':rec,'non1_macro':non1_macro}


def tune_gate(jul,gate,non1):
    trials=[]
    for th in GATES:
        s=stat(score_rows(jul,gate,non1,th))
        # Keep overall/head strength, while explicitly rewarding non-1 recovery.
        obj=.40*s['top']+.30*s['head']+.30*s['non1_macro']
        trials.append((th,obj,s))
    return max(trials,key=lambda x:x[1])[0],trials


def baseline_v144(rows,train_end,test):
    m=v144.fit_final(rows,train_end)
    q=[dict(z) for z in test]
    s=v144.stats(q,m)
    return s


def main():
    rs=v141.build_history()
    # v143 threshold is already validated by v144 and fixed at 0.45 in its successful run.
    pre_th=.45
    rows=v144.build_final_rows(rs,pre_th,v141.TRAIN_END)
    june=[z for z in rows if date.fromisoformat(z['date'])<=JUNE_END]
    jul=[z for z in rows if JUL0<=date.fromisoformat(z['date'])<=JUL1]
    aug=[z for z in rows if AUG0<=date.fromisoformat(z['date'])<=AUG1]

    gate_j=fit_gate(june,JUNE_END);non1_j=fit_non1(june,JUNE_END)
    best,trials=tune_gate(jul,gate_j,non1_j)

    # Untouched August: refit on June+July only after gate threshold is fixed.
    gate=fit_gate(rows,JUL1);non1=fit_non1(rows,JUL1)
    pred=score_rows(aug,gate,non1,best);st=stat(pred)
    base=baseline_v144(rows,JUL1,aug)

    fs=['date','race_code','actual','pre143','pred145','branch145','conf145','gate_p1']+[f'p_{c}' for c in CLASSES]
    with open(OUT,'w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=fs);w.writeheader()
        for z in pred:
            r={k:z.get(k,'') for k in fs};r.update({f'p_{c}':100*z['probs145'].get(c,0) for c in CLASSES});w.writerow(r)

    L=['# v145 v144①逃げゲート + 非①専用分岐','',
       '- PREはv143、直前特徴はv144と同じ。','- Stage1: v144系の直前特徴から①逃げゲートだけ判定。','- Stage2: ①逃げゲート未通過だけ、③まくり/③まくり差し/④カド/⑤頭/その他の専用選択器へ分岐。','- 非①選択器には既存PRE構造スコアと専用直前スコア（3ま/3差/4カド/5頭）を含むx_finalを使用。','- 閾値は7月だけで選択。8月は完全ホールドアウト。結果/払戻/締切後オッズは特徴に不使用。','',
       '## 7月 gate threshold tuning','|p1 gate|Top1|頭一致|非①macro recall|objective|','|---:|---:|---:|---:|---:|']
    for th,obj,s in trials:
        L.append(f"|{th:.2f}|{s['top']*100:.1f}%|{s['head']*100:.1f}%|{s['non1_macro']*100:.1f}%|{obj*100:.1f}%|")
    L += ['',f'**採用gate: p1 >= {best:.2f}**','',
          f"## Aug untouched holdout: {st['n']}R",f"- v145 Top1: **{st['top']*100:.1f}%**",f"- v145 頭一致: **{st['head']*100:.1f}%**",f"- v145 非①macro recall: **{st['non1_macro']*100:.1f}%**",'',
          f"### v144 baseline（同じAug）: Top1 {base['top']*100:.1f}% / 頭一致 {base['head']*100:.1f}%",'',
          '### 実クラス別 recall','|実展開|v145 recall|v144 recall|','|---|---:|---:|']
    for c in CLASSES:L.append(f"|{c}|{st['rec'][c]*100:.1f}%|{base['rec'][c]*100:.1f}%|")
    L += ['','### v145確信度別','|条件|R|Top1|','|---|---:|---:|']
    for th in [.30,.35,.40,.45,.50,.55,.60]:
        q=[z for z in pred if z['conf145']>=th];acc=sum(z['pred145']==z['actual'] for z in q)/len(q) if q else 0;L.append(f'|p>={th:.2f}|{len(q)}|{acc*100:.1f}%|')
    L += ['','## 採用判定','- v144より①逃げ精度を大きく落とさず、③/④/⑤のrecallと非①macro recallが明確に改善するかを見る。','- 改善しても本番採用前に、各分岐へ現行の相手選び/固定買い目を接続して3連単ROIを別途検証する。']
    open(SUMMARY,'w',encoding='utf-8').write('\n'.join(L)+'\n')

if __name__=='__main__':main()
