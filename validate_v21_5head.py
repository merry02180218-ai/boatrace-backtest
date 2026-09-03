import csv
from datetime import date

# v21: freeze the exploratory v20 rule 5選手力>=0.60 and evaluate it on historical v18 races.
# IMPORTANT: 2026-08-27..09-02 was used to discover this threshold and is excluded from validation summaries.
IN='races_v18.csv'; OUT='validation_v21_5head.md'
DISC_START=date(2026,8,27); DISC_END=date(2026,9,2)

def d(s): return date.fromisoformat(s)
def f(r,k):
    try:return float(r.get(k,''))
    except:return None

def summarize(rs):
    n=len(rs); hh=sum(int(r.get('head_hit') or 0) for r in rs); bh=sum(int(r.get('bet_hit') or 0) for r in rs); ret=sum(int(float(r.get('return') or 0)) for r in rs); stake=n*5000
    return n,hh,hh/n*100 if n else 0,bh,bh/n*100 if n else 0,stake,ret,ret/stake*100 if stake else 0

with open(IN,encoding='utf-8-sig') as fh:
    allr=[r for r in csv.DictReader(fh) if r.get('model')=='5頭展開']

# v18 race output may use 5取り切り力 rather than 5選手力; both are the same strength-style candidate feature in v18.
key='5選手力' if allr and '5選手力' in allr[0] else '5取り切り力'
usable=[r for r in allr if f(r,key) is not None]
# untouched relative to the 8/27-9/2 threshold discovery
pre=[r for r in usable if d(r['date']) < DISC_START]
# fixed threshold
pre60=[r for r in pre if f(r,key)>=0.60]
pre65=[r for r in pre if f(r,key)>=0.65]
pre70=[r for r in pre if f(r,key)>=0.70]

L=['# v21 5頭 選手力>=0.60 固定・別期間検証','',
   'v20の2026-08-27〜2026-09-02で発見した `5選手力>=0.60` を固定し、その発見期間を除外して既存v18履歴で検証。',
   '0.65/0.70は感度確認のみで、採用基準は0.60。','',
   f'使用特徴列: `{key}`','',
   '|条件|R|頭|頭率|3連単的中|的中率|投資|払戻|回収率|','|---|---:|---:|---:|---:|---:|---:|---:|---:|']
for name,rs in [('基準（発見期間前）',pre),('固定 5選手力>=0.60',pre60),('参考 >=0.65',pre65),('参考 >=0.70',pre70)]:
    n,hh,hp,bh,bp,st,ret,roi=summarize(rs);L.append(f'|{name}|{n}|{hh}|{hp:.1f}%|{bh}|{bp:.1f}%|{st:,}円|{ret:,}円|{roi:.1f}%|')

# monthly-ish breakdown for fixed rule
L+=['','## 固定0.60 日別/期間確認','|期間|R|頭|頭率|的中|払戻|回収率|','|---|---:|---:|---:|---:|---:|---:|']
periods=[('8/3-8/9',date(2026,8,3),date(2026,8,9)),('8/10-8/16',date(2026,8,10),date(2026,8,16)),('8/17-8/23',date(2026,8,17),date(2026,8,23)),('8/24-8/26',date(2026,8,24),date(2026,8,26))]
for name,a,b in periods:
    rs=[r for r in pre60 if a<=d(r['date'])<=b];n,hh,hp,bh,bp,st,ret,roi=summarize(rs);L.append(f'|{name}|{n}|{hh}|{hp:.1f}%|{bh}|{ret:,}円|{roi:.1f}%|')
open(OUT,'w',encoding='utf-8').write('\n'.join(L)+'\n')
