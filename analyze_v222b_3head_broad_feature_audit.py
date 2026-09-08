#!/usr/bin/env python3
"""v222b: implementation-only fix for duplicate v222 head feature columns."""
import analyze_v222_3head_broad_feature_audit as v222


def uniq(a):
    return list(dict.fromkeys(a))


def numeric_ok(d,fs,rate=.70):
    return [c for c in uniq(fs) if c in d.columns and v222.pd.to_numeric(d[c],errors='coerce').notna().mean()>=rate]


def head_groups(d,basefs):
    player=v222.cols(d,'b3_pl_');hist=v222.cols(d,'b3_vh_')
    rel=[c for c in d.columns if c.startswith(('c_b3_minus_','c_b3_inside_','c_b3_outside_'))]
    cur=[c for c in v222.cols(d,'c_b3_') if not c.startswith(('c_b3_minus_','c_b3_inside_','c_b3_outside_'))]
    cur += [c for c in d.columns if c.startswith(('c_wall','c_attack3','c_outer','c_ex_spread','c_st_spread','c_turn_spread','c_straight_spread'))]
    return {
      'PLAYER':uniq(list(basefs)+player),
      'PLAYER+CURRENT':uniq(list(basefs)+player+cur),
      'PLAYER+CURRENT+REL':uniq(list(basefs)+player+cur+rel),
      'PLAYER+HISTORY+CURRENT':uniq(list(basefs)+player+hist+cur),
      'PLAYER+HISTORY+CURRENT+REL':uniq(list(basefs)+player+hist+cur+rel),
      'PRIOR12':uniq(list(basefs)+hist),
      'PRIOR12+CURRENT':uniq(list(basefs)+hist+cur),
      'PRIOR12+CURRENT+REL':uniq(list(basefs)+hist+cur+rel),
    }

v222.numeric_ok=numeric_ok
v222.head_groups=head_groups

if __name__=='__main__':
    v222.main()
