"""v122: learn LIVE skip gates for the frozen two-stage PRE-top5 operation.
Discovery Mar-May only; evaluate frozen simple gates on clean Jun-Aug.
No odds. PRE top5 is fixed before LIVE. Outcomes are never used to select a race within its month.
"""
import csv
from collections import defaultdict
SRC='analysis_v121_1head_six_month_top5.csv'; OUT='summary_v122_1head_live_skip_filters.md'
def f(x):
 try:return float(x)
 except:return 0.0
def i(x):
 try:return int(float(x))
 except:return 0
def pct(a,b):return 100*a/b if b else 0
def metric(rs):
 q=[r for r in rs if i(r['live_buy'])==1]
 n=len(q); h=sum(i(r['head_hit']) for r in q); hit=[r for r in q if 0<i(r['rank_l50'])<=7]
 inv=n*700; ret=sum(i(r['payout100']) for r in hit)
 return n,pct(h,n),pct(len(hit),n),pct(ret,inv)
def main():
 with open(SRC,encoding='utf-8-sig',newline='') as z:rs=list(csv.DictReader(z))
 dev=[r for r in rs if r['month'] in ('2026-03','2026-04','2026-05')]
 hold=[r for r in rs if r['month'] in ('2026-06','2026-07','2026-08')]
 # simple LIVE p109 gates only; thresholds predeclared, choose on dev by ROI with min 2.5 buys/day and >=70% of max dev ROI tie favors lower cut.
 cuts=[.72,.74,.76,.78,.80,.82,.84,.86]
 def filt(z,c):return [r for r in z if i(r['live_buy'])==1 and f(r['p109_live'])>=c]
 days_dev=len(set(r['date'] for r in dev)); days_hold=len(set(r['date'] for r in hold))
 tab=[]
 for c in cuts:
  m=metric(filt(dev,c)); tab.append((c,m,m[0]/days_dev))
 eligible=[x for x in tab if x[2]>=2.5]
 chosen=max(eligible,key=lambda x:(x[1][3],-x[0]))[0] if eligible else .72
 baseD=metric(dev);baseH=metric(hold);chD=metric(filt(dev,chosen));chH=metric(filt(hold,chosen))
 L=['# v122 LIVE skip-filter validation','',
 '- Frozen operation: PRE top5/day from v121, then LIVE BUY gate inside that list only.','- Discovery/tuning: Mar-May. Clean evaluation: Jun-Aug.','- No odds; no post-race variable is used by the gate.','- Candidate gate family is deliberately simple: LIVE p109 minimum only.','',
 '## Mar-May discovery','|LIVE p109 min|BUY R/day|R|①頭率|7点的中率|7点ROI|','|---:|---:|---:|---:|---:|---:|']
 for c,m,rpd in tab:L.append(f'|{c*100:.0f}%|{rpd:.2f}|{m[0]}|{m[1]:.1f}%|{m[2]:.1f}%|{m[3]:.1f}%|')
 L+=['',f'- Frozen selected gate from development block: **p109 >= {chosen*100:.0f}%** (requires dev BUY >=2.5R/day).','',
 '## Clean Jun-Aug holdout','|rule|BUY R/day|R|①頭率|7点的中率|7点ROI|','|---|---:|---:|---:|---:|---:|',
 f'|v121 baseline p109>=72%|{baseH[0]/days_hold:.2f}|{baseH[0]}|{baseH[1]:.1f}%|{baseH[2]:.1f}%|{baseH[3]:.1f}%|',
 f'|v122 frozen p109>={chosen*100:.0f}%|{chH[0]/days_hold:.2f}|{chH[0]}|{chH[1]:.1f}%|{chH[2]:.1f}%|{chH[3]:.1f}%|','',
 '## Guardrail','- Do not adopt a stricter LIVE cut merely because it improves Mar-May. Adoption requires Jun-Aug improvement without collapsing race count, then prospective Sep confirmation.','- This v122 intentionally does not mine many exhibition subfeatures yet; first test whether the existing calibrated LIVE probability alone supplies a robust skip gate.']
 open(OUT,'w',encoding='utf-8').write('\n'.join(L)+'\n')
if __name__=='__main__':main()
