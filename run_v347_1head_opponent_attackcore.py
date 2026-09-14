#!/usr/bin/env python3
from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path
import json, math, pickle

import numpy as np
import pandas as pd

from backtest import rows
import onehead_production_profile as prod
import run_v299_1head_trifecta3_policy_search as v299
import run_v312_1head_opponent_outer_gate as v312
import run_v320_1head_exact3_ticket_policy as v320
import run_v326_1head_ticketaware_exhibition as v326
import run_v337_1head_head_cutoff_volume as v337
import run_v346_1head_v345_production_regression as v346

OUT=Path('/tmp/v347'); OUT.mkdir(parents=True,exist_ok=True)
GAMMAS=(0.0,0.5,1.0,1.5,2.0)
DEV_MONTHS=('2026-02','2026-03','2026-04','2026-05','2026-06')
SUPPORT_MONTHS=('2026-07','2026-08')
BOATS=(2,3,4,5,6)


def norm(q):
    s=sum(max(float(v),0.0) for v in q.values())
    if s<=0: return {k:1.0/len(q) for k in q}
    return {k:max(float(v),0.0)/s for k,v in q.items()}


def tilt_p2(p2,core,gamma):
    if gamma==0: return {int(k):float(v) for k,v in p2.items()}
    q={int(b):float(p2[b])*math.exp(gamma*(float(core[b])-.5)) for b in BOATS}
    return norm(q)


def tilt_pc(pc,core,gamma):
    if gamma==0: return {(int(s),int(t)):float(v) for (s,t),v in pc.items()}
    out={}
    for s in BOATS:
        q={t:float(pc[(s,t)])*math.exp(gamma*(float(core[t])-.5)) for t in BOATS if t!=s}
        q=norm(q)
        for t,v in q.items(): out[(s,t)]=v
    return out


def current_selected():
    if not prod.SEPTEMBER_OUTCOMES_MUST_REMAIN_UNREAD: raise AssertionError('September guard disabled')
    base=v337.load_candidate_base()
    old_y,_,_=v337.build_exhibition(base)
    old_pre,old_sel,_,_=v337.eval_cut(old_y,prod.HEAD_CUTOFF)
    if (len(old_sel),int(old_sel.head_hit.sum()),int(old_sel.hit.sum()))!=(276,241,119):
        raise AssertionError('pre-v345 sentinel drift')
    y=v346.apply_v345_attack_core(old_y)
    pre,sel,_,_=v337.eval_cut(y,prod.HEAD_CUTOFF)
    got=(len(sel),int(sel.head_hit.sum()),int(sel.hit.sum()),v346.identity_hash(sel))
    exp=(prod.CURRENT_EXPECTED_PASS_R,prod.CURRENT_EXPECTED_HEAD,prod.CURRENT_EXPECTED_EXACT3,prod.CURRENT_EXPECTED_PASS_ID_SHA256)
    if got!=exp: raise AssertionError(f'v345 identity drift {got} != {exp}')
    return sel.copy(),len(pre)


def opponent_maps():
    d,p3,p4=v312.load_cache(); d.race_code=d.race_code.astype(str).str.zfill(12)
    p2dev,pcdev=v320.build_factorized(d,p3,p4)
    with v337.SECOND.open('rb') as f: sec=pickle.load(f)
    with v337.THIRD.open('rb') as f: third=pickle.load(f)
    return p2dev,pcdev,sec['p2'],third


def get_dist(tm,code,p2dev,pcdev,p2ja,pcja):
    if tm in p2dev:
        return p2dev[tm][code],pcdev[tm][code]
    return p2ja[tm][code],pcja[tm][code]


def build_opponent_attackcore(ids):
    selected_days=sorted({date(int(c[:4]),int(c[4:6]),int(c[6:8])) for c in ids})
    dayset=set(selected_days); last=max(selected_days); sums=defaultdict(list); allv=[]; out={}
    d=v337.PRELOAD
    while d<=last:
        ymd=d.strftime('%Y/%m/%d'); strows=rows(f'data/previews/stt/{ymd}.csv'); bias=v326.st_bias(sums,allv)
        if d in dayset:
            tkz=v326.bycode(rows(f'data/previews/tkz/{ymd}.csv')); stt=v326.bycode(strows); orig=v326.bycode(rows(f'data/previews/original_exhibition/{ymd}.csv'))
            prefix=d.strftime('%Y%m%d')
            for code in sorted(c for c in ids if c.startswith(prefix)):
                tr=tkz.get(code,{}); sr=stt.get(code,{}); orr=orig.get(code,{})
                audit=v326.raw_completeness(tr,sr,orr)
                ready=all(audit[k] for k in ('tkz_all6','stt_all6','orig_straight_all6','orig_avg_all6'))
                if not ready: continue
                ex,st,os=v326.corrected_direct(code,tkz,stt,orig,bias)
                out[code]={b:(prod.ATTACK_CORE_W_ONE_EX*ex[b]+prod.ATTACK_CORE_W_ONE_ST*st[b]+prod.ATTACK_CORE_W_ONE_STRAIGHT*os[b]['straight']+prod.ATTACK_CORE_W_ONE_ORIG_AVG*os[b]['avg']) for b in BOATS}
        v326.update_st(strows,sums,allv); d+=timedelta(days=1)
    return out


def tickets(p2,pc):
    prob=v299.pair_prob(p2,pc,prod.TICKET_ALPHA)
    top=v299.STRATEGIES['HYBRID'](p2,pc,prob)[:3]
    return ';'.join(f'1-{s}-{t}' for s,t in top)


def evaluate(sel,cores,p2dev,pcdev,p2ja,pcja,g2,g3):
    rec=[]
    for _,r in sel.iterrows():
        tm=str(r.month); code=str(r.race_code).zfill(12)
        p2,pc=get_dist(tm,code,p2dev,pcdev,p2ja,pcja)
        core=cores.get(code)
        if core is None:
            a2={int(k):float(v) for k,v in p2.items()}; a3={(int(s),int(t)):float(v) for (s,t),v in pc.items()}
            ready=0
        else:
            a2=tilt_p2(p2,core,g2); a3=tilt_pc(pc,core,g3); ready=1
        ts=tickets(a2,a3); actual=str(r.actual_combo)
        parts=actual.split('-'); a1=int(parts[0]) if len(parts)==3 and parts[0].isdigit() else 0
        rec.append({'month':tm,'race_code':code,'head_hit':int(a1==1),'actual_combo':actual,'tickets':ts,'hit':int(actual in ts.split(';')),'core_ready':ready})
    z=pd.DataFrame(rec)
    dev=z[z.month.isin(DEV_MONTHS)]; sup=z[z.month.isin(SUPPORT_MONTHS)]
    mon=z.groupby('month').agg(R=('race_code','size'),head=('head_hit','sum'),hits=('hit','sum')).reset_index(); mon['rate']=mon.hits/mon.R
    dmon=mon[mon.month.isin(DEV_MONTHS)]
    return z,{
        'g2':g2,'g3':g3,'R':len(z),'head':int(z.head_hit.sum()),'hits':int(z.hit.sum()),'rate':float(z.hit.mean()),
        'dev_R':len(dev),'dev_hits':int(dev.hit.sum()),'dev_rate':float(dev.hit.mean()),'dev_worst_month':float(dmon.rate.min()),
        'support_R':len(sup),'support_hits':int(sup.hit.sum()),'support_rate':float(sup.hit.mean()),'ready_R':int(z.core_ready.sum())
    },mon


def main():
    sel,pre_R=current_selected(); ids=set(sel.race_code.astype(str).str.zfill(12))
    p2dev,pcdev,p2ja,pcja=opponent_maps()
    cores=build_opponent_attackcore(ids)
    rowsum=[]; allrace=[]; allmon=[]
    for g2 in GAMMAS:
        for g3 in GAMMAS:
            z,m,mon=evaluate(sel,cores,p2dev,pcdev,p2ja,pcja,g2,g3)
            z['g2']=g2; z['g3']=g3; allrace.append(z); rowsum.append(m); mon['g2']=g2;mon['g3']=g3;allmon.append(mon)
    sm=pd.DataFrame(rowsum); race=pd.concat(allrace,ignore_index=True); monthly=pd.concat(allmon,ignore_index=True)
    base=sm[(sm.g2==0)&(sm.g3==0)].iloc[0]
    if (int(base['R']),int(base['head']),int(base['hits']))!=(276,241,121): raise AssertionError(f'baseline ticket regeneration drift {base.to_dict()}')
    sm['delta_hits']=sm.hits-int(base['hits']); sm['delta_dev_hits']=sm.dev_hits-int(base['dev_hits']); sm['delta_support_hits']=sm.support_hits-int(base['support_hits'])
    cand=sm[~((sm.g2==0)&(sm.g3==0))].copy()
    best=cand.sort_values(['dev_hits','dev_worst_month','support_hits','hits'],ascending=False).iloc[0]
    bz=race[(np.isclose(race.g2,float(best.g2)))&(np.isclose(race.g3,float(best.g3)))].copy()
    b0=race[(race.g2==0)&(race.g3==0)].copy(); cmp=b0[['race_code','month','hit','tickets']].rename(columns={'hit':'base_hit','tickets':'base_tickets'}).merge(bz[['race_code','hit','tickets']].rename(columns={'hit':'attack_hit','tickets':'attack_tickets'}),on='race_code')
    cmp['delta']=cmp.attack_hit-cmp.base_hit
    sm.to_csv(OUT/'v347_grid.csv',index=False); monthly.to_csv(OUT/'v347_monthly.csv',index=False); cmp.to_csv(OUT/'v347_best_race_delta.csv',index=False)
    result={'profile':prod.PROFILE_NAME,'pre_R':pre_R,'pass_R':len(sel),'head':int(sel.head_hit.sum()),'baseline_hits':int(base['hits']),'baseline_rate':float(base['rate']),'opponent_attackcore_weights':{'ex':prod.ATTACK_CORE_W_ONE_EX,'st':prod.ATTACK_CORE_W_ONE_ST,'straight':prod.ATTACK_CORE_W_ONE_STRAIGHT,'orig_avg':prod.ATTACK_CORE_W_ONE_ORIG_AVG},'ready_R':len(cores),'grid_gammas':GAMMAS,'best':best.to_dict(),'best_gain_R':int((cmp.delta==1).sum()),'best_loss_R':int((cmp.delta==-1).sum()),'SEPTEMBER_OUTCOMES_READ':False,'JUL_AUG_STATUS':'NON_PRISTINE_SUPPORT_ONLY','PRODUCTION_CHANGED':False}
    (OUT/'result_v347.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    bm=monthly[(np.isclose(monthly.g2,float(best.g2)))&(np.isclose(monthly.g3,float(best.g3)))]
    lines=['# v347 opponent attackCore rerank','',f'- Fixed v345 production PASS: {len(sel)}R / head {int(sel.head_hit.sum())}.',f'- Control HYBRID alpha=.70: {int(base["hits"])}/{len(sel)} = {100*base["rate"]:.2f}%.',f'- Opponent attackCore ready: {len(cores)}/{len(sel)}R.',f'- Same v345 weights per opponent: EX .40 / ST .25 / straight .15 / original-average .20.','- SECOND p2 is exponentially tilted by g2; conditional THIRD pc by target boat attackCore with g3.','- Candidate choice uses Feb-Jun development hits then worst-month; Jul/Aug are support only. September outcomes unread.','',f"## Best research candidate\n- g2={best.g2:.1f}, g3={best.g3:.1f}: all {int(best.hits)}/{int(best.R)}={100*best.rate:.2f}% ({int(best.delta_hits):+d} hits).",f"- Feb-Jun: {int(best.dev_hits)}/{int(best.dev_R)}={100*best.dev_rate:.2f}% ({int(best.delta_dev_hits):+d} hits vs control).",f"- Jul-Aug support: {int(best.support_hits)}/{int(best.support_R)}={100*best.support_rate:.2f}% ({int(best.delta_support_hits):+d} hits vs control).",f"- Race-level swaps: +hit {int((cmp.delta==1).sum())}R / -hit {int((cmp.delta==-1).sum())}R.",'','## Monthly best','|month|R|hits|rate|','|---|---:|---:|---:|']
    for _,r in bm.iterrows(): lines.append(f'|{r.month}|{int(r.R)}|{int(r.hits)}|{100*r.rate:.2f}%|')
    lines+=['','- Research only: production profile is unchanged.']
    (OUT/'summary_v347.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print((OUT/'summary_v347.md').read_text(),flush=True)

if __name__=='__main__': main()
