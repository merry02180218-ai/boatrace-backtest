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
    # Stage v5: structure-first test. Does collapse/weakness of the inner wall (1-3)
    # explain when boat 5 follows the successful 4-corner attack?
    # All ingredients are pre-race causal. Thresholds are selected on June only.
    def zsafe(s):
        x=pd.to_numeric(s,errors='coerce')
        sd=x.std(ddof=0)
        return (x-x.mean())/(sd if pd.notna(sd) and sd>1e-12 else 1.0)
    wall_parts=[]
    # High p2 / player frame+recent / Waku WR-SR imply a stronger surviving inner wall.
    for col in ['p2','pl_frame_p2','pl_recent_p2','w10_wr','w10_sr']:
        vals=[]
        for _,r in races.iterrows():
            vv=[r.get(f'b{b}_{col}',np.nan) for b in (1,2,3)]
            vals.append(float(np.nanmean(vv)) if np.isfinite(pd.to_numeric(pd.Series(vv),errors='coerce')).any() else np.nan)
        races[f'wall_{col}']=vals
        wall_parts.append(f'wall_{col}')
    # Relative-to-4 Waku WR: larger inner relative value means a harder wall for 4/5.
    if all(f'b{b}_w10_rel4_wr' in races.columns for b in (1,2,3)):
        races['wall_rel4_wr']=races[[f'b{b}_w10_rel4_wr' for b in (1,2,3)]].mean(axis=1)
        wall_parts.append('wall_rel4_wr')
    # Standardize globally only for descriptive scoring; threshold selection remains June-only.
    # No outcomes enter this score.
    races['inner_wall_strength']=pd.concat([zsafe(races[x]) for x in wall_parts],axis=1).mean(axis=1)
    races['inner_wall_collapse']=-races.inner_wall_strength
    rows=[]
    june=races[races.month.eq('2026-06')].copy()
    qs=[0.25,0.40,0.50,0.60,0.75]
    cuts=[float(june.inner_wall_collapse.quantile(q)) for q in qs]
    for q,cut in zip(qs,cuts):
        for split,dq in [('JUNE_DEV',june),('JUL_HOLDOUT',races[races.month.eq('2026-07')]),
                         ('AUG_HOLDOUT',races[races.month.eq('2026-08')]),('JULAUG_HOLDOUT',races[races.month.isin(['2026-07','2026-08'])])]:
            hi=dq[dq.inner_wall_collapse.ge(cut)]
            lo=dq[dq.inner_wall_collapse.lt(cut)]
            rows.append({'q':q,'cut':cut,'split':split,'R':len(dq),
                         'high_collapse_R':len(hi),'high_five_rate':float(hi.five_in_pair.mean()) if len(hi) else np.nan,
                         'low_R':len(lo),'low_five_rate':float(lo.five_in_pair.mean()) if len(lo) else np.nan,
                         'lift':float(hi.five_in_pair.mean()-lo.five_in_pair.mean()) if len(hi) and len(lo) else np.nan})
    wdf=pd.DataFrame(rows)
    # choose June threshold by lift, requiring at least 6 races on each side to avoid tiny-cell fitting
    cand=wdf[(wdf.split.eq('JUNE_DEV')) & (wdf.high_collapse_R.ge(6)) & (wdf.low_R.ge(6))]
    bestQ=float(cand.sort_values(['lift','q'],ascending=[False,True]).iloc[0].q)
    wdf['selected_q']=bestQ
    wdf.to_csv(OUT/'inner_wall_five_v1.csv',index=False)
    print('INNER_WALL_FIVE_V1',wdf.to_json(orient='records',force_ascii=False))
    print('INNER_WALL_SELECTED_Q',bestQ)
    # Stage v6: decompose the wall by lanes 3 -> 2 -> 1 and distinguish
    # 5-follow (5 second) from 5-cutback (5 third).
    lane_rows=[]
    lane_cols=['p2','pl_frame_p2','pl_recent_p2','w10_wr','w10_sr','w10_rel4_wr']
    for b in (1,2,3):
        cols=[f'b{b}_{x}' for x in lane_cols if f'b{b}_{x}' in races.columns]
        races[f'wall_b{b}_strength']=pd.concat([zsafe(races[x]) for x in cols],axis=1).mean(axis=1)
        races[f'wall_b{b}_collapse']=-races[f'wall_b{b}_strength']
    # Structural scores: 3 breaks first; 2-break extends the lane; 1 resistance can open cutback.
    races['wall_3break']=races.wall_b3_collapse
    races['wall_32break']=(races.wall_b3_collapse+races.wall_b2_collapse)/2
    races['wall_321break']=(races.wall_b3_collapse+races.wall_b2_collapse+races.wall_b1_collapse)/3
    races['five_follow_second']=races.actual_second.eq(5).astype(int)
    races['five_cutback_third']=races.actual_third.eq(5).astype(int)
    for score in ['wall_3break','wall_32break','wall_321break']:
        june=races[races.month.eq('2026-06')]
        for q in [0.4,0.5,0.6,0.75]:
            cut=float(june[score].quantile(q))
            for split,dq in [('JUNE_DEV',june),('JUL_HOLDOUT',races[races.month.eq('2026-07')]),
                             ('AUG_HOLDOUT',races[races.month.eq('2026-08')]),('JULAUG_HOLDOUT',races[races.month.isin(['2026-07','2026-08'])])]:
                hi=dq[dq[score].ge(cut)]; lo=dq[dq[score].lt(cut)]
                lane_rows.append({'score':score,'q':q,'cut':cut,'split':split,'R':len(dq),'high_R':len(hi),
                  'high_5_second':float(hi.five_follow_second.mean()) if len(hi) else np.nan,
                  'low_5_second':float(lo.five_follow_second.mean()) if len(lo) else np.nan,
                  'lift_5_second':float(hi.five_follow_second.mean()-lo.five_follow_second.mean()) if len(hi) and len(lo) else np.nan,
                  'high_5_third':float(hi.five_cutback_third.mean()) if len(hi) else np.nan,
                  'low_5_third':float(lo.five_cutback_third.mean()) if len(lo) else np.nan,
                  'lift_5_third':float(hi.five_cutback_third.mean()-lo.five_cutback_third.mean()) if len(hi) and len(lo) else np.nan,
                  'high_5_any':float(hi.five_in_pair.mean()) if len(hi) else np.nan,
                  'low_5_any':float(lo.five_in_pair.mean()) if len(lo) else np.nan})
    ldf=pd.DataFrame(lane_rows)
    ldf.to_csv(OUT/'wall_lane_decomp_v1.csv',index=False)
    print('WALL_LANE_DECOMP_V1',ldf.to_json(orient='records',force_ascii=False))
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
          'stage':'WALL_LANE_DECOMP_V1'}
    (OUT/'meta.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2))
    print('REGIME_MONTHLY',pct.to_json(orient='records',force_ascii=False))
    print('PAIR_TOP',pair.groupby('month').head(8).to_json(orient='records',force_ascii=False))
    print(json.dumps(meta,ensure_ascii=False))
    print('HEAD4_OPPONENT_REGIME_V1_OK')
    print('SEPTEMBER_UNREAD')

if __name__=='__main__': main()
