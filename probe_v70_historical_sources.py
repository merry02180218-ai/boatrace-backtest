from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import re

URLS = [
    ('waku_20260601', 'https://race.boatcast.jp/hp_txt/09/bc_j_waku10_20260601_09_01.txt'),
    ('waku_20260501', 'https://race.boatcast.jp/hp_txt/01/bc_j_waku10_20260501_01_01.txt'),
    ('waku_20251101', 'https://race.boatcast.jp/hp_txt/01/bc_j_waku10_20251101_01_01.txt'),
    ('od3_20260627', 'https://race.boatcast.jp/txt/13/bc_smt_od3_20260627_13_12.txt'),
    ('od3_20260401', 'https://race.boatcast.jp/txt/18/bc_smt_od3_20260401_18_01.txt'),
    ('ai_overlap', 'https://boatrace-ai.app/races/2026-07-22/24/3'),
    ('ai_old', 'https://boatrace-ai.app/races/2026-04-01/18/1'),
]

def fetch(url):
    req=Request(url, headers={'User-Agent':'Mozilla/5.0'})
    try:
        with urlopen(req, timeout=25) as r:
            body=r.read().decode('utf-8','replace')
            return r.status, body
    except HTTPError as e:
        try: body=e.read().decode('utf-8','replace')
        except Exception: body=''
        return e.code, body
    except URLError as e:
        return 'URLERR', str(e)

for name,url in URLS:
    status,body=fetch(url)
    print('\n###',name,status,'len',len(body))
    print('prefix=',repr(body[:180]))
    if 'boatrace-ai.app' in url:
        times=re.findall(r'20\d\d-\d\d-\d\d[ T]\d\d:\d\d',body)
        print('times=',times[:10])
        for token in ['オッズ','odds','trifecta','3連単','updatedAt']:
            i=body.find(token)
            print(token,'idx',i, repr(body[max(0,i-120):i+500]) if i>=0 else '')
