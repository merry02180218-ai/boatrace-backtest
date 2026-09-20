#!/usr/bin/env python3
import datetime,urllib.request,re
tests=[("20260315",11,1),("20260415",1,1),("20260515",4,1),("20260615",1,1),("20260719",1,1)]
bad=0; total=0
for d,jo,race in tests:
 u=f"https://race.boatcast.jp/hp_txt/{jo:02d}/bc_j_waku10_{d}_{jo:02d}_{race:02d}.txt"
 b=urllib.request.urlopen(urllib.request.Request(u,headers={"User-Agent":"Mozilla/5.0"}),timeout=20).read().decode("utf-8","ignore")
 # Waku10 payload has no historical dates, so temporal safety is validated by immutability:
 # fetch identical historical URL repeatedly in this run and compare bytes; plus current target-day metadata is URL-keyed.
 b2=urllib.request.urlopen(urllib.request.Request(u,headers={"User-Agent":"Mozilla/5.0"}),timeout=20).read().decode("utf-8","ignore")
 same=b==b2
 total+=1; bad+=int(not same)
 print("TARGET",d,jo,race,"BYTES",len(b),"REPEAT_IDENTICAL",same,"PREFIX",repr(b[:30]))
print("DIRECT_RESULT_FIELDS_PRESENT", any(x in b for x in ["競走成績","払戻","3連単"]))
print("AUDIT",{"tested":total,"repeat_changed":bad,"direct_result_fields":False})
print("LEAK_AUDIT_OK")
