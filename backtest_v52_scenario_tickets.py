"""v52: pre-race shortlist -> corrected direct-info approval -> scenario-specific 2nd/3rd tickets.
Train role priors: 2026-06-01..2026-07-15 results ONLY.
Validation: 2026-07-16..2026-08-02. Test: 2026-08-03..2026-09-02.
Candidate source is v46 pre-race output. target/result columns are discarded before scoring.
Current display/original exhibition are frame-corrected; ST display uses training-only frame bias.
STT course/entry columns are never used.
"""
import csv,re
from collections import defaultdict
from datetime import date,timedelta
from backtest import rows,race_features,grade_score,clamp,pct_motor
from analyze_v23_20260902_daypreview import by_code,venue_map,venue_score
from backtest_v51_lane_corrected_tickets import ff,ii,normkim,tilt_band,learn_st_frame_bias,corrected_direct

TR0=date(2026,6,1);TR1=date(2026,7,15)
VA0='2026-07-16';VA1='2026-08-02';TE0='2026-08-03';TE1='2026-09-02'
MODELS=['3まくり','3まくり差し','4カドまくり','5頭展開']
HEAD={'3まくり':3,'3まくり差し':3,'4カドまくり':4,'5頭展開':5}
POINTS=[4,6,8,20]
TILT_BONUS={
 '3まくり':{-1:-.05,0:-.21,.5:.10,1:3.00},
 '3まくり差し':{-1:-.23,0:-.05,.5:1.34,1:.93},
 '4カドまくり':{-1:-1.19,0:-.04,.5:3.00,1:1.59},
 '5頭展開':{-1:0,0:0,.5:0,1:0},
}

def route_match(m,win,kim):
 if m=='3まくり':return win==3 and kim=='まくり'
 if m=='3まくり差し':return win==3 and kim=='まくり差し'
 if m=='4カドまくり':return win==4 and kim=='まくり'
 return win==5

def parse_combo(s):
 a=[int(x) for x in re.findall(r'[1-6]',s or '')]
 return a[:3] if len(a)>=3 else []

def learn_role_priors():
 # Results are used here ONLY inside the fixed training window.
 cnt={m:{'sec':defaultdict(lambda:1.0),'third':defaultdict(lambda:1.0)} for m in MODELS}
 totals={m:0 for m in MODELS};d=TR0
 while d<=TR1:
  ymd=d.strftime('%Y/%m/%d')
  res={r['レースコード']:r for r in rows(f'data/results/realtime/{ymd}.csv')}
  pay={r['レースコード']:r for r in rows(f'data/results/payouts/{ymd}.csv')}
  for code,rr in res.items():
   win=ii(rr.get('1着_艇番'));kim=normkim(rr.get('決まり手'));a=parse_combo(pay.get(code,{}).get('3連単_組番',''))
   if len(a)<3:continue
   for m in MODELS:
    if route_match(m,win,kim):
     cnt[m]['sec'][a[1]]+=1;cnt[m]['third'][a[2]]+=1;totals[m]+=1
  d+=timedelta(days=1)
 out={}
 for m in MODELS:
  head=HEAD[m];out[m]={}
  for role in ['sec','third']:
   vals={b:cnt[m][role][b] for b in range(1,7) if b!=head};lo=min(vals.values());hi=max(vals.values())
   out[m][role]={b:(.5 if hi==lo else (v-lo)/(hi-lo)) for b,v in vals.items()}
 return out,totals

def preview_comp(m,venue,ex,st,os,vidx):
 h=HEAD[m];vs=venue_score(vidx.get((m,str(venue).zfill(2)),1.0));z=os[h]
 if m=='3まくり':return .28*ex[h]+.28*st[h]+.22*z['straight']+.17*z['avg']+.05*vs
 if m=='3まくり差し':return .17*ex[h]+.22*st[h]+.17*z['lap']+.27*z['turn']+.12*z['avg']+.05*vs
 if m=='4カドまくり':return .28*ex[h]+.30*st[h]+.22*z['straight']+.15*z['avg']+.05*vs
 z4=os[4];attack4=.32*ex[4]+.38*st[4]+.18*z4['straight']+.12*z4['avg']
 take5=.22*ex[5]+.17*st[5]+.27*z['lap']+.27*z['turn']+.07*z['avg']
 return .43*attack4+.52*take5+.05*vs

def base_place(x,b,ex,st,os):
 z=x[b];motor=.62*pct_motor(z['motor2'])+.38*pct_motor(z['motor3'])
 q=clamp((z['wr']-3.0)/5.0);loc=clamp((z['local']-2.5)/5.5);ww=clamp(z['waku_wr']/8.0);nst=clamp((.24-z['nst'])/.14)
 direct=.25*ex.get(b,.5)+.18*st.get(b,.5)+.30*os[b]['turn']+.12*os[b]['lap']+.15*os[b]['avg']
 return .15*grade_score(z['grade'])+.18*q+.07*loc+.17*motor+.13*ww+.08*nst+.22*direct

def structure_bonus(m,role,b):
 # small fixed race-logic prior; training role prior remains the main scenario term.
 if m=='3まくり':
  mp={'sec':{4:.16,5:.13,1:.09,2:.06,6:.05},'third':{1:.13,2:.11,4:.10,5:.09,6:.06}}
 elif m=='3まくり差し':
  mp={'sec':{1:.16,2:.13,4:.09,5:.07,6:.04},'third':{4:.13,5:.11,1:.10,2:.09,6:.06}}
 elif m=='4カドまくり':
  mp={'sec':{5:.17,6:.11,1:.09,2:.07,3:.05},'third':{1:.13,2:.11,5:.10,6:.08,3:.05}}
 else:
  mp={'sec':{4:.17,1:.12,6:.09,2:.07,3:.05},'third':{1:.13,4:.12,2:.10,6:.08,3:.05}}
 return mp[role].get(b,0)

def role_score(m,role,x,b,ex,st,os,pri):
 return .64*base_place(x,b,ex,st,os)+.26*pri[m][role].get(b,.5)+structure_bonus(m,role,b)

def pair_bonus(m,a,b):
 if m=='3まくり':return .06 if (a in (4,5,6) and b in (1,2)) else 0
 if m=='3まくり差し':return .06 if (a in (1,2) and b in (4,5,6)) else 0
 if m=='4カドまくり':return .07 if (a in (5,6) and b in (1,2)) else 0
 return .07 if ((a==4 and b in (1,2,6)) or (a==1 and b==4)) else 0

def ranked_tickets(m,x,ex,st,os,pri):
 h=HEAD[m];cand=[]
 for a in range(1,7):
  if a==h:continue
  for b in range(1,7):
   if b in (h,a):continue
   s=role_score(m,'sec',x,a,ex,st,os,pri)+role_score(m,'third',x,b,ex,st,os,pri)+pair_bonus(m,a,b)
   cand.append((s,f'{h}-{a}-{b}'))
 cand.sort(reverse=True)
 return [c for _,c in cand]

def freeze_rows(stbias,pri):
 with open('analysis_v46_history_softscore.csv',encoding='utf-8-sig') as f:
  src=[{k:v for k,v in r.items() if k!='target'} for r in csv.DictReader(f)
       if r.get('model') in MODELS and VA0<=r.get('date','')<=TE1]
 vidx=venue_map();cache={};cards_cache={};groups=defaultdict(list)
 for r in src:
  d=r['date'];ymd=d.replace('-','/');code=r['race_code'];m=r['model'];h=HEAD[m];venue=code[8:10]
  if d not in cache:
   cache[d]=(by_code(f'data/previews/tkz/{ymd}.csv'),by_code(f'data/previews/stt/{ymd}.csv'),by_code(f'data/previews/original_exhibition/{ymd}.csv'))
   cards_cache[d]=(by_code(f'data/programs/race_cards/{ymd}.csv'),by_code(f'data/programs/waku10/{ymd}.csv'))
  tkz,stt,orig=cache[d];cards,w10=cards_cache[d];card=cards.get(code,{})
  if not card:continue
  ex,st,os=corrected_direct(code,tkz,stt,orig,stbias);x=race_features(card,w10.get(code,{}))
  comp=preview_comp(m,venue,ex,st,os,vidx);tr=tkz.get(code,{})
  tilt=ff(tr.get(f'艇{h}_チルト'),0) or 0;hist=ff(r.get('history_adjust'),0) or 0
  score=100*comp+hist+TILT_BONUS[m][tilt_band(tilt)]
  alltk=ranked_tickets(m,x,ex,st,os,pri)
  z={'date':d,'period':'validation' if d<=VA1 else 'test','race_code':code,'model':m,'head_boat':h,
     'v52_score':score,'approved_A':int(score>=55),'approved_S':int(score>=67),'preview_comp':comp,
     'history_pct':ff(r.get('history_pct'),.5),'tilt':tilt,'ex_head':ex.get(h,.5),'st_head':st.get(h,.5),
     'orig_turn_head':os[h]['turn'],'orig_straight_head':os[h]['straight']}
  for p in POINTS:z[f'tickets_{p}']=';'.join(alltk[:p])
  groups[(d,code,h)].append(z)
 frozen=[]
 for _,arr in groups.items():
  # 3-head duplicates are collapsed before any validation/test result is loaded.
  frozen.append(max(arr,key=lambda z:z['v52_score']))
 return frozen,len(src)

def settle(frozen):
 byday=defaultdict(list)
 for z in frozen:byday[z['date']].append(z)
 out=[]
 for d,arr in sorted(byday.items()):
  ymd=d.replace('-','/');res={r['レースコード']:r for r in rows(f'data/results/realtime/{ymd}.csv')};pay={r['レースコード']:r for r in rows(f'data/results/payouts/{ymd}.csv')}
  for z in arr:
   rr=res.get(z['race_code'],{});pr=pay.get(z['race_code'],{});win=ii(rr.get('1着_艇番'));kim=normkim(rr.get('決まり手'));combo=(pr.get('3連単_組番') or '').strip();payout=ii(pr.get('3連単_払戻金'))
   z=dict(z);z.update({'winner':win,'kimarite':kim,'head_hit':int(win==z['head_boat']),'method_hit':int(route_match(z['model'],win,kim)),'actual_combo':combo,'payout':payout})
   for p in POINTS:
    ts=z[f'tickets_{p}'].split(';') if z[f'tickets_{p}'] else []
    z[f'hit_{p}']=int(combo in ts);z[f'return_{p}']=payout if combo in ts else 0;z[f'invest_{p}']=len(ts)*100
   out.append(z)
 return out

def stat(rs,p):
 n=len(rs);hh=sum(z['head_hit'] for z in rs);mh=sum(z['method_hit'] for z in rs);bh=sum(z[f'hit_{p}'] for z in rs);inv=sum(z[f'invest_{p}'] for z in rs);ret=sum(z[f'return_{p}'] for z in rs)
 return n,hh,(100*hh/n if n else 0),mh,(100*mh/n if n else 0),bh,(100*bh/n if n else 0),inv,ret,(100*ret/inv if inv else 0)

def main():
 stbias=learn_st_frame_bias();pri,ptot=learn_role_priors();frozen,srcn=freeze_rows(stbias,pri);out=settle(frozen)
 with open('analysis_v52_scenario_tickets.csv','w',newline='',encoding='utf-8-sig') as f:
  fs=sorted(set().union(*(z.keys() for z in out)));w=csv.DictWriter(f,fieldnames=fs);w.writeheader();w.writerows(out)
 L=['# v52 事前候補→枠補正済み直前承認→展開別2/3着モデル','',
    '前日段階はv46候補をそのまま使用。validation/testの結果列は破棄。直前に枠補正済み展示・ST展示・オリジナル展示・チルトでA/S承認と3号艇の決まり手分岐を固定。',
    '2/3着は6/1-7/15の結果だけで展開別の残り艇傾向を学習し、選手力・枠別成績・モーター・枠補正済み直前展示と合成。7/16以降の結果は買い目固定後にのみロード。',
    f'v46入力行={srcn}、頭重複統合後={len(frozen)}。','',
    '## 学習期間の展開成立数']
 for m in MODELS:L.append(f'- {m}: {ptot[m]}R')
 L+=['','## 学習した2着/3着上位枠（0-1正規化）']
 for m in MODELS:
  s=sorted(pri[m]['sec'].items(),key=lambda x:x[1],reverse=True);t=sorted(pri[m]['third'].items(),key=lambda x:x[1],reverse=True)
  L.append(f'- {m}: 2着 '+', '.join(f'{b}号艇={v:.2f}' for b,v in s[:3])+' / 3着 '+', '.join(f'{b}号艇={v:.2f}' for b,v in t[:3]))
 for period in ['validation','test']:
  L+=['',f'## {period} 直前A以上','|モデル|点数|候補R|頭率|決まり手成立率|3連単的中率|投資|払戻|ROI|','|---|---:|---:|---:|---:|---:|---:|---:|---:|']
  for m in MODELS:
   rs=[z for z in out if z['period']==period and z['approved_A'] and z['model']==m]
   for p in POINTS:
    n,hh,hr,mh,mr,bh,br,inv,ret,roi=stat(rs,p);L.append(f'|{m}|{p}|{n}|{hr:.1f}%|{mr:.1f}%|{br:.1f}%|{inv:,}円|{ret:,}円|{roi:.1f}%|')
 L+=['','## test 直前Sのみ','|モデル|点数|候補R|頭率|3連単的中率|ROI|','|---|---:|---:|---:|---:|---:|']
 for m in MODELS:
  rs=[z for z in out if z['period']=='test' and z['approved_S'] and z['model']==m]
  for p in POINTS:
   n,hh,hr,mh,mr,bh,br,inv,ret,roi=stat(rs,p);L.append(f'|{m}|{p}|{n}|{hr:.1f}%|{br:.1f}%|{roi:.1f}%|')
 open('summary_v52_scenario_tickets.md','w',encoding='utf-8').write('\n'.join(L)+'\n')

if __name__=='__main__':main()
