#!/usr/bin/env python3
"""Convert a model-owned watchlist into a unified PRE feed without changing selection."""
import argparse,json
from pathlib import Path
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--model",required=True);ap.add_argument("--input",required=True);ap.add_argument("--out",required=True);a=ap.parse_args()
 z=json.loads(Path(a.input).read_text(encoding="utf-8")); model=a.model.upper(); ts=[]
 for raw in z.get("targets",[]):
  t=dict(raw);t["model"]=model;t.setdefault("adapter",model.lower());t.setdefault("pre_class",t.get("operational_class") or t.get("pre_reason") or "")
  t.setdefault("model_payload",{"head_prob":t.get("head_prob"),"pre_reason":t.get("pre_reason"),"operational_class":t.get("operational_class")})
  ts.append(t)
 out={"schema":"unified-head-pre-feed-v1","date":str(z["date"]).replace("-",""),"model":model,
      "source_profile":z.get("profile"),"target_day_results_used":False,"payouts_used":False,"targets":ts}
 Path(a.out).parent.mkdir(parents=True,exist_ok=True);Path(a.out).write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print("UNIFIED_HEAD_PRE_FEED_OK",model,len(ts))
if __name__=="__main__":main()
