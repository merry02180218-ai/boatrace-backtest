"""v119: Analyze frozen v118 Sep-01..04 replay by p109 probability bands.
No refit/tuning. Reads only already-frozen replay_v118 output.
"""
import csv
from collections import defaultdict
SRC='replay_v118_20260901_04_1head.csv'
OUT='summary_v119_1head_s_probability_bands.md'

def read_csv(path):
    with open(path,encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def ff(x):return float(x)
def ii(x):return int(float(x))
def pct(n,d):return 100*n/d if d else 0.0

def band(p):
    if p < .72:return None
    if p < .75:return '72-75%'
    if p < .80:return '75-80%'
    if p < .85:return '80-85%'
    return '85%+'

def metric(rs):
    n=len(rs);h=sum(ii(r['head_hit']) for r in rs);t=sum(ii(r['ticket7_hit']) for r in rs)
    hh=[r for r in rs if ii(r['head_hit'])==1]
    cov=sum(ii(r['ticket7_hit']) for r in hh)
    inv=sum(ii(r['invest7']) for r in rs);ret=sum(ii(r['return7']) for r in rs)
    mp=sum(ff(r['p109']) for r in rs)/n*100 if n else 0
    return n,h,pct(h,n),mp,pct(h,n)-mp,t,pct(t,n),pct(cov,len(hh)),inv,ret,pct(ret,inv)

def main():
    rs=read_csv(SRC); groups=defaultdict(list)
    for r in rs:
        b=band(ff(r['p109']))
        if b:groups[b].append(r)
    order=['72-75%','75-80%','80-85%','85%+']
    L=['# v119 1-head S probability-band validation','',
       '- Source: frozen v118 Sep-01..04 no-leak replay only.',
       '- v109/v110 are not refit or retuned here.',
       '- Bands are fixed in advance: 72-75, 75-80, 80-85, 85%+.', '',
       '|p109帯|R|①1着|頭率|平均p109|乖離|7点的中|7点的中率|頭的中時coverage|投資|払戻|ROI|',
       '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for b in order:
        n,h,hr,mp,gap,t,tr,cov,inv,ret,roi=metric(groups[b])
        L.append(f'|{b}|{n}|{h}|{hr:.1f}%|{mp:.1f}%|{gap:+.1f}pt|{t}|{tr:.1f}%|{cov:.1f}%|¥{inv:,}|¥{ret:,}|{roi:.1f}%|')
    L+=['','## By day and band','|日付|p109帯|R|頭率|7点的中率|ROI|','|---|---|---:|---:|---:|---:|']
    days=sorted(set(r['date'] for r in rs))
    for d in days:
        for b in order:
            z=[r for r in groups[b] if r['date']==d]
            n,h,hr,mp,gap,t,tr,cov,inv,ret,roi=metric(z)
            L.append(f'|{d}|{b}|{n}|{hr:.1f}%|{tr:.1f}%|{roi:.1f}%|')
    open(OUT,'w',encoding='utf-8').write('\n'.join(L)+'\n')
if __name__=='__main__':main()
