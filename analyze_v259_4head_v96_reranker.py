#!/usr/bin/env python3
"""v259: conservative reranker on top of the proven v96 4-head opponent ranking.

Idea: keep v96 role scores as the dominant prior, then learn only a small residual ordered-pair
correction from prior boat-4 wins. This tests whether topology/history can improve ordering without
replacing v96 as v258 did.
Primary evidence: Feb-Jun only. Jul/Aug excluded. Research/model-selection only.
"""
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
import analyze_v96_4corner_monthly_walkforward_tiebreak as c4
import analyze_v221_3head_scenario_pair as v221
import analyze_v251_4head_newroi_bridge as v251
from analyze_v205_3head_operational_replay import load_odds
ROOT=Path(__file__).resolve().parent; BANK=10000; BOATS=(1,2,3,5,6); MONTHS=[f'2026-{m:02d}' for m in range(2,7)]
PRED=ROOT/'analysis_v250_4head_rebuild_baseline.csv'; OUT=ROOT/'analysis_v259_4head_v96_reranker.csv'; SUM=ROOT/'summary_v259_4head_v96_reranker.md'
GATES=((.28,.25,'GATE_123R'),(.25,.25,'GATE_156R')); TOPS=(2,3,5,10); ALPHAS=(0.0,.05,.10,.15,.20,.30,.40)
def ff(x,d=0.):
 try:
  y=float(x); return y if np.isfinite(y) else d
 except:return d
def ii(x,d=0):
 try:return int(float(x))
 except:return d
def zmap(v):
 a=np.array(list(v.values()),float); sd=a.std()
 return {k:0. if sd<1e-9 else (x-a.mean())/sd for k,x in v.items()}
def old_role(r,w2,w3,mu,sd): return c4.role_scores(r,w2,w3,mu,sd)
def residual_vec(r,s,t):
 # Small residual feature set only; v96 remains the main signal.
 raw=lambda b:[ff(x,.5) for x in c4.rawfeat(r,b)]
 xs,xt,h=raw(s),raw(t),raw(4); x=[]
 x += [a-b for a,b in zip(xs,xt)]+[a-b for a,b in zip(xs,h)]+[a-b for a,b in zip(xt,h)]
 hist=['vh_p12_display','vh_p12_turn','vh_p12_straight','pl_all_p2','pl_frame_p2','pl_recent_p2']
 for k in hist:
  a=ff(r.get(f'b{s}_{k}'),.5 if 'vh_' in k else 0);b=ff(r.get(f'b{t}_{k}'),.5 if 'vh_' in k else 0);hh=ff(r.get(f'b4_{k}'),.5 if 'vh_' in k else 0)
  x += [a-b,a-hh,b-hh]
 x += [float(s<4),float(t<4),float(s>4),float(t>4),float(s==3),float(t==3),float(s==5),float(t==5),float(s<t),abs(s-t)/5]
 return x
def valid4(r): return ii(r.get('valid_result'))==1 and ii(r.get('winner'))==4 and ii(r.get('second')) in BOATS and ii(r.get('third')) in BOATS and ii(r.get('second'))!=ii(r.get('third'))
def fit_resid(tr):
 X=[];y=[];nr=0
 for _,r in tr.iterrows():
  if not valid4(r):continue
  nr+=1;s0,t0=ii(r.get('second')),ii(r.get('third'))
  for s in BOATS:
   for t in BOATS:
    if s!=t:X.append(residual_vec(r,s,t));y.append(int((s,t)==(s0,t0)))
 if nr<40:raise RuntimeError(f'train too small {nr}')
 m=Pipeline([('sc',StandardScaler()),('lr',LogisticRegression(C=.15,max_iter=1500,solver='lbfgs'))]);m.fit(X,y);return m,nr
def order(r,w2,w3,mu,sd,m,alpha):
 s2,s3=old_role(r,w2,w3,mu,sd); pairs=[]; rp={}
 for s in BOATS:
  for t in BOATS:
   if s==t:continue
   # v96 pair score is dominant baseline.
   base=s2[s]+s3[t]; p=float(m.predict_proba([residual_vec(r,s,t)])[0,1]); rp[(s,t)]=np.log(max(p,1e-8))
 zb=zmap({k:(s2[k[0]]+s3[k[1]]) for k in rp}); zr=zmap(rp)
 return sorted(rp,key=lambda k:(-(zb[k]+alpha*zr[k]),k[0],k[1]))
def settle(ordr,n,o,a):return v251.settle('',[f'4-{s}-{t}' for s,t in ordr[:n]],o,a)
def var10(ordr,o,a):
 z=[]
 for n in range(2,21):
  q=settle(ordr,n,o,a)
  if q is not None:z.append((n,*q))
 return min(z,key=lambda q:(abs(q[3]-10),q[0])) if z else None
def main():
 rs=c4.read();d=pd.DataFrame(rs);d['race_code']=d.race_code.astype(str).str.zfill(12);d['_date']=pd.to_datetime(d.date);d=d[d._date<pd.Timestamp('2026-07-01')].copy();d=v221.build(d,'date')
 pred=pd.read_csv(PRED,dtype={'race_code':str});pred.race_code=pred.race_code.str.zfill(12);pw=pred.pivot_table(index=['date','month','race_code'],columns='variant',values='p4head',aggfunc='last').reset_index();d['date']=d.date.astype(str);pw['date']=pw.date.astype(str);d=d.merge(pw[['date','race_code','PRE','POST']],on=['date','race_code'],how='left')
 od=load_odds();oi=od.set_index('race_code',drop=False); rows=[]
 for mon in MONTHS:
  first=pd.Timestamp(mon+'-01'); tr=d[d._date<first]; te=d[d._date.dt.strftime('%Y-%m')==mon]
  trlist=tr.to_dict('records'); htr=[r for r in trlist if c4.eligible(r) and ii(r.get('winner'))==4 and ii(r.get('second')) in BOATS and ii(r.get('third')) in BOATS]
  mu,sd=c4.scalers(htr);w2=c4.fit(htr,'second',mu,sd);w3=c4.fit(htr,'third',mu,sd);m,ntrain=fit_resid(tr)
  for _,r in te.iterrows():
   if ii(r.get('valid_result'))!=1:continue
   code=str(r.race_code).zfill(12)
   if code not in oi.index:continue
   o=oi.loc[code];o=o.iloc[-1] if isinstance(o,pd.DataFrame) else o;a=(ii(r.get('winner')),ii(r.get('second')),ii(r.get('third')),1)
   rec={'month':mon,'race_code':code,'PRE':ff(r.get('PRE'),-9),'POST':ff(r.get('POST'),-9),'head4':int(a[0]==4),'train':ntrain}
   for al in ALPHAS:
    oo=order(r,w2,w3,mu,sd,m,al);tag=f'a{int(al*100):02d}'
    if a[0]==4:
     try:rec[tag+'_rank']=oo.index((a[1],a[2]))+1
     except:rec[tag+'_rank']=0
    for n in TOPS:
     q=settle(oo,n,o,a)
     if q is not None:rec[tag+f'_hit{n}'],rec[tag+f'_ret{n}'],rec[tag+f'_comp{n}']=q
    q=var10(oo,o,a)
    if q is not None:rec[tag+'_vn'],rec[tag+'_vhit'],rec[tag+'_vret'],rec[tag+'_vcomp']=q
   rows.append(rec)
 z=pd.DataFrame(rows);z.to_csv(OUT,index=False);L=['# v259 4-head conservative v96 reranker','', '- v96 role scores remain dominant; learned ordered-pair residual is blended with alpha 0..0.40.','- strict monthly prior-only; primary Feb-Jun; Jul/Aug excluded.','- exact 10,000 yen Dutch; historical odds settlement-only.','- research/model-selection evidence only.','']
 for pc,qc,name in GATES:
  q=z[(z.PRE>=pc)&(z.POST>=qc)];h=q[q.head4==1];L += [f'## {name} PRE>={pc:.2f} POST>={qc:.2f}',f'- R={len(q)}, head4={len(h)}','', '|alpha|Top2 cov|Top5 cov|Top10 cov|var10 R|avg N|hit|ROI|','|---:|---:|---:|---:|---:|---:|---:|---:|']
  for al in ALPHAS:
   tag=f'a{int(al*100):02d}';cov=lambda n:100*((h[tag+'_rank']>0)&(h[tag+'_rank']<=n)).mean() if len(h) else 0;qq=q[q[tag+'_vn'].notna()]
   L.append(f'|{al:.2f}|{cov(2):.2f}%|{cov(5):.2f}%|{cov(10):.2f}%|{len(qq)}|{qq[tag+"_vn"].mean():.2f}|{100*qq[tag+"_vhit"].mean():.2f}%|{100*qq[tag+"_vret"].sum()/(len(qq)*BANK):.2f}%|')
  L += ['','### Fixed Top2 ROI','|alpha|hit|ROI|','|---:|---:|---:|']
  for al in ALPHAS:
   tag=f'a{int(al*100):02d}';L.append(f'|{al:.2f}|{100*q[tag+"_hit2"].mean():.2f}%|{100*q[tag+"_ret2"].sum()/(len(q)*BANK):.2f}%|')
  L.append('')
 SUM.write_text('\n'.join(L)+'\n',encoding='utf-8');print('\n'.join(L))
if __name__=='__main__':main()
