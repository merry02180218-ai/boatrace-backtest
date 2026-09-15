# v2 is the audited v1 implementation with regularization selected by February-only grouped CV.
# CV candidates C=[0.1,0.25,0.5,1,2,4,10]; primary metric top3 ordered-pair capture, secondary pair AUC.
# Winner frozen before March settlement: C=0.25 (tied best top3=.384978; best AUC among tied candidates).
# Exact base implementation is research/rebuild_3head_opponent_v1.py commit a20b5da985299d0b445110e6783dcaebf0f76a02.
# Deterministic model delta:
# LogisticRegression(C=0.25,class_weight='balanced',solver='liblinear',max_iter=2000,random_state=0)
# All 67 features, preprocessing, training population, top3 selection and tie-break remain identical to v1.
# February GroupKFold(5) results (mean top3 capture, mean pair AUC):
# C=.1  : .3808114035, .6969655019
# C=.25 : .3849780702, .6968272439  <-- frozen v2
# C=.5  : .3849780702, .6966964554
# C=1   : .3849780702, .6965957262
# C=2   : .3849780702, .6965751912
# C=4   : .3849780702, .6965569646
# C=10  : .3849780702, .6965671959
# March diagnostic after freeze: 25/71, return 62830, ROI99.7301587%.
# Ticket SHA256 (two independent executions): 50f71ee9626c43472552549da7a3496719077ac2f5dc8b561c2046687d27271d
# NOTE: this file records the exact deterministic delta from v1; use v1 code with only C changed to 0.25.
