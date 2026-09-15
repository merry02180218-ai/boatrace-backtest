import pandas as pd, numpy as np, json, hashlib, sys
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.linear_model import LogisticRegression

SRC='analysis_v289_3head_wave21_allrace_feature_settled.csv'
EX={202602071007,202602120606,202602150404,202602161108,202602171607,202602171911,202602191910,202602270507,202603031807,202603080101,202603081308,202603101810,202603111810,202603122004,202603141405,202603200809,202603211406,202603241009,202603271906,202603281904}
metrics=['全国平均ST','全国勝率','全国2連対率','全国3連対率','当地勝率','当地2連対率','モーター2連対率','モーター3連対率','ボート2連対率']
use=['date','race_code_norm','settle__actual_combo','settle__winner','settle__head3_actual','settle__trifecta_payout_100_yen','settle__usable','closing_odds__ok']+[f'card__艇{i}_{m}' for i in range(1,7) for m in metrics]
df=pd.read_csv(SRC,usecols=use,low_memory=False)
df['date']=pd.to_datetime(df.date); df['rc']=pd.to_numeric(df.race_code_norm,errors='coerce').astype('Int64')
df=df[(df.settle__usable==1)&(df.closing_odds__ok==1)&(~df.rc.isin(EX))].copy()
F=[]
for m in metrics:
 x3=pd.to_numeric(df[f'card__艇3_{m}'],errors='coerce'); others=pd.concat([pd.to_numeric(df[f'card__艇{i}_{m}'],errors='coerce') for i in [1,2,4,5,6]],axis=1)
 df[f'p3_{m}_raw']=x3; F.append(f'p3_{m}_raw'); df[f'p3_{m}_mean_gap']=x3-others.mean(axis=1); F.append(f'p3_{m}_mean_gap')
 for i in [1,2,4,5,6]:
  c=f'p3_{m}_gap{i}'; df[c]=x3-pd.to_numeric(df[f'card__艇{i}_{m}'],errors='coerce'); F.append(c)
feb=df[(df.date>='2026-02-01')&(df.date<'2026-03-01')].copy(); mar=df[(df.date>='2026-03-01')&(df.date<'2026-04-01')].copy()
lda=make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),LinearDiscriminantAnalysis(solver='lsqr',shrinkage='auto'))
lda.fit(feb[F],(feb.settle__winner==3).astype(int)); mar['p3']=lda.predict_proba(mar[F])[:,1]
m2=pd.to_numeric(mar['card__艇3_モーター2連対率'],errors='coerce')-pd.to_numeric(mar['card__艇2_モーター2連対率'],errors='coerce')
m3=pd.to_numeric(mar['card__艇3_モーター3連対率'],errors='coerce')-pd.to_numeric(mar['card__艇2_モーター3連対率'],errors='coerce')
n2=pd.to_numeric(mar['card__艇3_全国2連対率'],errors='coerce')-pd.to_numeric(mar['card__艇1_全国2連対率'],errors='coerce')
wave54=mar[(mar.p3<0.365448)&(mar.p3>=.20)&(m2>=.1)&(m3>=0)&(n2>=9.8)].copy()
assert len(wave54)==210 and int((wave54.settle__winner==3).sum())==71
CANDS=[1,2,4,5,6]
def combo_tuple(x):
 s=''.join(ch for ch in str(x) if ch.isdigit()); return tuple(map(int,s[:3])) if len(s)>=3 else None
def rows_for(races,labeled=True):
 rows=[]
 for _,r in races.iterrows():
  actual=combo_tuple(r['settle__actual_combo'])
  for a in CANDS:
   for b in CANDS:
    if a==b: continue
    z={'race_code':int(r.rc),'second':a,'third':b}
    for lane in CANDS: z[f'second_lane_{lane}']=int(a==lane); z[f'third_lane_{lane}']=int(b==lane)
    for m in metrics:
     va=pd.to_numeric(pd.Series([r[f'card__艇{a}_{m}']]),errors='coerce').iloc[0]; vb=pd.to_numeric(pd.Series([r[f'card__艇{b}_{m}']]),errors='coerce').iloc[0]; v3=pd.to_numeric(pd.Series([r[f'card__艇3_{m}']]),errors='coerce').iloc[0]
     z[f's_{m}']=va; z[f't_{m}']=vb; z[f's_gap3_{m}']=va-v3; z[f't_gap3_{m}']=vb-v3; z[f's_minus_t_{m}']=va-vb; z[f'pair_mean_{m}']=(va+vb)/2
    z['same_side']=int((a in [1,2])==(b in [1,2])); z['second_inner']=int(a in [1,2]); z['third_inner']=int(b in [1,2]); z['y']=int(actual==(3,a,b)) if labeled else 0; rows.append(z)
 return pd.DataFrame(rows)
train=rows_for(feb[feb.settle__winner==3]); test=rows_for(wave54,False); features=[c for c in train.columns if c not in ['race_code','second','third','y']]
model=make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),LogisticRegression(C=1.0,class_weight='balanced',solver='liblinear',max_iter=2000,random_state=0))
model.fit(train[features],train.y); test['score']=model.predict_proba(test[features])[:,1]
top=test.sort_values(['race_code','score','second','third'],ascending=[True,False,True,True]).groupby('race_code').head(3)
actual={int(r.rc):combo_tuple(r['settle__actual_combo']) for _,r in wave54.iterrows()}; payout={int(r.rc):float(r['settle__trifecta_payout_100_yen']) for _,r in wave54.iterrows()}
lines=[]; hits=0; ret=0
for rc,g in top.groupby('race_code'):
 tickets=[f'3-{int(a)}-{int(b)}' for a,b in zip(g.second,g.third)]; ac=actual[rc]; hit=ac is not None and f'{ac[0]}-{ac[1]}-{ac[2]}' in tickets
 if hit: hits+=1; ret+=payout[rc]
 lines.append({'race_code':rc,'tickets':'|'.join(tickets),'hit':int(hit),'payout':payout[rc] if hit else 0})
out=pd.DataFrame(lines).sort_values('race_code'); out.to_csv('research_v289_3head_opponent_rebuild_v1_tickets.csv',index=False)
sha=hashlib.sha256(open('research_v289_3head_opponent_rebuild_v1_tickets.csv','rb').read()).hexdigest()
summary={'wave54_races':210,'heads':71,'train_head_races':len(feb[feb.settle__winner==3]),'train_pair_rows':len(train),'features':len(features),'hits':hits,'stake_yen':63000,'return_yen':ret,'roi_pct':ret/63000*100,'ticket_sha256':sha,'model':'median+standardscale+LogisticRegression(C=1,class_weight=balanced,solver=liblinear,max_iter=2000,random_state=0)','tie_break':'score desc, second asc, third asc'}
open('research_v289_3head_opponent_rebuild_v1_summary.json','w').write(json.dumps(summary,ensure_ascii=False,indent=2))
print(json.dumps(summary,ensure_ascii=False,indent=2))
