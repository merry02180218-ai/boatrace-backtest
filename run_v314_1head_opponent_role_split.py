#!/usr/bin/env python3
"""v314: role-split SECOND autoresearch on frozen v308 345R cohort.

Goal
----
Address the persistent outer-boat SECOND failure by separating three tasks:
1) monthly walk-forward probability that SECOND is outer (4/5/6),
2) specialist ranking inside inner boats (2/3),
3) specialist ranking inside outer boats (4/5/6).

The three distributions are recombined without changing the frozen boat-1 head cohort
or the conditional THIRD model. Uses the reusable v313 causal cache. No meet_*, no
future backfill, Feb-Jun development only; Jul/Aug NON-PRISTINE and September unread.
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
P=ROOT/'analysis_v314_1head_opponent_role_split'
S=ROOT/'summary_v314_1head_opponent_role_split.md'
TM=list(v298.TEST_MONTHS)


def specialist_predict(sl, tm, boats, l2=3.0):
    boats=set(int(x) for x in boats)
    tr=sl[(sl.month<tm) & sl.actual2.isin(boats) & sl.boat.astype(int).isin(boats)].copy()
    te=sl[(sl.month==tm) & sl.boat.astype(int).isin(boats)].copy()
    fs=v311.audited_features(tr)
    fs=[c for c in fs if v311.family(c)!='START']  # v311 development-best family choice
    if not fs: raise RuntimeError(f'v314 no specialist features month={tm} boats={boats}')
    if pd.to_numeric(tr.y2,errors='coerce').sum() < 8:
        raise RuntimeError(f'v314 too few specialist positives month={tm} boats={boats}')
    m=v300.fastbase.FastSecond(float(l2)).fit(tr,fs,'y2')
    te=te.copy(); te['score']=m.score(te)
    out={}
    for code,g in te.groupby('race_code'):
        out[str(code).zfill(12)]=v298.v279.probs_within_race(g,'score')
    return out,len(fs)


def combine(inner, outer, p_outer, base, gate_power=1.0, specialist_mix=1.0, floor=.03):
    # Keep a small prior floor so sparse gate estimates cannot fully erase a role.
    pg=float(np.clip(p_outer,floor,1-floor))
    if gate_power!=1.0:
        a=pg**gate_power; b=(1-pg)**gate_power; pg=a/(a+b)
    q={}
    for b in (2,3): q[b]=(1-pg)*float(inner.get(b,0.0))
    for b in (4,5,6): q[b]=pg*float(outer.get(b,0.0))
    s=sum(q.values())
    if s<=0: q={b:float(base.get(b,0.0)) for b in (2,3,4,5,6)}
    else: q={b:v/s for b,v in q.items()}
    mix=float(specialist_mix)
    if mix<1.0:
        q={b:mix*q.get(b,0.0)+(1-mix)*float(base.get(b,0.0)) for b in (2,3,4,5,6)}
        s=sum(q.values()); q={b:(q[b]/s if s>0 else .2) for b in q}
    return q


def evaluate(p2,pc,d,ids):
    rows=[]
    for tm in TM:
        q=d[(d.month==tm)&(d.race_code.isin(ids))].copy()
        for _,r in q.iterrows():
            code=str(r.race_code).zfill(12); parts=str(r.actual_combo).split('-')
            if len(parts)!=3: continue
            a1,a2,a3=map(int,parts); p2m=p2[tm][code]; pcm=pc[tm][code]
            sr=v309.rank_of(p2m,a2) if a1==1 else np.nan
            tickets=v300.ticket3(p2m,pcm).split(';')
            rows.append({'month':tm,'race_code':code,'head_hit':int(a1==1),'actual2':a2,'second_rank':sr,
                         'second_top1':int(a1==1 and pd.notna(sr) and sr<=1),
                         'second_top2':int(a1==1 and pd.notna(sr) and sr<=2),
                         'second_top3':int(a1==1 and pd.notna(sr) and sr<=3),
                         'exact3':int(str(r.actual_combo) in tickets)})
    z=pd.DataFrame(rows)
    if len(z)!=345 or int(z.head_hit.sum())!=290:
        raise RuntimeError(f'v314 frozen mismatch R={len(z)} head={int(z.head_hit.sum())}')
    h=z[z.head_hit==1].copy(); by=h.groupby('actual2').second_top2.mean().to_dict(); mon=h.groupby('month').second_top2.mean()
    return z,{'R':345,'head_hits':290,'exact3_hits':int(z.exact3.sum()),'exact3_rate':float(z.exact3.mean()),
              'second_top1':float(h.second_top1.mean()),'second_top2':float(h.second_top2.mean()),'second_top3':float(h.second_top3.mean()),
              'worst_month_second_top2':float(mon.min()),'outer456_top2':float(h[h.actual2.isin([4,5,6])].second_top2.mean()),
              'boat2_top2':float(by.get(2,np.nan)),'boat3_top2':float(by.get(3,np.nan)),'boat4_top2':float(by.get(4,np.nan)),
              'boat5_top2':float(by.get(5,np.nan)),'boat6_top2':float(by.get(6,np.nan))}


def main():
    frozen=pd.read_csv(SEL,dtype={'race_code':str}); frozen['race_code']=frozen.race_code.astype(str).str.zfill(12)
    if len(frozen)!=345: raise RuntimeError('v314 frozen cohort changed')
    ids=set(frozen.race_code)

    d,p3,p4=v312.load_cache(); d['race_code']=d.race_code.astype(str).str.zfill(12)
    q=d[d.race_code.isin(ids)]
    if len(q)!=345 or int(q.head_hit.sum())!=290: raise RuntimeError('v314 cache frozen mismatch')

    v300.setup_v298(); sufs=v298.suffixes(d)
    if any('meet_' in str(x) for x in sufs): raise RuntimeError('v314 forbidden meet leakage')
    sl=v310.add_headrisk(v300.augment_second(v298.second_long(d,sufs)),p3,p4)
    cl=v300.augment_third(v298.conditional_long(d,sufs))
    pc={tm:v300.pc_predict(cl,tm,.1,True)[0] for tm in TM}
    base={tm:v311.p2_predict_explicit(sl,tm,3.0,None,{'START'})[0] for tm in TM}

    gt=v312.gate_table(sl); gate={tm:v312.gate_predict(gt,tm,.3)[0] for tm in TM}
    inner={}; outer={}; frows=[]
    for tm in TM:
        inner[tm],ni=specialist_predict(sl,tm,(2,3),3.0)
        outer[tm],no=specialist_predict(sl,tm,(4,5,6),3.0)
        frows.append({'month':tm,'inner_features':ni,'outer_features':no})

    configs=[('DROP_START_BASE',0.0,1.0,.03)]
    for mix in (.50,.65,.80,1.00):
        for gp in (.65,.85,1.00,1.20,1.50):
            for floor in (.03,.08,.12):
                configs.append((f'ROLE_m{mix:.2f}_g{gp:.2f}_f{floor:.2f}',mix,gp,floor))

    sums=[]; outs=[]
    for name,mix,gp,floor in configs:
        p2={}
        for tm in TM:
            p2[tm]={}
            for code,bp in base[tm].items():
                if name=='DROP_START_BASE': p2[tm][code]=bp
                else: p2[tm][code]=combine(inner[tm][code],outer[tm][code],gate[tm].get(code,.5),bp,gp,mix,floor)
        z,m=evaluate(p2,pc,d,ids); z['config']=name; outs.append(z)
        m.update({'config':name,'specialist_mix':mix,'gate_power':gp,'gate_floor':floor}); sums.append(m)
        print('v314',name,m,flush=True)

    sm=pd.DataFrame(sums); baseM=sm[sm.config=='DROP_START_BASE'].iloc[0]
    for c,src in [('delta_top2_pp','second_top2'),('delta_outer_pp','outer456_top2'),('delta_exact3_pp','exact3_rate')]:
        sm[c]=100*(sm[src]-baseM[src])
    cand=sm[sm.config!='DROP_START_BASE'].copy()
    best=cand.sort_values(['second_top2','worst_month_second_top2','outer456_top2','exact3_rate'],ascending=False).iloc[0]
    allz=pd.concat(outs,ignore_index=True); bz=allz[allz.config==best.config].copy(); bh=bz[bz.head_hit==1]
    by=bh.groupby('actual2').agg(R=('race_code','size'),top2=('second_top2','mean'),top3=('second_top3','mean'),exact3=('exact3','mean')).reset_index()
    mon=bz.groupby('month').agg(R=('race_code','size'),head=('head_hit','sum'),exact3=('exact3','mean')).reset_index()
    mon=mon.merge(bh.groupby('month').second_top2.mean().rename('second_top2').reset_index(),on='month')

    sm.to_csv(str(P)+'_configs.csv',index=False); pd.DataFrame(frows).to_csv(str(P)+'_feature_counts.csv',index=False)
    by.to_csv(str(P)+'_best_by_second.csv',index=False); mon.to_csv(str(P)+'_best_monthly.csv',index=False); bz.to_csv(str(P)+'_best_race.csv',index=False)
    L=['# v314 role-split SECOND autoresearch','',
       '- Fixed v308 cohort: **345 races / 290 boat-1 wins**; IDs unchanged.',
       '- Uses v313 reusable causal cache. No `meet_*`; no future backfill.',
       '- SECOND split into outer gate + inner specialist (2/3) + outer specialist (4/5/6).',
       '- THIRD remains frozen v300 conditional L2=.1.',
       '- Feb-Jun development only; Jul/Aug NON-PRISTINE; September outcomes unread.','',
       '## Development result',
       f'- Base DROP_START TOP2 {100*baseM.second_top2:.2f}%, outer {100*baseM.outer456_top2:.2f}%, exact3 {int(baseM.exact3_hits)}/345={100*baseM.exact3_rate:.2f}%.',
       f'- Best **{best.config}** TOP2 **{100*best.second_top2:.2f}%**, outer **{100*best.outer456_top2:.2f}%**, exact3 **{int(best.exact3_hits)}/345={100*best.exact3_rate:.2f}%**, worst month **{100*best.worst_month_second_top2:.2f}%**.','',
       '## Best by actual SECOND','|boat|R|TOP2|TOP3|exact3|','|---:|---:|---:|---:|---:|']
    for _,r in by.iterrows(): L.append(f'|{int(r.actual2)}|{int(r.R)}|{100*r.top2:.2f}%|{100*r.top3:.2f}%|{100*r.exact3:.2f}%|')
    L+=['','## Monthly','|month|R|head|TOP2|exact3|','|---|---:|---:|---:|---:|']
    for _,r in mon.iterrows(): L.append(f'|{r.month}|{int(r.R)}|{int(r["head"])}|{100*r.second_top2:.2f}%|{100*r.exact3:.2f}%|')
    S.write_text('\n'.join(L)+'\n',encoding='utf-8'); print(S.read_text(),flush=True)

if __name__=='__main__': main()
