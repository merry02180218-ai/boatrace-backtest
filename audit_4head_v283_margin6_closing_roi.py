#!/usr/bin/env python3
"""Strict retrospective pair-level closing-odds comparison: frozen v283 4pt vs gap<=.10 margin expansion.
Apr-Jun development, Jul-Aug holdout. September is never read. Production unchanged.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import audit_4head_86r_independent as cand
import audit_4head_86r_v283_closing_odds as audit
from head4_v291_downstream_inference import load_artifact, score_second, score_conditional_third, v283_top4, BOATS

OUT=Path('/tmp/head4_v283_margin6_roi'); OUT.mkdir(parents=True,exist_ok=True)
START='2026-04-01'; END='2026-08-31'; GAP=.10; STAKE=100

def main():
    cx=cand.rebuild(); cx=cx[(cx.date>=START)&(cx.date<=END)].copy(); assert len(cx)==164
    codes=set(cx.race_code.astype(str).str.zfill(12)); d=audit.source_rows(codes); long=audit.build_long_all(d); art=load_artifact()
    sf=list(art['v283_SECOND']['features']); cf=list(art['v283_COND_THIRD']['features'])
    truth={str(r.race_code).zfill(12):(int(float(r.winner)),int(float(r.second)),int(float(r.third))) for _,r in d.iterrows() if str(r.get('valid_result','0')) in ('1','1.0')}
    odds_cache={}; rec=[]
    for code,g in long.groupby('race_code'):
        sr=[]
        for _,r in g.iterrows():
            x={'boat':int(r.boat)}; x.update({f:r[f] for f in sf}); sr.append(x)
        p2=score_second(sr,art); cr=audit.conditional_rows(g,sf,cf); pc=score_conditional_third(cr,art)
        base=v283_top4(p2,pc)
        sorder=sorted(BOATS,key=lambda s:(-float(p2[s]),s)); expanded=[]; fires=[]
        for s in sorder[:2]:
            ts=sorted((t for t in BOATS if t!=s),key=lambda t:(-float(pc[(s,t)]),t))
            gap=float(pc[(s,ts[1])]-pc[(s,ts[2])]); use=ts[:3] if gap<=GAP else ts[:2]
            fires.append((s,gap,gap<=GAP,ts[2] if gap<=GAP else None))
            expanded += [(s,t) for t in use]
        # preserve pair score ordering and exact base contract; expansion only adds rank3 per fired SECOND branch
        expanded=list(dict.fromkeys(base + [p for p in expanded if p not in base]))
        ds=str(g.date.iloc[0]); oq=odds_cache.setdefault(ds,audit.odds_for_date(ds)); oo=oq[oq.race_code.astype(str)==str(code)] if len(oq) else oq
        covered=len(oo)==1; actual=truth.get(str(code)); hp=(actual[1],actual[2]) if actual and actual[0]==4 else None
        def settle(pairs):
            stake=len(pairs)*STAKE if covered else 0; hit=bool(hp in pairs) if covered else False; odd=np.nan
            if hit:
                odd=pd.to_numeric(oo.iloc[0].get(f'4-{hp[0]}-{hp[1]}'),errors='coerce')
            validhit=hit and pd.notna(odd); pay=float(odd*STAKE) if validhit else 0.0
            return stake,int(validhit),odd,pay
        bs,bh,bo,bp=settle(base); es,eh,eo,ep=settle(expanded)
        rec.append({'date':ds,'month':ds[:7],'race_code':str(code),'head4':int(actual is not None and actual[0]==4),'actual_pair':f'4-{hp[0]}-{hp[1]}' if hp else '',
                    'base_pairs':'|'.join(f'4-{s}-{t}' for s,t in base),'expanded_pairs':'|'.join(f'4-{s}-{t}' for s,t in expanded),
                    'fire_branches':sum(int(x[2]) for x in fires),'fire_detail':'|'.join(f's{s}:gap={gap:.6f}:add={add}' for s,gap,fire,add in fires if fire),
                    'odds_covered':int(covered),'base_tickets':len(base),'expanded_tickets':len(expanded),'base_stake':bs,'expanded_stake':es,
                    'base_hit':bh,'expanded_hit':eh,'hit_odds':eo if eh else bo,'base_payout':bp,'expanded_payout':ep,
                    'incremental_stake':es-bs,'incremental_payout':ep-bp,'incremental_profit':(ep-bp)-(es-bs),'rescued_hit':int(eh and not bh)})
    r=pd.DataFrame(rec).sort_values(['date','race_code']); assert len(r)==164; r.to_csv(OUT/'race_detail.csv',index=False)
    periods=[('Apr-Jun',['2026-04','2026-05','2026-06']),('Jul-Aug',['2026-07','2026-08']),('July',['2026-07']),('August',['2026-08']),('Apr-Aug',['2026-04','2026-05','2026-06','2026-07','2026-08'])]
    out=[]
    for name,mons in periods:
        q=r[r.month.isin(mons)]; q=q[q.odds_covered==1]
        for mode in ['base','expanded']:
            st=float(q[f'{mode}_stake'].sum()); pay=float(q[f'{mode}_payout'].sum())
            out.append({'period':name,'mode':mode,'covered_R':len(q),'tickets':int(q[f'{mode}_tickets'].sum()),'hits':int(q[f'{mode}_hit'].sum()),'stake_yen':st,'payout_yen':pay,'profit_yen':pay-st,'roi_pct':100*pay/st if st else np.nan,'rescued_hits':int(q.rescued_hit.sum()) if mode=='expanded' else 0})
        inc_st=float(q.incremental_stake.sum()); inc_pay=float(q.incremental_payout.sum())
        out.append({'period':name,'mode':'incremental_only','covered_R':len(q),'tickets':int((q.expanded_tickets-q.base_tickets).sum()),'hits':int(q.rescued_hit.sum()),'stake_yen':inc_st,'payout_yen':inc_pay,'profit_yen':inc_pay-inc_st,'roi_pct':100*inc_pay/inc_st if inc_st else np.nan,'rescued_hits':int(q.rescued_hit.sum())})
    s=pd.DataFrame(out); s.to_csv(OUT/'roi_summary.csv',index=False)
    rescued=r[r.rescued_hit.eq(1)][['date','race_code','actual_pair','hit_odds','base_pairs','expanded_pairs','incremental_stake','incremental_payout','incremental_profit']]
    rescued.to_csv(OUT/'rescued_hits.csv',index=False)
    meta={'status':'STRICT_RETROSPECTIVE_PAIR_LEVEL_CLOSING_ODDS_AUDIT','gap':GAP,'stake_per_ticket_yen':STAKE,'development':'Apr-Jun','holdout':'Jul-Aug','formal_prospective_roi':'NOT_COMPUTABLE','september':'UNREAD','production':'HEAD4_V291_COMP7 unchanged','v96_used':False}
    (OUT/'meta.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
    print('HEAD4_V283_MARGIN6_STRICT_CLOSING_ROI_OK'); print(s.to_string(index=False)); print('\nRESCUED_HITS'); print(rescued.to_string(index=False)); print('SEPTEMBER_UNREAD'); print('PRODUCTION_UNCHANGED')
if __name__=='__main__': main()
