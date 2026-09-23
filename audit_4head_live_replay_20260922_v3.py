#!/usr/bin/env python3
import csv,glob,json,math,os
from pathlib import Path
import pandas as pd
import run_4head_120r_lastminute_fast as fast
import run_4head_v291_third010_live as live
from head4_v291_downstream_inference import load_artifact,score_second,score_conditional_third
ROOT=Path(os.environ['BOATRACECSV_LOCAL_ROOT']); DATE='20260922'
def rows(rel):
 p=ROOT/rel
 if not p.is_file(): return []
 with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def rc(x):
 s=str(x or '').strip()
 if s.endswith('.0'):s=s[:-2]
 return s.zfill(12)
def text_from_csv_row(kind,r):
 # Convert archived CSV row to the exact parser-friendly BOATCAST text shape.
 if kind=='tkz':
  out=['data=','1']
  for b in range(1,7): out.append(f"{b}\t{r.get(f'艇{b}_展示タイム','')}")
  return '
'.join(out)+'
'
 raise RuntimeError(kind)
def archived_exhibition(code,state):
 ds=f'{code[:4]}/{code[4:6]}/{code[6:8]}'; j=int(code[8:10]);rn=int(code[10:12])
 tk={rc(x.get('レースコード')):x for x in rows(f'data/previews/tkz/{ds}.csv')}
 st={rc(x.get('レースコード')):x for x in rows(f'data/previews/stt/{ds}.csv')}
 og={rc(x.get('レースコード')):x for x in rows(f'data/previews/original_exhibition/{ds}.csv')}
 if code not in tk or code not in st: raise RuntimeError('ARCHIVED_EXHIBITION_MISSING')
 # Use archived CSV directly but build the same normalized strengths as production.
 from backtest_v3 import CORR
 from backtest_v51_lane_corrected_tickets import rank_scores
 from build_4head_v283_current_exhibition_live import _rank_strength
 disp={b:float(tk[code][f'艇{b}_展示タイム']) for b in range(1,7)}
 exraw={b:disp[b]+CORR[b]['展示'] for b in range(1,7)}; ex=rank_scores(exraw,True)
 st_raw={b:float(st[code][f'艇{b}_スタート展示']) for b in range(1,7)}
 bias={int(k):float(v) for k,v in (state.get('st_bias') or {}).items()}
 st_corr={b:st_raw[b]-bias.get(b,0.) for b in range(1,7)}; rr,rs=_rank_strength(st_raw);cr,cs=_rank_strength(st_corr)
 # Reuse the canonical historical original-exhibition correction.
 from backtest_v51_lane_corrected_tickets import corrected_direct
 old_rows=__import__('backtest_v51_lane_corrected_tickets').rows
 mod=__import__('backtest_v51_lane_corrected_tickets')
 def local(rel): return rows(rel)
 mod.rows=local
 try: _,_,osv=corrected_direct(code,tk,st,og,bias)
 finally: mod.rows=old_rows
 boats={};sf={}
 for b in range(1,7):
  z=osv[b]
  boats[str(b)]={'cur_ex':float(ex[b]),'cur_st':float(cs[b]),'cur_orig_lap':float(z.get('lap',0.)),'cur_orig_turn':float(z.get('turn',0.)),'cur_orig_straight':float(z.get('straight',0.)),'cur_orig_avg':float(z.get('avg',0.))}
  sf[f'st_raw_b{b}']=st_raw[b];sf[f'st_raw_rank_b{b}']=rr[b];sf[f'st_corr_rank_b{b}']=cr[b];sf[f'st_raw_strength_b{b}']=round(rs[b],4);sf[f'st_corr_strength_b{b}']=round(cs[b],4)
 return {'schema':'head4_historical_replay','race_code':code,'current_boats':boats,'st_flat':sf,'orig_avg_available':True,'orig_straight_available':True,'wall_exhibition_ready':True,'result_blind':True,'odds_used':False}
def load_odds():
 out={}
 for p in glob.glob(str(ROOT/'data/previews/od3/2026/09/*.csv')):
  q=pd.read_csv(p,dtype={'レースコード':str})
  for _,r in q.iterrows():
   code=rc(r.get('レースコード'))
   if not code.startswith(DATE):continue
   m={}
   for a in range(1,7):
    for b in range(1,7):
     if b==a:continue
     for c in range(1,7):
      if c in (a,b):continue
      k=f'{a}-{b}-{c}'
      try:v=float(r.get('3連単_'+k))
      except:continue
      if math.isfinite(v) and v>0:m[k]=v
   if len(m)==120:out[code]=m
 return out
def main():
 state=json.load(open(os.environ['STATE']));cards=fast.bycode(fast.rows_local(os.environ['CARD']));waku=fast.bycode(fast.rows_local(os.environ['WAKU'])); watch=json.load(open(os.environ['WATCH'])); odds=load_odds(); art=load_artifact(); frozen=[]
 for t in watch['targets']:
  code=f"{DATE}{int(t['jcd']):02d}{int(t['race']):02d}"
  if code not in cards or code not in waku or code not in odds:continue
  try: exh=archived_exhibition(code,state)
  except Exception as e:
   frozen.append({'race_code':code,'status':'EXHIBITION_MISSING','reason':str(e)});continue
  pf=fast.player_flat(cards[code],state); hp=fast.ph5_head_prob_live(cards[code],waku[code],exh,pf); src=fast.make_boats(cards[code],waku[code],exh,pf)
  sr,cr=fast.derive(src,art);p2=score_second(sr,art);pc=score_conditional_third(cr,art);tickets=fast.production_tickets(p2,pc);pairs=[tuple(map(int,x.split('-')[1:])) for x in tickets];mass=fast.pair_mass(p2,pc,pairs)
  vals=[odds[code][x] for x in tickets];comp=fast.composite_odds(vals);d=fast.newfeature_decide(hp,mass,comp,exh,cards[code],state,int(t['jcd']));shadow=bool(hp<.10)
  production_bet=bool(d['selected'] and not shadow)
  plan=live.dutch(tickets,vals) if production_bet else []
  frozen.append({'race_code':code,'status':'OK','head_prob':hp,'opponent_mass':mass,'composite_odds':comp,'base120':int(d['base120_selected']),'newfeature_add':int(d['newfeature_expanded_added']),'selected':int(d['selected']),'shadow':int(shadow),'production_bet':int(production_bet),'tickets':'|'.join(tickets),'ticket_count':len(tickets),'stake_plan':json.dumps(plan,ensure_ascii=False),'stake':sum(int(x['stake']) for x in plan)})
 out=Path('/tmp/head4_replay_20260922_v3');out.mkdir(exist_ok=True)
 pd.DataFrame(frozen).to_csv(out/'decision_frozen.csv',index=False)
 print('FROZEN',len(frozen),'OK',sum(x['status']=='OK' for x in frozen),'BET',sum(x.get('production_bet',0) for x in frozen))
 # truth only after freeze
 q=pd.read_csv(ROOT/'data/results/realtime/2026/09/22.csv',dtype={'レースコード':str});rcc=next(x for x in q if 'レース' in str(x) and 'コード' in str(x));c1=next(x for x in q if '1着' in str(x) and '艇' in str(x));c2=next(x for x in q if '2着' in str(x) and '艇' in str(x));c3=next(x for x in q if '3着' in str(x) and '艇' in str(x));truth={}
 for _,r in q.iterrows():
  try:truth[rc(r[rcc])]=(int(float(r[c1])),int(float(r[c2])),int(float(r[c3])))
  except:pass
 detail=[]
 for x in frozen:
  y=dict(x);a=truth.get(x['race_code']);actual='-'.join(map(str,a)) if a else '';pay=0.;hit=0
  if x.get('production_bet') and actual:
   for z in json.loads(x['stake_plan']):
    if z['combo']==actual:hit=1;pay=float(z['stake'])*float(z['odds'])
  y.update(actual=actual,head4=int(bool(a and a[0]==4)),hit=hit,payout=pay,profit=pay-int(x.get('stake',0)));detail.append(y)
 pd.DataFrame(detail).to_csv(out/'race_detail.csv',index=False)
 b=[x for x in detail if x.get('production_bet')];stake=sum(int(x['stake']) for x in b);pay=sum(float(x['payout']) for x in b)
 res={'target_date':'2026-09-22','watchlist_R':len(watch['targets']),'frozen_R':len(frozen),'valid_R':sum(x['status']=='OK' for x in frozen),'BET_R':len(b),'head4_R':sum(x['head4'] for x in b),'hits':sum(x['hit'] for x in b),'stake':stake,'payout':pay,'profit':pay-stake,'roi':100*pay/stake if stake else None,'base120_R':sum(x['base120'] for x in b),'newfeature_add_R':sum(x['newfeature_add'] for x in b),'truth_joined_after_freeze':True,'odds_source':'BoatraceCSV archived predeadline od3'}
 (out/'result.json').write_text(json.dumps(res,ensure_ascii=False,indent=2)+'
');print(json.dumps(res,ensure_ascii=False,indent=2));print('BET_DETAIL');[print({k:x[k] for k in ['race_code','head_prob','opponent_mass','composite_odds','ticket_count','actual','hit','stake','payout','profit']}) for x in b];print('HEAD4_SEP22_HISTORICAL_REPLAY_V3_OK')
if __name__=='__main__':main()
