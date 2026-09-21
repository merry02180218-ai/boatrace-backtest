#!/usr/bin/env python3
"""Forensic leakage audit for 4HEAD BASE. No model tuning; September blocked."""
import ast,json,re
from pathlib import Path
FILES=["build_4head_clean_long_dataset.py","rebuild_4head_v93_all_parent.py","analyze_4head_exhibition_original_trainonly.py","backtest.py","backtest_v51_lane_corrected_tickets.py","audit_4head_waku10_rel43_regime_v6.py"]
BAD=("data/results","winner","head4","payout","odds","finish","着順","1着","2着","3着")
report=[]
for fn in FILES:
 p=Path(fn); t=p.read_text(encoding="utf-8")
 ast.parse(t)
 hits=[]
 for i,line in enumerate(t.splitlines(),1):
  if any(x.lower() in line.lower() for x in BAD): hits.append({"line":i,"text":line.strip()[:240]})
 report.append({"file":fn,"hits":hits,"literal_escaped_newline":"\\\\n" in t})
# Explicit causal invariants in the two chronological builders.
clean=Path("build_4head_clean_long_dataset.py").read_text()
reb=Path("rebuild_4head_v93_all_parent.py").read_text()
checks={
 "clean_sep_block":'if END>=date(2026,9,1): raise RuntimeError("SEPTEMBER_BLOCKED")' in clean,
 "clean_feature_freeze_before_truth":clean.find("feature_cols=list(z.columns)")<clean.find("z=z.merge(tr"),
 "clean_daily_features_before_result_map":clean.find("frozen.append")<clean.find('rmap={rc(r.get("レースコード"'),
 "reb_day_rows_before_result_ingest":reb.find("rec.append(row)")<reb.find('rm={rc(r.get("レースコード"'),
 "reb_comment_prior_only":'ingest target day\'s result only after all target-day rows frozen' in reb,
}
if not all(checks.values()): raise RuntimeError("CAUSAL_INVARIANT_FAILED "+json.dumps(checks))
# Flag every result reference in feature-generating dependencies for manual classification.
out={"checks":checks,"files":report,"SEPTEMBER_OUTCOMES_READ":False,"PRODUCTION_CHANGED":False}
Path("/tmp/head4_leak_forensic_v7").mkdir(exist_ok=True)
Path("/tmp/head4_leak_forensic_v7/report.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
print(json.dumps(out,ensure_ascii=False,indent=2));print("HEAD4_LEAK_FORENSIC_V7_OK");print("SEPTEMBER_UNREAD")
