import csv, re, urllib.request, urllib.error

SRC='analysis_v83_wind_entry_gate.csv'
SLUG={
'01':'kiryu','02':'toda','03':'edogawa','04':'heiwajima','05':'tamagawa','06':'hamanako',
'07':'gamagori','08':'tokoname','09':'tsu','10':'mikuni','11':'biwako','12':'suminoe',
'13':'amagasaki','14':'naruto','15':'marugame','16':'kojima','17':'miyajima','18':'tokuyama',
'19':'shimonoseki','20':'wakamatsu','21':'ashiya','22':'fukuoka','23':'karatsu','24':'omura'}
PAT=re.compile(r'<div id="dm-(\d+)"[^>]*>\s*([1-6]-[1-6]-[1-6])\s*</div>.*?<div id="od-\1"[^>]*>\s*([^<]+?)\s*</div>',re.S)

def ff(x,d=-999):
    try:return float(x)
    except:return d

def fetch(code):
    code=str(code).strip()
    ds=code[:8]; jj=code[8:10]; rn=int(code[10:12]); slug=SLUG[jj]
    url=f'https://odds.kyotei24.jp/odds3t-{slug}-{ds}-{rn}.html'
    req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req,timeout=20) as r:b=r.read().decode('utf-8','replace')
    except Exception as e:return url,0,False,str(e)
    vals={}
    for _,t,v in PAT.findall(b):
        try: vals[t]=float(v.replace(',','').strip())
        except: pass
    return url,len(vals),'締切時オッズ' in b,''

with open(SRC,encoding='utf-8-sig',newline='') as f: rows=list(csv.DictReader(f))
print('fields',list(rows[0].keys()) if rows else [])
selected={}
for r in rows:
    code=(r.get('race_code') or r.get('レースコード') or '').strip()
    if len(code)<12: continue
    if not ('20251101'<=code[:8]<='20260831'):continue
    if ff(r.get('score'))<55:continue
    if str(r.get('entry_gate_keep','1')).strip() not in ('1','1.0'):continue
    jj=code[8:10]
    selected.setdefault(jj,code)
print('venues',len(selected),selected)
for jj in sorted(selected):
    code=selected[jj]
    url,n,label,err=fetch(code)
    print(jj,code,'parsed',n,'label',label,'err',err,'url',url)
