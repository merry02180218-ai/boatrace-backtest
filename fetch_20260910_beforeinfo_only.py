#!/usr/bin/env python3
import requests,re
from bs4 import BeautifulSoup

TARGETS=[('児島',16,5),('鳴門',14,7)]
UA={'User-Agent':'Mozilla/5.0'}

def clean(s): return ' '.join(str(s).split())

def parse(name,jcd,rno):
    url=f'https://www.boatrace.jp/owpc/pc/race/beforeinfo?hd=20260910&jcd={jcd:02d}&rno={rno}'
    r=requests.get(url,headers=UA,timeout=20)
    print('URL',url,'STATUS',r.status_code,'LEN',len(r.text))
    r.raise_for_status()
    soup=BeautifulSoup(r.text,'html.parser')
    # Never follow links. Parse only this beforeinfo response body.
    text=clean(soup.get_text(' ',strip=True))
    print('TEXT_HEAD',text[:1200])
    # dump table rows so exhibition data can be audited without result page access
    for ti,t in enumerate(soup.find_all('table')):
        print(f'--- {name}{rno}R TABLE {ti} ---')
        for tr in t.find_all('tr'):
            cells=[clean(x.get_text(' ',strip=True)) for x in tr.find_all(['th','td'])]
            if cells: print(' | '.join(cells))

def main():
    for x in TARGETS: parse(*x)
if __name__=='__main__': main()
