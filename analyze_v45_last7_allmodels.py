"""v45: last 7 days (2026-08-27..09-02) all-model test with adopted prior-history rules.
Uses v43 rows; thresholds are trained only on 6/1..7/15.
4-corner history = prior1 40% + prior2 60% (adopted v44).
"""
import csv
D0='2026-08-27';D1='2026-09-02'
MODELS=['3まくり','3まくり差し','4カドまくり','5頭展開']

def load():
 with open('analysis_v43_prior2_lane_corrected.csv',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def rate(a):return 100*sum(int(x['target']) for x in a)/len(a) if a else 0

def val(r,m):
 p1=float(r['prior1']);p2=float(r['prior2'])
 if m=='3まくり':return p1
 if m=='3まくり差し':return p1
 if m=='4カドまくり':return .4*p1+.6*p2
 return p2

def main():
 a=load();cuts={}
 for m in MODELS:
  tr=[r for r in a if r['period']=='train' and r['model']==m and (m not in ('4カドまくり','5頭展開') or int(r['has2']))]
  z=sorted(val(r,m) for r in tr);cuts[m]=z[int(.60*(len(z)-1))] if z else .5
 L=['# v45 過去1週間 全モデルバックテスト','','対象: 2026-08-27〜2026-09-02。候補条件はv43基準。履歴フィルタはtrain上位40% cutoff固定。4カドは前走40%+前々走60%。3まくり/3まくり差しは前走、5頭は前走+前々走60:40。','','|モデル|基準R/成立率|履歴選抜R/成立率|差|','|---|---:|---:|---:|']
 out=[]
 for m in MODELS:
  base=[r for r in a if r['model']==m and D0<=r['date']<=D1]
  elig=[r for r in base if (m not in ('4カドまくり','5頭展開') or int(r['has2']))]
  sel=[r for r in elig if val(r,m)>=cuts[m]]
  L.append(f'|{m}|{len(base)}R/{rate(base):.1f}%|{len(sel)}R/{rate(sel):.1f}%|{rate(sel)-rate(base):+.1f}pt|')
  for r in sel:out.append({'date':r['date'],'race_code':r['race_code'],'model':m,'target':r['target'],'history_score':f'{val(r,m):.4f}','cutoff':f'{cuts[m]:.4f}'})
 # daily detail
 L+=['','## 日別選抜','|日付|選抜R|成立R|成立率|','|---|---:|---:|---:|']
 for d in sorted(set(r['date'] for r in out)):
  q=[r for r in out if r['date']==d];h=sum(int(r['target']) for r in q);L.append(f'|{d}|{len(q)}|{h}|{100*h/len(q) if q else 0:.1f}%|')
 L+=['','注: 8/27〜9/2は既に開発中に確認済みの期間なので、完全な未見holdoutではなく試運転評価。実進入・艇N_コース不使用。']
 open('summary_v45_last7_allmodels.md','w',encoding='utf-8').write('\n'.join(L)+'\n')
 with open('analysis_v45_last7_allmodels.csv','w',newline='',encoding='utf-8-sig') as f:
  w=csv.DictWriter(f,fieldnames=['date','race_code','model','target','history_score','cutoff']);w.writeheader();w.writerows(out)
if __name__=='__main__':main()
