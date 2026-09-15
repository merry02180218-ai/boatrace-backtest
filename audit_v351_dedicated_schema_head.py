#!/usr/bin/env python3
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

SRC='analysis_v351_schema_correct_rebuild.csv'
BASE=['one_ex','one_st','sec_ex_mean_margin','sec_st_mean_margin']
GROUPS={
 'half':['one_half','sec_half_mean_margin','third_half_mean_margin','covered_half_weak_margin','uncovered_half_dominance'],
 'lap':['one_lap','sec_lap_mean_margin','third_lap_mean_margin','covered_lap_weak_margin','uncovered_lap_dominance'],
 'turn':['one_turn','sec_turn_mean_margin','third_turn_mean_margin','covered_turn_weak_margin','uncovered_turn_dominance'],
 'straight':['one_straight','sec_straight_mean_margin','third_straight_mean_margin','covered_straight_weak_margin','uncovered_straight_dominance'],
}
SCHEMAS=['lap+turn','half+turn+straight','turn+straight','base','lap+turn+straight']
MIN_TRAIN_GRID=[5,8,10,12,15,20,25,30]
C_GRID=[.03,.08,.15,.3,.7,1.5]

def feats(schema):
    ts=[] if schema=='base' else schema.split('+')
    return BASE+sum((GROUPS[t] for t in ts),[])

def oof(g,fs,min_train,C):
    g=g.sort_values('race_code').copy(); g['dedicated_p']=np.nan
    idx=list(g.index)
    for pos,i in enumerate(idx):
        if not g.loc[i,'schema_ready']: continue
        tr=g.loc[idx[:pos]]; tr=tr[tr.schema_ready.eq(1)].dropna(subset=fs+['head_hit'])
        if len(tr)<min_train or tr.head_hit.nunique()<2: continue
        m=Pipeline([('sc',StandardScaler()),('lr',LogisticRegression(C=C,max_iter=2000,class_weight=None))])
        m.fit(tr[fs],tr.head_hit.astype(int)); g.loc[i,'dedicated_p']=m.predict_proba(g.loc[[i],fs])[:,1][0]
    return g

def stats(z,cut):
    q=z[z.dedicated_p.notna() & (z.dedicated_p>=cut)]
    return len(q), int(q.head_hit.sum()), 100*q.head_hit.mean() if len(q) else np.nan, int(q.hit.sum()),100*q.hit.mean() if len(q) else np.nan

def main():
    d=pd.read_csv(SRC,dtype={'race_code':str}); d.race_code=d.race_code.str.zfill(12)
    d=d[d.race_code.str[:8]<'20260901'].copy()
    allrows=[]; best=[]
    for schema in SCHEMAS:
        g=d[(d.schema==schema)&d.schema_ready.eq(1)].copy(); fs=feats(schema)
        if not len(g): continue
        candidates=[]
        for mt in MIN_TRAIN_GRID:
          for C in C_GRID:
            z=oof(g,fs,mt,C); scored=z[z.dedicated_p.notna()]
            for cut in np.round(np.arange(.50,.951,.01),2):
              n,h,hr,e,er=stats(z,cut)
              candidates.append({'schema':schema,'min_train':mt,'C':C,'cut':cut,'ready':len(g),'oof':len(scored),'n':n,'head':h,'head_rate':hr,'exact3':e,'exact3_rate':er})
        c=pd.DataFrame(candidates); allrows.append(c)
        viable=c[(c.n>=10)&(c.head_rate>=78)].sort_values(['n','exact3_rate','head_rate'],ascending=[False,False,False])
        if len(viable): b=viable.iloc[0]
        else:
          viable=c[c.n>=5].sort_values(['head_rate','n','exact3_rate'],ascending=[False,False,False])
          b=viable.iloc[0] if len(viable) else c.sort_values(['oof','head_rate'],ascending=[False,False]).iloc[0]
        best.append(b.to_dict())
        print('BEST',schema,'READY',int(b['ready']),'OOF',int(b['oof']),'MIN_TRAIN',int(b['min_train']),'C',b['C'],'CUT',b['cut'],'R',int(b['n']),'HEAD',int(b['head']),'HEAD_RATE',b['head_rate'],'EXACT3',int(b['exact3']),'EXACT3_RATE',b['exact3_rate'])
        z=oof(g,fs,int(b['min_train']),float(b['C'])); q=z[z.dedicated_p.notna() & (z.dedicated_p>=float(b['cut']))]
        for j,x in q.groupby('jcd'):
          print('HOLDOUT',schema,'JCD',int(j),'R',len(x),'HEAD',int(x.head_hit.sum()),'HEAD_RATE',100*x.head_hit.mean() if len(x) else np.nan,'EXACT3',int(x.hit.sum()))
        z.to_csv('analysis_v351_dedicated_'+schema.replace('+','_')+'.csv',index=False,encoding='utf-8-sig')
    pd.concat(allrows,ignore_index=True).to_csv('analysis_v351_dedicated_schema_sweep.csv',index=False,encoding='utf-8-sig')
    pd.DataFrame(best).to_csv('analysis_v351_dedicated_schema_best.csv',index=False,encoding='utf-8-sig')
if __name__=='__main__': main()
