"""2026-09-09 1-head PRE scan using the current v116/v109 production implementation.
This is a date wrapper only; no model architecture/cut changes.
"""
from datetime import date
import predict_v116_20260905_1head_live as m

m.HD=date(2026,9,9)
m.HD8='20260909'
m.TRAIN_END='2026-08-31'
m.OUT='prediction_v116_20260909_1head_pre.csv'
m.SUMMARY='summary_v116_20260909_1head_pre.md'

if __name__=='__main__':
    m.main()
