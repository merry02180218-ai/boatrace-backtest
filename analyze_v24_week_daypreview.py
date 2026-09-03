import csv
from collections import defaultdict
from analyze_v23_20260902_daypreview import f,rank_score,by_code,venue_map,preview_for
from backtest import rows

START='2026-08-27'; END='2026-09-02'

def main():
    with open('races_v20.csv',encoding='utf-8-sig') as fh: base=[r for r in csv.DictReader(fh) if START<=r.get('date','')<=END]
    vidx=venue_map(); cache={}; out=[]
    for r in base:
        d=r['date']; ymd=d.replace('-','/')
        if d not in cache:
            cache[d]=(by_code(f'data/previews/tkz/{ymd}.csv'),by_code(f'data/previews/stt/{ymd}.csv'),by_code(f'data/previews/original_exhibition/{ymd}.csv'))
        tkz,stt,orig=cache[d]; p=preview_for(r['model'],r['race_code'],r.get('venue',''),tkz,stt,orig,vidx)
        z=dict(r); z.update({k:(round(v,3) if isinstance(v,float) else v) for k,v in p.items()}); z['adjusted_score']=round((f(r.get('score')) or 0)+p['preview_adj'],2); out.append(z)
    with open('races_v24_week_daypreview.csv','w',newline='',encoding='utf-8-sig') as fh:
        w=csv.DictWriter(fh,fieldnames=sorted(set().union(*(r.keys() for r in out))));w.writeheader();w.writerows(out)
    L=['# v24 2026-08-27〜2026-09-02 1週間 当日展示補正検証（実進入なし）','', 'v23と同じ固定式。実進入・進入コースは完全除外。展示タイム、スタート展示タイム、オリジナル展示、v22場指数のみ。1R 5,000円換算。','', '## 全体/グレード別','|区分|R|狙い成立|成立率|3連単的中|的中率|払戻|回収率|','|---|---:|---:|---:|---:|---:|---:|---:|']
    def stat(label,rs):
        n=len(rs); hh=sum(int(x.get('head_hit') or 0) for x in rs); bh=sum(int(x.get('bet_hit') or 0) for x in rs); ret=sum(int(float(x.get('return') or 0)) for x in rs); roi=100*ret/(n*5000) if n else 0; L.append(f'|{label}|{n}|{hh}|{hh/n*100 if n else 0:.1f}%|{bh}|{bh/n*100 if n else 0:.1f}%|{ret:,}円|{roi:.1f}%|')
    stat('全候補',out)
    for g in ['S','A','B']:stat(g,[x for x in out if x['grade']==g])
    stat('S+A',[x for x in out if x['grade'] in ('S','A')])
    L+=['','## モデル別 S+A','|モデル|R|狙い成立|成立率|3連単的中|払戻|回収率|','|---|---:|---:|---:|---:|---:|---:|']
    for m in ['3まくり','3まくり差し','4カドまくり','5頭展開']:
        rs=[x for x in out if x['model']==m and x['grade'] in ('S','A')]; n=len(rs); hh=sum(int(x.get('head_hit') or 0) for x in rs); bh=sum(int(x.get('bet_hit') or 0) for x in rs); ret=sum(int(float(x.get('return') or 0)) for x in rs); roi=100*ret/(n*5000) if n else 0; L.append(f'|{m}|{n}|{hh}|{hh/n*100 if n else 0:.1f}%|{bh}|{ret:,}円|{roi:.1f}%|')
    L+=['','## 日別 S+A','|日付|R|狙い成立|3連単的中|払戻|回収率|','|---|---:|---:|---:|---:|---:|']
    for d in sorted(set(x['date'] for x in out)):
        rs=[x for x in out if x['date']==d and x['grade'] in ('S','A')];n=len(rs);hh=sum(int(x.get('head_hit') or 0) for x in rs);bh=sum(int(x.get('bet_hit') or 0) for x in rs);ret=sum(int(float(x.get('return') or 0)) for x in rs);roi=100*ret/(n*5000) if n else 0;L.append(f'|{d}|{n}|{hh}|{bh}|{ret:,}円|{roi:.1f}%|')
    open('analysis_v24_week_daypreview.md','w',encoding='utf-8').write('\n'.join(L)+'\n')
if __name__=='__main__':main()
