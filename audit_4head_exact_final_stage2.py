#!/usr/bin/env python3
"""Coverage-first exact LIVE final replay Stage2.
Consumes all-parent exhibition artifact. Quantifies V93/headprob/official-closing
coverage before any profitability claim. Sep blocked; production unchanged.
"""
from __future__ import annotations
from pathlib import Path
import json,os
import pandas as pd
import audit_4head_86r_v283_closing_odds as oddsmod
OUT=Path("/tmp/head4_exact_final_stage2");OUT.mkdir(exist_ok=True)
def main():
 p=os.environ["PARENT_EXHIBITION"]; z=pd.read_csv(p,dtype={"race_code":str});z["race_code"]=z.race_code.astype(str).str.zfill(12)
 if z.date.astype(str).str.startswith("2026-09").any():raise RuntimeError("SEPTEMBER ACCESS")
 structural=z[z.newfeature_struct.astype(str).str.lower().isin(("true","1"))].copy()
 codes=set(structural.race_code)
 d=oddsmod.source_rows(codes,"2026-04-01","2026-08-31"); v93=set(d.race_code.astype(str).str.zfill(12))
 hp=pd.read_csv(os.environ["HEADPROB_SCORED"],dtype={"race_code":str}); hp["race_code"]=hp.race_code.astype(str).str.zfill(12); hpc=set(hp.race_code)
 odds_cache={}; oddsc=set()
 for ds,g in structural.groupby(structural.date.astype(str).str[:10]):
  oq=odds_cache.setdefault(ds,oddsmod.odds_for_date(ds))
  if len(oq):oddsc.update(set(oq.race_code.astype(str))&set(g.race_code))
 full=codes&v93&hpc&oddsc
 structural["v93_covered"]=structural.race_code.isin(v93);structural["headprob_covered"]=structural.race_code.isin(hpc);structural["odds_covered"]=structural.race_code.isin(oddsc);structural["fully_replayable"]=structural.race_code.isin(full)
 bym={}
 for m,g in structural.assign(month=structural.date.astype(str).str[:7]).groupby("month"):
  bym[m]={"structural_R":len(g),"v93_R":int(g.v93_covered.sum()),"headprob_R":int(g.headprob_covered.sum()),"odds_R":int(g.odds_covered.sum()),"full_R":int(g.fully_replayable.sum())}
 out={"parent_R":int(len(z)),"newfeature_struct_R":int(len(structural)),"v93_covered_R":len(codes&v93),"headprob_covered_R":len(codes&hpc),"official_closing_odds_covered_R":len(codes&oddsc),"fully_replayable_R":len(full),"fully_replayable_rate":len(full)/len(codes) if codes else 0,"by_month":bym,"SEPTEMBER_OUTCOMES_READ":False,"PRODUCTION_CHANGED":False}
 structural.to_csv(OUT/"coverage_rows.csv",index=False);(OUT/"result.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
 print(json.dumps(out,ensure_ascii=False,indent=2));print("HEAD4_EXACT_FINAL_STAGE2_COVERAGE_OK");print("SEPTEMBER_UNREAD")
if __name__=="__main__":main()
