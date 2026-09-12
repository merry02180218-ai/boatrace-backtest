#!/usr/bin/env python3
"""v315: pairwise SECOND ranking with outer-balanced weighting.

Frozen boat-1 cohort: v308 345 races / 290 boat-1 wins.
Uses v313 causal cache only. No meet_* predictors, no future backfill.
THIRD stays frozen at v300 conditional L2=.1 so this run attributes changes to SECOND.
Feb-Jun is development only; Jul/Aug NON-PRISTINE; September outcomes unread.
"""
from pathlib import Path
from itertools import combinations
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

import analyze_v298_1head_threat_listwise_trifecta5 as v298
import run_v300_1head_trifecta3_feature_upgrade as v300
import run_v309_1head_opponent_zero_base_audit as v309
import run_v310_1head_opponent_headrisk_second as v310
import run_v311_1head_opponent_second_family_autoresearch as v311
import run_v312_1head_opponent_outer_gate as v312

ROOT=Path(__file__).resolve().parent
SEL=ROOT/'analysis_v308_1head_volume_opponent_joint_best_selected.csv'
P=ROOT/'analysis_v315_1head_opponent_pairwise_second'
S=ROOT/'summary_v315_1head_opponent_pairwise_second.md'
TM=list(v298.TEST_MONTHS)
BOATS=(2,3,4,5,6)


def _numframe(df,fs):
    return df[fs].apply(pd.to_numeric,errors='coerce')


def make_pair_train(sl,fs,tm,outer_weight=1.0):
    tr=sl[sl.month<tm].copy()
    rows=[]; ys=[]; ws=[]
    for code,g in tr.groupby('race_code'):
        g=g[g.boat.astype(int).isin(BOATS)].copy()
        if len(g)!=5: continue
        actual=pd.to_numeric(g.actual2,errors='coerce').dropna()
        if actual.empty: continue
        a=int(actual.iloc[0])
        if a not in BOATS: continue
        by={int(r.boat):r for _,r in g.iterrows()}
        if set(by)!=set(BOATS): continue
        # winner-vs-loser plus reversed orientation keeps the pair model symmetric.
        for b in BOATS:
            if b==a: continue
            xa=pd.to_numeric(pd.Series(by[a][fs]),errors='coerce').to_numpy(dtype=float)
            xb=pd.to_numeric(pd.Series(by[b][fs]),errors='coerce').to_numpy(dtype=float)
            diff=xa-xb
            w=float(outer_weight if a in (4,5,6) else 1.0)
            rows.append(diff); ys.append(1); ws.append(w)
            rows.append(-diff); ys.append(0); ws.append(w)
    if not rows: raise RuntimeError(f'v315 no pair training rows month={tm}')
    return np.asarray(rows,float),np.asarray(ys,int),np.asarray(ws,float)


def pairwise_predict(sl,tm,l2=3.0,outer_weight=1.0,drop_start=True):
    tr=sl[sl.month<tm].copy(); te=sl[sl.month==tm].copy()
    fs=v311.audited_features(tr)
    if drop_start: fs=[c for c in fs if v311.family(c)!='START']
    if any('meet_' in str(c) for c in fs): raise RuntimeError('v315 forbidden meet feature')
    if not fs: raise RuntimeError(f'v315 no features month={tm}')
    X,y,w=make_pair_train(sl,fs,tm,outer_weight)
    imp=SimpleImputer(strategy='median'); sc=StandardScaler()
    X=imp.fit_transform(X); X=sc.fit_transform(X)
    C=1.0/max(float(l2),1e-9)
    m=LogisticRegression(C=C,max_iter=2000,solver='lbfgs',random_state=315)
    m.fit(X,y,sample_weight=w)
    out={}
    for code,g in te.groupby('race_code'):
        g=g[g.boat.astype(int).isin(BOATS)].copy()
        if len(g)!=5: continue
        by={int(r.boat):r for _,r in g.iterrows()}
        if set(by)!=set(BOATS): continue
        score={b:0.0 for b in BOATS}
        for a,b in combinations(BOATS,2):
            xa=pd.to_numeric(pd.Series(by[a][fs]),errors='coerce').to_numpy(dtype=float)
            xb=pd.to_numeric(pd.Series(by[b][fs]),errors='coerce').to_numpy(dtype=float)
            d=imp.transform(np.asarray([xa-xb],float)); d=sc.transform(d)
            p=float(m.predict_proba(d)[0,1])
            score[a]+=p; score[b]+=1.0-p
        # Normalize Copeland-like expected pairwise wins into a probability simplex.
        vals=np.array([max(score[b],1e-9) for b in BOATS],float)
        vals=vals/vals.sum()
        out[str(code).zfill(12)]={b:float(vals[i]) for i,b in enumerate(BOATS)}
    return out,len(fs),len(y)


def blend_pair(base,pair,mix):
    q={b:(1-mix)*float(base.get(b,0.0))+mix*float(pair.get(b,0.0)) for b in BOATS}
    s=sum(q.values())
    return {b:(q[b]/s if s>0 else .2) for b in BOATS}


def evaluate(p2,pc,d,ids):
    rows=[]
    for tm in TM:
        q=d[(d.month==tm)&(d.race_code.isin(ids))].copy()
        for _,r in q.iterrows():
            code=str(r.race_code).zfill(12); parts=str(r.actual_combo).split('-')
            if len(parts)!=3: continue
            a1,a2,a3=map(int,parts)
            if code not in p2[tm] or code not in pc[tm]: raise RuntimeError(f'v315 missing prediction {tm} {code}')
            p2m=p2[tm][code]; pcm=pc[tm][code]
            sr=v309.rank_of(p2m,a2) if a1==1 else np.nan
            tickets=v300.ticket3(p2m,pcm).split(';')
            rows.append({'month':tm,'race_code':code,'head_hit':int(a1==1),'actual2':a2,'actual3':a3,
                         'second_rank':sr,
                         'second_top1':int(a1==1 and pd.notna(sr) and sr<=1),
                         'second_top2':int(a1==1 and pd.notna(sr) and sr<=2),
                         'second_top3':int(a1==1 and pd.notna(sr) and sr<=3),
                         'exact3':int(str(r.actual_combo) in tickets)})
    z=pd.DataFrame(rows)
    if len(z)!=345 or int(z.head_hit.sum())!=290:
        raise RuntimeError(f'v315 frozen mismatch R={len(z)} head={int(z.head_hit.sum())}')
    h=z[z.head_hit==1].copy(); mon=h.groupby('month').second_top2.mean(); by=h.groupby('actual2').second_top2.mean().to_dict()
    return z,{'R':345,'head_hits':290,'exact3_hits':int(z.exact3.sum()),'exact3_rate':float(z.exact3.mean()),
              'second_top1':float(h.second_top1.mean()),'second_top2':float(h.second_top2.mean()),'second_top3':float(h.second_top3.mean()),
              'worst_month_second_top2':float(mon.min()),'outer456_top2':float(h[h.actual2.isin([4,5,6])].second_top2.mean()),
              'boat2_top2':float(by.get(2,np.nan)),'boat3_top2':float(by.get(3,np.nan)),'boat4_top2':float(by.get(4,np.nan)),
              'boat5_top2':float(by.get(5,np.nan)),'boat6_top2':float(by.get(6,np.nan))}


def main():
    frozen=pd.read_csv(SEL,dtype={'race_code':str}); frozen['race_code']=frozen.race_code.astype(str).str.zfill(12)
    if len(frozen)!=345: raise RuntimeError('v315 frozen cohort changed')
    ids=set(frozen.race_code)
    d,p3,p4=v312.load_cache(); d['race_code']=d.race_code.astype(str).str.zfill(12)
    q=d[d.race_code.isin(ids)]
    if len(q)!=345 or int(q.head_hit.sum())!=290: raise RuntimeError('v315 cache frozen mismatch')

    v300.setup_v298(); sufs=v298.suffixes(d)
    if any('meet_' in str(x) for x in sufs): raise RuntimeError('v315 forbidden meet leakage')
    sl=v310.add_headrisk(v300.augment_second(v298.second_long(d,sufs)),p3,p4)
    cl=v300.augment_third(v298.conditional_long(d,sufs))
    pc={tm:v300.pc_predict(cl,tm,.1,True)[0] for tm in TM}
    base={tm:v311.p2_predict_explicit(sl,tm,3.0,None,{'START'})[0] for tm in TM}

    configs=[('DROP_START_BASE',0.0,1.0,3.0)]
    pair_cache={}; meta=[]
    for ow in (1.0,1.5,2.0,3.0,4.0):
        pair_cache[ow]={}
        for tm in TM:
            pred,nf,npair=pairwise_predict(sl,tm,3.0,ow,True)
            pair_cache[ow][tm]=pred
            meta.append({'outer_weight':ow,'month':tm,'n_features':nf,'n_pair_rows':npair})
        for mix in (.35,.50,.65,.80,1.00):
            configs.append((f'PAIR_ow{ow:.1f}_m{mix:.2f}',mix,ow,3.0))

    sums=[]; outs=[]
    for name,mix,ow,l2 in configs:
        p2={}
        for tm in TM:
            p2[tm]={}
            for code,bp in base[tm].items():
                if name=='DROP_START_BASE': p2[tm][code]=bp
                else:
                    pp=pair_cache[ow][tm].get(code)
                    if pp is None: raise RuntimeError(f'v315 missing pair pred {tm} {code}')
                    p2[tm][code]=blend_pair(bp,pp,mix)
        z,m=evaluate(p2,pc,d,ids); z['config']=name; outs.append(z)
        m.update({'config':name,'pair_mix':mix,'outer_weight':ow,'pair_l2':l2}); sums.append(m)
        print('v315',name,m,flush=True)

    sm=pd.DataFrame(sums); b=sm[sm.config=='DROP_START_BASE'].iloc[0]
    for c,src in [('delta_top2_pp','second_top2'),('delta_outer_pp','outer456_top2'),('delta_exact3_pp','exact3_rate')]: sm[c]=100*(sm[src]-b[src])
    cand=sm[sm.config!='DROP_START_BASE'].copy()
    best=cand.sort_values(['second_top2','worst_month_second_top2','outer456_top2','exact3_rate'],ascending=False).iloc[0]
    allz=pd.concat(outs,ignore_index=True); bz=allz[allz.config==best.config].copy(); bh=bz[bz.head_hit==1]
    by=bh.groupby('actual2').agg(R=('race_code','size'),top1=('second_top1','mean'),top2=('second_top2','mean'),top3=('second_top3','mean'),exact3=('exact3','mean')).reset_index()
    mon=bz.groupby('month').agg(R=('race_code','size'),head=('head_hit','sum'),exact3=('exact3','mean')).reset_index()
    mon=mon.merge(bh.groupby('month').agg(second_top1=('second_top1','mean'),second_top2=('second_top2','mean'),second_top3=('second_top3','mean')).reset_index(),on='month')

    sm.to_csv(str(P)+'_configs.csv',index=False); pd.DataFrame(meta).to_csv(str(P)+'_fit_meta.csv',index=False)
    by.to_csv(str(P)+'_best_by_second.csv',index=False); mon.to_csv(str(P)+'_best_monthly.csv',index=False); bz.to_csv(str(P)+'_best_race.csv',index=False)
    L=['# v315 pairwise SECOND autoresearch','',
       '- Fixed v308 cohort: **345 races / 290 boat-1 wins**; IDs unchanged.',
       '- Uses v313 reusable causal cache; no `meet_*`; no future backfill.',
       '- Pairwise candidate-vs-candidate logistic ranking with outer-winner weighting.',
       '- THIRD frozen at v300 conditional L2=.1 for SECOND attribution.',
       '- Feb-Jun development only; Jul/Aug NON-PRISTINE; September outcomes unread.','',
       '## Development result',
       f'- DROP_START base TOP2 {100*b.second_top2:.2f}%, outer {100*b.outer456_top2:.2f}%, exact3 {int(b.exact3_hits)}/345={100*b.exact3_rate:.2f}%, worst month {100*b.worst_month_second_top2:.2f}%.',
       f'- Best **{best.config}** TOP2 **{100*best.second_top2:.2f}%**, outer **{100*best.outer456_top2:.2f}%**, exact3 **{int(best.exact3_hits)}/345={100*best.exact3_rate:.2f}%**, worst month **{100*best.worst_month_second_top2:.2f}%**.','',
       '## Best by actual SECOND','|boat|R|TOP1|TOP2|TOP3|exact3|','|---:|---:|---:|---:|---:|---:|']
    for _,r in by.iterrows(): L.append(f'|{int(r.actual2)}|{int(r.R)}|{100*r.top1:.2f}%|{100*r.top2:.2f}%|{100*r.top3:.2f}%|{100*r.exact3:.2f}%|')
    L+=['','## Monthly','|month|R|head|TOP1|TOP2|TOP3|exact3|','|---|---:|---:|---:|---:|---:|---:|']
    for _,r in mon.iterrows(): L.append(f'|{r.month}|{int(r.R)}|{int(r["head"])}|{100*r.second_top1:.2f}%|{100*r.second_top2:.2f}%|{100*r.second_top3:.2f}%|{100*r.exact3:.2f}%|')
    L+=['','## Automatic decision rule',
        '- If pairwise gain is weak/flat (roughly <= +0.5pp TOP2 with no robust outer improvement), do not micro-tune endlessly; move to a materially different multiclass/listwise formulation with route/class balancing.',
        '- Any suspicious large gain requires leakage/causal audit before acceptance.']
    S.write_text('\n'.join(L)+'\n',encoding='utf-8'); print(S.read_text(),flush=True)

if __name__=='__main__': main()
