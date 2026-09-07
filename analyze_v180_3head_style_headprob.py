#!/usr/bin/env python3
"""v180: test whether no-leak racer-style features improve 3-head probability itself.

Compare strict Jun-Aug monthly walk-forward:
- v165 base feature set
- v180 base + racer-style features reconstructed by v177

No current-race exhibition and no current/future result-derived style state.
Thresholds are reported for comparison only; Jun-Aug is not used to tune a new production cut.
"""
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score,brier_score_loss,log_loss
from analyze_v165_3head_monthly_walkforward import load,target,feats,model,pc
from analyze_v166_3head_pair_direct import read
from analyze_v177_3head_historical_web_enrichment import reconstruct

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'analysis_v180_3head_style_headprob.csv'
SUMMARY=ROOT/'summary_v180_3head_style_headprob.md'
STYLE=['b1_hist_starts','b1_makurare_rate','b1_sasare_rate','b1_escape_rate','b3_hist_starts','b3_makuri_rate','b3_makuri_sashi_rate','b3_head_rate','style_makuri_edge','style_makurisashi_edge']
MONTHS=['2026-06','2026-07','2026-08']
CUTS=[.20,.25,.30,.35,.40]

def auc(y,p):
    try:return roc_auc_score(y,p) if len(set(y))>1 else np.nan
    except:return np.nan

def main():
    src,df=load(); dc=pc(df,['date','race_date','ymd']); vc=pc(df,['venue','jcd','stadium','place'])
    if not dc: raise SystemExit('no date col')
    y,td=target(df); basefs=feats(df)
    raw=read(str(src)); extra,cov=reconstruct(raw)
    if len(extra)!=len(df): raise SystemExit(f'reconstruct length mismatch {len(extra)} != {len(df)}')
    d=df.copy(); d['_date']=pd.to_datetime(d[dc].astype(str),errors='coerce'); d['_y']=y
    for k in STYLE:
        d[k]=[float(extra[i].get(k,0.0)) for i in range(len(df))]
    d=d[d._date.notna()&d._y.notna()].copy()
    rows=[]; metrics=[]
    for mon in MONTHS:
        m=pd.Timestamp(mon+'-01'); e=m+pd.offsets.MonthBegin(1)
        tr=d[d._date<m].copy(); te=d[(d._date>=m)&(d._date<e)].copy()
        for name,fs in [('base',basefs),('style',basefs+STYLE)]:
            nums=[]
            for c in fs:
                q=pd.to_numeric(d[c],errors='coerce')
                if q.notna().mean()>=.8:
                    tr[c]=pd.to_numeric(tr[c],errors='coerce');te[c]=pd.to_numeric(te[c],errors='coerce');nums.append(c)
            cats=[vc] if vc and vc not in nums else []
            mo=model(nums,cats);mo.fit(tr[nums+cats],tr._y.astype(int));p=mo.predict_proba(te[nums+cats])[:,1]; yy=te._y.astype(int).to_numpy()
            metrics.append({'month':mon,'variant':name,'n':len(te),'auc':auc(yy,p),'brier':brier_score_loss(yy,p),'logloss':log_loss(yy,p,labels=[0,1]),'mean_p':float(np.mean(p))})
            for ix,pr in zip(te.index,p):rows.append({'source_index':int(ix),'date':te.loc[ix,'_date'].strftime('%Y-%m-%d'),'month':mon,'variant':name,'p3head':float(pr),'y3head':int(te.loc[ix,'_y'])})
    od=pd.DataFrame(rows);od.to_csv(OUT,index=False)
    md=pd.DataFrame(metrics); L=['# v180 ③頭確率 racer-style OOS比較','', '- v165の③頭確率モデルに、v178で有効だったracer-style特徴だけを追加。','- styleは当該レースより前の履歴だけでrolling生成。現在レース展示は不使用。','- Jun-Aug各月はその月より前だけで学習。Jun-Augを見て閾値を最適化しない。','',f"- reconstruction matched: {cov['matched_src']}",'','## Monthly OOS','|month|variant|R|AUC|Brier|logloss|','|---|---|---:|---:|---:|---:|']
    for _,r in md.iterrows():L.append(f"|{r.month}|{r.variant}|{int(r.n)}|{r.auc:.4f}|{r.brier:.5f}|{r.logloss:.5f}|")
    L+=['','## Delta style - base','|month|AUC差|Brier差|logloss差|','|---|---:|---:|---:|']
    for mon in MONTHS:
        q=md[md.month==mon].set_index('variant');b=q.loc['base'];s=q.loc['style'];L.append(f"|{mon}|{s.auc-b.auc:+.4f}|{s.brier-b.brier:+.5f}|{s.logloss-b.logloss:+.5f}|")
    L+=['','## Threshold diagnostics','|cut|variant|R|③頭率|','|---:|---|---:|---:|']
    for cut in CUTS:
        for name in ['base','style']:
            q=od[(od.variant==name)&(od.p3head>=cut)];L.append(f"|{cut:.2f}|{name}|{len(q)}|{100*q.y3head.mean():.2f}%|" if len(q) else f"|{cut:.2f}|{name}|0|-|")
    L+=['','## Decision rule','- AUC上昇に加えBrier/loglossと月別安定性を確認する。','- p>=0.30の③頭率だけを見て採用しない。','- Jun-Augで一貫改善なら、別の事前期間でcutを固定してからROI検証へ進む。']
    SUMMARY.write_text('\n'.join(L)+'\n',encoding='utf-8');print('\n'.join(L))
if __name__=='__main__':main()
