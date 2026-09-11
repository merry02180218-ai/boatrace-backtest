#!/usr/bin/env python3
"""v291 PRE input fetcher: keep races even when one Waku10 history row is absent."""
import fetch_kyoteibiyori_v288_pre_inputs as base

_orig_find_kako = base.find_kako

def tolerant_find_kako(entries, pn, course):
    a = _orig_find_kako(entries, pn, course)
    if a:
        return a
    # Match historical parser semantics for missing Waku10 stats: blank fields
    # later fall back to national ST / 0 win rate / 3.5 start-order defaults.
    return {'player_no': pn, 'course': course, '_v291_missing_kako': 1}

base.find_kako = tolerant_find_kako

if __name__ == '__main__':
    base.main()
