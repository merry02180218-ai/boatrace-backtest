#!/usr/bin/env python3
"""4号艇頭確率: 厳密な未来情報混入監査。9月結果はアクセス禁止。"""
from __future__ import annotations
from io import StringIO
from pathlib import Path
import math, requests
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

OUT=Path('/tmp/head4_boatracecsv_leakage_audit'); OUT.mkdir(parents=True,exist_ok=True)
BASE='https://boatracecsv.github.io/data'
START=pd.Timestamp('2026-04-01'); END=pd.Timestamp('2026-08-31')
TRAIN_MONTHS={'2026-04','2026-05','2026-06'}; VALID_MONTHS={'2026-07','2026-08'}
CUTS=[round(x,2) for x in np.arange(.10,.601,.01)]
RNG=np.random.default_rng(20260917)

def get_csv(kind,d):
    if d>=pd.Timestamp('2026-09-01'): raise RuntimeError('9月アクセス禁止')
    r=requests.get(f'{BASE}/{kind}/{d:%Y/%m/%d}.csv',timeout=20)
    if r.status_code==404:return pd.DataFrame()
    r.raise_for_status(); return pd.read_csv(StringIO(r.text))

def pick_col(df,*needles):
    for c in df.columns:
        s=str(c).lower()
        if all(n.lower() in s for n in needles):return c
    return None

def boat_col(df,b,*needles):
    tags=[f'艇{b}',f'{b}枠',f'{b}号艇']
    for c in df.columns:
        s=str(c)
        if any(t in s for t in tags) and all(n.lower() in s.lower() for n in needles):return c
    return None

def num(v):
    try:
        x=float(v); return x if math.isfinite(x) else np.nan
    except:return np.nan

def build():
    rows=[]; raw_names=set()
    for d in pd.date_range(START,END,freq='D'):
        cards=get_csv('programs/race_cards',d); results=get_csv('results/realtime',d)
        if cards.empty or results.empty:continue
        rc=pick_col(cards,'レース','コード') or pick_col(cards,'race','code')
        rr=pick_col(results,'レース','コード') or pick_col(results,'race','code')
        win=pick_col(results,'1着','艇') or pick_col(results,'winner')
        if not rc or not rr or not win:continue
        rmap={str(x[rr]).zfill(12):x for _,x in results.iterrows()}
        for _,x in cards.iterrows():
            code=str(x[rc]).zfill(12); y=rmap.get(code)
            if y is None:continue
            row={'date':str(d.date()),'month':d.strftime('%Y-%m'),'race_code':code,'head4':int(num(y[win])==4)}
            for b in range(1,7):
                specs={'national_win':['全国','勝率'],'national_top2':['全国','2連'],'national_top3':['全国','3連'],
                       'local_win':['当地','勝率'],'local_top2':['当地','2連'],'local_top3':['当地','3連'],
                       'motor_top2':['モーター','2連'],'motor_top3':['モーター','3連'],
                       'boat_top2':['ボート','2連'],'boat_top3':['ボート','3連'],'avg_st':['平均','ST'],'flying':['F'],'late':['L']}
                for name,need in specs.items():
                    c=boat_col(cards,b,*need)
                    if c: raw_names.add(str(c))
                    row[f'b{b}_{name}']=num(x[c]) if c else np.nan
            rows.append(row)
    z=pd.DataFrame(rows)
    if z.empty:raise RuntimeError('データなし')
    pd.DataFrame({'race_card元列':sorted(raw_names)}).to_csv(OUT/'race_card_raw_columns.csv',index=False)
    return z

def model():
    return Pipeline([('欠損補完',SimpleImputer(strategy='median')),('標準化',StandardScaler()),('ロジスティック回帰',LogisticRegression(max_iter=2000,C=.5))])

def sweep(df,label):
    out=[]
    for c in CUTS:
        s=df[df.head_prob>=c]
        out.append({'基準値':c,'期間':label,'レース数':len(s),'4号艇1着数':int(s.head4.sum()),'4号艇1着率':100*s.head4.mean() if len(s) else np.nan,'対象率':100*len(s)/len(df)})
    return out

def main():
    z=build(); tr=z[z.month.isin(TRAIN_MONTHS)].copy(); va=z[z.month.isin(VALID_MONTHS)].copy()
    if set(tr.race_code)&set(va.race_code):raise RuntimeError('学習と検証でレースキー重複')
    if z.race_code.duplicated().any():raise RuntimeError('全体でレースキー重複')
    # 重要: 使用項目の選定も学習期間だけを見る。
    candidate=[c for c in z.columns if c.startswith('b')]
    feats=[c for c in candidate if tr[c].notna().sum()>=max(50,int(.25*len(tr)))]
    forbidden=[c for c in feats if any(x in c.lower() for x in ['head4','result','winner','着順','払戻','odds','オッズ','展示','直前'])]
    if forbidden:raise RuntimeError('禁止項目が学習行列に混入: '+','.join(forbidden))
    m=model(); m.fit(tr[feats],tr.head4)
    tr['head_prob']=m.predict_proba(tr[feats])[:,1]; va['head_prob']=m.predict_proba(va[feats])[:,1]
    rows=sweep(tr,'4〜6月 学習期間')+sweep(va,'7〜8月 未使用検証期間')
    pd.DataFrame(rows).to_csv(OUT/'corrected_threshold_sweep.csv',index=False)
    # 負の対照: 正解をランダム化して学習。高性能なら異常。
    neg=[]
    for i in range(10):
        yy=RNG.permutation(tr.head4.to_numpy()); mm=model(); mm.fit(tr[feats],yy)
        p=mm.predict_proba(va[feats])[:,1]
        auc=roc_auc_score(va.head4,p)
        top=va.assign(p=p).sort_values('p',ascending=False).head(max(100,int(.05*len(va))))
        neg.append({'反復':i+1,'AUC':auc,'上位群レース数':len(top),'上位群4号艇1着率':100*top.head4.mean()})
    pd.DataFrame(neg).to_csv(OUT/'shuffled_target_negative_control.csv',index=False)
    auc=roc_auc_score(va.head4,va.head_prob)
    audit=pd.DataFrame([
      {'監査項目':'使用項目の選定','結果':'合格','詳細':'4〜6月だけで欠損率判定'},
      {'監査項目':'欠損補完・標準化・学習','結果':'合格','詳細':'4〜6月だけでfit'},
      {'監査項目':'7〜8月の利用','結果':'合格','詳細':'predictのみ。学習・前処理fitに不使用'},
      {'監査項目':'結果列の学習混入','結果':'合格','詳細':'結果はhead4正解ラベル作成だけ'},
      {'監査項目':'レースキー重複','結果':'合格','詳細':'学習/検証および全体で重複なし'},
      {'監査項目':'9月','結果':'合格','詳細':'コードでアクセス禁止'},
      {'監査項目':'使用項目数','結果':'情報','詳細':str(len(feats))},
      {'監査項目':'未使用検証期間AUC','結果':'情報','詳細':f'{auc:.6f}'},
      {'監査項目':'ランダム正解AUC平均','結果':'情報','詳細':f'{pd.DataFrame(neg).AUC.mean():.6f}'},
    ])
    audit.to_csv(OUT/'leakage_audit_summary.csv',index=False)
    pd.DataFrame({'使用項目':feats}).to_csv(OUT/'training_only_features.csv',index=False)
    pd.concat([tr,va]).to_csv(OUT/'corrected_scored_races.csv',index=False)
    print('4号艇頭確率_未来情報混入監査_OK')
    print('学習',len(tr),int(tr.head4.sum()),'未使用検証',len(va),int(va.head4.sum()),'使用項目',len(feats))
    print('未使用検証AUC',round(auc,6),'ランダム正解AUC平均',round(pd.DataFrame(neg).AUC.mean(),6))
    print(pd.DataFrame(rows).query('基準値 in [0.25,0.28,0.30,0.32,0.35,0.40]').to_string(index=False))
    print('9月_UNREAD')
    print('本番変更なし')
if __name__=='__main__':main()
