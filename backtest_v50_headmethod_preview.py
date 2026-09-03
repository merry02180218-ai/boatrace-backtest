"""v50 trial: separate head prediction from kimarite, with strict pre-result direct-info stage.
Period: 2026-08-03..2026-09-02.
Candidate source: v46 output, but result-derived target is explicitly ignored.
Direct info: tkz exhibition time + tilt, stt start-exhibition TIMING ONLY (course fields ignored), original exhibition.
History remains soft. Results/payouts are loaded only after candidates, subtype, score and approval are frozen.
"""
import csv
from collections import defaultdict
from backtest import rows
from analyze_v23_20260902_daypreview import by_code, venue_map, preview_for

START='2026-08-03'; END='2026-09-02'
HEAD={'3まくり':3,'3まくり差し':3,'4カドまくり':4,'5頭展開':5}
TILT_BONUS={
 '3まくり':{-1:-.05,0:-.21,.5:.10,1:3.00},
 '3まくり差し':{-1:-.23,0:-.05,.5:1.34,1:.93},
 '4カドまくり':{-1:-1.19,0:-.04,.5:3.00,1:.59},
 '5頭展開':{-1:0,0:0,.5:0,1:0},
}

def ff(x,d=.5):
 try:return float(x)
 except:return d

def ii(x,d=0):
 try:return int(float(x))
 except:return d

def tilt_band(x):
 v=ff(x,0)
 if v<=-0.5:return -1
 if v<0.5:return 0
 if v<1.0:return .5
 return 1

def normkim(x):return (x or '').replace(' ','').replace('　','')

def model_method_hit(model,win,kim):
 if model=='3まくり':return int(win==3 and kim=='まくり')
 if model=='3まくり差し':return int(win==3 and kim=='まくり差し')
 if model=='4カドまくり':return int(win==4 and kim=='まくり')
 return int(win==5)

def main():
 # PRE-RESULT PHASE 1: load v46 candidate/history rows; discard target/result column entirely.
 with open('analysis_v46_history_softscore.csv',encoding='utf-8-sig') as f:
  src=[]
  for r in csv.DictReader(f):
   if not (START<=r.get('date','')<=END):continue
   src.append({k:v for k,v in r.items() if k!='target'})

 # PRE-RESULT PHASE 2: enrich with direct info and freeze model-specific confidence.
 vidx=venue_map(); cache={}; modelrows=[]
 for r in src:
  d=r['date'];ymd=d.replace('-','/');code=r['race_code'];m=r['model'];boat=HEAD[m]
  if d not in cache:
   cache[d]=(by_code(f'data/previews/tkz/{ymd}.csv'),by_code(f'data/previews/stt/{ymd}.csv'),by_code(f'data/previews/original_exhibition/{ymd}.csv'))
  tkz,stt,orig=cache[d];venue=code[8:10]
  p=preview_for(m,code,venue,tkz,stt,orig,vidx)
  tr=tkz.get(code,{})
  tilt=ff(tr.get(f'艇{boat}_チルト'),0);tb=tilt_band(tilt);tbonus=TILT_BONUS[m][tb]
  hist=ff(r.get('history_adjust'),0)
  # preview 0..1 => 0..100. History and tilt are previously fixed soft point bonuses.
  score=100*p['preview_comp']+hist+tbonus
  grade='S' if score>=67 else ('A' if score>=55 else 'B')
  z={'date':d,'race_code':code,'venue':venue,'race':code[-2:],'model':m,'head_boat':boat,
     'history_pct':ff(r.get('history_pct')),'history_adjust':hist,
     'preview_comp':p['preview_comp'],'preview_grade':p['grade'],'ex_score':p['ex_score'],'st_score':p['st_score'],
     'orig_lap':p['orig_lap'],'orig_turn':p['orig_turn'],'orig_straight':p['orig_straight'],'orig_avg':p['orig_avg'],
     'tilt':tilt,'tilt_bonus':tbonus,'v50_score':score,'v50_grade':grade}
  modelrows.append(z)

 # PRE-RESULT PHASE 3: redesign to one head candidate per boat/race. For 3-head, subtype is chosen BEFORE results.
 groups=defaultdict(list)
 for z in modelrows:groups[(z['date'],z['race_code'],z['head_boat'])].append(z)
 frozen=[]
 for key,arr in groups.items():
  # if 3-makuri and 3-makurizashi both qualify, direct-info score chooses expected method.
  chosen=max(arr,key=lambda z:z['v50_score'])
  # head confidence uses strongest applicable route; duplicates are collapsed.
  frozen.append(dict(chosen,route_count=len(arr),approved_A=int(chosen['v50_score']>=55),approved_S=int(chosen['v50_score']>=67)))

 # RESULT PHASE starts here. No field below can alter candidate/subtype/approval.
 byday=defaultdict(list)
 for z in frozen:byday[z['date']].append(z)
 out=[]
 for d,fr in sorted(byday.items()):
  ymd=d.replace('-','/');res={r['レースコード']:r for r in rows(f'data/results/realtime/{ymd}.csv')};pay={r['レースコード']:r for r in rows(f'data/results/payouts/{ymd}.csv')}
  for z in fr:
   rr=res.get(z['race_code'],{});pr=pay.get(z['race_code'],{});win=ii(rr.get('1着_艇番'));kim=normkim(rr.get('決まり手'))
   head_hit=int(win==z['head_boat']);method_hit=model_method_hit(z['model'],win,kim)
   payout=ii(pr.get('3連単_払戻金')) if head_hit else 0
   z.update({'winner':win,'kimarite':kim,'actual_combo':(pr.get('3連単_組番') or '').strip(),'trifecta_payout':ii(pr.get('3連単_払戻金')),'head_hit':head_hit,'method_hit':method_hit,'return_20pt':payout})
   out.append(z)

 with open('analysis_v50_headmethod_preview.csv','w',newline='',encoding='utf-8-sig') as f:
  fs=sorted(set().union(*(z.keys() for z in out)));w=csv.DictWriter(f,fieldnames=fs);w.writeheader();w.writerows(out)

 def stat(rs):
  n=len(rs);hh=sum(z['head_hit'] for z in rs);mh=sum(z['method_hit'] for z in rs);inv=n*2000;ret=sum(z['return_20pt'] for z in rs)
  return n,hh,(100*hh/n if n else 0),mh,(100*mh/n if n else 0),inv,ret,(100*ret/inv if inv else 0)
 L=['# v50 頭モデル / 決まり手分離 + 直前情報バックテスト','',
    f'対象: {START}〜{END}。v46候補から結果由来target列を破棄し、直前の展示タイム・スタート展示タイムのみ・オリジナル展示・チルトを加えてスコア固定。その後で初めて着順/払戻を読む。実進入・スタート展示のコース列は不使用。',
    '3号艇は「頭候補」を先に統合し、3まくり/3まくり差しが重複した場合は直前+履歴+学習済みチルト補正の高い方を決まり手予測として固定。4号艇は4カドまくり、5号艇は5頭展開。',
    'ROIは頭モデル比較用に、頭固定-残り5艇2/3着総流し20点×100円=2,000円/R。買い目絞り込みはまだ行わない。','',
    '## 承認閾値比較','|区分|候補R|頭的中|頭率|決まり手成立|成立率|投資|払戻|ROI|','|---|---:|---:|---:|---:|---:|---:|---:|---:|']
 for name,rs in [('全候補',out),('直前A以上',[z for z in out if z['approved_A']]),('直前S',[z for z in out if z['approved_S']])]:
  n,hh,hr,mh,mr,inv,ret,roi=stat(rs);L.append(f'|{name}|{n}|{hh}|{hr:.1f}%|{mh}|{mr:.1f}%|{inv:,}円|{ret:,}円|{roi:.1f}%|')
 L+=['','## 頭モデル別（直前A以上）','|頭モデル|候補R|頭的中|頭率|決まり手成立|成立率|投資|払戻|ROI|','|---|---:|---:|---:|---:|---:|---:|---:|---:|']
 for boat,label in [(3,'3頭'),(4,'4頭'),(5,'5頭')]:
  rs=[z for z in out if z['approved_A'] and z['head_boat']==boat];n,hh,hr,mh,mr,inv,ret,roi=stat(rs);L.append(f'|{label}|{n}|{hh}|{hr:.1f}%|{mh}|{mr:.1f}%|{inv:,}円|{ret:,}円|{roi:.1f}%|')
 L+=['','## 3頭の決まり手予測（直前A以上）','|予測|R|3号艇頭|頭率|予測決まり手一致|一致率|','|---|---:|---:|---:|---:|---:|']
 for m in ['3まくり','3まくり差し']:
  rs=[z for z in out if z['approved_A'] and z['head_boat']==3 and z['model']==m];n,hh,hr,mh,mr,_,_,_=stat(rs);L.append(f'|{m}|{n}|{hh}|{hr:.1f}%|{mh}|{mr:.1f}%|')
 L+=['','## 9/1 再確認（直前A以上）','|頭|R|頭的中|頭率|払戻|ROI|','|---|---:|---:|---:|---:|---:|']
 for boat in [3,4,5]:
  rs=[z for z in out if z['date']=='2026-09-01' and z['approved_A'] and z['head_boat']==boat];n,hh,hr,_,_,inv,ret,roi=stat(rs);L.append(f'|{boat}頭|{n}|{hh}|{hr:.1f}%|{ret:,}円|{roi:.1f}%|')
 open('summary_v50_headmethod_preview.md','w',encoding='utf-8').write('\n'.join(L)+'\n')

if __name__=='__main__':main()
