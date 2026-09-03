from urllib.request import Request, urlopen
from urllib.error import HTTPError
import re, html

URL='https://boatrace-ai.app/races/2026-04-01/18/1'
UAS={
 'mozilla':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/140 Safari/537.36',
 'googlebot':'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
 'bingbot':'Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)',
 'facebook':'facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)',
}

def fetch(url,headers=None):
    h={'Accept':'text/html,application/xhtml+xml','Accept-Language':'ja,en;q=0.8'}
    if headers:h.update(headers)
    req=Request(url,headers=h)
    try:
        with urlopen(req,timeout=30) as r:return r.status,r.read().decode('utf-8','replace'),dict(r.headers)
    except HTTPError as e:return e.code,e.read().decode('utf-8','replace'),dict(e.headers)

for name,ua in UAS.items():
    st,b,h=fetch(URL,{'User-Agent':ua})
    print('\n##',name,st,'len',len(b),'ct',h.get('Content-Type'))
    for tok in ['徳山 1R','オッズ','16.5','2026-04-01 08:30','島川','trifecta','oddsType']:
        print(tok,b.find(tok))
    print('flight',b.find('self.__next_f.push'))
    for tok in ['16.5','島川']:
        i=b.find(tok)
        if i>=0:print('snippet',repr(html.unescape(b[max(0,i-500):i+1000])))

# Try RSC endpoint/header variants. Next versions often return React Flight with RSC:1.
for q in ['?_rsc=1','?_rsc=abc123','?__nextDefaultLocale=ja&_rsc=1']:
    st,b,h=fetch(URL+q,{'User-Agent':UAS['mozilla'],'RSC':'1','Accept':'text/x-component'})
    print('\n## rsc',q,st,'len',len(b),'ct',h.get('Content-Type'))
    for tok in ['徳山','16.5','島川','trifecta','oddsType','updatedAt']:
        print(tok,b.find(tok))
    print(repr(b[:1000]))

# Download page chunks and enumerate public endpoints/project URLs/table-like identifiers.
st,b,_=fetch(URL,{'User-Agent':UAS['mozilla']})
srcs=re.findall(r'<script[^>]+src="([^"]+)"',b)
for src in srcs:
    if '.js' not in src:continue
    full='https://boatrace-ai.app'+src if src.startswith('/') else src
    st,j,_=fetch(full,{'User-Agent':UAS['mozilla'],'Accept':'*/*'})
    if st!=200:continue
    urls=sorted(set(re.findall(r'https://[A-Za-z0-9._-]+(?:supabase\.(?:co|in|red)|[A-Za-z0-9._-]+)(?:/[A-Za-z0-9_./?=&%-]*)?',j)))
    if urls: print('\nCHUNK_URLS',src,urls[:30])
    for patt in ['createClient(','.from("','.from(\'','race_odds','raceOdds','odds_type','oddsType','preview_updated_at','updated_at']:
        poss=[m.start() for m in re.finditer(re.escape(patt),j,re.I)]
        if poss:
            print('\nCHUNK_MATCH',src,patt,'count',len(poss))
            for i in poss[:5]:print(repr(j[max(0,i-600):i+1600]))
