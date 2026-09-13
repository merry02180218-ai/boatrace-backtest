#!/usr/bin/env python3
"""Assemble the frozen HEAD4 V291 VARN runner input from current-day causal bundles.

Input JSON keys:
 race_code, PRE, POST, env_primitives, a_features, boats
No network/outcome/odds access.  The emitted JSON is consumed unchanged by
run_4head_v291_varn_live.py, which owns official pre-deadline odds and JPY10,000 Dutch.
"""
from __future__ import annotations
import argparse,json,math
from pathlib import Path
from build_4head_env_entry_live import assemble as assemble_env
from build_4head_a_live_live import assemble as assemble_a
from build_4head_v283_rows_live import derive as derive_v283
from head4_v291_downstream_inference import load_artifact as load_down,score_env_entry,score_second,score_conditional_third
from head4_v273_a_live_inference import load_artifact as load_a,classify

class AutoInputError(RuntimeError):pass

def _p(name,x):
    try:v=float(x)
    except Exception as e: raise AutoInputError(f'invalid {name}') from e
    if not math.isfinite(v) or not 0<=v<=1: raise AutoInputError(f'invalid {name}')
    return v

def assemble(src):
    code=str(src.get('race_code','')).zfill(12)
    if len(code)!=12 or not code.isdigit(): raise AutoInputError('invalid race_code')
    pre=_p('PRE',src.get('PRE'));post=_p('POST',src.get('POST'))
    down=load_down();aa=load_a()
    env=assemble_env(src.get('env_primitives') or {},pre,post,down);envp=score_env_entry(env,down)
    ar=assemble_a(src.get('a_features') or {},aa);cls=classify(pre,post,envp,ar,aa)
    second,cond=derive_v283({'boats':src.get('boats') or {}},down)
    p2=score_second(second,down);pc=score_conditional_third(cond,down)
    out={'race_code':code,'PRE':pre,'POST':post,'ENV_ENTRY':envp,
         'p2':{str(k):v for k,v in p2.items()},'cond':{f'{s}>{t}':v for (s,t),v in pc.items()}}
    # final runner requires the frozen 17 A keys at top level for A classification.
    out.update(ar)
    out['_auto_meta']={'policy':'HEAD4_V291_COMP7_VARN_F4_N16','frozen_training_cutoff':'2026-06-30',
      'result_blind':True,'jul_aug_labels_used':False,'september_labels_used':False,'v96_used':False,
      'classification_preview':cls}
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--input-json',required=True);ap.add_argument('--out',required=True);a=ap.parse_args()
    src=json.loads(Path(a.input_json).read_text(encoding='utf-8'));out=assemble(src)
    Path(a.out).write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':'READY','path':a.out,'race_code':out['race_code'],'classification':out['_auto_meta']['classification_preview']},ensure_ascii=False))
if __name__=='__main__':main()
