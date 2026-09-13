#!/usr/bin/env python3
"""Derive frozen v283 SECOND5 + conditional THIRD20 rows from six current-day boat rows.

Result-blind / inference-only.  This reproduces the v279/v281/v282 feature formulas
needed by the frozen HEAD4 v291 artifact.  Input contains boat rows 1..6; boat 4 is
used only as head-current context while {1,2,3,5,6} are opponent candidates.
"""
from __future__ import annotations
import argparse,json,math
from pathlib import Path
from typing import Any,Mapping
from head4_v291_downstream_inference import BOATS,load_artifact,score_second,score_conditional_third,v283_top4

CURRENT=("cur_ex","cur_st","cur_orig_lap","cur_orig_turn","cur_orig_straight","cur_orig_avg")
PAIR_NAMES=("pair_same_side4","pair_second_inner","pair_second_outer","pair_third_inner","pair_third_outer","pair_adjacent","pair_distance","pair_third_minus_second","pair_second_is1","pair_second_is2","pair_second_is3","pair_second_is5","pair_second_is6")

class V283RowBuildError(RuntimeError): pass

def _num(name:str,v:Any)->float:
    try:x=float(v)
    except (TypeError,ValueError) as e: raise V283RowBuildError(f"invalid {name}") from e
    if not math.isfinite(x): raise V283RowBuildError(f"non-finite {name}")
    return x

def _boats(src:Mapping[str,Any])->dict[int,dict[str,float]]:
    raw=src.get("boats") if isinstance(src,Mapping) else None
    if not isinstance(raw,Mapping): raise V283RowBuildError("input must contain boats mapping")
    out={}
    for b in range(1,7):
        r=raw.get(str(b),raw.get(b))
        if not isinstance(r,Mapping): raise V283RowBuildError(f"missing boat row {b}")
        out[b]=dict(r)
    return out

def _head_context(rows:Mapping[int,Mapping[str,Any]])->dict[str,float]:
    h={c:_num(f"boat4.{c}",rows[4].get(c)) for c in CURRENT}
    h["h4_attack"]=(h["cur_ex"]+h["cur_st"]+h["cur_orig_straight"]+h["cur_orig_avg"])/4.0
    h["h4_turning"]=(h["cur_orig_lap"]+h["cur_orig_turn"])/2.0
    return h

def _scenario(b:int,row:Mapping[str,Any],head:Mapping[str,float])->dict[str,float]:
    z={}
    for k in BOATS:z[f"is_boat{k}"]=float(b==k)
    z["is_inner123"]=float(b<4);z["is_outer56"]=float(b>4)
    z["is_inner_edge3"]=float(b==3);z["is_outer_edge5"]=float(b==5)
    z["h4_attack"]=head["h4_attack"];z["h4_turning"]=head["h4_turning"]
    for c in CURRENT:
        x=_num(f"boat{b}.{c}",row.get(c));d=x-head[c]
        z[f"{c}__vs4"]=d;z[f"{c}__abs4"]=abs(d)
    for side in ("is_inner123","is_outer56","is_inner_edge3","is_outer_edge5"):
        z[f"h4_attack_x_{side}"]=head["h4_attack"]*z[side]
    for c in ("cur_orig_lap","cur_orig_turn","cur_orig_straight","cur_st"):
        z[f"h4_attack_x_{c}"]=head["h4_attack"]*_num(f"boat{b}.{c}",row.get(c))
    return z

def _pair(s:int,t:int)->dict[str,float]:
    return {
      "pair_same_side4":float((s<4 and t<4) or (s>4 and t>4)),
      "pair_second_inner":float(s<4),"pair_second_outer":float(s>4),
      "pair_third_inner":float(t<4),"pair_third_outer":float(t>4),
      "pair_adjacent":float(abs(t-s)==1),"pair_distance":float(abs(t-s)),
      "pair_third_minus_second":float(t-s),
      "pair_second_is1":float(s==1),"pair_second_is2":float(s==2),"pair_second_is3":float(s==3),
      "pair_second_is5":float(s==5),"pair_second_is6":float(s==6),
    }
def derive(src:Mapping[str,Any],artifact:Mapping[str,Any]):
    rows=_boats(src);head=_head_context(rows)
    fs2=list(artifact["v283_SECOND"]["features"]);fs3=list(artifact["v283_COND_THIRD"]["features"])
    if len(fs2)!=25 or len(fs3)!=69: raise V283RowBuildError("frozen schema size mismatch")
    second=[];enriched={}
    for b in BOATS:
        base=rows[b];missing=[c for c in fs2 if c not in base]
        if missing: raise V283RowBuildError(f"boat {b} missing SECOND primitives: "+",".join(missing[:12]))
        sr={"boat":b};sr.update({c:_num(f"boat{b}.{c}",base[c]) for c in fs2});second.append(sr)
        e=dict(base);e.update(_scenario(b,base,head));enriched[b]=e
    cond=[]
    for s in BOATS:
        for t in BOATS:
            if s==t:continue
            p=_pair(s,t);tr=enriched[t];r={"second_boat":s,"third_boat":t}
            for f in fs3:
                if f.startswith("t_"):
                    k=f[2:]
                    if k not in tr: raise V283RowBuildError(f"missing derived THIRD primitive {k} for boat {t}")
                    r[f]=_num(f"boat{t}.{k}",tr[k])
                elif f in p:r[f]=p[f]
                else: raise V283RowBuildError(f"unsupported frozen conditional feature {f}")
            cond.append(r)
    return second,cond

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--input-json',required=True);ap.add_argument('--artifact',default='artifacts/head4_v291_downstream_20260630.json');ap.add_argument('--out');a=ap.parse_args()
    art=load_artifact(a.artifact);src=json.loads(Path(a.input_json).read_text(encoding='utf-8'));second,cond=derive(src,art)
    p2=score_second(second,art);pc=score_conditional_third(cond,art);top4=v283_top4(p2,pc)
    out={"policy":"HEAD4_V291_COMP7","frozen_training_cutoff":"2026-06-30","production_inference_only":True,"result_blind":True,"jul_aug_labels_used":False,"september_labels_used":False,"v96_used":False,"second_rows":second,"conditional_rows":cond,"p2":{str(k):v for k,v in p2.items()},"cond":{f"{s}>{t}":v for (s,t),v in pc.items()},"top4":[[4,s,t] for s,t in top4]}
    text=json.dumps(out,ensure_ascii=False,indent=2)+'\n';Path(a.out).write_text(text,encoding='utf-8') if a.out else print(text,end='')
if __name__=='__main__':main()
