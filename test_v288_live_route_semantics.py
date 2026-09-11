#!/usr/bin/env python3
"""Verify the production LIVE route selector matches adopted v288 semantics."""
from itertools import product
import run_20260911_3head_v288_live as live


def expected(v243_pass,buyable,s_cond,a_cond,b_cond):
    s=bool(v243_pass and s_cond)
    a=bool(buyable and (not s) and a_cond)
    b=bool(buyable and (not s) and (not a) and b_cond)
    route='S' if s else ('A' if a else ('B' if b else None))
    return route,s,a,b


def main():
    checked=0
    for vals in product([False,True], repeat=5):
        got=live.select_v288_route(*vals)
        exp=expected(*vals)
        assert got==exp,(vals,got,exp)
        checked+=1
    print(f'V288_LIVE_ROUTE_PARITY_OK cases={checked}')

if __name__=='__main__':
    main()
