"""v47: 2026-08-20..08-26 soft-score backtest + simple trifecta ROI.
Candidates stay unchanged. History soft score: 4-corner p1:p2=40:60; 3 makuri p1; 3MS p1; 5-head p2 composite.
ROI ticket rule is fixed BEFORE reading results: target boat first, 2nd/3rd = all permutations of other 5 boats (20 trifecta tickets/race), 100 yen each.
This deliberately measures head-model monetization without result-dependent ticket selection.
"""
import csv,io
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
def find_pay(rr):
 # support common boatracecsv column variants; payout is per 100 yen
 for k,v in rr.items():
  kk=(k or '').replace(' ','').replace('　','')
  if ('3連単' in kk or '三連単' in kk) and ('払戻' in kk or '配当' in kk or '払戻金' in kk):
   try:return int(float(str(v).replace(',','').replace('円','')))
   except:pass
 return 0
def main():
 a=load(); trvals={m:sorted(hv(r,m) for r in a if r['model']==m and r['period']=='train') for m in MODELS}
 test=[r for r in a if D0<=r['date']<=D1]
 # cache results only after candidate/history scores are fixed
 resc={}
 for d in sorted(set(r['date'] for r in test)):
  y,m,dd=d.split('-');res=rows(f'data/results/realtime/{y}/{m}/{dd}.csv')
  for z in res:resc[z.get('レースコード','')]=z
 out=[];L=['# v47 先々週 ソフト履歴モデル + 回収率','','対象: 2026-08-20〜2026-08-26。候補はv43基準から削らない。履歴はv46方式の±2点。4カドは前走40%+前々走60%。','','回収率は結果を見る前に固定した単純ルール: **狙い艇1着固定－相手5艇総流し（2・3着全順列20点）**、各100円。1R投資2,000円。これにより「頭モデル自体」の回収性を比較する。','','|モデル|候補R|狙い決まり手率|履歴高/中/低 R・成立率|総投資|払戻|回収率|','|---|---:|---:|---|---:|---:|---:|']
 for mod in MODELS:
  q=[r for r in test if r['model']==mod];tv=trvals[mod]
  inv=ret=0; bands={'高':[],'中':[],'低':[]}
  for r in q:
   x=hv(r,mod);pct=sum(v<=x for v in tv)/len(tv) if tv else .5;adj=2*(2*pct-1)
   band='高' if pct>=.7 else ('低' if pct<=.3 else '中');bands[band].append(r)
   rr=resc.get(r['race_code'],{});pay=find_pay(rr);boat=TARGET[mod]
   # 20 tickets cover every trifecta with target boat first; if target wins, exactly one ticket hits.
   inv+=2000
   try:win=int(float(rr.get('1着_艇番',0) or 0))
   except:win=0
   if win==boat:ret+=pay
   out.append({'date':r['date'],'race_code':r['race_code'],'model':mod,'target':r['target'],'history_pct':round(pct,4),'history_adjust':round(adj,3),'band':band,'trifecta_payout':pay,'head_hit':int(win==boat)})
  bs=' / '.join(f"{b}{len(bands[b])}R・{rate(bands[b]):.1f}%" for b in ('高','中','低'))
  L.append(f'|{mod}|{len(q)}|{rate(q):.1f}%|{bs}|{inv:,}円|{ret:,}円|{100*ret/inv if inv else 0:.1f}%|')
 L+=['','## 注意','- 回収率は「狙い決まり手だけ」ではなく、対象艇が1着なら20点総流しのどれかが的中する設計。決まり手成立率とは別指標。','- 払戻列が取得できないレースは払戻0としてCSVに残るため、結果確認時に欠損数も確認する。','- 実進入・艇N_コースは不使用。']
 open('summary_v47_week_before_softscore_roi.md','w',encoding='utf-8').write('\n'.join(L)+'\n')
 with open('analysis_v47_week_before_softscore_roi.csv','w',newline='',encoding='utf-8-sig') as f:
  fs=['date','race_code','model','target','history_pct','history_adjust','band','trifecta_payout','head_hit'];w=csv.DictWriter(f,fieldnames=fs);w.writeheader();w.writerows(out)
if __name__=='__main__':main()
