#!/usr/bin/env python3
"""v311: leak-safe SECOND feature-family auto research on frozen 345R.

Purpose
-------
Keep the v308 1-head cohort frozen (345 races / 290 head wins) and automatically
compare SECOND feature families without changing THIRD or the ticket policy.

Causal discipline
-----------------
- Reuses the audited PRE/prior opponent table from v300/v310.
- `meet_*` is forbidden and asserted absent.
- p3/p4 are the causal monthly walk-forward signals from v310; sparse coverage uses
  availability flags + zero sentinel, never future backfill.
- For test month M, SECOND is trained only on rows with month < M.
- Jul/Aug are NON-PRISTINE and are not scored; September outcomes remain unread.
- Boat-1 losses remain misses in exact3 over the full fixed 345 denominator.

This is development-only feature attribution, not production promotion.
"""
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.special import logsumexp

import analyze_v298_1head_threat_listwise_trifecta5 as v298
import run_v300_1head_trifecta3_feature_upgrade as v300
import run_v309_1head_opponent_zero_base_audit as v309
import run_v310_1head_opponent_headrisk_second as v310

ROOT=Path(__file__).resolve().parent
SEL=ROOT/'analysis_v308_1head_volume_opponent_joint_best_selected.csv'
P=ROOT/'analysis_v311_1head_opponent_second_family_autoresearch'
S=ROOT/'summary_v311_1head_opponent_second_family_autoresearch.md'
TM=list(v298.TEST_MONTHS)
META={'date','month','race_code','y2','actual2','actual3','boat'}


def family(c):
    s=str(c)
    if s.startswith('v310_'): return 'HEADRISK'
    if 'nst_strength' in s: return 'START'
    if 'motor' in s: return 'MOTOR'
    if 'pl_' in s: return 'PLAYER'
    if any(k in s for k in ('grade','wr','local','f_safety')): return 'FORM_STATIC'
    if s.startswith('pos_'): return 'POSITION'
    # Geometry/within-race transforms that do not belong to a source family.
    if s.startswith(('cand_','diff1_','innermax_')) or '__center' in s or '__pct' in s or '__gapmax' in s:
        return 'OTHER_SAFE'
    if s.startswith('v300_'): return 'OTHER_SAFE'
    return 'OTHER_SAFE'


def audited_features(df):
    fs=[]
    for c in df.columns:
        if c in META: continue
        if 'meet_' in c: raise RuntimeError(f'forbidden meet feature in SECOND table: {c}')
        x=pd.to_numeric(df[c],errors='coerce')
        if x.notna().mean()>=.55 and x.nunique(dropna=True)>=2: fs.append(c)
    return fs


def p2_predict_explicit(sl,tm,l2,allowed_families=None,drop_families=None):
    tr=sl[sl.month<tm].copy(); te=sl[sl.month==tm].copy()
    fs=audited_features(tr)
    if allowed_families is not None:
        fs=[c for c in fs if family(c) in set(allowed_families)]
    if drop_families:
        fs=[c for c in fs if family(c) not in set(drop_families)]
    if not fs: raise RuntimeError(f'no SECOND features {tm} allowed={allowed_families} drop={drop_families}')
    m=v300.fastbase.FastSecond(float(l2)).fit(tr,fs,'y2')
    te=te.copy(); te['score']=m.score(te)
    out={}
    for code,g in te.groupby('race_code'):
        out[str(code).zfill(12)]=v298.v279.probs_within_race(g,'score')
    return out,fs


def evaluate(p2,pc,d,ids):
    rows=[]
    for tm in TM:
        q=d[d.month==tm].copy(); q['race_code']=q.race_code.astype(str).str.zfill(12); q=q[q.race_code.isin(ids)]
        for _,r in q.iterrows():
            code=r.race_code; parts=str(r.actual_combo).split('-')
            if len(parts)!=3: continue
            a1,a2,a3=map(int,parts); p2m=p2[tm][code]; pcm=pc[tm][code]
            sr=v309.rank_of(p2m,a2) if a1==1 else np.nan
            tickets=v300.ticket3(p2m,pcm).split(';')
            rows.append({'month':tm,'race_code':code,'head_hit':int(a1==1),'actual2':a2,
                         'second_rank':sr,
                         'second_top1':int(a1==1 and pd.notna(sr) and sr<=1),
                         'second_top2':int(a1==1 and pd.notna(sr) and sr<=2),
                         'second_top3':int(a1==1 and pd.notna(sr) and sr<=3),
                         'exact3':int(str(r.actual_combo) in tickets)})
    z=pd.DataFrame(rows)
    if len(z)!=345 or int(z.head_hit.sum())!=290:
        raise RuntimeError(f'frozen cohort mismatch R={len(z)} head={int(z.head_hit.sum())}')
    h=z[z.head_hit==1]
    by=h.groupby('actual2').second_top2.mean().to_dict()
    mon=h.groupby('month').second_top2.mean()
    return z,{
        'R':len(z),'head_hits':int(z.head_hit.sum()),
        'exact3_hits':int(z.exact3.sum()),'exact3_rate':float(z.exact3.mean()),
        'second_top1':float(h.second_top1.mean()),'second_top2':float(h.second_top2.mean()),'second_top3':float(h.second_top3.mean()),
        'worst_month_second_top2':float(mon.min()),
        'boat2_top2':float(by.get(2,np.nan)),'boat3_top2':float(by.get(3,np.nan)),
        'boat4_top2':float(by.get(4,np.nan)),'boat5_top2':float(by.get(5,np.nan)),'boat6_top2':float(by.get(6,np.nan)),
        'outer456_top2':float(h[h.actual2.isin([4,5,6])].second_top2.mean())
    }


def main():
    frozen=pd.read_csv(SEL,dtype={'race_code':str}); frozen['race_code']=frozen.race_code.astype(str).str.zfill(12)
    if len(frozen)!=345: raise RuntimeError(f'expected 345 frozen races, got {len(frozen)}')
    ids=set(frozen.race_code)

    # Independent causal p3/p4 maps. Missing cross-pipeline coverage stays explicit.
    p3=v310.causal_p3_map(); p4=v310.causal_p4_map()

    v300.setup_v298()
    d,_=v298.v294.freeze_true_pre(); d=v298.v294.add_prior_history(d); d=v298.v294.add_rel(d); d,_=v298.add_threat(d)
    d,_=v298.v297.settle_full_after_freeze(d); d=d[(d.valid_result==1)&(d.combo_valid==1)].copy()
    sufs=v298.suffixes(d)
    if any('meet_' in x for x in sufs): raise RuntimeError('forbidden meet_* suffix')
    sl0=v300.augment_second(v298.second_long(d,sufs))
    sl1=v310.add_headrisk(sl0,p3,p4)
    cl=v300.augment_third(v298.conditional_long(d,sufs))

    # Freeze THIRD exactly as current v300 best to attribute changes to SECOND.
    pc={tm:v300.pc_predict(cl,tm,.1,True)[0] for tm in TM}

    allf=sorted(set(family(c) for c in audited_features(sl1)))
    print('v311 families',allf,flush=True)
    # Baselines + leave-one-family-out + compact causal combinations.
    configs=[
        ('BASE_V300',3.0,False,None,None),
        ('FULL_HEADRISK',3.0,True,None,None),
    ]
    for fam in ('HEADRISK','START','MOTOR','PLAYER','FORM_STATIC','POSITION'):
        configs.append((f'DROP_{fam}',3.0,True,None,{fam}))
    combos=[
        ('COMPACT_SMP',{'START','MOTOR','PLAYER','POSITION'}),
        ('COMPACT_SMPH',{'START','MOTOR','PLAYER','POSITION','HEADRISK'}),
        ('COMPACT_SAFE_CORE',{'START','MOTOR','PLAYER','FORM_STATIC','POSITION'}),
        ('COMPACT_SAFE_CORE_H',{'START','MOTOR','PLAYER','FORM_STATIC','POSITION','HEADRISK'}),
        ('HEADRISK_ONLY',{'HEADRISK','POSITION'}),
    ]
    for name,allow in combos: configs.append((name,3.0,True,allow,None))

    summaries=[]; raceouts=[]; featrows=[]
    for name,l2,use_hr,allow,drop in configs:
        sl=sl1 if use_hr else sl0
        p2={}; fcounts=[]
        for tm in TM:
            p2[tm],fs=p2_predict_explicit(sl,tm,l2,allow,drop); fcounts.append(len(fs))
            for c in fs: featrows.append({'config':name,'month':tm,'feature':c,'family':family(c)})
        z,m=evaluate(p2,pc,d,ids); z['config']=name; raceouts.append(z)
        m.update({'config':name,'second_l2':l2,'min_features':min(fcounts),'max_features':max(fcounts)})
        summaries.append(m); print('v311',name,m,flush=True)

    sm=pd.DataFrame(summaries)
    base=sm[sm.config=='BASE_V300'].iloc[0]
    sm['delta_top2_pp']=100*(sm.second_top2-base.second_top2)
    sm['delta_outer456_top2_pp']=100*(sm.outer456_top2-base.outer456_top2)
    sm['delta_exact3_pp']=100*(sm.exact3_rate-base.exact3_rate)
    # Auto-selection is development-only and stability-aware: TOP2 first, then worst month,
    # then outer capture, then exact3. Never shrink the 345 denominator.
    cand=sm[sm.config!='BASE_V300'].sort_values(
        ['second_top2','worst_month_second_top2','outer456_top2','exact3_rate'],ascending=False)
    best=cand.iloc[0]
    allz=pd.concat(raceouts,ignore_index=True); bz=allz[allz.config==best.config].copy(); bh=bz[bz.head_hit==1]
    by=bh.groupby('actual2').agg(R=('race_code','size'),top1=('second_top1','mean'),top2=('second_top2','mean'),top3=('second_top3','mean'),exact3=('exact3','mean')).reset_index()
    mon=bz.groupby('month').agg(R=('race_code','size'),head=('head_hit','sum'),exact3=('exact3','mean')).reset_index()
    mh=bh.groupby('month').agg(second_top1=('second_top1','mean'),second_top2=('second_top2','mean'),second_top3=('second_top3','mean')).reset_index(); mon=mon.merge(mh,on='month',how='left')

    sm.to_csv(str(P)+'_configs.csv',index=False)
    pd.DataFrame(featrows).drop_duplicates().to_csv(str(P)+'_features.csv',index=False)
    by.to_csv(str(P)+'_best_by_second.csv',index=False); mon.to_csv(str(P)+'_best_monthly.csv',index=False); bz.to_csv(str(P)+'_best_race.csv',index=False)

    L=['# v311 SECOND family auto-research','',
       '- Fixed evaluation cohort: **345 races / 290 boat-1 wins**.',
       '- THIRD frozen at v300 conditional L2=.1; exact3 changes are attributable primarily to SECOND.',
       '- No `meet_*`; PRE/prior only; p3/p4 use causal monthly walk-forward maps with explicit sparse-coverage flags.',
       '- Jul/Aug excluded as NON-PRISTINE; September outcomes unread.',
       '- Development-only: best config is not promoted automatically.','',
       '## Configs','|config|TOP1|TOP2|TOP3|outer456 TOP2|worst month TOP2|exact3|dTOP2 pp|dOuter pp|dExact3 pp|','|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for _,r in sm.sort_values(['second_top2','worst_month_second_top2'],ascending=False).iterrows():
        L.append(f"|{r.config}|{100*r.second_top1:.2f}%|{100*r.second_top2:.2f}%|{100*r.second_top3:.2f}%|{100*r.outer456_top2:.2f}%|{100*r.worst_month_second_top2:.2f}%|{int(r.exact3_hits)}/345={100*r.exact3_rate:.2f}%|{r.delta_top2_pp:+.2f}|{r.delta_outer456_top2_pp:+.2f}|{r.delta_exact3_pp:+.2f}|")
    L += ['',f'## Development best: {best.config}',
          f'- SECOND TOP2: **{100*best.second_top2:.2f}%** vs base {100*base.second_top2:.2f}%.',
          f'- outer 4/5/6 SECOND TOP2: **{100*best.outer456_top2:.2f}%** vs base {100*base.outer456_top2:.2f}%.',
          f'- exact3: **{int(best.exact3_hits)}/345 = {100*best.exact3_rate:.2f}%** vs base {100*base.exact3_rate:.2f}%.','',
          '## Best by actual SECOND','|boat|R|TOP1|TOP2|TOP3|exact3|','|---:|---:|---:|---:|---:|---:|']
    for _,r in by.iterrows(): L.append(f"|{int(r.actual2)}|{int(r.R)}|{100*r.top1:.2f}%|{100*r.top2:.2f}%|{100*r.top3:.2f}%|{100*r.exact3:.2f}%|")
    L += ['', '## Monthly','|month|R|head wins|SECOND TOP2|exact3|','|---|---:|---:|---:|---:|']
    for _,r in mon.iterrows(): L.append(f"|{r.month}|{int(r.R)}|{int(r['head'])}|{100*r.second_top2:.2f}%|{100*r.exact3:.2f}%|")
    S.write_text('\n'.join(L)+'\n',encoding='utf-8'); print(S.read_text(),flush=True)

if __name__=='__main__': main()
