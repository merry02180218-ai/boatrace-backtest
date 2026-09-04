"""v104b: run v104 with a persistent, validated historical final-odds cache.

Fixes v104 timeout by:
- fetching only A+ 3HEAD / 4C races needed by v104, not every source row;
- reusing cache_v104_final_odds.csv on later runs;
- trying the historical closed-race URL as a fallback;
- validating fetched odds against the actual 100-yen trifecta payout when available.

Ranking no-leak rule is unchanged: current-race final odds are evaluation labels only.
Price tendency for a race uses strictly earlier dates, exactly as v104.
"""
from __future__ import annotations

import csv
import html as htmlmod
import os
import re
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

import analyze_v104_role_value_hybrid as v104

CACHE='cache_v104_final_odds.csv'
A=55.0
END='2026-08-31'


def ff(x,d=0.0):
    try:
        if x is None or str(x).strip()=='': return d
        return float(x)
    except Exception: return d


def ii(x,d=0):
    try: return int(float(x))
    except Exception: return d


def load_cache():
    out={}
    if not os.path.exists(CACHE): return out
    with open(CACHE,encoding='utf-8-sig',newline='') as f:
        for r in csv.DictReader(f):
            c=(r.get('race_code') or '').strip(); t=(r.get('combo') or '').strip()
            try: o=float(r.get('odds') or 0)
            except Exception: o=0
            if c and t and o>1: out.setdefault(c,{})[t]=o
    return {c:d for c,d in out.items() if len(d)>=100}


def save_cache(fmap):
    with open(CACHE,'w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['race_code','combo','odds'])
        w.writeheader()
        for c in sorted(fmap):
            for t in sorted(fmap[c],key=lambda s:tuple(map(int,s.split('-')))):
                w.writerow({'race_code':c,'combo':t,'odds':fmap[c][t]})


def broad_parse(raw):
    # First use the parser that succeeded in v102/v103.
    d=v104.vo.parse_final(raw)
    if len(d)>=100: return d
    # Historical closed-race pages can use table cells rather than dm-/od- divs.
    text=htmlmod.unescape(re.sub(r'<[^>]+>',' ',raw)).replace('\xa0',' ')
    text=re.sub(r'\s+',' ',text)
    vals={}
    pats=[
        re.compile(r'(?<!\d)([1-6])\s*-\s*([1-6])\s*-\s*([1-6])\s*(?:\||:|：)?\s*([0-9]+(?:\.[0-9]+)?)'),
        re.compile(r'(?<!\d)([1-6])\s+([1-6])\s+([1-6])\s*(?:\||:|：)?\s*([0-9]+(?:\.[0-9]+)?)'),
    ]
    for pat in pats:
        for a,b,c,o in pat.findall(text):
            if len({a,b,c})<3: continue
            try: z=float(o)
            except Exception: continue
            if z>1: vals[f'{a}-{b}-{c}']=z
        if len(vals)>=100: break
    return vals


def truth_map(rows3,rows4):
    z={}
    for r in rows3+rows4:
        code=(r.get('race_code') or '').strip()
        w=ii(r.get('winner')); s=ii(r.get('second')); t=ii(r.get('third')); p=ii(r.get('payout100'))
        if len(code)>=12 and w and s and t and p>100:
            z[code]=(f'{w}-{s}-{t}',p/100.0)
    return z


def valid_against_payout(code,od,truth):
    if len(od)<100: return False
    q=truth.get(code)
    if not q: return True
    combo,expected=q
    got=od.get(combo)
    if got is None: return False
    # Final 3T odds and official 100-yen payout should match to one decimal.
    return abs(got-expected)<=0.11


def urls_for(code):
    date=code[:8]; jcd=code[8:10]; rn=int(code[10:12])
    u1=f'https://odds.kyotei24.jp/od-{date}-{jcd}-{rn}.html'
    u2=v104.vo.final_url(code)
    return [u for u in (u1,u2) if u]


def fetch_one(code,truth):
    err=''
    for url in urls_for(code):
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 (compatible; boatrace-backtest/1.1)'})
            with urllib.request.urlopen(req,timeout=8) as resp:
                raw=resp.read().decode('utf-8','replace')
            od=broad_parse(raw)
            if valid_against_payout(code,od,truth): return code,od,url,''
            err=f'invalid parsed={len(od)} url={url}'
        except Exception as e:
            err=f'{type(e).__name__}: {e} url={url}'
    return code,{},'',err


def selected_sources(rows3,rows4):
    q3=[r for r in rows3 if r.get('date','')<=END and v104.h3.elig(r) and ff(r.get('score'),-999)>=A]
    q4=[r for r in rows4 if r.get('date','')<=END and v104.c4.eligible(r) and ff(r.get('score_CORR20_v91'),-999)>=A]
    return q3,q4


def cached_fetch_odds(rows3,rows4):
    q3,q4=selected_sources(rows3,rows4)
    need=sorted({(r.get('race_code') or '').strip() for r in q3+q4 if len((r.get('race_code') or '').strip())>=12})
    truth=truth_map(rows3,rows4)
    fmap=load_cache()
    fmap={c:d for c,d in fmap.items() if c in set(need)}
    missing=[c for c in need if c not in fmap]
    print(f'v104b needed A+ odds={len(need)} cache={len(fmap)} missing={len(missing)}',flush=True)

    # Chunking gives fast failure if the provider is completely unavailable.
    for bi in range(0,len(missing),100):
        batch=missing[bi:bi+100]; gained=0; errors=[]
        with ThreadPoolExecutor(max_workers=16) as ex:
            futs={ex.submit(fetch_one,c,truth):c for c in batch}
            for fut in as_completed(futs):
                c,od,url,err=fut.result()
                if od:
                    fmap[c]=od; gained+=1
                elif len(errors)<5:
                    errors.append((c,err))
        save_cache(fmap)
        print(f'v104b odds {min(bi+len(batch),len(missing))}/{len(missing)} gained={gained} total={len(fmap)}',flush=True)
        if errors: print('sample errors:',errors,flush=True)
        if bi==0 and batch and gained==0:
            raise RuntimeError('No validated final odds were obtainable in first 100 requests; aborting early.')
    return fmap


# Monkey-patch only the transport/cache layer. v104 ranking/tuning logic remains unchanged.
v104.fetch_odds=cached_fetch_odds

if __name__=='__main__':
    v104.main()
