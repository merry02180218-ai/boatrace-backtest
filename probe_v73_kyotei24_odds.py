from __future__ import annotations
import csv, io, re, urllib.request
from html.parser import HTMLParser

RAW='https://raw.githubusercontent.com/BoatraceCSV/boatracecsv.github.io/main/'
PAGES=[
 ('new','https://odds.kyotei24.jp/odds3t-omura-20260901-6.html'),
 ('old','https://odds.kyotei24.jp/od3t-omura-20260901-6.html'),
]
CODE='202609012406'

class Text(HTMLParser):
    def __init__(self): super().__init__(); self.a=[]
    def handle_data(self,d):
        s=' '.join(d.split())
        if s:self.a.append(s)

def get(url):
    req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req,timeout=30) as r:return r.status,r.read().decode('utf-8','replace')
    except Exception as e:return 0,str(e)

st,s=get(RAW+'data/previews/od3/2026/09/01.csv')
rows=list(csv.DictReader(io.StringIO(s))) if st==200 else []
r=next((x for x in rows if x.get('レースコード')==CODE),None)
print('official_row?',bool(r), 'cutoff',r.get('締切時刻') if r else '', 'acquired',r.get('取得日時') if r else '')
if r:
    sample=['1-2-3','1-4-5','1-5-4','5-1-4','4-1-5','3-1-2']
    print('official samples',{c:r.get('3連単_'+c) for c in sample})

for name,url in PAGES:
    st,b=get(url)
    print('\n##',name,'status',st,'len',len(b))
    print('contains deadline label', '締切時オッズ' in b)
    for tok in ['1-4-5','8.5','1-5-4','9.7','締切時オッズ','以前の人気順オッズ']:
        i=b.find(tok); print(tok,i,repr(b[max(0,i-200):i+500]) if i>=0 else '')
    p=Text(); p.feed(b); text=' | '.join(p.a)
    print('text_prefix',repr(text[:2000]))
    for tok in ['1-4-5','1-5-4','5-1-4','4-1-5']:
        i=text.find(tok); print('TXT',tok,i,repr(text[max(0,i-150):i+300]) if i>=0 else '')
