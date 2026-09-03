from urllib.request import Request, urlopen
from urllib.error import HTTPError
import re, json

PAGE='https://boatrace-ai.app/races/2026-04-01/18/1'

def get(url,headers=None):
    h={'User-Agent':'Mozilla/5.0','Accept':'*/*'}
    if headers:h.update(headers)
    req=Request(url,headers=h)
    try:
        with urlopen(req,timeout=30) as r:return r.status,r.read().decode('utf-8','replace'),dict(r.headers)
    except HTTPError as e:return e.code,e.read().decode('utf-8','replace'),dict(e.headers)

st,html,_=get(PAGE,{'Accept':'text/html'})
srcs=re.findall(r'<script[^>]+src="([^"]+)"',html)
blob=''
for src in srcs:
    if '.js' not in src:continue
    st,j,_=get('https://boatrace-ai.app'+src if src.startswith('/') else src)
    if st==200: blob+='\n'+j
urls=re.findall(r'https://[a-z0-9]+\.supabase\.co',blob,re.I)
project=urls[0] if urls else ''
# Public anon JWT is intentionally embedded in browser code. Do not print it.
jwts=re.findall(r'eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+',blob)
key=max(jwts,key=len) if jwts else ''
print('project_found',bool(project),project)
print('public_anon_key_found',bool(key),'length',len(key))
if not project or not key: raise SystemExit(0)
headers={'apikey':key,'Authorization':'Bearer '+key,'Accept':'application/openapi+json'}
st,b,h=get(project+'/rest/v1/',headers)
print('openapi',st,'len',len(b),'ct',h.get('Content-Type'))
try:
    doc=json.loads(b)
except Exception:
    print('openapi_prefix',repr(b[:1000])); raise SystemExit(0)
paths=list(doc.get('paths',{}))
tables=sorted({p.strip('/').split('?')[0] for p in paths if p.startswith('/') and p.count('/')==1})
print('table_count',len(tables))
print('interesting_tables',[t for t in tables if any(x in t.lower() for x in ['race','odd','preview','stadium','entry','result'])])
# Print schemas/columns for interesting tables only.
def schema_cols(t):
    defs=doc.get('definitions',{}) or doc.get('components',{}).get('schemas',{})
    z=defs.get(t,{})
    return list((z.get('properties') or {}).keys())
for t in tables:
    if any(x in t.lower() for x in ['race','odd','preview']):
        print('TABLE',t,'cols',schema_cols(t))

# Query likely historical odds tables with a narrow date/race filter if columns exist.
for t in tables:
    if 'odd' not in t.lower():continue
    cols=schema_cols(t)
    qs=['select=*','limit=3']
    # choose known date/race field names without assuming exact schema
    for c in ['race_date','date']:
        if c in cols: qs.append(f'{c}=eq.2026-04-01')
    for c in ['stadium_number','stadium_no','stadium_code','place_no']:
        if c in cols: qs.append(f'{c}=eq.18')
    for c in ['race_number','race_no']:
        if c in cols: qs.append(f'{c}=eq.1')
    url=project+'/rest/v1/'+t+'?'+('&'.join(qs))
    st,b,_=get(url,{'apikey':key,'Authorization':'Bearer '+key,'Accept':'application/json'})
    print('QUERY',t,'status',st,'len',len(b),'prefix',repr(b[:1200]))
