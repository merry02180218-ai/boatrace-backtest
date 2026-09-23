#!/usr/bin/env python3
"""Opponent research v2: leakage-safe SECOND soft rerank on frozen PH5 163R.

Development: June only (race-group CV chooses alpha). Holdout: July-August, never used
for alpha selection. PH5 head model / production BET population are immutable.
PLAYERHistory is prior-day causal; Waku10 is pre-race only. September outcomes unread.
Research only: no production mutation and no ROI claim until counterfactual odds audit.
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import GroupKFold, cross_val_predict
import audit_4head_ph5_live_walkforward as parent
import research_4head_player_waku_soft_ablation_v23 as phsrc
import research_4head_waku10_rel43_v4 as wsrc

ROOT=Path('/tmp/head4_ph5_live_walkforward')
OUT=Path('/tmp/head4_opponent_second_rerank_v2'); OUT.mkdir(parents=True,exist_ok=True)
BOATS=(1,2,3,5,6)
ALPHAS=(0.0,0.15,0.25,0.35,0.50,0.70,1.0)
MODES=('rerank','rescue','scenario')
SECOND_GAP=.11
THIRD_GAP=.18
FEATURES=['logit_p2','pl_all_win','pl_all_p2','pl_frame_win','pl_frame_p2','pl_recent_p2','w10_wr','w10_st','w10_sr','w10_pastwin','w10_rel4_wr','w10_rel4_st','w10_rel4_sr','w10_rel4_pastwin']

def logit(p):
    p=float(np.clip(p,1e-6,1-1e-6)); return np.log(p/(1-p))

def model():
    return Pipeline([('imp',SimpleImputer(strategy='median',add_indicator=True)),('sc',StandardScaler()),('lr',LogisticRegression(C=.5,max_iter=2000,class_weight='balanced'))])

def build_long():
    d=pd.read_csv(ROOT/'race_detail.csv',dtype={'race_code':str}); d.race_code=d.race_code.astype(str).str.zfill(12)
    d=d[d.production_bet.eq(1)].copy()
    if len(d)!=163: raise RuntimeError(f'FROZEN_POPULATION_DRIFT {len(d)} != 163')
    tr=parent.truth()
    ph=phsrc.build_ph(); ph.race_code=ph.race_code.astype(str).str.zfill(12)
    w=wsrc.build_waku(d.race_code.tolist()); w.race_code=w.race_code.astype(str).str.zfill(12)
    wide=d[['race_code','date','head4','tickets','opponent_diag']].merge(ph,on='race_code',how='left',validate='one_to_one').merge(w,on='race_code',how='left',validate='one_to_one')
    rows=[]
    for _,r in wide.iterrows():
        a=tr.get(r.race_code)
        if not a or a[0]!=4: continue
        diag=json.loads(r.opponent_diag); actual_s=int(a[1]); actual_t=int(a[2])
        for b in BOATS:
            rec={'race_code':r.race_code,'date':str(r.date),'month':str(r.date)[:7],'boat':b,'y_second':int(b==actual_s),'actual_second':actual_s,'actual_third':actual_t,'p2':float(diag['p2'][str(b)]),'logit_p2':logit(diag['p2'][str(b)]),'tickets':r.tickets,'opponent_diag':r.opponent_diag}
            for k in ('all_win','all_p2','frame_win','frame_p2','recent_p2'): rec['pl_'+k]=pd.to_numeric(pd.Series([r.get(f'b{b}_pl_{k}')]),errors='coerce').iloc[0]
            for k in ('wr','st','sr','pastwin','rel4_wr','rel4_st','rel4_sr','rel4_pastwin'):
                col=f'w10_b{b}_{k}' if not k.startswith('rel4_') else f'w10_rel4_b{b}_{k[5:]}'
                rec['w10_'+k]=pd.to_numeric(pd.Series([r.get(col)]),errors='coerce').iloc[0]
            rows.append(rec)
    z=pd.DataFrame(rows)
    if z.race_code.nunique()!=81: raise RuntimeError(f'HEAD4_POPULATION_DRIFT {z.race_code.nunique()} != 81')
    return z

def score_group(g,score_col):
    return list(g.sort_values([score_col,'boat'],ascending=[False,True]).boat.astype(int))

def tickets_for(diag, second_rank, score_map):
    pc={(int(k.split('>')[0]),int(k.split('>')[1])):float(v) for k,v in diag['pc'].items()}
    out=[]; secs=second_rank[:2]
    if score_map[second_rank[1]]-score_map[second_rank[2]]<=SECOND_GAP: secs=secs+[second_rank[2]]
    for s in secs:
        thirds=sorted((t for t in BOATS if t!=s),key=lambda t:(-pc[(s,t)],t))
        for t in thirds[:2]:
            x=f'4-{s}-{t}'
            if x not in out: out.append(x)
        if pc[(s,thirds[1])]-pc[(s,thirds[2])]<=THIRD_GAP:
            x=f'4-{s}-{thirds[2]}'
            if x not in out: out.append(x)
    return out

def evaluate(z,score_col,label):
    rows=[]
    for rc,g in z.groupby('race_code',sort=False):
        r=g.iloc[0]; rank=score_group(g,score_col); sm={int(x.boat):float(g.loc[g.boat.eq(int(x.boat)), score_col].iloc[0]) for x in g.itertuples()}; diag=json.loads(r.opponent_diag)
        ts=tickets_for(diag,rank,sm); actual=f"4-{int(r.actual_second)}-{int(r.actual_third)}"
        rows.append({'race_code':rc,'month':r.month,'variant':label,'second_rank':rank.index(int(r.actual_second))+1,'second_top2':int(int(r.actual_second) in rank[:2]),'second_top3':int(int(r.actual_second) in rank[:3]),'trifecta_capture':int(actual in ts),'ticket_count':len(ts)})
    return pd.DataFrame(rows)

def scenario_score(frame):
    # Development-only expansion: use pre-race PLAYERHistory/Waku10 as an attack/wall scenario signal.
    # No head/outcome fields enter this score.
    x=frame.copy()
    def z(s):
        s=pd.to_numeric(s,errors='coerce'); med=s.median(); s=s.fillna(med)
        sd=s.std(); return (s-s.mean())/(sd if pd.notna(sd) and sd>1e-9 else 1.0)
    # Higher win/p2 and Waku10 win/straight-rate support an opponent surviving the 4 attack.
    sig=(z(x.pl_frame_p2)+z(x.pl_recent_p2)+z(x.w10_wr)+z(x.w10_sr)+z(x.w10_rel4_wr))/5.0
    return x.logit_p2 + 0.25*sig

def pattern_score(frame, pattern):
    x=frame.copy()
    def z(s):
        s=pd.to_numeric(s,errors='coerce'); s=s.fillna(s.median()); sd=s.std()
        return (s-s.mean())/(sd if pd.notna(sd) and sd>1e-9 else 1.0)
    base=x.logit_p2.copy()
    if pattern=='inner_survive':
        bonus=(z(x.pl_frame_p2)+z(x.w10_wr)-z(x.w10_rel4_wr))/3.0
        bonus=bonus*np.where(x.boat.isin([1,2,3]),1.0,-0.35)
    elif pattern=='wall23':
        bonus=(z(x.pl_recent_p2)+z(x.w10_st)+z(x.w10_sr))/3.0
        bonus=bonus*np.where(x.boat.isin([2,3]),1.0,-0.30)
    elif pattern=='five_follow':
        bonus=(z(x.w10_wr)+z(x.w10_sr)+z(x.w10_rel4_wr)+z(x.pl_all_p2))/4.0
        bonus=bonus*np.where(x.boat.eq(5),1.0,-0.20)
    elif pattern=='six_open':
        bonus=(z(x.w10_st)+z(x.w10_sr)+z(x.pl_recent_p2))/3.0
        bonus=bonus*np.where(x.boat.eq(6),1.0,-0.20)
    else: raise ValueError(pattern)
    return base+0.20*bonus

def main():
    z=build_long(); dev=z[z.month.eq('2026-06')].copy(); hold=z[z.month.isin(['2026-07','2026-08'])].copy()
    if dev.race_code.nunique()!=24 or hold.race_code.nunique()!=57: raise RuntimeError('MONTH_HEAD4_COUNTS_DRIFT')
    groups=dev.race_code.values; cv=GroupKFold(n_splits=min(6,dev.race_code.nunique()))
    dev['ml_cv']=cross_val_predict(model(),dev[FEATURES],dev.y_second,groups=groups,cv=cv,method='predict_proba')[:,1]
    cvrows=[]
    for a in ALPHAS:
        lp=np.log(np.clip(dev.ml_cv,1e-6,1-1e-6)/np.clip(1-dev.ml_cv,1e-6,1-1e-6))
        dev[f'score_{a}']=(1-a)*dev.logit_p2+a*lp
        ev=evaluate(dev,f'score_{a}',f'cv_a{a}')
        cvrows.append({'alpha':a,'second_top2':int(ev.second_top2.sum()),'second_top3':int(ev.second_top3.sum()),'trifecta_capture':int(ev.trifecta_capture.sum()),'avg_points':float(ev.ticket_count.mean())})
    cvdf=pd.DataFrame(cvrows).sort_values(['second_top2','trifecta_capture','second_top3','alpha'],ascending=[False,False,False,True])
    alpha=float(cvdf.iloc[0].alpha)
    m=model().fit(dev[FEATURES],dev.y_second)
    for frame in (dev,hold):
        pp=m.predict_proba(frame[FEATURES])[:,1]; frame['ml_prob']=pp
        frame['rerank_score']=(1-alpha)*frame.logit_p2+alpha*np.log(np.clip(pp,1e-6,1-1e-6)/np.clip(1-pp,1e-6,1-1e-6))
        frame['baseline_score']=frame.logit_p2
    for frame in (dev,hold):
        frame['scenario_score']=scenario_score(frame)
        for p in ('inner_survive','wall23','five_follow','six_open'): frame['pattern_'+p]=pattern_score(frame,p)
    # Rescue-only variant: preserve production top2; use scenario signal only to choose the optional third SECOND.
    def rescue_eval(frame,label):
        rows=[]
        for rc,g in frame.groupby('race_code',sort=False):
            r=g.iloc[0]; base=score_group(g,'baseline_score'); cand=base[2:]; cand=sorted(cand,key=lambda b:(-float(g.loc[g.boat.eq(b),'scenario_score'].iloc[0]),b)); rank=base[:2]+cand
            sm={int(b):float(g.loc[g.boat.eq(b),'baseline_score'].iloc[0]) for b in g.boat}
            # Force rescue decision to production gap; scenario only determines which outsider is rescued.
            diag=json.loads(r.opponent_diag); ts=tickets_for(diag,rank,sm); actual=f"4-{int(r.actual_second)}-{int(r.actual_third)}"
            rows.append({'race_code':rc,'month':r.month,'variant':label,'second_rank':rank.index(int(r.actual_second))+1,'second_top2':int(int(r.actual_second) in rank[:2]),'second_top3':int(int(r.actual_second) in rank[:3]),'trifecta_capture':int(actual in ts),'ticket_count':len(ts)})
        return pd.DataFrame(rows)
    detail=pd.concat([evaluate(dev,'baseline_score','baseline_dev'),evaluate(dev,'rerank_score','rerank_dev'),evaluate(dev,'scenario_score','scenario_dev'),rescue_eval(dev,'rescue_dev')]+[evaluate(dev,'pattern_'+p,'pattern_'+p+'_dev') for p in ('inner_survive','wall23','five_follow','six_open')]+[evaluate(hold,'baseline_score','baseline_holdout'),evaluate(hold,'rerank_score','rerank_holdout'),evaluate(hold,'scenario_score','scenario_holdout'),rescue_eval(hold,'rescue_holdout')]+[evaluate(hold,'pattern_'+p,'pattern_'+p+'_holdout') for p in ('inner_survive','wall23','five_follow','six_open')],ignore_index=True)
    summary=detail.groupby(['variant','month']).agg(R=('race_code','size'),second_top2=('second_top2','sum'),second_top3=('second_top3','sum'),trifecta_capture=('trifecta_capture','sum'),avg_points=('ticket_count','mean')).reset_index()
    cvdf.to_csv(OUT/'june_groupcv_alpha_grid.csv',index=False); detail.to_csv(OUT/'race_detail.csv',index=False); summary.to_csv(OUT/'summary.csv',index=False)
    meta={'production_bets':163,'head4_R':81,'dev':'2026-06 only','holdout':['2026-07','2026-08'],'dev_head4_R':24,'holdout_head4_R':57,'selected_alpha':alpha,'features':FEATURES,'SECOND_GAP':SECOND_GAP,'THIRD_GAP':THIRD_GAP,'PLAYER_HISTORY':'causal prior-day','Waku10':'pre-race only','SEPTEMBER_OUTCOMES_READ':False,'PH5_HEAD_MODEL_CHANGED':False,'PRODUCTION_CHANGED':False,'research_modes':['SECOND rerank','SECOND rescue','pre-race scenario/展開 proxy','inner survive','2/3 wall survive','5 follow/makurisashi','6 open-lane'],'ROI_EVALUATED':False,'roi_note':'counterfactual newly-added ticket odds must be reconstructed before ROI claim'}
    (OUT/'meta.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
    print('SECOND_RERANK_CV_TOP',cvdf.head(7).to_json(orient='records'))
    print('SECOND_RERANK_SUMMARY',summary.to_json(orient='records'))
    print(json.dumps(meta,ensure_ascii=False)); print('HEAD4_OPPONENT_SECOND_RERANK_V2_OK'); print('SEPTEMBER_UNREAD')
if __name__=='__main__': main()
