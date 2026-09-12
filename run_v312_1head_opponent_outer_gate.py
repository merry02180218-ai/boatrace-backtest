#!/usr/bin/env python3
"""v312: leak-safe inner-vs-outer SECOND gate on frozen 345R.

Distinct from v311 feature ablation: learn, month by month, whether actual SECOND is
outer (4/5/6) using only PRE/prior candidate-table summaries, then blend/reweight the
v311 DROP_START SECOND distribution. THIRD remains frozen to v300 L2=.1.

CACHE-FIRST RULE
----------------
This script MUST use the reusable v313 causal cache and MUST NOT repeat the expensive
historical reconstruction on every experiment. If the cache is absent, fail fast and
build it once with build_v313_1head_opponent_causal_cache.py.

No meet_*, no future backfill, Feb-Jun development only, Jul/Aug NON-PRISTINE,
September outcomes unread. Boat-1 losses remain misses over all 345 races.
"""
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

import analyze_v298_1head_threat_listwise_trifecta5 as v298
import run_v300_1head_trifecta3_feature_upgrade as v300
import run_v309_1head_opponent_zero_base_audit as v309
import run_v310_1head_opponent_headrisk_second as v310
import run_v311_1head_opponent_second_family_autoresearch as v311

ROOT=Path(__file__).resolve().parent
SEL=ROOT/'analysis_v308_1head_volume_opponent_joint_best_selected.csv'
CACHE_D=ROOT/'cache_v313_1head_opponent_pre.csv.gz'
CACHE_P3=ROOT/'cache_v313_1head_opponent_p3.csv.gz'
CACHE_P4=ROOT/'cache_v313_1head_opponent_p4.csv.gz'
CACHE_MANIFEST=ROOT/'CACHE_V313_1HEAD_OPPONENT_CAUSAL.md'
P=ROOT/'analysis_v312_1head_opponent_outer_gate'
S=ROOT/'summary_v312_1head_opponent_outer_gate.md'
TM=list(v298.TEST_MONTHS)


def load_cache():
    missing=[str(p.name) for p in (CACHE_D,CACHE_P3,CACHE_P4,CACHE_MANIFEST) if not p.exists()]
    if missing:
        raise RuntimeError('v313 causal cache missing: '+','.join(missing)+'; build cache once before v312')
    d=pd.read_csv(CACHE_D,dtype={'race_code':str})
    d['race_code']=d.race_code.astype(str).str.zfill(12); d['month']=d.month.astype(str)
    if any('meet_' in str(c) for c in d.columns):
        raise RuntimeError('v312 refused cache containing forbidden meet_* columns')
    p3q=pd.read_csv(CACHE_P3,dtype={'race_code':str}); p4q=pd.read_csv(CACHE_P4,dtype={'race_code':str})
    p3=dict(zip(p3q.race_code.astype(str).str.zfill(12),pd.to_numeric(p3q.p3head,errors='coerce')))
    p4=dict(zip(p4q.race_code.astype(str).str.zfill(12),pd.to_numeric(p4q.p4head,errors='coerce')))
    return d,p3,p4


def gate_table(sl):
    fs=v311.audited_features(sl)
    keep=[]
    for c in fs:
        fam=v311.family(c)
        if fam in {'HEADRISK','MOTOR','PLAYER','FORM_STATIC','POSITION','OTHER_SAFE'}: keep.append(c)
    keep=keep[:120]
    rows=[]
    for code,g in sl.groupby('race_code',sort=False):
        g=g.copy(); b=g.boat.astype(int)
        r={'race_code':str(code).zfill(12),'month':str(g.month.iloc[0]),'date':g.date.iloc[0],
           'actual2':int(g.actual2.iloc[0]) if pd.notna(g.actual2.iloc[0]) else 0,
           'y_outer':int(pd.notna(g.actual2.iloc[0]) and int(g.actual2.iloc[0]) in (4,5,6))}
        for c in keep:
            x=pd.to_numeric(g[c],errors='coerce'); inn=x[b.isin([2,3])]; out=x[b.isin([4,5,6])]
            r[f'{c}__outmax_minus_inmax']=(out.max()-inn.max()) if out.notna().any() and inn.notna().any() else np.nan
            r[f'{c}__outmean_minus_inmean']=(out.mean()-inn.mean()) if out.notna().any() and inn.notna().any() else np.nan
        rows.append(r)
    return pd.DataFrame(rows)


def gate_predict(gt,tm,C=0.3):
    tr=gt[gt.month<tm].copy(); te=gt[gt.month==tm].copy(); tr=tr[tr.actual2.isin([2,3,4,5,6])]
    meta={'race_code','month','date','actual2','y_outer'}; fs=[c for c in gt.columns if c not in meta and 'meet_' not in c]
    if tr.y_outer.nunique()<2: raise RuntimeError(f'gate has one class in {tm}')
    m=make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),LogisticRegression(C=C,max_iter=1000,class_weight='balanced'))
    m.fit(tr[fs],tr.y_outer.astype(int)); p=m.predict_proba(te[fs])[:,1]
    return dict(zip(te.race_code.astype(str).str.zfill(12),p)),len(fs)


def reweight(base,pg,mult,threshold):
    q={int(k):float(v) for k,v in base.items()}; boost=mult if pg>=threshold else 1.0
    for b in (4,5,6): q[b]=q.get(b,0.0)*boost
    s=sum(q.values()); return {b:(q[b]/s if s>0 else 0.2) for b in sorted(q)}


def evaluate(p2,pc,d,ids):
    rows=[]
    for tm in TM:
        q=d[d.month==tm].copy(); q=q[q.race_code.isin(ids)]
        for _,r in q.iterrows():
            code=r.race_code; parts=str(r.actual_combo).split('-')
            if len(parts)!=3: continue
            a1,a2,a3=map(int,parts); p2m=p2[tm][code]; pcm=pc[tm][code]
            sr=v309.rank_of(p2m,a2) if a1==1 else np.nan; tickets=v300.ticket3(p2m,pcm).split(';')
            rows.append({'month':tm,'race_code':code,'head_hit':int(a1==1),'actual2':a2,'second_rank':sr,
                         'second_top1':int(a1==1 and pd.notna(sr) and sr<=1),'second_top2':int(a1==1 and pd.notna(sr) and sr<=2),
                         'second_top3':int(a1==1 and pd.notna(sr) and sr<=3),'exact3':int(str(r.actual_combo) in tickets)})
    z=pd.DataFrame(rows)
    if len(z)!=345 or int(z.head_hit.sum())!=290: raise RuntimeError(f'frozen mismatch {len(z)} {int(z.head_hit.sum())}')
    h=z[z.head_hit==1]; by=h.groupby('actual2').second_top2.mean().to_dict(); mon=h.groupby('month').second_top2.mean()
    return z,{'R':345,'head_hits':290,'exact3_hits':int(z.exact3.sum()),'exact3_rate':float(z.exact3.mean()),
              'second_top1':float(h.second_top1.mean()),'second_top2':float(h.second_top2.mean()),'second_top3':float(h.second_top3.mean()),
              'worst_month_second_top2':float(mon.min()),'outer456_top2':float(h[h.actual2.isin([4,5,6])].second_top2.mean()),
              'boat4_top2':float(by.get(4,np.nan)),'boat5_top2':float(by.get(5,np.nan)),'boat6_top2':float(by.get(6,np.nan))}


def main():
    frozen=pd.read_csv(SEL,dtype={'race_code':str}); frozen['race_code']=frozen.race_code.astype(str).str.zfill(12)
    if len(frozen)!=345: raise RuntimeError('frozen cohort changed')
    ids=set(frozen.race_code)

    print('v312 loading reusable v313 causal cache',flush=True)
    d,p3,p4=load_cache()
    q=d[d.race_code.isin(ids)]
    if len(q)!=345 or int(q.head_hit.sum())!=290: raise RuntimeError('cached frozen cohort mismatch')

    v300.setup_v298()
    sufs=v298.suffixes(d)
    if any('meet_' in x for x in sufs): raise RuntimeError('meet leakage')
    sl=v310.add_headrisk(v300.augment_second(v298.second_long(d,sufs)),p3,p4)
    cl=v300.augment_third(v298.conditional_long(d,sufs))
    pc={tm:v300.pc_predict(cl,tm,.1,True)[0] for tm in TM}
    base={tm:v311.p2_predict_explicit(sl,tm,3.0,None,{'START'})[0] for tm in TM}
    gt=gate_table(sl); gates={}; nf={}
    for tm in TM: gates[tm],nf[tm]=gate_predict(gt,tm,.3)

    configs=[('DROP_START_BASE',1.0,1.1)]
    for mult in (1.15,1.3,1.5,1.8,2.2,2.8):
        for th in (.35,.45,.55,.65,.75): configs.append((f'GATE_m{mult:g}_t{th:.2f}',mult,th))
    sums=[]; outs=[]
    for name,mult,th in configs:
        p2={}
        for tm in TM:
            p2[tm]={code:(bp if name=='DROP_START_BASE' else reweight(bp,gates[tm].get(code,0.0),mult,th)) for code,bp in base[tm].items()}
        z,m=evaluate(p2,pc,d,ids); z['config']=name; outs.append(z); m.update({'config':name,'outer_multiplier':mult,'gate_threshold':th}); sums.append(m)
        print('v312',name,m,flush=True)
    sm=pd.DataFrame(sums); baseM=sm[sm.config=='DROP_START_BASE'].iloc[0]
    for c,src in [('delta_top2_pp','second_top2'),('delta_outer_pp','outer456_top2'),('delta_exact3_pp','exact3_rate')]: sm[c]=100*(sm[src]-baseM[src])
    cand=sm[sm.config!='DROP_START_BASE'].copy(); best=cand.sort_values(['second_top2','worst_month_second_top2','outer456_top2','exact3_rate'],ascending=False).iloc[0]
    allz=pd.concat(outs,ignore_index=True); bz=allz[allz.config==best.config].copy(); bh=bz[bz.head_hit==1]
    by=bh.groupby('actual2').agg(R=('race_code','size'),top2=('second_top2','mean'),top3=('second_top3','mean'),exact3=('exact3','mean')).reset_index()
    mon=bz.groupby('month').agg(R=('race_code','size'),head=('head_hit','sum'),exact3=('exact3','mean')).reset_index(); mh=bh.groupby('month').second_top2.mean().rename('second_top2').reset_index(); mon=mon.merge(mh,on='month')
    sm.to_csv(str(P)+'_configs.csv',index=False); by.to_csv(str(P)+'_best_by_second.csv',index=False); mon.to_csv(str(P)+'_best_monthly.csv',index=False); bz.to_csv(str(P)+'_best_race.csv',index=False)
    L=['# v312 outer SECOND gating','', '- Uses reusable v313 causal cache; no full historical rebuild in this experiment.', '- Frozen 345R / 290 head wins; THIRD frozen v300 L2=.1.', '- Gate is monthly walk-forward, PRE/prior-only, class-balanced logistic; no meet_*.', '- Base is v311 DROP_START.', '', '## Result', f'- Base TOP2: {100*baseM.second_top2:.2f}%, outer: {100*baseM.outer456_top2:.2f}%, exact3: {int(baseM.exact3_hits)}/345={100*baseM.exact3_rate:.2f}%.', f'- Best: **{best.config}** TOP2 {100*best.second_top2:.2f}%, outer {100*best.outer456_top2:.2f}%, exact3 {int(best.exact3_hits)}/345={100*best.exact3_rate:.2f}%, worst month {100*best.worst_month_second_top2:.2f}%.', '', '## By actual SECOND','|boat|R|TOP2|TOP3|exact3|','|---:|---:|---:|---:|---:|']
    for _,r in by.iterrows(): L.append(f'|{int(r.actual2)}|{int(r.R)}|{100*r.top2:.2f}%|{100*r.top3:.2f}%|{100*r.exact3:.2f}%|')
    L+=['','## Monthly','|month|R|head|TOP2|exact3|','|---|---:|---:|---:|---:|']
    for _,r in mon.iterrows(): L.append(f'|{r.month}|{int(r.R)}|{int(r["head"])}|{100*r.second_top2:.2f}%|{100*r.exact3:.2f}%|')
    S.write_text('\n'.join(L)+'\n',encoding='utf-8'); print(S.read_text(),flush=True)

if __name__=='__main__': main()
