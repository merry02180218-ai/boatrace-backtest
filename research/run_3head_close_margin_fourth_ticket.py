from __future__ import annotations
import json
from pathlib import Path
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from research.run_3head_exhibition_v5 import EX, STATIC, load_direct, pair_rows

SOURCE='analysis_v289_3head_wave21_allrace_feature_settled.csv'
MARGINS=[.0025,.005,.0075,.01,.015,.02,.03,.05,.075,.10]
MONTHS=[3,4,5,6,7,8]

def model_and_features(x):
    feats=[c for c in x if c not in ['race_code','second','third','y']]
    m=make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),LogisticRegression(C=.25,class_weight='balanced',solver='liblinear',max_iter=2000,random_state=0))
    return m,feats

def audit_month(x, margin):
    z=x.sort_values(['race_code','p','second','third'],ascending=[True,False,True,True]).copy()
    z['rank']=z.groupby('race_code').cumcount()+1
    top3=z[z['rank']<=3]; base_hits=set(top3.loc[top3.y.eq(1),'race_code'])
    r3=z[z['rank']==3].set_index('race_code'); r4=z[z['rank']==4].set_index('race_code')
    common=r3.index.intersection(r4.index); gaps=(r3.loc[common,'p']-r4.loc[common,'p']).astype(float)
    add=set(gaps[gaps<=margin].index); fourth=z[(z['rank']==4)&z.race_code.isin(add)]
    added_hits=set(fourth.loc[fourth.y.eq(1),'race_code'])-base_hits; n=int(z.race_code.nunique())
    return {'races':n,'baseline_hits':len(base_hits),'baseline_capture':len(base_hits)/n if n else None,'fourth_added_races':len(add),'fourth_added_tickets':len(fourth),'incremental_hits':len(added_hits),'four_point_hits':len(base_hits|added_hits),'four_point_capture':len(base_hits|added_hits)/n if n else None,'incremental_hit_per_added_ticket':len(added_hits)/len(fourth) if len(fourth) else None,'total_tickets':3*n+len(fourth),'ticket_increase_pct':len(fourth)/(3*n) if n else None,'gap_mean_added':float(gaps[gaps<=margin].mean()) if len(add) else None}

def main():
    use=['date','race_code_norm','settle__actual_combo','settle__winner','settle__usable','closing_odds__ok']+[f'card__艇{i}_{m}' for i in range(1,7) for m in STATIC]
    df=pd.read_csv(SOURCE,usecols=use,low_memory=False); df.date=pd.to_datetime(df.date); df['rc']=pd.to_numeric(df.race_code_norm,errors='coerce').astype('Int64')
    # Hard cutoff before any outcome-based filtering: September is never present below.
    df=df[df.date<'2026-09-01'].copy(); df=df[(df.settle__usable==1)&(df.closing_odds__ok==1)&(~df.rc.isin(EX))].copy()
    feb=df[(df.date>='2026-02-01')&(df.date<'2026-03-01')].copy(); assert len(feb)==3970
    feb_heads=feb[feb.settle__winner==3].copy(); assert len(feb_heads)==478
    hist=df[(df.date>='2026-03-01')&(df.date<'2026-09-01')].copy()
    codes=[str(int(x)).zfill(12) for x in pd.concat([feb.rc,hist.rc]).dropna().unique()]; direct=load_direct(codes)
    feb_common=feb_heads[feb_heads.rc.map(lambda x:direct.get(str(int(x)).zfill(12),{}).get('common',False))].copy(); assert len(feb_common)==390
    train=pair_rows(feb_common,direct,'A',{}); model,feats=model_and_features(train); model.fit(train[feats],train.y)
    data={}
    for month in MONTHS:
      start=pd.Timestamp(2026,month,1); end=start+pd.offsets.MonthBegin(1)
      heads=df[(df.date>=start)&(df.date<end)&(df.settle__winner==3)].copy(); common=heads[heads.rc.map(lambda x:direct.get(str(int(x)).zfill(12),{}).get('common',False))].copy()
      x=pair_rows(common,direct,'A',{}); x['p']=model.predict_proba(x[feats])[:,1]; data[month]=x
    candidates=[{'margin':mar,**audit_month(data[3],mar)} for mar in MARGINS]
    c=pd.DataFrame(candidates); c['_eff']=c.incremental_hit_per_added_ticket.fillna(-1)
    # Freeze using March only; Apr-Jun never participates in selection.
    best=c.sort_values(['incremental_hits','_eff','fourth_added_tickets','margin'],ascending=[False,False,True,True]).iloc[0]; frozen=float(best.margin)
    monthly={str(m):{**audit_month(data[m],frozen),'non_pristine':m in [7,8]} for m in MONTHS}
    out={'phase':'3HEAD_CLOSE_MARGIN_FOURTH_TICKET','train_period':'2026-02','selection_month':'2026-03 only','frozen_margin':frozen,'march_grid':c.drop(columns=['_eff']).to_dict('records'),'frozen_monthly':monthly,'candidate_selected_using_apr_jun':False,'july_august_non_pristine':True,'exact_v288_exclusion_preserved':True,'september_outcomes_read':False,'production_changed':False,'note':'Adds rank-4 ticket only when base rank3-rank4 probability margin is close; existing top3 is never replaced.'}
    Path('research_v289_3head_close_margin_fourth_ticket.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)); c.drop(columns=['_eff']).to_csv('research_v289_3head_close_margin_fourth_ticket_march_grid.csv',index=False); print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
