from __future__ import annotations
import json
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from research.run_3head_exhibition_v5 import EX, STATIC, load_direct, pair_rows

SOURCE='analysis_v289_3head_wave21_allrace_feature_settled.csv'
W_EX=0.08; W_ST=0.08; THRESHOLD=0.0

def model_and_features(x):
    feats=[c for c in x if c not in ['race_code','second','third','y']]
    m=make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),LogisticRegression(C=.25,class_weight='balanced',solver='liblinear',max_iter=2000,random_state=0))
    return m,feats

def top3(v,score):
    z=v.copy(); z['_score']=score
    return z.sort_values(['race_code','_score','second','third'],ascending=[True,False,True,True]).groupby('race_code').head(3)

def hitset(top): return {rc for rc,g in top.groupby('race_code') if g.y.eq(1).any()}

def add_direct_scores(x,direct):
    x=x.copy()
    x['exq']=[.55*direct[rc]['ex'][int(a)]+.45*direct[rc]['ex'][int(b)] for rc,a,b in zip(x.race_code,x.second,x.third)]
    x['stq']=[.55*direct[rc]['st'][int(a)]+.45*direct[rc]['st'][int(b)] for rc,a,b in zip(x.race_code,x.second,x.third)]
    return x

def audit(test,direct,model,feats):
    test=pair_rows(test,direct,'A',{})
    test['p']=model.predict_proba(test[feats])[:,1]; test=add_direct_scores(test,direct)
    basehits=hitset(top3(test,test.p)); allr=set(test.race_code.unique())
    raw=W_EX*(test.exq-.5)+W_ST*(test.stq-.5)
    strength=(test.exq-.5).abs()+(test.stq-.5).abs(); adj=np.where(strength>=THRESHOLD,raw,0.0)
    hh=hitset(top3(test,test.p+adj))
    rescued=len((allr-basehits)&hh); broken=len(basehits-hh)
    return {'races':len(allr),'baseline_hits':len(basehits),'baseline_capture':len(basehits)/len(allr),'corrected_hits':len(hh),'corrected_capture':len(hh)/len(allr),'rescued_miss':rescued,'broken_hit':broken,'net_rescue':rescued-broken}

def main():
    use=['date','race_code_norm','settle__actual_combo','settle__winner','settle__usable','closing_odds__ok']+[f'card__艇{i}_{m}' for i in range(1,7) for m in STATIC]
    df=pd.read_csv(SOURCE,usecols=use,low_memory=False); df.date=pd.to_datetime(df.date); df['rc']=pd.to_numeric(df.race_code_norm,errors='coerce').astype('Int64')
    df=df[(df.settle__usable==1)&(df.closing_odds__ok==1)&(~df.rc.isin(EX))].copy()
    feb=df[(df.date>='2026-02-01')&(df.date<'2026-03-01')].copy(); assert len(feb)==3970
    feb_heads=feb[feb.settle__winner==3].copy(); assert len(feb_heads)==478
    hist=df[(df.date>='2026-04-01')&(df.date<'2026-09-01')].copy()
    codes=[str(int(x)).zfill(12) for x in pd.concat([feb.rc,hist.rc]).dropna().unique()]
    direct=load_direct(codes)
    feb_common=feb_heads[feb_heads.rc.map(lambda x:direct.get(str(int(x)).zfill(12),{}).get('common',False))].copy(); assert len(feb_common)==390
    train=pair_rows(feb_common,direct,'A',{}); model,feats=model_and_features(train); model.fit(train[feats],train.y)
    monthly={}; total={'races':0,'baseline_hits':0,'corrected_hits':0,'rescued_miss':0,'broken_hit':0,'net_rescue':0}
    for month in range(4,9):
        start=pd.Timestamp(2026,month,1); end=start+pd.offsets.MonthBegin(1)
        m=df[(df.date>=start)&(df.date<end)&(df.settle__winner==3)].copy()
        common=m[m.rc.map(lambda x:direct.get(str(int(x)).zfill(12),{}).get('common',False))].copy()
        r=audit(common,direct,model,feats); r['non_pristine']=month in (7,8); monthly[f'2026-{month:02d}']=r
        for k in total: total[k]+=r[k]
    total['baseline_capture']=total['baseline_hits']/total['races']; total['corrected_capture']=total['corrected_hits']/total['races']
    out={'phase':'APR_AUG_FROZEN_POST_RANKING_TICKET_RESCUE_STABILITY','train_period':'2026-02','audit_period':'2026-04..2026-08','frozen_params':{'w_ex':W_EX,'w_st':W_ST,'threshold':THRESHOLD},'monthly':monthly,'total':total,'retuned':False,'july_august_non_pristine':True,'exact_v288_exclusion_preserved':True,'september_outcomes_read':False,'production_changed':False}
    Path('research_v289_3head_exhibition_ticket_rescue_apr_aug.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)); print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
