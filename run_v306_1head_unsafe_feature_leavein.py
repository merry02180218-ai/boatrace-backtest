#!/usr/bin/env python3
"""v306: attribute v304 gain to the 9 operationally-unproven meeting-derived features.
Development only. Same frozen 204-race monthly coverage. Jul/Aug NON-PRISTINE; Sep unread.
Each unsafe feature is added back ONE AT A TIME to the strict-safe TURN_FORM+STMOTOR set.
This identifies which exact snapshot field creates the apparent v304 lift without adopting it.
"""
from pathlib import Path
import pandas as pd
import analyze_v298_1head_threat_listwise_trifecta5 as v298
import run_v300_1head_trifecta3_feature_upgrade as v300
import run_v303_1head_headmodel_transfer_ablation as v303
import run_v305_1head_leakage_audit as v305

ROOT=Path(__file__).resolve().parent
PREFIX=ROOT/'analysis_v306_1head_unsafe_feature_leavein'
SUMMARY=ROOT/'summary_v306_1head_unsafe_feature_leavein.md'
TM=list(v298.TEST_MONTHS)

def main():
    v300.setup_v298()
    d,_=v298.v294.freeze_true_pre(); d=v298.v294.add_prior_history(d); d=v298.v294.add_rel(d)
    d,threat=v298.add_threat(d); fams=v298.v296.clean_manifest(d); d,tf=v303.add_transfer_features(d)
    alltf=list(dict.fromkeys(tf['TURN_FORM']+tf['STMOTOR']))
    unsafe=[c for c in alltf if 'meet_' in c.lower()]
    safe=[c for c in alltf if c not in unsafe]
    if len(unsafe)!=9: raise RuntimeError(f'expected 9 unsafe features, got {len(unsafe)}: {unsafe}')
    print('v306 unsafe features',*unsafe,sep='\n',flush=True)
    d,_=v298.v297.settle_full_after_freeze(d); d=d[(d.valid_result==1)&(d.combo_valid==1)].copy()
    masses=v303.opponent_mass(d)
    core0=list(dict.fromkeys(fams['CLEAN_STATIC6_PLAYER']+threat)); guard0=[c for c in core0 if c.startswith(('b1_','b2_','b3_','b4_','rel_','attack23_','v298_'))]
    configs={'BASE':[], 'STRICT_SAFE':safe, 'FULL_ALL9':safe+unsafe}
    for i,c in enumerate(unsafe,1): configs[f'ADD_{i:02d}'] = safe+[c]
    pred=[]; fmap=[]
    for i,c in enumerate(unsafe,1): fmap.append({'config':f'ADD_{i:02d}','feature':c})
    for tm in TM:
        tr=d[d.month<tm].copy(); te=d[d.month==tm].copy(); z=te[['date','month','race_code','venue','race','head_hit']].copy(); z['test_month']=tm
        z['opp_mass']=[masses[str(x).zfill(12)] for x in z.race_code]; z['eligible']=(z.opp_mass>=v300.BASE_CONF).astype(int)
        bc=v298.v293.available(tr,core0,.55); bg=v298.v293.available(tr,guard0,.55)
        ph,_,hc,_,_,_=v298.head_fold(tr,te,bc,bg); bsel=(ph>=hc[.95])&(z.eligible.to_numpy()==1); n=int(bsel.sum())
        z['sel_BASE']=bsel.astype(int); z['p_BASE']=ph
        for name,raw in configs.items():
            if name=='BASE': continue
            ex=v303.available(tr,list(dict.fromkeys(raw))); px,_,_,_,_,_=v298.head_fold(tr,te,list(dict.fromkeys(bc+ex)),bg)
            z[f'p_{name}']=px; idx=z[z.eligible==1].sort_values(f'p_{name}',ascending=False).head(n).index; z[f'sel_{name}']=0; z.loc[idx,f'sel_{name}']=1
        pred.append(z); print('v306 fold',tm,'n',n,flush=True)
    p=pd.concat(pred,ignore_index=True); b=p[p.sel_BASE==1]
    if len(b)!=204 or int(b.head_hit.sum())!=166: raise RuntimeError(f'baseline drift {len(b)} {int(b.head_hit.sum())}')
    rows=[]; mon=[]
    for name in configs:
        s=p[p[f'sel_{name}']==1]; gm=s.groupby('test_month').head_hit.agg(['size','sum','mean'])
        rows.append({'config':name,'R':len(s),'hits':int(s.head_hit.sum()),'rate':float(s.head_hit.mean()),'worst_month':float(gm['mean'].min())})
        for mo,r in gm.iterrows(): mon.append({'config':name,'month':mo,'R':int(r['size']),'hits':int(r['sum']),'rate':float(r['mean'])})
    score=pd.DataFrame(rows); strict=float(score.loc[score.config=='STRICT_SAFE','rate'].iloc[0]); score['delta_vs_strict']=score.rate-strict
    score=score.merge(pd.DataFrame(fmap),on='config',how='left')
    p.to_csv(str(PREFIX)+'_pred.csv',index=False); score.to_csv(str(PREFIX)+'_configs.csv',index=False); pd.DataFrame(mon).to_csv(str(PREFIX)+'_monthly.csv',index=False)
    singles=score[score.config.str.startswith('ADD_')].sort_values(['rate','worst_month'],ascending=False)
    L=['# v306 1HEAD unsafe meeting-feature attribution','', '- Development only; no unsafe feature is eligible for production adoption.', '- Same frozen 204-race coverage as v303-v305. Jul/Aug NON-PRISTINE; September outcomes unread.','', '## One-at-a-time add-back','|config|feature|hits/R|rate|delta vs strict|worst month|','|---|---|---:|---:|---:|---:|']
    for _,r in singles.iterrows(): L.append(f"|{r.config}|`{r.feature}`|{int(r.hits)}/{int(r.R)}|{100*r.rate:.2f}%|{100*r.delta_vs_strict:+.2f}pt|{100*r.worst_month:.2f}%|")
    for name in ['BASE','STRICT_SAFE','FULL_ALL9']:
        r=score[score.config==name].iloc[0]; L += ['',f'- {name}: **{int(r.hits)}/{int(r.R)} = {100*r.rate:.2f}%**, worst month {100*r.worst_month:.2f}%.']
    best=singles.iloc[0]; L += ['', '## Decision', f"- Largest single unsafe lift: `{best.feature}` => **{int(best.hits)}/204 = {100*best.rate:.2f}%** ({100*best.delta_vs_strict:+.2f}pt vs strict).", '- Treat all nine meeting-snapshot features as contaminated until a causal prior-race-only reconstruction reproduces the signal.']
    SUMMARY.write_text('\n'.join(L)+'\n',encoding='utf-8'); print(SUMMARY.read_text(),flush=True)
if __name__=='__main__': main()
