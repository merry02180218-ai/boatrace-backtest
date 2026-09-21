#!/usr/bin/env python3
"""March 2026 one-shot settlement evaluator for frozen Artifact 10621281342.
Predictions are embedded from the audited dry-run artifact before March outcome reveal.
Do not recompute predictions or tune any rule here.
"""
import csv,json,sys
from datetime import date,timedelta
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import analyze_v221_3head_scenario_pair as v221

ARTIFACT_ID=10621281342
EXPECTED_N=33
EXPECTED_SWAPS=18
THRESHOLD=.50
PRED=Path(__file__).with_name('frozen_3head_mar_predictions_10621281342.json')

def main():
 frozen=json.loads(PRED.read_text(encoding='utf-8'))
 dec=frozen['decisions']
 if frozen.get('artifact_id')!=ARTIFACT_ID or len(dec)!=EXPECTED_N: raise RuntimeError('frozen prediction identity/count mismatch')
 if frozen.get('threshold')!=THRESHOLD: raise RuntimeError('threshold mismatch')
 if sum(v.get('promoted') is not None for v in dec.values())!=EXPECTED_SWAPS: raise RuntimeError('swap count mismatch')
 for code,v in dec.items():
  if len(v['base'])!=6 or len(set(v['base']))!=6 or len(v['protected'])!=6 or len(set(v['protected']))!=6: raise RuntimeError(f'six-ticket invariant failed {code}')
 print('FROZEN_PREDICTIONS_VERIFIED',{'artifact_id':ARTIFACT_ID,'n':len(dec),'swaps':EXPECTED_SWAPS,'threshold':THRESHOLD},flush=True)

 settled={}; day=date(2026,3,1)
 while day<=date(2026,3,31):
  for r in v221.rows(f"data/results/realtime/{day.strftime('%Y/%m/%d')}.csv"):
   code=str(r.get('レースコード','')).zfill(12)
   a=[str(r.get(f'{i}着_艇番','')).strip() for i in (1,2,3)]
   if code in dec and all(x in '123456' and len(x)==1 for x in a): settled[code]='-'.join(a)
  day+=timedelta(days=1)
 head=bh=ph=rescue=lost=0; rows=[]
 for code,v in dec.items():
  actual=settled.get(code)
  if not actual or not actual.startswith('3-'): continue
  head+=1; b=actual in v['base']; p=actual in v['protected']
  bh+=int(b); ph+=int(p); rescue+=int((not b) and p); lost+=int(b and not p)
  rows.append({'race_code':code,'actual':actual,'base_hit':b,'protected_hit':p,'turn4':v.get('turn4'),'promoted':v.get('promoted'),'dropped':v.get('dropped')})
 out={'policy':{'source_artifact_id':ARTIFACT_ID,'predictions_recomputed':False,'threshold_tuned_on_march':False,'threshold':THRESHOLD,'tickets':6,'sep2026_loaded':False},
      'march':{'selected_races':len(dec),'settled_races':len(settled),'boat3_wins':head,'base_hits':bh,'protected_hits':ph,'base_capture':bh/head if head else None,'protected_capture':ph/head if head else None,'rescued':rescue,'lost':lost,'net':ph-bh},'rows':rows}
 Path('research_3head_a_opponent_mar_oneshot.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
 with open('research_3head_a_opponent_mar_oneshot.csv','w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=['race_code','actual','base_hit','protected_hit','turn4','promoted','dropped']); w.writeheader(); w.writerows(rows)
 print(json.dumps(out,ensure_ascii=False,indent=2),flush=True)
if __name__=='__main__': main()
