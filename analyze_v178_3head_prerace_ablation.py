#!/usr/bin/env python3
"""v178: ablation of v177 pre-race development features.

Compare on strict Jun-Aug OOS:
- base: v175/v176 race features only
- style: racer rolling style only
- prevex: previous-race exhibition/original-exhibition only
- both: style + previous exhibition (v177 enriched)

NO LEAK
- Uses reconstruct() from v177, which reads player state before current race then updates after it.
- Current-race exhibition is never included.
- Actual winning method is target only.
- Each evaluation month trains only on dates before that month.
"""
from __future__ import annotations
import csv
from datetime import date
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score, log_loss, accuracy_score

from analyze_v166_3head_pair_direct import read, ii, combo, SRC
from analyze_v175_3head_prerace_development_softpair import race_feat
from analyze_v177_3head_historical_web_enrichment import reconstruct, target

OUT='analysis_v178_3head_prerace_ablation.csv'
SUMMARY='summary_v178_3head_prerace_ablation.md'
TEST_MONTHS=['2026-06','2026-07','2026-08']
STYLE=[
 'b1_hist_starts','b1_makurare_rate','b1_sasare_rate','b1_escape_rate',
 'b3_hist_starts','b3_makuri_rate','b3_makuri_sashi_rate','b3_head_rate',
 'style_makuri_edge','style_makurisashi_edge'
]
PREVEX=['b3_prev_ex','b3_prev_lap','b3_prev_turn','b3_prev_straight','b3_prev_orig_avg','b3_has_prev_ex']
VARIANTS={'base':[],'style':STYLE,'prevex':PREVEX,'both':STYLE+PREVEX}

def vec(r,e,cols):
    x=list(race_feat(r))
    x.extend(float(e[k]) for k in cols)
    return x

def eligible(r):
    if ii(r.get('valid_result'))!=1:return False
    a=combo(r.get('actual_combo'));t=target(r)
    return len(a)==3 and a[0]==3 and t is not None

def eval_month(base,extra,mo,name,cols):
    first=date.fromisoformat(mo+'-01');X=[];y=[];te=[];yt=[]
    for i,r in enumerate(base):
        if not eligible(r):continue
        t=target(r)
        if date.fromisoformat(r['date'])<first:
            X.append(vec(r,extra[i],cols));y.append(t)
        elif r.get('month')==mo:
            te.append(vec(r,extra[i],cols));yt.append(t)
    if len(X)<300 or len(te)<5:return None
    m=Pipeline([('s',StandardScaler()),('m',LogisticRegression(C=.25,max_iter=1800,solver='lbfgs'))])
    m.fit(np.asarray(X,float),np.asarray(y,int))
    p=m.predict_proba(np.asarray(te,float))[:,1];yy=np.asarray(yt,int)
    return {
      'month':mo,'variant':name,'n':len(yy),'auc':roc_auc_score(yy,p),
      'logloss':log_loss(yy,p,labels=[0,1]),'accuracy':accuracy_score(yy,(p>=.5).astype(int)),
      'train_n':len(y),'mean_p':float(p.mean())
    }

def main():
    base=read(SRC);extra,cov=reconstruct(base);out=[]
    for mo in TEST_MONTHS:
        for name,cols in VARIANTS.items():
            q=eval_month(base,extra,mo,name,cols)
            if q:out.append(q)
    fs=['month','variant','n','auc','logloss','accuracy','train_n','mean_p']
    with open(OUT,'w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fs);w.writeheader();w.writerows(out)
    L=['# v178 ③頭・事前展開特徴 ablation','',
       '- base / 選手style / 前走展示 / 両方を同一Jun-Aug OOSで比較。',
       '- 現在レースの展示は使用しない。実決まり手はtargetのみ。',
       '- 各月はその月より前だけで学習。','',
       '## coverage',f"- SRC matched: {cov['matched_src']}",f"- prior exhibition available: {cov['matched_prev_ex']}",'',
       '## Jun-Aug OOS','|month|variant|N|AUC|logloss|accuracy|train N|','|---|---|---:|---:|---:|---:|---:|']
    for r in out:
        L.append(f"|{r['month']}|{r['variant']}|{r['n']}|{r['auc']:.3f}|{r['logloss']:.3f}|{100*r['accuracy']:.1f}%|{r['train_n']}|")
    L+=['','## delta vs base','|month|variant|AUC差|logloss差|accuracy差|','|---|---|---:|---:|---:|']
    for mo in TEST_MONTHS:
        rr={r['variant']:r for r in out if r['month']==mo}
        b=rr.get('base')
        if not b:continue
        for name in ['style','prevex','both']:
            r=rr.get(name)
            if not r:continue
            L.append(f"|{mo}|{name}|{r['auc']-b['auc']:+.3f}|{r['logloss']-b['logloss']:+.3f}|{100*(r['accuracy']-b['accuracy']):+.1f}pt|")
    L+=['','## 判定ルール','- 3か月で一貫してAUC上昇かつlogloss悪化なしの特徴群を次段階のsoft-pair候補にする。','- 両方が最良でも、片方が無効なら不要特徴を落として過学習を抑える。','- Jun-Augを見て特徴定義や閾値を後付け調整しない。']
    open(SUMMARY,'w',encoding='utf-8').write('\n'.join(L)+'\n');print('\n'.join(L))
if __name__=='__main__':main()
