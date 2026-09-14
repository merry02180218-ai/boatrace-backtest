#!/usr/bin/env python3
"""4-head head-rate-first research on top of the frozen 4v3 motor gate.

Policy
- Base fixed gate is NOT re-optimized:
    motor_win_diff_4v3 >= 0.010782 AND motor_2ren_diff_4v3 >= 0.4000pt
- Apr-Jun 2026 may choose one additional head-rate gate.
- Jul-Aug 2026 is fixed holdout.
- September 2026 outcomes are never read.
- production HEAD4_V291_COMP7 is untouched.

New causal inputs
- motor_3ren_diff_4v3: prior-only top-3 rate, same venue+motor, 4 minus 3.
- player4_all_win: prior-only all-frame win rate for boat4's player.
- player4_frame4_win: prior-only frame-4 win rate for boat4's player.
- player4_recent_p2: prior-only recent-30 top-2 rate for boat4's player.
- ST inputs: already-frozen v90/v91 corrected ST strengths from analysis_v93.
"""
from __future__ import annotations
from collections import defaultdict, deque
from datetime import date, timedelta
from pathlib import Path
import itertools
import numpy as np
import pandas as pd

from backtest import rows
from backtest_v4 import clean_name
import analyze_v96_4corner_monthly_walkforward_tiebreak as c4
from analyze_4head_b4_minus_b3_motor_full_universe import settle_all
from analyze_4head_b4_minus_b3_motor_win_2ren import build_motor_features, code, met

ROOT=Path(__file__).resolve().parent
DETAIL=ROOT/'analysis_4head_headrate_3ren_player_st_races.csv'
GRID=ROOT/'analysis_4head_headrate_3ren_player_st_grid.csv'
SUMMARY=ROOT/'summary_4head_headrate_3ren_player_st.md'
TRAIN=('2026-04','2026-05','2026-06')
HOLD=('2026-07','2026-08')
MONTHS=TRAIN+HOLD
WIN_CUT=0.010782
REN2_CUT=0.4000
HISTORY_START=date(2025,10,1)
END=date(2026,8,31)
MIN_TRAIN_R=45


def ii(x,d=0):
    try:return int(float(str(x).strip()))
    except Exception:return d


def ff(x,d=np.nan):
    try:
        v=float(x); return v if np.isfinite(v) else d
    except Exception:return d


def bycode(rs):
    return {code(r.get('レースコード',r.get('race_code',''))):r for r in rs if r.get('レースコード',r.get('race_code'))}


def venue(card):return str(card.get('レース場コード','')).zfill(2)
def mkey(card,b):return venue(card),str(card.get(f'艇{b}_モーター番号','')).strip()


def pblank():
    return {'n':0,'w':0,'nf4':0,'wf4':0,'recent':deque(maxlen=30)}


def build_prior_features():
    """Single causal day-walk; freeze all same-day inputs before ingesting results."""
    mh=defaultdict(lambda:[0,0])  # top3,total
    ph=defaultdict(pblank)
    rec=[]
    d=HISTORY_START
    while d<=END:
        if d.year==2026 and d.month==9:
            raise RuntimeError('September outcome access blocked')
        ymd=d.strftime('%Y/%m/%d')
        cards=rows(f'data/programs/race_cards/{ymd}.csv')
        # Freeze features first.
        if d>=date(2026,4,1):
            for card in cards:
                c=code(card.get('レースコード',''))
                k4,k3=mkey(card,4),mkey(card,3)
                a4=mh[k4]; a3=mh[k3]
                m4=a4[0]/a4[1] if a4[1] else np.nan
                m3=a3[0]/a3[1] if a3[1] else np.nan
                name4=clean_name(card.get('艇4_選手名',''))
                ps=ph[name4]
                all_win=ps['w']/ps['n'] if ps['n'] else np.nan
                frame4_win=ps['wf4']/ps['nf4'] if ps['nf4'] else np.nan
                recent_p2=sum(ps['recent'])/len(ps['recent']) if ps['recent'] else np.nan
                rec.append({'date':str(d),'month':str(d)[:7],'race_code':c,
                    'motor4_3ren_prior':m4,'motor3_3ren_prior':m3,
                    'motor_3ren_diff_4v3':m4-m3 if np.isfinite(m4) and np.isfinite(m3) else np.nan,
                    'player4_all_win':all_win,'player4_frame4_win':frame4_win,
                    'player4_recent_p2':recent_p2})
        # Only after every race on the date is frozen, ingest that date's outcomes.
        rm=bycode(rows(f'data/results/realtime/{ymd}.csv'))
        for card in cards:
            c=code(card.get('レースコード','')); rr=rm.get(c,{})
            w=ii(rr.get('1着_艇番')); s=ii(rr.get('2着_艇番')); t=ii(rr.get('3着_艇番'))
            if w not in range(1,7):continue
            top3={w,s,t}
            for b in range(1,7):
                k=mkey(card,b)
                if k[1]:
                    mh[k][1]+=1; mh[k][0]+=int(b in top3)
                name=clean_name(card.get(f'艇{b}_選手名',''))
                if not name:continue
                ps=ph[name]; ps['n']+=1; ps['w']+=int(w==b)
                if b==4:
                    ps['nf4']+=1; ps['wf4']+=int(w==4)
                ps['recent'].append(int(b==w or b==s))
        d+=timedelta(days=1)
    return pd.DataFrame(rec)


def st_features():
    rs=c4.read(); out=[]
    for r in rs:
        ds=str(r.get('date','')); mon=ds[:7]
        if mon not in MONTHS:continue
        vals={b:ff(r.get(f'st_corr_strength_b{b}')) for b in range(1,7)}
        if not np.isfinite(vals[4]):continue
        inside=[vals[b] for b in (1,2,3) if np.isfinite(vals[b])]
        if len(inside)!=3:continue
        out.append({'date':ds,'month':mon,'race_code':code(r.get('race_code','')),
            'st4_strength':vals[4],
            'st4_minus_b3':vals[4]-vals[3],
            'st4_minus_inside_avg':vals[4]-float(np.mean(inside)),
            'inside_max_st_strength':max(inside),
            'inside_avg_st_strength':float(np.mean(inside))})
    return pd.DataFrame(out)


def base_rows():
    z=settle_all().merge(build_motor_features(),on=['date','month','race_code'],how='left')
    z=z[(z.motor_win_diff_4v3>=WIN_CUT)&(z.motor_2ren_diff_4v3>=REN2_CUT)].copy()
    z=z.merge(build_prior_features(),on=['date','month','race_code'],how='left')
    z=z.merge(st_features(),on=['date','month','race_code'],how='left')
    return z


FEATURES={
    # name: direction, where + means keep >= cut and - means keep <= cut
    'motor_3ren_diff_4v3':'+',
    'player4_all_win':'+',
    'player4_frame4_win':'+',
    'player4_recent_p2':'+',
    'st4_strength':'+',
    'st4_minus_b3':'+',
    'st4_minus_inside_avg':'+',
    'inside_max_st_strength':'-',
    'inside_avg_st_strength':'-',
}


def qcuts(tr,feat,direction):
    s=pd.to_numeric(tr[feat],errors='coerce').dropna()
    qs=(.20,.30,.40,.50,.60,.70) if direction=='+' else (.30,.40,.50,.60,.70,.80)
    return sorted(set(float(s.quantile(q)) for q in qs))


def apply_gate(df,parts):
    m=pd.Series(True,index=df.index)
    for feat,direction,cut in parts:
        x=pd.to_numeric(df[feat],errors='coerce')
        m &= (x>=cut) if direction=='+' else (x<=cut)
    return m


def month_floor_head(q):
    a=[float(g.actual_head4.mean()) for _,g in q.groupby('month') if len(g)]
    return min(a) if a else np.nan


def month_counts(q):
    return ', '.join(f'{m}:{len(g)}R/{100*g.actual_head4.mean():.1f}%' for m,g in q.groupby('month'))


def main():
    z=base_rows()
    z.to_csv(DETAIL,index=False)
    tr=z[z.month.isin(TRAIN)].copy(); ho=z[z.month.isin(HOLD)].copy()
    base_tr=met(tr); base_ho=met(ho)
    rows_grid=[]
    # Single gates.
    for feat,direction in FEATURES.items():
        for cut in qcuts(tr,feat,direction):
            q=tr[apply_gate(tr,[(feat,direction,cut)])]
            if len(q)<MIN_TRAIN_R:continue
            x=met(q); rows_grid.append({'kind':'SINGLE','rule':f'{feat}{direction}{cut:.6g}',
                'parts':repr([(feat,direction,cut)]),**{f'train_{k}':v for k,v in x.items()},
                'train_month_floor_head':month_floor_head(q),'train_months':month_counts(q)})
    # Pair gates using only the three least aggressive quantile cuts per feature.
    candidates={}
    for feat,direction in FEATURES.items():
        cs=qcuts(tr,feat,direction)
        candidates[feat]=cs[:3] if direction=='+' else cs[-3:]
    for f1,f2 in itertools.combinations(FEATURES,2):
        d1,d2=FEATURES[f1],FEATURES[f2]
        for c1 in candidates[f1]:
            for c2 in candidates[f2]:
                parts=[(f1,d1,c1),(f2,d2,c2)]
                q=tr[apply_gate(tr,parts)]
                if len(q)<MIN_TRAIN_R:continue
                x=met(q); rows_grid.append({'kind':'PAIR','rule':f'{f1}{d1}{c1:.6g} & {f2}{d2}{c2:.6g}',
                    'parts':repr(parts),**{f'train_{k}':v for k,v in x.items()},
                    'train_month_floor_head':month_floor_head(q),'train_months':month_counts(q)})
    G=pd.DataFrame(rows_grid)
    if G.empty:raise RuntimeError('no eligible gates')
    # Head-rate first, but reject a rule whose weakest Apr-Jun month is below fixed-base aggregate head rate.
    G['stable_head'] = G.train_month_floor_head >= base_tr['head4_rate']
    G=G.sort_values(['stable_head','train_head4_rate','train_R','train_month_floor_head'],ascending=[False,False,False,False]).reset_index(drop=True)
    G['selected']=False; G.loc[0,'selected']=True; G.to_csv(GRID,index=False)
    import ast
    parts=ast.literal_eval(G.iloc[0].parts)
    qtr=tr[apply_gate(tr,parts)]; qho=ho[apply_gate(ho,parts)]
    htr=met(qtr); hho=met(qho)
    L=['# 4号艇 頭率優先 — 3連対率・選手力・ST環境 追加研究','',
       f'- fixed base motor rule: `motor_win_diff_4v3 >= {WIN_CUT:.6f} AND motor_2ren_diff_4v3 >= {REN2_CUT:.4f}pt`。ここは再最適化しない。',
       '- 3連対率差・選手力は当日より前だけで因果的に再構築。STは既存v90/v91の補正済み事前入力。',
       '- Apr-Junだけで追加条件を選択し、Jul-Augは固定holdout。',
       '- 選択基準は4号艇1着率最優先。ただしApr-Junの最低月頭率が固定base合算頭率を下回る候補は後順位。',
       '- September outcomesはUNREAD。production `HEAD4_V291_COMP7` は変更しない。','',
       '## Apr-Jun fixed-base',
       f"- {base_tr['R']}R / 4頭 {base_tr['head4']} ({100*base_tr['head4_rate']:.2f}%) / 3連単 {base_tr['hits']} ({100*base_tr['hit_rate']:.2f}%) / ROI {100*base_tr['roi']:.2f}%",'',
       '## Chosen extra gate',f"- `{G.iloc[0].rule}`",f"- train: {htr['R']}R / 4頭 {htr['head4']} ({100*htr['head4_rate']:.2f}%) / 3連単 {htr['hits']} ({100*htr['hit_rate']:.2f}%) / ROI {100*htr['roi']:.2f}%",
       f'- train months: {month_counts(qtr)}','',
       '## Jul-Aug fixed holdout',
       f"- base: {base_ho['R']}R / 4頭 {base_ho['head4']} ({100*base_ho['head4_rate']:.2f}%) / 3連単 {base_ho['hits']} ({100*base_ho['hit_rate']:.2f}%) / ROI {100*base_ho['roi']:.2f}%",
       f"- chosen: {hho['R']}R / 4頭 {hho['head4']} ({100*hho['head4_rate']:.2f}%) / 3連単 {hho['hits']} ({100*hho['hit_rate']:.2f}%) / ROI {100*hho['roi']:.2f}%",
       f'- holdout months: {month_counts(qho)}','',
       '## Top 10 Apr-Jun head-rate candidates','|rank|kind|rule|R|4頭率|最低月頭率|','|---:|---|---|---:|---:|---:|']
    for i,r in G.head(10).iterrows():
        L.append(f"|{i+1}|{r.kind}|`{r.rule}`|{int(r.train_R)}|{100*r.train_head4_rate:.2f}%|{100*r.train_month_floor_head:.2f}%|")
    L += ['','## Guardrail','- Jul-Aug holdoutで条件再調整しない。','- archived odds ROIは補助評価。今回の第一目的は4号艇1着率。','- この研究だけではproductionを変更しない。']
    SUMMARY.write_text('\n'.join(L)+'\n',encoding='utf-8')
    print('\n'.join(L))

if __name__=='__main__':main()
