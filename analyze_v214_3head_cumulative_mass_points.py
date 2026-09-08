#!/usr/bin/env python3
"""v214: choose 4/6/8/10 tickets directly from v166 cumulative pair probability mass.

Protocol
- July 2026 only tunes three cumulative-mass thresholds: mass4, mass6, mass8.
- Rule: if mass4>=t4 -> 4pt; elif mass6>=t6 -> 6pt; elif mass8>=t8 -> 8pt; else 10pt.
- Tiny threshold grid is made from July quantiles only. Objective: maximize July ROI subject to
  hit rate >=85% of fixed Top10 and average points <10.
- August is untouched: July thresholds are frozen.
- Then the SAME frozen rule is backward stress-tested on 2025-12..2026-06 with monthly prior-only
  v165/v166 reconstruction and the same 10,000-yen Hamilton Dutch settlement.
- Odds/results never enter v166 ranking or cumulative mass; they are settlement/tuning labels only.

Caveat: v166 lambda=1.00 was historically selected using Mar-May, and the v214 thresholds are tuned
on July. Therefore Dec-Jun backward results are robustness stress, not pristine OOS evidence.
"""
from pathlib import Path
from datetime import date
import itertools
import numpy as np
import pandas as pd
import analyze_v165_3head_monthly_walkforward as v165
import analyze_v166_3head_pair_direct as v166
import analyze_v205_3head_operational_replay as v205
import analyze_v211_3head_variable_points_newroi as v211

ROOT=Path(__file__).resolve().parent
SRC=ROOT/'analysis_v108_1head_feasibility.csv'
V211=ROOT/'analysis_v211_3head_variable_points_newroi.csv'
OUT=ROOT/'analysis_v214_3head_cumulative_mass_points.csv'
SUM=ROOT/'summary_v214_3head_cumulative_mass_points.md'
BANK=10000
POINTS=(4,6,8,10)
QGRID=(0.20,0.30,0.40,0.50,0.60,0.70,0.80)
OLD_MONTHS=['2025-12']+[f'2026-{m:02d}' for m in range(1,7)]


def metrics(g,pcol='rule_points'):
    if g.empty:return dict(R=0,hit=0,pts=0,comp=0,cost=0,ret=0,roi=0,profit=0)
    cost=float(g.cost.sum());ret=float(g.return_yen.sum())
    return dict(R=len(g),hit=100*float(g.hit.mean()),pts=float(g[pcol].mean()),
                comp=float(g.composite_odds.mean()),cost=cost,ret=ret,
                roi=100*ret/cost if cost else 0,profit=ret-cost)


def choose_points(m4,m6,m8,cuts):
    t4,t6,t8=cuts
    if m4>=t4:return 4
    if m6>=t6:return 6
    if m8>=t8:return 8
    return 10


def select_from_fixed(fixed,cuts):
    base=fixed.drop_duplicates('race_code')
    rows=[]
    for _,r in base.iterrows():
        n=choose_points(float(r.mass4),float(r.mass6),float(r.mass8),cuts)
        q=fixed[(fixed.race_code==r.race_code)&(fixed.points==n)]
        if len(q):
            x=q.iloc[0].copy();x['rule_points']=n;x['strategy']='v214_mass_variable';rows.append(x)
    return pd.DataFrame(rows)


def tune(jul):
    base=jul.drop_duplicates('race_code')
    grids=[]
    for c in ('mass4','mass6','mass8'):
        vals=sorted(set(float(base[c].quantile(q)) for q in QGRID))
        grids.append(vals)
    top10=jul[jul.points==10].copy();top10['rule_points']=10
    b=metrics(top10);cands=[]
    for cuts in itertools.product(*grids):
        g=select_from_fixed(jul,cuts)
        if g.empty:continue
        m=metrics(g)
        if m['pts']>=10:continue
        if b['hit']>0 and m['hit']<0.85*b['hit']:continue
        cands.append((m['roi'],-m['pts'],m['hit'],cuts,m))
    if not cands:
        return (float('inf'),float('inf'),float('inf')),metrics(top10)
    cands.sort(key=lambda x:(x[0],x[1],x[2]),reverse=True)
    return cands[0][3],cands[0][4]


def reconstruct_old(cuts):
    src_path,df=v165.load(); dc=v165.pc(df,['date','race_date','ymd']); vc=v165.pc(df,['venue','jcd','stadium','place'])
    if Path(src_path).name!='analysis_v108_1head_feasibility.csv':raise SystemExit(f'v165 source mismatch: {src_path}')
    y,td=v165.target(df);fs=v165.feats(df)
    d=df.copy();d['_date']=pd.to_datetime(d[dc].astype(str),errors='coerce');d['_y']=y
    d=d[d._date.notna()&d._y.notna()].copy()
    src=v166.read(str(SRC)); odds=v205.load_odds();oi=odds.set_index('race_code',drop=False)
    rows=[];candidate_counts={}
    for mon in OLD_MONTHS:
        m=pd.Timestamp(mon+'-01');e=m+pd.offsets.MonthBegin(1)
        tr=d[d._date<m].copy();te=d[(d._date>=m)&(d._date<e)].copy()
        if len(tr)<200 or len(te)<20 or tr._y.nunique()<2:continue
        nums=[]
        for c in fs:
            q=pd.to_numeric(d[c],errors='coerce')
            if q.notna().mean()>=.8:
                tr[c]=pd.to_numeric(tr[c],errors='coerce');te[c]=pd.to_numeric(te[c],errors='coerce');nums.append(c)
        cats=[vc] if vc and vc not in nums else []
        hm=v165.model(nums,cats);hm.fit(tr[nums+cats],tr._y.astype(int));probs=hm.predict_proba(te[nums+cats])[:,1]
        pm,pair_n=v166.fit([r for r in src if date.fromisoformat(r['date'])<date.fromisoformat(mon+'-01')])
        cands=[]
        for ix,p in zip(te.index,probs):
            if p<.30:continue
            rr=dict(src[int(ix)])
            if v166.ii(rr.get('course3'),3)!=3:continue
            cands.append((str(rr.get('race_code')),float(p),rr))
        candidate_counts[mon]=len(cands)
        for code,p,rr in cands:
            if code not in oi.index:continue
            od=oi.loc[code];od=od.iloc[-1] if isinstance(od,pd.DataFrame) else od
            ordered,effn,ent,masses=v211.pair_distribution(rr,pm)
            actual=str(rr.get('actual_combo','')).strip();proxy=type('R',(),{'actual_combo':actual})()
            n=choose_points(masses[4],masses[6],masses[8],cuts)
            s=v211.settle_topn(proxy,od,ordered,n)
            if s is None:continue
            rows.append({'split':'old_stress','month':mon,'date':rr.get('date'),'race_code':code,'p3head':p,
                         'actual_combo':actual,'pair_train_3wins':pair_n,'effn':effn,'entropy':ent,
                         'mass4':masses[4],'mass6':masses[6],'mass8':masses[8],'mass10':masses[10],
                         'rank20':';'.join(ordered),**s,'rule_points':n,'strategy':'v214_mass_variable',
                         'odds_source':str(od.get('odds_source','unknown'))})
    return pd.DataFrame(rows),candidate_counts


def main():
    z=pd.read_csv(V211,dtype={'race_code':str})
    fixed=z[z.strategy=='fixed'].copy()
    jul=fixed[fixed.month=='2026-07'].copy();aug=fixed[fixed.month=='2026-08'].copy()
    cuts,tunem=tune(jul)
    jsel=select_from_fixed(jul,cuts);asel=select_from_fixed(aug,cuts)
    jsel['split']='july_tune';asel['split']='aug_untouched'
    old,cc=reconstruct_old(cuts)
    out=pd.concat([jsel,asel,old],ignore_index=True,sort=False);out.to_csv(OUT,index=False)

    L=['# v214 3-head cumulative-mass variable points','',
       '- signal: direct v166 cumulative pair probability mass only',
       f'- frozen July thresholds: **mass4 >= {cuts[0]:.6f} -> 4pt; else mass6 >= {cuts[1]:.6f} -> 6pt; else mass8 >= {cuts[2]:.6f} -> 8pt; else 10pt**',
       '- July tuning constraint: hit >=85% of fixed Top10 and avg points <10',
       '- August untouched uses the frozen July thresholds',
       '- old stress 2025-12..2026-06 reconstructs v165/v166 month-by-month using prior dates only',
       '- settlement: unified pre-deadline odds, 10,000 yen/race, 100-yen Hamilton Dutch',
       '- IMPORTANT: backward old-month results are stress tests, not pristine OOS.','',
       '## July/August comparison','|month|strategy|R|hit|avg pts|avg comp|return|ROI|profit|','|---|---|---:|---:|---:|---:|---:|---:|---:|']
    for mon,gfix,gvar in [('2026-07',jul,jsel),('2026-08',aug,asel)]:
        for n in POINTS:
            g=gfix[gfix.points==n].copy();g['rule_points']=n;m=metrics(g)
            L.append(f"|{mon}|Top{n} fixed|{m['R']}|{m['hit']:.2f}%|{m['pts']:.2f}|{m['comp']:.3f}|{m['ret']:.0f}|{m['roi']:.1f}%|{m['profit']:+.0f}|")
        m=metrics(gvar);L.append(f"|{mon}|v214 mass variable|{m['R']}|{m['hit']:.2f}%|{m['pts']:.2f}|{m['comp']:.3f}|{m['ret']:.0f}|{m['roi']:.1f}%|{m['profit']:+.0f}|")
    L += ['','## August point distribution','|points|R|share|','|---:|---:|---:|']
    for n in POINTS:
        c=int((asel.rule_points==n).sum());L.append(f'|{n}|{c}|{100*c/len(asel) if len(asel) else 0:.1f}%|')
    L += ['','## Old-month frozen-rule stress','|month|candidates|settled|hit|avg pts|avg comp|return|ROI|profit|','|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for mon in OLD_MONTHS:
        g=old[old.month==mon];m=metrics(g)
        L.append(f"|{mon}|{cc.get(mon,0)}|{m['R']}|{m['hit']:.2f}%|{m['pts']:.2f}|{m['comp']:.3f}|{m['ret']:.0f}|{m['roi']:.1f}%|{m['profit']:+.0f}|")
    m=metrics(old)
    L += ['','## Aggregate Dec-Jun',f"- v214 mass variable: **{m['R']}R, hit {m['hit']:.2f}%, avg points {m['pts']:.2f}, avg composite {m['comp']:.3f}, ROI {m['roi']:.1f}%, profit {m['profit']:+.0f} yen**",'',
          '## Interpretation','- Primary clean comparison for the new threshold rule is August untouched.',
          '- Dec-Jun is backward stability stress only because the point rule was created later on July and v166 lambda has prior tuning history.',
          '- Production remains unchanged unless the rule shows materially better stability than fixed Top6/Top10 and v212.']
    SUM.write_text('\n'.join(L)+'\n',encoding='utf-8');print('\n'.join(L))

if __name__=='__main__':main()
