#!/usr/bin/env python3
"""v211: variable ticket-count test for current 3-head production under the new 10k Dutch ROI.

Protocol
- Candidate population is frozen v195 production pass (v165 p3head>=.30), July/August only.
- Reconstruct exact monthly v166 pair model from prior dates only, lambda=1.00.
- Baselines: Top4/6/8/10/12/15, each settled with total 10,000 yen Dutch allocation.
- Variable rule uses ONLY v166 pair-probability concentration (effective number of pairs).
- July tunes a small monotone rule that maps more concentrated races -> fewer tickets.
- August is untouched evaluation with the July rule frozen.
- Odds/results/payout are settlement-only and never enter pair ranking or concentration.
"""
from pathlib import Path
from datetime import date
import itertools, math
import numpy as np
import pandas as pd
import analyze_v166_3head_pair_direct as v166
import analyze_v205_3head_operational_replay as v205

ROOT=Path(__file__).resolve().parent
PROD=ROOT/'analysis_v195_3head_production_6month_backtest.csv'
SRC=ROOT/'analysis_v108_1head_feasibility.csv'
OUT=ROOT/'analysis_v211_3head_variable_points_newroi.csv'
SUM=ROOT/'summary_v211_3head_variable_points_newroi.md'
MONTHS=('2026-07','2026-08')
BANK=10000
POINTS=(4,6,8,10,12,15)
VAR_POINTS=(4,6,8,10)


def pair_distribution(r,m):
    pairs=[]; q=[]
    for s in v166.OPP:
        for t in v166.OPP:
            if s==t: continue
            p=float(m.predict_proba(np.asarray([v166.pvec(r,s,t)],float))[0,1])
            pairs.append((s,t));q.append(max(p,1e-12))
    a=np.asarray(q,float); a=a/a.sum()
    z=sorted(zip(a,pairs),key=lambda x:(-x[0],x[1][0],x[1][1]))
    probs=np.asarray([x[0] for x in z],float)
    ordered=[f'3-{s}-{t}' for _,(s,t) in z]
    effn=float(1.0/np.sum(probs**2))
    ent=float(-np.sum(probs*np.log(probs+1e-15))/math.log(len(probs)))
    masses={n:float(probs[:n].sum()) for n in POINTS}
    return ordered,effn,ent,masses


def settle_topn(r,odrow,ordered,n):
    ts=ordered[:n]
    vals=[]
    for t in ts:
        try:v=float(odrow[t])
        except:return None
        if not np.isfinite(v) or v<=0:return None
        vals.append(v)
    stakes=v205.round_dutch(vals,BANK)
    actual=str(r.actual_combo)
    ret=0.0; astake=0
    if actual in ts:
        i=ts.index(actual);astake=int(stakes[i]);ret=float(stakes[i])*vals[i]
    comp=1/sum(1/x for x in vals)
    return dict(points=n,hit=int(actual in ts and astake>0),composite_odds=comp,cost=BANK,
                return_yen=ret,profit=ret-BANK,actual_stake=astake)


def metrics(df,pcol='points'):
    if df.empty:return dict(R=0,hit=0,avg_points=0,comp=0,cost=0,ret=0,roi=0,profit=0)
    cost=float(df.cost.sum());ret=float(df.return_yen.sum())
    return dict(R=len(df),hit=100*df.hit.mean(),avg_points=float(df[pcol].mean()),comp=float(df.composite_odds.mean()),
                cost=cost,ret=ret,roi=100*ret/cost if cost else 0,profit=ret-cost)


def rule_points(effn,cuts):
    a,b,c=cuts
    if effn<=a:return 4
    if effn<=b:return 6
    if effn<=c:return 8
    return 10


def tune_rule(jul):
    # thresholds are July effn quantiles; monotone and deliberately small search space.
    qs=sorted(set(float(jul.effn.quantile(q)) for q in (0.10,0.20,0.30,0.40,0.50,0.60,0.70,0.80)))
    b10=metrics(jul[jul.points==10])
    candidates=[]
    base=jul.drop_duplicates('race_code').copy()
    for a,b,c in itertools.combinations(qs,3):
        rows=[]
        for _,r in base.iterrows():
            n=rule_points(float(r.effn),(a,b,c))
            z=jul[(jul.race_code==r.race_code)&(jul.points==n)]
            if len(z): rows.append(z.iloc[0])
        if not rows:continue
        g=pd.DataFrame(rows)
        m=metrics(g)
        # preserve at least 90% of Top10 hit rate; prefer ROI, then fewer points.
        if b10['hit']>0 and m['hit']<0.90*b10['hit']:continue
        candidates.append((m['roi'],-m['avg_points'],m['hit'],(a,b,c),m))
    if not candidates:
        # fallback: fixed Top10
        return (float('-inf'),float('-inf'),float('-inf')),b10
    candidates.sort(key=lambda x:(x[0],x[1],x[2]),reverse=True)
    return candidates[0][3],candidates[0][4]


def main():
    prod=pd.read_csv(PROD,dtype={'race_code':str})
    prod=prod[prod.month.isin(MONTHS)].copy()
    src=v166.read(str(SRC)); bycode={str(r.get('race_code')):r for r in src}
    odds=v205.load_odds(); oi=odds.set_index('race_code',drop=False)
    rows=[]
    for mon in MONTHS:
        first=date.fromisoformat(mon+'-01')
        train=[r for r in src if date.fromisoformat(r['date'])<first]
        model,pair_n=v166.fit(train)
        for _,pr in prod[prod.month==mon].iterrows():
            code=str(pr.race_code)
            if code not in bycode or code not in oi.index:continue
            rr=bycode[code]
            c3=v166.ii(rr.get('course3'),3)
            if c3!=3:continue
            od=oi.loc[code];od=od.iloc[-1] if isinstance(od,pd.DataFrame) else od
            ordered,effn,ent,masses=pair_distribution(rr,model)
            # assert exact v166 lambda=1 order matches production Top10 when available
            prod10=[x for x in str(pr.top10).split(';') if x]
            if prod10 and ordered[:10]!=prod10:
                raise RuntimeError(f'v166 reconstruction mismatch {code}: {ordered[:10]} != {prod10}')
            for n in POINTS:
                s=settle_topn(pr,od,ordered,n)
                if s is None:continue
                rows.append({**pr.to_dict(),'pair_train_3wins':pair_n,'effn':effn,'entropy':ent,
                             **{f'mass{nn}':masses[nn] for nn in POINTS},'rank20':';'.join(ordered),
                             **s,'odds_source':str(od.get('odds_source','unknown'))})
    z=pd.DataFrame(rows)
    if z.empty:raise SystemExit('no evaluable rows')
    jul=z[z.month=='2026-07'].copy();aug=z[z.month=='2026-08'].copy()
    cuts,tuned=tune_rule(jul)
    varrows=[]
    for mon,g in [('2026-07',jul),('2026-08',aug)]:
        base=g.drop_duplicates('race_code')
        for _,r in base.iterrows():
            n=rule_points(float(r.effn),cuts)
            q=g[(g.race_code==r.race_code)&(g.points==n)]
            if len(q):
                x=q.iloc[0].to_dict();x['rule_points']=n;varrows.append(x)
    var=pd.DataFrame(varrows)
    z['strategy']='fixed'; z['rule_points']=z.points
    var['strategy']='variable'
    out=pd.concat([z,var],ignore_index=True,sort=False)
    out.to_csv(OUT,index=False)

    L=['# v211 3-head variable points under new 10k Dutch ROI','',
       '- candidate population: frozen v195 production pass (v165 p3head>=0.30), July/August only',
       '- v166 pair model: exact monthly prior-only refit, lambda=1.00',
       '- fixed comparisons: Top4/6/8/10/12/15, each with total 10,000 yen Dutch',
       '- variable rule feature: v166 pair-probability concentration only (effective number of pairs, effN)',
       '- July chooses 3 effN cutoffs from a small quantile grid; rule is monotone 4 -> 6 -> 8 -> 10 points',
       '- tune constraint: variable hit rate must be >=90% of July Top10 hit rate',
       '- August uses the July-frozen rule untouched','']
    L += ['## Fixed point-count comparison','|month|points|R|hit|avg comp|cost|return|ROI|profit|','|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for mon,g in [('2026-07',jul),('2026-08',aug)]:
        for n in POINTS:
            m=metrics(g[g.points==n])
            L.append(f"|{mon}|{n}|{m['R']}|{m['hit']:.2f}%|{m['comp']:.3f}|{m['cost']:.0f}|{m['ret']:.0f}|{m['roi']:.1f}%|{m['profit']:+.0f}|")
    L += ['','## July-tuned variable rule',f'- frozen effN cutoffs: **{cuts[0]:.4f} / {cuts[1]:.4f} / {cuts[2]:.4f}**',
          '- mapping: effN<=c1 => 4pt; <=c2 => 6pt; <=c3 => 8pt; else 10pt','',
          '|month|R|hit|avg points|avg comp|cost|return|ROI|profit|','|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for mon in MONTHS:
        g=var[var.month==mon];m=metrics(g,'rule_points')
        L.append(f"|{mon}|{m['R']}|{m['hit']:.2f}%|{m['avg_points']:.2f}|{m['comp']:.3f}|{m['cost']:.0f}|{m['ret']:.0f}|{m['roi']:.1f}%|{m['profit']:+.0f}|")
    L += ['','## August point distribution','|points|R|share|','|---:|---:|---:|']
    ga=var[var.month=='2026-08']
    for n in VAR_POINTS:
        c=int((ga.rule_points==n).sum());L.append(f'|{n}|{c}|{100*c/len(ga):.1f}%|')
    L += ['','## Interpretation','- This is SHADOW research only. July is explicitly tune; August is the only untouched comparison for the variable rule.',
          '- If variable points beat fixed Top10 on August while using fewer average tickets, that supports a dedicated variable-points production candidate.',
          '- Do not adopt from this one August test alone; next step would be older-month locked/pseudo-forward stability.']
    SUM.write_text('\n'.join(L)+'\n',encoding='utf-8')
    print('\n'.join(L))

if __name__=='__main__':main()
