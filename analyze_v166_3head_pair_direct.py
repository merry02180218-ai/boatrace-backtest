#!/usr/bin/env python3
"""v166 direct ordered-pair model for 3-head tickets.

Runs only after v165 has produced frozen monthly walk-forward 3-head probabilities.
This scaffold is intentionally conservative: it refuses to run unless the repository
contains an explicit per-race ordered trifecta/result source and lane-level opponent
features, preventing accidental leakage or fabricated pair features.
"""
from pathlib import Path
import json
import pandas as pd

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'summary_v166_3head_pair_direct.md'
SCHEMA=ROOT/'analysis_v166_3head_pair_schema.json'

CANDS=[ROOT/'analysis_v108_1head_feasibility.csv',ROOT/'analysis_v90_model_candidates.csv',ROOT/'analysis_v83_candidates.csv']

src=None; df=None
for p in CANDS:
    if p.exists():
        x=pd.read_csv(p)
        if len(x): src=p; df=x; break
if df is None:
    raise SystemExit('No canonical race feature source found')

result_cols=[c for c in ['result','trifecta','kumi','combination','first','second','third'] if c in df.columns]
opp=[]
for lane in [1,2,4,5,6]:
    for stem in ['grade','wr','local','motor','waku_wr','nst_strength','ex','st','lap','turn','straight','orig_avg','direct','score','threat']:
        for c in [f'{stem}{lane}',f'{stem}_{lane}',f'boat{lane}_{stem}',f'lane{lane}_{stem}']:
            if c in df.columns: opp.append(c)
status='READY_FOR_IMPLEMENTATION' if result_cols and len(set(opp))>=10 else 'INSUFFICIENT_EXPLICIT_PAIR_SCHEMA'
SCHEMA.write_text(json.dumps({'source':src.name,'status':status,'result_cols':result_cols,'opponent_features':sorted(set(opp)),'columns':list(df.columns)},ensure_ascii=False,indent=2),encoding='utf-8')
if status!='READY_FOR_IMPLEMENTATION':
    OUT.write_text('# v166 3-head direct pair model\n\n- status: schema audit only\n- reason: explicit ordered-result/opponent feature schema is insufficient; no ticket model was fabricated.\n',encoding='utf-8')
    print(OUT.read_text())
    raise SystemExit(0)
OUT.write_text('# v166 3-head direct pair model\n\n- status: explicit schema found; implement pair training after v165 head model validation.\n',encoding='utf-8')
print(OUT.read_text())
