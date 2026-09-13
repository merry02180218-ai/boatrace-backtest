#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import hashlib
import json
import math
import pickle
import time

import pandas as pd
import requests
from bs4 import BeautifulSoup

import onehead_production_profile as prod
import run_v299_1head_trifecta3_policy_search as v299
import run_v312_1head_opponent_outer_gate as v312
import run_v320_1head_exact3_ticket_policy as v320
import run_v337_1head_head_cutoff_volume as v337

OUT=Path('/tmp/v340'); OUT.mkdir(parents=True,exist_ok=True)
STAKE=10000
UNIT=100
LOW=3.0
HIGH=4.0
POLICY='HYBRID'
ALPHA=.70

# Official BOAT RACE odds page table order.
ARRAY_3T=[
123,213,312,412,512,612,124,214,314,413,513,613,125,215,315,415,514,614,126,216,316,416,516,615,
132,231,321,421,521,621,134,234,324,423,523,623,135,235,325,425,524,624,136,236,326,426,526,625,
142,241,341,431,531,631,143,243,342,432,532,632,145,245,345,435,534,634,146,246,346,436,536,635,
152,251,351,451,541,641,153,253,352,452,542,642,154,254,354,453,543,643,156,256,356,456,546,645,
162,261,361,461,561,651,163,263,362,462,562,652,164,264,364,463,563,653,165,265,365,465,564,654]


def identity_hash(df):
    ids=sorted(df.race_code.astype(str).str.zfill(12).tolist())
    return hashlib.sha256('\n'.join(ids).encode()).hexdigest()


def combo(x):
    s=str(x)
    return f'{s[0]}-{s[1]}-{s[2]}'


def combined_odds(odds):
    return 1.0/sum(1.0/o for o in odds)


def dutch_stakes(odds):
    """Allocate exactly 10,000 yen in 100-yen units, minimum 100 per included ticket."""
    n=len(odds); total_units=STAKE//UNIT
    if n>total_units: raise ValueError('too many tickets')
    inv=[1.0/o for o in odds]; den=sum(inv)
    target=[total_units*x/den for x in inv]
    units=[max(1,int(math.floor(x))) for x in target]
    while sum(units)>total_units:
        choices=[i for i,u in enumerate(units) if u>1]
        if not choices: raise RuntimeError('cannot reduce dutch allocation')
        i=max(choices,key=lambda k:(units[k]-target[k],units[k]*odds[k]))
        units[i]-=1
    while sum(units)<total_units:
        # Raise the currently lowest gross payout first.
        i=min(range(n),key=lambda k:(units[k]*odds[k],k))
        units[i]+=1
    stakes=[u*UNIT for u in units]
    return stakes


def fetch_odds(code, session):
    code=str(code).zfill(12); hd=code[:8]; jcd=code[8:10]; rno=int(code[10:12])
    url=f'https://www.boatrace.jp/owpc/pc/race/odds3t?rno={rno}&jcd={jcd}&hd={hd}'
    last=''
    for attempt in range(3):
        try:
            r=session.get(url,timeout=30); r.raise_for_status(); last=r.text
            soup=BeautifulSoup(r.text,'html.parser')
            tables=soup.find_all('div',class_='table1')
            if len(tables)<2: raise RuntimeError(f'odds table missing tables={len(tables)}')
            vals=[td.get_text(strip=True).replace(',','') for td in tables[1].find_all('td',class_='oddsPoint')]
            if len(vals)!=120: raise RuntimeError(f'odds count={len(vals)}')
            out={}
            for k,v in zip(ARRAY_3T,vals):
                try:o=float(v)
                except: continue
                if o>0: out[combo(k)]=o
            if len(out)<100: raise RuntimeError(f'valid odds={len(out)}')
            return out,url
        except Exception as e:
            if attempt==2: return None,f'{url} ERROR {e}'
            time.sleep(.5*(attempt+1))
    return None,url


def full_rankings(selected):
    # Feb-Jun: exact frozen v320 factorized path.
    d,p3,p4=v312.load_cache(); d.race_code=d.race_code.astype(str).str.zfill(12)
    p2_dev,pc_dev=v320.build_factorized(d,p3,p4)
    # Jul-Aug NON-PRISTINE: exact frozen v321 caches already used by v337/v338.
    with v337.SECOND.open('rb') as f: sec=pickle.load(f)
    with v337.THIRD.open('rb') as f: pc_ja=pickle.load(f)
    p2_ja=sec['p2']
    fn=v299.STRATEGIES[POLICY]
    out={}
    for _,r in selected.iterrows():
        m=str(r.month); code=str(r.race_code).zfill(12)
        if m in p2_dev and code in p2_dev[m] and m in pc_dev and code in pc_dev[m]:
            p2,pc=p2_dev[m][code],pc_dev[m][code]
        elif m in p2_ja and code in p2_ja[m] and m in pc_ja and code in pc_ja[m]:
            p2,pc=p2_ja[m][code],pc_ja[m][code]
        else:
            raise RuntimeError(f'missing frozen ranking probabilities {m} {code}')
        probs=v299.pair_prob(p2,pc,ALPHA)
        order=fn(p2,pc,probs)
        tickets=[f'1-{s}-{t}' for s,t in order]
        if tickets[:3] != str(r.tickets).split(';'):
            raise AssertionError(f'top3 identity drift {code}: {tickets[:3]} vs {r.tickets}')
        out[code]=tickets
    return out


def evaluate_one(r,tickets,odmap):
    top3=tickets[:3]; top3_od=[odmap[x] for x in top3]
    c3=combined_odds(top3_od)
    action='keep3'; chosen=top3
    if c3<LOW:
        action='skip'; chosen=[]
    elif c3>=HIGH:
        action='expand'
        # Combined odds decreases monotonically as ranked prefixes are added.
        # Keep the largest ranked prefix whose combined odds remains >= 3.0.
        best=top3
        for k in range(4,len(tickets)+1):
            cand=tickets[:k]
            c=combined_odds([odmap[x] for x in cand])
            if c>=LOW:
                best=cand
            else:
                break
        chosen=best
    if not chosen:
        return {'top3_combined':c3,'action':action,'n_tickets':0,'final_combined':None,
                'hit':0,'return_yen':0,'profit_yen':0,'stake_yen':0,'tickets_final':'','stakes_final':''}
    ods=[odmap[x] for x in chosen]; cf=combined_odds(ods); stakes=dutch_stakes(ods)
    actual=str(r.actual_combo); ret=0
    if actual in chosen:
        i=chosen.index(actual); ret=stakes[i]*ods[i]
    return {'top3_combined':c3,'action':action,'n_tickets':len(chosen),'final_combined':cf,
            'hit':int(actual in chosen),'return_yen':ret,'profit_yen':ret-STAKE,'stake_yen':STAKE,
            'tickets_final':';'.join(chosen),'stakes_final':';'.join(map(str,stakes))}


def baseline_one(r,tickets,odmap):
    chosen=tickets[:3]; ods=[odmap[x] for x in chosen]; stakes=dutch_stakes(ods); actual=str(r.actual_combo); ret=0
    if actual in chosen:
        i=chosen.index(actual); ret=stakes[i]*ods[i]
    return {'baseline_hit':int(actual in chosen),'baseline_return_yen':ret,'baseline_stake_yen':STAKE,
            'baseline_combined':combined_odds(ods)}


def main():
    if not prod.SEPTEMBER_OUTCOMES_MUST_REMAIN_UNREAD: raise AssertionError('September outcomes permitted')
    base=v337.load_candidate_base(); y,_,_=v337.build_exhibition(base); v337.validate_no_sep(y)
    _,selected,_,_=v337.eval_cut(y,prod.HEAD_CUTOFF)
    got=(len(selected),int(selected.head_hit.sum()),int(selected.hit.sum()),identity_hash(selected))
    exp=(prod.EXPECTED_PASS_R,prod.EXPECTED_HEAD,prod.EXPECTED_EXACT3,prod.EXPECTED_PASS_ID_SHA256)
    if got!=exp: raise AssertionError(f'production identity drift got={got} expected={exp}')
    if any(str(x).startswith('2026-09') for x in selected.month.astype(str)): raise AssertionError('September entered v340')
    ranks=full_rankings(selected)

    sess=requests.Session(); sess.headers.update({'User-Agent':'Mozilla/5.0 v340 research audit'})
    records=[]; missing=[]
    for idx,(_,r) in enumerate(selected.sort_values('race_code').iterrows(),1):
        code=str(r.race_code).zfill(12); odmap,url=fetch_odds(code,sess)
        if odmap is None:
            missing.append({'race_code':code,'detail':url}); print('ODDS_MISSING',code,url,flush=True); continue
        # All model-ranked tickets are 1-head; require all 20 odds to avoid expansion bias.
        req=ranks[code]
        miss=[x for x in req if x not in odmap]
        if miss:
            missing.append({'race_code':code,'detail':'missing combos '+','.join(miss)}); continue
        z={'month':str(r.month),'race_code':code,'actual_combo':str(r.actual_combo),'head_hit':int(r.head_hit)}
        z.update(baseline_one(r,req,odmap)); z.update(evaluate_one(r,req,odmap)); records.append(z)
        if idx%25==0: print('odds progress',idx,'/',len(selected),flush=True)
        time.sleep(.08)
    pd.DataFrame(missing).to_csv(OUT/'odds_missing.csv',index=False)
    z=pd.DataFrame(records)
    if len(z)==0: raise RuntimeError('no odds coverage')
    z.to_csv(OUT/'race_level.csv',index=False)
    covered=len(z); bought=z[z.stake_yen>0].copy()
    baseline_stake=float(z.baseline_stake_yen.sum()); baseline_return=float(z.baseline_return_yen.sum())
    stake=float(bought.stake_yen.sum()); ret=float(bought.return_yen.sum())
    monthly=bought.groupby('month',as_index=False).agg(R=('race_code','size'),hits=('hit','sum'),stake=('stake_yen','sum'),returns=('return_yen','sum'))
    monthly['hit_rate']=monthly.hits/monthly.R
    monthly['roi_pct']=100*monthly.returns/monthly.stake
    monthly['profit']=monthly.returns-monthly.stake
    monthly.to_csv(OUT/'monthly.csv',index=False)
    dist=bought.groupby('n_tickets').size().reset_index(name='R'); dist.to_csv(OUT/'ticket_count_distribution.csv',index=False)
    result={
      'production_identity':{'R':got[0],'head':got[1],'exact3_top3':got[2],'sha256':got[3]},
      'odds_source':'BOAT RACE official closing trifecta odds','odds_coverage_R':covered,'odds_missing_R':len(missing),
      'policy':{'skip_if_top3_combined_lt':LOW,'expand_if_top3_combined_gte':HIGH,'expand_rule':'largest HYBRID alpha=.70 ranked prefix with combined odds >=3.0','stake_yen':STAKE,'dutch_unit_yen':UNIT},
      'actions':z.action.value_counts().to_dict(),
      'adaptive':{'bought_R':len(bought),'hits':int(bought.hit.sum()),'hit_rate_pct':100*float(bought.hit.mean()) if len(bought) else None,
                  'total_stake_yen':stake,'total_return_yen':ret,'profit_yen':ret-stake,'roi_pct':100*ret/stake if stake else None,
                  'avg_final_combined':float(bought.final_combined.mean()) if len(bought) else None,'median_final_combined':float(bought.final_combined.median()) if len(bought) else None},
      'baseline_top3_all_covered':{'R':covered,'hits':int(z.baseline_hit.sum()),'hit_rate_pct':100*float(z.baseline_hit.mean()),
                                  'total_stake_yen':baseline_stake,'total_return_yen':baseline_return,'profit_yen':baseline_return-baseline_stake,'roi_pct':100*baseline_return/baseline_stake},
      'ticket_count_distribution':{str(int(r.n_tickets)):int(r.R) for _,r in dist.iterrows()},
      'SEPTEMBER_OUTCOMES_READ':False}
    (OUT/'result_v340.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
    L=['# v340 adaptive combined-odds Dutch audit','',f'- production identity: {got[0]}R / head {got[1]} / exact3 top3 {got[2]} / {got[3]}',
       '- September 2026 outcomes unread.','- odds: official BOAT RACE closing trifecta odds.',f'- odds coverage: {covered}/{len(selected)}, missing {len(missing)}.',
       f"- actions: {result['actions']}",f"- adaptive: bought {len(bought)}R, hits {int(bought.hit.sum())}, ROI {result['adaptive']['roi_pct']:.2f}%, profit {ret-stake:+.0f} yen",
       f"- baseline top3 all covered: {covered}R, hits {int(z.baseline_hit.sum())}, ROI {result['baseline_top3_all_covered']['roi_pct']:.2f}%, profit {baseline_return-baseline_stake:+.0f} yen",
       f"- ticket count distribution: {result['ticket_count_distribution']}"]
    (OUT/'summary_v340.md').write_text('\n'.join(L)+'\n',encoding='utf-8'); print(json.dumps(result,indent=2,ensure_ascii=False),flush=True)

if __name__=='__main__': main()
