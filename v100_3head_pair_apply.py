"""Apply the frozen v100 3HEAD second/third role model to one pre-race row.

Input row must contain, for boats 1/2/4/5/6:
  opp_score_bN
  opp_grade_bN, opp_national_bN, opp_local_bN, opp_motor_bN,
  opp_waku_bN, opp_nst_bN, opp_direct_bN
Aliases with _v97 suffix are also accepted.

This helper NEVER selects the head and NEVER changes A/S. It only orders 2nd/3rd
opponents after a 3HEAD race has already passed the normal live gate.
"""
from __future__ import annotations
import json,math,sys
from pathlib import Path

MODEL_PATH=Path(__file__).with_name('v100_3head_pair_frozen_20260905.json')


def ff(x,d=.5):
    try:
        if x is None or str(x).strip()=='': return d
        return float(x)
    except Exception:return d

def get(row,key,default=.5):
    if key in row:return ff(row.get(key),default)
    if key+'_v97' in row:return ff(row.get(key+'_v97'),default)
    return default

def zmap(v):
    a=list(v.values());m=sum(a)/len(a)
    s=math.sqrt(sum((x-m)**2 for x in a)/len(a))
    return {b:(0. if s<1e-12 else (x-m)/s) for b,x in v.items()}

def role_scores(row,model):
    boats=model['boats'];feats=model['features'];mu=model['mu'];sd=model['sd']
    current={b:get(row,f'opp_score_b{b}',0.) for b in boats};zc=zmap(current)
    r2={};r3={}
    for b in boats:
        x=[(get(row,f'opp_{k}_b{b}',.5)-mu[k])/sd[k] for k in feats]
        x += [1. if b==k else 0. for k in boats]
        r2[b]=sum(w*v for w,v in zip(model['w_second'],x))
        r3[b]=sum(w*v for w,v in zip(model['w_third'],x))
    z2=zmap(r2);z3=zmap(r3);lam=float(model['lambda'])
    s2={b:(1-lam)*zc[b]+lam*z2[b] for b in boats}
    s3={b:(1-lam)*zc[b]+lam*z3[b] for b in boats}
    return current,s2,s3

def make_pairs(head,r2,r3,s2,s3,k):
    n3=3 if k==4 else 4
    c=[(a,b) for a in r2[:2] for b in r3[:n3] if a!=b]
    c.sort(key=lambda p:(s2[p[0]]+s3[p[1]],s2[p[0]],s3[p[1]]),reverse=True)
    if len(c)<k:
        extra=[(a,b) for a in r2 for b in r3 if a!=b and (a,b) not in c]
        extra.sort(key=lambda p:(s2[p[0]]+s3[p[1]],s2[p[0]],s3[p[1]]),reverse=True)
        c+=extra
    return [f'{head}-{a}-{b}' for a,b in c[:k]]
def current_pairs(head,ranked,k):
    n3=3 if k==4 else 4
    c=[(a,b) for a in ranked[:2] for b in ranked[:n3] if a!=b]
    if len(c)<k:
        c += [(a,b) for a in ranked for b in ranked if a!=b and (a,b) not in c]
    return [f'{head}-{a}-{b}' for a,b in c[:k]]
def apply(row,model=None):
    model=model or json.loads(MODEL_PATH.read_text(encoding='utf-8'))
    head=int(model['head']);boats=[int(x) for x in model['boats']]
    current,s2,s3=role_scores(row,model)
    ranked_cur=sorted(boats,key=lambda b:current[b],reverse=True)
    ranked2=sorted(boats,key=lambda b:s2[b],reverse=True)
    ranked3=sorted(boats,key=lambda b:s3[b],reverse=True)
    return {
      'version':model['version'],'status':model['status'],'head':head,'lambda':model['lambda'],
      'current_rank':ranked_cur,'v100_second_rank':ranked2,'v100_third_rank':ranked3,
      'current4':current_pairs(head,ranked_cur,4),'v100_4':make_pairs(head,ranked2,ranked3,s2,s3,4),
      'current6':current_pairs(head,ranked_cur,6),'v100_6':make_pairs(head,ranked2,ranked3,s2,s3,6),
      'v100_second_score':{str(b):round(s2[b],8) for b in boats},
      'v100_third_score':{str(b):round(s3[b],8) for b in boats},
    }

def main():
    if len(sys.argv)!=2:
        raise SystemExit('usage: python v100_3head_pair_apply.py pre_race_row.json')
    row=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    print(json.dumps(apply(row),ensure_ascii=False,indent=2))
if __name__=='__main__':main()
