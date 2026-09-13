#!/usr/bin/env python3
"""v318: rebuild conditional THIRD after leak-safe SECOND saturation.
Frozen v308 cohort 345R/290 head wins. v313 cache only. No meet_*, no future backfill.
Uses v317 OUTER_L2_1 SECOND as fixed reference and varies THIRD only for attribution.
Feb-Jun development only; Jul/Aug NON-PRISTINE; September outcomes unread.
"""
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.special import logsumexp
import analyze_v298_1head_threat_listwise_trifecta5 as v298
import run_v300_1head_trifecta3_feature_upgrade as v300
import run_v309_1head_opponent_zero_base_audit as v309
import run_v310_1head_opponent_headrisk_second as v310
import run_v311_1head_opponent_second_family_autoresearch as v311
import run_v312_1head_opponent_outer_gate as v312
import run_v317_1head_opponent_error_features as v317
import run_v298_1head_v288v283_audited as fastbase
ROOT=Path(__file__).resolve().parent
SEL=ROOT/'analysis_v308_1head_volume_opponent_joint_best_selected.csv'
P=ROOT/'analysis_v318_1head_opponent_third_rebuild'
S=ROOT/'summary_v318_1head_opponent_third_rebuild.md'
TM=list(v298.TEST_MONTHS)

def pc_predict(cl,tm,l2,mode):
    tr=cl[(cl.month<tm)&(cl.train_group==1)].copy(); te=cl[cl.month==tm].copy()
    meta={'date','month','race_code','group_id','second_boat','third_boat','train_group','ycond','actual2','actual3'}
    fs=v300.good(tr,[c for c in tr.columns if c not in meta])
    if any('meet_' in str(c) for c in fs): raise RuntimeError('v318 forbidden meet feature')
    if mode=='DROP_START': fs=[c for c in fs if 'nst_strength' not in str(c)]
    elif mode=='COMPACT':
        keep=('v300_','motor','grade','wr','local','f_safety','pair_','cand_','diff','innermax','pos_','pl_','turn','straight','overall','vh_','gh_')
        fs=[c for c in fs if any(k in str(c) for k in keep)]
    m=fastbase.FastConditional(l2).fit(tr,fs); te=te.copy(); te['score']=m.score(te)
    out={}
    for code,g in te.groupby('race_code'):
        pc={}
        for s,gs in g.groupby('second_boat'):
            a=gs.score.to_numpy(float); pp=np.exp(a-logsumexp(a))
            for t,p in zip(gs.third_boat.astype(int),pp): pc[(int(s),int(t))]=float(p)
        out[str(code).zfill(12)]=pc
    return out,len(fs)

def evaluate(p2,pc,d,ids):
    rows=[]
    for tm in TM:
        q=d[(d.month==tm)&(d.race_code.isin(ids))]
        for _,r in q.iterrows():
            code=str(r.race_code).zfill(12); parts=str(r.actual_combo).split('-')
            if len(parts)!=3: continue
            a1,a2,a3=map(int,parts); p2m=p2[tm][code]; pcm=pc[tm][code]
            sr=v309.rank_of(p2m,a2) if a1==1 else np.nan
            cand={t:p for (s,t),p in pcm.items() if s==a2}; trank=v309.rank_of(cand,a3) if a1==1 else np.nan
            tickets=v300.ticket3(p2m,pcm).split(';')
            rows.append({'month':tm,'race_code':code,'head_hit':int(a1==1),'actual2':a2,'actual3':a3,'second_rank':sr,'third_rank':trank,
              'second_top2':int(a1==1 and pd.notna(sr) and sr<=2),'third_top1':int(a1==1 and pd.notna(trank) and trank<=1),
              'third_top2':int(a1==1 and pd.notna(trank) and trank<=2),'third_top3':int(a1==1 and pd.notna(trank) and trank<=3),
              'exact3':int(str(r.actual_combo) in tickets)})
    z=pd.DataFrame(rows)
    if len(z)!=345 or int(z.head_hit.sum())!=290: raise RuntimeError(f'v318 frozen mismatch {len(z)}/{int(z.head_hit.sum())}')
    h=z[z.head_hit==1]; mon=h.groupby('month').third_top2.mean()
    return z,{'R':345,'head_hits':290,'exact3_hits':int(z.exact3.sum()),'exact3_rate':float(z.exact3.mean()),
      'second_top2':float(h.second_top2.mean()),'third_top1':float(h.third_top1.mean()),'third_top2':float(h.third_top2.mean()),
      'third_top3':float(h.third_top3.mean()),'worst_month_third_top2':float(mon.min())}

def main():
    frozen=pd.read_csv(SEL,dtype={'race_code':str}); frozen.race_code=frozen.race_code.astype(str).str.zfill(12); ids=set(frozen.race_code)
    if len(frozen)!=345: raise RuntimeError('v318 cohort changed')
    d,p3,p4=v312.load_cache(); d.race_code=d.race_code.astype(str).str.zfill(12)
    q=d[d.race_code.isin(ids)]
    if len(q)!=345 or int(q.head_hit.sum())!=290: raise RuntimeError('v318 cache frozen mismatch')
    v300.setup_v298(); sufs=v298.suffixes(d)
    if any('meet_' in str(x) for x in sufs): raise RuntimeError('v318 forbidden meet suffix')
    sl=v310.add_headrisk(v300.augment_second(v298.second_long(d,sufs)),p3,p4)
    sx,_=v317.add_engineered(sl,'OUTER')
    p2={tm:v311.p2_predict_explicit(sx,tm,1.0,None,{'START'})[0] for tm in TM}
    cl=v300.augment_third(v298.conditional_long(d,sufs))
    configs=[('BASE_T0.1','ALL',.1),('ALL_T0.3','ALL',.3),('ALL_T1','ALL',1.),('ALL_T3','ALL',3.),('DROPSTART_T0.1','DROP_START',.1),('DROPSTART_T0.3','DROP_START',.3),('DROPSTART_T1','DROP_START',1.),('COMPACT_T0.1','COMPACT',.1),('COMPACT_T0.3','COMPACT',.3),('COMPACT_T1','COMPACT',1.)]
    sums=[]; outs=[]
    for name,mode,l2 in configs:
        pc={}; nfs=[]
        for tm in TM:
            x,n=pc_predict(cl,tm,l2,mode); pc[tm]=x; nfs.append(n)
        z,m=evaluate(p2,pc,d,ids); z['config']=name; outs.append(z); m.update({'config':name,'mode':mode,'l2':l2,'min_features':min(nfs),'max_features':max(nfs)}); sums.append(m); print('v318',name,m,flush=True)
    sm=pd.DataFrame(sums); base=sm[sm.config=='BASE_T0.1'].iloc[0]; sm['delta_third_top2_pp']=100*(sm.third_top2-base.third_top2); sm['delta_exact3_pp']=100*(sm.exact3_rate-base.exact3_rate)
    best=sm.sort_values(['third_top2','worst_month_third_top2','exact3_rate'],ascending=False).iloc[0]
    allz=pd.concat(outs,ignore_index=True); bz=allz[allz.config==best.config]; bh=bz[bz.head_hit==1]
    mon=bh.groupby('month').agg(R=('race_code','size'),third_top1=('third_top1','mean'),third_top2=('third_top2','mean'),third_top3=('third_top3','mean')).reset_index()
    sm.to_csv(str(P)+'_configs.csv',index=False); bz.to_csv(str(P)+'_best_race.csv',index=False); mon.to_csv(str(P)+'_best_monthly.csv',index=False)
    L=['# v318 conditional THIRD rebuild','', '- Fixed v308 cohort: **345 races / 290 boat-1 wins**.', '- v313 cache only; no `meet_*`; no future backfill; month M trains only before M.', '- SECOND fixed to v317 OUTER_L2_1 so this experiment attributes changes to THIRD only.', '- Feb-Jun development only; Jul/Aug NON-PRISTINE; September outcomes unread.','', '## Result', f'- Baseline THIRD TOP2 **{100*base.third_top2:.2f}%**, exact3 **{int(base.exact3_hits)}/345={100*base.exact3_rate:.2f}%**.', f'- Best **{best.config}** THIRD TOP2 **{100*best.third_top2:.2f}%**, TOP1 **{100*best.third_top1:.2f}%**, TOP3 **{100*best.third_top3:.2f}%**, exact3 **{int(best.exact3_hits)}/345={100*best.exact3_rate:.2f}%**, worst-month THIRD TOP2 **{100*best.worst_month_third_top2:.2f}%**.','', '## Monthly best','|month|R|THIRD TOP1|TOP2|TOP3|','|---|---:|---:|---:|---:|']
    for _,r in mon.iterrows(): L.append(f'|{r.month}|{int(r.R)}|{100*r.third_top1:.2f}%|{100*r.third_top2:.2f}%|{100*r.third_top3:.2f}%|')
    L += ['','## Automatic next decision','- If THIRD gain is weak/unstable, move to direct 20 ordered `(second,third)` pair modeling.','- If THIRD materially improves, preserve it and then compare factorized vs direct ordered-pair before ticket optimization.','- Any suspicious large gain triggers leakage/causal audit.']
    S.write_text('\n'.join(L)+'\n',encoding='utf-8'); print(S.read_text(),flush=True)
if __name__=='__main__': main()
