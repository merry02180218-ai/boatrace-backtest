#!/usr/bin/env python3
"""Safe entrypoint for v301 transfer research; preserves v300 base augmenter references."""
from pathlib import Path
import analyze_v298_1head_threat_listwise_trifecta5 as v298
import run_v300_1head_trifecta3_feature_upgrade as v300
import run_v301_1head_trifecta3_transfer_3head4head_features as v301

ROOT=Path(__file__).resolve().parent
ORIG_SECOND=v300.augment_second
ORIG_THIRD=v300.augment_third


def aug_second(sl):
    # v301 augmenter delegates once to the frozen v300 augmenter.
    v300.augment_second=ORIG_SECOND
    try:
        return v301.augment_second(sl)
    finally:
        v300.augment_second=aug_second


def aug_third(cl):
    v300.augment_third=ORIG_THIRD
    try:
        return v301.augment_third(cl)
    finally:
        v300.augment_third=aug_third


def main():
    v300.setup_v298()
    v300.augment_second=aug_second
    v300.augment_third=aug_third
    d,_=v298.v294.freeze_true_pre();d=v298.v294.add_prior_history(d);d=v298.v294.add_rel(d);d,threat=v298.add_threat(d)
    fams=v298.v296.clean_manifest(d)
    for fs in fams.values():
        if any('meet_' in c for c in fs):raise RuntimeError('forbidden meeting feature')
    print('v301 PRE features frozen; audited settlement now',flush=True)
    d,cov=v298.v297.settle_full_after_freeze(d);d=d[(d.valid_result==1)&(d.combo_valid==1)].copy()
    p,folds,configs=v300.run(d,fams,threat)
    sel,score,monthly=v300.summarize(p,configs)
    p.to_csv(str(v301.PREFIX)+'_pred.csv',index=False)
    folds.to_csv(str(v301.PREFIX)+'_folds.csv',index=False)
    score.to_csv(str(v301.PREFIX)+'_configs.csv',index=False)
    monthly.to_csv(str(v301.PREFIX)+'_monthly.csv',index=False)
    txt=v301.make_summary(sel,score,monthly);v301.SUMMARY.write_text(txt,encoding='utf-8');print(txt,flush=True)

if __name__=='__main__':main()
