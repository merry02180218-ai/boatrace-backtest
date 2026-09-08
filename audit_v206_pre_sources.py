#!/usr/bin/env python3
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parent
FILES=['analysis_v108_1head_feasibility.csv','analysis_3attack_rows.csv','analysis_v165_3head_monthly_walkforward.csv','analysis_v191_3head_clean_pre_validation.csv','analysis_v195_3head_production_6month_backtest.csv']
for fn in FILES:
    p=ROOT/fn
    print('\n###',fn,'exists=',p.exists(),'size=',p.stat().st_size if p.exists() else None,flush=True)
    if not p.exists(): continue
    try:
        d=pd.read_csv(p,nrows=5)
        print('columns=',list(d.columns),flush=True)
        print('sample=',d.to_dict('records')[:2],flush=True)
    except Exception as e:
        print('ERROR',repr(e),flush=True)

print('\n### generator grep',flush=True)
needles=['3前回展示総合','3コース攻撃実績','analysis_3attack_rows','前回直線','節間ST']
for p in ROOT.rglob('*'):
    if not p.is_file() or p.suffix.lower() not in {'.py','.md','.yml','.yaml','.txt'}: continue
    try: txt=p.read_text(encoding='utf-8',errors='ignore')
    except: continue
    hits=[n for n in needles if n in txt]
    if hits:
        print(str(p.relative_to(ROOT)),hits,flush=True)
        for i,line in enumerate(txt.splitlines(),1):
            if any(n in line for n in needles): print(f'  L{i}: {line[:500]}',flush=True)
