from __future__ import annotations
import csv, io, sys, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

BOATCAST='https://race.boatcast.jp/hp_txt'
RAW='https://raw.githubusercontent.com/BoatraceCSV/boatracecsv.github.io/main/'
FW={'１':'1','２':'2','３':'3','４':'4','５':'5','６':'6','７':'7','８':'8','９':'9','Ｆ':'F','Ｌ':'L'}
SUMMARY=['選手名','枠番別勝率','枠番別平均ST','枠番別平均スタート順']
RUN=['着順','進入','グレード']
HEAD=['レースコード','レース日','レース場コード','レース回']
for b in range(1,7):
    HEAD += [f'艇{b}_{x}' for x in SUMMARY]
    for k in range(1,11): HEAD += [f'艇{b}_過去{k}走_{x}' for x in RUN]

def get(url, timeout=12):
    req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req,timeout=timeout) as r:return r.read().decode('utf-8-sig')
    except Exception:return ''

def norm_name(s):
    return ' '.join((s or '').replace('\u3000',' ').split())

def parse_tsv(body, code, ds, jo, rno):
    ls=[x.rstrip('\r') for x in body.splitlines()]
    if len(ls)<3 or not ls[0].lstrip().startswith('data=') or not ls[1].startswith('1'):
        return None
    vals=[code,ds,jo,f'{int(rno):02d}R']
    boat_lines=ls[2:8]
    if len(boat_lines)<6:return None
    for ln in boat_lines:
        c=ln.split('\t')
        c += ['']*(34-len(c))
        vals += [norm_name(c[0]),c[1].strip(),c[2].strip(),c[3].strip()]
        for k in range(10):
            i=4+3*k
            fin=FW.get(c[i].strip(),c[i].strip())
            ent=c[i+1].strip(); grd=c[i+2].strip()
            vals += [fin,ent,grd]
    return dict(zip(HEAD,vals))

def fetch_day(ds, sleep=0.0, workers=16):
    y,m,d=ds.split('-'); ymd=f'{y}/{m}/{d}'
    card_url=RAW+f'data/programs/race_cards/{ymd}.csv'
    s=get(card_url)
    if not s:return []
    cards=list(csv.DictReader(io.StringIO(s)))
    codes=[]; seen=set()
    for r in cards:
        code=r.get('レースコード','')
        if code and code not in seen:
            seen.add(code); codes.append(code)
    def one(code):
        jo=code[8:10]; rno=code[10:12]
        url=f'{BOATCAST}/{jo}/bc_j_waku10_{y}{m}{d}_{jo}_{rno}.txt'
        return code,parse_tsv(get(url),code,ds,jo,rno)
    got={}
    with ThreadPoolExecutor(max_workers=workers) as ex:
        fs=[ex.submit(one,c) for c in codes]
        for fut in as_completed(fs):
            code,z=fut.result()
            if z:got[code]=z
    return [got[c] for c in codes if c in got]

def write_day(ds,path):
    rows=fetch_day(ds)
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=HEAD);w.writeheader();w.writerows(rows)
    return len(rows)

if __name__=='__main__':
    ds=sys.argv[1] if len(sys.argv)>1 else '2026-07-20'
    path=sys.argv[2] if len(sys.argv)>2 else f'w10_{ds}.csv'
    n=write_day(ds,path)
    print(ds,'rows',n,'->',path)
