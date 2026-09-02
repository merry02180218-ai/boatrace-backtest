import csv,io,urllib.request,statistics
BASE='https://raw.githubusercontent.com/BoatraceCSV/boatracecsv.github.io/main/'
TARGET=['202609020803','202609021203','202609021204','202609020809','202609021306']
# correct known examples from prior report are venue08 R03/R09, venue12 R04, venue13 R06, venue16 R03
TARGET=['202609020803','202609020809','202609021204','202609021306','202609021603']
def load(path):
    with urllib.request.urlopen(BASE+path,timeout=30) as r:
        return list(csv.DictReader(io.StringIO(r.read().decode('utf-8-sig'))))
od={r['レースコード']:r for r in load('data/previews/od3/2026/09/02.csv')}
pay={r['レースコード']:r for r in load('data/results/payouts/2026/09/02.csv')}
lines=['# 2026-09-02 実オッズ確認','', '|場|R|結果|締切前勝ち目オッズ|最終払戻/100円|確定換算オッズ|4頭レンジ|5頭レンジ|','|---|---:|---|---:|---:|---:|---|---|']
for code in TARGET:
    r=od.get(code,{}); p=pay.get(code,{})
    result=p.get('3連単_組番',''); payout=float(p.get('3連単_払戻金') or 0)
    pre=float(r.get('3連単_'+result) or 0) if result else 0
    vals4=[float(v) for k,v in r.items() if k.startswith('3連単_4-') and v not in ('',None) and float(v)>0]
    vals5=[float(v) for k,v in r.items() if k.startswith('3連単_5-') and v not in ('',None) and float(v)>0]
    def rng(a):
        return f'{min(a):.1f}〜{max(a):.1f} (中央値{statistics.median(a):.1f})' if a else '-'
    lines.append(f"|{r.get('レース場','')}|{r.get('レース回','')}|{result}|{pre:.1f}|{payout:.0f}円|{payout/100:.1f}倍|{rng(vals4)}|{rng(vals5)}|")
open('odds_0902.md','w',encoding='utf-8').write('\n'.join(lines)+'\n')
