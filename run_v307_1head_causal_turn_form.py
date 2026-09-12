#!/usr/bin/env python3
"""v307: replace unsafe meeting-snapshot signal with causal prior-day features only.
Development only. Same frozen 204-race monthly coverage; Jul/Aug NON-PRISTINE; Sep unread.
No meet_win / meet_st_strength-derived feature is permitted.
"""
from pathlib import Path
import pandas as pd
import numpy as np
import analyze_v298_1head_threat_listwise_trifecta5 as v298
import run_v300_1head_trifecta3_feature_upgrade as v300
import run_v303_1head_headmodel_transfer_ablation as v303
import run_v305_1head_leakage_audit as v305

ROOT=Path(__file__).resolve().parent
PREFIX=ROOT/'analysis_v307_1head_causal_turn_form'
SUMMARY=ROOT/'summary_v307_1head_causal_turn_form.md'
TM=list(v298.TEST_MONTHS)

def num(s): return pd.to_numeric(s,errors='coerce')

def add_causal(d):
    q=d.copy(); made=[]
    # Strictly prior-day player state and prior exhibition state from v221.build.
    player=['pl_all_win','pl_all_p2','pl_frame_win','pl_frame_p2','pl_recent_p2']
    prior=['vh_p12_turn','gh_p12_turn','vh_p12_straight','gh_p12_straight','vh_p12_overall','gh_p12_overall']
    # Per-boat composites: form, frame-fit, turn/foot, and start/motor static interaction.
    for b in range(1,7):
        def col(k): return f'b{b}_{k}'
        req=[col(k) for k in player]
        if all(c in q for c in req):
            q[f'v307_b{b}_prior_form']=0.35*num(q[col('pl_all_win')])+0.25*num(q[col('pl_all_p2')])+0.20*num(q[col('pl_frame_win')])+0.10*num(q[col('pl_frame_p2')])+0.10*num(q[col('pl_recent_p2')]); made.append(f'v307_b{b}_prior_form')
            q[f'v307_b{b}_frame_form']=0.55*num(q[col('pl_frame_win')])+0.30*num(q[col('pl_frame_p2')])+0.15*num(q[col('pl_recent_p2')]); made.append(f'v307_b{b}_frame_form')
        avail=[col(k) for k in prior if col(k) in q]
        if avail:
            vals=pd.concat([num(q[c]) for c in avail],axis=1)
            q[f'v307_b{b}_prior_foot']=vals.mean(axis=1); made.append(f'v307_b{b}_prior_foot')
        if col('nst_strength') in q and col('motor') in q:
            q[f'v307_b{b}_start_motor']=num(q[col('nst_strength')])*num(q[col('motor')]); made.append(f'v307_b{b}_start_motor')
    # Relative boat-1 vs each opponent and strongest opponent, mirroring the unsafe meet_win geometry.
    bases=['prior_form','frame_form','prior_foot','start_motor']
    for k in bases:
        b1=f'v307_b1_{k}'
        if b1 not in q: continue
        opp=[]
        for b in range(2,7):
            c=f'v307_b{b}_{k}'
            if c not in q: continue
            n=f'v307_{k}_b1_minus_b{b}'; q[n]=num(q[b1])-num(q[c]); made.append(n); opp.append(c)
        if opp:
            n=f'v307_{k}_b1_minus_maxopp'; q[n]=num(q[b1])-pd.concat([num(q[c]) for c in opp],axis=1).max(axis=1); made.append(n)
    # Key pair interactions aimed specifically at replacing b1-b2 meet_win.
    for a,b in [('prior_form','prior_foot'),('frame_form','prior_foot'),('prior_form','start_motor')]:
        ca=f'v307_{a}_b1_minus_b2'; cb=f'v307_{b}_b1_minus_b2'
        if ca in q and cb in q:
            n=f'v307_b1v2_{a}_x_{b}'; q[n]=num(q[ca])*num(q[cb]); made.append(n)
    return q,list(dict.fromkeys(made))

def main():
    v300.setup_v298()
    d,_=v298.v294.freeze_true_pre(); d=v298.v294.add_prior_history(d); d=v298.v294.add_rel(d); d,threat=v298.add_threat(d)
    fams=v298.v296.clean_manifest(d); d,tf=v303.add_transfer_features(d); d,causal=add_causal(d)
    strict=list(dict.fromkeys(v305.safe_transfer(tf['TURN_FORM'])+v305.safe_transfer(tf['STMOTOR'])))
    if any('meet_' in c.lower() for c in strict+causal): raise RuntimeError('unsafe meet feature entered v307')
    print('v307 PRE frozen; causal features',len(causal),flush=True)
    d,_=v298.v297.settle_full_after_freeze(d); d=d[(d.valid_result==1)&(d.combo_valid==1)].copy(); masses=v303.opponent_mass(d)
    core0=list(dict.fromkeys(fams['CLEAN_STATIC6_PLAYER']+threat)); guard0=[c for c in core0 if c.startswith(('b1_','b2_','b3_','b4_','rel_','attack23_','v298_'))]
    configs={'BASE':[], 'STRICT_SAFE':strict, 'CAUSAL_ONLY':causal, 'STRICT_PLUS_CAUSAL':strict+causal}
    pred=[]
    for tm in TM:
        tr=d[d.month<tm].copy(); te=d[d.month==tm].copy(); z=te[['date','month','race_code','venue','race','head_hit']].copy(); z['test_month']=tm
        z['opp_mass']=[masses[str(x).zfill(12)] for x in z.race_code]; z['eligible']=(z.opp_mass>=v300.BASE_CONF).astype(int)
        bc=v298.v293.available(tr,core0,.55); bg=v298.v293.available(tr,guard0,.55)
        ph,_,hc,_,_,_=v298.head_fold(tr,te,bc,bg); bsel=(ph>=hc[.95])&(z.eligible.to_numpy()==1); n=int(bsel.sum()); z['p_BASE']=ph; z['sel_BASE']=bsel.astype(int)
        for name,raw in configs.items():
            if name=='BASE': continue
            ex=v303.available(tr,list(dict.fromkeys(raw))); px,_,_,_,_,_=v298.head_fold(tr,te,list(dict.fromkeys(bc+ex)),bg)
            z[f'p_{name}']=px; idx=z[z.eligible==1].sort_values(f'p_{name}',ascending=False).head(n).index; z[f'sel_{name}']=0; z.loc[idx,f'sel_{name}']=1
        pred.append(z); print('v307 fold',tm,'n',n,flush=True)
    p=pd.concat(pred,ignore_index=True); base=p[p.sel_BASE==1]
    if len(base)!=204 or int(base.head_hit.sum())!=166: raise RuntimeError(f'baseline drift R={len(base)} hits={int(base.head_hit.sum())}')
    rows=[]; mon=[]
    for name in configs:
        s=p[p[f'sel_{name}']==1]; gm=s.groupby('test_month').head_hit.agg(['size','sum','mean'])
        rows.append({'config':name,'R':len(s),'hits':int(s.head_hit.sum()),'rate':float(s.head_hit.mean()),'worst_month':float(gm['mean'].min())})
        for mo,r in gm.iterrows(): mon.append({'config':name,'month':mo,'R':int(r['size']),'hits':int(r['sum']),'rate':float(r['mean'])})
    score=pd.DataFrame(rows); br=float(score.loc[score.config=='BASE','rate'].iloc[0]); score['delta_vs_base']=score.rate-br
    p.to_csv(str(PREFIX)+'_pred.csv',index=False); score.to_csv(str(PREFIX)+'_configs.csv',index=False); pd.DataFrame(mon).to_csv(str(PREFIX)+'_monthly.csv',index=False); pd.DataFrame({'feature':causal}).to_csv(str(PREFIX)+'_features.csv',index=False)
    best=score.sort_values(['rate','worst_month'],ascending=False).iloc[0]
    L=['# v307 1HEAD causal turn-form research','', '- Development only; production unchanged.', '- Same frozen 204-race coverage. Jul/Aug NON-PRISTINE; September outcomes unread.', '- No meet_win / meet_st_strength-derived transfer feature is allowed.', f'- Causal engineered features: **{len(causal)}**.','', '## Results','|config|hits/R|rate|delta vs base|worst month|','|---|---:|---:|---:|---:|']
    for _,r in score.sort_values(['rate','worst_month'],ascending=False).iterrows(): L.append(f"|{r.config}|{int(r.hits)}/{int(r.R)}|{100*r.rate:.2f}%|{100*r.delta_vs_base:+.2f}pt|{100*r.worst_month:.2f}%|")
    L += ['', '## Best monthly audit','|month|R|hits|rate|','|---|---:|---:|---:|']
    mm=pd.DataFrame(mon); 
    for _,r in mm[mm.config==best.config].iterrows(): L.append(f"|{r.month}|{int(r.R)}|{int(r.hits)}|{100*r.rate:.2f}%|")
    L += ['', '## Decision', f"- Best leak-free candidate: **{best.config}: {int(best.hits)}/204 = {100*best.rate:.2f}%**, worst month {100*best.worst_month:.2f}%.", '- This is still reused Feb-Jun development evidence; prospective validation is required before promotion.']
    SUMMARY.write_text('\n'.join(L)+'\n',encoding='utf-8'); print(SUMMARY.read_text(),flush=True)
if __name__=='__main__': main()
