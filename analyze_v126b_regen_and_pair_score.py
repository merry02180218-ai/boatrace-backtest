"""v126b: regenerate frozen v110 pair orders for Mar-Aug, tune pair rescoring on Mar-May, evaluate once on Jun-Aug.
No Sep outcomes; no odds in ranking. v109 head gate unchanged.
"""
import csv
from analyze_v110b_1head_role_tickets import read_csv,prepare_month
SRC='analysis_v108_1head_feasibility.csv'; HEAD='analysis_v109_1head_monthly_walkforward.csv'
DEV=['2026-03','2026-04','2026-05']; TEST=['2026-06','2026-07','2026-08']; OUT='summary_v126b_1head_pair_score.md'
ALPHAS=[0,.15,.30,.45,.60,.75,1.0]
def ff(x,d=0):
 try:return float(x)
 except:return d
def ii(x,d=0):
 try:return int(float(x))
 except:return d
def rm(r):
 a=[int(x) for x in (r.get('ranked_others') or '').split('-') if x];return {b:i+1 for i,b in enumerate(a)}
def base_order(r):return [x for x in (r.get('order_l50') or '').split(';') if x]
def rescored(r,a):
 o=base_order(r);m=rm(r);z=[]
 for j,c in enumerate(o):
  _,s,t=map(int,c.split('-')); v=.70*(-(j+1))+.30*(-(m.get(s,5)+a*m.get(t,5)));z.append((v,c))
 return [c for _,c in sorted(z,key=lambda x:(-x[0],x[1]))]
def metric(rs,a):
 q=[r for r in rs if ff(r.get('p109'))>=.72 and ii(r.get('valid_payout'))==1];hit=head=ret=0
 for r in q:
  act=(r.get('actual_combo') or '').strip(); head+=ii(r.get('head_hit'))==1
  if act in rescored(r,a)[:7]:hit+=1;ret+=ii(r.get('payout100'))
 return len(q),100*hit/len(q) if q else 0,100*hit/head if head else 0,100*ret/(len(q)*700) if q else 0
def main():
 src=read_csv(SRC); hp={(r.get('date'),r.get('race_code')):r.get('p109','') for r in read_csv(HEAD)}
 # prepare_month is frozen v110 role logic; p109 is attached only for selection/metrics, not pair ranking.
 by={}
 for mo in DEV+TEST:
  print('regen',mo,flush=True);by[mo]=prepare_month(src,mo)
  for r in by[mo]:r['p109']=hp.get((r.get('date'),r.get('race_code')),'')
 dev=sum((by[m] for m in DEV),[]);test=sum((by[m] for m in TEST),[])
 rows=[]
 for a in ALPHAS:rows.append((a,metric(dev,a)))
 # choose by dev coverage, then hit rate, then ROI, then simpler/lower alpha.
 best=max(rows,key=lambda x:(x[1][2],x[1][1],x[1][3],-x[0]))[0]
 b=metric(test,0);v=metric(test,best)
 L=['# v126b clean pair-score validation','', '- Frozen v110 pair orders regenerated chronologically for Mar-Aug.','- Tune only on Mar-May; Jun-Aug evaluated once after alpha freeze.','- v109 p109>=72 gate unchanged; no Sep outcomes used; no odds used in pair ranking.','', '## Mar-May development','|alpha|R|7hit|coverage|ROI|','|---:|---:|---:|---:|---:|']
 for a,m in rows:L.append(f'|{a:.2f}|{m[0]}|{m[1]:.1f}%|{m[2]:.1f}%|{m[3]:.1f}%|')
 L += ['',f'Frozen alpha = **{best:.2f}**','', '## Jun-Aug untouched holdout','|rule|R|7hit|coverage|ROI|','|---|---:|---:|---:|---:|',f'|v110 baseline|{b[0]}|{b[1]:.1f}%|{b[2]:.1f}%|{b[3]:.1f}%|',f'|v126b|{v[0]}|{v[1]:.1f}%|{v[2]:.1f}%|{v[3]:.1f}%|']
 passed=v[2]>b[2] and v[1]>=b[1] and v[3]>=b[3]
 L += ['',f'- **V126B PAIR SCORE = {"PASS" if passed else "FAIL"}**', '- PASS requires holdout coverage improvement with no hit-rate or ROI deterioration.']
 open(OUT,'w',encoding='utf-8').write('\n'.join(L)+'\n')
if __name__=='__main__':main()
