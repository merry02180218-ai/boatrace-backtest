import csv
from collections import defaultdict

PATH='analysis_v61_sensitivity.csv'
TARGETS=[(3,.30,1.10),(3,.30,1.20),(3,.30,1.30),(3,.40,1.10),(5,.50,1.20)]

def f(x):
    try:return float(x)
    except:return 0.0

def stat(rs):
    n=len(rs);hit=sum(int(float(r.get('ticket_hit') or 0)) for r in rs);inv=sum(int(float(r.get('invest') or 0)) for r in rs);ret=sum(int(float(r.get('return') or 0)) for r in rs);avg=sum(int(float(r.get('tickets_n') or 0)) for r in rs)/n if n else 0
    return n,hit,avg,inv,ret,100*ret/inv if inv else 0

def main():
    with open(PATH,encoding='utf-8-sig') as f0: rows=list(csv.DictReader(f0))
    L=['# v61 感度セル 前半/後半診断','','感度表で良かったセルを正式採用するためではなく、期間内の偏りを見る診断。','', '|頭|カバー|EV|期間|R|的中|平均点|ROI|','|---:|---:|---:|---|---:|---:|---:|---:|']
    for h,c,e in TARGETS:
        base=[r for r in rows if int(float(r['head']))==h and abs(f(r['cover_rule'])-c)<1e-9 and abs(f(r['ev_rule'])-e)<1e-9]
        for name,lo,hi in [('前半','2026-07-19','2026-08-10'),('後半','2026-08-11','2026-09-02')]:
            q=[r for r in base if lo<=r['date']<=hi];n,hit,avg,inv,ret,roi=stat(q);L.append(f'|{h}|{c*100:.0f}%|{e:.2f}|{name}|{n}|{hit}|{avg:.2f}|{roi:.1f}%|')
    open('summary_v61_split_diagnostics.md','w',encoding='utf-8').write('\n'.join(L)+'\n')
if __name__=='__main__':main()
