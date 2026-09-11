#!/usr/bin/env python3
"""Run v298 with a closer, audited transfer of v288/v283 structure.

This wrapper intentionally leaves the v297/v298 evaluation and official-settlement
semantics unchanged.  It only replaces the v298 PRE threat/opponent feature builders:
- curated PLAYER_START-like opponent inputs instead of every symmetric b1_* column;
- race-relative candidate center/pct signals like v279;
- explicit wall/attack role gaps inspired by v288, using PRE-only fields;
- conditional THIRD pair-position, candidate diff and product structure like v282.

Jul/Aug remain excluded upstream; September outcomes are not read.  No meet_* feature
is admitted.  Boat-1 losses remain in the final exact-trifecta denominator.
"""
from __future__ import annotations
import numpy as np
import pandas as pd

import analyze_v298_1head_threat_listwise_trifecta5 as v298
import run_v297_1head_guard_trifecta5_research as settlement

SAFE=('grade','wr','local','motor','nst_strength','f_safety')
BOATS=v298.BOATS


def _scalar(x):
    return pd.to_numeric(pd.Series([x]),errors='coerce').iloc[0]


def curated_suffixes(d):
    """PRE-only PLAYER_START-like symmetric fields; fail closed on meet_* leakage."""
    out=[]
    for k in SAFE:
        if all(f'b{b}_{k}' in d for b in range(1,7)):
            out.append(k)
    for c in d.columns:
        if not c.startswith('b1_'):
            continue
        k=c[3:]
        if 'meet_' in k:
            continue
        # v279 PLAYER_START = ability + player + start + position.  In the
        # clean 1-head PRE table, nst_strength/f_safety are the start block;
        # prior-only player fields are the *_pl_* block.
        if '_pl_' in k and all(f'b{b}_{k}' in d for b in range(1,7)):
            out.append(k)
    out=sorted(set(out))
    if any('meet_' in x for x in out):
        raise RuntimeError('forbidden meet_* opponent feature')
    return out


def add_threat(d):
    q,made=v298.add_threat_original(d) if hasattr(v298,'add_threat_original') else v298._base_add_threat(d)
    # Direct PRE analogues of v288 wall/inside/attack decomposition.  No tuned
    # weights and no current exhibition/result fields are introduced.
    for k in SAFE:
        cols=[f'b{b}_{k}' for b in range(1,5)]
        if not all(c in q for c in cols):
            continue
        b1,b2,b3,b4=[pd.to_numeric(q[c],errors='coerce') for c in cols]
        feats={
            f'v298_role_b3_minus_b2_{k}':b3-b2,
            f'v298_role_b4_minus_b3_{k}':b4-b3,
            f'v298_role_b4_minus_b2_{k}':b4-b2,
            f'v298_role_attack34_minus_wall12_{k}':pd.concat([b3,b4],axis=1).max(axis=1)-pd.concat([b1,b2],axis=1).max(axis=1),
            f'v298_role_inside12_minus_attack34_{k}':pd.concat([b1,b2],axis=1).max(axis=1)-pd.concat([b3,b4],axis=1).max(axis=1),
        }
        for name,val in feats.items():
            q[name]=val;made.append(name)
    # Explicit interaction: a weak 1-2 start wall together with a strong 3-4
    # attacker is the core structural threat to a 1-head outcome.
    if all(f'b{b}_nst_strength' in q for b in range(1,5)):
        b1,b2,b3,b4=[pd.to_numeric(q[f'b{b}_nst_strength'],errors='coerce') for b in range(1,5)]
        wall=pd.concat([b1,b2],axis=1).max(axis=1)
        attack=pd.concat([b3,b4],axis=1).max(axis=1)
        q['v298_role_wall12_x_attack34_nst']=(wall-attack)*(attack-b1)
        made.append('v298_role_wall12_x_attack34_nst')
    return q,list(dict.fromkeys(made))


def cand_record(r,b,sufs,prefix=''):
    z={}
    if prefix:
        z[f'{prefix}pos_boat']=float(b)
        z[f'{prefix}pos_inner23']=float(b in (2,3))
        z[f'{prefix}pos_outer456']=float(b in (4,5,6))
        z[f'{prefix}pos_edge3']=float(b==3)
        z[f'{prefix}pos_edge4']=float(b==4)
        z[f'{prefix}pos_distance1']=float(b-1)
    else:
        z.update({'boat':int(b),'pos_boat':float(b),'pos_inner23':float(b in (2,3)),
                  'pos_outer456':float(b in (4,5,6)),'pos_edge3':float(b==3),
                  'pos_edge4':float(b==4),'pos_distance1':float(b-1)})
    for k in sufs:
        cv=_scalar(r.get(f'b{b}_{k}',np.nan));h=_scalar(r.get(f'b1_{k}',np.nan))
        z[f'{prefix}cand_{k}']=cv
        z[f'{prefix}diff1_{k}']=cv-h if pd.notna(cv) and pd.notna(h) else np.nan
        inner=[]
        for j in BOATS:
            if j>=b: break
            vv=_scalar(r.get(f'b{j}_{k}',np.nan))
            if pd.notna(vv): inner.append(float(vv))
        z[f'{prefix}innermax_{k}_minus_cand']=(max(inner)-cv) if inner and pd.notna(cv) else (0.0 if b==2 and pd.notna(cv) else np.nan)
    return z


def _add_race_relative(z,sufs):
    q=z.copy()
    for k in sufs:
        c=f'cand_{k}'
        if c not in q: continue
        x=pd.to_numeric(q[c],errors='coerce');q[c]=x
        g=q.assign(_x=x).groupby('race_code')['_x']
        med=g.transform('median')
        q[f'{c}__center']=x-med
        q[f'{c}__pct']=q.assign(_x=x).groupby('race_code')['_x'].rank(pct=True,method='average')
    return q


def second_long(d,sufs):
    rec=[]
    for _,r in d.iterrows():
        a2,a3=v298.actual23(r.actual_combo)
        if int(r.head_hit)!=1 or a2 not in BOATS or a3 not in BOATS:
            continue
        for b in BOATS:
            z={'date':r.date,'month':r.month,'race_code':str(r.race_code).zfill(12),
               'y2':int(b==a2),'actual2':a2,'actual3':a3}
            z.update(cand_record(r,b,sufs));rec.append(z)
    return _add_race_relative(pd.DataFrame(rec),sufs)


def conditional_long(d,sufs):
    rec=[]
    for _,r in d.iterrows():
        a2,a3=v298.actual23(r.actual_combo)
        if int(r.head_hit)!=1 or a2 not in BOATS or a3 not in BOATS:
            continue
        for s in BOATS:
            sr=cand_record(r,s,sufs,'s_')
            for t in BOATS:
                if t==s: continue
                tr=cand_record(r,t,sufs,'t_')
                z={'date':r.date,'month':r.month,'race_code':str(r.race_code).zfill(12),
                   'group_id':f'{str(r.race_code).zfill(12)}|{s}',
                   'second_boat':s,'third_boat':t,'train_group':int(s==a2),
                   'ycond':int(s==a2 and t==a3),'actual2':a2,'actual3':a3,
                   'pair_same_side1':float((s<=3 and t<=3) or (s>=4 and t>=4)),
                   'pair_second_inner23':float(s in (2,3)),'pair_second_outer456':float(s in (4,5,6)),
                   'pair_third_inner23':float(t in (2,3)),'pair_third_outer456':float(t in (4,5,6)),
                   'pair_adjacent':float(abs(s-t)==1),'pair_distance':float(abs(s-t)),
                   'pair_third_minus_second':float(t-s),
                   'pair_second_is2':float(s==2),'pair_second_is3':float(s==3),
                   'pair_second_is4':float(s==4),'pair_second_is5':float(s==5),'pair_second_is6':float(s==6)}
                z.update(sr);z.update(tr)
                for k in sufs:
                    tv=z.get(f't_cand_{k}',np.nan);sv=z.get(f's_cand_{k}',np.nan)
                    z[f'diff_{k}']=tv-sv if pd.notna(tv) and pd.notna(sv) else np.nan
                    z[f'prod_{k}']=tv*sv if pd.notna(tv) and pd.notna(sv) else np.nan
                rec.append(z)
    return pd.DataFrame(rec)


if __name__=='__main__':
    # Keep references so the upgraded head builder can call the original once.
    v298._base_add_threat=v298.add_threat
    v298.add_threat_original=v298.add_threat
    v298.add_threat=add_threat
    v298.suffixes=curated_suffixes
    v298.cand_record=cand_record
    v298.second_long=second_long
    v298.conditional_long=conditional_long
    settlement.AUDIT.clear()
    v298.v297.settle_full_after_freeze=settlement.settle_union_after_freeze
    print('v298 upgrade: curated PLAYER_START + v288 role gaps + v282 conditional pair structure',flush=True)
    v298.main()
