from __future__ import annotations
import argparse, json
from collections import defaultdict
from datetime import date,timedelta
from pathlib import Path
from statistics import mean
import numpy as np, pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from backtest import rows
from backtest_v51_lane_corrected_tickets import corrected_direct, ff, norm_metric

CANDS=[1,2,4,5,6]
STATIC=['全国平均ST','全国勝率','全国2連対率','全国3連対率','当地勝率','当地2連対率','モーター2連対率','モーター3連対率','ボート2連対率']
EX={202602071007,202602120606,202602150404,202602161108,202602171607,202602171911,202602191910,202602270507,202603031807,202603080101,202603081308,202603101810,202603111810,202603122004,202603141405,202603200809,202603211406,202603241009,202603271906,202603281904}

def bycode(rs): return {str(r.get('レースコード','')).zfill(12):r for r in rs if r.get('レースコード')}
def combo(x):
 s=''.join(c for c in str(x) if c.isdigit()); return tuple(map(int,s[:3])) if len(s)>=3 else None
def st_bias(sums,allv):
 g=mean(allv) if allv else .15
 return {b:(mean(sums[b])-g if sums[b] else 0.) for b in range(1,7)}
def update_st(rs,sums,allv):
 for r in rs:
  for b in range(1,7):
   v=ff(r.get(f'艇{b}_スタート展示'))
   if v is not None and -.30<v<1.: sums[b].append(v); allv.append(v)
def orig_all6(r,target):
 if not r:return False
 for k in range(1,5):
  if norm_metric(r.get(f'計測項目{k}',''))==target and all(ff(r.get(f'艇{b}_値{k}')) is not None for b in range(1,7)):return True
 return False

def load_direct(codes):
 wanted=set(codes); days=sorted({date(int(c[:4]),int(c[4:6]),int(c[6:8])) for c in wanted}); out={}; sums=defaultdict(list);allv=[]
 d=date(2025,10,1); last=max(days); dayset=set(days)
 while d<=last:
  ymd=d.strftime('%Y/%m/%d'); sr=rows(f'data/previews/stt/{ymd}.csv'); bias=st_bias(sums,allv)
  if d in dayset:
   tk=bycode(rows(f'data/previews/tkz/{ymd}.csv')); st=bycode(sr); og=bycode(rows(f'data/previews/original_exhibition/{ymd}.csv'))
   for code in [c for c in wanted if c.startswith(d.strftime('%Y%m%d'))]:
    tr=tk.get(code,{}); ss=st.get(code,{}); oo=og.get(code,{})
    common=bool(tr and ss and all(ff(tr.get(f'艇{b}_展示タイム')) is not None for b in range(1,7)) and all(ff(ss.get(f'艇{b}_スタート展示')) is not None for b in range(1,7)))
    ex,stsc,os=corrected_direct(code,tk,st,og,bias)
    turn=orig_all6(oo,'回り足') or orig_all6(oo,'まわり足'); straight=orig_all6(oo,'直線'); lap=orig_all6(oo,'一周')
    avg=all(os.get(b,{}).get('avg') is not None for b in range(1,7))
    out[code]={'common':common,'ex':ex,'st':stsc,'os':os,'turn':turn,'straight':straight,'lap':lap,'avg':avg}
  update_st(sr,sums,allv); d+=timedelta(days=1)
 return out

def pair_rows(races,direct,variant,venue_ok):
 rr=[]
 for _,r in races.iterrows():
  code=str(int(r.rc)).zfill(12); actual=combo(r.settle__actual_combo); di=direct[code]; jcd=code[8:10]
  for a in CANDS:
   for b in CANDS:
    if a==b:continue
    z={'race_code':code,'second':a,'third':b,'y':int(actual==(3,a,b))}
    for lane in CANDS:z[f'slane{lane}']=int(a==lane);z[f'tlane{lane}']=int(b==lane)
    for m in STATIC:
     va=pd.to_numeric(r[f'card__艇{a}_{m}'],errors='coerce');vb=pd.to_numeric(r[f'card__艇{b}_{m}'],errors='coerce');v3=pd.to_numeric(r[f'card__艇3_{m}'],errors='coerce')
     for n,v in [('s',va),('t',vb),('sg3',va-v3),('tg3',vb-v3),('smt',va-vb),('pm',(va+vb)/2)]:z[f'{n}_{m}']=v
    z['same_side']=int((a in [1,2])==(b in [1,2]));z['second_inner']=int(a in [1,2]);z['third_inner']=int(b in [1,2])
    if variant in ('B','C'):
     for m in ['ex','st']:
      q=di[m];z[f's_{m}']=q[a];z[f't_{m}']=q[b];z[f'sg3_{m}']=q[a]-q[3];z[f'tg3_{m}']=q[b]-q[3];z[f'smt_{m}']=q[a]-q[b];z[f'head3_{m}']=q[3]
    if variant=='C':
     for m in ['turn','straight','lap','avg']:
      if venue_ok.get(jcd,{}).get(m,False) and di[m]:
       q={x:di['os'][x][m] for x in range(1,7)}
       z[f's_{m}']=q[a];z[f't_{m}']=q[b];z[f'sg3_{m}']=q[a]-q[3];z[f'tg3_{m}']=q[b]-q[3];z[f'smt_{m}']=q[a]-q[b];z[f'head3_{m}']=q[3]
    rr.append(z)
 return pd.DataFrame(rr)

def cvscore(x):
 feats=[c for c in x if c not in ['race_code','second','third','y']]; oof=np.full(len(x),np.nan); fold=[]
 for tr,va in GroupKFold(5).split(x,groups=x.race_code):
  m=make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),LogisticRegression(C=.25,class_weight='balanced',solver='liblinear',max_iter=2000,random_state=0));m.fit(x.iloc[tr][feats],x.iloc[tr].y);p=m.predict_proba(x.iloc[va][feats])[:,1];oof[va]=p
  v=x.iloc[va].copy();v['p']=p;top=v.sort_values(['race_code','p','second','third'],ascending=[True,False,True,True]).groupby('race_code').head(3); nr=v.race_code.nunique(); fold.append(sum(g.y.eq(1).any() for _,g in top.groupby('race_code'))/nr)
 v=x.copy();v['p']=oof;top=v.sort_values(['race_code','p','second','third'],ascending=[True,False,True,True]).groupby('race_code').head(3); nr=v.race_code.nunique(); hits=sum(g.y.eq(1).any() for _,g in top.groupby('race_code'))
 return {'features':len(feats),'oof_hits':int(hits),'oof_races':int(nr),'capture':float(hits/nr),'auc':float(roc_auc_score(v.y,v.p)),'fold_capture':fold,'fold_capture_sd':float(np.std(fold))}

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--source',default='analysis_v289_3head_wave21_allrace_feature_settled.csv');ap.add_argument('--phase',choices=['feb'],default='feb');a=ap.parse_args()
 use=['date','race_code_norm','settle__actual_combo','settle__winner','settle__usable','closing_odds__ok']+[f'card__艇{i}_{m}' for i in range(1,7) for m in STATIC]
 df=pd.read_csv(a.source,usecols=use,low_memory=False);df.date=pd.to_datetime(df.date);df['rc']=pd.to_numeric(df.race_code_norm,errors='coerce').astype('Int64');df=df[(df.settle__usable==1)&(df.closing_odds__ok==1)&(~df.rc.isin(EX))].copy()
 feb_all=df[(df.date>='2026-02-01')&(df.date<'2026-03-01')].copy(); assert len(feb_all)==3970, len(feb_all)
 feb_heads=feb_all[feb_all.settle__winner==3].copy(); assert len(feb_heads)==478, len(feb_heads)
 codes=[str(int(x)).zfill(12) for x in feb_all.rc.dropna()]; direct=load_direct(codes)
 venue_ok={}
 for jcd in sorted({c[8:10] for c in codes}):
  cs=[c for c in codes if c[8:10]==jcd and c in direct]
  venue_ok[jcd]={m:(sum(bool(direct[c].get(m,False)) for c in cs)/len(cs)>=.8 if cs else False) for m in ['turn','straight','lap','avg']}
 common_heads=feb_heads[feb_heads.rc.map(lambda x: direct.get(str(int(x)).zfill(12),{}).get('common',False))].copy()
 assert len(common_heads)>0
 res={}
 for v in 'ABC':
  x=pair_rows(common_heads,direct,v,venue_ok);res[v]={'pair_rows':len(x),'races':x.race_code.nunique(),**cvscore(x)}
 assert len({res[v]['races'] for v in res})==1
 winner=max(res,key=lambda k:(res[k]['capture'],res[k]['auc']))
 out={'phase':'FEB_ONLY_FREEZE_CORRECTED','canonical_feb_eligible':len(feb_all),'canonical_feb_heads':len(feb_heads),'common_ready_head_races':len(common_heads),'results':res,'frozen_winner':winner,'venue_ok':venue_ok,'exact_v288_exclusion_preserved':True,'september_outcomes_read':False,'production_changed':False}
 Path('research_v289_3head_exhibition_v5_feb.json').write_text(json.dumps(out,ensure_ascii=False,indent=2));print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
