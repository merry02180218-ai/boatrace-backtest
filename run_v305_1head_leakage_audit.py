#!/usr/bin/env python3
"""v305: leakage audit for v304 1-head TURN_FORM + STMOTOR gains.

Development-only. Jul/Aug remain NON-PRISTINE; September outcomes unread.
Audit goals:
1) enumerate exact transferred feature columns and flag meeting-derived fields;
2) rerun the same frozen monthly coverage after removing all `meet_*`-derived transfer features;
3) compare FULL v304 against strict PRE-safe variants.

Important: prior player/exhibition histories created by v221.build are frozen before ingesting
day-D previews/results. Current-card grade/wr/local/nst/motor are scheduled PRE fields.
Meeting-derived fields are treated as UNSAFE here because the retained historical race-card
snapshot is not time-versioned within day D, so operational availability cannot be proven.
"""
from pathlib import Path
import pandas as pd

import analyze_v298_1head_threat_listwise_trifecta5 as v298
import run_v300_1head_trifecta3_feature_upgrade as v300
import run_v303_1head_headmodel_transfer_ablation as v303

ROOT=Path(__file__).resolve().parent
PREFIX=ROOT/'analysis_v305_1head_leakage_audit'
SUMMARY=ROOT/'summary_v305_1head_leakage_audit.md'
TM=list(v298.TEST_MONTHS)


def safe_transfer(fs):
    # fail-closed: anything derived from meeting aggregates is excluded.
    return [c for c in fs if 'meet_' not in c.lower()]


def classify(c):
    x=c.lower()
    if 'meet_' in x:return 'UNSAFE_MEETING_SNAPSHOT'
    if '_pl_' in x:return 'SAFE_PRIOR_PLAYER_DAY'
    if '_vh_' in x or '_gh_' in x:return 'SAFE_PRIOR_EXHIBITION_DAY'
    if any(k in x for k in ('_grade','_wr','_local')):return 'SAFE_CURRENT_CARD_STATIC'
    if 'nst_strength' in x or '_motor' in x:return 'SAFE_CURRENT_CARD_STATIC'
    return 'REVIEW'


def main():
    v300.setup_v298()
    d,_=v298.v294.freeze_true_pre()
    d=v298.v294.add_prior_history(d)
    d=v298.v294.add_rel(d)
    d,threat=v298.add_threat(d)
    fams=v298.v296.clean_manifest(d)
    d,tf=v303.add_transfer_features(d)

    # Feature inventory before settlement.
    inv=[]
    for fam in ('TURN_FORM','STMOTOR'):
        for c in tf[fam]:
            inv.append({'family':fam,'feature':c,'audit_class':classify(c),'strict_safe':int(c in safe_transfer(tf[fam]))})
    inv=pd.DataFrame(inv).drop_duplicates()
    inv.to_csv(str(PREFIX)+'_feature_inventory.csv',index=False)

    print('v305 PRE frozen; settlement now',flush=True)
    d,_=v298.v297.settle_full_after_freeze(d)
    d=d[(d.valid_result==1)&(d.combo_valid==1)].copy()
    masses=v303.opponent_mass(d)
    core0=list(dict.fromkeys(fams['CLEAN_STATIC6_PLAYER']+threat))
    guard0=[c for c in core0 if c.startswith(('b1_','b2_','b3_','b4_','rel_','attack23_','v298_'))]

    configs={
      'BASE':[],
      'V304_FULL':tf['TURN_FORM']+tf['STMOTOR'],
      'STRICT_TURN_FORM':safe_transfer(tf['TURN_FORM']),
      'STRICT_TURN_FORM_STMOTOR':safe_transfer(tf['TURN_FORM'])+safe_transfer(tf['STMOTOR']),
    }

    pred=[]; availability=[]
    for tm in TM:
        tr=d[d.month<tm].copy();te=d[d.month==tm].copy()
        z=te[['date','month','race_code','venue','race','head_hit']].copy();z['test_month']=tm
        z['opp_mass']=[masses[str(x).zfill(12)] for x in z.race_code]
        z['eligible']=(z.opp_mass>=v300.BASE_CONF).astype(int)
        base_core=v298.v293.available(tr,core0,.55);base_guard=v298.v293.available(tr,guard0,.55)
        ph,_,hc,_,_,_=v298.head_fold(tr,te,base_core,base_guard)
        base_sel=(ph>=hc[.95])&(z.eligible.to_numpy()==1);n=int(base_sel.sum())
        z['p_BASE']=ph;z['sel_BASE']=base_sel.astype(int)

        for name,rawextra in configs.items():
            if name=='BASE':continue
            extra=v303.available(tr,list(dict.fromkeys(rawextra)))
            availability.append({'month':tm,'config':name,'available_features':len(extra),
                                 'meeting_features':sum('meet_' in c.lower() for c in extra)})
            phx,_,_,_,_,_=v298.head_fold(tr,te,list(dict.fromkeys(base_core+extra)),base_guard)
            z[f'p_{name}']=phx
            idx=z[z.eligible==1].sort_values(f'p_{name}',ascending=False).head(n).index
            z[f'sel_{name}']=0;z.loc[idx,f'sel_{name}']=1
        pred.append(z);print('v305 fold',tm,'n',n,flush=True)

    p=pd.concat(pred,ignore_index=True)
    base=p[p.sel_BASE==1]
    if len(base)!=204 or int(base.head_hit.sum())!=166:
        raise RuntimeError(f'baseline drift R={len(base)} hits={int(base.head_hit.sum())}')

    rows=[];monthly=[]
    for name in configs:
        s=p[p[f'sel_{name}']==1];gm=s.groupby('test_month').head_hit.agg(['size','sum','mean'])
        rows.append({'config':name,'R':len(s),'head_hits':int(s.head_hit.sum()),'head_rate':float(s.head_hit.mean()),'worst_month':float(gm['mean'].min())})
        for mo,r in gm.iterrows():monthly.append({'config':name,'month':mo,'R':int(r['size']),'hits':int(r['sum']),'head_rate':float(r['mean'])})
    score=pd.DataFrame(rows);mon=pd.DataFrame(monthly)
    base_rate=float(score.loc[score.config=='BASE','head_rate'].iloc[0]);score['delta']=score.head_rate-base_rate
    p.to_csv(str(PREFIX)+'_pred.csv',index=False);score.to_csv(str(PREFIX)+'_configs.csv',index=False)
    mon.to_csv(str(PREFIX)+'_monthly.csv',index=False);pd.DataFrame(availability).to_csv(str(PREFIX)+'_availability.csv',index=False)

    unsafe=inv[inv.audit_class=='UNSAFE_MEETING_SNAPSHOT']
    strict=score[score.config=='STRICT_TURN_FORM_STMOTOR'].iloc[0]
    full=score[score.config=='V304_FULL'].iloc[0]
    L=['# v305 1HEAD leakage audit','',
       '- Development only; production unchanged.','- Jul/Aug NON-PRISTINE; September outcomes unread.',
       '- Same frozen opponent eligibility and exact monthly selected counts as v303/v304.',
       '- Meeting-derived transfer fields are fail-closed as unsafe because historical race-card snapshots are not intraday-versioned.','',
       '## Feature provenance audit',f'- Transferred TURN_FORM/STMOTOR features inventoried: **{len(inv)}**.',
       f'- Meeting-derived / operationally unproven features: **{len(unsafe)}**.','',
       '## Results','|config|R|head hits|head rate|delta|worst month|','|---|---:|---:|---:|---:|---:|']
    for _,r in score.sort_values(['head_rate','worst_month'],ascending=False).iterrows():
        L.append(f"|{r.config}|{int(r.R)}|{int(r.head_hits)}|{100*r.head_rate:.2f}%|{100*r.delta:+.2f}pt|{100*r.worst_month:.2f}%|")
    L+=['','## Strict-safe monthly audit','|month|R|hits|head rate|','|---|---:|---:|---:|']
    for _,r in mon[mon.config=='STRICT_TURN_FORM_STMOTOR'].iterrows():
        L.append(f"|{r.month}|{int(r.R)}|{int(r.hits)}|{100*r.head_rate:.2f}%|")
    drop=float(full.head_rate-strict.head_rate)
    L+=['','## Decision',f'- FULL v304: **{int(full.head_hits)}/204 = {100*full.head_rate:.2f}%**.',
        f'- STRICT no-meeting transfer: **{int(strict.head_hits)}/204 = {100*strict.head_rate:.2f}%**.',
        f'- Removing operationally unproven meeting-derived transfer fields changes head rate by **{-100*drop:+.2f}pt**.',
        '- If STRICT retains most of the gain, the late-month decline is more consistent with distribution/season drift than direct meeting-field leakage. If STRICT collapses, v304 gain must be treated as contaminated until those fields are reconstructed causally.']
    SUMMARY.write_text('\n'.join(L)+'\n',encoding='utf-8');print(SUMMARY.read_text(),flush=True)

if __name__=='__main__':main()
