#!/usr/bin/env python3
"""Exact frozen A-LIVE variable-N rescue research for HEAD4_V291_COMP7.

The old v288 all-N table labels A using historical v271 OOF identities.  Frozen
A-LIVE uses a final <=2026-06-30 artifact and can select different race
identities even when aggregate counts are similar.  This script therefore
reconstructs exact A-LIVE identities first, audits odds-curve coverage, and only
runs rescue optimization if every exact A-LIVE race has a complete archived
pre-deadline N=2..20 curve.  Partial identity reuse is prohibited.

BASE v291 stays immutable.  Jul/Aug outcomes and all September outcomes are
excluded.  No v96 production signal is used.
"""
from __future__ import annotations
from pathlib import Path
import json
import numpy as np
import pandas as pd

import analyze_v270_4head_win_feature_importance as v270
import analyze_v271_4head_arank_expansion as v271
from head4_v273_a_live_inference import load_artifact, score_a

ROOT=Path(__file__).resolve().parent
SRC=ROOT/'analysis_v288_4head_composite_odds_alln_detail.csv'
OUT=ROOT/'analysis_4head_v291_a_targetcomp_rescue.csv'
MONTH=ROOT/'analysis_4head_v291_a_targetcomp_rescue_monthly.csv'
LOMO=ROOT/'analysis_4head_v291_a_targetcomp_rescue_lomo.csv'
SUM=ROOT/'summary_4head_v291_a_targetcomp_rescue.md'
CAND=ROOT/'head4_v291_a_targetcomp_rescue_candidate.json'
AUDIT=ROOT/'audit_4head_v291_a_live_identity.json'
BANK=10000
MONTHS=('2026-04','2026-05','2026-06')
TARGETS=tuple(np.arange(5.0,15.01,.5).round(2))
MAXNS=(4,6,8,10,12,16,20)
FLOORS=tuple(np.arange(3.0,8.01,.5).round(2))
GRID=[(float(t),int(n),float(f)) for t in TARGETS for n in MAXNS for f in FLOORS]
CUTOFF=pd.Timestamp('2026-06-30')


def met(g):
    if len(g)==0:return {'R':0,'return_yen':0.,'profit_yen':0.,'roi_pct':np.nan,'head_rate_pct':np.nan,'hit_rate_pct':np.nan,'avg_n':np.nan,'avg_comp_odds':np.nan}
    ret=float(g.return_yen.sum());cost=len(g)*BANK
    return {'R':int(len(g)),'return_yen':ret,'profit_yen':ret-cost,'roi_pct':100*ret/cost,
            'head_rate_pct':100*float(g.head4_win.mean()),'hit_rate_pct':100*float(g.hit.mean()),
            'avg_n':float(g.n.mean()),'avg_comp_odds':float(g.comp_odds.mean())}


def load_curves():
    q=pd.read_csv(SRC,dtype={'race_code':str});q['race_code']=q.race_code.astype(str).str.zfill(12)
    if set(q.month.astype(str).unique())!=set(MONTHS):raise RuntimeError('forbidden month in all-N source')
    if q.race_code.nunique()!=100 or len(q)!=1900:raise RuntimeError('expected exactly 100 races x N2..20')
    if set(q.n.astype(int).unique())!=set(range(2,21)):raise RuntimeError('N universe mismatch')
    for code,g in q.groupby('race_code'):
        z=g.sort_values('n')
        if len(z)!=19 or z.n.nunique()!=19:raise RuntimeError(f'incomplete N curve {code}')
        if np.any(np.diff(z.comp_odds.to_numpy(float))>1e-9):raise RuntimeError(f'non-monotone composite curve {code}')
    return q


def exact_a_live_ids(q):
    artifact=load_artifact()
    oof=v271.oof_a_scores().copy();oof['race_code']=oof.race_code.astype(str).str.zfill(12)
    oof=oof[oof.month.astype(str).isin(MONTHS)].copy()
    pre=pd.to_numeric(oof.PRE,errors='coerce');post=pd.to_numeric(oof.POST,errors='coerce');env=pd.to_numeric(oof.ENV_ENTRY,errors='coerce')
    sg=artifact['S_gate'];ag=artifact['A_gate']
    outside_s=~((pre>=sg['PRE'])&(post>=sg['POST'])&(env>=sg['ENV_ENTRY']))
    elig=oof[(pre>=ag['PRE'])&(post>=ag['POST'])&outside_s][['race_code','month','PRE','POST','ENV_ENTRY']].copy()
    if len(elig)!=int(artifact['mapping']['reference_R']):raise RuntimeError(f'A reference size mismatch {len(elig)}')

    d,_,_=v270.prepare();d=d.copy();d['_date']=pd.to_datetime(d['_date'],errors='coerce');d=d[d._date<=CUTOFF].copy()
    fs=list(artifact['A_SCORE']['features']);missing=[c for c in fs if c not in d.columns]
    if missing:raise RuntimeError('missing exact A-LIVE features: '+','.join(missing))
    ref=d[['race_code',*fs]].copy();ref['race_code']=ref.race_code.astype(str).str.zfill(12)
    z=elig.merge(ref,on='race_code',how='left',validate='one_to_one',indicator=True)
    if not z._merge.eq('both').all():raise RuntimeError('A-LIVE reconstruction feature rows missing')
    z['a_live_score']=[score_a(r,artifact) for r in z[fs].to_dict('records')]
    cut=float(artifact['A_gate']['A_SCORE_LIVE']);live=z[z.a_live_score>=cut].copy()
    if len(live)!=int(artifact['mapping']['mapped_selected_R']):raise RuntimeError(f'A-LIVE selected count mismatch {len(live)}')

    old=set(q.loc[q.layer.astype(str).eq('A'),'race_code'].unique())
    new=set(live.race_code.unique())
    curve_counts=q.groupby('race_code').n.nunique().to_dict()
    missing_curves=sorted(c for c in new if int(curve_counts.get(c,0))!=19)
    audit={
      'schema':'head4_v291_a_live_identity_audit_v1','development_months':list(MONTHS),
      'jul_aug_outcomes_used':False,'september_outcomes_used':False,'v96_used':False,
      'artifact_policy':artifact['policy'],'artifact_cutoff':artifact['frozen_training_cutoff'],
      'mapped_live_threshold':cut,'reference_R':int(len(elig)),'exact_a_live_R':int(len(new)),
      'old_oof_A_curve_R':int(len(old)),'identity_overlap_R':int(len(new&old)),
      'identity_added_vs_old_R':int(len(new-old)),'identity_dropped_vs_old_R':int(len(old-new)),
      'identity_sets_equal':bool(new==old),'complete_curve_coverage_R':int(sum(int(curve_counts.get(c,0))==19 for c in new)),
      'missing_curve_R':int(len(missing_curves)),'missing_curve_race_codes':missing_curves,
      'status':'PASS_EXACT_CURVES_AVAILABLE' if not missing_curves else 'BLOCKED_MISSING_EXACT_PREDEADLINE_ODDS_CURVES'
    }
    AUDIT.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return live,audit


def frozen_base(q,months=MONTHS):
    z=q[(q.month.isin(months))&(q.n==4)&(q.comp_odds>=7.0)].copy()
    if z.race_code.duplicated().any():raise RuntimeError('duplicate frozen base race')
    return z


def rescue_universe(q,live_ids,months=MONTHS):
    b=set(frozen_base(q,months).race_code);ids=set(live_ids)
    return q[(q.month.isin(months))&(q.race_code.isin(ids))&(~q.race_code.isin(b))].copy()


def select(q,live_ids,target,maxn,floor,months=MONTHS):
    z=rescue_universe(q,live_ids,months);z=z[(z.n>=2)&(z.n<=int(maxn))].copy()
    if z.empty:return z
    z['dist']=(z.comp_odds-float(target)).abs()
    r=z.sort_values(['race_code','dist','n']).groupby('race_code',as_index=False).head(1).copy()
    r=r[r.comp_odds>=float(floor)].copy()
    if r.race_code.duplicated().any():raise RuntimeError('duplicate rescue selection')
    return r


def summarize(q,live_ids,target,maxn,floor,months=MONTHS):
    r=select(q,live_ids,target,maxn,floor,months);rm=met(r);mrs=[]
    for m in months:
        x=met(r[r.month==m]);mrs.append({'target':target,'maxn':maxn,'floor':floor,'month':m,**x})
    md=pd.DataFrame(mrs);valid=md[md.R>0]
    return {'target':target,'maxn':maxn,'floor':floor,**rm,
            'min_month_R':int(md.R.min()) if len(md) else 0,
            'min_month_roi_pct':float(valid.roi_pct.min()) if len(valid) else np.nan},mrs


def choose(tab):
    tiers=[
      ('STRONG_ALL_MONTHS',(tab.R>=12)&(tab.min_month_R>=2)&(tab.roi_pct>=140)&(tab.min_month_roi_pct>=120)),
      ('SAFE_ALL_MONTHS',(tab.R>=12)&(tab.min_month_R>=2)&(tab.roi_pct>=125)&(tab.min_month_roi_pct>=110)),
      ('POSITIVE_ALL_MONTHS',(tab.R>=9)&(tab.min_month_R>=2)&(tab.roi_pct>=115)&(tab.min_month_roi_pct>=100)),
    ]
    for name,mask in tiers:
        z=tab[mask].sort_values(['R','min_month_roi_pct','roi_pct','avg_n'],ascending=[False,False,False,True])
        if len(z):return name,z.iloc[0]
    return 'NO_STANDALONE_SAFE_CANDIDATE',None


def lomo(q,live_ids):
    rows=[]
    for hold in MONTHS:
        trmons=tuple(m for m in MONTHS if m!=hold);rec=[]
        for t,n,f in GRID:rec.append(summarize(q,live_ids,t,n,f,trmons)[0])
        tier,ch=choose(pd.DataFrame(rec))
        if ch is None:rows.append({'holdout_month':hold,'status':'NO_TRAIN_CANDIDATE'});continue
        r=select(q,live_ids,float(ch.target),int(ch.maxn),float(ch.floor),(hold,));x=met(r)
        rows.append({'holdout_month':hold,'status':'OK','train_tier':tier,'target':float(ch.target),'maxn':int(ch.maxn),
                     'floor':float(ch.floor),'hold_R':x['R'],'hold_roi_pct':x['roi_pct'],'hold_profit_yen':x['profit_yen'],
                     'hold_avg_n':x['avg_n'],'hold_comp_odds':x['avg_comp_odds']})
    return pd.DataFrame(rows)


def blocked_outputs(q,audit):
    pd.DataFrame(columns=['target','maxn','floor','R','roi_pct']).to_csv(OUT,index=False)
    pd.DataFrame(columns=['target','maxn','floor','month','R','roi_pct']).to_csv(MONTH,index=False)
    pd.DataFrame(columns=['holdout_month','status']).to_csv(LOMO,index=False)
    payload={'schema':'head4_v291_a_targetcomp_rescue_v2','development_months':list(MONTHS),'jul_aug_outcomes_used':False,
             'september_outcomes_used':False,'v96_used':False,'base':{'policy':'HEAD4_V291_COMP7','R':int(len(frozen_base(q))),'immutable':True},
             'selection_tier':'BLOCKED_IDENTITY_COVERAGE','status':'REJECT_OLD_OOF_IDENTITY_REUSE','identity_audit':audit}
    CAND.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    SUM.write_text('# HEAD4 v291 exact A-LIVE variable-N rescue\n\n- **RESEARCH BLOCKED / NO PROMOTION.**\n- Frozen A-LIVE identities were reconstructed before ticket optimization.\n- Old v288 OOF-A identities are not allowed as a substitute.\n- Exact archived pre-deadline all-N odds curves are missing for one or more frozen A-LIVE identities.\n- Current `HEAD4_V291_COMP7` remains unchanged.\n\n## Identity audit\n\n```json\n'+json.dumps(audit,ensure_ascii=False,indent=2)+'\n```\n',encoding='utf-8')


def main():
    q=load_curves();live,audit=exact_a_live_ids(q);live_ids=set(live.race_code)
    if audit['missing_curve_R']:
        blocked_outputs(q,audit);print(SUM.read_text(encoding='utf-8'));return
    rows=[];mrows=[]
    for t,n,f in GRID:
        s,m=summarize(q,live_ids,t,n,f);rows.append(s);mrows.extend(m)
    A=pd.DataFrame(rows);M=pd.DataFrame(mrows);tier,ch=choose(A);L=lomo(q,live_ids)
    A.to_csv(OUT,index=False);M.to_csv(MONTH,index=False);L.to_csv(LOMO,index=False)
    bm=met(frozen_base(q));lomo_ok=bool(len(L)==3 and L.status.eq('OK').all() and (L.hold_R>=1).all() and (L.hold_roi_pct>=100).all())
    payload={'schema':'head4_v291_a_targetcomp_rescue_v2','development_months':list(MONTHS),'jul_aug_outcomes_used':False,
             'september_outcomes_used':False,'v96_used':False,'base':{'policy':'HEAD4_V291_COMP7','R':bm['R'],'immutable':True},
             'selection_tier':tier,'lomo_all_holdouts_profitable':lomo_ok,'identity_audit':audit}
    lines=['# HEAD4 v291 exact A-LIVE target-composite variable-N rescue','',
           '- BASE HEAD4_V291_COMP7 is immutable.','- Rescue identities come from the frozen A-LIVE artifact, not old OOF A labels.',
           '- Exact all-N archived curves are required for every frozen A-LIVE identity.','- Jul/Aug/Sep outcomes excluded; no v96.','',
           f'- Identity sets equal to old OOF A: **{"YES" if audit["identity_sets_equal"] else "NO"}**.',
           f'- Exact A-LIVE R={audit["exact_a_live_R"]}; overlap={audit["identity_overlap_R"]}; added={audit["identity_added_vs_old_R"]}; dropped={audit["identity_dropped_vs_old_R"]}.',
           f'- BASE: **{bm["R"]}R / ROI {bm["roi_pct"]:.2f}%**.','',f'## Selection: {tier}']
    if ch is None:lines+=['','No exact A-LIVE target-composite rescue passed standalone all-month safety tiers.']
    else:
        payload['candidate']={'target':float(ch.target),'maxn':int(ch.maxn),'floor':float(ch.floor),'R':int(ch.R),'roi_pct':float(ch.roi_pct),
                              'min_month_roi_pct':float(ch.min_month_roi_pct),'avg_n':float(ch.avg_n),'avg_comp_odds':float(ch.avg_comp_odds),
                              'status':'RESEARCH_CANDIDATE_NOT_FROZEN' if lomo_ok else 'REJECT_LOMO'}
        lines += ['',f'- Rule: **target={ch.target:.1f}, maxN={int(ch.maxn)}, floor={ch.floor:.1f}**',
                  f'- Added standalone: **{int(ch.R)}R / ROI {ch.roi_pct:.2f}% / monthly floor {ch.min_month_roi_pct:.2f}%**',
                  f'- avg N {ch.avg_n:.2f} / avg composite {ch.avg_comp_odds:.3f}.','',
                  '|month|R|ROI|profit|avg N|','|---|---:|---:|---:|---:|']
        mm=M[(M.target==ch.target)&(M.maxn==ch.maxn)&(M.floor==ch.floor)].sort_values('month')
        for _,r in mm.iterrows():lines.append(f'|{r.month}|{int(r.R)}|{r.roi_pct:.2f}%|{r.profit_yen:+.0f}円|{r.avg_n:.2f}|')
    lines += ['','## LOMO','','|holdout|train rule|hold R|hold ROI|hold profit|','|---|---|---:|---:|---:|']
    for _,r in L.iterrows():
        if r.status!='OK':lines.append(f'|{r.holdout_month}|NO_TRAIN_CANDIDATE|-|-|-|')
        else:lines.append(f'|{r.holdout_month}|target {r.target:.1f} / maxN {int(r.maxn)} / floor {r.floor:.1f}|{int(r.hold_R)}|{r.hold_roi_pct:.2f}%|{r.hold_profit_yen:+.0f}円|')
    lines += ['',f'- All held-out rescue ROIs >=100%: **{"YES" if lomo_ok else "NO"}**.','',
              '## Promotion guard','- Promotion requires standalone safety + all three LOMO holdouts >=100%.',
              '- Any missing exact pre-deadline odds curve blocks promotion.','- New policy ID required; v291 remains unchanged.']
    CAND.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');SUM.write_text('\n'.join(lines)+'\n',encoding='utf-8');print('\n'.join(lines))

if __name__=='__main__':main()
