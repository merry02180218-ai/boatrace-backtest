from backtest_v20_week import *
from datetime import date
import csv
D=date(2026,9,3)
def main():
 cache={};hist=defaultdict(list);seen=set();d=PRELOAD_START
 while d<TRAIN_START:
  ingest_motor(hist,seen,d)
  if d>=TRAIN_START-timedelta(days=12): ingest_prior_day_preview(cache,d)
  d+=timedelta(days=1)
 train={m:[] for m in RULES};pairs={m:defaultdict(int) for m in RULES}
 d=TRAIN_START
 while d<=TRAIN_END:
  feats=process_features(d,cache,hist);ymd=d.strftime('%Y/%m/%d');res={r['レースコード']:r for r in rows(f'data/results/realtime/{ymd}.csv')};pay={r['レースコード']:r for r in rows(f'data/results/payouts/{ymd}.csv')}
  for r,x,s4,s5,dc in feats:
   s3=score3v4(x)
   for m in RULES:
    sc=score_for(x,s3,s4,m);y=target(res.get(r['レースコード'],{}),m);train[m].append((sc,y))
    if y:
     k=pair_key((pay.get(r['レースコード'],{}).get('3連単_組番') or '').strip())
     if k:pairs[m][k]+=1
  ingest_prior_day_preview(cache,d);ingest_motor(hist,seen,d);d+=timedelta(days=1)
 while d<D:
  process_features(d,cache,hist);ingest_prior_day_preview(cache,d);ingest_motor(hist,seen,d);d+=timedelta(days=1)
 feats=process_features(D,cache,hist);ymd=D.strftime('%Y/%m/%d');ods={r['レースコード']:r for r in rows(f'data/previews/od3/{ymd}.csv')};out=[]
 for r,x,s4,s5,dc in feats:
  s3=score3v4(x)
  for m,rule in RULES.items():
   fr=features(x,s3,s4,dc,m)
   if not passes(fr,rule):continue
   sc=score_for(x,s3,s4,m);p=cal_prob(train[m],sc);chosen=select_set(HEAD[m],p,ods.get(r['レースコード'],{}),pairs[m])
   if not chosen:continue
   rr={'model':m,'date':str(D),'race_code':r['レースコード'],'venue':r.get('レース場コード',''),'race':r.get('レース回',''),'score':round(sc,2),'prob':round(p,4),'tickets':len(chosen),'composite_odds':round(composite(chosen),2)};rr.update({k:round(fr[k],3) for k in rule});out.append(rr)
 with open('pred_v25_20260903_pre.csv','w',newline='',encoding='utf-8-sig') as f:
  w=csv.DictWriter(f,fieldnames=sorted(set().union(*(r.keys() for r in out))));w.writeheader();w.writerows(out)
 L=['# v25 2026-09-03 事前候補（展示前）','','v20固定条件で全場全R走査。実進入・当日展示は未使用。ここから展示後にv23補正でS/A/B判定する。','','|モデル|場|R|基礎score|推定確率|買い目数|合成オッズ|特徴|','|---|---:|---:|---:|---:|---:|---:|---|']
 for r in sorted(out,key=lambda z:(z['model'],z['venue'],int(str(z['race']).replace('R','') or 0))):
  feat=', '.join(f'{k}={r[k]}' for k in RULES[r['model']]);L.append(f"|{r['model']}|{r['venue']}|{r['race']}|{r['score']}|{r['prob']:.1%}|{r['tickets']}|{r['composite_odds']}|{feat}|")
 L+=['',f'候補数: {len(out)}R']
 open('prediction_v25_20260903_pre.md','w',encoding='utf-8').write('\n'.join(L)+'\n')
if __name__=='__main__':main()
