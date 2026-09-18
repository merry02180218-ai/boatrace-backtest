#!/usr/bin/env python3
from __future__ import annotations
"""v352: independent 3-lane wall-risk audit for the promoted 1-head LIVE operating cell.

Research only.  HEAD model stays v308; same-day exhibition is used only as a
post-ranking/final gate.  2026-09 outcomes are never read.
"""
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path
import hashlib, json

import numpy as np
import pandas as pd

from backtest import rows
import onehead_production_profile as prod
import run_v321_1head_julaug_nonpristine_validation as v321
import run_v326_1head_ticketaware_exhibition as v326
import run_v337_1head_head_cutoff_volume as v337
import run_v346_1head_v345_production_regression as v346
import run_v347_1head_opponent_attackcore as v347
import run_v351_1head_joint_roi_grid as grid

OUT=Path('/tmp/v352-wall3-risk'); OUT.mkdir(parents=True,exist_ok=True)
DEV=('2026-02','2026-03','2026-04','2026-05','2026-06')
SUP=('2026-07','2026-08')
ALL=DEV+SUP
BASIC={'head':.790,'mass':.375,'env_w':.05,'env_q':.70}
WATCH={'head':.790,'mass':.425,'env_w':.05,'env_q':.70}


def sha(lines):
    return hashlib.sha256('\n'.join(lines).encode()).hexdigest()


def pre_wall_table():
    s=pd.read_csv(v321.PREP_SLIM,dtype={'race_code':str})
    s['race_code']=s.race_code.astype(str).str.zfill(12)
    if any(s.month.astype(str).str.startswith('2026-09')):
        raise RuntimeError('September entered PRE wall table')
    def n(c): return pd.to_numeric(s[c],errors='coerce')
    for b in (3,4):
        req=[f'b{b}_pl_all_win',f'b{b}_pl_all_p2',f'b{b}_pl_frame_win',f'b{b}_pl_frame_p2',f'b{b}_pl_recent_p2']
        s[f'pre_form_b{b}']=.35*n(req[0])+.25*n(req[1])+.20*n(req[2])+.10*n(req[3])+.10*n(req[4])
        s[f'pre_startmotor_b{b}']=n(f'b{b}_nst_strength')*n(f'b{b}_motor')
    gaps=[]
    for key in ('nst_strength','motor','grade','wr','local'):
        c=f'pre_gap_{key}'; s[c]=n(f'b3_{key}')-n(f'b4_{key}'); gaps.append(c)
    s['pre_gap_form']=s.pre_form_b3-s.pre_form_b4; gaps.append('pre_gap_form')
    s['pre_gap_startmotor']=s.pre_startmotor_b3-s.pre_startmotor_b4
    s['pre_wall_gap']=s[gaps].mean(axis=1,skipna=True)
    s['pre_wall_votes']=sum((s[c]>=0).astype(float) for c in gaps)
    s['pre_wall_n']=s[gaps].notna().sum(axis=1)
    s.loc[s.pre_wall_n.eq(0),'pre_wall_votes']=np.nan
    keep=['race_code','pre_wall_gap','pre_wall_votes','pre_wall_n','pre_gap_nst_strength','pre_gap_motor','pre_gap_form','pre_gap_startmotor']
    return s[keep].drop_duplicates('race_code')


def exhibition_wall(ids:set[str]):
    days=sorted({date(int(c[:4]),int(c[4:6]),int(c[6:8])) for c in ids})
    dayset=set(days); last=max(days); sums=defaultdict(list); allv=[]; rec=[]; d=v337.PRELOAD
    while d<=last:
        ymd=d.strftime('%Y/%m/%d'); strows=rows(f'data/previews/stt/{ymd}.csv'); bias=v326.st_bias(sums,allv)
        if d in dayset:
            tkz=v326.bycode(rows(f'data/previews/tkz/{ymd}.csv'))
            stt=v326.bycode(strows)
            orig=v326.bycode(rows(f'data/previews/original_exhibition/{ymd}.csv'))
            prefix=d.strftime('%Y%m%d')
            for code in sorted(c for c in ids if c.startswith(prefix)):
                tr=tkz.get(code,{}); sr=stt.get(code,{}); orr=orig.get(code,{})
                audit=v326.raw_completeness(tr,sr,orr)
                ready=bool(audit['tkz_all6'] and audit['stt_all6'] and audit['orig_straight_all6'] and audit['orig_avg_all6'])
                ex,st,os=v326.corrected_direct(code,tkz,stt,orig,bias)
                if ready:
                    vals={
                        'ex_wall_gap':float(ex[3]-ex[4]),
                        'st_wall_gap':float(st[3]-st[4]),
                        'straight_wall_gap':float(os[3]['straight']-os[4]['straight']),
                        'avg_wall_gap':float(os[3]['avg']-os[4]['avg']),
                    }
                    vals['ex_wall_score']=.20*vals['ex_wall_gap']+.40*vals['st_wall_gap']+.25*vals['straight_wall_gap']+.15*vals['avg_wall_gap']
                    vals['attack4_score']=.20*float(ex[4])+.40*float(st[4])+.25*float(os[4]['straight'])+.15*float(os[4]['avg'])
                    vals['wall3_score']=.20*float(ex[3])+.40*float(st[3])+.25*float(os[3]['straight'])+.15*float(os[3]['avg'])
                    vals['ex_wall_votes']=float(sum(x>=0 for x in (vals['ex_wall_gap'],vals['st_wall_gap'],vals['straight_wall_gap'],vals['avg_wall_gap'])))
                else:
                    vals={k:np.nan for k in ('ex_wall_gap','st_wall_gap','straight_wall_gap','avg_wall_gap','ex_wall_score','attack4_score','wall3_score','ex_wall_votes')}
                rec.append({'race_code':code,'wall_exhibition_ready':ready,**vals})
        v326.update_st(strows,sums,allv); d+=timedelta(days=1)
    return pd.DataFrame(rec)


def selected(y,mass,head,env_w,env_q,maps,cores):
    ym=y[pd.to_numeric(y.opp_mass,errors='coerce').ge(mass)].copy()
    ym=v346.apply_v345_attack_core(ym)
    return grid.tickets(grid.eval_cfg(ym,head,env_w,env_q),maps,cores)


def met(z,cache):
    x=grid.met(z,cache)
    x['head_rate']=x['head']/x['R'] if x['R'] else np.nan
    x['exact3_rate']=x['exact3']/x['R'] if x['R'] else np.nan
    return x


def split_metrics(z,cache):
    return {
        'all':met(z,cache),
        'dev':met(z[z.month.isin(DEV)],cache),
        'support':met(z[z.month.isin(SUP)],cache),
    }


def rule_masks(z):
    ready=z.wall_exhibition_ready.fillna(False).astype(bool)
    pre_ready=pd.to_numeric(z.pre_wall_n,errors='coerce').ge(4)
    rules=[('BASE',pd.Series(True,index=z.index),{})]
    for k in (1,2,3,4):
        keep=(~pre_ready)|pd.to_numeric(z.pre_wall_votes,errors='coerce').ge(k)
        rules.append((f'PRE_VOTES_GE_{k}',keep,{'pre_votes_min':k}))
    for t in (-.20,-.15,-.10,-.05,0.0,.05):
        keep=(~pre_ready)|pd.to_numeric(z.pre_wall_gap,errors='coerce').ge(t)
        rules.append((f'PRE_GAP_GE_{t:+.2f}',keep,{'pre_gap_min':t}))
    for t in (-1.0,-.8,-.6,-.4,-.2,0.0):
        keep=(~ready)|pd.to_numeric(z.st_wall_gap,errors='coerce').gt(t)
        rules.append((f'EX_ST_GAP_GT_{t:+.1f}',keep,{'st_gap_gt':t}))
    for k in (1,2,3,4):
        keep=(~ready)|pd.to_numeric(z.ex_wall_votes,errors='coerce').ge(k)
        rules.append((f'EX_VOTES_GE_{k}',keep,{'ex_votes_min':k}))
    for t in (-.40,-.30,-.20,-.10,0.0,.10):
        keep=(~ready)|pd.to_numeric(z.ex_wall_score,errors='coerce').gt(t)
        rules.append((f'EX_SCORE_GT_{t:+.2f}',keep,{'ex_wall_score_gt':t}))
    for sg in (-.8,-.6,-.4,-.2):
        for a4 in (.60,.70,.80):
            risk=ready & pd.to_numeric(z.st_wall_gap,errors='coerce').le(sg) & pd.to_numeric(z.attack4_score,errors='coerce').ge(a4)
            rules.append((f'TARGET_ST{sg:+.1f}_A4{a4:.1f}',~risk,{'drop_if_st_gap_le':sg,'and_attack4_ge':a4}))
    for pv in (1,2):
        for sg in (-.6,-.4,-.2):
            risk=pre_ready & ready & pd.to_numeric(z.pre_wall_votes,errors='coerce').le(pv) & pd.to_numeric(z.st_wall_gap,errors='coerce').le(sg)
            rules.append((f'PREEX_PV{pv}_ST{sg:+.1f}',~risk,{'drop_if_pre_votes_le':pv,'and_st_gap_le':sg}))
    return rules


def evaluate_rules(z,cache,label):
    base=split_metrics(z,cache); rowsout=[]; monthly=[]
    for name,mask,params in rule_masks(z):
        s=z[mask].copy(); mm=split_metrics(s,cache)
        row={'universe':label,'rule':name,**params}
        for p,m in mm.items():
            for k,v in m.items(): row[f'{p}_{k}']=v
        row['retention']=mm['all']['R']/base['all']['R'] if base['all']['R'] else 0
        row['delta_head_pp']=100*(mm['all']['head_rate']-base['all']['head_rate']) if mm['all']['R'] else np.nan
        row['delta_roi_pp']=100*(mm['all']['roi']-base['all']['roi']) if mm['all']['R'] else np.nan
        rowsout.append(row)
        for mo,g in s.groupby('month'):
            monthly.append({'universe':label,'rule':name,'month':mo,**met(g,cache)})
    return pd.DataFrame(rowsout),pd.DataFrame(monthly),base


def strata(z,cache,label):
    out=[]
    st=pd.to_numeric(z.st_wall_gap,errors='coerce')
    bins=[-1.01,-.61,-.21,.21,.61,1.01]
    names=['very_weak','weak','even','strong','very_strong']
    q=z.copy();q['st_band']=pd.cut(st,bins=bins,labels=names,include_lowest=True)
    for band,g in q.groupby('st_band',observed=True): out.append({'universe':label,'feature':'st_wall_gap','band':str(band),**met(g,cache)})
    pv=pd.to_numeric(z.pre_wall_votes,errors='coerce')
    q=z.copy();q['pre_vote_band']=pv
    for band,g in q.groupby('pre_vote_band',dropna=True): out.append({'universe':label,'feature':'pre_wall_votes','band':str(int(band)),**met(g,cache)})
    return pd.DataFrame(out)


def main():
    if not prod.SEPTEMBER_OUTCOMES_MUST_REMAIN_UNREAD: raise RuntimeError('September guard disabled')
    y=grid.universe(); maps=v347.opponent_maps(); cores=v347.build_opponent_attackcore(set(y.race_code)); cache={}
    # Independent historical production sentinel before wall research.
    p=selected(y,.375,.780,.10,.65,maps,cores).sort_values('race_code').reset_index(drop=True)
    got=(len(p),int(p.head_hit.sum()),int(p.hit.sum()),sha(p.race_code.tolist()),sha((p.race_code+':'+p.tickets).tolist()))
    exp=(prod.PRODUCTION_EXPECTED_PASS_R,prod.PRODUCTION_EXPECTED_HEAD,prod.PRODUCTION_EXPECTED_EXACT3,prod.PRODUCTION_EXPECTED_PASS_ID_SHA256,prod.PRODUCTION_EXPECTED_TICKET_ID_SHA256)
    if got!=exp: raise RuntimeError(f'PRODUCTION_SENTINEL_DRIFT got={got} expected={exp}')
    basic=selected(y,**BASIC,maps=maps,cores=cores)
    watch=selected(y,**WATCH,maps=maps,cores=cores)
    ids=set(basic.race_code)|set(watch.race_code)
    pre=pre_wall_table(); ex=exhibition_wall(ids)
    allrules=[]; allmonthly=[]; allstrata=[]; bases={}
    for label,z in [('BASIC',basic),('WATCH',watch)]:
        z=z.merge(pre,on='race_code',how='left',validate='one_to_one').merge(ex,on='race_code',how='left',validate='one_to_one')
        z.to_csv(OUT/f'{label.lower()}_wall_features.csv',index=False)
        r,m,b=evaluate_rules(z,cache,label); allrules.append(r);allmonthly.append(m);allstrata.append(strata(z,cache,label));bases[label]=b
    rules=pd.concat(allrules,ignore_index=True); monthly=pd.concat(allmonthly,ignore_index=True); st=pd.concat(allstrata,ignore_index=True)
    # Volume-preserving research shortlist: at least 80% of BASIC baseline and both periods represented.
    rb=rules[rules.universe.eq('BASIC')].copy(); eligible=rb[(rb.rule!='BASE')&(rb.retention>=.80)&(rb.dev_R>=100)&(rb.support_R>=20)].copy()
    if len(eligible):
        eligible['floor_roi']=eligible[['dev_roi','support_roi']].min(axis=1)
        best=eligible.sort_values(['floor_roi','all_roi','all_head_rate','all_R'],ascending=False).iloc[0].to_dict()
    else: best=None
    rules.sort_values(['universe','all_roi','all_R'],ascending=[True,False,False]).to_csv(OUT/'rules.csv',index=False)
    monthly.to_csv(OUT/'monthly.csv',index=False);st.to_csv(OUT/'strata.csv',index=False)
    result={
        'basic_cfg':BASIC,'watch_cfg':WATCH,'production_sentinel':{'got':got,'expected':exp,'ok':True},
        'basic_base':bases['BASIC'],'watch_base':bases['WATCH'],'best_basic_retention80':best,
        'rule_count':int(rules.rule.nunique()),'SEPTEMBER_OUTCOMES_READ':False,'PRODUCTION_CHANGED':False,'AUDIT_OK':True,
    }
    (OUT/'result.json').write_text(json.dumps(result,indent=2,default=str),encoding='utf-8')
    print(json.dumps(result,indent=2,default=str),flush=True)
    print('\nTOP BASIC',flush=True)
    print(rb.sort_values(['all_roi','all_R'],ascending=False).head(20).to_string(index=False),flush=True)
    print('\nSTRATA',flush=True);print(st.to_string(index=False),flush=True)

if __name__=='__main__': main()
