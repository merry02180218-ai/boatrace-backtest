from __future__ import annotations
import json
import sys
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"research"))

from run_3head_funsite_broad50_wave16 import build_pre_enhanced, choose_features

MONTHS=[
 ("2025-10-01","2025-10-31"),
 ("2025-11-01","2025-11-30"),
 ("2025-12-01","2025-12-31"),
 ("2026-01-01","2026-01-31"),
 ("2026-02-01","2026-02-28"),
]

def main():
    frames=[]
    audits={}
    for a,b in MONTHS:
        x,_,audit=build_pre_enhanced(a,b,False)
        if x.empty:
            raise RuntimeError(f"empty frozen feature source {a}..{b}")
        frames.append(x)
        audits[a[:7]]=audit
    all_data=pd.concat(frames,ignore_index=True,sort=False)
    _,enh,new=choose_features(all_data)
    if len(enh)!=370:
        raise RuntimeError(f"frozen feature count drift {len(enh)} != 370")
    out={
      "policy":"3HEAD_A_PRECISION_V1",
      "feature_freeze_period":"2025-10-01..2026-02-28",
      "feature_count":len(enh),
      "features":enh,
      "new_feature_count":len(new),
      "source_audit":audits,
    }
    Path("research/3head_a_frozen_pre_features.json").write_text(
        json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"
    )
    print("3HEAD_A_FROZEN_PRE_FEATURES_OK",len(enh))

if __name__=="__main__":
    main()
