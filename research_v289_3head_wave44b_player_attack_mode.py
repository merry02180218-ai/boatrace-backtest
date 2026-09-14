from __future__ import annotations
import csv, io, json, urllib.request, time
from datetime import date, timedelta
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, log_loss, accuracy_score
from sklearn.linear_model import LogisticRegression
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline

BASE='https://raw.githubusercontent.com/BoatraceCSV/boatracecsv.github.io/main/'
SRC=Path('analysis_v289_3head_wave21_allrace_feature_settled.csv')
OUT=Path('analysis_v289_3head_wave44b_player_attack_mode.csv')
OUTJ=Path('research_v289_3head_wave44b_player_attack_mode.json')
OUTM=Path('research_v289_3head_wave44b_player_attack_mode.md')
START=date(2025,2,1); END=date(2026,3,31)


def fetch_rows(path, attempts=3):
    for i in range(attempts):
        try:
            with urllib.request.urlopen(BASE+path,timeout=30) as r:
                return list(csv.DictReader(io.StringIO(r.read().decode('utf-8-sig'))))
        except Exception:
            time.sleep(.4*(i+1))
    return []

def norm_code(x):
    s=''.join(ch for ch in str(x or '') if ch.isdigit()); return s.zfill(12) if s else ''

def pick(row, keys):
    for k in keys:
        v=str(row.get(k,'')).strip()
        if v: return v
    return ''

def norm_mode(x):
    s=str(x).replace(' ','').replace('　','')
    if 'まくり差し' in s: return 'MAKURI_SASHI'
    if 'まくり' in s: return 'MAKURI'
    return 'OTHER'

def day_rows(d):
    ymd=d.strftime('%Y/%m/%d')
    return fetch_rows(f'data/results/realtime/{ymd}.csv')

def main():
    d=pd.read_csv(SRC,dtype=str).fillna('')
    if d.date.max()>'2026-08-31': raise RuntimeError('September forbidden')
    # Stable racer id for boat3 from race-card columns.
    idcols=[c for c in d.columns if c.startswith('card__') and ('3号艇' in c or '_3_' in c or c.endswith('_3')) and ('登録番号' in c or '登番' in c)]
    if not idcols:
        idcols=[c for c in d.columns if c.startswith('card__') and ('登録番号' in c or '登番' in c)]
    if not idcols: raise RuntimeError('stable racer ID column not found')
    idcol=idcols[0]
    target=d[(d.date>='2026-02-01')&(d.date<='2026-03-31')&(d.settle__head3_actual.astype(str)=='1')].copy()
    target['racer_id']=target[idcol].astype(str).str.strip()
    wanted=set(target.race_code.map(norm_code)); labels={}
    # Build chronological history from official-derived BoatraceCSV realtime result records.
    hist=[]; cur=START
    while cur<=END:
        for r in day_rows(cur):
            code=norm_code(r.get('レースコード',''))
            winner=pick(r,['1着_艇番'])
            mode=norm_mode(pick(r,['決まり手','勝利決まり手','1着_決まり手']))
            # Winner racer id: prefer explicit winner registration; otherwise map winner boat field.
            rid=pick(r,['1着_登録番号','1着_登番'])
            if not rid and winner:
                rid=pick(r,[f'{winner}号艇_登録番号',f'{winner}号艇_登番',f'登録番号_{winner}',f'登番_{winner}'])
            if rid and winner:
                hist.append((cur.isoformat(),code,rid,str(winner),mode))
            if code in wanted: labels[code]=mode
        cur+=timedelta(days=1)
    h=pd.DataFrame(hist,columns=['date','race_code','racer_id','winner_boat','mode'])
    if h.empty: raise RuntimeError('no historical result rows with racer id')
    # Chronological leakage-safe priors. Only prior wins from the same racer are used.
    rows=[]
    for _,r in target.sort_values(['date','race_code']).iterrows():
        code=norm_code(r.race_code); mode=labels.get(code,'OTHER')
        if mode not in ('MAKURI','MAKURI_SASHI'): continue
        prior=h[(h.racer_id==r.racer_id)&(h.date<r.date)&(h.winner_boat=='3')&h.mode.isin(['MAKURI','MAKURI_SASHI'])]
        recent=prior[prior.date>=str(date.fromisoformat(r.date)-timedelta(days=365))]
        def feats(q,pfx):
            n=len(q); m=int((q.mode=='MAKURI').sum()); s=int((q.mode=='MAKURI_SASHI').sum())
            # Beta(1,1) smoothing.
            return {f'{pfx}_n':n,f'{pfx}_makuri':m,f'{pfx}_makurizashi':s,f'{pfx}_makuri_share':(m+1)/(n+2),f'{pfx}_logodds':float(np.log((m+1)/(s+1)))}
        z={'date':r.date,'race_code':r.race_code,'racer_id':r.racer_id,'mode':mode}; z.update(feats(prior,'career')); z.update(feats(recent,'y1')); rows.append(z)
    x=pd.DataFrame(rows)
    if x.empty: raise RuntimeError('no labeled MAKURI/MAKURI-SASHI target rows')
    x['y']=(x.mode=='MAKURI').astype(int)
    tr=x[x.date.str[:7]=='2026-02'].copy(); te=x[x.date.str[:7]=='2026-03'].copy()
    fs=['career_n','career_makuri_share','career_logodds','y1_n','y1_makuri_share','y1_logodds']
    if tr.y.nunique()<2 or te.y.nunique()<2: raise RuntimeError('both mode classes required')
    model=make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),LogisticRegression(C=.2,max_iter=1000,class_weight='balanced'))
    model.fit(tr[fs],tr.y); p=model.predict_proba(te[fs])[:,1]; pred=(p>=.5).astype(int)
    auc=float(roc_auc_score(te.y,p)); ll=float(log_loss(te.y,p)); acc=float(accuracy_score(te.y,p))
    # Pure individual-history prior is also audited without ML.
    priorp=te.y1_makuri_share.to_numpy(float); prior_auc=float(roc_auc_score(te.y,priorp)); prior_ll=float(log_loss(te.y,np.clip(priorp,1e-6,1-1e-6)))
    te=te.assign(pred_p_makuri=p,pred_mode=np.where(pred==1,'MAKURI','MAKURI_SASHI'))
    te.to_csv(OUT,index=False,encoding='utf-8-sig')
    byn={}
    for ncut in [0,3,5,10]:
        q=te[te.y1_n>=ncut]
        byn[str(ncut)]={'rows':len(q),'auc':float(roc_auc_score(q.y,q.pred_p_makuri)) if len(q) and q.y.nunique()==2 else None,'accuracy':float(accuracy_score(q.y,(q.pred_p_makuri>=.5).astype(int))) if len(q) else None}
    out={'wave':'44b-player-attack-mode','racer_id_column':idcol,'train_feb_rows':len(tr),'march_rows':len(te),'march_makuri':int(te.y.sum()),'march_makuri_sashi':int((1-te.y).sum()),'march_auc':auc,'march_logloss':ll,'march_accuracy':acc,'individual_prior_auc':prior_auc,'individual_prior_logloss':prior_ll,'by_prior_3course_win_history_n':byn,'decision':'MODE_SIGNAL_FOUND' if auc>=.60 or prior_auc>=.60 else 'MODE_SIGNAL_WEAK','next':'If MODE_SIGNAL_FOUND, integrate predicted mode probabilities into Wave36 opponent ranker; otherwise stop without Apr-Jun.'}
    OUTJ.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    md=['# Wave44b player-specific attack-mode audit','',f'- racer id column: `{idcol}`',f'- February train: **{len(tr)}** labeled boat3-head MAKURI/MAKURI-SASHI rows',f'- March OOS: **{len(te)}** rows (MAKURI {int(te.y.sum())}, MAKURI-SASHI {int((1-te.y).sum())})',f'- March ML AUC: **{auc:.4f}** / logloss **{ll:.4f}** / accuracy **{acc:.3%}**',f'- Individual 1-year prior AUC: **{prior_auc:.4f}** / logloss **{prior_ll:.4f}**',f"- decision: **{out['decision']}**",'- Actual current-race kimarite is evaluation target only; all history features are strictly prior-date.','- September outcomes are not read.']
    OUTM.write_text('\n'.join(md)+'\n',encoding='utf-8'); print('\n'.join(md),flush=True)
if __name__=='__main__': main()
