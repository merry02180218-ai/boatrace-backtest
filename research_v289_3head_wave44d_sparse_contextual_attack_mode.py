from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score,log_loss,accuracy_score
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
import research_v289_3head_wave44c_contextual_player_attack_mode as base

SRC=Path('analysis_v289_3head_wave21_allrace_feature_settled.csv')
OUTJ=Path('research_v289_3head_wave44d_sparse_contextual_attack_mode.json')
OUTM=Path('research_v289_3head_wave44d_sparse_contextual_attack_mode.md')

def num(s): return pd.to_numeric(s.astype(str).str.replace('%','',regex=False),errors='coerce')
def gap(d,met,b):
    a=f'card__艇3_{met}'; c=f'card__艇{b}_{met}'
    if a not in d or c not in d: raise RuntimeError(f'missing {a} or {c}')
    return num(d[a])-num(d[c])
def score(y,p):
    return {'auc':float(roc_auc_score(y,p)),'logloss':float(log_loss(y,np.clip(p,1e-6,1-1e-6))),'accuracy':float(accuracy_score(y,(p>=.5).astype(int)))}
def main():
    d=pd.read_csv(SRC,dtype=str).fillna('')
    if d.date.max()>'2026-08-31': raise RuntimeError('September forbidden')
    target=d[(d.date>='2026-02-01')&(d.date<='2026-03-31')&(d.settle__head3_actual.astype(str)=='1')].copy()
    target['racer_id']=target['card__艇3_登録番号'].astype(str).str.strip()
    h,labels=base.build_history_and_labels(target)
    x=base.add_player_priors(target,h,labels)
    x['y']=(x['mode']=='MAKURI').astype(int)
    src=d.loc[x.src_index].copy(); src.index=x.index
    ctx=pd.DataFrame(index=x.index)
    families={
      'st12':['全国平均ST'],
      'win12':['全国勝率','当地勝率'],
      'motor12':['モーター2連対率','モーター3連対率'],
    }
    family_cols={}
    for fam,mets in families.items():
        cols=[]
        for met in mets:
            for b in (1,2):
                c=f'b3_minus_b{b}_{met}'; ctx[c]=gap(src,met,b); cols.append(c)
        family_cols[fam]=cols
    # Mechanically motivated compact combinations only; no Apr-Jun tuning.
    variants={
      'prior_only':[],
      'prior_st12':family_cols['st12'],
      'prior_win12':family_cols['win12'],
      'prior_motor12':family_cols['motor12'],
      'prior_st_win12':family_cols['st12']+family_cols['win12'],
      'prior_st_motor12':family_cols['st12']+family_cols['motor12'],
      'prior_st_win_motor12':family_cols['st12']+family_cols['win12']+family_cols['motor12'],
    }
    tr=x.date.str[:7].eq('2026-02'); te=x.date.str[:7].eq('2026-03')
    march=x.loc[te].sort_values(['date','race_code']); cut=len(march)//2
    out={}; prior=x.loc[te,'y1_makuri_share'].to_numpy(float); yte=x.loc[te,'y'].to_numpy()
    out['prior_only']={'features':0,'march':score(yte,prior)}
    # align early/late using sorted indices
    for name,cols in variants.items():
        if name=='prior_only': continue
        X=pd.concat([x[['y1_makuri_share','y1_logodds','y1_n']],ctx[cols]],axis=1).replace([np.inf,-np.inf],np.nan)
        model=make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),LogisticRegression(C=.08,max_iter=1200,class_weight='balanced'))
        model.fit(X.loc[tr],x.loc[tr,'y']); p=pd.Series(model.predict_proba(X.loc[te])[:,1],index=x.index[te])
        full=score(x.loc[te,'y'].to_numpy(),p.to_numpy())
        ps=p.loc[march.index]
        early=score(march.iloc[:cut].y.to_numpy(),ps.iloc[:cut].to_numpy()); late=score(march.iloc[cut:].y.to_numpy(),ps.iloc[cut:].to_numpy())
        out[name]={'features':int(X.shape[1]),'context_columns':cols,'march':full,'early':early,'late':late}
    best=max((k for k in out if k!='prior_only'),key=lambda k:out[k]['march']['auc'])
    bm=out[best]
    gate=bm['march']['auc']>=.60 and min(bm['early']['auc'],bm['late']['auc'])>=.54
    result={'wave':'44d-sparse-contextual-attack-mode','feb_train_rows':int(tr.sum()),'march_oos_rows':int(te.sum()),'individual_prior_reference_auc':float(out['prior_only']['march']['auc']),'variants':out,'best_variant':best,'decision':'MODE_SIGNAL_FOUND' if gate else 'NO_ADOPTION_STOP_ATTACK_MODE','september_outcomes_read':False}
    OUTJ.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=['# Wave44d sparse contextual attack-mode audit','',f"- Feb train: **{int(tr.sum())}** / March OOS: **{int(te.sum())}**",f"- individual prior AUC: **{out['prior_only']['march']['auc']:.4f}**"]
    for k,v in out.items():
        if k=='prior_only': continue
        lines.append(f"- {k}: AUC **{v['march']['auc']:.4f}**, logloss {v['march']['logloss']:.4f}, acc {v['march']['accuracy']:.3%}, early {v['early']['auc']:.4f}, late {v['late']['auc']:.4f}")
    lines += [f"- best: **{best}** / AUC **{bm['march']['auc']:.4f}**",f"- decision: **{result['decision']}**",'- September outcomes are not read.']
    OUTM.write_text('\n'.join(lines)+'\n',encoding='utf-8'); print('\n'.join(lines),flush=True)
if __name__=='__main__': main()
