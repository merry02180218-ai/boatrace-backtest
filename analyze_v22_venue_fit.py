from backtest import rows, i
from collections import defaultdict
from datetime import date, timedelta
import csv

TRAIN_START=date(2026,6,1); TRAIN_END=date(2026,7,15)
DEV_START=date(2026,8,3); DEV_END=date(2026,8,26)
ALPHA=80.0
MODELS=['3まくり','3まくり差し','4カドまくり','5頭展開']

def target(rr,m):
    win=i(rr.get('1着_艇番')); kim=(rr.get('決まり手') or '').replace('　','').replace(' ','')
    if m=='3まくり': return int(win==3 and kim=='まくり')
    if m=='3まくり差し': return int(win==3 and kim=='まくり差し')
    if m=='4カドまくり': return int(win==4 and kim=='まくり')
    return int(win==5)

def venue_from_code(code):
    # race code format YYYYMMDDJJRR: JJ is venue code.
    s=str(code or '').strip()
    return s[8:10] if len(s)>=12 else ''

counts={m:defaultdict(lambda:[0,0]) for m in MODELS}
global_counts={m:[0,0] for m in MODELS}
d=TRAIN_START
while d<=TRAIN_END:
    ymd=d.strftime('%Y/%m/%d')
    for rr in rows(f'data/results/realtime/{ymd}.csv'):
        v=venue_from_code(rr.get('レースコード'))
        if not v: continue
        for m in MODELS:
            y=target(rr,m); counts[m][v][0]+=y; counts[m][v][1]+=1; global_counts[m][0]+=y; global_counts[m][1]+=1
    d+=timedelta(days=1)

venue_rows=[]; venue_index={m:{} for m in MODELS}
for m in MODELS:
    gh,gn=global_counts[m]; gr=gh/gn if gn else 0
    for v in sorted(counts[m]):
        h,n=counts[m][v]; sr=(h+ALPHA*gr)/(n+ALPHA) if n+ALPHA else gr; idx=(sr/gr) if gr else 1.0
        venue_index[m][v]=idx
        venue_rows.append({'model':m,'venue':v,'train_races':n,'hits':h,'raw_rate':round(h/n if n else 0,5),'smoothed_rate':round(sr,5),'venue_index':round(idx,3)})

with open('venue_model_index_v22.csv','w',newline='',encoding='utf-8-sig') as f:
    w=csv.DictWriter(f,fieldnames=['model','venue','train_races','hits','raw_rate','smoothed_rate','venue_index']);w.writeheader();w.writerows(venue_rows)

with open('races_v20.csv',encoding='utf-8-sig') as f: r20=list(csv.DictReader(f))
for r in r20:r['venue_index']=venue_index.get(r['model'],{}).get(str(r.get('venue','')).zfill(2),1.0)

with open('races_v18.csv',encoding='utf-8-sig') as f: r18=[r for r in csv.DictReader(f) if r.get('model')=='5頭展開']
for r in r18:r['venue_index']=venue_index['5頭展開'].get(str(r.get('venue','')).zfill(2),1.0)
pre=[r for r in r18 if DEV_START<=date.fromisoformat(r['date'])<=DEV_END]
key='5選手力' if pre and '5選手力' in pre[0] else '5取り切り力'

def fv(r,k):
    try:return float(r.get(k,''))
    except:return None

def summary(rs):
    n=len(rs); hh=sum(int(r.get('head_hit') or 0) for r in rs); bh=sum(int(r.get('bet_hit') or 0) for r in rs); ret=sum(int(float(r.get('return') or 0)) for r in rs); stake=n*5000
    return n,hh,(100*hh/n if n else 0),bh,(100*bh/n if n else 0),ret,(100*ret/stake if stake else 0)

cases=[
 ('5選手力>=0.70',lambda r:(fv(r,key) or 0)>=.70),
 ('>=0.70 + 場指数>=0.95',lambda r:(fv(r,key) or 0)>=.70 and r['venue_index']>=.95),
 ('>=0.70 + 場指数>=1.00',lambda r:(fv(r,key) or 0)>=.70 and r['venue_index']>=1.00),
 ('>=0.70 + 場指数>=1.05',lambda r:(fv(r,key) or 0)>=.70 and r['venue_index']>=1.05),
 ('>=0.65 + 場指数>=1.05',lambda r:(fv(r,key) or 0)>=.65 and r['venue_index']>=1.05),
]

L=['# v22 場別適性補正 分析','',
   f'場適性は学習期間 {TRAIN_START}〜{TRAIN_END} の全レースからモデル別に算出。',
   f'各場の発生率は全場平均へ alpha={ALPHA:.0f} で縮約し、場指数=縮約後発生率/全場発生率。1.00が平均。',
   '場は必須条件ではなく補助補正として扱う。以下の閾値比較は探索用であり、新規期間で再検証が必要。','']
for m in MODELS:
    L += [f'## {m} 場指数 上位/下位','|場|学習R|成立|生率|縮約率|場指数|','|---|---:|---:|---:|---:|---:|']
    z=[x for x in venue_rows if x['model']==m]
    z=sorted(z,key=lambda x:x['venue_index'],reverse=True)
    show=z[:5]+z[-5:]
    for x in show:L.append(f"|{x['venue']}|{x['train_races']}|{x['hits']}|{x['raw_rate']*100:.1f}%|{x['smoothed_rate']*100:.1f}%|{x['venue_index']:.3f}|")
    L.append('')

L += ['## 5頭モデル 別期間診断（8/3〜8/26）','',f'使用特徴列: `{key}`','|条件|R|5頭|頭率|3連単的中|的中率|払戻|回収率|','|---|---:|---:|---:|---:|---:|---:|---:|']
for name,fn in cases:
    rs=[r for r in pre if fn(r)]; n,hh,hp,bh,bp,ret,roi=summary(rs);L.append(f'|{name}|{n}|{hh}|{hp:.1f}%|{bh}|{bp:.1f}%|{ret:,}円|{roi:.1f}%|')

L += ['','## v20週 5頭候補の場指数別（記述のみ）','|場指数帯|R|頭|頭率|的中|回収率|','|---|---:|---:|---:|---:|---:|']
for label,lo,hi in [('低 <0.95',-9,.95),('中 0.95-1.05',.95,1.05),('高 >=1.05',1.05,99)]:
    rs=[r for r in r20 if r.get('model')=='5頭展開' and lo<=r['venue_index']<hi]; n,hh,hp,bh,bp,ret,roi=summary(rs);L.append(f'|{label}|{n}|{hh}|{hp:.1f}%|{bh}|{roi:.1f}%|')

open('analysis_v22_venue.md','w',encoding='utf-8').write('\n'.join(L)+'\n')
