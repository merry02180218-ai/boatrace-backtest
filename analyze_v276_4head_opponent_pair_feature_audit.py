#!/usr/bin/env python3
"""v276: direct ordered-pair feature audit for 4-head opponent selection.

Instead of ranking 2nd and 3rd independently, learn the ordered pair 4-s-t
conditional on historical boat-4 wins.  This allows position, role differences,
and attack-shape interactions to influence the pair ordering.

Strict research discipline:
- 2026-07/08 excluded; September not read.
- Every evaluation month trains only on earlier boat-4-win races.
- No odds in features/ranking.
- v268/v273 head selectors unchanged; S+A is only a reporting slice.
- Outcome fields are labels only, never candidate features.
"""
from __future__ import annotations
from pathlib import Path
import math
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

import analyze_v274_4head_opponent_feature_audit as v274
import analyze_v270_4head_win_feature_importance as v270
import analyze_v96_4corner_monthly_walkforward_tiebreak as v96
import analyze_v251_4head_newroi_bridge as v251

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'analysis_v276_4head_opponent_pair_family.csv'
MONTH=ROOT/'analysis_v276_4head_opponent_pair_monthly.csv'
SUM=ROOT/'summary_v276_4head_opponent_pair_feature_audit.md'
BOATS=v274.BOATS
MONTHS=('2026-02','2026-03','2026-04','2026-05','2026-06')
HOLD=('2026-04','2026-05','2026-06')
MIN_TRAIN=40

BASE=('v93_grade','v93_national','v93_local','v93_motor','v93_waku','v93_nst','v93_direct')
PLAYER=('pref_pl_all_p2','pref_pl_all_win','pref_pl_frame_p2','pref_pl_recent_p2','pref_pl_frame_win')
PRIOR=('pref_vh_p12_display','pref_vh_p12_overall','pref_vh_p12_turn','pref_vh_p12_straight',
       'pref_vh_delta_overall','pref_vh_delta_turn','pref_gh_p2_turn','pref_gh_p2_overall')
SCENARIO=('POST','v91_straight','attack4_st_edge3','attack4_corr_strength_edge3','score_CORR20_v91',
          'preview_comp','relative_wind','wind_speed')


def num(x):
    try:
        z=float(x);return z if np.isfinite(z) else np.nan
    except Exception:return np.nan

def model():
    return Pipeline([('imp',SimpleImputer(strategy='median')),('sc',StandardScaler()),
                     ('lr',LogisticRegression(C=.12,max_iter=3000))])

def pair_feature_names(candidate,scenario=False):
    out=[]
    for f in candidate:
        out += [f's__{f}',f't__{f}',f'diff__{f}']
    out += ['s_boat','t_boat','s_inside','t_inside','s_outside','t_outside','s_dist4','t_dist4','pair_gap',
            's_b1','s_b2','s_b3','s_b5','s_b6','t_b1','t_b2','t_b3','t_b5','t_b6']
    if scenario:
        for g in SCENARIO:
            out += [f'{g}__s_inside',f'{g}__t_inside',f'{g}__s_outside',f'{g}__t_outside',
                    f'{g}__s_b3',f'{g}__s_b5',f'{g}__t_b3',f'{g}__t_b5']
    return out

def build_pairs(long,d,candidate,scenario=False):
    use=[x for x in candidate if x in long.columns]
    dm={str(r.race_code).zfill(12):r for _,r in d.iterrows()}
    rec=[]
    for code,g in long[long.month.isin(MONTHS) | (long.month<'2026-02')].groupby('race_code'):
        if len(g)!=5:continue
        code=str(code).zfill(12);rr=dm.get(code);vals={int(r.boat):r for _,r in g.iterrows()}
        actual2=int(g.loc[g.y2==1,'boat'].iloc[0]);actual3=int(g.loc[g.y3==1,'boat'].iloc[0])
        for s in BOATS:
            for t in BOATS:
                if s==t:continue
                z={'date':str(g.date.iloc[0]),'month':str(g.month.iloc[0]),'race_code':code,'s':s,'t':t,
                   'y':int(s==actual2 and t==actual3)}
                a=vals[s];b=vals[t]
                for f in use:
                    sv=num(a.get(f));tv=num(b.get(f));z[f's__{f}']=sv;z[f't__{f}']=tv
                    z[f'diff__{f}']=sv-tv if np.isfinite(sv) and np.isfinite(tv) else np.nan
                z.update({'s_boat':s,'t_boat':t,'s_inside':int(s<4),'t_inside':int(t<4),
                          's_outside':int(s>4),'t_outside':int(t>4),'s_dist4':abs(s-4),'t_dist4':abs(t-4),
                          'pair_gap':abs(s-t)})
                for bb in BOATS:z[f's_b{bb}']=int(s==bb);z[f't_b{bb}']=int(t==bb)
                if scenario and rr is not None:
                    for gn in SCENARIO:
                        gv=num(rr.get(gn));
                        for suffix,mul in [('s_inside',int(s<4)),('t_inside',int(t<4)),('s_outside',int(s>4)),('t_outside',int(t>4)),
                                           ('s_b3',int(s==3)),('s_b5',int(s==5)),('t_b3',int(t==3)),('t_b5',int(t==5))]:
                            z[f'{gn}__{suffix}']=gv*mul if np.isfinite(gv) else np.nan
                rec.append(z)
    return pd.DataFrame(rec),pair_feature_names(use,scenario)

def good(tr,fs):
    o=[]
    for c in fs:
        if c not in tr:continue
        x=pd.to_numeric(tr[c],errors='coerce')
        if x.notna().mean()>=.55 and x.nunique(dropna=True)>=2:o.append(c)
    return o

def baseline():return v251.pair_orders(v96.read())
def prank(order,actual):
    try:return order.index(actual)+1
    except ValueError:return 0

def predict_family(pairs,fs,name,base,selcodes):
    out=[]
    for mon in MONTHS:
        tr=pairs[pairs.month<mon].copy();te=pairs[pairs.month==mon].copy()
        nr=tr.race_code.nunique()
        if nr<MIN_TRAIN or te.empty:continue
        use=good(tr,fs)
        if len(use)<10:continue
        m=model();m.fit(tr[use].apply(pd.to_numeric,errors='coerce'),tr.y)
        te=te.copy();te['p']=m.predict_proba(te[use].apply(pd.to_numeric,errors='coerce'))[:,1]
        for code,g in te.groupby('race_code'):
            g=g.sort_values(['p','s','t'],ascending=[False,True,True]);order=[(int(s),int(t)) for s,t in zip(g.s,g.t)]
            pos=g[g.y==1]
            if len(pos)!=1:continue
            actual=(int(pos.s.iloc[0]),int(pos.t.iloc[0]));key=(str(g.date.iloc[0]),str(code).zfill(12));old=base.get(key,[])
            out.append({'family':name,'month':mon,'date':g.date.iloc[0],'race_code':str(code).zfill(12),
                        'train_races':nr,'n_features':len(use),'new_rank':prank(order,actual),'v96_rank':prank(old,actual),
                        'selected_SA':int(str(code).zfill(12) in selcodes)})
    return pd.DataFrame(out)

def metrics(g,prefix):
    r={'races':len(g)}
    for k in (1,2,4,6,10,20):r[f'{prefix}_top{k}_pct']=100*((g[f'{prefix}_rank']>0)&(g[f'{prefix}_rank']<=k)).mean() if len(g) else np.nan
    return r

def main():
    d,_,_=v270.prepare();d=d[d._date<pd.Timestamp('2026-07-01')].copy();d['date']=d.date.astype(str)
    specs=v274.feature_specs(d);long=v274.build_long(d,specs);base=baseline();sel=v274.selected_codes()
    families={
      'PAIR_BASE':(BASE,False),
      'PAIR_BASE_PLAYER':(BASE+PLAYER,False),
      'PAIR_BASE_PRIOR':(BASE+PRIOR,False),
      'PAIR_PLAYER_PRIOR':(BASE+PLAYER+PRIOR,False),
      'PAIR_BASE_SCENARIO':(BASE,True),
      'PAIR_PLAYER_SCENARIO':(BASE+PLAYER,True),
      'PAIR_ALL':(BASE+PLAYER+PRIOR,True),
    }
    pp=[]
    for name,(cand,sc) in families.items():
        pairs,fs=build_pairs(long,d,cand,sc);q=predict_family(pairs,fs,name,base,sel)
        if not q.empty:pp.append(q)
    pred=pd.concat(pp,ignore_index=True)
    rows=[];monthly=[]
    for fam,g in pred.groupby('family'):
        for scope,gg in [('ALL',g),('HOLD_ALL',g[g.month.isin(HOLD)]),('HOLD_SA',g[(g.month.isin(HOLD))&(g.selected_SA==1)])]:
            if gg.empty:continue
            rec={'family':fam,'scope':scope,'avg_features':gg.n_features.mean(),**metrics(gg,'new'),**metrics(gg,'v96')}
            for k in (1,2,4,6,10,20):rec[f'delta_top{k}_pt']=rec[f'new_top{k}_pct']-rec[f'v96_top{k}_pct']
            rows.append(rec)
        for mon,gg in g[g.month.isin(HOLD)].groupby('month'):
            rec={'family':fam,'month':mon,**metrics(gg,'new'),**metrics(gg,'v96')};monthly.append(rec)
    o=pd.DataFrame(rows);o.to_csv(OUT,index=False);mm=pd.DataFrame(monthly);mm.to_csv(MONTH,index=False)

    L=['# v276 4-head direct pair feature audit','',
       '- Direct target: exact ordered opponent pair `(second, third)` conditional on historical boat-4 wins.',
       '- Each evaluation month trains only on earlier races; Jul/Aug excluded; September not read.',
       '- No odds in pair features/ranking; v268/v273 head selectors unchanged.',
       '- v96 remains the baseline. This is retrospective feature research/model selection.','',
       '## Apr-Jun holdout-like comparison: all boat-4 wins','',
       '|family|R|features|T1|T2|T4|T6|T10|v96 T2|T4|T6|T10|',
       '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    q=o[o.scope=='HOLD_ALL'].sort_values(['new_top2_pct','new_top4_pct','new_top6_pct'],ascending=False)
    for _,r in q.iterrows():L.append(f'|{r.family}|{int(r.races)}|{r.avg_features:.0f}|{r.new_top1_pct:.1f}%|{r.new_top2_pct:.1f}%|{r.new_top4_pct:.1f}%|{r.new_top6_pct:.1f}%|{r.new_top10_pct:.1f}%|{r.v96_top2_pct:.1f}%|{r.v96_top4_pct:.1f}%|{r.v96_top6_pct:.1f}%|{r.v96_top10_pct:.1f}%|')
    L += ['','## Frozen S+A selected boat-4 wins, Apr-Jun','',
          '|family|R|T1|T2|T4|T6|T10|v96 T2|T4|T6|T10|ΔT2|ΔT4|',
          '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    sa=o[o.scope=='HOLD_SA'].sort_values(['new_top2_pct','new_top4_pct','new_top6_pct'],ascending=False)
    for _,r in sa.iterrows():L.append(f'|{r.family}|{int(r.races)}|{r.new_top1_pct:.1f}%|{r.new_top2_pct:.1f}%|{r.new_top4_pct:.1f}%|{r.new_top6_pct:.1f}%|{r.new_top10_pct:.1f}%|{r.v96_top2_pct:.1f}%|{r.v96_top4_pct:.1f}%|{r.v96_top6_pct:.1f}%|{r.v96_top10_pct:.1f}%|{r.delta_top2_pt:+.1f}pt|{r.delta_top4_pt:+.1f}pt|')
    # Small-N priority: current composite-odds policy often uses only a few tickets.
    if len(sa):
        z=sa.copy();z['priority']=.50*z.delta_top2_pt+.30*z.delta_top4_pt+.15*z.delta_top6_pt+.05*z.delta_top10_pt
        best=z.sort_values(['priority','delta_top2_pt','delta_top4_pt'],ascending=False).iloc[0]
        L += ['','## Feature-family finding',
              f'- Best direct-pair family by small-N priority: **{best.family}**.',
              f'- S+A delta vs v96: Top2 {best.delta_top2_pt:+.1f}pt, Top4 {best.delta_top4_pt:+.1f}pt, Top6 {best.delta_top6_pt:+.1f}pt, Top10 {best.delta_top10_pt:+.1f}pt.',
              '- A direct-pair family is only a candidate if it improves the small-N region; broad Top10 gains alone are not enough.',
              '- If no family beats v96 at Top2/Top4, retain v96 and use the discovered player-history variables only for diagnostics or narrowly conditioned tie-break research.']
    SUM.write_text('\n'.join(L)+'\n',encoding='utf-8');print('\n'.join(L))

if __name__=='__main__':main()
