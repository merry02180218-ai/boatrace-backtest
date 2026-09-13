#!/usr/bin/env python3
"""One-command AUTO LIVE bridge for frozen HEAD4 v291 VARN.

Accept either the already-normalized result-blind bundle or the stricter current
causal source schema.  Source mode first derives the frozen A-LIVE/v283 bundle,
then assembles exact model input and hands it to the existing production market/
ticket runner. The final runner remains the sole owner of official pre-deadline
odds, V291 Top4 composite entry, variable N=4..16 and exact JPY10,000 Dutch.
"""
from __future__ import annotations
import argparse,json,subprocess,sys,tempfile
from pathlib import Path
from assemble_4head_v291_varn_live_input import assemble
from build_4head_current_bundle import build as build_current_bundle

POLICY='HEAD4_V291_COMP7_VARN_F4_N16'

def _load(path:str)->dict:
    return json.loads(Path(path).read_text(encoding='utf-8'))

def prepare(bundle_path:str|None,out_path:str,source_path:str|None=None,bundle_out:str|None=None)->dict:
    if bool(bundle_path)==bool(source_path):
        raise ValueError('exactly one of bundle_path/source_path is required')
    if source_path:
        bundle=build_current_bundle(_load(source_path))
        if bundle_out:
            Path(bundle_out).write_text(json.dumps(bundle,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        src=bundle
    else:
        src=_load(str(bundle_path))
    out=assemble(src)
    Path(out_path).write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return out

def main():
    ap=argparse.ArgumentParser()
    g=ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--bundle-json')
    g.add_argument('--source-json',help='strict result-blind flat/current source consumed by build_4head_current_bundle.py')
    ap.add_argument('--date',required=True)
    ap.add_argument('--jcd',required=True,type=int)
    ap.add_argument('--race',required=True,type=int)
    ap.add_argument('--deadline-jst',required=True)
    ap.add_argument('--audit',default='live_audit_4head_v291_varn.jsonl')
    ap.add_argument('--prepared-out')
    ap.add_argument('--bundle-out')
    ap.add_argument('--prepare-only',action='store_true')
    a=ap.parse_args()
    code=f'{a.date}{a.jcd:02d}{a.race:02d}'
    with tempfile.TemporaryDirectory(prefix='head4_v291_auto_') as td:
        p=Path(a.prepared_out) if a.prepared_out else Path(td)/'runner_input.json'
        out=prepare(a.bundle_json,str(p),a.source_json,a.bundle_out)
        if out['race_code']!=code: raise SystemExit(f'race_code mismatch: {out["race_code"]} != {code}')
        if a.prepare_only:
            print(json.dumps({'status':'READY','policy':POLICY,'race_code':code,'prepared_input':str(p),'source_mode':bool(a.source_json),'classification':out['_auto_meta']['classification_preview']},ensure_ascii=False))
            return
        cmd=[sys.executable,'run_4head_v291_varn_live.py','--input-json',str(p),'--date',a.date,'--jcd',str(a.jcd),'--race',str(a.race),'--deadline-jst',a.deadline_jst,'--audit',a.audit]
        cp=subprocess.run(cmd,check=False)
        raise SystemExit(cp.returncode)
if __name__=='__main__':main()
