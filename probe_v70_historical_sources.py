from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import re, html as htmlmod

URLS = [
    ('waku_20260601', 'https://race.boatcast.jp/hp_txt/09/bc_j_waku10_20260601_09_01.txt'),
    ('waku_20250503', 'https://race.boatcast.jp/hp_txt/01/bc_j_waku10_20250503_01_01.txt'),
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
        srcs=re.findall(r'<script[^>]+src="([^"]+)"',body)
        print('script_srcs=',srcs[:30])
        print('next_data?', '__NEXT_DATA__' in body, 'flight?', 'self.__next_f.push' in body)
        clean=htmlmod.unescape(body)
        for token in ['/api/','supabase','odds','raceId','race_id','trifecta','oddsUpdatedAt','updatedAt','fetch(']:
            hits=[m.start() for m in re.finditer(re.escape(token),clean,re.I)]
            print(token,'hits',hits[:10])
            if hits:
                i=hits[0]; print('snippet',repr(clean[max(0,i-250):i+800]))
        base='https://boatrace-ai.app'
        for src in srcs[:30]:
            clean_src=src.split('?',1)[0]
            if not clean_src.endswith('.js'): continue
            st,j=fetch(base+src if src.startswith('/') else src)
            if st!=200:
                print('CHUNK_FAIL',src,st); continue
            interesting=[]
            for tok in ['/api/','supabase','odds','races/','race-odds','trifecta','graphql','firebase','prisma','drizzle']:
                if tok.lower() in j.lower(): interesting.append(tok)
            if interesting:
                print('CHUNK',src,'len',len(j),'tokens',interesting)
                for tok in interesting:
                    pos=[m.start() for m in re.finditer(re.escape(tok),j,re.I)]
                    for i in pos[:3]: print(tok,repr(j[max(0,i-450):i+1400]))
