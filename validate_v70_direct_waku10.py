import csv, io, urllib.request
from historical_waku10_fetcher import fetch_day, HEAD

RAW='https://raw.githubusercontent.com/BoatraceCSV/boatracecsv.github.io/main/'

def get(path):
    try:
        req=urllib.request.Request(RAW+path,headers={'User-Agent':'Mozilla/5.0'})
        with urllib.request.urlopen(req,timeout=25) as r:return r.read().decode('utf-8-sig')
    except Exception:return ''

def norm(v):
    s=(v or '').strip()
    try:
        x=float(s)
        return ('%.8f'%x).rstrip('0').rstrip('.')
    except:return ' '.join(s.replace('\u3000',' ').split())

def main():
    ds='2026-07-20'; ymd='2026/07/20'
    got=fetch_day(ds,sleep=0.015)
    true=list(csv.DictReader(io.StringIO(get(f'data/programs/waku10/{ymd}.csv'))))
    tg={r['レースコード']:r for r in got}; tt={r['レースコード']:r for r in true}
    cmp=ok=0; mism=[]
    for code,r in tt.items():
        g=tg.get(code)
        if not g: continue
        for h in HEAD:
            cmp+=1
            if norm(g.get(h))==norm(r.get(h)): ok+=1
            elif len(mism)<20:mism.append((code,h,r.get(h),g.get(h)))
    historical=[]
    for d in ['2025-05-03','2025-11-01','2026-05-01','2026-06-01']:
        rows=fetch_day(d,sleep=0.01)
        historical.append((d,len(rows)))
    lines=['# v70 BOATCAST過去waku10 直接取得検証','',
           f'- 2026-07-20 overlap: published {len(true)} races / direct {len(got)} races',
           f'- field match: {ok}/{cmp} = {(100*ok/cmp if cmp else 0):.4f}%','',
           '## 過去日の直接取得件数']
    for d,n in historical:lines.append(f'- {d}: {n} races')
    lines += ['','## mismatch sample']
    for x in mism:lines.append(f'- {x}')
    adopt=(len(got)==len(true) and ok/max(cmp,1)>=.999 and all(n>0 for _,n in historical))
    lines += ['','## 判定',f'**{"採用可能" if adopt else "要追加確認"}**']
    open('summary_v70_direct_waku10.md','w',encoding='utf-8').write('\n'.join(lines)+'\n')
    print('\n'.join(lines))

if __name__=='__main__':main()
