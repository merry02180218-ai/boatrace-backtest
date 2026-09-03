"""v48: fix v47 ROI by joining dedicated payouts CSV (3連単_払戻金)."""
import csv
from backtest import rows
D0='2026-08-20';D1='2026-08-26';MODELS=['3まくり','3まくり差し','4カドまくり','5頭展開']
TARGET={'3まくり':3,'3まくり差し':3,'4カドまくり':4,'5頭展開':5}
def load():
 with open('analysis_v43_prior2_lane_corrected.csv',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def hv(r,m):
 p1=float(r['prior1']);p2=float(r['prior2'])
 if m=='4カドまくり':return .4*p1+.6*p2 if int(r['has2']) else p1
 if m=='5頭展開':return p2 if int(r['has2']) else p1
 return p1
def rate(q):return 100*sum(int(r['target']) for r in q)/len(q) if q else 0
def paynum(x):
 try:return int(float(str(x).replace(',','').replace('円','')))
 except:return 0
def main():
 a=load();trvals={m:sorted(hv(r,m) for r in a if r['model']==m and r['period']=='train') for m in MODELS};test=[r for r in a if D0<=r['date']<=D1]
 resc={};pays={}
 for d in sorted(set(r['date'] for r in test)):
  y,m,dd=d.split('-')
  for z in rows(f'data/results/realtime/{y}/{m}/{dd}.csv'):resc[z.get('レースコード','')]=z
  for z in rows(f'data/results/payouts/{y}/{m}/{dd}.csv'):pays[z.get('レースコード','')]=z
 out=[];L=['# v48 先々週 ソフト履歴モデル + 実払戻ROI','','対象: 2026-08-20〜2026-08-26。候補はv43基準から削らない。履歴はv46方式の±2点。4カドは前走40%+前々走60%。','','3連単は狙い艇1着固定－相手5艇総流し20点、各100円（1R投資2,000円）。払戻は dedicated payouts CSV の `3連単_払戻金` をレースコードで結合。','','|モデル|候補R|狙い決まり手率|頭1着率|履歴高/中/低 R・成立率|総投資|払戻|回収率|払戻欠損|','|---|---:|---:|---:|---|---:|---:|---:|---:|']
 for mod in MODELS:
  q=[r for r in test if r['model']==mod];tv=trvals[mod];inv=ret=miss=0;head=0;bands={'高':[],'中':[],'低':[]}
  for r in q:
   x=hv(r,mod);pct=sum(v<=x for v in tv)/len(tv) if tv else .5;adj=2*(2*pct-1);band='高' if pct>=.7 else ('低' if pct<=.3 else '中');bands[band].append(r)
   rr=resc.get(r['race_code'],{});pr=pays.get(r['race_code'],{});boat=TARGET[mod];inv+=2000
   try:win=int(float(rr.get('1着_艇番',0) or 0))
   except:win=0
   p=paynum(pr.get('3連単_払戻金',''))
   if not pr or not pr.get('3連単_払戻金',''):miss+=1
   if win==boat:head+=1;ret+=p
   out.append({'date':r['date'],'race_code':r['race_code'],'model':mod,'target':r['target'],'history_pct':round(pct,4),'history_adjust':round(adj,3),'band':band,'winner':win,'trifecta_payout':p,'head_hit':int(win==boat),'payout_missing':int(not pr or not pr.get('3連単_払戻金',''))})
  bs=' / '.join(f"{b}{len(bands[b])}R・{rate(bands[b]):.1f}%" for b in ('高','中','低'))
  L.append(f'|{mod}|{len(q)}|{rate(q):.1f}%|{100*head/len(q) if q else 0:.1f}%|{bs}|{inv:,}円|{ret:,}円|{100*ret/inv if inv else 0:.1f}%|{miss}|')
 L+=['','## 注意','- 狙い決まり手率は元のtargetラベル、頭1着率は対象艇が実際に1着だった率。ROIは後者に対応。','- 20点総流しなので対象艇が1着なら実際の3連単払戻が1本分返る。','- 払戻欠損が0でない場合はROIを過小評価する。']
 open('summary_v48_week_before_softscore_roi.md','w',encoding='utf-8').write('\n'.join(L)+'\n')
 with open('analysis_v48_week_before_softscore_roi.csv','w',newline='',encoding='utf-8-sig') as f:
  fs=['date','race_code','model','target','history_pct','history_adjust','band','winner','trifecta_payout','head_hit','payout_missing'];w=csv.DictWriter(f,fieldnames=fs);w.writeheader();w.writerows(out)
if __name__=='__main__':main()
