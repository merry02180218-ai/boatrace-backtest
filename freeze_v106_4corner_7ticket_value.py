"""v106: freeze the v105 4-corner 7-ticket value hybrid for prospective use.

Prospective start: 2026-09-05.
Everything that can affect V106 ticket ordering is frozen using data available
through 2026-08-31. No Sep-05+ result, payout, or final odds may update this file.

Frozen stack:
- head = 4 (head selection itself is unchanged)
- role layer = v96 2nd/3rd role model, lambda 0.10
- value layer = v105 exact-7 price tendency, lambda 0.15
- ticket count = exactly 7

Important: target-race final odds are NEVER used by this prospective model.
The value constants are historical, pre-freeze pattern tendencies only.
"""
from __future__ import annotations

import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

import analyze_v96_4corner_monthly_walkforward_tiebreak as c4

SRC='analysis_v93_4corner_second_third.csv'
ODDS_CACHE='cache_v104_final_odds.csv'
OUT='v106_4corner_7ticket_frozen_20260905.json'
SUMMARY='summary_v106_4corner_freeze.md'
TRAIN_END='2026-08-31'
PROSPECTIVE_START='2026-09-05'
HEAD=4
ROLE_LAMBDA=0.10
VALUE_LAMBDA=0.15
TICKETS=7
MIN_PRICE_N=15
A=55.0
S=67.0


def ff(x,d=0.0):
    try:
        if x is None or str(x).strip()=='': return d
        return float(x)
    except Exception: return d


def load_cache():
    out={}
    with open(ODDS_CACHE,encoding='utf-8-sig',newline='') as f:
        for r in csv.DictReader(f):
            code=(r.get('race_code') or '').strip()
            combo=(r.get('combo') or '').strip()
            o=ff(r.get('odds'),0.0)
            if code and combo and o>1:
                out.setdefault(code,{})[combo]=o
    return {c:d for c,d in out.items() if len(d)>=100}


def pairs():
    bs=list(c4.BOATS)
    return [(a,b) for a in bs for b in bs if a!=b]


def price_freeze(rs,fmap):
    # Reproduce the endpoint state of v104/v105 prior-price scoring at 2026-09-01:
    # every cached race in the 4C source that occurred by Aug-31 contributes once.
    sums=defaultdict(float); counts=defaultdict(int)
    seen=set()
    for r in sorted(rs,key=lambda z:(z.get('date',''),z.get('race_code',''))):
        if r.get('date','')>TRAIN_END: continue
        code=(r.get('race_code') or '').strip()
        if not code or code in seen: continue
        seen.add(code)
        od=fmap.get(code)
        if not od: continue
        for a,b in pairs():
            t=f'{HEAD}-{a}-{b}'
            o=od.get(t)
            if o and o>1:
                sums[t]+=1.0/o; counts[t]+=1
    known=[]
    for a,b in pairs():
        t=f'{HEAD}-{a}-{b}'
        n=counts.get(t,0)
        if n>=MIN_PRICE_N:
            known.append((t,sums[t]/n,n))
    known.sort(key=lambda x:x[1])  # lower market implied rate = more value
    den=max(1,len(known)-1)
    ranks={t:i for i,(t,_,_) in enumerate(known)}
    out={}
    for a,b in pairs():
        t=f'{HEAD}-{a}-{b}'
        n=counts.get(t,0)
        avg=(sums[t]/n) if n else None
        score=(1.0-ranks[t]/den) if t in ranks else None
        out[t]={'count':n,'mean_final_implied_rate':avg,'value_score':score}
    return out,len(seen),sum(1 for x in out.values() if x['value_score'] is not None)


def main():
    rs=c4.read()
    # Exactly the v96 role fit that would be available immediately before Sep-2026.
    tr=c4.headrows_before(rs,'2026-09')
    if len(tr)<c4.MIN_TRAIN:
        raise RuntimeError(f'role training rows too small: {len(tr)}')
    mu,sd=c4.scalers(tr)
    w2=c4.fit(tr,'second',mu,sd)
    w3=c4.fit(tr,'third',mu,sd)
    fmap=load_cache()
    price,source_codes,priced_patterns=price_freeze(rs,fmap)

    model={
      'version':'v106',
      'status':'PROSPECTIVE_SHADOW_NOT_PRODUCTION',
      'prospective_start':PROSPECTIVE_START,
      'training_end':TRAIN_END,
      'head':HEAD,
      'tickets':TICKETS,
      'boats':list(c4.BOATS),
      'features':list(c4.FEATS),
      'role_lambda':ROLE_LAMBDA,
      'value_lambda':VALUE_LAMBDA,
      'role_training_head_hit_rows':len(tr),
      'role_l2':c4.L2,'role_iters':c4.ITERS,'role_lr':c4.LR,
      'mu':dict(zip(c4.FEATS,mu)),
      'sd':dict(zip(c4.FEATS,sd)),
      'weight_labels':list(c4.FEATS)+[f'boat_{b}' for b in c4.BOATS],
      'w_second':w2,'w_third':w3,
      'price_min_history_n':MIN_PRICE_N,
      'price_source_cached_races':source_codes,
      'priced_patterns':priced_patterns,
      'price_patterns':price,
      'source_sha256':{
        SRC:hashlib.sha256(Path(SRC).read_bytes()).hexdigest(),
        ODDS_CACHE:hashlib.sha256(Path(ODDS_CACHE).read_bytes()).hexdigest(),
      },
      'rules':{
        'head_selection':'UNCHANGED_CURRENT_4C',
        'candidate_gate':'UNCHANGED',
        'base_score_and_grade':'UNCHANGED',
        'corr20_score':'SHADOW_LINEAGE_ONLY',
        'entry_gate':'target boat 4 must remain exhibition course 4',
        'wind':'UNCHANGED',
        'current7':'must be frozen from actual production ticket order before result',
        'role7':'frozen role layer only',
        'v106_7':'role layer plus frozen historical value tendency',
        'target_race_final_odds':'POST_RESULT_EVALUATION_ONLY',
        'future_update':'NO Sep-05+ outcomes or final odds may update weights/value constants',
      },
      'formal_adoption_rule':{
        'minimum_base_A_settled_races':100,
        'minimum_base_A_head_wins':30,
        'minimum_base_S_settled_races':50,
        'minimum_base_S_head_wins':15,
        'both_A_and_S_overall_hit_nonworse_vs_current7':True,
        'both_A_and_S_head_coverage_nonworse_vs_current7':True,
        'both_A_and_S_avg_final_composite_rate_reduction_min_pt':0.5,
        'minimum_final_odds_coverage_pct':80.0,
        'both_A_and_S_roi_diff_floor_pt':-5.0,
        'decision':'only after all conditions; otherwise shadow continues'
      }
    }
    Path(OUT).write_text(json.dumps(model,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

    L=['# v106 4カド7点 prospective 固定','',
       f'- prospective開始: **{PROSPECTIVE_START}**',
       f'- 学習・価格履歴の最終日: **{TRAIN_END}**',
       f'- 役割モデル学習4号艇頭的中: **{len(tr)}R**',
       f'- role λ: **{ROLE_LAMBDA:.2f}固定**',
       f'- value λ: **{VALUE_LAMBDA:.2f}固定**',
       f'- 点数: **7点固定**',
       f'- frozen価格パターン: **{priced_patterns}/20** / source cached races **{source_codes}R**','',
       '## 結果前に必ず凍結する3系列',
       '- **CURRENT7**: 実際のproduction相手順位からの7点。',
       '- **ROLE7**: v96役割別順位だけの7点。',
       '- **V106_7**: ROLE7 + value λ=0.15。','',
       '## no-leak',
       '- 対象レース自身の確定オッズは買い目作成に使わない。',
       '- v106の価格補正は2026-08-31までに確定済みの過去パターン定数だけ。',
       '- 9/5以降の結果・払戻・確定オッズで重みや価格定数を更新しない。',
       '- 候補抽出、4号艇頭判定、production score/A/S、進入除外、風評価は変更しない。','',
       '## 正式production採用の事前固定条件',
       '- BASE A以上: **100R以上かつ4号艇頭30R以上**。',
       '- BASE S以上: **50R以上かつ4号艇頭15R以上**。',
       '- A/SともV106_7の総合的中率と頭内coverageがCURRENT7以上。',
       '- A/Sとも平均確定合成オッズ率がCURRENT7より **0.5pt以上低い**。',
       '- 確定合成オッズ率を比較できるsettled rowが各級 **80%以上**。',
       '- A/Sともequal-stake ROI差がCURRENT7比 **-5pt以上**。',
       '- 全条件を満たした後だけproduction採用を再判定する。満たすまではshadow継続。']
    Path(SUMMARY).write_text('\n'.join(L)+'\n',encoding='utf-8')
    print('\n'.join(L),flush=True)

if __name__=='__main__': main()
