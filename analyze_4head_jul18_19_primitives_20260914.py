from backtest import rows,race_features
from backtest_v4 import resistance12,score4v4
from backtest_v18_core45 import features4
import pandas as pd,json
DATES=['2026/07/18','2026/07/19']
out=[];audit={}
for ymd in DATES:
 c=rows('data/programs/race_cards/'+ymd+'.csv');w=rows('data/programs/waku10/'+ymd+'.csv');wm={z.get('レースコード'):z for z in w};rr=[]
 for r in c:
  q=wm.get(r.get('レースコード'),{});x=race_features(r,q);f=features4(x);z={'date':ymd,'resistance12':resistance12(x),'wall3_weak':f['3壁弱さ'],'past_win4':x[4]['past_win'],'legacy_score4':score4v4(x)}
  for b in range(1,5):
   for k in ['wr','nst','waku_wr','waku_st','waku_sr']:z[f'b{b}_{k}']=x[b][k]
   z[f'b{b}_past10_n']=sum(str(q.get(f'艇{b}_過去{k}走_着順','')).strip().isdigit() for k in range(1,11))
   z[f'b{b}_waku_wr_blank']=int(str(q.get(f'艇{b}_枠番別勝率','')).strip()=='')
   z[f'b{b}_waku_st_blank']=int(str(q.get(f'艇{b}_枠番別平均ST','')).strip()=='')
  rr.append(z);out.append(z)
 A=pd.DataFrame(rr);audit[ymd]={'cards':len(c),'waku10':len(w),'matched':sum(r.get('レースコード') in wm for r in c),'means':A.mean(numeric_only=True).to_dict(),'card_cols':sorted(c[0]) if c else [],'waku_cols':sorted(w[0]) if w else []}
D=pd.DataFrame(out);D.to_csv('analysis_4head_jul18_19_primitives_20260914.csv',index=False)
a,b=audit[DATES[0]],audit[DATES[1]];diff={'card_added':sorted(set(b['card_cols'])-set(a['card_cols'])),'card_removed':sorted(set(a['card_cols'])-set(b['card_cols'])),'waku_added':sorted(set(b['waku_cols'])-set(a['waku_cols'])),'waku_removed':sorted(set(a['waku_cols'])-set(b['waku_cols']))}
J={'outcome_blind':True,'production_modified':False,'days':audit,'schema_diff':diff};open('audit_4head_jul18_19_primitives_20260914.json','w').write(json.dumps(J,ensure_ascii=False,indent=2))
L=['# HEAD4 Jul18-19 primitive audit','',f"schemas card +{len(diff['card_added'])}/-{len(diff['card_removed'])}, waku +{len(diff['waku_added'])}/-{len(diff['waku_removed'])}",'','|metric|7/18|7/19|change|','|---|---:|---:|---:|']
keys=sorted(set(a['means'])&set(b['means']),key=lambda k:abs(b['means'][k]-a['means'][k]),reverse=True)
for k in keys:L.append(f"|{k}|{a['means'][k]:.6f}|{b['means'][k]:.6f}|{b['means'][k]-a['means'][k]:+.6f}|")
open('summary_4head_jul18_19_primitives_20260914.md','w').write('\n'.join(L)+'\n');print('\n'.join(L[:35]))
