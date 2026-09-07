"""2026-09-08 1-head PRE priority scan using the current v116/v109 implementation.
Date wrapper only; no model architecture/cut changes.
Neutral-pre is priority only, never formal A/S or BUY/SKIP.
"""
from datetime import date
import predict_v116_20260905_1head_live as m

m.HD=date(2026,9,8)
m.HD8='20260908'
m.TRAIN_END='2026-08-31'
m.OUT='prediction_v116_20260908_1head_pre.csv'
m.SUMMARY='summary_v116_20260908_1head_pre.md'

if __name__=='__main__':
    m.main()
