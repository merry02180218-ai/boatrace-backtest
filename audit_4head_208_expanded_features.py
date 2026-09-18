#!/usr/bin/env python3
"""Build causal expanded features for the 208R odds-covered 4HEAD universe.

Inputs:
- frozen Stage2 race_detail_226.csv (208 verified-odds rows)
- frozen Stage1 selected_pool.csv (226 rows, carries causal motor features)
- archived same-day exhibition CSVs for formal wall3 semantics

No September outcomes are read. Production is unchanged.
"""
from __future__ import annotations
from pathlib import Path
import csv, json, os
import numpy as np
import pandas as pd
import run_v352_1head_wall3_risk_audit as wall1

OUT=Path('/tmp/head4_208_expanded_features'); OUT.mkdir(parents=True,exist_ok=True)
MONTHS=('2026-04','2026-05','2026-06','2026-07','2026-08')

_local_root=os.environ.get('BOATRACECSV_LOCAL_ROOT')
if _local_root:
    root=Path(_local_root)
    def _rows(path):
        p=root/path
        if not p.is_file(): return []
        try:
            with p.open(encoding='utf-8-sig',newline='') as fh:
                return list(csv.DictReader(fh))
        except Exception:
            return []
    wall1.rows=_rows

def met(q):
    n=len(q)
    return {
      'R':int(n),
      'head4':int(q.head4.sum()) if n else 0,
      'head4_rate':100*float(q.head4.mean()) if n else np.nan,
      'exact3':int(q.raw_hit.sum()) if n else 0,
      'ROI':100*float(q.payout_if_bet.sum())/(10000*n) if n else np.nan,
    }

def main():
    detail=os.environ.get('RACE_DETAIL_226')
    pool=os.environ.get('STAGE1_POOL')
    if not detail or not pool: raise RuntimeError('RACE_DETAIL_226/STAGE1_POOL missing')

    z=pd.read_csv(detail,dtype={'race_code':str})
    z['race_code']=z.race_code.astype(str).str.zfill(12)
    if len(z)!=208: raise RuntimeError(f'Stage2 verified-odds rows drift {len(z)} != 208')
    if any(z.month.astype(str).str.startswith('2026-09')): raise RuntimeError('SEPTEMBER ACCESS')
    if int(z.base120.astype(bool).sum())!=120: raise RuntimeError('base120 drift')

    p=pd.read_csv(pool,dtype={'race_code':str})
    p['race_code']=p.race_code.astype(str).str.zfill(12)
    need_motor=['race_code','motor_win_diff_4v3','motor_2ren_diff_4v3']
    miss=[c for c in need_motor if c not in p.columns]
    if miss: raise RuntimeError(f'Stage1 motor columns missing {miss}')
    pm=p[need_motor].drop_duplicates('race_code')
    z=z.merge(pm,on='race_code',how='left',validate='one_to_one')

    wall=wall1.exhibition_wall(set(z.race_code))
    wall['race_code']=wall.race_code.astype(str).str.zfill(12)
    keep=['race_code','wall_exhibition_ready','ex_wall_gap','st_wall_gap',
          'straight_wall_gap','avg_wall_gap','ex_wall_score','attack4_score',
          'wall3_score','ex_wall_votes']
    z=z.merge(wall[keep],on='race_code',how='left',validate='one_to_one')
    z=z.rename(columns={'ex_wall_score':'wall_score'})
    z['wall_ready']=z.wall_exhibition_ready.fillna(False).astype(bool)
    z['open_risk']=(-pd.to_numeric(z.wall_score,errors='coerce')).clip(lower=0)
    z['block_risk']=(pd.to_numeric(z.wall_score,errors='coerce')).clip(lower=0)
    z['motor_win_diff_4v3']=pd.to_numeric(z.motor_win_diff_4v3,errors='coerce')
    z['motor_2ren_diff_4v3']=pd.to_numeric(z.motor_2ren_diff_4v3,errors='coerce')

    base=z[z.base120.astype(bool)].copy()
    non=z[~z.base120.astype(bool)].copy()
    coverage={
      'all_R':int(len(z)),
      'base120_R':int(len(base)),
      'nonbase_R':int(len(non)),
      'wall_ready_all_R':int(z.wall_ready.sum()),
      'wall_ready_nonbase_R':int(non.wall_ready.sum()),
      'motor_win_ready_all_R':int(z.motor_win_diff_4v3.notna().sum()),
      'motor_win_ready_nonbase_R':int(non.motor_win_diff_4v3.notna().sum()),
      'motor_2ren_ready_all_R':int(z.motor_2ren_diff_4v3.notna().sum()),
      'motor_2ren_ready_nonbase_R':int(non.motor_2ren_diff_4v3.notna().sum()),
    }

    strata=[]
    specs=[
      ('wall_score','wall_ready',[-2,-.30,-.10,0,.10,.30,2]),
      ('attack4_score','wall_ready',[-3,-.50,-.20,0,.20,.50,3]),
      ('st_wall_gap','wall_ready',[-3,-.60,-.20,0,.20,.60,3]),
      ('motor_win_diff_4v3',None,[-1,-.10,-.03,0,.03,.10,1]),
      ('motor_2ren_diff_4v3',None,[-100,-10,-3,0,3,10,100]),
    ]
    for scope,q0 in [('ALL',z),('NONBASE',non)]:
        for feat,ready,bins in specs:
            q=q0.copy()
            if ready: q=q[q[ready].fillna(False).astype(bool)].copy()
            x=pd.to_numeric(q[feat],errors='coerce')
            q=q[x.notna()].copy(); x=pd.to_numeric(q[feat],errors='coerce')
            if q.empty: continue
            q['band']=pd.cut(x,bins=bins,include_lowest=True,duplicates='drop')
            for band,g in q.groupby('band',observed=True):
                strata.append({'scope':scope,'feature':feat,'band':str(band),**met(g)})
    st=pd.DataFrame(strata)

    z.to_csv(OUT/'expanded_features_208.csv',index=False)
    st.to_csv(OUT/'feature_strata.csv',index=False)
    result={
      'coverage':coverage,
      'base120':met(base),
      'nonbase88':met(non),
      'wall_feature_semantics':'run_v352_1head_wall3_risk_audit.exhibition_wall',
      'motor_feature_semantics':'Stage1 causal prior motor win + official race-card motor 2-ren, both 4v3',
      'SEPTEMBER_OUTCOMES_READ':False,
      'PRODUCTION_CHANGED':False,
      'AUDIT_OK':True,
    }
    (OUT/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,default=str)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2,default=str),flush=True)
    print('\nNONBASE FEATURE STRATA',flush=True)
    print(st[st.scope.eq('NONBASE')].to_string(index=False),flush=True)
    print('HEAD4_208_EXPANDED_FEATURES_OK',flush=True)
    print('SEPTEMBER_UNREAD',flush=True)

if __name__=='__main__': main()
