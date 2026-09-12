#!/usr/bin/env python3
from __future__ import annotations
import copy,math
import head4_v273_a_live_inference as h

FEATURES=[f'f{i}' for i in range(17)]
def artifact():
    return {'schema':'head4_v273_a_live_artifact_v1','policy':h.POLICY,'frozen_training_cutoff':h.CUTOFF,
      'production_inference_only':True,'jul_aug_labels_used':False,'september_labels_used':False,'v96_production_signal_used':False,
      'mapping':{'method':'OUTCOME_BLIND_SELECTED_FRACTION_QUANTILE','outcomes_used_by_mapping':False},
      'S_gate':{'PRE':.28,'POST':.25,'ENV_ENTRY':.224790},'A_gate':{'PRE':.18,'POST':.18,'A_SCORE_LIVE':.40},
      'A_SCORE':{'features':FEATURES,'imputer_median':[0.]*17,'scaler_mean':[0.]*17,'scaler_scale':[1.]*17,
                 'coef':[1.]+[0.]*16,'intercept':0.0}}

def main():
    a=artifact();h.validate_artifact(a);row={f:0.0 for f in FEATURES}
    assert abs(h.score_a(row,a)-.5)<1e-12
    assert h.classify(.30,.30,.30,row,a)['layer']=='S'
    assert h.classify(.20,.20,.10,row,a)['layer']=='A'
    assert h.classify(.17,.30,.10,row,a)['layer']=='NONE'
    q=dict(row);q['f0']=float('nan');assert math.isfinite(h.score_a(q,a))
    q=dict(row);q.pop('f3')
    try:h.score_a(q,a);raise AssertionError('missing key accepted')
    except h.FrozenARankError:pass
    b=copy.deepcopy(a);b['jul_aug_labels_used']=True
    try:h.validate_artifact(b);raise AssertionError('contamination flag accepted')
    except h.FrozenARankError:pass
    b=copy.deepcopy(a);b['mapping']['outcomes_used_by_mapping']=True
    try:h.validate_artifact(b);raise AssertionError('outcome-based mapping accepted')
    except h.FrozenARankError:pass
    print('PASS: frozen v273 A LIVE inference guards')
if __name__=='__main__':main()
