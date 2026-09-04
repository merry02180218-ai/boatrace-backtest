"""v108b: runtime/data-source fix for v108 1-head feasibility.

The original v108 no-leak design is preserved. Two implementation fixes only:
1) replace sklearn/pandas ColumnTransformer with an explicit numeric matrix;
2) load historical waku10 through the repo's validated historical_data_loader,
   so old months are not silently dropped when saved BoatraceCSV files are absent.
"""
from __future__ import annotations

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

import analyze_v108_1head_feasibility as v108
from historical_data_loader import waku10_rows

VENUES=[f'{i:02d}' for i in range(1,25)]


def xmatrix(rs,with_venue=False):
    out=[]
    for r in rs:
        row=[]
        for k in v108.NUM_FEATURES:
            try: row.append(float(r.get(k,0) or 0))
            except Exception: row.append(0.0)
        if with_venue:
            vv=str(r.get('venue','')).zfill(2)
            row.extend(1.0 if vv==v else 0.0 for v in VENUES)
        out.append(row)
    nfeat=len(v108.NUM_FEATURES)+(24 if with_venue else 0)
    if not out:return np.empty((0,nfeat),dtype=float)
    return np.asarray(out,dtype=float)


def build_pipe(with_venue=False):
    p=Pipeline([
        ('scale',StandardScaler()),
        ('lr',LogisticRegression(C=.5,max_iter=1500,solver='lbfgs')),
    ])
    p._v108_with_venue=bool(with_venue)
    return p


def fit_variant(train,with_venue):
    if not train:
        raise RuntimeError('v108 training set is empty; check historical source coverage')
    p=build_pipe(with_venue)
    p.fit(xmatrix(train,with_venue),[r['head_hit'] for r in train])
    return p


def predict(model,rs):
    if not rs:return np.array([])
    w=bool(getattr(model,'_v108_with_venue',False))
    return model.predict_proba(xmatrix(rs,w))[:,1]


def feature_importance(pipe):
    try:
        w=bool(getattr(pipe,'_v108_with_venue',False))
        names=list(v108.NUM_FEATURES)+([f'venue_{x}' for x in VENUES] if w else [])
        coef=pipe.named_steps['lr'].coef_[0]
        z=sorted(zip(names,coef),key=lambda x:abs(x[1]),reverse=True)
        return z[:15]
    except Exception:
        return []


def fetch_feature_day(d):
    """Same v108 pre-race feature fetch, but historical waku10 uses validated fallback."""
    ymd=d.strftime('%Y/%m/%d')
    wrows,wsrc=waku10_rows(str(d))
    return d,{
      'cards':v108.rows(f'data/programs/race_cards/{ymd}.csv'),
      'waku':wrows,
      'waku_source':wsrc,
      'tkz':v108.rows(f'data/previews/tkz/{ymd}.csv'),
      'stt':v108.rows(f'data/previews/stt/{ymd}.csv'),
      'orig':v108.rows(f'data/previews/original_exhibition/{ymd}.csv'),
    }


# Patch implementation only; v108 feature construction, freeze-before-result order,
# development split, fixed cuts, settlement and report logic remain unchanged.
v108.build_pipe=build_pipe
v108.fit_variant=fit_variant
v108.predict=predict
v108.feature_importance=feature_importance
v108.fetch_feature_day=fetch_feature_day

if __name__=='__main__':
    v108.main()
