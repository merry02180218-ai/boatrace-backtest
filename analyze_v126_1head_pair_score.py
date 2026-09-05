"""v126: improve v110 pair/order scoring only.
Frozen head model/gate. Tune pair-score formula on Mar-May, evaluate once on Jun-Aug.
No odds. Sep outcomes are not used.
"""
import csv
DEV={'2026-03','2026-04','2026-05'}
TEST={'2026-06','2026-07','2026-08'}
SRC='analysis_v110_1head_role_tickets.csv'
OUT='summary_v126_1head_pair_score.md'

def read(p):
 with open(p,encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def F(r,k,d=0):
 try:return float(r.get(k,d))
 except:return d
def I(r,k,d=0):
 try:return int(float(r.get(k,d)))
 except:return d
def order(r,col):return [x for x in (r.get(col,'') or '').split(';') if x]
def rankmap(r):
 a=[int(x) for x in (r.get('ranked_others','') or '').split('-') if x]
 return {b:i+1 for i,b in enumerate(a)}
def candidate_orders(r):
 # Re-score the frozen v110 full 20-order using only order_l50 and prior/current threat ranks.
 base=order(r,'order_l50')
 if not base:return {}
 rm=rankmap(r)
 out={}
 # alpha controls how much to favor balanced second/third rank vs original v110 order.
 for alpha in [0,.15,.30,.45,.60,.75,1.0]:
  vals=[]
  for j,c in enumerate(base):
   a=c.split('-');s=int(a[1]);t=int(a[2])
   br=-(rm.get(s,5)+alpha*rm.get(t,5))
   # preserve v110 information via normalized original rank score
   vr=-(j+1)
   vals.append((.70*vr+.30*br,c))
  out[alpha]=[c for _,c in sorted(vals,key=lambda x:(-x[0],x[1]))]
 return out
def metric(rs,alpha,n=7):
 q=[r for r in rs if F(r,'p109')>=.72 and I(r,'valid_payout')==1]
 h=0;head=0;ret=0
 for r in q:
  act=(r.get('actual_combo') or '').strip();o=candidate_orders(r).get(alpha,[])[:n]
  if I(r,'head_hit')==1:head+=1
  if act in o:h+=1;ret+=I(r,'payout100')
 inv=len(q)*n*100
 return len(q),h,head,(100*h/len(q) if q else 0),(100*h/head if head else 0),(100*ret/inv if inv else 0)
def main():
 rs=read(SRC)
 # v110 output contains Jun-Aug only in current implementation; never fake Mar-May tuning.
 months={r.get('month') for r in rs}
 dev=[r for r in rs if r.get('month') in DEV];test=[r for r in rs if r.get('month') in TEST]
 L=['# v126 v110 pair-score validation','', '- v109/head gate frozen at p109>=72%.','- Changes pair/order construction only; no odds and no Sep outcomes.','']
 if not dev:
  L += ['## STOP: development block unavailable',f'- Source months present: **{", ".join(sorted(x for x in months if x))}**.', '- `analysis_v110_1head_role_tickets.csv` is Jun-Aug holdout output only, so Mar-May candidate orders are not available.', '- Therefore v126 must not tune on Jun-Aug and call that a holdout result.', '- Next action: regenerate Mar-May v110 pair-order rows from the frozen v110b code, then tune pair scoring on Mar-May and evaluate once on Jun-Aug.']
  open(OUT,'w',encoding='utf-8').write('\n'.join(L)+'\n');return
 # Only reachable after source is extended with true Mar-May rows.
 scores=[]
 for a in [0,.15,.30,.45,.60,.75,1.0]:
  m=metric(dev,a);scores.append((m[4],m[5],-a,a,m))
 best=max(scores)[3]
 L += ['## Mar-May tuning','|alpha|R|7hit|coverage|ROI|','|---:|---:|---:|---:|---:|']
 for _,_,_,a,m in scores:L.append(f'|{a:.2f}|{m[0]}|{m[3]:.1f}%|{m[4]:.1f}%|{m[5]:.1f}%|')
 b=metric(test,0);v=metric(test,best)
 L += ['',f'Frozen alpha = **{best:.2f}**','', '## Jun-Aug untouched holdout', '|rule|R|7hit|coverage|ROI|','|---|---:|---:|---:|---:|', f'|baseline v110|{b[0]}|{b[3]:.1f}%|{b[4]:.1f}%|{b[5]:.1f}%|',f'|v126|{v[0]}|{v[3]:.1f}%|{v[4]:.1f}%|{v[5]:.1f}%|']
 open(OUT,'w',encoding='utf-8').write('\n'.join(L)+'\n')
if __name__=='__main__':main()
