#!/usr/bin/env python3
import urllib.request
for d in ["20260315","20260415","20260515","20260615","20260719"]:
 print("DATE",d)
 for jo in [1,4,11,24]:
  u=f"https://race.boatcast.jp/hp_txt/{jo:02d}/bc_j_waku10_{d}_{jo:02d}_01.txt"
  try:
   r=urllib.request.urlopen(urllib.request.Request(u,headers={"User-Agent":"Mozilla/5.0"}),timeout=20)
   b=r.read().decode("utf-8","ignore")
   print(jo,r.status,len(b),repr(b[:60]))
  except Exception as e: print(jo,"ERR",repr(e))
print("BOATCAST_HIST_PROBE_OK")
