"""Apply frozen v106 to one already-eligible 4-corner pre-race row.

This helper does NOT select the race/head, does NOT change A/S, and never reads
current/final odds. The caller must pass the actual production ticket order via
`current_tickets20` or `tickets20_display` so CURRENT7 is an exact production
comparison, not a reconstructed approximation.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

MODEL_PATH=Path(__file__).with_name('v106_4corner_7ticket_frozen_20260905.json')


def ff(x,d=.5):
    try:
        if x is None or str(x).strip()=='': return d
        return float(x)
    except Exception: return d


def get(row,key,default=.5):
    if key in row: return ff(row.get(key),default)
    if key+'_v93' in row: return ff(row.get(key+'_v93'),default)
    return default


def zmap(v):
    a=list(v.values()); m=sum(a)/len(a)
    s=math.sqrt(sum((x-m)**2 for x in a)/len(a))
    return {b:(0.0 if s<1e-12 else (x-m)/s) for b,x in v.items()}


def parse_tickets(v,head):
    if isinstance(v,list): raw=[str(x).strip() for x in v]
    else: raw=[x.strip() for x in str(v or '').split(';')]
    out=[]
    for t in raw:
        p=t.split('-')
        if len(p)!=3: continue
        try: a,b,c=map(int,p)
        except Exception: continue
        if a==head and len({a,b,c})==3 and all(1<=x<=6 for x in (a,b,c)):
            out.append(f'{a}-{b}-{c}')
    return out


def role_scores(row,model):
    boats=[int(x) for x in model['boats']]
    feats=model['features']; mu=model['mu']; sd=model['sd']
    current={b:get(row,f'opp_score_b{b}',0.0) for b in boats}; zc=zmap(current)
    raw2={}; raw3={}
    for b in boats:
        x=[(get(row,f'opp_{k}_b{b}',.5)-float(mu[k]))/float(sd[k]) for k in feats]
        x += [1.0 if b==k else 0.0 for k in boats]
        raw2[b]=sum(float(w)*v for w,v in zip(model['w_second'],x))
        raw3[b]=sum(float(w)*v for w,v in zip(model['w_third'],x))
    z2=zmap(raw2); z3=zmap(raw3); lam=float(model['role_lambda'])
    s2={b:(1-lam)*zc[b]+lam*z2[b] for b in boats}
    s3={b:(1-lam)*zc[b]+lam*z3[b] for b in boats}
    return current,s2,s3


def role_order(head,boats,s2,s3):
    ps=[(a,b) for a in boats for b in boats if a!=b]
    ps.sort(key=lambda p:(s2[p[0]]+s3[p[1]],s2[p[0]],s3[p[1]]),reverse=True)
    return ps


def value_order(head,role,model):
    price=model['price_patterns']; lam=float(model['value_lambda'])
    rscore={p:1.0-i/19.0 for i,p in enumerate(role)}
    score={}
    for p in role:
        key=f'{head}-{p[0]}-{p[1]}'
        pv=price.get(key,{}).get('value_score')
        pv=rscore[p] if pv is None else float(pv)
        score[p]=(1-lam)*rscore[p]+lam*pv
    return sorted(role,key=lambda p:(score[p],rscore[p]),reverse=True),score


def apply(row,model=None):
    model=model or json.loads(MODEL_PATH.read_text(encoding='utf-8'))
    head=int(model['head']); boats=[int(x) for x in model['boats']]; n=int(model['tickets'])
    cur_source='current_tickets20' if row.get('current_tickets20') else ('tickets20_display' if row.get('tickets20_display') else '')
    cur_all=parse_tickets(row.get(cur_source,''),head) if cur_source else []
    if len(cur_all)<n:
        raise ValueError('actual production ticket order is required: pass current_tickets20 or tickets20_display with >=7 head-4 tickets')
    current7=cur_all[:n]

    current,s2,s3=role_scores(row,model)
    ro=role_order(head,boats,s2,s3)
    vo,vs=value_order(head,ro,model)
    role7=[f'{head}-{a}-{b}' for a,b in ro[:n]]
    v106=[f'{head}-{a}-{b}' for a,b in vo[:n]]
    return {
      'version':model['version'],'status':model['status'],'head':head,'tickets':n,
      'role_lambda':model['role_lambda'],'value_lambda':model['value_lambda'],
      'current7_source':cur_source,'current7':current7,'role7':role7,'v106_7':v106,
      'changed_current_to_role':current7!=role7,
      'changed_role_to_v106':role7!=v106,
      'current_rank':sorted(boats,key=lambda b:current[b],reverse=True),
      'role_second_rank':sorted(boats,key=lambda b:s2[b],reverse=True),
      'role_third_rank':sorted(boats,key=lambda b:s3[b],reverse=True),
      'role_second_score':{str(b):round(s2[b],8) for b in boats},
      'role_third_score':{str(b):round(s3[b],8) for b in boats},
      'v106_pair_score':{f'{head}-{a}-{b}':round(vs[(a,b)],8) for a,b in vo},
    }


def main():
    if len(sys.argv)!=2:
        raise SystemExit('usage: python v106_4corner_7ticket_apply.py pre_race_row.json')
    row=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    print(json.dumps(apply(row),ensure_ascii=False,indent=2))

if __name__=='__main__': main()
