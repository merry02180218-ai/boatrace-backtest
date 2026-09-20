#!/usr/bin/env python3
import re, urllib.request
from urllib.parse import urljoin
url='https://kyoteibiyori.com/race_shusso.php?hiduke=20260728&place_no=9&race_no=3&slider=8'
h={'User-Agent':'Mozilla/5.0'}
html=urllib.request.urlopen(urllib.request.Request(url,headers=h),timeout=30).read().decode('utf-8','ignore')
print('PAGE_BYTES',len(html))
scripts=re.findall(r'<script[^>]+src=[\"\']([^\"\']+)',html,re.I)
print('SCRIPT_COUNT',len(scripts))
for s in scripts:
 u=urljoin(url,s)
 try: t=urllib.request.urlopen(urllib.request.Request(u,headers=h),timeout=30).read().decode('utf-8','ignore')
 except Exception as e: print('ERR',u,e); continue
 low=t.lower()
 if any(k in low for k in ['ajax','xmlhttprequest','fetch(','slider','race_shusso']):
  print('MATCH',u,'BYTES',len(t))
  for line in t.splitlines():
   if any(k in line.lower() for k in ['ajax','xmlhttprequest','fetch(','slider','race_shusso']):
    print(line[:1000])
print('PROBE_OK')
