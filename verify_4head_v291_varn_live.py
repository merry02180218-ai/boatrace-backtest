#!/usr/bin/env python3
import math
import run_4head_v291_varn_live as r
from head4_v273_a_live_inference import load_artifact,classify

# deterministic opponent probabilities with complete conditional map
p2={1:.40,2:.25,3:.15,5:.12,6:.08}
pc={(s,t):1.0/(1+abs(t-s)) for s in r.base.BOATS for t in r.base.BOATS if s!=t}
order=r.full_order(p2,pc)
assert len(order)==20 and len(set(order))==20
assert order[:4]==r.base.v283_top4(p2,pc)

# synthetic odds: Top4 composite exactly above entry; expansion must stop when floor breaks.
od={t:100.0 for t in order}
sel=r.pick_n(order,od)
assert sel['entered'] and sel['n']==16 and sel['comp']>=4.0

od={t:20.0 for t in order}
sel=r.pick_n(order,od)
# Top4 comp=5 => must preserve old v291 PASS regardless of variable-N floor.
assert not sel['entered'] and abs(sel['entry_comp']-5.0)<1e-12

# S has priority over A.
a=load_artifact()
features={k:float(v) for k,v in zip(a['A_SCORE']['features'],a['A_SCORE']['imputer_median'])}
c=classify(.28,.25,.224790,features,a)
assert c['layer']=='S' and c['eligible']

# A can classify outside S when PRE/POST pass A gate; verify scorer path executes.
c=classify(.18,.18,0.0,features,a)
assert c['layer'] in ('A','NONE') and c['policy']=='HEAD4_V273_A_LIVE_QMAP'

# Dutch is exact 10k and 100-yen units for variable ticket counts.
for n in (4,6,12,16):
    tickets=order[:n];odds=[20.0+i for i in range(n)]
    rows=r.dutch(tickets,odds)
    assert sum(x['stake'] for x in rows)==10000
    assert all(x['stake']>0 and x['stake']%100==0 for x in rows)

print('VERIFY_4HEAD_V291_VARN_LIVE_OK')
