"""4-head opponent research: race-development regime classification.
Research only. Frozen PH5 production population. June development, Jul-Aug holdout.
September outcomes remain unread. No production mutation.
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import research_4head_opponent_second_rerank_v2 as base

OUT=Path('/tmp/head4_opponent_regime_v1'); OUT.mkdir(parents=True,exist_ok=True)

def classify_truth(s,t):
    inner={1,2,3}
    if s in inner and t in inner: return 'INNER_REMAIN'
    if s==5 or t==5: return 'FIVE_FOLLOW'
    if s==6 or t==6: return 'SIX_RISE'
    return 'MIXED'

def race_features(g):
    inn=g[g.boat.isin([1,2,3])]; out=g[g.boat.isin([5,6])]
    def med(q,c):
        x=pd.to_numeric(q[c],errors='coerce')
        return float(x.median()) if x.notna().any() else np.nan
    def mx(q,c):
        x=pd.to_numeric(q[c],errors='coerce')
        return float(x.max()) if x.notna().any() else np.nan
    r=g.iloc[0]
    rec={'race_code':r.race_code,'month':r.month,'actual_second':int(r.actual_second),'actual_third':int(r.actual_third)}
    for c in ['pl_frame_p2','pl_recent_p2','w10_wr','w10_st','w10_sr','w10_rel4_wr','w10_rel4_st','w10_rel4_sr']:
        rec['inner_'+c]=med(inn,c); rec['outer_'+c]=med(out,c); rec['gap_'+c]=rec['inner_'+c]-rec['outer_'+c]
    for b in (1,2,3,5,6):
        q=g[g.boat.eq(b)]
        for c in ['p2','pl_frame_p2','pl_recent_p2','w10_wr','w10_st','w10_sr','w10_rel4_wr']:
            rec[f'b{b}_{c}']=med(q,c)
    rec['inner_p2_max']=mx(inn,'p2'); rec['outer_p2_max']=mx(out,'p2')
    rec['truth_regime']=classify_truth(rec['actual_second'],rec['actual_third'])
    return rec

def main():
    z=base.build_long()
    races=pd.DataFrame([race_features(g) for _,g in z.groupby('race_code',sort=False)])
    if len(races)!=81: raise RuntimeError(f'HEAD4_POPULATION_DRIFT {len(races)} != 81')
    dev=races[races.month.eq('2026-06')].copy()
    hold=races[races.month.isin(['2026-07','2026-08'])].copy()
    if len(dev)!=24 or len(hold)!=57: raise RuntimeError('MONTH_SPLIT_DRIFT')
    # First pass is intentionally descriptive: establish whether stable regimes exist
    # before fitting a classifier or changing tickets.
    summary=(races.groupby(['month','truth_regime']).size().rename('R').reset_index())
    pct=summary.copy(); pct['pct']=pct.R/pct.groupby('month').R.transform('sum')*100
    pair=(races.assign(pair=races.actual_second.astype(str)+'-'+races.actual_third.astype(str))
          .groupby(['month','pair']).size().rename('R').reset_index()
          .sort_values(['month','R'],ascending=[True,False]))
    # Pair-family taxonomy keeps 5/6 coexistence visible instead of masking it by precedence.
    def pair_family(row):
        s,t=int(row.actual_second),int(row.actual_third); inner={1,2,3}
        if s in inner and t in inner: return 'INNER_INNER'
        if s in inner and t==5: return 'INNER_5'
        if s==5 and t in inner: return '5_INNER'
        if s in inner and t==6: return 'INNER_6'
        if s==6 and t in inner: return '6_INNER'
        if {s,t}=={5,6}: return '5_6'
        return 'OTHER'
    races['pair_family']=races.apply(pair_family,axis=1)

    # Stage v3: leakage-safe pre-race classification of the three dominant families.
    # Fit/tune on June only; July and August are untouched holdouts.
    from sklearn.impute import SimpleImputer
    from sklearn.preprocessing import StandardScaler
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    major=['5_INNER','INNER_5','INNER_INNER']
    feature_cols=[x for x in races.columns if x not in
                  ['race_code','month','actual_second','actual_third','truth_regime','pair_family']]
    feature_cols=[x for x in feature_cols if pd.api.types.is_numeric_dtype(races[x])]
    train=races[(races.month.eq('2026-06')) & races.pair_family.isin(major)].copy()
    tests=races[(races.month.isin(['2026-07','2026-08'])) & races.pair_family.isin(major)].copy()
    pred_rows=[]
    if train.pair_family.nunique()==3:
        for C in [0.03,0.1,0.3,1.0,3.0]:
            model=make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),
                                LogisticRegression(C=C,max_iter=5000,class_weight='balanced'))
            model.fit(train[feature_cols],train.pair_family)
            for split,q in [('JUNE_DEV',train),('JUL_HOLDOUT',tests[tests.month.eq('2026-07')]),
                            ('AUG_HOLDOUT',tests[tests.month.eq('2026-08')]),('JULAUG_HOLDOUT',tests)]:
                if len(q)==0: continue
                pr=model.predict(q[feature_cols])
                acc=float(np.mean(pr==q.pair_family))
                pred_rows.append({'C':C,'split':split,'R':len(q),'accuracy':acc})
        pred=pd.DataFrame(pred_rows)
        # C is selected strictly by June development accuracy, with smaller C as tie-break.
        bestC=float(pred[pred.split.eq('JUNE_DEV')].sort_values(['accuracy','C'],ascending=[False,True]).iloc[0].C)
        pred['selected_C']=bestC
        pred.to_csv(OUT/'major_family_classifier_v1.csv',index=False)
        print('MAJOR_FAMILY_CLASSIFIER',pred.to_json(orient='records',force_ascii=False))
        print('MAJOR_FAMILY_SELECTED_C',bestC)
    # Stage v4: simpler binary target -- does boat 5 appear in 2nd/3rd when 4 wins?
    races['five_in_pair']=((races.actual_second.eq(5)) | (races.actual_third.eq(5))).astype(int)
    bin_features=[x for x in races.columns if x not in
                  ['race_code','month','actual_second','actual_third','truth_regime','pair_family','five_in_pair']]
    bin_features=[x for x in bin_features if pd.api.types.is_numeric_dtype(races[x])]
    btrain=races[races.month.eq('2026-06')].copy()
    btest=races[races.month.isin(['2026-07','2026-08'])].copy()
    brows=[]
    for C in [0.01,0.03,0.1,0.3,1.0]:
        bm=make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),
                         LogisticRegression(C=C,max_iter=5000,class_weight='balanced'))
        bm.fit(btrain[bin_features],btrain.five_in_pair)
        for split,q in [('JUNE_DEV',btrain),('JUL_HOLDOUT',btest[btest.month.eq('2026-07')]),
                        ('AUG_HOLDOUT',btest[btest.month.eq('2026-08')]),('JULAUG_HOLDOUT',btest)]:
            prob=bm.predict_proba(q[bin_features])[:,list(bm.classes_).index(1)]
            pred=(prob>=0.5).astype(int)
            acc=float(np.mean(pred==q.five_in_pair))
            # balanced accuracy avoids the ~58% positive base rate hiding a weak model.
            pos=q.five_in_pair.eq(1); neg=~pos
            tpr=float(np.mean(pred[pos]==1)) if pos.any() else np.nan
            tnr=float(np.mean(pred[neg]==0)) if neg.any() else np.nan
            bal=float(np.nanmean([tpr,tnr]))
            brows.append({'C':C,'split':split,'R':len(q),'accuracy':acc,'balanced_accuracy':bal,
                          'positive_rate':float(q.five_in_pair.mean())})
    bdf=pd.DataFrame(brows)
    bestBC=float(bdf[bdf.split.eq('JUNE_DEV')].sort_values(['balanced_accuracy','C'],ascending=[False,True]).iloc[0].C)
    bdf['selected_C']=bestBC
    bdf.to_csv(OUT/'five_binary_classifier_v1.csv',index=False)
    print('FIVE_BINARY_CLASSIFIER',bdf.to_json(orient='records',force_ascii=False))
    print('FIVE_BINARY_SELECTED_C',bestBC)
    fam=(races.groupby(['month','pair_family']).size().rename('R').reset_index())
    fam['pct']=fam.R/fam.groupby('month').R.transform('sum')*100
    fam.to_csv(OUT/'pair_family_monthly.csv',index=False)
    print('PAIR_FAMILY_MONTHLY',fam.to_json(orient='records',force_ascii=False))
    races.to_csv(OUT/'race_regime_features.csv',index=False)
    pct.to_csv(OUT/'regime_monthly.csv',index=False)
    pair.to_csv(OUT/'pair_monthly.csv',index=False)
    meta={'head4_R':len(races),'dev':'2026-06 only','holdout':['2026-07','2026-08'],
          'dev_R':len(dev),'holdout_R':len(hold),'SEPTEMBER_OUTCOMES_READ':False,
          'PH5_HEAD_MODEL_CHANGED':False,'PRODUCTION_CHANGED':False,
          'stage':'FIVE_BINARY_CLASSIFIER_V1'}
    (OUT/'meta.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2))
    print('REGIME_MONTHLY',pct.to_json(orient='records',force_ascii=False))
    print('PAIR_TOP',pair.groupby('month').head(8).to_json(orient='records',force_ascii=False))
    print(json.dumps(meta,ensure_ascii=False))
    print('HEAD4_OPPONENT_REGIME_V1_OK')
    print('SEPTEMBER_UNREAD')

if __name__=='__main__': main()
