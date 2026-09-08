#!/usr/bin/env python3
"""v213: long-history stress of 3-head Top6 vs Top10 vs frozen v212 variable points under 10k Dutch ROI.

Protocol
- Reconstruct v165 p3head monthly walk-forward for 2025-12..2026-06, each month trained only on earlier dates.
- Candidate: p3head>=.30 and course3==3.
- Reconstruct v166 direct ordered-pair model each month from prior 3-head wins only, lambda=1.00.
- Settle Top4/6/8/10 and frozen v212 4/6/8/10 variable rule using unified odds and exact 10k Hamilton Dutch.
- Frozen v212 calibration is taken from July fixed v211 rows: July p3head/effN mean+sd, weight=.50,
  score cuts=.2746/-.1427/-.4034. No historical outcomes are used to change the rule.

Interpretation warning:
- v166 lambda=1.00 was selected using Mar-May historically, and v212 rule was tuned on July.
- Therefore Dec-May and the backward-applied v212 rule are retrospective stress, NOT pristine OOS validation.
- June is an original v166 untouched-test month, but v212 itself is still backward-applied there.
"""
from pathlib import Path
from datetime import date
import math
import numpy as np
import pandas as pd
import analyze_v165_3head_monthly_walkforward as v165
import analyze_v166_3head_pair_direct as v166
import analyze_v205_3head_operational_replay as v205
import analyze_v211_3head_variable_points_newroi as v211

ROOT=Path(__file__).resolve().parent
SRC=ROOT/'analysis_v108_1head_feasibility.csv'
V211=ROOT/'analysis_v211_3head_variable_points_newroi.csv'
OUT=ROOT/'analysis_v213_3head_top6_variable_longhistory_newroi.csv'
SUM=ROOT/'summary_v213_3head_top6_variable_longhistory_newroi.md'
MONTHS=[f'2025-{m:02d}' for m in range(12,13)]+[f'2026-{m:02d}' for m in range(1,7)]
CUT=.30; LAM=1.0; BANK=10000; POINTS=(4,6,8,10)
W=.50; CUTS=(.2746,-.1427,-.4034)

def choose_points(score):
    a,b,c=CUTS
    if score>=a:return 4
    if score>=b:return 6
    if score>=c:return 8
    return 10

def metrics(g,pcol='points'):
    if g.empty:return dict(R=0,hit=0,pts=0,comp=0,cost=0,ret=0,roi=0,profit=0)
    cost=float(g.cost.sum());ret=float(g.return_yen.sum())
    return dict(R=len(g),hit=100*float(g.hit.mean()),pts=float(g[pcol].mean()),comp=float(g.composite_odds.mean()),cost=cost,ret=ret,roi=100*ret/cost if cost else 0,profit=ret-cost)

def main():
    # v165 canonical source and feature discovery
    src_path,df=v165.load(); dc=v165.pc(df,['date','race_date','ymd']); vc=v165.pc(df,['venue','jcd','stadium','place'])
    if Path(src_path).name!='analysis_v108_1head_feasibility.csv': raise SystemExit(f'v165 source mismatch: {src_path}')
    y,td=v165.target(df); fs=v165.feats(df)
    d=df.copy();d['_date']=pd.to_datetime(d[dc].astype(str),errors='coerce');d['_y']=y
    d=d[d._date.notna()&d._y.notna()].copy()
    src=v166.read(str(SRC)); bycode={str(r.get('race_code')):r for r in src}

    # Exact frozen July standardization from v211 fixed rows (no result/odds columns involved).
    j=pd.read_csv(V211,dtype={'race_code':str});j=j[(j.month=='2026-07')&(j.strategy=='fixed')].drop_duplicates('race_code')
    p_mu=float(j.p3head.mean());p_sd=float(j.p3head.std(ddof=0) or 1)
    e_mu=float(j.effn.mean());e_sd=float(j.effn.std(ddof=0) or 1)

    odds=v205.load_odds(); oi=odds.set_index('race_code',drop=False) if not odds.empty else pd.DataFrame()
    rows=[]; candidate_counts={}
    for mon in MONTHS:
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
            if p<CUT:continue
            rr=dict(src[int(ix)])
            if v166.ii(rr.get('course3'),3)!=3:continue
            code=str(rr.get('race_code'))
            cands.append((code,float(p),rr))
        candidate_counts[mon]=len(cands)
        for code,p,rr in cands:
            if oi.empty or code not in oi.index:continue
            od=oi.loc[code];od=od.iloc[-1] if isinstance(od,pd.DataFrame) else od
            ordered,effn,ent,masses=v211.pair_distribution(rr,pm)
            actual=str(rr.get('actual_combo','')).strip()
            base={'month':mon,'date':rr.get('date'),'race_code':code,'p3head':p,'actual_combo':actual,
                  'pair_train_3wins':pair_n,'effn':effn,'entropy':ent,'rank20':';'.join(ordered),
                  'odds_source':str(od.get('odds_source','unknown'))}
            fixed={}
            for n in POINTS:
                proxy=type('R',(),{'actual_combo':actual})()
                s=v211.settle_topn(proxy,od,ordered,n)
                if s is not None:fixed[n]=s
            if len(fixed)!=len(POINTS):continue
            score=W*((p-p_mu)/p_sd)+(1-W)*(-(effn-e_mu)/e_sd)
            vn=choose_points(score)
            for n,s in fixed.items():
                rows.append({**base,**s,'strategy':f'Top{n}','rule_points':n,'joint_score':score})
            rows.append({**base,**fixed[vn],'strategy':'v212_variable','rule_points':vn,'joint_score':score})
    z=pd.DataFrame(rows)
    if z.empty:raise SystemExit('no evaluable rows')
    z.to_csv(OUT,index=False)

    L=['# v213 3-head Top6 vs frozen variable long-history new-ROI stress','',
       '- window: 2025-12..2026-06; each month reconstructs v165 and v166 using only prior dates',
       '- candidate: v165 p3head>=0.30 and course3==3',
       '- v166 ranking: direct pair lambda=1.00; fixed Top4/6/8/10',
       '- settlement: unified pre-deadline odds, 10,000 yen per race, 100-yen Hamilton Dutch',
       f'- frozen v212: July p_mu={p_mu:.6f}, p_sd={p_sd:.6f}, effN_mu={e_mu:.6f}, effN_sd={e_sd:.6f}, weight={W:.2f}, cuts={CUTS}',
       '- IMPORTANT: lambda=1.00 was historically selected using Mar-May and v212 was tuned on July; backward results are stress tests, not pristine OOS.','',
       '## Monthly comparison','|month|candidates|settled|strategy|hit|avg pts|avg comp|return|ROI|profit|','|---|---:|---:|---|---:|---:|---:|---:|---:|---:|']
    for mon in MONTHS:
        for st in ('Top4','Top6','Top8','Top10','v212_variable'):
            g=z[(z.month==mon)&(z.strategy==st)];m=metrics(g,'rule_points')
            L.append(f"|{mon}|{candidate_counts.get(mon,0)}|{m['R']}|{st}|{m['hit']:.2f}%|{m['pts']:.2f}|{m['comp']:.3f}|{m['ret']:.0f}|{m['roi']:.1f}%|{m['profit']:+.0f}|")
    L += ['','## Aggregate Dec-Jun','|strategy|R|hit|avg pts|avg comp|cost|return|ROI|profit|','|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for st in ('Top4','Top6','Top8','Top10','v212_variable'):
        g=z[z.strategy==st];m=metrics(g,'rule_points')
        L.append(f"|{st}|{m['R']}|{m['hit']:.2f}%|{m['pts']:.2f}|{m['comp']:.3f}|{m['cost']:.0f}|{m['ret']:.0f}|{m['roi']:.1f}%|{m['profit']:+.0f}|")
    L += ['','## Variable point distribution','|points|R|share|','|---:|---:|---:|']
    gv=z[z.strategy=='v212_variable']
    for n in POINTS:
        c=int((gv.rule_points==n).sum());L.append(f'|{n}|{c}|{100*c/len(gv) if len(gv) else 0:.1f}%|')
    L += ['','## Temporal interpretation',
          '- 2025-12..2026-02: backward stress before the original v166 lambda tuning window.',
          '- 2026-03..2026-05: descriptive/tuning-era for v166 lambda; not untouched validation.',
          '- 2026-06: original v166 untouched-test month for lambda=1.00; v212 point rule is still backward-applied because it was tuned later on July.',
          '- Production remains unchanged until stability is judged with these caveats.']
    SUM.write_text('\n'.join(L)+'\n',encoding='utf-8');print('\n'.join(L))
if __name__=='__main__':main()
