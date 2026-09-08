#!/usr/bin/env python3
"""v211: SHADOW rescue layer on top of v210 8% PRE.
June train -> July choose rescue rule -> frozen August replay.
Rescue uses only PRE-safe component probabilities from v207 models.
Production remains v191 until prospective evidence.
"""
from pathlib import Path
import numpy as np, pandas as pd
import analyze_v207_3head_enhanced_pre as v207
import analyze_v191_3head_clean_pre_restore_june as restore
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'analysis_v211_3head_pre_rescue.csv'; SUM=ROOT/'summary_v211_3head_pre_rescue.md'
BASE_CUT=.301497
TARGET_MAX=.105

def main():
    hist,miss,cover,missing=restore.hist_rows(); h=pd.DataFrame(hist);h['_code']=h.race_code.map(v207.norm_code)
    att=pd.read_csv(v207.ATT);att['_code']=att.race_code.map(v207.norm_code)
    h=h.merge(att[['_code']+v207.TACTICS+v207.PRIOR_EX],on='_code',how='inner',validate='one_to_one')
    for c in v207.TACTICS+v207.PRIOR_EX:h[c]=pd.to_numeric(h[c],errors='coerce').fillna(.5)
    h['venue']=h['venue'].astype(str);tr=h[h.month=='2026-06'].copy();ju=h[h.month=='2026-07'].copy();au=h[h.month=='2026-08'].copy()
    names=list(v207.SETS); models={n:v207.fit_model(tr,v207.SETS[n]) for n in names}
    def score(d):return {n:v207.probs(models[n],d,v207.SETS[n]) for n in names}
    pj,pa=score(ju),score(au)
    bj=.6*pj['base+prior_ex']+.4*pj['base'];ba=.6*pa['base+prior_ex']+.4*pa['base']
    basej=bj>=BASE_CUT;basea=ba>=BASE_CUT
    # Rescue rules are selected on July only. They add races missed by base 8%.
    cand=[]
    for n in names:
      for q in (.90,.92,.94,.95,.96,.97,.98,.99):
        cut=float(np.quantile(pj[n],q,method='higher'));sj=basej|(pj[n]>=cut);y=ju.label.to_numpy(int)
        rate=sj.mean();rec=((sj)&(y==1)).sum()/max(1,(y==1).sum());add=int((sj&~basej).sum())
        if rate<=TARGET_MAX:cand.append((rec,-rate,-add,n,cut))
    # OR of two high-confidence components, still constrained by July workload.
    for a in names:
      for b in names:
        if names.index(b)<=names.index(a):continue
        for q in (.94,.96,.98):
          ca=float(np.quantile(pj[a],q,method='higher'));cb=float(np.quantile(pj[b],q,method='higher'))
          sj=basej|(pj[a]>=ca)|(pj[b]>=cb);y=ju.label.to_numpy(int);rate=sj.mean();rec=(sj&(y==1)).sum()/max(1,(y==1).sum())
          if rate<=TARGET_MAX:cand.append((rec,-rate,-int((sj&~basej).sum()),a+' OR '+b,(ca,cb)))
    best=max(cand,key=lambda x:(x[0],x[1],x[2])); rule=best[3];cut=best[4]
    def apply(d,p,base):
      if ' OR ' in rule:
        a,b=rule.split(' OR ');return base|(p[a]>=cut[0])|(p[b]>=cut[1])
      return base|(p[rule]>=cut)
    sj=apply(ju,pj,basej);sa=apply(au,pa,basea)
    rows=[]
    for split,d,s,b in [('tune_july',ju,sj,basej),('shadow_aug',au,sa,basea)]:
      y=d.label.to_numpy(int);rows.append({'split':split,'rule':rule,'cut':str(cut),'R':len(d),'watch':int(s.sum()),'watch_rate':s.mean(),'formal':int(y.sum()),'recall':(s&(y==1)).sum()/max(1,y.sum()),'base_watch':int(b.sum()),'base_recall':(b&(y==1)).sum()/max(1,y.sum()),'added':int((s&~b).sum()),'rescued_formal':int(((s&~b)&(y==1)).sum())})
    pd.DataFrame(rows).to_csv(OUT,index=False)
    L=['# v211 3-head PRE rescue — SHADOW','',f'- base: v210 8% prior_plus_base raw cut {BASE_CUT:.6f}',f'- rescue chosen on July only, max July watch {TARGET_MAX*100:.1f}%',f'- selected rescue: **{rule}**, cut={cut}','', '|split|watch|rate|formal recall|base recall|added|rescued formal|','|---|---:|---:|---:|---:|---:|---:|']
    for z in rows:L.append(f"|{z['split']}|{z['watch']}|{z['watch_rate']*100:.1f}%|{z['recall']*100:.1f}%|{z['base_recall']*100:.1f}%|{z['added']}|{z['rescued_formal']}|")
    L+=['','- August is shadow replay already inspected; not pristine adoption evidence.','- Production unchanged.']
    SUM.write_text('\n'.join(L)+'\n',encoding='utf-8');print('\n'.join(L))
if __name__=='__main__':main()
