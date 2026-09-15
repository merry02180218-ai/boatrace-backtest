#!/usr/bin/env python3
"""4-head causal player-strength threshold Pareto study.

- Fixed 4v3 motor gate remains unchanged.
- player4_all_win is rebuilt prior-only by the imported causal day-walk.
- Threshold grid is derived from Apr-Jun only.
- Representative thresholds are selected from Apr-Jun only; Jul-Aug is evaluation only.
- September outcomes are never read; production is untouched.
"""
from pathlib import Path
import numpy as np
import pandas as pd
from analyze_4head_headrate_3ren_player_st import base_rows, TRAIN, HOLD, met, month_counts

ROOT=Path(__file__).resolve().parent
GRID=ROOT/'analysis_4head_player_all_win_pareto.csv'
SUMMARY=ROOT/'summary_4head_player_all_win_pareto.md'


def metrics(q):
    x=met(q)
    x['months']=month_counts(q)
    return x


def main():
    z=base_rows()
    tr=z[z.month.isin(TRAIN)].copy(); ho=z[z.month.isin(HOLD)].copy()
    s=pd.to_numeric(tr.player4_all_win,errors='coerce').dropna()
    # Train-only threshold family: empirical quantiles plus previous selected cut.
    qs=np.arange(0.05,0.61,0.025)
    cuts=sorted(set([float(s.quantile(q)) for q in qs]+[0.230699]))
    rec=[]
    for cut in cuts:
        qt=tr[pd.to_numeric(tr.player4_all_win,errors='coerce')>=cut]
        if len(qt)<35: continue
        mt=metrics(qt)
        rec.append({'cut':cut,'train_R':mt['R'],'train_head':mt['head4'],'train_head_rate':mt['head4_rate'],
                    'train_months':mt['months']})
    g=pd.DataFrame(rec).sort_values('cut').reset_index(drop=True)
    # Pareto in train space: no other candidate may have >=R and >=head-rate with one strict.
    pareto=[]
    for i,r in g.iterrows():
        dom=((g.train_R>=r.train_R)&(g.train_head_rate>=r.train_head_rate)&
             ((g.train_R>r.train_R)|(g.train_head_rate>r.train_head_rate))).any()
        pareto.append(not dom)
    g['train_pareto']=pareto

    # Fix representative candidates BEFORE holdout: volume, balance, head-rate.
    p=g[g.train_pareto].copy()
    reps=[]
    if len(p):
        reps.append(p.sort_values(['train_R','train_head_rate'],ascending=[False,False]).index[0])
        # balance: closest train R to 70, tie higher head rate
        reps.append(p.assign(dist=(p.train_R-70).abs()).sort_values(['dist','train_head_rate'],ascending=[True,False]).index[0])
        reps.append(p.sort_values(['train_head_rate','train_R'],ascending=[False,False]).index[0])
    reps=list(dict.fromkeys(reps))
    g['representative']=False
    for i in reps:g.loc[i,'representative']=True

    # Holdout is evaluated for every pre-specified threshold only after train frontier/reps are fixed.
    holdR=[];holdH=[];holdRate=[];holdMonths=[];totalR=[];totalH=[];totalRate=[]
    for _,r in g.iterrows():
        cut=r.cut
        qh=ho[pd.to_numeric(ho.player4_all_win,errors='coerce')>=cut]
        mh=metrics(qh)
        qt=z[z.month.isin(TRAIN+HOLD) & (pd.to_numeric(z.player4_all_win,errors='coerce')>=cut)]
        ma=metrics(qt)
        holdR.append(mh['R']);holdH.append(mh['head4']);holdRate.append(mh['head4_rate']);holdMonths.append(mh['months'])
        totalR.append(ma['R']);totalH.append(ma['head4']);totalRate.append(ma['head4_rate'])
    g['hold_R']=holdR;g['hold_head']=holdH;g['hold_head_rate']=holdRate;g['hold_months']=holdMonths
    g['total_R']=totalR;g['total_head']=totalH;g['total_head_rate']=totalRate
    g.to_csv(GRID,index=False)

    L=['# 4号艇 player4_all_win 閾値 Pareto','',
       '- fixed motor baseは変更なし。追加条件はprior-only `player4_all_win` 単独。',
       '- 閾値集合・Pareto・代表候補はApr-Junだけで固定。Jul-Augはその後に一括評価し、holdoutで閾値を選び直さない。',
       '- September outcomesはUNREAD。production `HEAD4_V291_COMP7` は変更しない。','',
       '## Train Pareto + fixed representatives','',
       '|cut|Apr-Jun R|Apr-Jun頭率|Apr-Jun月別|Jul-Aug R|Jul-Aug頭率|Jul-Aug月別|Apr-Aug R|Apr-Aug頭率|代表|',
       '|---:|---:|---:|---|---:|---:|---|---:|---:|---|']
    show=g[g.train_pareto | g.representative].sort_values('cut')
    for _,r in show.iterrows():
        L.append(f"|{r.cut:.6f}|{int(r.train_R)}|{100*r.train_head_rate:.2f}%|{r.train_months}|{int(r.hold_R)}|{100*r.hold_head_rate:.2f}%|{r.hold_months}|{int(r.total_R)}|{100*r.total_head_rate:.2f}%|{'YES' if r.representative else ''}|")
    L += ['','## Interpretation',
          '- 正式候補はholdoutの数字だけで選ばない。代表候補3点はApr-Junだけで事前固定した比較点。',
          '- 100〜150Rかつ35%近辺以上に入る点があれば、次段階でそのtrain-only代表条件を独立再現監査する。',
          '- 条件が足りなければ、次に軽いsecondary gateをApr-Junだけで追加研究する。']
    SUMMARY.write_text('\n'.join(L)+'\n',encoding='utf-8')
    print('\n'.join(L))

if __name__=='__main__':main()
