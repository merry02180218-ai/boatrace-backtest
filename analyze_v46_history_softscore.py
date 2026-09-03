"""v46: use prior exhibition history as soft score, never as hard filter.
Source: v43 rows. 4-corner uses prior1 40% + prior2 60%; 3 makuri/MS prior1; 5-head prior2 (60/40 composite from v43).
Train-only quantile normalization and point-size selection; validation primary, last7 reference.
"""
import csv
MODELS=['3まくり','3まくり差し','4カドまくり','5頭展開']
POINTS=[2,4,6,8]

def load():
 with open('analysis_v43_prior2_lane_corrected.csv',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def val(r,m):
 p1=float(r['prior1']);p2=float(r['prior2'])
 if m=='4カドまくり': return .4*p1+.6*p2 if int(r['has2']) else p1
 if m=='5頭展開': return p2 if int(r['has2']) else p1
 return p1
def pct_rank(x,a):
 if not a:return .5
 return sum(v<=x for v in a)/len(a)
def rate(a):return 100*sum(int(x['target']) for x in a)/len(a) if a else 0

def main():
 rows=load(); out=[]; lines=['# v46 過去展示履歴 ソフト加減点検証','','候補は削らない。履歴評価を基準スコア50点に対する±点として使用。履歴percentileはtrainだけで正規化。4カド=前走40%+前々走60%。','','|モデル|採用点幅|train 高評価/低評価|validation 高評価/低評価|8/27-9/2 高評価/低評価|','|---|---:|---:|---:|---:|']
 for m in MODELS:
  rr=[r for r in rows if r['model']==m]; tr=[val(r,m) for r in rr if r['period']=='train']; tr.sort()
  for r in rr:r['hpct']=pct_rank(val(r,m),tr)
  # soft points: centered percentile => [-P,+P]; choose P by train separation, with no selection/filter effect
  best=None
  for P in POINTS:
   for r in rr:r['adj']=P*(2*r['hpct']-1)
   # grade proxy: high >= +P*.4, low <= -P*.4; ranking itself same across P, use shrink toward zero to prefer smaller P on ties
   hi=[r for r in rr if r['period']=='train' and r['adj']>=P*.4];lo=[r for r in rr if r['period']=='train' and r['adj']<=-P*.4]
   sep=rate(hi)-rate(lo)-.05*P
   if best is None or sep>best[0]:best=(sep,P)
  P=best[1]
  def stat(period,last7=False):
   q=[r for r in rr if (r['period']==period and (not last7 or r['date']>='2026-08-27'))]
   for r in q:r['adj']=P*(2*r['hpct']-1)
   hi=[r for r in q if r['adj']>=P*.4];lo=[r for r in q if r['adj']<=-P*.4]
   return len(hi),rate(hi),len(lo),rate(lo)
  a=stat('train');b=stat('validation');c=stat('latest_month',True)
  lines.append(f'|{m}|±{P}点|{a[0]}R/{a[1]:.1f}% vs {a[2]}R/{a[3]:.1f}%|{b[0]}R/{b[1]:.1f}% vs {b[2]}R/{b[3]:.1f}%|{c[0]}R/{c[1]:.1f}% vs {c[2]}R/{c[3]:.1f}%|')
  for r in rr:
   r['history_pct']=round(r['hpct'],4);r['history_adjust']=round(P*(2*r['hpct']-1),3);out.append(r)
 lines+=['','高評価/低評価は履歴percentile上位30%/下位30%相当。候補自体は全件残す。validationで高評価>低評価が再現するモデルだけ加減点採用候補。8/27-9/2は既確認期間なので参考。']
 with open('analysis_v46_history_softscore.csv','w',newline='',encoding='utf-8-sig') as f:
  fs=['date','race_code','model','period','target','prior1','prior2','has2','history_pct','history_adjust'];w=csv.DictWriter(f,fieldnames=fs,extrasaction='ignore');w.writeheader();w.writerows(out)
 open('summary_v46_history_softscore.md','w',encoding='utf-8').write('\n'.join(lines)+'\n')
if __name__=='__main__':main()
