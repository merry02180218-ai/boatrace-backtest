#!/usr/bin/env python3
"""Fast post-exhibition final decision for HEAD4 120R research/live line.

Per-race path intentionally avoids the heavy POST/ENV/A full production chain.
It uses:
- current race card + waku10
- once-daily causal player/ST state through target_date-1
- current official/BOATCAST exhibition sources
- frozen v283 opponent models
- official pre-deadline trifecta odds
- frozen 120R selection rule

No target-race result/payout access.
"""
from __future__ import annotations
import argparse,csv,json,math,time,hashlib,re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,time as dtime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import requests
from build_4head_post_live import boatcast_st_url,boatcast_orig_url,BOATCAST,UA
from build_4head_v283_current_exhibition_live import parse_boatcast_st,parse_boatcast_original,original_corrected,_rank_strength
from backtest_v3 import CORR
from backtest_v51_lane_corrected_tickets import rank_scores
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

def build_exhibition_boatcast(hd,jcd,rno,tkz_text,st_text,orig_text,bias):
    disp=parse_tkz_display(tkz_text)
    exraw={b:disp[b]+CORR[b]['展示'] for b in range(1,7)}
    ex=rank_scores(exraw,True)
    parsed=parse_boatcast_st(st_text)
    if any(parsed[b] is None for b in range(1,7)):raise Fast120Error('start display incomplete/L')
    st_raw={b:float(parsed[b]) for b in range(1,7)}
    st_corr={b:st_raw[b]-float(bias.get(b,0.0)) for b in range(1,7)}
    rr,rs=_rank_strength(st_raw);cr,cs=_rank_strength(st_corr)
    labels,oraw=parse_boatcast_original(orig_text);os=original_corrected(labels,oraw)
    boats={};st_flat={}
    for b in range(1,7):
        boats[str(b)]={'cur_ex':float(ex[b]),'cur_st':float(cs[b]),
          'cur_orig_lap':float(os[b]['lap']),'cur_orig_turn':float(os[b]['turn']),
          'cur_orig_straight':float(os[b]['straight']),'cur_orig_avg':float(os[b]['avg'])}
        st_flat[f'st_raw_b{b}']=st_raw[b];st_flat[f'st_raw_rank_b{b}']=rr[b];st_flat[f'st_corr_rank_b{b}']=cr[b]
        st_flat[f'st_raw_strength_b{b}']=round(rs[b],4);st_flat[f'st_corr_strength_b{b}']=round(cs[b],4)
    return {'schema':'head4_v283_current_exhibition_fast_v1','race_code':f'{hd}{jcd:02d}{rno:02d}',
      'current_boats':boats,'st_flat':st_flat,'result_blind':True,'odds_used':False}

def fetch_current(hd,jcd,rno,timeout):
    tu=boatcast_tkz_url(hd,jcd,rno);su=boatcast_st_url(hd,jcd,rno);ou=boatcast_orig_url(hd,jcd,rno)
    with ThreadPoolExecutor(max_workers=3) as ex:
        ft=ex.submit(_get_fast,tu,timeout,2);fs=ex.submit(_get_fast,su,timeout,2);fo=ex.submit(_get_fast,ou,timeout,2)
        return ft.result(),fs.result(),fo.result()

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

def decide(head_prob,mass,comp):
    cur=comp>=7.0
    base77=(cur and mass>=.425) or ((not cur) and head_prob>=.22 and mass>=.375 and comp>=3.0)
    score=head_prob+1.50*mass
    sel=base77 or ((not base77) and comp>=2.5 and score>=.82)
    return {'selected':bool(sel),'base77':bool(base77),'current_comp7':bool(cur),'linear_score':float(score)}

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
    ap.add_argument('--timeout',type=int,default=4);ap.add_argument('--poll-interval',type=float,default=2.0);ap.add_argument('--exhibition-safety-seconds',type=int,default=75);ap.add_argument('--odds-safety-seconds',type=int,default=45);ap.add_argument('--max-exhibition-wait-seconds',type=float,default=30);ap.add_argument('--max-odds-wait-seconds',type=float,default=15);ap.add_argument('--allow-unmonitored-benchmark',action='store_true')
    ap.add_argument('--out',required=True)
    a=ap.parse_args(); total0=time.perf_counter(); stages={}
    deadline=parse_deadline_flexible(a.date,a.deadline_jst); require_before_deadline(deadline,'fast120 startup')
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
            a.date,a.jcd,a.race,bias,deadline,a.timeout,a.poll_interval,a.exhibition_safety_seconds,a.max_exhibition_wait_seconds
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
            a.date,a.jcd,a.race,deadline,a.timeout,min(1.5,a.poll_interval),a.odds_safety_seconds,a.max_odds_wait_seconds
        )
    except Fast120NotReady as e:
        stages['fetch_odds_s']=time.perf_counter()-t
        persist_no_bet_not_ready(a,code,deadline,'ODDS',e,total0,stages,monitored,hp,state)
        return
    stages['fetch_odds_s']=time.perf_counter()-t
    vals=[float(odds[x]) for x in tickets];comp=composite_odds(vals);d=decide(hp,mass,comp)
    now=require_before_deadline(deadline,'before fast120 persist')
    out={
      'schema':'head4_120r_fast_lastminute_v1','race_code':code,'monitoring_parent':monitored,'benchmark_unmonitored':bool(a.allow_unmonitored_benchmark and not monitored),
      'head_prob':hp,'opponent_mass':mass,'tickets':tickets,'ticket_odds':dict(zip(tickets,vals)),'composite_odds':comp,
      **d,'decision':'BET' if d['selected'] and monitored else ('BENCHMARK_ONLY' if not monitored else 'PASS'),
      'daily_state_history_end':state.get('history_end'),'september_prior_history_allowed':True,
      'target_race_result_used':False,'payout_used':False,'current_exhibition_used':True,'predeadline_odds_used':True,'odds_source':meta.get('source'),
      'exhibition_attempts':ex_attempts,'exhibition_last_retry_error':ex_last,'odds_attempts':od_attempts,'odds_last_retry_error':od_last,
      'safety_seconds':{'exhibition':a.exhibition_safety_seconds,'odds':a.odds_safety_seconds},
      'odds_snapshot':meta,'deadline_jst':deadline.isoformat(),'decision_time_jst':now.isoformat(),
      'stages_seconds':stages,'total_seconds':time.perf_counter()-total0,
    }
    Path(a.out).parent.mkdir(parents=True,exist_ok=True);Path(a.out).write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(out,ensure_ascii=False,indent=2))
    print('HEAD4_120R_FAST_LASTMINUTE_OK')

if __name__=='__main__':main()
