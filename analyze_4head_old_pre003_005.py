#!/usr/bin/env python3
from collections import defaultdict
from datetime import date,timedelta
from pathlib import Path
import json,pandas as pd
from backtest_v3 import ingest_motor
from backtest_v4 import ingest_prior_day_preview
from backtest_v5_ev import process_features
from analyze_v250_4head_rebuild_baseline import pre_features,post_features,make_model
from analyze_v23_20260902_daypreview import by_code
from backtest import rows,i
ROOT=Path(__file__).resolve().parent;START=date(2025,12,1);END=date(2026,6,30);PRELOAD=START-timedelta(days=120)
MONTHS=[f'2026-{m:02d}' for m in range(2,7)];LO=.03;HI=.05
OUT=ROOT/'analysis_4head_old_pre003_005.csv';AUD=ROOT/'audit_4head_old_pre003_005.json';SUM=ROOT/'summary_4head_old_pre003_005.md'
def main():
 cache={};hist=defaultdict(list);seen=set();d=PRELOAD
 while d<START:
  ingest_motor(hist,seen,d)
  if d>=START-timedelta(days=12):ingest_prior_day_preview(cache,d)
  d+=timedelta(days=1)
 data=[]
 while d<=END:
  feats=process_features(d,cache,hist);ymd=d.strftime('%Y/%m/%d');tkz=by_code(f'data/previews/tkz/{ymd}.csv');stt=by_code(f'data/previews/stt/{ymd}.csv');orig=by_code(f'data/previews/original_exhibition/{ymd}.csv');f=[]
  for r,x,s4,s5,dc in feats:
   z={'date':str(d),'race_code':r['レースコード']};z.update(pre_features(x,s4));z.update(post_features(z['race_code'],tkz,stt,orig));f.append(z)
  rm={r['レースコード']:r for r in rows(f'data/results/realtime/{ymd}.csv')}
  for z in f:z['y4head']=int(i(rm.get(z['race_code'],{}).get('1着_艇番'))==4);data.append(z)
  ingest_prior_day_preview(cache,d);ingest_motor(hist,seen,d);d+=timedelta(days=1)
 df=pd.DataFrame(data);df['_date']=pd.to_datetime(df.date);pre=['legacy_score4','racer4','hist_st_edge_4v3','wall3_weak','inner12_resistance','motor4_2ren','motor4_hist','turnfoot4_prior','past_win4'];post=pre+['ex_st_rank4','ex_st_4','ex_st_edge_4v3','orig_straight4','orig_lap4','orig_turn4','tilt4'];out=[]
 for mon in MONTHS:
  m=pd.Timestamp(mon+'-01');e=m+pd.offsets.MonthBegin(1);tr=df[df._date<m];te=df[(df._date>=m)&(df._date<e)].copy()
  if len(tr)<500 or len(te)<50:continue
  a=make_model(pre);b=make_model(post);a.fit(tr[pre],tr.y4head);b.fit(tr[post],tr.y4head);te['PRE']=a.predict_proba(te[pre])[:,1];te['POST']=b.predict_proba(te[post])[:,1];te['month']=mon;out.append(te[te.PRE.between(LO,HI,inclusive='both')][['date','race_code','month','PRE','POST','y4head']])
 O=pd.concat(out,ignore_index=True);O.to_csv(OUT,index=False);monthly=[]
 for mon,g in O.groupby('month'):monthly.append({'month':mon,'R':len(g),'wins':int(g.y4head.sum()),'rate':float(g.y4head.mean()),'post_ge_018':int((g.POST>=.18).sum()),'post_ge_025':int((g.POST>=.25).sum())})
 audit={'status':'COMPLETE','contract':'MONTHLY_WALK_FORWARD_PREVIOUS_MONTHS_ONLY','period':'2026-02..2026-06','band':[LO,HI],'target_result_join_after_feature_freeze':True,'months':monthly,'total_R':len(O),'total_wins':int(O.y4head.sum()),'total_rate':float(O.y4head.mean()),'roi':'NOT_COMPUTED_NO_ARCHIVED_2026_02_06_CLOSING_ODDS_IN_VERIFIED_REPO_PATH'};AUD.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n')
 L=['# HEAD4 older PRE 0.03-0.05','', '|month|R|wins|rate|POST>=.18|POST>=.25|','|---|---:|---:|---:|---:|---:|']+[f"|{x['month']}|{x['R']}|{x['wins']}|{100*x['rate']:.2f}%|{x['post_ge_018']}|{x['post_ge_025']}|" for x in monthly]+['',f"Total **{len(O)}R / {int(O.y4head.sum())} wins / {100*O.y4head.mean():.2f}%**",'','ROI not computed: user permits closing/deadline odds for historical backtest, but verified repo archive currently has no 2026-02..06 closing-odds files; no fabrication.'];SUM.write_text('\n'.join(L)+'\n');print(SUM.read_text())
if __name__=='__main__':main()
