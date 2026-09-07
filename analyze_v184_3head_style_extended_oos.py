#!/usr/bin/env python3
"""v184: extended historical OOS stress test of v180 racer-style features.

Goal: actively try to falsify v180, not confirm it.
- Compare v165 base vs v180 base+STYLE over Jan-Aug 2026.
- Strict monthly walk-forward: each test month trains only on prior dates.
- Racer-style state is reconstructed from PRIOR completed races only via v177.
- No current-race exhibition or future/result leakage into features.
- No threshold/ROI tuning here; this is probability-model robustness only.
"""
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score,brier_score_loss,log_loss

from analyze_v165_3head_monthly_walkforward import load,target,feats,model,pc
from analyze_v166_3head_pair_direct import read
from analyze_v177_3head_historical_web_enrichment import reconstruct

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'analysis_v184_3head_style_extended_oos.csv'
SUMMARY=ROOT/'summary_v184_3head_style_extended_oos.md'
STYLE=['b1_hist_starts','b1_makurare_rate','b1_sasare_rate','b1_escape_rate',
       'b3_hist_starts','b3_makuri_rate','b3_makuri_sashi_rate','b3_head_rate',
       'style_makuri_edge','style_makurisashi_edge']
MONTHS=[f'2026-{m:02d}' for m in range(1,9)]


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
    for k in STYLE:d[k]=[float(extra[i].get(k,0.0)) for i in range(len(df))]
    d=d[d._date.notna()&d._y.notna()].copy()

    rows=[]; metrics=[]
    for mon in MONTHS:
        m=pd.Timestamp(mon+'-01'); e=m+pd.offsets.MonthBegin(1)
        tr=d[d._date<m].copy(); te=d[(d._date>=m)&(d._date<e)].copy()
        if len(tr)<200 or len(te)<20 or tr._y.nunique()<2: continue
        for name,fs in [('base',basefs),('style',basefs+STYLE)]:
            nums=[]
            for c in fs:
                q=pd.to_numeric(d[c],errors='coerce')
                if q.notna().mean()>=.8:
                    tr[c]=pd.to_numeric(tr[c],errors='coerce');te[c]=pd.to_numeric(te[c],errors='coerce');nums.append(c)
            cats=[vc] if vc and vc not in nums else []
            mo=model(nums,cats); mo.fit(tr[nums+cats],tr._y.astype(int))
            p=mo.predict_proba(te[nums+cats])[:,1]; yy=te._y.astype(int).to_numpy()
            metrics.append({'month':mon,'variant':name,'n':len(te),'train_n':len(tr),
                            'auc':auc(yy,p),'brier':brier_score_loss(yy,p),
                            'logloss':log_loss(yy,p,labels=[0,1]),'mean_p':float(np.mean(p))})
            for ix,pr in zip(te.index,p):
                rows.append({'source_index':int(ix),'date':te.loc[ix,'_date'].strftime('%Y-%m-%d'),
                             'month':mon,'variant':name,'p3head':float(pr),'y3head':int(te.loc[ix,'_y']),
                             'b1_hist_starts':float(te.loc[ix,'b1_hist_starts']),
                             'b3_hist_starts':float(te.loc[ix,'b3_hist_starts'])})

    od=pd.DataFrame(rows); md=pd.DataFrame(metrics)
    if od.empty or md.empty: raise SystemExit('no OOS rows')
    od.to_csv(OUT,index=False)

    L=['# v184 v180 racer-style extended historical OOS stress test','',
       '- v180を疑うための長期再検証。Jan-Aug 2026を月別walk-forwardでbase vs style比較。',
       '- 各月はその月より前のデータだけで学習。styleは当該レースより前の完了レースだけでrolling生成。',
       '- 現在レース展示は不使用。閾値・ROIはここでは最適化しない。',
       f"- reconstruction matched: {cov['matched_src']}",'',
       '## Monthly OOS','|month|variant|R|train R|AUC|Brier|logloss|','|---|---|---:|---:|---:|---:|---:|']
    for _,r in md.iterrows():
        L.append(f"|{r.month}|{r.variant}|{int(r.n)}|{int(r.train_n)}|{r.auc:.4f}|{r.brier:.5f}|{r.logloss:.5f}|")

    L+=['','## Delta style - base','|month|AUC差|Brier差|logloss差|判定|','|---|---:|---:|---:|---|']
    wins=0; tested=0
    for mon in MONTHS:
        q=md[md.month==mon].set_index('variant')
        if not {'base','style'}.issubset(q.index): continue
        b=q.loc['base'];s=q.loc['style']; da=s.auc-b.auc; db=s.brier-b.brier; dl=s.logloss-b.logloss
        ok=(da>0 and db<0 and dl<0); wins+=int(ok); tested+=1
        L.append(f"|{mon}|{da:+.4f}|{db:+.5f}|{dl:+.5f}|{'3指標改善' if ok else '不一致/悪化'}|")

    # Aggregate metrics over identical OOS rows, preserving monthly predictions.
    L+=['','## Aggregate Jan-Aug OOS','|variant|R|AUC|Brier|logloss|','|---|---:|---:|---:|---:|']
    for name in ['base','style']:
        q=od[od.variant==name]
        L.append(f"|{name}|{len(q)}|{auc(q.y3head,q.p3head):.4f}|{brier_score_loss(q.y3head,q.p3head):.5f}|{log_loss(q.y3head,q.p3head,labels=[0,1]):.5f}|")

    # Maturity stress: does style only work after enough prior starts?
    L+=['','## Style-history maturity stress','|min prior starts (both 1&3)|R|base AUC|style AUC|AUC差|','|---:|---:|---:|---:|---:|']
    b=od[od.variant=='base'].set_index('source_index'); s=od[od.variant=='style'].set_index('source_index')
    common=b.index.intersection(s.index)
    for cut in [0,3,5,10,15,20]:
        idx=[i for i in common if min(s.loc[i,'b1_hist_starts'],s.loc[i,'b3_hist_starts'])>=cut]
        if len(idx)<50: continue
        yv=s.loc[idx,'y3head']; ba=auc(yv,b.loc[idx,'p3head']); sa=auc(yv,s.loc[idx,'p3head'])
        L.append(f"|{cut}|{len(idx)}|{ba:.4f}|{sa:.4f}|{sa-ba:+.4f}|")

    L+=['','## Falsification rule',
        f'- 3指標（AUC↑・Brier↓・logloss↓）が同時改善した月: {wins}/{tested}.',
        '- 6/8以上かつaggregateでも3指標改善なら「長期でも有効」の根拠。',
        '- 4/8以下、aggregate悪化、または成熟履歴だけで改善が消えるならv180は弱い/不安定と判定。',
        '- Jun-Augだけ良く、Jan-Mayで崩れる場合はv180の期間依存を疑い、production利用はしない。']
    SUMMARY.write_text('\n'.join(L)+'\n',encoding='utf-8'); print('\n'.join(L))

if __name__=='__main__':main()
