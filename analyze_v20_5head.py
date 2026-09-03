import csv
from statistics import mean

IN='races_v20.csv'; OUT='analysis_v20_5head.md'
rows=[]
with open(IN,encoding='utf-8-sig') as f:
    for r in csv.DictReader(f):
        if r.get('model')=='5頭展開': rows.append(r)

def fv(r,k):
    try:return float(r.get(k,''))
    except:return None

def avg(rs,k):
    v=[fv(r,k) for r in rs if fv(r,k) is not None]
    return mean(v) if v else 0

def stats(rs):
    n=len(rs);hh=sum(int(r['head_hit']) for r in rs);bh=sum(int(r['bet_hit']) for r in rs);ret=sum(int(float(r.get('return') or 0)) for r in rs);stake=n*5000
    return n,hh,hh/n*100 if n else 0,bh,bh/n*100 if n else 0,ret,ret/stake*100 if stake else 0

hits=[r for r in rows if int(r['head_hit'])==1];miss=[r for r in rows if int(r['head_hit'])==0]
features=['4攻撃力_非motor','1_2抵抗力','5選手力','score','composite_odds','tickets']
L=['# v20 5頭展開 当たり/外れ分析','',f'対象 {len(rows)}R / 頭成立 {len(hits)}R / 不成立 {len(miss)}R。','', '## 頭成立 vs 不成立 平均','|特徴|頭成立平均|不成立平均|差|','|---|---:|---:|---:|']
for k in features:
    a=avg(hits,k);b=avg(miss,k);L.append(f'|{k}|{a:.3f}|{b:.3f}|{a-b:+.3f}|')

# Single-feature threshold scans are descriptive only: thresholds are evaluated on this test week and are NOT unbiased backtests.
L+=['','## 参考: 今週データ上の単一条件別（探索用・未検証）','※以下は8/27〜9/2の結果を見て比較する探索分析。回収率100%超でも新しい期間で再検証が必要。','', '|条件|R|頭|頭率|3連単的中|的中率|払戻|回収率|','|---|---:|---:|---:|---:|---:|---:|---:|']
conds=[]
for k in ['4攻撃力_非motor','1_2抵抗力','5選手力']:
    for t in [0.55,0.60,0.65,0.70,0.75,0.80]:
        rs=[r for r in rows if fv(r,k) is not None and fv(r,k)>=t]
        if len(rs)>=5:conds.append((f'{k}>={t:.2f}',rs))
for t in [50,55,60,65,70]:
    rs=[r for r in rows if fv(r,'score') is not None and fv(r,'score')>=t]
    if len(rs)>=5:conds.append((f'score>={t}',rs))
ranked=[]
for name,rs in conds:
    s=stats(rs);ranked.append((s[-1],s[2],name,s))
for roi,hr,name,s in sorted(ranked,reverse=True)[:15]:
    n,hh,hp,bh,bp,ret,rv=s;L.append(f'|{name}|{n}|{hh}|{hp:.1f}%|{bh}|{bp:.1f}%|{ret:,}円|{rv:.1f}%|')

L+=['','## 頭成立6R','|日付|場|R|4攻撃|1・2抵抗|5選手力|score|3連単的中|払戻|','|---|---|---:|---:|---:|---:|---:|---:|---:|']
for r in hits:
    L.append(f"|{r['date']}|{r['venue']}|{r['race']}|{fv(r,'4攻撃力_非motor'):.3f}|{fv(r,'1_2抵抗力'):.3f}|{fv(r,'5選手力'):.3f}|{fv(r,'score'):.2f}|{r['bet_hit']}|{int(float(r.get('return') or 0)):,}円|")
open(OUT,'w',encoding='utf-8').write('\n'.join(L)+'\n')
