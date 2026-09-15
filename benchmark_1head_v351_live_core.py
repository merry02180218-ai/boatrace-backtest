#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,math,time,statistics
import onehead_production_profile as prod
import run_v299_1head_trifecta3_policy_search as v299
BOATS=(2,3,4,5,6)

def norm(q):
 s=sum(max(float(v),0.0) for v in q.values());return {k:max(float(v),0.0)/s for k,v in q.items()}
def score(p2,pc,core):
 a2=norm({b:float(p2[b])*math.exp(float(prod.OPPONENT_CORE_SECOND_G2)*(float(core[b])-.5)) for b in BOATS})
 a3={}
 for s in BOATS:
  q=norm({t:float(pc[(s,t)])*math.exp(float(prod.OPPONENT_CORE_THIRD_G3)*(float(core[t])-.5)) for t in BOATS if t!=s})
  for t,v in q.items():a3[(s,t)]=v
 pair=v299.pair_prob(a2,a3,prod.TICKET_ALPHA);top=v299.STRATEGIES['HYBRID'](a2,a3,pair)[:3]
 return ['1-%d-%d'%x for x in top]
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--n',type=int,default=20000);a=ap.parse_args()
 p2={b:1/5 for b in BOATS};pc={(s,t):1/4 for s in BOATS for t in BOATS if t!=s};core={2:.42,3:.61,4:.55,5:.47,6:.66}
 score(p2,pc,core);xs=[]
 for _ in range(a.n):
  t=time.perf_counter_ns();score(p2,pc,core);xs.append((time.perf_counter_ns()-t)/1e6)
 xs.sort();o={'n':a.n,'mean_ms':statistics.fmean(xs),'median_ms':statistics.median(xs),'p95_ms':xs[int(.95*(len(xs)-1))],'max_ms':max(xs),'tickets':score(p2,pc,core),'g2':prod.OPPONENT_CORE_SECOND_G2,'g3':prod.OPPONENT_CORE_THIRD_G3,'alpha':prod.TICKET_ALPHA}
 print(json.dumps(o,indent=2))
if __name__=='__main__':main()
