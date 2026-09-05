"""v120 exploratory diagnostics on frozen v118 replay.
Goal: user wants roughly 5 buy races/day. Do NOT change production rules here.
1) diagnose S head-hit but fixed7 miss.
2) compare fixed pre-result daily ranking rules and top-N=3/5/7/10.
No outcome is used in ranking.
"""
import csv
from collections import defaultdict,Counter
SRC='replay_v118_20260901_04_1head.csv'; OUT='summary_v120_1head_top5_and_misses.md'
def rows():
 with open(SRC,encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def F(r,k):return float(r[k])
def I(r,k):return int(float(r[k]))
def pct(a,b):return 100*a/b if b else 0
def metrics(z):
 n=len(z); h=sum(I(r,'head_hit') for r in z); t=sum(I(r,'ticket7_hit') for r in z); inv=sum(I(r,'invest7') for r in z); ret=sum(I(r,'return7') for r in z)
 return n,h,pct(h,n),t,pct(t,n),inv,ret,pct(ret,inv)
def rank_p75(z): return sorted(z,key=lambda r:(abs(F(r,'p109')-.775),-F(r,'p109'),r['race_code']))
def rank_p(z): return sorted(z,key=lambda r:(-F(r,'p109'),r['race_code']))
def main():
 rs=rows(); S=[r for r in rs if F(r,'p109')>=.72]; days=sorted(set(r['date'] for r in S))
 miss=[r for r in S if I(r,'head_hit')==1 and I(r,'ticket7_hit')==0]
 pos2=Counter();pos3=Counter(); outside=Counter()
 for r in miss:
  a=r['actual_combo'].split('-'); tickets=[x.split('-') for x in r['top7'].split(';')]
  secs={x[1] for x in tickets}; thirds={x[2] for x in tickets}
  s2=a[1] in secs; s3=a[2] in thirds
  pos2['in' if s2 else 'out']+=1; pos3['in' if s3 else 'out']+=1
  outside[('2nd_out' if not s2 else '')+('+' if (not s2 and not s3) else '')+('3rd_out' if not s3 else '') or 'both_roles_present']+=1
 L=['# v120 1-head: fixed7 miss diagnostics + ~5 races/day exploration','',
 '- Source is frozen v118 Sep-01..04 replay. No result is used to rank/select races.',
 '- This is exploratory only; production v109/v110 rules are unchanged.', '',
 '## S head-hit but fixed7 miss diagnostics',f'- S races: **{len(S)}**; head hits: **{sum(I(r,"head_hit") for r in S)}**; head-hit/fixed7-miss: **{len(miss)}**.',
 f'- Actual 2nd boat appears somewhere in fixed7 second-position set: **{pos2["in"]}/{len(miss)} ({pct(pos2["in"],len(miss)):.1f}%)**.',
 f'- Actual 3rd boat appears somewhere in fixed7 third-position set: **{pos3["in"]}/{len(miss)} ({pct(pos3["in"],len(miss)):.1f}%)**.',
 '- Miss decomposition: '+', '.join(f'{k}={v}' for k,v in outside.items())+'.','',
 '## Daily top-N selection (pre-result fixed ranking rules)','',
 'Rule P75-center = among S, rank closest to p109=77.5% (motivated only as a fixed diagnostic rule, not production).',
 'Rule P-high = among S, rank highest p109.','',
 '|rule|N/day|R|①頭率|7点的中率|投資|払戻|ROI|','|---|---:|---:|---:|---:|---:|---:|---:|']
 for name,fn in [('P75-center',rank_p75),('P-high',rank_p)]:
  for N in [3,5,7,10]:
   z=[]
   for d in days:z+=fn([r for r in S if r['date']==d])[:N]
   n,h,hr,t,tr,inv,ret,roi=metrics(z);L.append(f'|{name}|{N}|{n}|{hr:.1f}%|{tr:.1f}%|¥{inv:,}|¥{ret:,}|{roi:.1f}%|')
 L+=['','## Top-5/day details','|date|rule|selected R|①頭率|7点的中率|ROI|','|---|---|---|---:|---:|---:|']
 for d in days:
  day=[r for r in S if r['date']==d]
  for name,fn in [('P75-center',rank_p75),('P-high',rank_p)]:
   z=fn(day)[:5]; n,h,hr,t,tr,inv,ret,roi=metrics(z); sel=', '.join(f"{r['venue_name']}{int(r['race'])}R({F(r,'p109')*100:.1f}%)" for r in z)
   L.append(f'|{d}|{name}|{sel}|{hr:.1f}%|{tr:.1f}%|{roi:.1f}%|')
 open(OUT,'w',encoding='utf-8').write('\n'.join(L)+'\n')
if __name__=='__main__':main()
