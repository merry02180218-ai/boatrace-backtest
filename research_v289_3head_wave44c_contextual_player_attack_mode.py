from __future__ import annotations
import json
from datetime import date, timedelta
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, log_loss, accuracy_score
from sklearn.linear_model import LogisticRegression
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
import research_v289_3head_wave44b_player_attack_mode as pbase
import research_v289_3head_wave31_nonlinear_gate as sbase

SRC=Path('analysis_v289_3head_wave21_allrace_feature_settled.csv')
OUT=Path('analysis_v289_3head_wave44c_contextual_player_attack_mode.csv')
OUTJ=Path('research_v289_3head_wave44c_contextual_player_attack_mode.json')
OUTM=Path('research_v289_3head_wave44c_contextual_player_attack_mode.md')
START=date(2025,2,1); END=date(2026,3,31)


def build_history_and_labels(target):
    wanted=set(target.race_code.map(pbase.norm_code)); labels={}; bundles={}; days=[]; cur=START
    while cur<=END:
        days.append(cur); cur+=timedelta(days=1)
    with ThreadPoolExecutor(max_workers=16) as ex:
        fs={ex.submit(pbase.day_bundle,dd):dd for dd in days}
        for f in as_completed(fs):
            day_s,cmap,results=f.result(); bundles[day_s]=(cmap,results)
    hist=[]
    for day_s in sorted(bundles):
        cmap,results=bundles[day_s]
        for r in results:
            code=pbase.norm_code(r.get('レースコード',''))
            winner=pbase.pick(r,['1着_艇番'])
            mode=pbase.norm_mode(pbase.pick(r,['決まり手']))
            card=cmap.get(code,{})
            rid=pbase.pick(card,[f'艇{winner}_登録番号']) if winner else ''
            if rid and winner:
                hist.append((day_s,code,rid,str(winner),mode))
            if code in wanted: labels[code]=mode
    return pd.DataFrame(hist,columns=['date','race_code','racer_id','winner_boat','mode']),labels


def add_player_priors(target,h,labels):
    rows=[]
    for idx,r in target.sort_values(['date','race_code']).iterrows():
        code=pbase.norm_code(r.race_code); mode=labels.get(code,'OTHER')
        if mode not in ('MAKURI','MAKURI_SASHI'): continue
        prior=h[(h['racer_id']==r.racer_id)&(h['date']<r.date)&(h['winner_boat']=='3')&h['mode'].isin(['MAKURI','MAKURI_SASHI'])]
        recent=prior[prior['date']>=str(date.fromisoformat(r.date)-timedelta(days=365))]
        def feats(q,pfx):
            n=len(q); m=int((q['mode']=='MAKURI').sum()); s=int((q['mode']=='MAKURI_SASHI').sum())
            return {f'{pfx}_n':n,f'{pfx}_makuri_share':(m+1)/(n+2),f'{pfx}_logodds':float(np.log((m+1)/(s+1)))}
        z={'src_index':idx,'date':r.date,'race_code':r.race_code,'mode':mode}
        z.update(feats(prior,'career')); z.update(feats(recent,'y1')); rows.append(z)
    return pd.DataFrame(rows)


def metrics(y,p):
    pred=(p>=.5).astype(int)
    return {'rows':int(len(y)),'auc':float(roc_auc_score(y,p)),'logloss':float(log_loss(y,p)),'accuracy':float(accuracy_score(y,pred))}


def main():
    d=pd.read_csv(SRC,dtype=str).fillna('')
    if d.date.max()>'2026-08-31': raise RuntimeError('September forbidden')
    idcol='card__艇3_登録番号'
    if idcol not in d.columns: raise RuntimeError('missing racer id')
    target=d[(d.date>='2026-02-01')&(d.date<='2026-03-31')&(d.settle__head3_actual.astype(str)=='1')].copy()
    target['racer_id']=target[idcol].astype(str).str.strip()
    h,labels=build_history_and_labels(target)
    x=add_player_priors(target,h,labels)
    if x.empty: raise RuntimeError('no labeled targets')
    static=sbase.build_static(d.loc[x.src_index].copy()).copy()
    static.index=x.index
    fs_player=['career_n','career_makuri_share','career_logodds','y1_n','y1_makuri_share','y1_logodds']
    X=pd.concat([x[fs_player],static],axis=1).replace([np.inf,-np.inf],np.nan)
    x['y']=(x['mode']=='MAKURI').astype(int)
    tr=x.date.str[:7].eq('2026-02'); te=x.date.str[:7].eq('2026-03')
    if x.loc[tr,'y'].nunique()<2 or x.loc[te,'y'].nunique()<2: raise RuntimeError('both classes required')
    model=make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),LogisticRegression(C=.12,max_iter=1500,class_weight='balanced'))
    model.fit(X.loc[tr],x.loc[tr,'y']); p=model.predict_proba(X.loc[te])[:,1]
    march=x.loc[te].copy(); march['pred_p_makuri']=p
    full=metrics(march.y,p)
    priorp=march.y1_makuri_share.to_numpy(float)
    prior={'auc':float(roc_auc_score(march.y,priorp)),'logloss':float(log_loss(march.y,np.clip(priorp,1e-6,1-1e-6)))}
    msort=march.sort_values(['date','race_code']).reset_index(drop=True); cut=len(msort)//2
    early=metrics(msort.iloc[:cut].y,msort.iloc[:cut].pred_p_makuri)
    late=metrics(msort.iloc[cut:].y,msort.iloc[cut:].pred_p_makuri)
    march.to_csv(OUT,index=False,encoding='utf-8-sig')
    gate=full['auc']>=.60 and min(early['auc'],late['auc'])>=.54
    decision='MODE_SIGNAL_FOUND' if gate else 'MODE_SIGNAL_WEAK'
    out={'wave':'44c-contextual-player-attack-mode','historical_join_rows':int(len(h)),'train_feb_rows':int(tr.sum()),'march_rows':int(te.sum()),'feature_count':int(X.shape[1]),'player_feature_count':len(fs_player),'static_context_feature_count':int(static.shape[1]),'march':full,'march_early':early,'march_late':late,'individual_prior':prior,'wave44b_auc_reference':0.5672,'decision':decision,'next':'If found, soft-route Wave36 opponent ranking on March only; otherwise stop without Apr-Jun.'}
    OUTJ.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=['# Wave44c contextual player attack-mode audit','',f"- features: **{X.shape[1]}** = player priors {len(fs_player)} + static matchup {static.shape[1]}",f"- February train: **{int(tr.sum())}**",f"- March OOS: **{int(te.sum())}**",f"- March AUC: **{full['auc']:.4f}** / logloss **{full['logloss']:.4f}** / accuracy **{full['accuracy']:.3%}**",f"- March early AUC: **{early['auc']:.4f}** / late AUC: **{late['auc']:.4f}**",f"- individual-prior AUC reference: **{prior['auc']:.4f}**; Wave44b ML reference **0.5672**",f'- decision: **{decision}**','- September outcomes are not read.']
    OUTM.write_text('\n'.join(lines)+'\n',encoding='utf-8'); print('\n'.join(lines),flush=True)

if __name__=='__main__': main()
