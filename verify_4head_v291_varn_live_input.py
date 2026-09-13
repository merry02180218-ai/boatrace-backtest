#!/usr/bin/env python3
from __future__ import annotations
import math
from assemble_4head_v291_varn_live_input import assemble
from build_4head_env_entry_live import PRIMITIVES
from head4_v291_downstream_inference import BOATS,load_artifact
from head4_v273_a_live_inference import load_artifact as load_a
import run_20260911_4head_v291_live as base
from run_4head_v291_varn_live import full_order,pick_n

def main():
    d=load_artifact();a=load_a()
    envst=d['ENV_ENTRY'];emed=dict(zip(envst['features'],envst['imputer_median']))
    env={k:emed[k] for k in PRIMITIVES}
    ast=a['A_SCORE'];af=dict(zip(ast['features'],ast['imputer_median']))
    fs=d['v283_SECOND']['features'];med=d['v283_SECOND']['imputer_median'];b0=dict(zip(fs,med))
    boats={str(b):dict(b0) for b in BOATS};boats['4']={c:.5 for c in ('cur_ex','cur_st','cur_orig_lap','cur_orig_turn','cur_orig_straight','cur_orig_avg')}
    for b in BOATS:
        for c in ('cur_ex','cur_st','cur_orig_lap','cur_orig_turn','cur_orig_straight','cur_orig_avg'):boats[str(b)][c]=.45+.005*b
    out=assemble({'race_code':'202609130101','PRE':.29,'POST':.26,'env_primitives':env,'a_features':af,'boats':boats})
    assert out['race_code']=='202609130101' and 0<out['ENV_ENTRY']<1
    p2=base.parse_p2(out['p2']);pc=base.parse_cond(out['cond']);order=full_order(p2,pc)
    assert len(order)==20 and len(set(order))==20
    # Synthetic odds only test immutable variable-N mathematics; no network/market data.
    odds={t:100.0 for t in order};sel=pick_n(order,odds)
    assert sel['entered'] is True and sel['n']==16
    for k in ast['features']: assert k in out
    m=out['_auto_meta'];assert m['jul_aug_labels_used'] is False and m['september_labels_used'] is False and m['v96_used'] is False
    print('HEAD4 v291 VARN assembled-input contract PASS')
if __name__=='__main__':main()
