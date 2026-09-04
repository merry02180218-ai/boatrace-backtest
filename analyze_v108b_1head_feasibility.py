"""v108b: runtime fix for v108 sklearn/pandas ColumnTransformer compatibility.

All v108 data/no-leak logic is unchanged. Only the model input encoding is replaced
with an explicit numeric matrix: NUM_FEATURES + optional 24 venue one-hot columns.
"""
from __future__ import annotations

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

import analyze_v108_1head_feasibility as v108

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
    return np.asarray(out,dtype=float)


def build_pipe(with_venue=False):
    p=Pipeline([
        ('scale',StandardScaler()),
        ('lr',LogisticRegression(C=.5,max_iter=1500,solver='lbfgs')),
    ])
    p._v108_with_venue=bool(with_venue)
    return p


def fit_variant(train,with_venue):
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


# Patch only model-matrix functions; all feature freezing, result ordering, splits,
# thresholds, evaluation and report generation remain exactly v108.
v108.build_pipe=build_pipe
v108.fit_variant=fit_variant
v108.predict=predict
v108.feature_importance=feature_importance

if __name__=='__main__':
    v108.main()
