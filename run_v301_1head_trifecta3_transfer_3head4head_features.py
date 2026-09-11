#!/usr/bin/env python3
"""v301: transfer proven 3-head/4-head feature structures into 1-head 3-ticket opponent ranking.

Development-only research. Jul/Aug remain NON-PRISTINE and September outcomes are unread.
The race denominator and ticket policy stay frozen to v299/v300 so any gain comes from
SECOND/THIRD ranking features only.

Transferred concepts:
- 3-head v288: relative ST edge, wall weakness, inner-ST pressure, motor edge.
- 4-head v291/v268: historical ST edge, inner resistance, motor history, prior turn/foot,
  racer/form history.

These are generalized to every opponent candidate/pair rather than hard-coding boat 3/4.
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd

import analyze_v298_1head_threat_listwise_trifecta5 as v298
import run_v300_1head_trifecta3_feature_upgrade as v300

ROOT=Path(__file__).resolve().parent
PREFIX=ROOT/'analysis_v301_1head_trifecta3_transfer_3head4head'
SUMMARY=ROOT/'summary_v301_1head_trifecta3_transfer_3head4head.md'

START_TOKENS=('nst','st_','start','waku_st','hist_st')
MOTOR_TOKENS=('motor',)
TURN_TOKENS=('turn','foot','mawari','exh','tenji')
FORM_TOKENS=('pl_','wr','local','grade','racer','win','past')


def _match(k,toks):
    x=k.lower()
    return any(t in x for t in toks)


def _target_suffixes(q,prefix='cand_'):
    out=[]
    for c in q.columns:
        if not c.startswith(prefix) or '__' in c:
            continue
        k=c[len(prefix):]
        if _match(k,START_TOKENS+MOTOR_TOKENS+TURN_TOKENS+FORM_TOKENS):out.append(k)
    return sorted(set(out))


def _neighbor_features(q,k):
    c=f'cand_{k}'
    if c not in q:return q
    base=q[['race_code','boat',c]].copy()
    base['boat']=pd.to_numeric(base['boat'],errors='coerce').astype('Int64')
    # For candidate b, inner neighbour is b-1. Shift source b -> target b+1.
    inn=base.copy();inn['boat']=inn['boat']+1;inn=inn.rename(columns={c:f'v300_v301_inner_{k}'})
    out=base.copy();out['boat']=out['boat']-1;out=out.rename(columns={c:f'v300_v301_outer_{k}'})
    q=q.merge(inn,on=['race_code','boat'],how='left').merge(out,on=['race_code','boat'],how='left')
    x=pd.to_numeric(q[c],errors='coerce')
    iv=pd.to_numeric(q[f'v300_v301_inner_{k}'],errors='coerce')
    ov=pd.to_numeric(q[f'v300_v301_outer_{k}'],errors='coerce')
    # boat2 inner neighbour is head=1; recover head value from cand-diff1.
    d1=f'diff1_{k}'
    if d1 in q:
        head=x-pd.to_numeric(q[d1],errors='coerce')
        iv=iv.where(pd.to_numeric(q.boat,errors='coerce')!=2,head)
    q[f'v300_v301_minus_inner_{k}']=x-iv
    q[f'v300_v301_minus_outer_{k}']=x-ov
    im=f'innermax_{k}_minus_cand'
    if im in q:q[f'v300_v301_wall_adv_{k}']=-pd.to_numeric(q[im],errors='coerce')
    return q


def augment_second(sl):
    q=v300.augment_second(sl)
    ks=_target_suffixes(q)
    # Explicit neighbour/wall geometry mirrors the useful 3-head/4-head relative rules.
    for k in ks:
        q=_neighbor_features(q,k)
        pct=f'cand_{k}__pct';cen=f'cand_{k}__center'
        for role in ('pos_edge3','pos_edge4','pos_inner23','pos_outer456'):
            if role not in q:continue
            r=pd.to_numeric(q[role],errors='coerce')
            if pct in q:q[f'v300_v301_{role}_x_{k}_pct']=r*pd.to_numeric(q[pct],errors='coerce')
            if cen in q:q[f'v300_v301_{role}_x_{k}_center']=r*pd.to_numeric(q[cen],errors='coerce')
    starts=[k for k in ks if _match(k,START_TOKENS)]
    motors=[k for k in ks if _match(k,MOTOR_TOKENS)]
    turns=[k for k in ks if _match(k,TURN_TOKENS)]
    # Compact cross-family consensus; cap combinations to avoid feature explosion.
    for sk in starts[:4]:
        sp=f'cand_{sk}__pct'
        if sp not in q:continue
        s=pd.to_numeric(q[sp],errors='coerce')
        for mk in motors[:3]:
            mp=f'cand_{mk}__pct'
            if mp in q:
                m=pd.to_numeric(q[mp],errors='coerce')
                q[f'v300_v301_stmotor_{sk}_{mk}_prod']=s*m
                q[f'v300_v301_stmotor_{sk}_{mk}_min']=pd.concat([s,m],axis=1).min(axis=1)
        for tk in turns[:2]:
            tp=f'cand_{tk}__pct'
            if tp in q:q[f'v300_v301_stturn_{sk}_{tk}_prod']=s*pd.to_numeric(q[tp],errors='coerce')
    return q


def augment_third(cl):
    q=v300.augment_third(cl)
    # Determine transferable suffixes from s_/t_ candidate columns.
    ks=[]
    for c in q.columns:
        if c.startswith('s_cand_') and '__' not in c:
            k=c[len('s_cand_'):]
            if _match(k,START_TOKENS+MOTOR_TOKENS+TURN_TOKENS+FORM_TOKENS):ks.append(k)
    ks=sorted(set(ks))
    for k in ks:
        for side in ('s','t'):
            c=f'{side}_cand_{k}'
            im=f'{side}_innermax_{k}_minus_cand'
            d1=f'{side}_diff1_{k}'
            if im in q:q[f'v300_v301_{side}_wall_adv_{k}']=-pd.to_numeric(q[im],errors='coerce')
            if d1 in q:q[f'v300_v301_{side}_head_edge_{k}']=pd.to_numeric(q[d1],errors='coerce')
        sp=f's_cand_{k}__pct';tp=f't_cand_{k}__pct'
        if sp in q and tp in q:
            s=pd.to_numeric(q[sp],errors='coerce');t=pd.to_numeric(q[tp],errors='coerce')
            q[f'v300_v301_pair_gap_{k}']=t-s
            q[f'v300_v301_pair_weak_{k}']=pd.concat([s,t],axis=1).min(axis=1)
        # Boat-3/4 attack structures transferred as role x relative edge interactions.
        for role in ('pair_second_is3','pair_second_is4','pair_second_inner23','pair_second_outer456','pair_adjacent'):
            if role in q and tp in q:
                q[f'v300_v301_{role}_x_t_{k}']=pd.to_numeric(q[role],errors='coerce')*pd.to_numeric(q[tp],errors='coerce')
    starts=[k for k in ks if _match(k,START_TOKENS)]
    motors=[k for k in ks if _match(k,MOTOR_TOKENS)]
    turns=[k for k in ks if _match(k,TURN_TOKENS)]
    for sk in starts[:4]:
        for side in ('s','t'):
            sp=f'{side}_cand_{sk}__pct'
            if sp not in q:continue
            s=pd.to_numeric(q[sp],errors='coerce')
            for mk in motors[:3]:
                mp=f'{side}_cand_{mk}__pct'
                if mp in q:q[f'v300_v301_{side}_stmotor_{sk}_{mk}']=s*pd.to_numeric(q[mp],errors='coerce')
            for tk in turns[:2]:
                tp=f'{side}_cand_{tk}__pct'
                if tp in q:q[f'v300_v301_{side}_stturn_{sk}_{tk}']=s*pd.to_numeric(q[tp],errors='coerce')
    return q


def make_summary(sel,score,monthly):
    base=score[score.config=='BASE'].iloc[0]
    q=score.copy();q['delta']=q.hit_rate-base.hit_rate
    best=q.sort_values(['hit_rate','worst_month','hits'],ascending=False).head(12);top=best.iloc[0]
    L=['# v301 1HEAD 3-ticket transfer research: 3-head/4-head features','',
       '- Development research only; production unchanged.','- Jul/Aug NON-PRISTINE and excluded upstream; September outcomes unread.',
       '- Same frozen 204-race denominator and TOP2XTOP2 alpha=.60 ticket policy as v299/v300.',
       '- Transferred structures: relative ST/inner-wall pressure, motor edge/history, ST×motor, prior turn/foot, racer/form history.',
       f'- Fixed selected races: **{len(sel)}**; head rate **{100*sel.head_hit.mean():.2f}%**.','',
       '## Results','|config|S L2|T L2|R|hits|hit rate|delta|worst month|','|---|---:|---:|---:|---:|---:|---:|---:|']
    for _,r in best.iterrows():L.append(f"|{r.config}|{r.second_l2:g}|{r.third_l2:g}|{int(r.R)}|{int(r.hits)}|{100*r.hit_rate:.2f}%|{100*r.delta:+.2f}pt|{100*r.worst_month:.2f}%|")
    L+=['','## Monthly best-config audit','|month|R|hits|hit rate|','|---|---:|---:|---:|']
    for _,r in monthly[monthly.config==top.config].iterrows():L.append(f"|{r.month}|{int(r.R)}|{int(r.hits)}|{100*r.hit_rate:.2f}%|")
    L+=['','## Decision']
    L.append(f"- Best v301: **{top.config} = {100*top.hit_rate:.2f}% ({int(top.hits)}/{int(top.R)})**, baseline {100*base.hit_rate:.2f}% ({int(base.hits)}/{int(base.R)}), delta {100*(top.hit_rate-base.hit_rate):+.2f}pt.")
    L.append(f"- Worst-month hit rate: **{100*top.worst_month:.2f}%**.")
    L.append('- Feb-Jun are reused development data; any winning config must be frozen before prospective validation.')
    return '\n'.join(L)+'\n'


def main():
    v300.setup_v298()
    # Monkey-patch v300 augmenters; v300_* prefix keeps BASE truly unchanged.
    v300.augment_second=augment_second
    v300.augment_third=augment_third
    d,_=v298.v294.freeze_true_pre();d=v298.v294.add_prior_history(d);d=v298.v294.add_rel(d);d,threat=v298.add_threat(d)
    fams=v298.v296.clean_manifest(d)
    for fs in fams.values():
        if any('meet_' in c for c in fs):raise RuntimeError('forbidden meeting feature')
    print('v301 PRE features frozen; audited settlement now',flush=True)
    d,cov=v298.v297.settle_full_after_freeze(d);d=d[(d.valid_result==1)&(d.combo_valid==1)].copy()
    p,folds,configs=v300.run(d,fams,threat)
    sel,score,monthly=v300.summarize(p,configs)
    p.to_csv(str(PREFIX)+'_pred.csv',index=False)
    folds.to_csv(str(PREFIX)+'_folds.csv',index=False)
    score.to_csv(str(PREFIX)+'_configs.csv',index=False)
    monthly.to_csv(str(PREFIX)+'_monthly.csv',index=False)
    txt=make_summary(sel,score,monthly);SUMMARY.write_text(txt,encoding='utf-8');print(txt,flush=True)

if __name__=='__main__':main()
