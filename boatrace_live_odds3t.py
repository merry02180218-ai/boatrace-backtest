#!/usr/bin/env python3
"""Fetch current BOAT RACE official trifecta odds for one race.

Official page:
https://www.boatrace.jp/owpc/pc/race/odds3t?rno={rno}&jcd={jcd}&hd={yyyymmdd}

Parser follows the official table layout: the second div.table1, first tbody,
and td.oddsPoint in DOM order. ARRAY_3T is the official table order.
"""
from __future__ import annotations
from datetime import datetime, timezone, timedelta
import requests
from bs4 import BeautifulSoup

JST=timezone(timedelta(hours=9))
ARRAY_3T=[
123,213,312,412,512,612,124,214,314,413,513,613,125,215,315,415,514,614,126,216,316,416,516,615,
132,231,321,421,521,621,134,234,324,423,523,623,135,235,325,425,524,624,136,236,326,426,526,625,
142,241,341,431,531,631,143,243,342,432,532,632,145,245,345,435,534,634,146,246,346,436,536,635,
152,251,351,451,541,641,153,253,352,452,542,642,154,254,354,453,543,643,156,256,356,456,546,645,
162,261,361,461,561,651,163,263,362,462,562,652,164,264,364,463,563,653,165,265,365,465,564,654]

def fetch_odds3t(hd:str,jcd:str,rno:int,timeout:int=20):
    hd=str(hd).replace('-','').replace('/','');jcd=str(jcd).zfill(2);rno=int(rno)
    url=f'https://www.boatrace.jp/owpc/pc/race/odds3t?rno={rno}&jcd={jcd}&hd={hd}'
    headers={'User-Agent':'Mozilla/5.0 (compatible; boatrace-backtest-live/1.0)'}
    resp=requests.get(url,headers=headers,timeout=timeout)
    resp.raise_for_status()
    soup=BeautifulSoup(resp.text,'html.parser')
    tables=soup.find_all('div',class_='table1')
    if len(tables)<2: raise RuntimeError(f'official odds table not found: {url}')
    bodies=tables[1].find_all('tbody')
    if not bodies: raise RuntimeError(f'official odds tbody not found: {url}')
    vals=[]
    for tr in bodies[0].find_all('tr'):
        for td in tr.find_all('td',class_='oddsPoint'):
            s=td.get_text(strip=True).replace(',','')
            try: vals.append(float(s))
            except: vals.append(float('nan'))
    if len(vals)!=120:
        raise RuntimeError(f'expected 120 trifecta odds, got {len(vals)}: {url}')
    odds={f'{x//100}-{(x//10)%10}-{x%10}':v for x,v in zip(ARRAY_3T,vals)}
    good=sum(1 for v in odds.values() if v==v and v>0)
    if good<100: raise RuntimeError(f'only {good}/120 valid odds: {url}')
    return {'source':'boatrace_official_live','url':url,'fetched_at_jst':datetime.now(JST).isoformat(timespec='seconds'),'odds':odds}

if __name__=='__main__':
    import argparse,json
    p=argparse.ArgumentParser();p.add_argument('--date',required=True);p.add_argument('--jcd',required=True);p.add_argument('--race',type=int,required=True)
    a=p.parse_args();print(json.dumps(fetch_odds3t(a.date,a.jcd,a.race),ensure_ascii=False,indent=2))
