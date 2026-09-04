"""v92: diagnose why 4-corner CORR20 improves head rate but not A+ ROI.
Uses frozen v91 scores/outcomes only; no score fitting or new prediction feature.
"""
import csv
from statistics import mean, median

SRC='analysis_v91_st_weight_walkforward.csv'
OUT='summary_v92_4corner_corr20_payout_shift.md'
A=55.0
S=67.0


def ff(x,d=None):
    try:
        if x is None or str(x).strip()=='': return d
        return float(x)
    except Exception:return d

def ii(x,d=0):
    try:return int(float(x))
    except Exception:return d

def pct(n,d):return 100*n/d if d else 0.0

def read():
    with open(SRC,encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def stats(q):
    q=[r for r in q if ii(r.get('valid_result'))==1 and ii(r.get('entry_gate_keep'))==1]
    n=len(q); h=[r for r in q if ii(r.get('head_hit'))==1]
    hp=[ii(r.get('payout100')) for r in h if ii(r.get('valid_payout'))==1 and ii(r.get('payout100'))>0]
    qp=[r for r in q if ii(r.get('valid_payout'))==1]
    ret=sum(ii(r.get('payout100')) for r in qp if ii(r.get('ticket20_hit'))==1)
    inv=2000*len(qp)
    return {
      'n':n,'head':len(h),'hr':pct(len(h),n),'pay_n':len(hp),
      'avg':mean(hp) if hp else 0,'med':median(hp) if hp else 0,
      'p10k':pct(sum(v>=10000 for v in hp),len(hp)) if hp else 0,
      'p20k':pct(sum(v>=20000 for v in hp),len(hp)) if hp else 0,
      'max':max(hp) if hp else 0,'roi':pct(ret,inv),'return':ret,'invest':inv,
      'tail10_share':pct(sum(v for v in hp if v>=10000),sum(hp)) if hp and sum(hp) else 0,
    }

def fmt(s):
    return f"{s['n']}R / 頭{s['head']} ({s['hr']:.1f}%) / 頭的中時平均 {s['avg']:.0f}円 / 中央値 {s['med']:.0f}円 / 1万円以上 {s['p10k']:.1f}% / ROI {s['roi']:.1f}%"

def selected(r,field,cut):return ff(r.get(field),-999)>=cut

def main():
    rs=[r for r in read() if r.get('model')=='4カドまくり' and ii(r.get('entry_gate_keep'))==1 and ii(r.get('valid_result'))==1]
    L=['# v92 4カド CORR20 配当構造分析','',
       '対象: v91で凍結済みの4カド候補。予測ロジックは一切変更せず、BASEとCORR20の選別後に結果・配当を比較する診断。','']
    L+=['## BASE vs CORR20','',
        '|期間|評価|BASE|CORR20|平均3連単差|中央値差|ROI差|','|---|---|---|---|---:|---:|---:|']
    for per in ('prior7','recent3','10mo'):
        q=rs if per=='10mo' else [r for r in rs if r.get('period_v91')==per]
        for label,cut in (('A+',A),('S+',S)):
            b=stats([r for r in q if selected(r,'score_BASE_v91',cut)])
            c=stats([r for r in q if selected(r,'score_CORR20_v91',cut)])
            L.append(f"|{per}|{label}|{fmt(b)}|{fmt(c)}|{c['avg']-b['avg']:+.0f}円|{c['med']-b['med']:+.0f}円|{c['roi']-b['roi']:+.1f}pt|")
    L+=['','## 閾値を跨いだレースの配当構造','',
        '|評価|区分|R|頭率|頭的中時平均3連単|中央値|1万円以上|2万円以上|最大|20点ROI|','|---|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for label,cut in (('A+',A),('S+',S)):
        common=[r for r in rs if selected(r,'score_BASE_v91',cut) and selected(r,'score_CORR20_v91',cut)]
        prom=[r for r in rs if not selected(r,'score_BASE_v91',cut) and selected(r,'score_CORR20_v91',cut)]
        dem=[r for r in rs if selected(r,'score_BASE_v91',cut) and not selected(r,'score_CORR20_v91',cut)]
        for name,q in (('共通',common),('CORR20で昇格',prom),('CORR20で降格',dem)):
            s=stats(q)
            L.append(f"|{label}|{name}|{s['n']}|{s['hr']:.1f}%|{s['avg']:.0f}円|{s['med']:.0f}円|{s['p10k']:.1f}%|{s['p20k']:.1f}%|{s['max']:.0f}円|{s['roi']:.1f}%|")
    L+=['','## 高配当への依存','',
        '|評価/選別|頭的中配当のうち1万円以上が占める金額比率|','|---|---:|']
    for label,cut in (('A+',A),('S+',S)):
        for name,field in (('BASE','score_BASE_v91'),('CORR20','score_CORR20_v91')):
            s=stats([r for r in rs if selected(r,field,cut)])
            L.append(f"|{label} {name}|{s['tail10_share']:.1f}%|")
    with open(OUT,'w',encoding='utf-8') as f:f.write('\n'.join(L)+'\n')
    print('\n'.join(L))
if __name__=='__main__':main()
