#!/usr/bin/env python3
import os, json, pandas as pd
from pathlib import Path
import audit_4head_ph5_live_walkforward as a
# Reuse audited replay machinery but extend rolling origin one day into Sep.
# Build PH5 on Mar-Aug truth, score 2026-09-10 only. Decisions are frozen before 9/10 truth join.
orig_range=pd.date_range
def patched_range(start,end,*args,**kwargs):
    if str(end)=="2026-08-31": end="2026-09-10"
    return orig_range(start,end,*args,**kwargs)
a.pd.date_range=patched_range
# This script is intentionally separate from production; production files are unchanged.
# Current audit main is month-bounded, so use a minimally patched source copy at runtime.
p=Path(a.__file__)
s=p.read_text()
s=s.replace('(strict.month>="2026-06")&(strict.month<="2026-08")','(strict.month=="2026-09")')
s=s.replace('rolls=[("2026-06",["2026-03","2026-04","2026-05"]),("2026-07",["2026-03","2026-04","2026-05","2026-06"]),("2026-08",["2026-03","2026-04","2026-05","2026-06","2026-07"])]','rolls=[("2026-09",["2026-03","2026-04","2026-05","2026-06","2026-07","2026-08"])]')
s=s.replace('if not ("202603010000" <= code <= "202608319999"):continue','if not ("202609100000" <= code <= "202609109999"):continue')
s=s.replace('if not ("20260301" <= ds <= "20260831") or rn<1:continue','if ds != "20260910" or rn<1:continue')
s=s.replace('for mon in ("2026-06","2026-07","2026-08"):', 'for mon in ("2026-09",):')
s=s.replace('for ds in pd.date_range("2026-03-01","2026-08-31"):', 'for ds in pd.date_range("2026-09-10","2026-09-10"):')
s=s.replace('for ds in pd.date_range("2025-11-01","2026-08-31"):', 'for ds in pd.date_range("2025-11-01","2026-09-09"):')
s=s.replace('if d.startswith("2026-08"):', 'if d=="2026-09-10":')
s=s.replace('strict=strict[(strict.month=="2026-09")&strict.struct_ready.astype(str).str.lower().isin(["true","1"])].copy()', 'strict=strict[(strict.month=="2026-09")&strict.race_code.astype(str).str.startswith("20260910")&strict.struct_ready.astype(str).str.lower().isin(["true","1"])].copy()')
s=s.replace('print("HEAD4_PH5_LIVE_WALKFORWARD_OK")','print("HEAD4_20260910_LIVE_REPLAY_OK")')
Path('/tmp/replay.py').write_text(s)
exec(compile(s,'/tmp/replay.py','exec'),{'__name__':'__main__','__file__':'/tmp/replay.py'})
