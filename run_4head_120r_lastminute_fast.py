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
import argparse,csv,json,math,time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,time as dtime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from build_4head_post_live import _fetch,beforeinfo_url,boatcast_st_url,boatcast_orig_url,BOATCAST
from build_4head_v283_current_exhibition_live import build_from_sources as build_exhibition
from build_4head_v93_primitives_live import build as build_v93
from build_4head_v283_rows_live import derive
from head4_v291_downstream_inference import load_artifact,score_second,score_conditional_third,BOATS
import run_4head_v291_third010_live as live

JST=ZoneInfo('Asia/Tokyo')
PL=('all_p2','all_win','frame_p2','recent_p2','frame_win')
ST=('raw','raw_strength','raw_rank','corr_strength','corr_rank')
V93=('grade','national','local','motor','nst')
CUR=('cur_ex','cur_st','cur_orig_lap','cur_orig_turn','cur_orig_straight','cur_orig_avg')

class Fast120Error(RuntimeError):pass

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

def fetch_current(hd,jcd,rno,timeout):
    bu=beforeinfo_url(hd,jcd,rno); su=boatcast_st_url(hd,jcd,rno); ou=boatcast_orig_url(hd,jcd,rno)
    with ThreadPoolExecutor(max_workers=3) as ex:
        fb=ex.submit(_fetch,bu,'https://www.boatrace.jp/owpc/pc/race/beforeinfo',timeout)
        fs=ex.submit(_fetch,su,f'{BOATCAST}/hp_txt/{jcd:02d}/bc_j_stt_',timeout)
        fo=ex.submit(_fetch,ou,f'{BOATCAST}/txt/{jcd:02d}/bc_oriten_',timeout)
        return fb.result(),fs.result(),fo.result()

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

def pair_mass(p2,pc,pairs):
    vals={}
    for s in BOATS:
        for t in BOATS:
            if s==t:continue
            vals[(s,t)]=math.exp(live.ALPHA2*math.log(max(float(p2[s]),1e-12))+(1-live.ALPHA2)*math.log(max(float(pc[(s,t)]),1e-12)))
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
    return live.parse_deadline(v)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--date',required=True,help='YYYYMMDD')
    ap.add_argument('--jcd',required=True,type=int);ap.add_argument('--race',required=True,type=int)
    ap.add_argument('--deadline-jst',required=True)
    ap.add_argument('--race-cards',required=True);ap.add_argument('--waku10',required=True)
    ap.add_argument('--pre-all',required=True);ap.add_argument('--daily-state',required=True)
    ap.add_argument('--timeout',type=int,default=8);ap.add_argument('--allow-unmonitored-benchmark',action='store_true')
    ap.add_argument('--out',required=True)
    a=ap.parse_args(); total0=time.perf_counter(); stages={}
    deadline=parse_deadline_flexible(a.date,a.deadline_jst); live.require_before_deadline(deadline,'fast120 startup')
    code=f'{a.date}{a.jcd:02d}{a.race:02d}'
    cards=bycode(rows_local(a.race_cards));waku=bycode(rows_local(a.waku10));pre=bycode(rows_local(a.pre_all))
    if code not in cards or code not in waku or code not in pre:raise Fast120Error(f'missing current row {code}')
    prow=pre[code]; hp=float(prow['head_prob']); monitored=int(float(prow['monitoring_parent']))==1
    if not monitored and not a.allow_unmonitored_benchmark:raise Fast120Error('race not in monitoring parent')
    state=json.loads(Path(a.daily_state).read_text())
    if state.get('target_date')!=f'{a.date[:4]}-{a.date[4:6]}-{a.date[6:8]}':raise Fast120Error('daily-state target mismatch')
    if state.get('target_date_results_used') is not False:raise Fast120Error('daily state contamination')

    t=time.perf_counter(); before,st,orig=fetch_current(a.date,a.jcd,a.race,a.timeout);stages['fetch_exhibition_s']=time.perf_counter()-t
    bias={int(k):float(v) for k,v in state['st_bias'].items()}
    t=time.perf_counter(); exh=build_exhibition(a.date,a.jcd,a.race,before,st,orig,bias);stages['build_exhibition_s']=time.perf_counter()-t
    t=time.perf_counter(); pf=player_flat(cards[code],state); src=make_boats(cards[code],waku[code],exh,pf);stages['build_v283_inputs_s']=time.perf_counter()-t
    art=load_artifact()
    t=time.perf_counter(); sr,cr=derive(src,art);p2=score_second(sr,art);pc=score_conditional_third(cr,art);tickets=live.production_tickets(p2,pc);pairs=[tuple(map(int,x.split('-')[1:])) for x in tickets];mass=pair_mass(p2,pc,pairs);stages['v283_inference_s']=time.perf_counter()-t
    t=time.perf_counter();odds,meta=live.fetch_odds(a.date,a.jcd,a.race,deadline);stages['fetch_odds_s']=time.perf_counter()-t
    vals=[float(odds[x]) for x in tickets];comp=live.composite_odds(vals);d=decide(hp,mass,comp)
    now=live.require_before_deadline(deadline,'before fast120 persist')
    out={
      'schema':'head4_120r_fast_lastminute_v1','race_code':code,'monitoring_parent':monitored,'benchmark_unmonitored':bool(a.allow_unmonitored_benchmark and not monitored),
      'head_prob':hp,'opponent_mass':mass,'tickets':tickets,'ticket_odds':dict(zip(tickets,vals)),'composite_odds':comp,
      **d,'decision':'BET' if d['selected'] and monitored else ('BENCHMARK_ONLY' if not monitored else 'PASS'),
      'daily_state_history_end':state.get('history_end'),'september_prior_history_allowed':True,
      'target_race_result_used':False,'payout_used':False,'current_exhibition_used':True,'official_predeadline_odds_used':True,
      'odds_snapshot':meta,'deadline_jst':deadline.isoformat(),'decision_time_jst':now.isoformat(),
      'stages_seconds':stages,'total_seconds':time.perf_counter()-total0,
    }
    Path(a.out).parent.mkdir(parents=True,exist_ok=True);Path(a.out).write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(out,ensure_ascii=False,indent=2))
    print('HEAD4_120R_FAST_LASTMINUTE_OK')

if __name__=='__main__':main()
