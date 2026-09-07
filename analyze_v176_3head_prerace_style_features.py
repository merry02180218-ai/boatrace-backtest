#!/usr/bin/env python3
"""v176: build no-leak pre-race style features for 3-head development prediction.

Goal:
- Use only information knowable before the race.
- Build rolling historical style rates for boat1/boat3 racers from PRIOR races only:
  * boat1 makurare / sasare proxy rates
  * boat3 makuri / makuri-sashi win rates
- Auto-detect racer-id and previous/exhibition-related columns where possible.
- Evaluate whether makuri vs makuri-sashi can be separated OOS (Jun-Aug 2026).

Important:
- Current-race kimarite is used only as the target label.
- Rolling style rates are calculated using strictly earlier dates/rows.
- If racer identifiers are unavailable in SRC, script reports that clearly and falls back to existing v175 race features only.
"""
from __future__ import annotations
import csv, math, re
from collections import defaultdict, Counter
from datetime import date
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score, log_loss, accuracy_score
from analyze_v166_3head_pair_direct import read, ff, ii, combo, SRC, VENUES
from analyze_v175_3head_prerace_development_softpair import race_feat, method

OUT='analysis_v176_3head_prerace_style_features.csv'
SUMMARY='summary_v176_3head_prerace_style_features.md'
TEST_MONTHS=['2026-06','2026-07','2026-08']

ID_ALIASES={
  1:['racer1','player1','player_id1','racer_id1','registration1','regno1','boat1_racer','boat1_player','entry1','teiban1'],
  3:['racer3','player3','player_id3','racer_id3','registration3','regno3','boat3_racer','boat3_player','entry3','teiban3'],
}
EX_PATTERNS=[
 'prev_ex','previous_ex','prev_tenji','previous_tenji','last_ex','last_tenji',
 'prev_original','previous_original','last_original','orig_prev','tenji_prev',
 'prev_straight','prev_turn','prev_lap','previous_straight','previous_turn','previous_lap'
]

def detect_col(fields, aliases):
    low={f.lower():f for f in fields}
    for a in aliases:
        if a.lower() in low:return low[a.lower()]
    # fuzzy normalized exact-ish
    norm=lambda s:re.sub(r'[^a-z0-9]','',s.lower())
    m={norm(f):f for f in fields}
    for a in aliases:
        if norm(a) in m:return m[norm(a)]
    return ''

def detect_ex_cols(fields):
    z=[]
    for f in fields:
        lf=f.lower()
        if any(p in lf for p in EX_PATTERNS):z.append(f)
    return z[:30]

def racer_key(r,col):
    return str(r.get(col,'')).strip() if col else ''

def target(r):
    m=method(r)
    if m=='makuri':return 0
    if m=='makuri-sashi':return 1
    return None

def rolling_style(rows,id1,id3):
    # stats are updated only after feature extraction => no current-row leakage.
    st1=defaultdict(lambda:Counter(starts=0,makurare=0,sasare=0))
    st3=defaultdict(lambda:Counter(starts=0,makuri=0,makuri_sashi=0,head3=0))
    feats={}
    order=sorted(enumerate(rows),key=lambda x:(x[1].get('date',''),x[0]))
    for idx,r in order:
        k1=racer_key(r,id1);k3=racer_key(r,id3)
        a=combo(r.get('actual_combo'));m=method(r)
        f={}
        if k1:
            q=st1[k1];d=max(q['starts'],1)
            f['b1_hist_starts']=q['starts'];f['b1_makurare_rate']=q['makurare']/d;f['b1_sasare_rate']=q['sasare']/d
        else:
            f['b1_hist_starts']=0;f['b1_makurare_rate']=0.;f['b1_sasare_rate']=0.
        if k3:
            q=st3[k3];d=max(q['starts'],1)
            f['b3_hist_starts']=q['starts'];f['b3_makuri_rate']=q['makuri']/d;f['b3_makuri_sashi_rate']=q['makuri_sashi']/d;f['b3_head3_rate']=q['head3']/d
        else:
            f['b3_hist_starts']=0;f['b3_makuri_rate']=0.;f['b3_makuri_sashi_rate']=0.;f['b3_head3_rate']=0.
        f['style_makuri_edge']=f['b3_makuri_rate']-f['b1_makurare_rate']
        f['style_makurisashi_edge']=f['b3_makuri_sashi_rate']-f['b1_sasare_rate']
        feats[idx]=f
        # update from this completed race only for later rows
        if ii(r.get('valid_result'))==1 and len(a)==3:
            if k1:
                q=st1[k1];q['starts']+=1
                if a[0]!=1:
                    if m=='makuri':q['makurare']+=1
                    if m in ('makuri-sashi','sashi-other'):q['sasare']+=1
            if k3:
                q=st3[k3];q['starts']+=1
                if a[0]==3:q['head3']+=1
                if a[0]==3 and m=='makuri':q['makuri']+=1
                if a[0]==3 and m=='makuri-sashi':q['makuri_sashi']+=1
    return feats

def xvec(r,sty,ex_cols):
    x=list(race_feat(r))
    x += [sty[k] for k in ['b1_hist_starts','b1_makurare_rate','b1_sasare_rate','b3_hist_starts','b3_makuri_rate','b3_makuri_sashi_rate','b3_head3_rate','style_makuri_edge','style_makurisashi_edge']]
    # only use columns that are explicitly previous/last-race style; current exhibition columns are never auto-added.
    for c in ex_cols:x.append(ff(r.get(c)))
    return x

def fit_predict(rows,styles,ex_cols,month):
    first=date.fromisoformat(month+'-01')
    X=[];y=[]
    for i,r in enumerate(rows):
        if date.fromisoformat(r['date'])>=first:continue
        if ii(r.get('valid_result'))!=1:continue
        a=combo(r.get('actual_combo'));t=target(r)
        if len(a)!=3 or a[0]!=3 or t is None:continue
        X.append(xvec(r,styles[i],ex_cols));y.append(t)
    te=[];yt=[]
    for i,r in enumerate(rows):
        if r.get('month')!=month or ii(r.get('valid_result'))!=1:continue
        a=combo(r.get('actual_combo'));t=target(r)
        if len(a)!=3 or a[0]!=3 or t is None:continue
        te.append((i,r));yt.append(t)
    if len(X)<300 or len(set(y))<2 or len(te)<5:return None
    mdl=Pipeline([('s',StandardScaler()),('m',LogisticRegression(C=.25,max_iter=1800,solver='lbfgs'))])
    mdl.fit(np.asarray(X,float),np.asarray(y,int))
    p=mdl.predict_proba(np.asarray([xvec(r,styles[i],ex_cols) for i,r in te],float))[:,1]
    yy=np.asarray(yt,int)
    auc=roc_auc_score(yy,p) if len(set(yt))>1 else float('nan')
    ll=log_loss(yy,p,labels=[0,1]);acc=accuracy_score(yy,(p>=.5).astype(int))
    return dict(month=month,n=len(yy),makuri=int((yy==0).sum()),makuri_sashi=int((yy==1).sum()),auc=auc,logloss=ll,accuracy=acc,train_n=len(y),mean_p=float(p.mean()))

def main():
    rows=read(SRC)
    fields=list(rows[0].keys()) if rows else []
    id1=detect_col(fields,ID_ALIASES[1]);id3=detect_col(fields,ID_ALIASES[3]);ex_cols=detect_ex_cols(fields)
    styles=rolling_style(rows,id1,id3)
    res=[]
    for mo in TEST_MONTHS:
        q=fit_predict(rows,styles,ex_cols,mo)
        if q:res.append(q)
    fs=['month','n','makuri','makuri_sashi','auc','logloss','accuracy','train_n','mean_p']
    with open(OUT,'w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fs);w.writeheader();w.writerows(res)
    L=['# v176 ③頭・事前展開専用特徴 診断','',
       '- 現在レースの直前展示は使わない。','- 実決まり手は目的変数だけ。','- 選手スタイル率はそのレースより前の履歴だけでrolling生成。','',
       '## 自動検出','',f'- ①選手ID列: `{id1 or "NOT FOUND"}`',f'- ③選手ID列: `{id3 or "NOT FOUND"}`',f'- 前走展示/オリ展候補列: {ex_cols if ex_cols else "NOT FOUND"}','',
       '## Jun-Aug OOS: まくり vs まくり差し','|month|N|まくり|まくり差し|AUC|logloss|accuracy|train N|','|---|---:|---:|---:|---:|---:|---:|---:|']
    for r in res:L.append(f"|{r['month']}|{r['n']}|{r['makuri']}|{r['makuri_sashi']}|{r['auc']:.3f}|{r['logloss']:.3f}|{100*r['accuracy']:.1f}%|{r['train_n']}|")
    if not res:L += ['','**評価不能:** 必要なラベル/件数または入力列が不足。']
    L += ['','## 判定メモ','- AUCが月別で安定して0.60以上なら、事前候補段階で展開タイプをsoftに使う価値あり。','- 0.55前後なら単独判定には弱い。選手IDや前走展示列がNOT FOUNDなら、次にそのデータをhistorical sourceへ追加するのが優先。','- ①まくられ/差され率は現データ上の決まり手から作るproxy。公式/専門サイトのコース別率が取得できるなら将来はそちらを優先。']
    open(SUMMARY,'w',encoding='utf-8').write('\n'.join(L)+'\n')
    print('\n'.join(L))

if __name__=='__main__':main()
