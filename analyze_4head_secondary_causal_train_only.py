#!/usr/bin/env python3
"""4-head secondary causal gate study.

- Fixed motor base comes from base_rows().
- Primary player4_all_win cuts are pre-fixed at 0.210863 and 0.215605.
- Secondary thresholds are derived from Apr-Jun only.
- Secondary features are prior-only motor_3ren_diff_4v3, player4_recent_p2,
  and player4_frame4_win. ST is intentionally excluded pending lineage audit.
- Representatives are selected from Apr-Jun only; Jul-Aug is evaluation only.
- September outcomes are never read; production is untouched.
"""
from pathlib import Path
import numpy as np
import pandas as pd
from analyze_4head_headrate_3ren_player_st import base_rows, TRAIN, HOLD, met, month_counts

ROOT=Path(__file__).resolve().parent
GRID=ROOT/'analysis_4head_secondary_causal_train_only.csv'
SUMMARY=ROOT/'summary_4head_secondary_causal_train_only.md'
PRIMARY=(0.210863,0.215605)
FEATURES=('motor_3ren_diff_4v3','player4_recent_p2','player4_frame4_win')
MIN_R=38


def metrics(q):
    x=met(q); x['months']=month_counts(q)
    rates=[float(g.actual_head4.mean()) for _,g in q.groupby('month') if len(g)]
    x['month_floor']=min(rates) if rates else np.nan
    return x


def main():
    z=base_rows()
    tr=z[z.month.isin(TRAIN)].copy(); ho=z[z.month.isin(HOLD)].copy()
    rec=[]
    for pc in PRIMARY:
        bt=tr[pd.to_numeric(tr.player4_all_win,errors='coerce')>=pc].copy()
        for feat in FEATURES:
            s=pd.to_numeric(bt[feat],errors='coerce').dropna()
            if s.empty: continue
            # Train-only mild-to-moderate gates; no holdout-derived cuts.
            cuts=sorted(set(float(s.quantile(q)) for q in np.arange(.10,.56,.05)))
            for cut in cuts:
                qt=bt[pd.to_numeric(bt[feat],errors='coerce')>=cut]
                if len(qt)<MIN_R: continue
                m=metrics(qt)
                rec.append({'primary_cut':pc,'feature':feat,'secondary_cut':cut,
                    'train_R':m['R'],'train_head':m['head4'],'train_head_rate':m['head4_rate'],
                    'train_month_floor':m['month_floor'],'train_months':m['months']})
    g=pd.DataFrame(rec)
    if g.empty: raise RuntimeError('no eligible secondary gates')
    # Train-only Pareto: maximize R, aggregate head rate, and weakest-month head rate.
    pareto=[]
    for _,r in g.iterrows():
        dom=((g.train_R>=r.train_R)&(g.train_head_rate>=r.train_head_rate)&
             (g.train_month_floor>=r.train_month_floor)&
             ((g.train_R>r.train_R)|(g.train_head_rate>r.train_head_rate)|(g.train_month_floor>r.train_month_floor))).any()
        pareto.append(not dom)
    g['train_pareto']=pareto
    p=g[g.train_pareto].copy()
    # Representatives fixed before holdout: volume, balanced target, head-rate.
    reps=[]
    if len(p):
        reps.append(p.sort_values(['train_R','train_head_rate','train_month_floor'],ascending=False).index[0])
        eligible=p[p.train_head_rate>=.35]
        if len(eligible):
            reps.append(eligible.sort_values(['train_R','train_month_floor','train_head_rate'],ascending=False).index[0])
        else:
            reps.append(p.sort_values(['train_head_rate','train_R','train_month_floor'],ascending=False).index[0])
        reps.append(p.sort_values(['train_month_floor','train_head_rate','train_R'],ascending=False).index[0])
    reps=list(dict.fromkeys(reps)); g['representative']=False
    for i in reps: g.loc[i,'representative']=True

    # Holdout only after representatives are frozen.
    vals=[]
    for _,r in g.iterrows():
        def filt(df):
            return df[(pd.to_numeric(df.player4_all_win,errors='coerce')>=r.primary_cut) &
                      (pd.to_numeric(df[r.feature],errors='coerce')>=r.secondary_cut)]
        mh=metrics(filt(ho)); ma=metrics(filt(z[z.month.isin(TRAIN+HOLD)]))
        vals.append((mh['R'],mh['head4'],mh['head4_rate'],mh['months'],ma['R'],ma['head4'],ma['head4_rate']))
    g[['hold_R','hold_head','hold_head_rate','hold_months','total_R','total_head','total_head_rate']]=pd.DataFrame(vals,index=g.index)
    g=g.sort_values(['train_pareto','representative','train_head_rate','train_R'],ascending=[False,False,False,False])
    g.to_csv(GRID,index=False)

    L=['# 4号艇 secondary causal gate — train-only research','',
       '- primary cuts: `player4_all_win >= 0.210863` / `>= 0.215605` (pre-fixed).',
       '- secondary: motor 3連対率差 / recent top2 / frame4 win only; all prior-only.',
       '- ST excluded pending independent lineage audit.',
       '- cuts/Pareto/representatives are Apr-Jun only. Jul-Aug evaluated afterwards.',
       '- September outcomes UNREAD; production `HEAD4_V291_COMP7` untouched.','',
       '## Train Pareto / representatives','',
       '|primary|secondary|cut|Apr-Jun R|頭率|最低月頭率|月別|Jul-Aug R|頭率|月別|Apr-Aug R|頭率|rep|',
       '|---:|---|---:|---:|---:|---:|---|---:|---:|---|---:|---:|---|']
    show=g[g.train_pareto | g.representative].sort_values(['primary_cut','feature','secondary_cut'])
    for _,r in show.iterrows():
        L.append(f"|{r.primary_cut:.6f}|{r.feature}|{r.secondary_cut:.6f}|{int(r.train_R)}|{100*r.train_head_rate:.2f}%|{100*r.train_month_floor:.2f}%|{r.train_months}|{int(r.hold_R)}|{100*r.hold_head_rate:.2f}%|{r.hold_months}|{int(r.total_R)}|{100*r.total_head_rate:.2f}%|{'YES' if r.representative else ''}|")
    L += ['','## Guardrail','- Holdout results do not alter the representative selection.','- This research does not modify production.']
    SUMMARY.write_text('\n'.join(L)+'\n',encoding='utf-8')
    print('\n'.join(L))

if __name__=='__main__': main()
