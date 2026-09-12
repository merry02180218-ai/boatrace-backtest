#!/usr/bin/env python3
"""v317: error-driven causal PRE/prior feature engineering for SECOND.

Frozen boat-1 cohort: v308 345 races / 290 boat-1 wins.
Uses v313 causal cache only; no meet_*; no future backfill.
SECOND remains the target because v316 still leaves outer 4/5/6 as the dominant error.
THIRD stays frozen at v300 conditional L2=.1 for attribution.
Feb-Jun development only; Jul/Aug NON-PRISTINE; September outcomes unread.
"""
from pathlib import Path
import numpy as np
import pandas as pd

import analyze_v298_1head_threat_listwise_trifecta5 as v298
import run_v300_1head_trifecta3_feature_upgrade as v300
import run_v309_1head_opponent_zero_base_audit as v309
import run_v310_1head_opponent_headrisk_second as v310
import run_v311_1head_opponent_second_family_autoresearch as v311
import run_v312_1head_opponent_outer_gate as v312

ROOT=Path(__file__).resolve().parent
SEL=ROOT/'analysis_v308_1head_volume_opponent_joint_best_selected.csv'
P=ROOT/'analysis_v317_1head_opponent_error_features'
S=ROOT/'summary_v317_1head_opponent_error_features.md'
TM=list(v298.TEST_MONTHS)


def safe_source_features(df):
    """Choose only already-audited causal/pre-race numeric columns for interactions."""
    out=[]
    tokens=('v310_','motor','pl_','grade','wr','local','f_safety','pos_','turn','straight','overall','vh_','gh_','cand_','diff1_','innermax_')
    for c in v311.audited_features(df):
        s=str(c)
        if 'meet_' in s:
            raise RuntimeError(f'v317 forbidden meet feature {c}')
        if any(t in s for t in tokens):
            out.append(c)
    # deterministic cap protects the small development sample from feature explosion
    return sorted(out)[:80]


def add_engineered(sl, mode):
    z=sl.copy()
    b=pd.to_numeric(z['boat'],errors='coerce').fillna(0).astype(int)
    z['v317_outer456']=b.isin([4,5,6]).astype(float)
    z['v317_boat4']=(b==4).astype(float)
    z['v317_boat5']=(b==5).astype(float)
    z['v317_boat6']=(b==6).astype(float)
    src=safe_source_features(z)
    if mode=='BASE':
        return z,[]
    added=[]
    for c in src:
        x=pd.to_numeric(z[c],errors='coerce')
        # Route-conditioned interactions target the observed 4/5/6 SECOND failures.
        name=f'v317_outer__{c}'
        z[name]=x*z['v317_outer456']; added.append(name)
        if mode in ('BOAT56','FULL'):
            n5=f'v317_b5__{c}'; n6=f'v317_b6__{c}'
            z[n5]=x*z['v317_boat5']; z[n6]=x*z['v317_boat6']; added += [n5,n6]
    # Explicit geometry/head-risk interactions are cheap, causal transforms.
    hr=[c for c in src if str(c).startswith('v310_')]
    for c in hr[:20]:
        x=pd.to_numeric(z[c],errors='coerce')
        n=f'v317_boatnum__{c}'; z[n]=x*b.astype(float); added.append(n)
    if mode=='HEADRISK':
        keep=set(hr)
        drop=[c for c in added if not any(h in c for h in keep)]
        z=z.drop(columns=drop,errors='ignore'); added=[c for c in added if c not in drop]
    return z,added


def evaluate(p2,pc,d,ids):
    rows=[]
    for tm in TM:
        q=d[(d.month==tm)&(d.race_code.isin(ids))].copy()
        for _,r in q.iterrows():
            code=str(r.race_code).zfill(12); parts=str(r.actual_combo).split('-')
            if len(parts)!=3: continue
            a1,a2,a3=map(int,parts)
            p2m=p2[tm][code]; pcm=pc[tm][code]
            sr=v309.rank_of(p2m,a2) if a1==1 else np.nan
            tickets=v300.ticket3(p2m,pcm).split(';')
            rows.append({'month':tm,'race_code':code,'head_hit':int(a1==1),'actual2':a2,'actual3':a3,'second_rank':sr,
                         'second_top1':int(a1==1 and pd.notna(sr) and sr<=1),
                         'second_top2':int(a1==1 and pd.notna(sr) and sr<=2),
                         'second_top3':int(a1==1 and pd.notna(sr) and sr<=3),
                         'exact3':int(str(r.actual_combo) in tickets)})
    z=pd.DataFrame(rows)
    if len(z)!=345 or int(z.head_hit.sum())!=290:
        raise RuntimeError(f'v317 frozen mismatch R={len(z)} head={int(z.head_hit.sum())}')
    h=z[z.head_hit==1].copy(); mon=h.groupby('month').second_top2.mean(); by=h.groupby('actual2').second_top2.mean().to_dict()
    return z,{'R':345,'head_hits':290,'exact3_hits':int(z.exact3.sum()),'exact3_rate':float(z.exact3.mean()),
              'second_top1':float(h.second_top1.mean()),'second_top2':float(h.second_top2.mean()),'second_top3':float(h.second_top3.mean()),
              'worst_month_second_top2':float(mon.min()),'outer456_top2':float(h[h.actual2.isin([4,5,6])].second_top2.mean()),
              'boat2_top2':float(by.get(2,np.nan)),'boat3_top2':float(by.get(3,np.nan)),'boat4_top2':float(by.get(4,np.nan)),
              'boat5_top2':float(by.get(5,np.nan)),'boat6_top2':float(by.get(6,np.nan))}


def main():
    frozen=pd.read_csv(SEL,dtype={'race_code':str}); frozen['race_code']=frozen.race_code.astype(str).str.zfill(12)
    if len(frozen)!=345: raise RuntimeError('v317 frozen cohort changed')
    ids=set(frozen.race_code)
    d,p3,p4=v312.load_cache(); d['race_code']=d.race_code.astype(str).str.zfill(12)
    q=d[d.race_code.isin(ids)]
    if len(q)!=345 or int(q.head_hit.sum())!=290: raise RuntimeError('v317 cache frozen mismatch')
    v300.setup_v298(); sufs=v298.suffixes(d)
    if any('meet_' in str(x) for x in sufs): raise RuntimeError('v317 forbidden meet suffix')
    sl=v310.add_headrisk(v300.augment_second(v298.second_long(d,sufs)),p3,p4)
    cl=v300.augment_third(v298.conditional_long(d,sufs))
    pc={tm:v300.pc_predict(cl,tm,.1,True)[0] for tm in TM}

    configs=[]
    for mode in ('BASE','OUTER','HEADRISK','BOAT56','FULL'):
        for l2 in ((3.0,) if mode=='BASE' else (1.0,3.0,10.0)):
            configs.append((f'{mode}_L2_{l2:g}',mode,l2))

    sums=[]; outs=[]; featmeta=[]
    for name,mode,l2 in configs:
        sx,added=add_engineered(sl,mode)
        p2={}; nf=[]
        for tm in TM:
            # Preserve the strongest clean v311 formulation by dropping START.
            pred,fs=v311.p2_predict_explicit(sx,tm,l2,None,{'START'})
            p2[tm]=pred; nf.append(len(fs))
            if any('meet_' in str(c) for c in fs): raise RuntimeError('v317 meet leakage in fitted features')
        z,m=evaluate(p2,pc,d,ids); z['config']=name; outs.append(z)
        m.update({'config':name,'mode':mode,'l2':l2,'added_features':len(added),'min_fit_features':min(nf),'max_fit_features':max(nf)})
        sums.append(m); featmeta.append({'config':name,'mode':mode,'l2':l2,'added_features':len(added)})
        print('v317',name,m,flush=True)

    sm=pd.DataFrame(sums); base=sm[sm.config=='BASE_L2_3'].iloc[0]
    sm['delta_top2_pp']=100*(sm.second_top2-base.second_top2)
    sm['delta_outer_pp']=100*(sm.outer456_top2-base.outer456_top2)
    sm['delta_exact3_pp']=100*(sm.exact3_rate-base.exact3_rate)
    cand=sm[sm.config!='BASE_L2_3'].sort_values(['second_top2','worst_month_second_top2','outer456_top2','exact3_rate'],ascending=False)
    best=cand.iloc[0]
    allz=pd.concat(outs,ignore_index=True); bz=allz[allz.config==best.config].copy(); bh=bz[bz.head_hit==1]
    by=bh.groupby('actual2').agg(R=('race_code','size'),top1=('second_top1','mean'),top2=('second_top2','mean'),top3=('second_top3','mean'),exact3=('exact3','mean')).reset_index()
    mon=bz.groupby('month').agg(R=('race_code','size'),head=('head_hit','sum'),exact3=('exact3','mean')).reset_index().merge(
        bh.groupby('month').agg(second_top1=('second_top1','mean'),second_top2=('second_top2','mean'),second_top3=('second_top3','mean')).reset_index(),on='month')

    sm.to_csv(str(P)+'_configs.csv',index=False); pd.DataFrame(featmeta).to_csv(str(P)+'_feature_meta.csv',index=False)
    by.to_csv(str(P)+'_best_by_second.csv',index=False); mon.to_csv(str(P)+'_best_monthly.csv',index=False); bz.to_csv(str(P)+'_best_race.csv',index=False)
    L=['# v317 error-driven causal SECOND feature engineering','',
       '- Fixed v308 cohort: **345 races / 290 boat-1 wins**; IDs unchanged.',
       '- v313 cache only; no `meet_*`; no future backfill; month M trains only before M.',
       '- Derived interactions use only already-audited PRE/prior features and candidate boat/route identity.',
       '- START family remains dropped; THIRD frozen at v300 conditional L2=.1.',
       '- Feb-Jun development only; Jul/Aug NON-PRISTINE; September outcomes unread.','',
       '## Development result',
       f'- DROP_START base TOP2 {100*base.second_top2:.2f}%, outer {100*base.outer456_top2:.2f}%, exact3 {int(base.exact3_hits)}/345={100*base.exact3_rate:.2f}%, worst month {100*base.worst_month_second_top2:.2f}%.',
       f'- Best **{best.config}** TOP2 **{100*best.second_top2:.2f}%**, outer **{100*best.outer456_top2:.2f}%**, exact3 **{int(best.exact3_hits)}/345={100*best.exact3_rate:.2f}%**, worst month **{100*best.worst_month_second_top2:.2f}%**.','',
       '## Best by actual SECOND','|boat|R|TOP1|TOP2|TOP3|exact3|','|---:|---:|---:|---:|---:|---:|']
    for _,r in by.iterrows(): L.append(f'|{int(r.actual2)}|{int(r.R)}|{100*r.top1:.2f}%|{100*r.top2:.2f}%|{100*r.top3:.2f}%|{100*r.exact3:.2f}%|')
    L+=['','## Monthly','|month|R|head|TOP1|TOP2|TOP3|exact3|','|---|---:|---:|---:|---:|---:|---:|']
    for _,r in mon.iterrows(): L.append(f'|{r.month}|{int(r.R)}|{int(r["head"])}|{100*r.second_top1:.2f}%|{100*r.second_top2:.2f}%|{100*r.second_top3:.2f}%|{100*r.exact3:.2f}%|')
    L+=['','## Automatic decision rule','- If v317 remains weak/unstable, SECOND model classes are considered saturated enough to rebuild conditional THIRD next.','- If v317 materially improves SECOND without collapsing inner boats/month stability, preserve the feature set and then rebuild THIRD.','- Any suspicious large gain requires leakage/causal audit before acceptance.']
    S.write_text('\n'.join(L)+'\n',encoding='utf-8'); print(S.read_text(),flush=True)

if __name__=='__main__': main()
