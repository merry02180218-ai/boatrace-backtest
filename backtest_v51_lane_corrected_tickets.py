"""v51: lane/frame-correct current direct info + head-first ticket reduction.
Validation: 2026-07-16..2026-08-02. Test: 2026-08-03..2026-09-02.
Focus heads: 3 and 5. Results/payouts are loaded only after candidate approval, subtype and tickets are frozen.
Current display/original exhibition are frame corrected with the same CORR used for prior exhibitions.
Start-exhibition timing uses a frame-bias correction learned only from 2026-06-01..2026-07-15 STT data.
STT course/entry columns are not used.
"""
import csv
from collections import defaultdict
from datetime import date,timedelta
from statistics import mean
from backtest import rows,race_features,grade_score,clamp,pct_motor
from backtest_v3 import CORR
from analyze_v23_20260902_daypreview import by_code,venue_map,venue_score

TR0=date(2026,6,1);TR1=date(2026,7,15)
VA0='2026-07-16';VA1='2026-08-02';TE0='2026-08-03';TE1='2026-09-02'
MODELS=['3まくり','3まくり差し','5頭展開']
HEAD={'3まくり':3,'3まくり差し':3,'5頭展開':5}
POINTS=[4,6,8,20]
TILT_BONUS={
 '3まくり':{-1:-.05,0:-.21,.5:.10,1:3.00},
 '3まくり差し':{-1:-.23,0:-.05,.5:1.34,1:.93},
 '5頭展開':{-1:0,0:0,.5:0,1:0},
}

def ff(x,d=None):
 try:return float(x)
 except:return d

def ii(x,d=0):
 try:return int(float(x))
 except:return d

def normkim(x):return (x or '').replace(' ','').replace('　','')
def tilt_band(x):
 v=ff(x,0) or 0
 if v<=-.5:return -1
 if v<.5:return 0
 if v<1:return .5
 return 1

def norm_metric(label):
 s=(label or '').replace(' ','').replace('　','')
 if '直線' in s:return '直線'
 if 'まわり' in s:return 'まわり足'
 if '回り' in s or 'ターン' in s:return '回り足'
 if '一周' in s or 'ラップ' in s or ('周' in s and '周波数' not in s):return '一周'
 return s

def rank_scores(vals,lower=True):
 a=[(b,v) for b,v in vals.items() if v is not None]
 if len(a)<2:return {b:.5 for b in vals}
 a=sorted(a,key=lambda z:z[1],reverse=not lower);n=len(a)
 return {b:1-j/(n-1) for j,(b,_) in enumerate(a)}

def learn_st_frame_bias():
 sums=defaultdict(list);allv=[];d=TR0
 while d<=TR1:
  ymd=d.strftime('%Y/%m/%d')
  for r in rows(f'data/previews/stt/{ymd}.csv'):
   for b in range(1,7):
    v=ff(r.get(f'艇{b}_スタート展示'))
    if v is not None and -.30<v<1.0:sums[b].append(v);allv.append(v)
  d+=timedelta(days=1)
 g=mean(allv) if allv else .15
 return {b:(mean(sums[b])-g if sums[b] else 0.0) for b in range(1,7)}

def corrected_direct(code,tkz,stt,orig,stbias):
 tr=tkz.get(code,{});sr=stt.get(code,{});orr=orig.get(code,{})
 exraw={b:(ff(tr.get(f'艇{b}_展示タイム')) + CORR[b]['展示'] if ff(tr.get(f'艇{b}_展示タイム')) is not None else None) for b in range(1,7)}
 ex=rank_scores(exraw,True)
 straw={}
 for b in range(1,7):
  v=ff(sr.get(f'艇{b}_スタート展示'))
  straw[b]=(v-stbias[b]) if v is not None else None
 st=rank_scores(straw,True)
 os={b:{'lap':.5,'turn':.5,'straight':.5,'avg':.5} for b in range(1,7)}
 labels=[orr.get(f'計測項目{k}','') for k in range(1,5)] if orr else []
 per={b:[] for b in range(1,7)}
 for k,label in enumerate(labels,1):
  if not label:continue
  mk=norm_metric(label)
  vals={}
  for b in range(1,7):
   v=ff(orr.get(f'艇{b}_値{k}'))
   vals[b]=(v+CORR[b].get(mk,0)) if v is not None else None
  sc=rank_scores(vals,True)
  for b in range(1,7):
   if vals.get(b) is None:continue
   per[b].append(sc[b])
   if mk=='直線':os[b]['straight']=sc[b]
   elif mk in ('一周',):os[b]['lap']=sc[b]
   elif mk in ('まわり足','回り足'):os[b]['turn']=sc[b]
 for b in range(1,7):
  if per[b]:os[b]['avg']=sum(per[b])/len(per[b])
 return ex,st,os

def preview_comp(m,boat,venue,ex,st,os,vidx):
 vs=venue_score(vidx.get((m,str(venue).zfill(2)),1.0));z=os[boat]
 if m=='3まくり':return .28*ex[boat]+.28*st[boat]+.22*z['straight']+.17*z['avg']+.05*vs
 if m=='3まくり差し':return .17*ex[boat]+.22*st[boat]+.17*z['lap']+.27*z['turn']+.12*z['avg']+.05*vs
 # 5-head: 4 attack + 5 take-up
 z4=os[4];attack4=.32*ex[4]+.38*st[4]+.18*z4['straight']+.12*z4['avg']
 take5=.22*ex[5]+.17*st[5]+.27*z['lap']+.27*z['turn']+.07*z['avg']
 return .43*attack4+.52*take5+.05*vs

def opp_place_score(x,b,ex,st,os):
 z=x[b]; motor=.62*pct_motor(z['motor2'])+.38*pct_motor(z['motor3'])
 q=clamp((z['wr']-3.0)/5.0);loc=clamp((z['local']-2.5)/5.5);ww=clamp(z['waku_wr']/8.0)
 nst=clamp((.24-z['nst'])/.14)
 direct=.35*ex[b]+.20*st[b]+.25*os[b]['turn']+.20*os[b]['avg']
 return .16*grade_score(z['grade'])+.19*q+.08*loc+.17*motor+.13*ww+.09*nst+.18*direct

def tickets_for(head,ranked,npt):
 if npt==20:
  return [f'{head}-{a}-{b}' for a in ranked for b in ranked if b!=a]
 sec=ranked[:2]
 k={4:3,6:4,8:5}[npt];third=ranked[:k]
 return [f'{head}-{a}-{b}' for a in sec for b in third if b!=a]

def freeze_rows(stbias):
 with open('analysis_v46_history_softscore.csv',encoding='utf-8-sig') as f:
  src=[]
  for r in csv.DictReader(f):
   if r.get('model') not in MODELS:continue
   if not (VA0<=r.get('date','')<=TE1):continue
   src.append({k:v for k,v in r.items() if k!='target'})
 vidx=venue_map();cache={};cards_cache={};groups=defaultdict(list)
 for r in src:
  d=r['date'];ymd=d.replace('-','/');code=r['race_code'];m=r['model'];head=HEAD[m];venue=code[8:10]
  if d not in cache:
   cache[d]=(by_code(f'data/previews/tkz/{ymd}.csv'),by_code(f'data/previews/stt/{ymd}.csv'),by_code(f'data/previews/original_exhibition/{ymd}.csv'))
   cards_cache[d]=(by_code(f'data/programs/race_cards/{ymd}.csv'),by_code(f'data/programs/waku10/{ymd}.csv'))
  tkz,stt,orig=cache[d];cards,w10=cards_cache[d]
  ex,st,os=corrected_direct(code,tkz,stt,orig,stbias)
  comp=preview_comp(m,head,venue,ex,st,os,vidx);tr=tkz.get(code,{})
  tilt=ff(tr.get(f'艇{head}_チルト'),0) or 0;hist=ff(r.get('history_adjust'),0) or 0;score=100*comp+hist+TILT_BONUS[m][tilt_band(tilt)]
  card=cards.get(code,{});x=race_features(card,w10.get(code,{})) if card else None
  if not x:continue
  ranked=sorted([b for b in range(1,7) if b!=head],key=lambda b:opp_place_score(x,b,ex,st,os),reverse=True)
  z={'date':d,'period':'validation' if d<=VA1 else 'test','race_code':code,'model':m,'head_boat':head,'v51_score':score,'approved_A':int(score>=55),'approved_S':int(score>=67),'preview_comp':comp,'history_pct':ff(r.get('history_pct'),.5),'tilt':tilt,'ex_head':ex[head],'st_head':st[head],'orig_turn_head':os[head]['turn'],'orig_straight_head':os[head]['straight'],'ranked_others':'-'.join(map(str,ranked))}
  for p in POINTS:z[f'tickets_{p}']=';'.join(tickets_for(head,ranked,p))
  groups[(d,code,head)].append(z)
 frozen=[]
 for _,arr in groups.items():
  # head=3 duplicates: freeze expected method using corrected direct-info score; 5 has one route.
  frozen.append(max(arr,key=lambda z:z['v51_score']))
 return frozen

def settle(frozen):
 byday=defaultdict(list)
 for z in frozen:byday[z['date']].append(z)
 out=[]
 for d,arr in sorted(byday.items()):
  ymd=d.replace('-','/');res={r['レースコード']:r for r in rows(f'data/results/realtime/{ymd}.csv')};pay={r['レースコード']:r for r in rows(f'data/results/payouts/{ymd}.csv')}
  for z in arr:
   rr=res.get(z['race_code'],{});pr=pay.get(z['race_code'],{});win=ii(rr.get('1着_艇番'));kim=normkim(rr.get('決まり手'));combo=(pr.get('3連単_組番') or '').strip();payout=ii(pr.get('3連単_払戻金'))
   z=dict(z);z['winner']=win;z['kimarite']=kim;z['head_hit']=int(win==z['head_boat']);z['actual_combo']=combo;z['payout']=payout
   for p in POINTS:
    ts=z[f'tickets_{p}'].split(';') if z[f'tickets_{p}'] else []
    z[f'hit_{p}']=int(combo in ts);z[f'return_{p}']=payout if combo in ts else 0;z[f'invest_{p}']=len(ts)*100
   out.append(z)
 return out

def stat(rs,p):
 n=len(rs);hh=sum(z['head_hit'] for z in rs);bh=sum(z[f'hit_{p}'] for z in rs);inv=sum(z[f'invest_{p}'] for z in rs);ret=sum(z[f'return_{p}'] for z in rs)
 return n,hh,100*hh/n if n else 0,bh,100*bh/n if n else 0,inv,ret,100*ret/inv if inv else 0

def main():
 stbias=learn_st_frame_bias();frozen=freeze_rows(stbias);out=settle(frozen)
 with open('analysis_v51_lane_corrected_tickets.csv','w',newline='',encoding='utf-8-sig') as f:
  fs=sorted(set().union(*(z.keys() for z in out)));w=csv.DictWriter(f,fieldnames=fs);w.writeheader();w.writerows(out)
 L=['# v51 枠補正済み直前情報 + 3頭/5頭 買い目絞りバックテスト','',
    '当日展示タイムと当日オリジナル展示はv3と同じ枠補正を raw 値に入れてから相対順位化。スタート展示タイムは学習期間(6/1-7/15)だけで艇番別平均差を推定して補正。STTのコース/進入列は使わない。',
    '候補・頭・3頭の決まり手予測・直前A/S承認・2/3着順位・買い目を先に固定し、その後で着順/払戻をロード。',
    '2/3着順位は選手級別/全国・当地勝率/枠別勝率/ST/モーター2・3連率/枠補正済み直前展示を合成。4点=2着上位2×3着上位3、6点=2×4、8点=2×5、20点=総流し。','',
    '## 学習したスタート展示 枠バイアス（平均との差、秒）','|艇|1|2|3|4|5|6|','|---|---:|---:|---:|---:|---:|---:|',
    '|bias|'+'|'.join(f'{stbias[b]:+.4f}' for b in range(1,7))+'|']
 for period in ['validation','test']:
  L+=['',f'## {period} 直前A以上','|頭|点数|候補R|頭的中|頭率|3連単的中|的中率|投資|払戻|ROI|','|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
  for head in [3,5]:
   rs=[z for z in out if z['period']==period and z['approved_A'] and z['head_boat']==head]
   for p in POINTS:
    n,hh,hr,bh,br,inv,ret,roi=stat(rs,p);L.append(f'|{head}頭|{p}|{n}|{hh}|{hr:.1f}%|{bh}|{br:.1f}%|{inv:,}円|{ret:,}円|{roi:.1f}%|')
  rs=[z for z in out if z['period']==period and z['approved_A']]
  for p in POINTS:
   n,hh,hr,bh,br,inv,ret,roi=stat(rs,p);L.append(f'|合計|{p}|{n}|{hh}|{hr:.1f}%|{bh}|{br:.1f}%|{inv:,}円|{ret:,}円|{roi:.1f}%|')
 L+=['','## test 直前Sのみ','|頭|点数|候補R|頭率|3連単的中率|ROI|','|---|---:|---:|---:|---:|---:|']
 for head in [3,5]:
  rs=[z for z in out if z['period']=='test' and z['approved_S'] and z['head_boat']==head]
  for p in POINTS:
   n,hh,hr,bh,br,inv,ret,roi=stat(rs,p);L.append(f'|{head}頭|{p}|{n}|{hr:.1f}%|{br:.1f}%|{roi:.1f}%|')
 open('summary_v51_lane_corrected_tickets.md','w',encoding='utf-8').write('\n'.join(L)+'\n')

if __name__=='__main__':main()
