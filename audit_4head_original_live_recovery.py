#!/usr/bin/env python3
"""Quantify races recovered by the venue-aware HEAD4 original-exhibition fix.

Compares:
OLD buggy LIVE gate:
  every labeled original-exhibition cell must be numeric for all six boats.
NEW/frozen research semantics:
  ignore a metric column when all six values are blank; any used column must be
  complete for all six boats. orig_avg is then built from only used columns.

The production selection is recomputed on the frozen 208R feature table.
No September outcomes are read.
"""
from __future__ import annotations
import csv, json, math, os
from pathlib import Path
import pandas as pd

import run_4head_120r_lastminute_fast as live

OUT=Path('/tmp/head4_original_live_recovery');OUT.mkdir(parents=True,exist_ok=True)

def ff(v):
    try:
        if v is None:return None
        s=str(v).strip()
        if s in ('','-','--','－'):return None
        x=float(s)
        return x if math.isfinite(x) else None
    except Exception:return None

def load_orig(root:Path,code:str):
    y,m,d=code[:4],code[4:6],code[6:8]
    p=root/'data'/'previews'/'original_exhibition'/y/m/f'{d}.csv'
    if not p.is_file():return {}
    with p.open(encoding='utf-8-sig',newline='') as f:
        for r in csv.DictReader(f):
            if str(r.get('レースコード','')).zfill(12)==code:
                return r
    return {}

def labeled_indices(row):
    out=[]
    for k in range(1,5):
        if str(row.get(f'計測項目{k}','')).strip():
            out.append(k)
    return out

def old_strict_ready(row):
    if not row:return False
    idx=labeled_indices(row)
    if not idx:return False
    return all(ff(row.get(f'艇{b}_値{k}')) is not None for k in idx for b in range(1,7))

def new_avg_ready(row):
    if not row:return False
    used=0
    for k in labeled_indices(row):
        vals=[ff(row.get(f'艇{b}_値{k}')) for b in range(1,7)]
        if not any(v is not None for v in vals):
            continue
        used+=1
        if not all(v is not None for v in vals):
            return False
    return used>0

def val(x):
    try:
        y=float(x)
        return y if math.isfinite(y) else None
    except Exception:return None

def production_selected(z:pd.DataFrame):
    art=live.load_newfeature_artifact()
    out=[]
    for _,r in z.iterrows():
        wall=val(r.get('wall_score'));stwall=val(r.get('st_wall_gap'))
        mwin=val(r.get('motor_win_diff_4v3'));m2=val(r.get('motor_2ren_diff_4v3'))
        raw={
          'hp':float(r.head_prob),'mass':float(r.opponent_mass),
          'st':float(r.st4_adv_inside),'orig':float(r.orig4_adv_inside),
          'market_conf':-math.log(max(float(r.composite_odds),1e-12)),
          'motor_win_rev':(-mwin if mwin is not None else None),
          'motor_2ren_rev':(-m2 if m2 is not None else None),
          'attack4':val(r.get('attack4_score')),
          'stwall_center':(-abs(stwall-.10) if stwall is not None else None),
          'wall_rev':(-wall if wall is not None else None),
        }
        score,_=live.score_newfeature_raw(raw,art)
        base=bool(r.base120)
        add=(not base and float(r.st4_adv_inside)>=-.80 and
             float(r.orig4_adv_inside)>=-.35 and
             score>=float(art['production_threshold']))
        out.append(base or add)
    return out

def main():
    table=Path(os.environ['EXPANDED_FEATURES_208'])
    root=Path(os.environ['BOATRACECSV_LOCAL_ROOT'])
    z=pd.read_csv(table,dtype={'race_code':str})
    z['race_code']=z.race_code.astype(str).str.zfill(12)
    z['base120']=z.base120.astype(str).str.lower().isin(('true','1'))
    if len(z)!=208 or int(z.base120.sum())!=120:
        raise RuntimeError('208/base120 drift')
    if any(z.month.astype(str).str.startswith('2026-09')):
        raise RuntimeError('SEPTEMBER ACCESS')
    z['production_selected']=production_selected(z)
    if int(z.production_selected.sum())!=156:
        raise RuntimeError(f"production count drift {int(z.production_selected.sum())}")

    old=[];new=[];labels=[]
    for code in z.race_code:
        r=load_orig(root,code)
        old.append(old_strict_ready(r))
        new.append(new_avg_ready(r))
        labels.append('|'.join(str(r.get(f'計測項目{k}','')).strip() for k in labeled_indices(r)))
    z['old_buggy_live_orig_ready']=old
    z['new_research_orig_ready']=new
    z['orig_labels']=labels
    z['recovered_by_fix']=z.new_research_orig_ready & ~z.old_buggy_live_orig_ready
    z['jcd']=z.race_code.str[8:10]

    # 208 is the structural/orig-ready research universe, so all must satisfy new semantics.
    if not z.new_research_orig_ready.all():
        bad=z.loc[~z.new_research_orig_ready,'race_code'].tolist()
        raise RuntimeError(f'new research readiness drift {bad[:10]}')

    rec=z[z.recovered_by_fix]
    recsel=rec[rec.production_selected]
    grp=(z.groupby('jcd',as_index=False)
          .agg(R=('race_code','size'),
               old_ready_R=('old_buggy_live_orig_ready','sum'),
               recovered_R=('recovered_by_fix','sum'),
               production_R=('production_selected','sum')))
    selgrp=(recsel.groupby('jcd',as_index=False).agg(recovered_production_R=('race_code','size')))
    grp=grp.merge(selgrp,on='jcd',how='left').fillna({'recovered_production_R':0})
    grp['recovered_production_R']=grp.recovered_production_R.astype(int)

    detail_cols=['race_code','month','jcd','orig_labels','base120','production_selected',
                 'old_buggy_live_orig_ready','new_research_orig_ready','recovered_by_fix']
    z[detail_cols].to_csv(OUT/'detail.csv',index=False)
    grp.to_csv(OUT/'venue_summary.csv',index=False)

    result={
      'universe_R':len(z),
      'production_R':int(z.production_selected.sum()),
      'old_buggy_live_orig_ready_R':int(z.old_buggy_live_orig_ready.sum()),
      'new_research_orig_ready_R':int(z.new_research_orig_ready.sum()),
      'recovered_decidable_R':int(z.recovered_by_fix.sum()),
      'recovered_production_selected_R':int((z.recovered_by_fix & z.production_selected).sum()),
      'recovered_by_venue':grp[grp.recovered_R.gt(0)].to_dict('records'),
      'interpretation':'recovered_production_selected_R estimates frozen production selections the old all-labeled-cells LIVE gate could have falsely blocked in this 208R historical universe',
      'SEPTEMBER_OUTCOMES_READ':False,
      'THRESHOLDS_CHANGED':False,
      'AUDIT_OK':True,
    }
    (OUT/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))
    print('HEAD4_ORIGINAL_LIVE_RECOVERY_AUDIT_OK')
    print('SEPTEMBER_UNREAD')

if __name__=='__main__':
    main()
