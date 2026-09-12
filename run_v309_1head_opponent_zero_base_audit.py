#!/usr/bin/env python3
"""v309: zero-base diagnostic audit of opponent selection on frozen v308 345 races.

Head model / selected race set is frozen to v308 best operating point. This script does
NOT optimize tickets. It decomposes current v300 opponent errors into SECOND ranking,
conditional THIRD ranking, and exact 3-ticket coverage so the next opponent model can be
redesigned from evidence rather than incremental tuning.

Development only. Jul/Aug NON-PRISTINE; September outcomes remain unread upstream.
"""
from pathlib import Path
import numpy as np
import pandas as pd

import analyze_v298_1head_threat_listwise_trifecta5 as v298
import run_v300_1head_trifecta3_feature_upgrade as v300

ROOT=Path(__file__).resolve().parent
SEL=ROOT/'analysis_v308_1head_volume_opponent_joint_best_selected.csv'
P=ROOT/'analysis_v309_1head_opponent_zero_base_audit'
S=ROOT/'summary_v309_1head_opponent_zero_base_audit.md'
TM=list(v298.TEST_MONTHS)


def rank_of(prob_map, boat):
    order=[int(b) for b,_ in sorted(prob_map.items(), key=lambda kv: kv[1], reverse=True)]
    try:return order.index(int(boat))+1
    except ValueError:return np.nan


def topk(prob_map,k):
    return [int(b) for b,_ in sorted(prob_map.items(), key=lambda kv: kv[1], reverse=True)[:k]]


def main():
    if not SEL.exists(): raise RuntimeError('missing frozen v308 selected set')
    frozen=pd.read_csv(SEL,dtype={'race_code':str})
    frozen['race_code']=frozen.race_code.astype(str).str.zfill(12)
    if len(frozen)!=345: raise RuntimeError(f'expected frozen 345 races, got {len(frozen)}')
    ids=set(frozen.race_code)

    v300.setup_v298()
    d,_=v298.v294.freeze_true_pre()
    d=v298.v294.add_prior_history(d); d=v298.v294.add_rel(d); d,_=v298.add_threat(d)
    d,_=v298.v297.settle_full_after_freeze(d)
    d=d[(d.valid_result==1)&(d.combo_valid==1)].copy()
    sufs=v298.suffixes(d)
    sl=v300.augment_second(v298.second_long(d,sufs))
    cl=v300.augment_third(v298.conditional_long(d,sufs))

    rows=[]
    for tm in TM:
        p2,_=v300.p2_predict(sl,tm,3.0,True)
        pc,_=v300.pc_predict(cl,tm,.1,True)
        q=d[d.month==tm].copy()
        q['race_code']=q.race_code.astype(str).str.zfill(12)
        q=q[q.race_code.isin(ids)]
        for _,r in q.iterrows():
            code=r.race_code
            combo=str(r.actual_combo)
            parts=combo.split('-') if combo else []
            if len(parts)!=3: continue
            a1,a2,a3=map(int,parts)
            p2m=p2[code]; pcm=pc[code]
            s_rank=rank_of(p2m,a2) if a1==1 else np.nan
            cond={t:p for (s,t),p in pcm.items() if int(s)==a2}
            t_rank=rank_of(cond,a3) if a1==1 else np.nan
            pred_s=topk(p2m,1)[0]
            pred_cond={t:p for (s,t),p in pcm.items() if int(s)==pred_s}
            pred_t_rank=rank_of(pred_cond,a3) if (a1==1 and pred_s==a2) else np.nan
            tickets=v300.ticket3(p2m,pcm).split(';')
            rows.append({
                'date':r.date,'month':tm,'race_code':code,'venue':r.venue,'race':r.race,
                'head_hit':int(a1==1),'actual_combo':combo,'actual2':a2,'actual3':a3,
                'second_rank':s_rank,'third_rank_given_actual2':t_rank,
                'second_top1':int(a1==1 and s_rank<=1) if pd.notna(s_rank) else 0,
                'second_top2':int(a1==1 and s_rank<=2) if pd.notna(s_rank) else 0,
                'second_top3':int(a1==1 and s_rank<=3) if pd.notna(s_rank) else 0,
                'third_top1_given_actual2':int(a1==1 and t_rank<=1) if pd.notna(t_rank) else 0,
                'third_top2_given_actual2':int(a1==1 and t_rank<=2) if pd.notna(t_rank) else 0,
                'third_top3_given_actual2':int(a1==1 and t_rank<=3) if pd.notna(t_rank) else 0,
                'pred_second':pred_s,'third_rank_when_second_correct':pred_t_rank,
                'tickets':'|'.join(tickets),'exact3':int(combo in tickets)
            })
        print('v309 fold',tm,'done',len(q),flush=True)

    z=pd.DataFrame(rows)
    if len(z)!=345 or z.head_hit.sum()!=290:
        raise RuntimeError(f'frozen audit mismatch R={len(z)} head={int(z.head_hit.sum())}')
    h=z[z.head_hit==1].copy()

    overall=pd.DataFrame([{
        'R':len(z),'head_hits':int(z.head_hit.sum()),'head_rate':z.head_hit.mean(),
        'exact3_hits':int(z.exact3.sum()),'exact3_rate':z.exact3.mean(),
        'second_top1_on_headwins':h.second_top1.mean(),
        'second_top2_on_headwins':h.second_top2.mean(),
        'second_top3_on_headwins':h.second_top3.mean(),
        'third_top1_given_actual2_on_headwins':h.third_top1_given_actual2.mean(),
        'third_top2_given_actual2_on_headwins':h.third_top2_given_actual2.mean(),
        'third_top3_given_actual2_on_headwins':h.third_top3_given_actual2.mean(),
    }])
    monthly=z.groupby('month').agg(R=('race_code','size'),head_hits=('head_hit','sum'),exact3_hits=('exact3','sum')).reset_index()
    monthly['head_rate']=monthly.head_hits/monthly.R; monthly['exact3_rate']=monthly.exact3_hits/monthly.R
    mh=h.groupby('month').agg(headwin_R=('race_code','size'),second_top1=('second_top1','mean'),second_top2=('second_top2','mean'),second_top3=('second_top3','mean'),third_top1=('third_top1_given_actual2','mean'),third_top2=('third_top2_given_actual2','mean'),third_top3=('third_top3_given_actual2','mean')).reset_index()
    monthly=monthly.merge(mh,on='month',how='left')

    by_second=h.groupby('actual2').agg(R=('race_code','size'),second_top1=('second_top1','mean'),second_top2=('second_top2','mean'),third_top2=('third_top2_given_actual2','mean'),exact3=('exact3','mean')).reset_index()
    by_pair=h.groupby(['actual2','actual3']).agg(R=('race_code','size'),exact3=('exact3','mean')).reset_index().sort_values('R',ascending=False)
    err=h.copy()
    err['error_class']=np.select([
        err.exact3.eq(1),
        err.second_top2.eq(0),
        err.second_top2.eq(1)&err.third_top2_given_actual2.eq(0),
    ],['EXACT3_HIT','SECOND_OUTSIDE_TOP2','THIRD_OUTSIDE_TOP2_GIVEN_ACTUAL2'],default='COMBINATION_POLICY_OR_ORDER')
    ec=err.groupby('error_class').size().reset_index(name='R').sort_values('R',ascending=False)
    ec['share_of_headwins']=ec.R/len(h)

    z.to_csv(str(P)+'_race.csv',index=False)
    overall.to_csv(str(P)+'_overall.csv',index=False)
    monthly.to_csv(str(P)+'_monthly.csv',index=False)
    by_second.to_csv(str(P)+'_by_actual_second.csv',index=False)
    by_pair.to_csv(str(P)+'_by_pair.csv',index=False)
    ec.to_csv(str(P)+'_error_classes.csv',index=False)

    o=overall.iloc[0]
    L=['# v309 opponent zero-base audit','',
       '- Frozen head model/race set: v308 selected 345 races. No race-selection retuning.',
       '- Current opponent benchmark: v300 augmented SECOND L2=3 / conditional THIRD L2=.1 / TOP2XTOP2 alpha=.60.',
       '- Boat-1 losses remain exact-ticket misses.', '',
       '## Overall decomposition',
       f"- R=**345**; head wins **290/345 = {100*o.head_rate:.2f}%**; exact 3-ticket **{int(o.exact3_hits)}/345 = {100*o.exact3_rate:.2f}%**",
       f"- On the 290 head-win races, actual SECOND rank: TOP1 **{100*o.second_top1_on_headwins:.2f}%**, TOP2 **{100*o.second_top2_on_headwins:.2f}%**, TOP3 **{100*o.second_top3_on_headwins:.2f}%**",
       f"- Given the actual SECOND, actual THIRD rank: TOP1 **{100*o.third_top1_given_actual2_on_headwins:.2f}%**, TOP2 **{100*o.third_top2_given_actual2_on_headwins:.2f}%**, TOP3 **{100*o.third_top3_given_actual2_on_headwins:.2f}%**",'',
       '## Error classes on head-win races','|class|R|share|','|---|---:|---:|']
    for _,r in ec.iterrows():L.append(f"|{r.error_class}|{int(r.R)}|{100*r.share_of_headwins:.2f}%|")
    L += ['', '## Monthly diagnostic','|month|R|head|exact3|second TOP2|third TOP2 given actual second|','|---|---:|---:|---:|---:|---:|']
    for _,r in monthly.iterrows():
        L.append(f"|{r.month}|{int(r.R)}|{int(r.head_hits)}|{100*r.exact3_rate:.2f}%|{100*r.second_top2:.2f}%|{100*r.third_top2:.2f}%|")
    L += ['', '## By actual SECOND','|actual second|R|second TOP1|second TOP2|third TOP2|exact3|','|---:|---:|---:|---:|---:|---:|']
    for _,r in by_second.iterrows():
        L.append(f"|{int(r.actual2)}|{int(r.R)}|{100*r.second_top1:.2f}%|{100*r.second_top2:.2f}%|{100*r.third_top2:.2f}%|{100*r.exact3:.2f}%|")
    S.write_text('\n'.join(L)+'\n',encoding='utf-8')
    print(S.read_text(),flush=True)

if __name__=='__main__':main()
