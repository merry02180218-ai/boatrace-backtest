#!/usr/bin/env python3
"""Post-deadline NON-PRISTINE smoke test for the two 2026-09-10 frozen PRE candidates.

Decision construction is result-blind for the target day:
- current target rows use programs/previews only;
- v221 current-day result feed is forcibly blanked before history feature building;
- official odds3t is the only current odds endpoint;
- no target result/payout is loaded or settled.

This is an operational integration smoke test, NOT pristine/live performance evidence.
"""
from __future__ import annotations
from collections import defaultdict
from datetime import date
import hashlib, json
import numpy as np
import pandas as pd

import analyze_v108_1head_feasibility as v108
import analyze_v165_3head_monthly_walkforward as v165
import analyze_v221_3head_scenario_pair as v221
import analyze_v222_3head_broad_feature_audit as v222
import analyze_v223_3head_unused_feature_audit as v223
import analyze_v224_3head_national_form_decompose as v224
import analyze_v234_3head_waku10_restored_replay as v234
import analyze_v242_3head_target_comp3_min5_max10 as v242
import fetch_live_trifecta_odds as live
from backtest import rows

TARGETS=[('児島',16,5,'平田さやか'),('鳴門',14,7,'今井美亜')]
DAY=date(2026,9,10); FIRST=pd.Timestamp('2026-09-01'); NEXT=pd.Timestamp('2026-10-01')
KEEP=-0.1999999999999999; RESCUE=0.5672342857142857
OUT='smoke_20260910_3head_live_bridge.json'
TXT='smoke_20260910_3head_live_bridge.txt'


def bycode(rs):
    return {str(r.get('レースコード','')).zfill(12):r for r in rs if r.get('レースコード')}


def learn_bias(end=date(2026,9,9),start=date(2026,8,1)):
    sums=defaultdict(list); allv=[]; d=start
    while d<=end:
        for r in rows(f'data/previews/stt/{d:%Y/%m/%d}.csv'):
            for b in range(1,7):
                try:v=float(r.get(f'艇{b}_スタート展示'))
                except Exception:continue
                if -.30<v<1.0:sums[b].append(v);allv.append(v)
        d+=pd.Timedelta(days=1)
        if hasattr(d,'date'): d=d.date()
    g=float(np.mean(allv)) if allv else .15
    return {b:(float(np.mean(sums[b]))-g if sums[b] else 0.) for b in range(1,7)}


def make_current_base():
    y='2026/09/10'; cards=bycode(rows(f'data/programs/race_cards/{y}.csv')); waku=bycode(rows(f'data/programs/waku10/{y}.csv'))
    tkz=bycode(rows(f'data/previews/tkz/{y}.csv')); stt=bycode(rows(f'data/previews/stt/{y}.csv')); orig=bycode(rows(f'data/previews/original_exhibition/{y}.csv'))
    bias=learn_bias(); out=[]
    for name,jcd,rno,racer in TARGETS:
        code=f'20260910{jcd:02d}{rno:02d}'
        if code not in cards or code not in waku: raise RuntimeError(f'missing card/waku {code}')
        z=v108.feature_row('2026-09-10',cards[code],waku[code],tkz,stt,orig,bias)
        if z is None: raise RuntimeError(f'v108 feature_row rejected {code}')
        z.update({'winner':0,'valid_result':0,'actual_combo':'','valid_payout':0,'payout100':0})
        out.append(z)
    return pd.DataFrame(out)


def build_augmented():
    # Restore historical Waku10 exactly as canonical v234, then extend feature builders to Sep10.
    cov=v234.reconstruct()
    if (cov.source=='missing').any(): raise RuntimeError('historical restored Waku10 still missing')
    raw=pd.read_csv(v224.SRC,dtype={'race_code':str}); cur=make_current_base()
    raw=pd.concat([raw,cur],ignore_index=True,sort=False)
    dc=v165.pc(raw,['date','race_date','ymd']); vc=v165.pc(raw,['venue','jcd','stadium','place']); y,_=v165.target(raw); basefs=v165.feats(raw)
    raw['_date']=pd.to_datetime(raw[dc].astype(str),errors='coerce'); raw['_y']=y
    raw=raw[raw._date.notna() & (raw._date<NEXT)].copy()

    # Extend builders through current day, but target-day results are NEVER made available to v221.
    v221.CONTAM=NEXT; v221.END=DAY
    old221=v221.day_fetch
    def safe221(d):
        dd,z=old221(d)
        if d==DAY:z=dict(z);z['res']=[]
        return dd,z
    v221.day_fetch=safe221

    v222.CONTAM=NEXT; v222.END=DAY
    old222=v222.day_fetch
    def safe222(d):
        dd,z=old222(d);z=dict(z)
        if d<=date(2026,8,31):
            rr=v234.local_rows(d)
            if rr:z['waku']=rr
        return dd,z
    v222.day_fetch=safe222
    v223.CONTAM=NEXT; v224.CONTAM=NEXT

    d=v221.build(raw,dc)
    d=v222.build_current(d,dc)
    d=v223.build_unused(d,dc)
    d=v224.add_decomp(d,dc)
    fs=[x for x in v234.full_features(d,basefs) if x in d.columns]
    return d,vc,basefs,fs


def fetch_odds(jcd,rno):
    params={'rno':rno,'jcd':f'{jcd:02d}','hd':'20260910'}
    r=live.safe_get(live.BASE,params); html=r.text; parsed=live.parse_odds(html)
    exp=live.expected_combos()
    if set(parsed)!=exp or len(parsed)!=120: raise RuntimeError(f'odds incomplete jcd={jcd} r={rno}: {len(parsed)}')
    return {f'{a}-{b}-{c}':float(o) for (a,b,c),o in parsed.items()}, {
        'resolved_url':r.url,'parsed_count':len(parsed),'html_sha256':hashlib.sha256(html.encode('utf-8',errors='replace')).hexdigest(),
        'result_endpoint_requested':False,'payout_endpoint_requested':False,'post_deadline_smoke_test':True}


def dutch(ts,vals):
    stakes=np.asarray(v234.v205.round_dutch(vals,10000),int)
    if int(stakes.sum())!=10000:raise RuntimeError('Dutch sum invariant')
    return [{'combo':q,'odds':float(o),'stake':int(s)} for q,o,s in zip(ts,vals,stakes) if s>0]


def main():
    d,vc,basefs,fs=build_augmented(); tr=d[d._date<FIRST].copy()
    pair=v222.fit_pair(tr,'V221')
    te,nfeat=v223.fit_head(d,fs,vc,FIRST,NEXT)
    results=[]
    for name,jcd,rno,racer in TARGETS:
        code=f'20260910{jcd:02d}{rno:02d}'; q=te[te.race_code.astype(str).str.zfill(12)==code]
        if len(q)!=1:raise RuntimeError(f'target inference row count {code}={len(q)}')
        r=q.iloc[0]; p3=float(r._p)
        ts=v242.safe_order(r,pair)
        if ts is None:raise RuntimeError(f'pair-rank-invalid {code}')
        odds,meta=fetch_odds(jcd,rno); ch=v242.choose_n(ts,odds)
        raw_n=ch.get('raw_n'); raw_comp=ch.get('raw_comp'); action=ch.get('action')
        top_n=ch.get('top_n'); comp_odds=ch.get('comp_odds')
        minus=float(r.get('c_b3_minus_b5_st')); attack=float(r.get('c_attack3_stretch'))
        v242_buyable=(action=='bet')
        base=bool(v242_buyable and p3>=.45 and raw_n is not None and 7<=raw_n<=18 and comp_odds is not None and 3.05<=comp_odds<=4.0)
        keep=bool(np.isfinite(minus) and minus>=KEEP); rescue=bool(np.isfinite(attack) and attack<=RESCUE)
        final=bool(v242_buyable and ((base and keep) or ((not base) and rescue)))
        tickets=[]
        if final:
            n=int(top_n); vals=[float(odds[x]) for x in ts[:n]]; tickets=dutch(ts[:n],vals)
        results.append({'race':f'{name}{rno}R','race_code':code,'racer3':racer,'pre_grade':'A','non_pristine_post_deadline_smoke_test':True,
          'p3':p3,'pair_order20':ts,'raw_top_n':raw_n,'raw_comp_odds':raw_comp,'v242_action':action,'purchased_top_n':top_n,
          'comp_odds':comp_odds,'f__c_b3_minus_b5_st':minus,'keep_pass':keep,'f__c_attack3_stretch':attack,'rescue_pass':rescue,
          'v243_base':base,'official_final_bet':final,'tickets':tickets,'total_stake':sum(x['stake'] for x in tickets),'odds_snapshot':meta,
          'model_features':nfeat})
    obj={'date':'2026-09-10','mode':'NON-PRISTINE post-deadline integration smoke test','target_result_or_payout_used':False,
         'canonical_chain':'v249 PRE A -> v243 final -> v242 variable 5-10 -> 10000 yen Dutch','results':results}
    open(OUT,'w',encoding='utf-8').write(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
    lines=[f"{x['race']} p3={x['p3']:.6f} rawN={x['raw_top_n']} rawComp={x['raw_comp_odds']} topN={x['purchased_top_n']} comp={x['comp_odds']} base={x['v243_base']} keep={x['keep_pass']} rescue={x['rescue_pass']} FINAL={x['official_final_bet']}" for x in results]
    for x in results:
        if x['tickets']:
            lines += [f"  {t['combo']} odds={t['odds']:.1f} stake={t['stake']}" for t in x['tickets']]
            lines.append(f"  TOTAL={x['total_stake']}")
    open(TXT,'w',encoding='utf-8').write('\n'.join(lines)+'\n');print('\n'.join(lines))

if __name__=='__main__':main()
