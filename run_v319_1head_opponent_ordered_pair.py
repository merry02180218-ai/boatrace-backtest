#!/usr/bin/env python3
"""v319: direct ordered (SECOND,THIRD) pair model after v318 THIRD saturation.
Frozen v308 cohort 345R/290 head wins. v313 cache only. No meet_*, no future backfill.
Month M trains only before M. Feb-Jun development only; Jul/Aug NON-PRISTINE; September unread.
"""
from pathlib import Path
import numpy as np
import pandas as pd
import analyze_v298_1head_threat_listwise_trifecta5 as v298
import run_v300_1head_trifecta3_feature_upgrade as v300
import run_v309_1head_opponent_zero_base_audit as v309
import run_v312_1head_opponent_outer_gate as v312
import run_v298_1head_v288v283_audited as fastbase
ROOT=Path(__file__).resolve().parent
SEL=ROOT/'analysis_v308_1head_volume_opponent_joint_best_selected.csv'
P=ROOT/'analysis_v319_1head_opponent_ordered_pair'
S=ROOT/'summary_v319_1head_opponent_ordered_pair.md'
TM=list(v298.TEST_MONTHS)

def predict(cl,tm,l2,mode):
    tr=cl[(cl.month<tm)&(cl.train_group==1)].copy(); te=cl[cl.month==tm].copy()
    tr['ypair']=((tr.second_boat.astype(int)==tr.actual2.astype(int))&(tr.third_boat.astype(int)==tr.actual3.astype(int))).astype(int)
    meta={'date','month','race_code','group_id','second_boat','third_boat','train_group','ycond','ypair','actual2','actual3'}
    fs=v300.good(tr,[c for c in tr.columns if c not in meta])
    if any('meet_' in str(c) for c in fs): raise RuntimeError('v319 forbidden meet feature')
    if mode=='DROP_START': fs=[c for c in fs if 'nst_strength' not in str(c)]
    elif mode=='COMPACT':
        keep=('v300_','motor','grade','wr','local','f_safety','pair_','cand_','diff','innermax','pos_','pl_','turn','straight','overall','vh_','gh_')
        fs=[c for c in fs if any(k in str(c) for k in keep)]
    m=fastbase.FastListwise(float(l2)); m.group_n=20; m.target_col='ypair'; m.fit(tr,fs,'ypair')
    te=te.copy(); te['score']=m.score(te); out={}
    for code,g in te.groupby('race_code'):
        if len(g)!=20: raise RuntimeError(f'v319 incomplete pair group {code} n={len(g)}')
        a=g.score.to_numpy(float); a=a-np.max(a); p=np.exp(a); p=p/p.sum()
        out[str(code).zfill(12)]={(int(s),int(t)):float(x) for s,t,x in zip(g.second_boat,g.third_boat,p)}
    return out,len(fs)

def evaluate(pp,d,ids):
    rows=[]
    for tm in TM:
        q=d[(d.month==tm)&(d.race_code.isin(ids))]
        for _,r in q.iterrows():
            code=str(r.race_code).zfill(12); parts=str(r.actual_combo).split('-')
            if len(parts)!=3: continue
            a1,a2,a3=map(int,parts); pm=pp[tm][code]; ranked=sorted(pm,key=pm.get,reverse=True); true=(a2,a3)
            rank=(ranked.index(true)+1) if (a1==1 and true in ranked) else np.nan
            rows.append({'month':tm,'race_code':code,'head_hit':int(a1==1),'actual2':a2,'actual3':a3,'pair_rank':rank,
                         'pair_top1':int(a1==1 and pd.notna(rank) and rank<=1),'pair_top2':int(a1==1 and pd.notna(rank) and rank<=2),
                         'pair_top3':int(a1==1 and pd.notna(rank) and rank<=3),'pair_top5':int(a1==1 and pd.notna(rank) and rank<=5),
                         'exact3':int(a1==1 and pd.notna(rank) and rank<=3)})
    z=pd.DataFrame(rows)
    if len(z)!=345 or int(z.head_hit.sum())!=290: raise RuntimeError(f'v319 frozen mismatch {len(z)}/{int(z.head_hit.sum())}')
    h=z[z.head_hit==1]; mon=h.groupby('month').pair_top3.mean()
    return z,{'R':345,'head_hits':290,'exact3_hits':int(z.exact3.sum()),'exact3_rate':float(z.exact3.mean()),
              'pair_top1':float(h.pair_top1.mean()),'pair_top2':float(h.pair_top2.mean()),'pair_top3':float(h.pair_top3.mean()),
              'pair_top5':float(h.pair_top5.mean()),'worst_month_pair_top3':float(mon.min())}

def main():
    frozen=pd.read_csv(SEL,dtype={'race_code':str}); frozen.race_code=frozen.race_code.astype(str).str.zfill(12); ids=set(frozen.race_code)
    if len(frozen)!=345: raise RuntimeError('v319 cohort changed')
    d,p3,p4=v312.load_cache(); d.race_code=d.race_code.astype(str).str.zfill(12)
    q=d[d.race_code.isin(ids)]
    if len(q)!=345 or int(q.head_hit.sum())!=290: raise RuntimeError('v319 cache frozen mismatch')
    v300.setup_v298(); sufs=v298.suffixes(d)
    if any('meet_' in str(x) for x in sufs): raise RuntimeError('v319 forbidden meet suffix')
    cl=v300.augment_third(v298.conditional_long(d,sufs))
    configs=[('ALL_P0.1','ALL',.1),('ALL_P0.3','ALL',.3),('ALL_P1','ALL',1.),('ALL_P3','ALL',3.),('DROPSTART_P0.1','DROP_START',.1),('DROPSTART_P0.3','DROP_START',.3),('DROPSTART_P1','DROP_START',1.),('COMPACT_P0.1','COMPACT',.1),('COMPACT_P0.3','COMPACT',.3),('COMPACT_P1','COMPACT',1.)]
    sums=[]; outs=[]
    for name,mode,l2 in configs:
        pp={}; nf=[]
        for tm in TM:
            x,n=predict(cl,tm,l2,mode); pp[tm]=x; nf.append(n)
        z,m=evaluate(pp,d,ids); z['config']=name; outs.append(z); m.update({'config':name,'mode':mode,'l2':l2,'min_features':min(nf),'max_features':max(nf)}); sums.append(m); print('v319',name,m,flush=True)
    sm=pd.DataFrame(sums); sm['delta_vs_factorized_exact3_pp']=100*(sm.exact3_rate-(137/345)); best=sm.sort_values(['exact3_rate','worst_month_pair_top3','pair_top2'],ascending=False).iloc[0]
    allz=pd.concat(outs,ignore_index=True); bz=allz[allz.config==best.config]; bh=bz[bz.head_hit==1]
    mon=bh.groupby('month').agg(R=('race_code','size'),pair_top1=('pair_top1','mean'),pair_top2=('pair_top2','mean'),pair_top3=('pair_top3','mean'),pair_top5=('pair_top5','mean')).reset_index()
    sm.to_csv(str(P)+'_configs.csv',index=False); bz.to_csv(str(P)+'_best_race.csv',index=False); mon.to_csv(str(P)+'_best_monthly.csv',index=False)
    L=['# v319 direct ordered-pair model','', '- Fixed v308 cohort: **345 races / 290 boat-1 wins**.','- v313 cache only; no `meet_*`; no future backfill; month M trains only before M.','- Directly ranks all 20 ordered `(second,third)` pairs; top 3 pairs are the exact-3-ticket candidate set.','- Factorized v317 SECOND + v318 THIRD reference exact3: **137/345=39.71%**.','', '## Result',f'- Best **{best.config}**: pair TOP1 **{100*best.pair_top1:.2f}%**, TOP2 **{100*best.pair_top2:.2f}%**, TOP3 **{100*best.pair_top3:.2f}%**, TOP5 **{100*best.pair_top5:.2f}%**; exact3 **{int(best.exact3_hits)}/345={100*best.exact3_rate:.2f}%**; worst-month TOP3 **{100*best.worst_month_pair_top3:.2f}%**.','', '## Monthly best','|month|R|PAIR TOP1|TOP2|TOP3|TOP5|','|---|---:|---:|---:|---:|---:|']
    for _,r in mon.iterrows(): L.append(f'|{r.month}|{int(r.R)}|{100*r.pair_top1:.2f}%|{100*r.pair_top2:.2f}%|{100*r.pair_top3:.2f}%|{100*r.pair_top5:.2f}%|')
    L += ['','## Automatic next decision','- Compare direct ordered-pair against factorized 137/345 reference with monthly stability.','- If ordered-pair is not materially better, retain the stronger ranking reference and move to exact-3-ticket policy optimization rather than further micro-tuning.','- Suspicious large gain requires leakage/causal audit before acceptance.']
    S.write_text('\n'.join(L)+'\n',encoding='utf-8'); print(S.read_text(),flush=True)
if __name__=='__main__': main()
