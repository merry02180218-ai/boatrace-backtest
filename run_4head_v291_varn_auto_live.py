#!/usr/bin/env python3
"""One-command downstream AUTO LIVE bridge for frozen HEAD4 v291 VARN.

Given a result-blind current-day causal bundle, assemble the exact frozen model
input and hand it to the existing production market/ticket runner. The final
runner remains the sole owner of official pre-deadline odds, V291 Top4 composite
entry, variable N=4..16, and exact JPY10,000 Dutch.
"""
from __future__ import annotations
import argparse,json,subprocess,sys,tempfile
from pathlib import Path
from assemble_4head_v291_varn_live_input import assemble

POLICY='HEAD4_V291_COMP7_VARN_F4_N16'

def prepare(bundle_path:str,out_path:str)->dict:
    src=json.loads(Path(bundle_path).read_text(encoding='utf-8'))
    out=assemble(src)
    Path(out_path).write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--bundle-json',required=True)
    ap.add_argument('--date',required=True)
    ap.add_argument('--jcd',required=True,type=int)
    ap.add_argument('--race',required=True,type=int)
    ap.add_argument('--deadline-jst',required=True)
    ap.add_argument('--audit',default='live_audit_4head_v291_varn.jsonl')
    ap.add_argument('--prepared-out')
    ap.add_argument('--prepare-only',action='store_true')
    a=ap.parse_args()
    code=f'{a.date}{a.jcd:02d}{a.race:02d}'
    with tempfile.TemporaryDirectory(prefix='head4_v291_auto_') as td:
        p=Path(a.prepared_out) if a.prepared_out else Path(td)/'runner_input.json'
        out=prepare(a.bundle_json,str(p))
        if out['race_code']!=code: raise SystemExit(f'race_code mismatch: {out["race_code"]} != {code}')
        if a.prepare_only:
            print(json.dumps({'status':'READY','policy':POLICY,'race_code':code,'prepared_input':str(p),'classification':out['_auto_meta']['classification_preview']},ensure_ascii=False))
            return
        cmd=[sys.executable,'run_4head_v291_varn_live.py','--input-json',str(p),'--date',a.date,'--jcd',str(a.jcd),'--race',str(a.race),'--deadline-jst',a.deadline_jst,'--audit',a.audit]
        cp=subprocess.run(cmd,check=False)
        raise SystemExit(cp.returncode)
if __name__=='__main__':main()
