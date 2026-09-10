#!/usr/bin/env python3
"""v274: research richer opponent-selection features for frozen 4-head models.

Purpose
-------
Boat 4 is fixed as the head.  This audit studies only how to rank the five
opponents for 2nd and 3rd place.  It compares the current v96 pair order with
role-specific walk-forward models using richer pre-result boat-level features.

Discipline
----------
* 2026-07/08 are excluded completely.
* September is not read.
* Inputs are pre-result only. Result/payout/ticket/kimarite fields are excluded.
* 2nd and 3rd are modeled separately because their useful features may differ.
* Pair order is frozen without odds. Odds are NOT used anywhere in v274.
* Historical outcomes are used only as training labels / evaluation targets.
* This is retrospective feature research/model-selection, not pristine OOS.
"""
from __future__ import annotations
from pathlib import Path
from collections import defaultdict
import math, re
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

import analyze_v264_4head_feature_exhaustive as v264
import analyze_v270_4head_win_feature_importance as v270
import analyze_v251_4head_newroi_bridge as v251
import analyze_v96_4corner_monthly_walkforward_tiebreak as v96

ROOT=Path(__file__).resolve().parent
OUT_UNI=ROOT/'analysis_v274_4head_opponent_feature_univariate.csv'
OUT_FAM=ROOT/'analysis_v274_4head_opponent_family.csv'
OUT_MONTH=ROOT/'analysis_v274_4head_opponent_monthly.csv'
SUM=ROOT/'summary_v274_4head_opponent_feature_audit.md'
SEL=ROOT/'analysis_v271_4head_arank_races.csv'
BOATS=(1,2,3,5,6)
EVAL_MONTHS=('2026-02','2026-03','2026-04','2026-05','2026-06')
PORT_MONTHS=('2026-04','2026-05','2026-06')
MIN_TRAIN_RACES=40
LEAK=('winner','second','third','payout','actual_','head_hit','ticket','route_hit','kimarite',
      'valid_result','valid_payout','result_join','production_buy','approved_','y4','_target',
      'return','profit','odds','rank2_v96','rank3_v96')


def num(x):
    try:
        v=float(x)
        return v if np.isfinite(v) else np.nan
    except Exception:return np.nan

def ii(x,d=0):
    try:return int(float(x))
    except Exception:return d

def safe_name(x):
    q=x.lower()
    return not any(z in q for z in LEAK)

def model():
    return Pipeline([('imp',SimpleImputer(strategy='median')),
                     ('sc',StandardScaler()),
                     ('lr',LogisticRegression(C=.16,max_iter=2500))])


def feature_specs(d):
    """Discover symmetric pre-result opponent features already present in repo data."""
    specs={}
    # Exact v93 ingredients + current score/rank context.
    for k in ('grade','national','local','motor','waku','nst','direct','score','rank'):
        cols=[f'opp_{k}_b{b}_v93' if k not in ('rank',) else f'rank_b{b}_v93' for b in BOATS]
        if all(c in d.columns for c in cols):specs[f'v93_{k}']=('v93',k)

    # v221 frozen player / previous exhibition traits: b1_pl_*, b1_vh_*, b1_gh_*.
    tails=defaultdict(set)
    for c in d.columns:
        m=re.match(r'^b([1-6])_(.+)$',c)
        if m and safe_name(c):tails[m.group(2)].add(int(m.group(1)))
    for tail,bs in tails.items():
        if all(b in bs for b in BOATS) and safe_name(tail):
            specs[f'pref_{tail}']=('prefix',tail)

    # Symmetric suffix features such as st_raw_b1 / st_corr_strength_b1.
    roots=defaultdict(set)
    for c in d.columns:
        m=re.match(r'^(.+)_b([1-6])$',c)
        if m and safe_name(c):roots[m.group(1)].add(int(m.group(2)))
    for root,bs in roots.items():
        if all(b in bs for b in BOATS) and safe_name(root):
            specs[f'suf_{root}']=('suffix',root)

    # Stable position/context descriptors known before result.
    specs['pos_boat_number']=('manual','boat')
    specs['pos_inside4']=('manual','inside')
    specs['pos_outside4']=('manual','outside')
    specs['pos_distance4']=('manual','distance')
    return specs


def fval(r,b,spec):
    kind,key=spec
    if kind=='v93':
        if key=='rank':return num(r.get(f'rank_b{b}_v93'))
        return num(r.get(f'opp_{key}_b{b}_v93'))
    if kind=='prefix':return num(r.get(f'b{b}_{key}'))
    if kind=='suffix':return num(r.get(f'{key}_b{b}'))
    if key=='boat':return float(b)
    if key=='inside':return float(b<4)
    if key=='outside':return float(b>4)
    if key=='distance':return float(abs(b-4))
    return np.nan


def category(name):
    if name.startswith('v93_'):return 'V93_BASE_CONTEXT'
    if '_pl_' in name:return 'PLAYER_HISTORY'
    if '_vh_' in name or '_gh_' in name:return 'PRIOR_EXHIBITION'
    if name.startswith('suf_st_') or '_st_' in name:return 'START'
    if any(k in name for k in ('display','straight','turn','lap','overall')):return 'EXHIBITION_FOOT'
    if any(k in name for k in ('motor','waku','course','frame','grade','national','local')):return 'ABILITY_COURSE'
    if name.startswith('pos_'):return 'POSITION'
    return 'OTHER'


def build_long(d,specs):
    recs=[]
    for _,r in d.iterrows():
        if ii(r.get('valid_result'))!=1 or ii(r.get('winner'))!=4:continue
        sec=ii(r.get('second'));third=ii(r.get('third'))
        if sec not in BOATS or third not in BOATS or sec==third:continue
        base={'date':str(r.get('date','')),'race_code':str(r.get('race_code','')).zfill(12),
              'month':str(r.get('date',''))[:7]}
        for b in BOATS:
            z=dict(base);z['boat']=b;z['y2']=int(b==sec);z['y3']=int(b==third)
            for n,s in specs.items():z[n]=fval(r,b,s)
            recs.append(z)
    return pd.DataFrame(recs)


def good_features(tr,fs,mincov=.55):
    out=[]
    for c in fs:
        if c not in tr:continue
        x=pd.to_numeric(tr[c],errors='coerce')
        if x.notna().mean()>=mincov and x.nunique(dropna=True)>=2:out.append(c)
    return out


def univariate(long,specs):
    ev=long[long.month.isin(EVAL_MONTHS)].copy();rows=[]
    for c in specs:
        x=pd.to_numeric(ev[c],errors='coerce')
        if x.notna().mean()<.55 or x.nunique(dropna=True)<3:continue
        for role,yc in (('SECOND','y2'),('THIRD','y3')):
            z=ev.loc[x.notna(),['race_code','month','boat',yc]].copy();z['x']=x.loc[x.notna()].to_numpy()
            if z[yc].nunique()<2:continue
            try:a=roc_auc_score(z[yc],z.x)
            except Exception:continue
            direction='high' if a>=.5 else 'low';auc=max(a,1-a);sgn=1 if direction=='high' else -1
            z['ox']=sgn*z.x
            # Race-level top1/top2 with deterministic boat-number tie break.
            top1=top2=n=0
            for _,g in z.groupby('race_code'):
                if len(g)<5 or g[yc].sum()!=1:continue
                gg=g.sort_values(['ox','boat'],ascending=[False,True])
                actual=int(gg.loc[gg[yc]==1,'boat'].iloc[0]);pred=gg.boat.astype(int).tolist();n+=1
                top1+=int(pred[0]==actual);top2+=int(actual in pred[:2])
            mg=seen=0;details=[]
            for m,g in z.groupby('month'):
                if g[yc].sum()<5 or g[yc].nunique()<2:continue
                try:ma=roc_auc_score(g[yc],sgn*g.x)
                except Exception:continue
                seen+=1;mg+=int(ma>.5);details.append(f'{m}:{ma:.3f}')
            rows.append({'role':role,'feature':c,'category':category(c),'n_long':len(z),'races':n,
                         'direction':direction,'auc_oriented':auc,'top1_pct':100*top1/n if n else np.nan,
                         'top2_pct':100*top2/n if n else np.nan,'month_positive':mg,'month_seen':seen,
                         'month_consistency':mg/seen if seen else np.nan,'month_auc':';'.join(details)})
    return pd.DataFrame(rows).sort_values(['role','auc_oriented','top2_pct'],ascending=[True,False,False])


def families(specs):
    names=list(specs)
    base=[f'v93_{k}' for k in ('grade','national','local','motor','waku','nst','direct') if f'v93_{k}' in specs]
    pos=[x for x in names if category(x)=='POSITION']
    player=[x for x in names if category(x)=='PLAYER_HISTORY']
    prior=[x for x in names if category(x) in ('PRIOR_EXHIBITION','EXHIBITION_FOOT')]
    st=[x for x in names if category(x)=='START']
    # Include score/rank only in the context family; current v96 is separately evaluated as baseline.
    context=[x for x in ('v93_score','v93_rank') if x in specs]
    def uniq(a):return list(dict.fromkeys(a))
    return {
      'BASE7':uniq(base+pos),
      'BASE7_CONTEXT':uniq(base+context+pos),
      'BASE7_PLAYER':uniq(base+player+pos),
      'BASE7_PRIOR':uniq(base+prior+pos),
      'BASE7_ST':uniq(base+st+pos),
      'BASE7_PLAYER_PRIOR':uniq(base+player+prior+pos),
      'ALL_RICH':uniq(base+context+player+prior+st+pos),
    }


def selected_codes():
    if not SEL.exists():return set()
    s=pd.read_csv(SEL,dtype={'race_code':str});s['race_code']=s.race_code.astype(str).str.zfill(12)
    for c in ('PRE','POST','a_score'):s[c]=pd.to_numeric(s[c],errors='coerce')
    is_s=s['is_S'].astype(str).str.lower().isin(('true','1'))
    is_a=(~is_s)&(s.PRE>=.18)&(s.POST>=.18)&(s.a_score>=.28)
    q=s[(s.month.isin(PORT_MONTHS))&(is_s|is_a)]
    return set(q.race_code.astype(str))


def baseline_orders():
    rs=v96.read();return v251.pair_orders(rs)


def pair_rank_from_scores(g,p2,p3):
    s2={int(b):float(p) for b,p in zip(g.boat,p2)};s3={int(b):float(p) for b,p in zip(g.boat,p3)}
    pairs=[]
    for a in BOATS:
        for b in BOATS:
            if a==b:continue
            # log probabilities makes the two role probabilities contribute multiplicatively.
            score=math.log(max(s2.get(a,1e-9),1e-9))+math.log(max(s3.get(b,1e-9),1e-9))
            pairs.append((score,a,b))
    pairs.sort(key=lambda z:(-z[0],z[1],z[2]))
    return [(a,b) for _,a,b in pairs]


def rank_metrics(order,actual):
    try:r=order.index(actual)+1
    except ValueError:r=0
    return r


def evaluate_family(long,fs,name,base_orders,selcodes):
    preds=[]
    for mon in EVAL_MONTHS:
        tr=long[long.month<mon].copy();te=long[long.month==mon].copy()
        train_r=tr.race_code.nunique()
        if train_r<MIN_TRAIN_RACES or te.empty:continue
        use=good_features(tr,fs,.55)
        if len(use)<5:continue
        m2=model();m3=model();m2.fit(tr[use],tr.y2);m3.fit(tr[use],tr.y3)
        te=te.copy();te['p2']=m2.predict_proba(te[use])[:,1];te['p3']=m3.predict_proba(te[use])[:,1]
        for code,g in te.groupby('race_code'):
            if len(g)!=5:continue
            actual2=int(g.loc[g.y2==1,'boat'].iloc[0]);actual3=int(g.loc[g.y3==1,'boat'].iloc[0]);actual=(actual2,actual3)
            new=pair_rank_from_scores(g,g.p2.to_numpy(),g.p3.to_numpy())
            key=(str(g.date.iloc[0]),str(code).zfill(12));old=base_orders.get(key,[])
            p2rank=list(g.sort_values(['p2','boat'],ascending=[False,True]).boat.astype(int));p3rank=list(g.sort_values(['p3','boat'],ascending=[False,True]).boat.astype(int))
            preds.append({'family':name,'month':mon,'date':g.date.iloc[0],'race_code':str(code).zfill(12),
                          'train_races':train_r,'n_features':len(use),
                          'second_top1':int(p2rank[0]==actual2),'second_top2':int(actual2 in p2rank[:2]),
                          'third_top1':int(p3rank[0]==actual3),'third_top2':int(actual3 in p3rank[:2]),
                          'new_pair_rank':rank_metrics(new,actual),'v96_pair_rank':rank_metrics(old,actual),
                          'selected_SA':int(str(code).zfill(12) in selcodes)})
    return pd.DataFrame(preds)


def summarize_pred(p):
    rows=[];monthly=[]
    for fam,g in p.groupby('family'):
        for scope,gg in [('ALL_HEAD',g),('SA_SELECTED',g[(g.selected_SA==1)&g.month.isin(PORT_MONTHS)])]:
            if gg.empty:continue
            rec={'family':fam,'scope':scope,'races':len(gg),'avg_features':gg.n_features.mean(),
                 'second_top1_pct':100*gg.second_top1.mean(),'second_top2_pct':100*gg.second_top2.mean(),
                 'third_top1_pct':100*gg.third_top1.mean(),'third_top2_pct':100*gg.third_top2.mean()}
            for n in (1,2,4,6,10,20):
                rec[f'new_pair_top{n}_pct']=100*((gg.new_pair_rank>0)&(gg.new_pair_rank<=n)).mean()
                rec[f'v96_pair_top{n}_pct']=100*((gg.v96_pair_rank>0)&(gg.v96_pair_rank<=n)).mean()
                rec[f'delta_top{n}_pt']=rec[f'new_pair_top{n}_pct']-rec[f'v96_pair_top{n}_pct']
            rows.append(rec)
        for mon,gg in g.groupby('month'):
            monthly.append({'family':fam,'month':mon,'races':len(gg),
                'new_top4_pct':100*((gg.new_pair_rank>0)&(gg.new_pair_rank<=4)).mean(),
                'v96_top4_pct':100*((gg.v96_pair_rank>0)&(gg.v96_pair_rank<=4)).mean(),
                'new_top6_pct':100*((gg.new_pair_rank>0)&(gg.new_pair_rank<=6)).mean(),
                'v96_top6_pct':100*((gg.v96_pair_rank>0)&(gg.v96_pair_rank<=6)).mean(),
                'new_top10_pct':100*((gg.new_pair_rank>0)&(gg.new_pair_rank<=10)).mean(),
                'v96_top10_pct':100*((gg.v96_pair_rank>0)&(gg.v96_pair_rank<=10)).mean()})
    return pd.DataFrame(rows),pd.DataFrame(monthly)


def main():
    d,_,_=v270.prepare();d=d[d._date<pd.Timestamp('2026-07-01')].copy();d['date']=d.date.astype(str)
    specs=feature_specs(d);long=build_long(d,specs)
    if long.empty:raise RuntimeError('no boat-4 head opponent rows')
    uni=univariate(long,specs);uni.to_csv(OUT_UNI,index=False)
    fams=families(specs);base=baseline_orders();selcodes=selected_codes()
    pp=[]
    for name,fs in fams.items():
        q=evaluate_family(long,fs,name,base,selcodes)
        if not q.empty:pp.append(q)
    if not pp:raise RuntimeError('no family predictions')
    pred=pd.concat(pp,ignore_index=True);agg,monthly=summarize_pred(pred)
    agg.to_csv(OUT_FAM,index=False);monthly.to_csv(OUT_MONTH,index=False)

    L=['# v274 4-head opponent feature audit','',
       f'- discovered safe opponent features: **{len(specs)}**',
       f'- conditional boat-4-win races in long data: **{long.race_code.nunique()}**',
       '- Evaluation months: Feb-Jun 2026; every month trains only on earlier boat-4-win races.',
       '- Jul/Aug excluded completely; September not read.',
       '- 2nd and 3rd have separate models; pair score combines role probabilities only after role scoring.',
       '- No odds in feature training/ranking. v96 is the current opponent-order baseline.',
       '- Retrospective feature research/model selection only; not pristine OOS.','']
    for role in ('SECOND','THIRD'):
        q=uni[uni.role==role].sort_values(['auc_oriented','top2_pct'],ascending=False).head(25)
        L += [f'## {role}: strongest individual pre-result features','',
              '|rank|feature|category|direction|AUC|Top1|Top2|month +|',
              '|---:|---|---|---|---:|---:|---:|---:|']
        for i,(_,r) in enumerate(q.iterrows(),1):
            L.append(f'|{i}|{r.feature}|{r.category}|{r.direction}|{r.auc_oriented:.4f}|{r.top1_pct:.1f}%|{r.top2_pct:.1f}%|{int(r.month_positive)}/{int(r.month_seen)}|')
        L.append('')
    L += ['## Walk-forward family comparison: all boat-4 wins','',
          '|family|R|2nd T1|2nd T2|3rd T1|3rd T2|pair T2|T4|T6|T10|v96 T10|ΔT10|',
          '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for _,r in agg[agg.scope=='ALL_HEAD'].sort_values(['new_pair_top10_pct','new_pair_top6_pct'],ascending=False).iterrows():
        L.append(f'|{r.family}|{int(r.races)}|{r.second_top1_pct:.1f}%|{r.second_top2_pct:.1f}%|{r.third_top1_pct:.1f}%|{r.third_top2_pct:.1f}%|{r.new_pair_top2_pct:.1f}%|{r.new_pair_top4_pct:.1f}%|{r.new_pair_top6_pct:.1f}%|{r.new_pair_top10_pct:.1f}%|{r.v96_pair_top10_pct:.1f}%|{r.delta_top10_pt:+.1f}pt|')
    sa=agg[agg.scope=='SA_SELECTED'].sort_values(['new_pair_top10_pct','new_pair_top6_pct'],ascending=False)
    L += ['','## Frozen v268+v273 S+A selected head-wins (Apr-Jun)','',
          'This scope changes only opponent ordering; the frozen head selectors are not retuned.','',
          '|family|4-head hit R|pair T2|T4|T6|T10|v96 T2|T4|T6|T10|ΔT10|',
          '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for _,r in sa.iterrows():
        L.append(f'|{r.family}|{int(r.races)}|{r.new_pair_top2_pct:.1f}%|{r.new_pair_top4_pct:.1f}%|{r.new_pair_top6_pct:.1f}%|{r.new_pair_top10_pct:.1f}%|{r.v96_pair_top2_pct:.1f}%|{r.v96_pair_top4_pct:.1f}%|{r.v96_pair_top6_pct:.1f}%|{r.v96_pair_top10_pct:.1f}%|{r.delta_top10_pt:+.1f}pt|')
    # Robust choice for next stage: prioritize T6/T10 lift with no obvious T4 sacrifice.
    if len(sa):
        z=sa.copy();z['score']=z.delta_top10_pt+.6*z.delta_top6_pt+.25*z.delta_top4_pt
        best=z.sort_values(['score','delta_top10_pt','delta_top6_pt'],ascending=False).iloc[0]
        L += ['','## Research decision',
              f'- Best S+A expansion family by pre-declared coverage score: **{best.family}**.',
              f'- On selected boat-4 wins: Top4 {best.new_pair_top4_pct:.1f}% vs v96 {best.v96_pair_top4_pct:.1f}%, Top6 {best.new_pair_top6_pct:.1f}% vs {best.v96_pair_top6_pct:.1f}%, Top10 {best.new_pair_top10_pct:.1f}% vs {best.v96_pair_top10_pct:.1f}%.',
              '- Do not adopt from v274 alone. Next stage should freeze the best feature family and test exact current 10,000-yen Dutch/composite-odds economics against v96 on the same frozen S+A races.',
              '- Any opponent model intended for prospective use must be frozen before September outcomes are inspected.']
    SUM.write_text('\n'.join(L)+'\n',encoding='utf-8');print('\n'.join(L))

if __name__=='__main__':main()
