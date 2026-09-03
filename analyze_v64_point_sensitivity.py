import csv
from collections import defaultdict

def tickets(head, ranked, p):
    if p==20:return [f'{head}-{a}-{b}' for a in ranked for b in ranked if b!=a]
    sec=ranked[:2];k={4:3,6:4,8:5}[p];third=ranked[:k]
    return [f'{head}-{a}-{b}' for a in sec for b in third if b!=a]

def load():
    with open('analysis_v64_three_month_strict_flow.csv',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def b(x):return int(float(x or 0))
def stat(rs,p,grade):
    q=[]
    for r in rs:
        if b(r['head']) not in (3,5):continue
        if grade=='A' and not b(r['approved_A']):continue
        if grade=='S' and not b(r['approved_S']):continue
        q.append(r)
    inv=ret=hit=headhit=0
    for r in q:
        h=b(r['head']);ranked=[int(x) for x in r['ranked_others'].split('-') if x];ts=tickets(h,ranked,p);inv+=len(ts)*100
        actual=r['actual_combo'];pay=b(r['payout100']);headhit+=b(r['head_hit'])
        if actual in ts:hit+=1;ret+=pay
    n=len(q);return n,headhit,100*headhit/n if n else 0,hit,100*hit/n if n else 0,inv,ret,100*ret/inv if inv else 0

def main():
    rows=load();L=['# v64 点数・A/S感度診断','','v64で既に固定済みの頭・相手順位を変えず、結果確認後に4/6/8/20点ならどうだったかを再集計する診断。予測や順位の再学習はしない。','','## 全期間 3頭+5頭','|評価|点数|R|頭率|3連単的中率|投資|払戻|ROI|','|---|---:|---:|---:|---:|---:|---:|---:|']
    for g in ['A','S']:
        for p in [4,6,8,20]:
            n,hh,hr,hit,hitr,inv,ret,roi=stat(rows,p,g);L.append(f'|{g}以上|{p}|{n}|{hr:.1f}%|{hitr:.1f}%|{inv:,}円|{ret:,}円|{roi:.1f}%|')
    L+=['','## 月別 S評価','|月|点数|R|頭率|的中率|ROI|','|---|---:|---:|---:|---:|---:|']
    for month in ['2026-06','2026-07','2026-08','2026-09']:
        rr=[r for r in rows if r['date'].startswith(month)]
        for p in [4,6,8,20]:
            n,hh,hr,hit,hitr,inv,ret,roi=stat(rr,p,'S');L.append(f'|{month}|{p}|{n}|{hr:.1f}%|{hitr:.1f}%|{roi:.1f}%|')
    L+=['','## 頭別 S評価 6点','|頭|R|頭率|6点的中率|ROI|','|---:|---:|---:|---:|---:|']
    for h in [3,5]:
        rr=[r for r in rows if b(r['head'])==h];n,hh,hr,hit,hitr,inv,ret,roi=stat(rr,6,'S');L.append(f'|{h}|{n}|{hr:.1f}%|{hitr:.1f}%|{roi:.1f}%|')
    open('summary_v64_point_sensitivity.md','w',encoding='utf-8').write('\n'.join(L)+'\n')
if __name__=='__main__':main()
