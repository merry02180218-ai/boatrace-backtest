#!/usr/bin/env python3
"""v218 SHADOW: current 3-head LIVE + current official odds + odds-aware point choice.

Production decision itself is unchanged: v165 p3head>=.30. For BUY races, reconstruct
v166 lambda=1.00 all 20 pairs, fetch current official 3T odds, evaluate TopN N=4..15,
and Dutch 10,000 yen for each N.

SHADOW point choice only:
  estimated_topN_hit = p3head * normalized_v166_massN
  shadow_EV_multiple = estimated_topN_hit * composite_odds
Select N with maximum shadow_EV_multiple among fully funded candidates. This is NOT
production-adopted until genuinely unseen prospective validation.

Important LIVE safeguards:
- odds are fetched only after the v165 BUY gate;
- Hamilton allocation remains the canonical 100-yen-unit Dutch implementation;
- a TopN candidate is ineligible when Hamilton gives any selected ticket 0 yen,
  because otherwise model TopN/composite mass and actually purchased tickets diverge;
- every BUY run writes an immutable timestamped freeze JSON containing the exact odds
  snapshot, candidates, selected tickets and fetch timestamp before any result lookup.
"""
from __future__ import annotations
import csv,json,re
from datetime import date
from pathlib import Path
import numpy as np,pandas as pd
from analyze_v108_1head_feasibility import feature_row,bycode
from analyze_v166_3head_pair_direct import fit as fit_pair
from analyze_v211_3head_variable_points_newroi import pair_distribution
from analyze_v205_3head_operational_replay import round_dutch
from predict_v192_3head_live_manual import fit_head,exact_prior_bias,build_manual_maps
from backtest import rows
from boatrace_live_odds3t import fetch_odds3t

ROOT=Path(__file__).resolve().parent
INPUT=ROOT/'live_input_3head.json'; SRC=ROOT/'analysis_v108_1head_feasibility.csv'; SCHEMA=ROOT/'analysis_v165_3head_schema.json'
OUT=ROOT/'prediction_v218_3head_live_odds_shadow.json'; SUMMARY=ROOT/'summary_v218_3head_live_odds_shadow.md'
FREEZE_DIR=ROOT/'live_freeze'/'v218_3head'
CUT=.30; BANK=10000; NS=tuple(range(4,16))

def calc_candidate(n,ordered,masses,odds,p3):
    ts=ordered[:n]; vals=[]
    for t in ts:
        v=float(odds.get(t,float('nan')))
        if not np.isfinite(v) or v<=0:return None
        vals.append(v)
    stakes=round_dutch(vals,BANK)
    if len(stakes)!=n or int(np.sum(stakes))!=BANK:
        raise RuntimeError(f'Dutch allocation invariant failed N={n}: stakes={stakes} total={int(np.sum(stakes))}')
    zero=[t for t,s in zip(ts,stakes) if int(s)<=0]
    comp=float(1.0/sum(1.0/v for v in vals))
    mass=float(masses.get(n,np.nan))
    est_hit=float(p3*mass) if np.isfinite(mass) else np.nan
    ev=float(est_hit*comp) if np.isfinite(est_hit) else np.nan
    tickets=[{'combo':t,'odds':float(v),'stake':int(s),'equal_return':float(v*s)} for t,v,s in zip(ts,vals,stakes)]
    return {'points':n,'composite_odds':comp,'v166_mass':mass,'estimated_hit_prob':est_hit,
            'shadow_ev_multiple':ev,'fully_funded':not zero,'zero_stake_combos':zero,'tickets':tickets}

def freeze_snapshot(res,snap):
    FREEZE_DIR.mkdir(parents=True,exist_ok=True)
    stamp=re.sub(r'[^0-9]','',str(snap['fetched_at_jst']))[:14]
    p=FREEZE_DIR/f"{res['race_code']}_{stamp}.json"
    payload={**res,'frozen_full_odds':snap['odds']}
    # Never silently overwrite a pre-deadline snapshot. Same-second duplicate is an error.
    with p.open('x',encoding='utf-8') as f:
        json.dump(payload,f,ensure_ascii=False,indent=2)
        f.write('\n')
    return str(p.relative_to(ROOT))

def main():
    j=json.loads(INPUT.read_text(encoding='utf-8'));hd=date.fromisoformat(j['date']);venue=str(j['venue']).zfill(2);rno=int(j['race'])
    code=f"{hd:%Y%m%d}{venue}{rno:02d}"; y=hd.strftime('%Y/%m/%d')
    cards=bycode(rows(f'data/programs/race_cards/{y}.csv'));waku=bycode(rows(f'data/programs/waku10/{y}.csv'))
    if code not in cards or code not in waku:raise RuntimeError(f'card/waku not available for {code}')
    bias,bias_days=exact_prior_bias(hd);tk,stt,orig=build_manual_maps(code,j)
    fr=feature_row(hd.isoformat(),cards[code],waku[code],tk,stt,orig,bias)
    if fr is None:raise RuntimeError('entry changed/excluded')
    schema=json.loads(SCHEMA.read_text(encoding='utf-8'));srcdf=pd.read_csv(SRC)
    hm,nums,cats,ntrain=fit_head(srcdf,schema['features'],'venue' if 'venue' in srcdf.columns else None,hd)
    x=pd.DataFrame([{c:fr.get(c,np.nan) for c in nums+cats}]);p=float(hm.predict_proba(x)[0,1])
    res={'date':hd.isoformat(),'venue':venue,'race':rno,'race_code':code,'boat3':cards[code].get('艇3_選手名',''),'p3head':p,'cut':CUT,'decision':'BUY' if p>=CUT else 'SKIP','status':'SHADOW_ODDS_AWARE','head_train_rows':ntrain,'prior_st_bias_days':bias_days,'manual_input':j}
    snap=None
    if p<CUT:
        res.update({'v166_lambda':1.0,'rank20':[],'odds_snapshot':None,'point_candidates':[],'shadow_choice':None,'freeze_file':None})
    else:
        hist=[]
        with SRC.open(encoding='utf-8-sig',newline='') as f:
            for r in csv.DictReader(f):
                if r.get('date','')<hd.isoformat():hist.append(r)
        pm,pair_n=fit_pair(hist);ordered,effn,ent,_=pair_distribution(fr,pm)
        import analyze_v166_3head_pair_direct as v166
        score={}
        for s in v166.OPP:
            for t in v166.OPP:
                if s==t:continue
                q=float(pm.predict_proba(np.asarray([v166.pvec(fr,s,t)],float))[0,1]);score[f'3-{s}-{t}']=max(q,1e-12)
        den=sum(score.values()); probs=[score[t]/den for t in ordered];masses={n:float(sum(probs[:n])) for n in NS}
        snap=fetch_odds3t(f'{hd:%Y%m%d}',venue,rno)
        cs=[calc_candidate(n,ordered,masses,snap['odds'],p) for n in NS];cs=[c for c in cs if c]
        eligible=[c for c in cs if c['fully_funded']]
        choice=max(eligible,key=lambda c:(c['shadow_ev_multiple'],-c['points'])) if eligible else None
        res.update({'v166_lambda':1.0,'pair_train_3wins':pair_n,'rank20':ordered,'effn':effn,'entropy':ent,
                    'odds_snapshot':{k:v for k,v in snap.items() if k!='odds'},'point_candidates':cs,'shadow_choice':choice,
                    'freeze_file':None})
        # Freeze before any downstream settlement/result processing. No result data is read here.
        res['freeze_file']=freeze_snapshot(res,snap)
    OUT.write_text(json.dumps(res,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    L=[f"# v218 SHADOW live odds-aware 3-head {hd} {venue} {rno}R",'',f"- boat3: **{res['boat3']}**",f"- v165 p3head: **{100*p:.2f}%**",f"- decision: **{res['decision']}** (production cut 30%)",'- production point rule is NOT changed; odds-aware point choice below is SHADOW only.','- July/August are non-pristine/overfit and are not validation evidence for this rule.']
    if res['decision']=='BUY':
        s=res['odds_snapshot'];L += [f"- odds source: **{s['source']}**",f"- odds fetched: **{s['fetched_at_jst']}**",f"- immutable freeze: **{res['freeze_file']}**",'','## TopN candidates','|N|composite|v166 mass|est hit|shadow EV|funded|','|---:|---:|---:|---:|---:|:---:|']
        for c in res['point_candidates']:L.append(f"|{c['points']}|{c['composite_odds']:.3f}|{100*c['v166_mass']:.1f}%|{100*c['estimated_hit_prob']:.2f}%|{c['shadow_ev_multiple']:.3f}|{'yes' if c['fully_funded'] else 'NO'}|")
        c=res['shadow_choice']
        if c:
            L += ['','## SHADOW choice',f"- points: **{c['points']}**",f"- composite odds: **{c['composite_odds']:.3f}**",f"- shadow EV multiple: **{c['shadow_ev_multiple']:.3f}**",'','|combo|odds|stake|approx equal return|','|---|---:|---:|---:|']
            for t in c['tickets']:L.append(f"|{t['combo']}|{t['odds']:.1f}|{t['stake']}|{t['equal_return']:.0f}|")
        else:
            L += ['','- No SHADOW choice: every TopN candidate contained at least one 0-yen Hamilton allocation.']
    else:L += ['','- SKIP: current v165 did not reach 30%; no odds-aware tickets are produced.']
    SUMMARY.write_text('\n'.join(L)+'\n',encoding='utf-8');print('\n'.join(L))
if __name__=='__main__':main()
