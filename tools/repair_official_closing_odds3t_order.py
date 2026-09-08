#!/usr/bin/env python3
"""Repair legacy official closing 3T odds archives whose 120 values were
correctly extracted from the official table but labeled with the wrong combo order.

This is lossless: it reassigns the existing 120 values from legacy column order
(itertools.permutations) to the official table display order. Already-repaired
rows are skipped via odds_mapping_version=official_table_v2.
"""
from __future__ import annotations
import csv, itertools
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OD=ROOT/'data/official_closing_odds3t'
VERSION='official_table_v2'
OLD=[f'{a}-{b}-{c}' for a,b,c in itertools.permutations(range(1,7),3)]

def display_order():
    out=[]
    for second_idx in range(5):
        for third_idx in range(4):
            for first in range(1,7):
                seconds=[x for x in range(1,7) if x!=first]
                second=seconds[second_idx]
                thirds=[x for x in range(1,7) if x not in (first,second)]
                third=thirds[third_idx]
                out.append(f'{first}-{second}-{third}')
    assert len(out)==120 and len(set(out))==120
    return out
NEW=display_order()

def repair_file(p:Path):
    with p.open(newline='',encoding='utf-8') as f:
        r=csv.DictReader(f); rows=list(r); fields=r.fieldnames or []
    if not rows: return (0,0)
    if not all(c in fields for c in OLD):
        raise RuntimeError(f'{p}: missing legacy combo columns')
    changed=0
    for row in rows:
        if row.get('odds_mapping_version')==VERSION:
            continue
        vals=[row[c] for c in OLD]
        for c,v in zip(NEW,vals): row[c]=v
        row['odds_mapping_version']=VERSION
        changed+=1
    if changed:
        meta=[f for f in fields if f not in OLD and f!='odds_mapping_version']
        out_fields=meta+['odds_mapping_version']+OLD
        tmp=p.with_suffix('.tmp')
        with tmp.open('w',newline='',encoding='utf-8') as f:
            w=csv.DictWriter(f,fieldnames=out_fields); w.writeheader(); w.writerows(rows)
        tmp.replace(p)
    return (len(rows),changed)

def main():
    files=sorted(OD.glob('*/*/*.csv')); total=changed=0
    for p in files:
        n,c=repair_file(p); total+=n; changed+=c
    print(f'files={len(files)} rows={total} repaired_rows={changed} version={VERSION}')
    # Deterministic mapping sanity checks from official table layout.
    expected=['1-2-3','2-1-3','3-1-2','4-1-2','5-1-2','6-1-2','1-2-4','2-1-4']
    assert NEW[:8]==expected, (NEW[:8],expected)

if __name__=='__main__': main()
