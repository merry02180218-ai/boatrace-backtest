#!/usr/bin/env python3
"""Fast post-exhibition final decision for HEAD4 new-feature fixed156 production line.

Per-race path intentionally avoids the heavy POST/ENV/A full production chain.
It uses:
- current race card + waku10
- once-daily causal player/ST state through target_date-1
- current official/BOATCAST exhibition sources
- frozen v283 opponent models
- official pre-deadline trifecta odds
- frozen 156R ROI-expansion selection rule

No target-race result/payout access.
"""
from __future__ import annotations
import argparse,csv,json,math,time,hashlib,re,bisect
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,time as dtime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import requests
from build_4head_post_live import boatcast_st_url,boatcast_orig_url,BOATCAST,UA
from build_4head_v283_current_exhibition_live import parse_boatcast_st,parse_boatcast_original,original_corrected,_rank_strength
from backtest_v3 import CORR
from backtest_v51_lane_corrected_tickets import rank_scores,norm_metric
from head4_original_venue_schema import ORIG_REQUIRED,required_orig,publishes_original
from build_4head_v93_primitives_live import build as build_v93
from build_4head_v283_rows_live import derive
from head4_v291_downstream_inference import load_artifact,score_second,score_conditional_third,v283_top4,BOATS
import fetch_live_trifecta_odds as official_odds

JST=ZoneInfo('Asia/Tokyo')
PL=('all_p2','all_win','frame_p2','recent_p2','frame_win')
ST=('raw','raw_strength','raw_rank','corr_strength','corr_rank')
V93=('grade','national','local','motor','nst')
CUR=('cur_ex','cur_st','cur_orig_lap','cur_orig_turn','cur_orig_straight','cur_orig_avg')
ALPHA2=0.60
THIRD_GAP=0.10

class Fast120Error(RuntimeError):pass
class Fast120NotReady(Fast120Error):pass

def rows_local(path):
    with Path(path).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def bycode(rs):
    return {str(r.get('race_code',r.get('レースコード',''))).zfill(12):r for r in rs}

def _pstat(raw,b):
    if raw is None:
        return {'all_win':1/6,'all_p2':1/3,'frame_win':.125,'frame_p2':.25,'recent_p2':1/3}
    n=int(raw.get('n',0));w=int(raw.get('w',0));p2=int(raw.get('p2',0))
    nf=int((raw.get('nf') or {}).get(str(b),0));wf=int((raw.get('wf') or {}).get(str(b),0));p2f=int((raw.get('p2f') or {}).get(str(b),0))
    recent=list(raw.get('recent_p2') or [])
    return {
      'all_win':(w+2/6)/(n+2),
      'all_p2':(p2+2/3)/(n+2),
      'frame_win':(wf+3*.125)/(nf+3),
      'frame_p2':(p2f+3*.25)/(nf+3),
      'recent_p2':sum(recent)/len(recent) if recent else 1/3,
    }

def player_flat(card,state):
    players=state.get('players') or {}; out={}
    for b in range(1,7):
        reg=str(card.get(f'艇{b}_登録番号','')).strip()
        if not reg:raise Fast120Error(f'missing registration boat {b}')
        ps=_pstat(players.get(reg),b)
        for k,v in ps.items():out[f'b{b}_pl_{k}']=round(float(v),12)
    return out

def _get_fast(url,timeout=4,attempts=2):
    last=None
    for k in range(attempts):
        try:
            r=requests.get(url,headers=UA,timeout=timeout,allow_redirects=False)
            try:
                text=r.content.decode('utf-8-sig')
            except UnicodeDecodeError as de:
                last=Fast120Error(f'UTF-8 decode failed {url}: {de}')
                continue
            if r.status_code==200 and text.strip() and not text.lstrip().startswith('<'):
                return text
            last=Fast120Error(f'HTTP/body invalid {r.status_code} {url}')
        except Exception as e:
            last=e
        if k+1<attempts: time.sleep(.35*(k+1))
    raise Fast120Error(f'fetch failed after {attempts} attempts: {url}: {last}')

def boatcast_tkz_url(hd,jcd,rno):
    return f'{BOATCAST}/hp_txt/{jcd:02d}/bc_j_tkz_{hd}_{jcd:02d}_{rno:02d}.txt'

def parse_tkz_display(body):
    lines=body.splitlines()
    if len(lines)<8 or not lines[0].lstrip().startswith('data=') or lines[1].split('\t')[0].strip()!='1':
        raise Fast120Error('tkz not ready')
    vals={}; boat=1
    for raw in lines[2:]:
        if not raw.strip(): continue
        cols=raw.split('\t')
        if len(cols)<2: continue
        try:v=float(cols[1].strip())
        except: raise Fast120Error(f'tkz exhibition missing boat {boat}')
        vals[boat]=v;boat+=1
        if boat==7: break
    if set(vals)!=set(range(1,7)):raise Fast120Error(f'tkz rows incomplete {sorted(vals)}')
    return vals

def _orig_live_audit(labels,oraw):
    norms=[norm_metric(x) for x in labels]
    avg_all6=bool(labels) and all(
      len(oraw.get(b,[]))>=len(labels) and all(oraw[b][k] is not None for k in range(len(labels)))
      for b in range(1,7)
    )
    def metric_all6(kind):
        idx=[k for k,m in enumerate(norms) if (
          (kind=='turn' and m in ('まわり足','回り足')) or
          (kind=='straight' and m=='直線') or
          (kind=='lap' and m=='一周')
        )]
        return bool(idx) and any(all(oraw[b][k] is not None for b in range(1,7)) for k in idx)
    return {
      'orig_avg_available':bool(avg_all6),
      'orig_turn_available':bool(metric_all6('turn')),
      'orig_straight_available':bool(metric_all6('straight')),
      'orig_lap_available':bool(metric_all6('lap')),
      'orig_labels_norm':norms,
    }

def build_exhibition_boatcast(hd,jcd,rno,tkz_text,st_text,orig_text,bias):
    disp=parse_tkz_display(tkz_text)
    exraw={b:disp[b]+CORR[b]['展示'] for b in range(1,7)}
    ex=rank_scores(exraw,True)
    parsed=parse_boatcast_st(st_text)
    if any(parsed[b] is None for b in range(1,7)):raise Fast120Error('start display incomplete/L')
    st_raw={b:float(parsed[b]) for b in range(1,7)}
    st_corr={b:st_raw[b]-float(bias.get(b,0.0)) for b in range(1,7)}
    rr,rs=_rank_strength(st_raw);cr,cs=_rank_strength(st_corr)

    req=required_orig(jcd)
    if publishes_original(jcd):
        if orig_text is None:
            raise Fast120Error(f'original exhibition missing for venue {int(jcd):02d}')
        labels,oraw=parse_boatcast_original(orig_text)
        oa=_orig_live_audit(labels,oraw)
        missing=[]
        if 'avg' in req and not oa['orig_avg_available']:missing.append('avg')
        if 'turn' in req and not oa['orig_turn_available']:missing.append('turn')
        if 'straight' in req and not oa['orig_straight_available']:missing.append('straight')
        if missing:
            raise Fast120Error(f'original exhibition venue schema incomplete jcd={int(jcd):02d} missing={missing} labels={labels}')
    else:
        labels=[];oraw={b:[] for b in range(1,7)}
        oa={'orig_avg_available':False,'orig_turn_available':False,'orig_straight_available':False,
            'orig_lap_available':False,'orig_labels_norm':[]}

    os=original_corrected(labels,oraw)
    wall_ready=bool(oa['orig_avg_available'] and oa['orig_straight_available'])
    boats={};st_flat={}
    for b in range(1,7):
        boats[str(b)]={'cur_ex':float(ex[b]),'cur_st':float(cs[b]),
          'cur_orig_lap':float(os[b]['lap']),'cur_orig_turn':float(os[b]['turn']),
          'cur_orig_straight':float(os[b]['straight']),'cur_orig_avg':float(os[b]['avg'])}
        st_flat[f'st_raw_b{b}']=st_raw[b];st_flat[f'st_raw_rank_b{b}']=rr[b];st_flat[f'st_corr_rank_b{b}']=cr[b]
        st_flat[f'st_raw_strength_b{b}']=round(rs[b],4);st_flat[f'st_corr_strength_b{b}']=round(cs[b],4)
    return {'schema':'head4_v283_current_exhibition_fast_v2_venue_aware','race_code':f'{hd}{jcd:02d}{rno:02d}',
      'current_boats':boats,'st_flat':st_flat,
      'venue_original_required':list(req),'venue_original_published':bool(publishes_original(jcd)),
      'orig_avg_available':bool(oa['orig_avg_available']),
      'orig_turn_available':bool(oa['orig_turn_available']),
      'orig_straight_available':bool(oa['orig_straight_available']),
      'orig_lap_available':bool(oa['orig_lap_available']),
      'orig_labels_norm':list(oa['orig_labels_norm']),
      'wall_exhibition_ready':wall_ready,
      'result_blind':True,'odds_used':False}

def fetch_current(hd,jcd,rno,timeout):
    tu=boatcast_tkz_url(hd,jcd,rno);su=boatcast_st_url(hd,jcd,rno)
    if publishes_original(jcd):
        ou=boatcast_orig_url(hd,jcd,rno)
        with ThreadPoolExecutor(max_workers=3) as ex:
            ft=ex.submit(_get_fast,tu,timeout,2);fs=ex.submit(_get_fast,su,timeout,2);fo=ex.submit(_get_fast,ou,timeout,2)
            return ft.result(),fs.result(),fo.result()
    with ThreadPoolExecutor(max_workers=2) as ex:
        ft=ex.submit(_get_fast,tu,timeout,2);fs=ex.submit(_get_fast,su,timeout,2)
        return ft.result(),fs.result(),None

def wait_exhibition_ready(hd,jcd,rno,bias,deadline,timeout=4,poll_interval=2.0,safety_seconds=75,max_wait_seconds=30):
    attempts=0; last=''; started=time.perf_counter()
    while True:
        attempts+=1
        try:
            tkz,st,orig=fetch_current(hd,jcd,rno,timeout)
            exh=build_exhibition_boatcast(hd,jcd,rno,tkz,st,orig,bias)
            return exh,attempts,last
        except Exception as e:
            last=f'{type(e).__name__}: {e}'
            remain=(deadline-datetime.now(JST)).total_seconds()
            elapsed=time.perf_counter()-started
            if remain<=safety_seconds or elapsed>=max_wait_seconds:
                raise Fast120NotReady(f'exhibition not ready; attempts={attempts}; remain={remain:.1f}s; elapsed={elapsed:.1f}s; last={last}')
            time.sleep(min(poll_interval,max(0.2,remain-safety_seconds)))

def fetch_official_odds(hd,jcd,rno,deadline,timeout=4):
    require_before_deadline(deadline,'before official odds fetch')
    req=datetime.now(JST)
    params={'rno':rno,'jcd':f'{jcd:02d}','hd':hd}
    resp=official_odds.safe_get(official_odds.BASE,params,timeout=timeout)
    body=resp.text
    fetched=require_before_deadline(deadline,'after official odds fetch')
    parsed=official_odds.parse_odds(body)
    exp=official_odds.expected_combos()
    if set(parsed)!=exp or len(parsed)!=120:
        raise Fast120Error(f'official odds incomplete {len(parsed)}/120')
    odds={f'{a}-{b}-{d}':float(v) for (a,b,d),v in parsed.items()}
    return odds,{'source':'BOAT RACE official odds3t','url':resp.url,'count':120,
      'requested_at_jst':req.isoformat(),'fetched_at_jst':fetched.isoformat(),
      'sha256':hashlib.sha256(body.encode('utf-8',errors='replace')).hexdigest(),'complete':True,
      'result_endpoint_requested':False,'payout_endpoint_requested':False}

def wait_odds_ready(hd,jcd,rno,deadline,timeout=4,poll_interval=1.5,safety_seconds=45,max_wait_seconds=15):
    """Poll two independent pre-result odds sources in parallel.

    First complete 120-combo snapshot wins. This avoids serial timeout stacking.
    """
    attempts=0; last=''; started=time.perf_counter()
    while True:
        attempts+=1
        errs=[]
        with ThreadPoolExecutor(max_workers=2) as ex:
            futs=[
              ('official',ex.submit(fetch_official_odds,hd,jcd,rno,deadline,timeout)),
              ('boatcast',ex.submit(fetch_boatcast_odds,hd,jcd,rno,deadline,timeout)),
            ]
            results=[]
            for name,fut in futs:
                try:
                    odds,meta=fut.result()
                    results.append((name,odds,meta))
                except Exception as e:
                    errs.append(f'{name}={type(e).__name__}: {e}')
        if results:
            # Prefer official when both complete in the same polling round.
            results.sort(key=lambda z:0 if z[0]=='official' else 1)
            name,odds,meta=results[0]
            meta['fallback_used']=(name!='official')
            return odds,meta,attempts,'; '.join(errs)
        last='; '.join(errs)
        remain=(deadline-datetime.now(JST)).total_seconds()
        elapsed=time.perf_counter()-started
        if remain<=safety_seconds or elapsed>=max_wait_seconds:
            raise Fast120NotReady(f'odds not ready; attempts={attempts}; remain={remain:.1f}s; elapsed={elapsed:.1f}s; last={last}')
        time.sleep(min(poll_interval,max(0.2,remain-safety_seconds)))

def parse_od3(body):
    """Parse BOATCAST bc_smt_od3.

    Observed live format:
      line0=data=
      line1=1
      lines2..7 = racer-name + 20 odds + 5 trailing zero fields (+ optional empty tab)

    Only the first 20 fields after the racer name are odds. Trailing zero/status
    fields are deliberately ignored.
    """
    lines=body.splitlines()
    if len(lines)<8 or not lines[0].lstrip().startswith('data=') or lines[1].split('\t')[0].strip()!='1':
        raise Fast120Error(f'od3 not ready/status!=1 lines={len(lines)}')
    vals=[]
    for row_idx,row in enumerate(lines[2:8],start=1):
        cells=row.split('\t')
        # Keep empty trailing cells for diagnostics but only consume positions 1..20.
        if len(cells)<21:
            raise Fast120Error(f'od3 row incomplete first={row_idx} cells={len(cells)} raw={row[:160]!r}')
        odds_cells=[x.strip().replace(',','') for x in cells[1:21]]
        if len(odds_cells)!=20:
            raise Fast120Error(f'od3 row odds-count first={row_idx} count={len(odds_cells)}')
        for pos,v in enumerate(odds_cells,1):
            try:x=float(v)
            except:
                raise Fast120Error(f'bad od3 value first={row_idx} pos={pos} value={v!r}')
            if not math.isfinite(x) or x<=0:
                raise Fast120Error(f'nonpositive od3 first={row_idx} pos={pos} value={x}')
            vals.append(x)
    if len(vals)!=120:raise Fast120Error(f'od3 count {len(vals)}')
    combos=[]
    for a in range(1,7):
        for b in range(1,7):
            if b==a:continue
            for d in range(1,7):
                if d in (a,b):continue
                combos.append(f'{a}-{b}-{d}')
    if len(combos)!=120 or len(set(combos))!=120:
        raise Fast120Error('internal trifecta combo ordering invariant failed')
    return dict(zip(combos,vals))

def fetch_boatcast_odds(hd,jcd,rno,deadline,timeout=4):
    require_before_deadline(deadline,'before BOATCAST odds fetch')
    url=f'{BOATCAST}/txt/{jcd:02d}/bc_smt_od3_{hd}_{jcd:02d}_{rno:02d}.txt'
    req=datetime.now(JST);body=_get_fast(url,timeout,2);fetched=require_before_deadline(deadline,'after BOATCAST odds fetch')
    odds=parse_od3(body)
    return odds,{'source':'BOATCAST aggregating bc_smt_od3','url':url,'count':len(odds),
      'requested_at_jst':req.isoformat(),'fetched_at_jst':fetched.isoformat(),
      'sha256':hashlib.sha256(body.encode()).hexdigest(),'complete':len(odds)==120,
      'result_endpoint_requested':False,'payout_endpoint_requested':False}

def make_boats(card,waku,exh,pflat):
    v93=build_v93(card,waku,exh)
    vf=v93['v93_flat']; cb=exh['current_boats']; sf=exh['st_flat']; out={}
    for b in range(1,7):
        cur=cb[str(b)]; z={k:float(cur[k]) for k in CUR}
        if b!=4:
            for k in V93:z[f'v93_{k}']=float(vf[f'opp_{k}_b{b}_v93'])
            z['pos_boat_number']=float(b);z['pos_inside4']=float(b<4);z['pos_outside4']=float(b>4);z['pos_distance4']=float(abs(b-4))
            for k in PL:z[f'pref_pl_{k}']=float(pflat[f'b{b}_pl_{k}'])
            for k in ST:z[f'suf_st_{k}']=float(sf[f'st_{k}_b{b}'])
        out[str(b)]=z
    return {'boats':out}

def require_before_deadline(deadline,stage):
    now=datetime.now(JST)
    if now>=deadline:
        raise Fast120Error(f'deadline passed at {stage}: now={now.isoformat()} deadline={deadline.isoformat()}')
    return now


def production_tickets(p2,pc):
    tickets=[f'4-{s}-{t}' for s,t in v283_top4(p2,pc)]
    second_rank=sorted(BOATS,key=lambda s:(-float(p2[s]),s))
    for s in second_rank[:2]:
        thirds=sorted((t for t in BOATS if t!=s),key=lambda t:(-float(pc[(s,t)]),t))
        gap23=float(pc[(s,thirds[1])])-float(pc[(s,thirds[2])])
        if gap23<=THIRD_GAP:
            extra=f'4-{s}-{thirds[2]}'
            if extra not in tickets:
                tickets.append(extra)
    if not (4<=len(tickets)<=6) or len(set(tickets))!=len(tickets):
        raise Fast120Error(f'ticket invariant failed: {tickets}')
    return tickets


def composite_odds(vals):
    a=[float(x) for x in vals]
    if not (4<=len(a)<=6) or any((not math.isfinite(x) or x<=0) for x in a):
        raise Fast120Error(f'invalid odds list: {a}')
    return 1.0/sum(1.0/x for x in a)


def pair_mass(p2,pc,pairs):
    vals={}
    for s in BOATS:
        for t in BOATS:
            if s==t:continue
            vals[(s,t)]=math.exp(ALPHA2*math.log(max(float(p2[s]),1e-12))+(1-ALPHA2)*math.log(max(float(pc[(s,t)]),1e-12)))
    den=sum(vals.values())
    return sum(vals[x]/den for x in pairs)

def fetch_odds_timing_only(date,jcd,race):
    """Performance-only odds fetch. No decision/claim of pre-deadline validity."""
    t0=time.perf_counter()
    params={'rno':race,'jcd':f'{jcd:02d}','hd':date}
    resp=live.safe_get(live.BASE,params)
    parsed=live.parse_odds(resp.text)
    if set(parsed)!=live.expected_combos() or len(parsed)!=120:
        raise Fast120Error(f'official odds3t incomplete in benchmark: {len(parsed)}/120')
    odds={f'{a}-{b}-{cc}':float(o) for (a,b,cc),o in parsed.items()}
    return odds,{'source':'BOAT RACE official odds3t timing-only','count':120,'timing_only':True,
                 'fetched_at_jst':datetime.now(JST).isoformat(),'elapsed_s':time.perf_counter()-t0}

def structural_advantages(exh):
    b=exh['current_boats']
    inside=(1,2,3)
    st_inside=sum(float(b[str(i)]['cur_st']) for i in inside)/3.0
    orig_ready=bool(exh.get('orig_avg_available',True))
    orig_adv=None
    if orig_ready:
        orig_inside=sum(float(b[str(i)]['cur_orig_avg']) for i in inside)/3.0
        orig_adv=float(float(b['4']['cur_orig_avg'])-orig_inside)
    return {
      'st4_adv_inside':float(st_inside-float(b['4']['cur_st'])),
      'orig4_adv_inside':orig_adv,
      'orig_avg_available':orig_ready,
    }

def legacy_decide(head_prob,mass,comp,exh):
    """Legacy HEAD4_156R_ROI_EXPANSION_V1 semantics, retained for comparison."""
    s=structural_advantages(exh)
    cur=comp>=7.0
    base77_formula=(cur and mass>=.425) or ((not cur) and head_prob>=.22 and mass>=.375 and comp>=3.0)
    score=head_prob+1.50*mass
    old164_struct=(s['orig_avg_available'] and s['orig4_adv_inside'] is not None and
                   s['st4_adv_inside']>=-.6000000000000001 and
                   s['orig4_adv_inside']>=-.057777777777777706)
    base77=old164_struct and base77_formula
    base120=old164_struct and (base77_formula or (comp>=2.5 and score>=.82))
    expansion156=((not base120) and s['orig_avg_available'] and s['orig4_adv_inside'] is not None and
                  comp>=3.5 and score>=.75 and head_prob>=.16 and mass>=.30 and
                  s['st4_adv_inside']>=-.80 and s['orig4_adv_inside']>=-.35)
    sel=base120 or expansion156
    return {
      'profile':'HEAD4_156R_ROI_EXPANSION_V1',
      'selected':bool(sel),
      'base77':bool(base77),
      'base77_formula':bool(base77_formula),
      'base120_selected':bool(base120),
      'expanded156_added':bool(expansion156),
      'expanded156_selected':bool(sel),
      'old164_struct':bool(old164_struct),
      'current_comp7':bool(cur),
      'linear_score':float(score),
      **s,
    }


NEWFEATURE_ARTIFACT=Path(__file__).resolve().parent/'artifacts'/'head4_newfeature_fixed156_production.json'

def _float_card(v):
    try:
        x=float(str(v).replace('%','').strip())
        return x if math.isfinite(x) else None
    except Exception:
        return None

def _ecdf_rank(value, refs, missing_rank=.5):
    if value is None:
        return float(missing_rank)
    try:
        x=float(value)
    except Exception:
        return float(missing_rank)
    if not math.isfinite(x) or not refs:
        return float(missing_rank)
    return float(bisect.bisect_right(refs,x)/len(refs))

def load_newfeature_artifact():
    a=json.loads(NEWFEATURE_ARTIFACT.read_text(encoding='utf-8'))
    if a.get('profile')!='HEAD4_NEWFEATURE_FIXED156_V1':
        raise Fast120Error(f"newfeature artifact profile mismatch: {a.get('profile')}")
    if a.get('production_applied') is not True:
        raise Fast120Error('newfeature artifact is not production-applied')
    return a

def newfeature_motor_raw(card,state,jcd):
    if 'motors_newfeature_nov2025' not in state:
        raise Fast120NotReady('daily state lacks motors_newfeature_nov2025; rebuild state with current prepare_4head_120r_daily_state.py')
    hist=state.get('motors_newfeature_nov2025') or {}
    if state.get('newfeature_motor_history_start') not in (None,'2025-11-01'):
        raise Fast120Error(f"newfeature motor history start mismatch: {state.get('newfeature_motor_history_start')}")
    venue=f'{int(jcd):02d}'
    def prior_rate(b):
        mno=str(card.get(f'艇{b}_モーター番号','')).strip()
        if not mno:
            return None
        r=hist.get(f'{venue}|{mno}')
        if not r:
            return None
        n=int(r.get('n',0)); w=int(r.get('w',0))
        return (w/n) if n>0 else None
    r4=prior_rate(4); r3=prior_rate(3)
    win_diff=(r4-r3) if r4 is not None and r3 is not None else None
    p4=_float_card(card.get('艇4_モーター2連対率'))
    p3=_float_card(card.get('艇3_モーター2連対率'))
    ren2_diff=(p4-p3) if p4 is not None and p3 is not None else None
    return {
      'motor4_win_prior':r4,'motor3_win_prior':r3,
      'motor_win_diff_4v3':win_diff,
      'motor4_2ren':p4,'motor3_2ren':p3,
      'motor_2ren_diff_4v3':ren2_diff,
    }

def newfeature_wall_raw(exh):
    # Frozen research semantics: all wall-family values were NaN unless both
    # orig_avg and orig_straight were available for all six boats.
    if not bool(exh.get('wall_exhibition_ready',True)):
        return {
          'wall_exhibition_ready':False,
          'ex_wall_gap':None,'st_wall_gap':None,
          'straight_wall_gap':None,'avg_wall_gap':None,
          'wall_score':None,'attack4_score':None,
        }
    b3=exh['current_boats']['3']; b4=exh['current_boats']['4']
    ex_gap=float(b3['cur_ex'])-float(b4['cur_ex'])
    st_gap=float(b3['cur_st'])-float(b4['cur_st'])
    straight_gap=float(b3['cur_orig_straight'])-float(b4['cur_orig_straight'])
    avg_gap=float(b3['cur_orig_avg'])-float(b4['cur_orig_avg'])
    wall=(.20*ex_gap+.40*st_gap+.25*straight_gap+.15*avg_gap)
    attack4=(.20*float(b4['cur_ex'])+.40*float(b4['cur_st'])+
             .25*float(b4['cur_orig_straight'])+.15*float(b4['cur_orig_avg']))
    return {
      'wall_exhibition_ready':True,
      'ex_wall_gap':ex_gap,'st_wall_gap':st_gap,
      'straight_wall_gap':straight_gap,'avg_wall_gap':avg_gap,
      'wall_score':wall,'attack4_score':attack4,
    }

def score_newfeature_raw(raw,artifact):
    refs=artifact['ecdf_sorted_reference']; weights=artifact['weights']
    missing=float(artifact.get('score_transform',{}).get('missing_value_rank',.5))
    ranks={}
    for name,w in weights.items():
        ranks[name]=_ecdf_rank(raw.get(name),refs.get(name) or [],missing)
    score=sum(float(weights[k])*float(ranks[k]) for k in weights)
    return float(score),ranks

def newfeature_decide(head_prob,mass,comp,exh,card,state,jcd):
    legacy=legacy_decide(head_prob,mass,comp,exh)
    s={'st4_adv_inside':legacy['st4_adv_inside'],'orig4_adv_inside':legacy['orig4_adv_inside'],
       'orig_avg_available':bool(legacy.get('orig_avg_available',True))}
    motor=newfeature_motor_raw(card,state,jcd)
    wall=newfeature_wall_raw(exh)
    raw={
      'hp':float(head_prob),
      'mass':float(mass),
      'st':float(s['st4_adv_inside']),
      'orig':(float(s['orig4_adv_inside']) if s['orig4_adv_inside'] is not None else None),
      'market_conf':-math.log(max(float(comp),1e-12)),
      'motor_win_rev':(-float(motor['motor_win_diff_4v3']) if motor['motor_win_diff_4v3'] is not None else None),
      'motor_2ren_rev':(-float(motor['motor_2ren_diff_4v3']) if motor['motor_2ren_diff_4v3'] is not None else None),
      'attack4':(float(wall['attack4_score']) if wall['attack4_score'] is not None else None),
      'stwall_center':(-abs(float(wall['st_wall_gap'])-.10) if wall['st_wall_gap'] is not None else None),
      'wall_rev':(-float(wall['wall_score']) if wall['wall_score'] is not None else None),
    }
    art=load_newfeature_artifact()
    score,ranks=score_newfeature_raw(raw,art)
    threshold=float(art['production_threshold'])
    gate=art.get('explicit_expansion_structural_gate') or {}
    st_min=float(gate.get('st4_adv_inside_min',-.80))
    orig_min=float(gate.get('orig4_adv_inside_min',-.35))
    expansion=bool(
      (not legacy['base120_selected']) and s['orig_avg_available'] and
      s['orig4_adv_inside'] is not None and
      s['st4_adv_inside']>=st_min and s['orig4_adv_inside']>=orig_min and
      score>=threshold
    )
    selected=bool(legacy['base120_selected'] or expansion)
    return {
      'profile':'HEAD4_NEWFEATURE_FIXED156_V1',
      'selected':selected,
      'base77':bool(legacy['base77']),
      'base120_selected':bool(legacy['base120_selected']),
      'newfeature_expanded_added':expansion,
      'newfeature_score':float(score),
      'newfeature_threshold':threshold,
      'newfeature_score_margin':float(score-threshold),
      'newfeature_raw':raw,
      'newfeature_ranks':ranks,
      'newfeature_motor':motor,
      'newfeature_wall':wall,
      'legacy_156r_selected':bool(legacy['selected']),
      'legacy_156r_expanded_added':bool(legacy['expanded156_added']),
      'legacy_156r_linear_score':float(legacy['linear_score']),
      'old164_struct':bool(legacy['old164_struct']),
      'current_comp7':bool(legacy['current_comp7']),
      'st4_adv_inside':float(s['st4_adv_inside']),
      'orig4_adv_inside':(float(s['orig4_adv_inside']) if s['orig4_adv_inside'] is not None else None),
      'orig_avg_available':bool(s['orig_avg_available']),
      'wall_exhibition_ready':bool(wall.get('wall_exhibition_ready')),
      'venue_original_required':list(exh.get('venue_original_required',required_orig(jcd))),
      'venue_schema_supported_for_selection':bool(s['orig_avg_available']),
    }


def decide(head_prob,mass,comp,exh):
    """Compatibility wrapper for historical HEAD4_156R_ROI_EXPANSION_V1 tests."""
    return legacy_decide(head_prob,mass,comp,exh)


def wall3_open_shadow(head_prob,mass,comp,exh,current_selected):
    """Research-only 3-vs-4 open-path rescue diagnostic.

    This never changes the official selected/BET/PASS decision.
    Canonical profile is frozen from the 2026-09-18 retrospective audit.
    Frozen wall research required orig straight + orig avg; otherwise no shadow.
    """
    if not bool(exh.get('wall_exhibition_ready',True)):
        return {
          'profile':'HEAD4_WALL3_OPEN_RESCUE_SHADOW_V1_BETA010_Q082_COMP250',
          'research_only':True,'production_applied':False,
          'eligible_current_pass':False,'would_rescue':False,
          'wall_score':None,'open_risk':None,'attack4_score':None,
          'base_quality':float(head_prob)+1.50*float(mass),'shadow_quality':None,
          'thresholds':{'open_beta':.10,'quality':.82,'composite_odds':2.5},
          'gaps':{},'not_ready_reason':'venue wall schema unavailable',
        }
    b3=exh['current_boats']['3']; b4=exh['current_boats']['4']
    gaps={
      'ex':float(b3['cur_ex'])-float(b4['cur_ex']),
      'st':float(b3['cur_st'])-float(b4['cur_st']),
      'straight':float(b3['cur_orig_straight'])-float(b4['cur_orig_straight']),
      'orig_avg':float(b3['cur_orig_avg'])-float(b4['cur_orig_avg']),
    }
    wall=(.20*gaps['ex']+.40*gaps['st']+.25*gaps['straight']+.15*gaps['orig_avg'])
    attack4=(.20*float(b4['cur_ex'])+.40*float(b4['cur_st'])+
             .25*float(b4['cur_orig_straight'])+.15*float(b4['cur_orig_avg']))
    open_risk=max(0.0,-wall)
    base_quality=float(head_prob)+1.50*float(mass)
    shadow_quality=base_quality+.10*open_risk
    eligible=bool((not current_selected) and float(comp)>=2.5 and open_risk>0)
    rescue=bool(eligible and shadow_quality>=.82)
    return {
      'profile':'HEAD4_WALL3_OPEN_RESCUE_SHADOW_V1_BETA010_Q082_COMP250',
      'research_only':True,
      'production_applied':False,
      'eligible_current_pass':eligible,
      'would_rescue':rescue,
      'wall_score':wall,
      'open_risk':open_risk,
      'attack4_score':attack4,
      'base_quality':base_quality,
      'shadow_quality':shadow_quality,
      'thresholds':{'open_beta':.10,'quality':.82,'composite_odds':2.5},
      'gaps':gaps,
    }

def parse_deadline_flexible(date8,s):
    v=str(s).strip()
    if len(v) in (5,8) and v[2]==':':
        hh,mm,*rest=v.split(':')
        ss=rest[0] if rest else '00'
        return datetime(int(date8[:4]),int(date8[4:6]),int(date8[6:8]),int(hh),int(mm),int(ss),tzinfo=JST)
    try:
        dt=datetime.fromisoformat(v)
    except Exception as e:
        raise Fast120Error(f'invalid deadline {v!r}') from e
    if dt.tzinfo is None:
        dt=dt.replace(tzinfo=JST)
    return dt.astimezone(JST)

def persist_no_bet_not_ready(a,code,deadline,stage,reason,total0,stages,monitored,hp,state):
    now=datetime.now(JST)
    out={
      'schema':'head4_120r_fast_lastminute_v1',
      'race_code':code,
      'monitoring_parent':bool(monitored),
      'head_prob':float(hp),
      'selected':False,
      'decision':'NO_BET_DATA_NOT_READY',
      'not_ready_stage':stage,
      'not_ready_reason':str(reason),
      'daily_state_history_end':state.get('history_end'),
      'september_prior_history_allowed':True,
      'target_race_result_used':False,
      'payout_used':False,
      'deadline_jst':deadline.isoformat(),
      'decision_time_jst':now.isoformat(),
      'stages_seconds':stages,
      'total_seconds':time.perf_counter()-total0,
    }
    Path(a.out).parent.mkdir(parents=True,exist_ok=True)
    Path(a.out).write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(out,ensure_ascii=False,indent=2))
    print('HEAD4_120R_FAST_NO_BET_DATA_NOT_READY')
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--date',required=True,help='YYYYMMDD')
    ap.add_argument('--jcd',required=True,type=int);ap.add_argument('--race',required=True,type=int)
    ap.add_argument('--deadline-jst',required=True)
    ap.add_argument('--race-cards',required=True);ap.add_argument('--waku10',required=True)
    ap.add_argument('--pre-all',required=True);ap.add_argument('--daily-state',required=True)
    ap.add_argument('--timeout',type=int,default=4);ap.add_argument('--poll-interval',type=float,default=2.0);ap.add_argument('--exhibition-safety-seconds',type=int,default=75);ap.add_argument('--odds-safety-seconds',type=int,default=45);ap.add_argument('--max-exhibition-wait-seconds',type=float,default=30);ap.add_argument('--max-odds-wait-seconds',type=float,default=15);ap.add_argument('--decision-safety-seconds',type=int,default=60);ap.add_argument('--allow-unmonitored-benchmark',action='store_true');ap.add_argument('--performance-benchmark',action='store_true')
    ap.add_argument('--out',required=True)
    a=ap.parse_args(); total0=time.perf_counter(); stages={}
    deadline=parse_deadline_flexible(a.date,a.deadline_jst)
    if a.performance_benchmark:
        io_deadline=datetime(int(a.date[:4]),int(a.date[4:6]),int(a.date[6:8]),23,59,59,tzinfo=JST)
    else:
        io_deadline=deadline
        require_before_deadline(deadline,'fast120 startup')
    code=f'{a.date}{a.jcd:02d}{a.race:02d}'
    cards=bycode(rows_local(a.race_cards));waku=bycode(rows_local(a.waku10));pre=bycode(rows_local(a.pre_all))
    if code not in cards or code not in waku or code not in pre:raise Fast120Error(f'missing current row {code}')
    prow=pre[code]; hp=float(prow['head_prob']); monitored=int(float(prow['monitoring_parent']))==1
    if not monitored and not a.allow_unmonitored_benchmark:raise Fast120Error('race not in monitoring parent')
    state=json.loads(Path(a.daily_state).read_text())
    if state.get('target_date')!=f'{a.date[:4]}-{a.date[4:6]}-{a.date[6:8]}':raise Fast120Error('daily-state target mismatch')
    if state.get('target_date_results_used') is not False:raise Fast120Error('daily state contamination')

    bias={int(k):float(v) for k,v in state['st_bias'].items()}
    t=time.perf_counter()
    try:
        exh,ex_attempts,ex_last=wait_exhibition_ready(
            a.date,a.jcd,a.race,bias,io_deadline,a.timeout,a.poll_interval,a.exhibition_safety_seconds,a.max_exhibition_wait_seconds
        )
    except Fast120NotReady as e:
        stages['fetch_and_build_exhibition_s']=time.perf_counter()-t
        persist_no_bet_not_ready(a,code,deadline,'EXHIBITION',e,total0,stages,monitored,hp,state)
        return
    stages['fetch_and_build_exhibition_s']=time.perf_counter()-t
    t=time.perf_counter(); pf=player_flat(cards[code],state); src=make_boats(cards[code],waku[code],exh,pf);stages['build_v283_inputs_s']=time.perf_counter()-t
    art=load_artifact()
    t=time.perf_counter(); sr,cr=derive(src,art);p2=score_second(sr,art);pc=score_conditional_third(cr,art);tickets=production_tickets(p2,pc);pairs=[tuple(map(int,x.split('-')[1:])) for x in tickets];mass=pair_mass(p2,pc,pairs);stages['v283_inference_s']=time.perf_counter()-t
    t=time.perf_counter()
    try:
        odds,meta,od_attempts,od_last=wait_odds_ready(
            a.date,a.jcd,a.race,io_deadline,min(1.5,a.timeout),min(1.0,a.poll_interval),a.odds_safety_seconds,a.max_odds_wait_seconds
        )
    except Fast120NotReady as e:
        stages['fetch_odds_s']=time.perf_counter()-t
        persist_no_bet_not_ready(a,code,deadline,'ODDS',e,total0,stages,monitored,hp,state)
        return
    stages['fetch_odds_s']=time.perf_counter()-t
    vals=[float(odds[x]) for x in tickets];comp=composite_odds(vals)
    try:
        d=newfeature_decide(hp,mass,comp,exh,cards[code],state,a.jcd)
    except Fast120NotReady as e:
        stages['newfeature_state_s']=0.0
        persist_no_bet_not_ready(a,code,deadline,'NEWFEATURE_STATE',e,total0,stages,monitored,hp,state)
        return
    wallshadow=wall3_open_shadow(hp,mass,comp,exh,d['selected'])
    if a.performance_benchmark:
        now=datetime.now(JST)
    else:
        now=require_before_deadline(deadline,'before fast120 persist')
        remain=(deadline-now).total_seconds()
        if remain<a.decision_safety_seconds:
            stages['decision_headroom_s']=remain
            persist_no_bet_not_ready(a,code,deadline,'DECISION_HEADROOM',
                f'only {remain:.1f}s remain < safety {a.decision_safety_seconds}s',
                total0,stages,monitored,hp,state)
            return
    out={
      'schema':'head4_120r_fast_lastminute_v1','race_code':code,'monitoring_parent':monitored,'benchmark_unmonitored':bool(a.allow_unmonitored_benchmark and not monitored),
      'head_prob':hp,'opponent_mass':mass,'tickets':tickets,'ticket_odds':dict(zip(tickets,vals)),'composite_odds':comp,
      **d,'decision':('PERFORMANCE_BENCHMARK_ONLY' if a.performance_benchmark else ('BET' if d['selected'] and monitored else ('BENCHMARK_ONLY' if not monitored else 'PASS'))),
      'selection_policy_artifact':'artifacts/head4_newfeature_fixed156_production.json',
      'wall3_open_shadow':wallshadow,
      'daily_state_history_end':state.get('history_end'),'september_prior_history_allowed':True,
      'target_race_result_used':False,'payout_used':False,'current_exhibition_used':True,'predeadline_odds_used':(not a.performance_benchmark),'performance_benchmark':bool(a.performance_benchmark),'odds_source':meta.get('source'),
      'exhibition_attempts':ex_attempts,'exhibition_last_retry_error':ex_last,'odds_attempts':od_attempts,'odds_last_retry_error':od_last,
      'safety_seconds':{'exhibition':a.exhibition_safety_seconds,'odds':a.odds_safety_seconds,'decision':a.decision_safety_seconds},
      'odds_snapshot':meta,'deadline_jst':deadline.isoformat(),'decision_time_jst':now.isoformat(),
      'stages_seconds':stages,'total_seconds':time.perf_counter()-total0,
    }
    Path(a.out).parent.mkdir(parents=True,exist_ok=True);Path(a.out).write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(out,ensure_ascii=False,indent=2))
    print('HEAD4_120R_FAST_LASTMINUTE_OK')

if __name__=='__main__':main()
