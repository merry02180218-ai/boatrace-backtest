#!/usr/bin/env python3
import csv,io,os,time,urllib.request,datetime
OUT="data/reconstructed_waku10_boatcast"
os.makedirs(OUT,exist_ok=True)
# Use race-card daily files to enumerate only actually scheduled races; no result files are read.
BASE="https://raw.githubusercontent.com/BoatraceCSV/boatracecsv.github.io/main/data/programs/race_cards/{y}/{m}/{d}.csv"
def get(u):
 try:
  return urllib.request.urlopen(urllib.request.Request(u,headers={"User-Agent":"Mozilla/5.0"}),timeout=30).read().decode("utf-8","ignore")
 except Exception:return None
start=datetime.date(2026,3,1); end=datetime.date(2026,6,30); day=start
n=ok=0
while day<=end:
 ds=day.strftime("%Y%m%d"); y=day.strftime("%Y"); m=day.strftime("%m"); dd=day.strftime("%d")
 txt=get(BASE.format(y=y,m=m,d=dd))
 if txt:
  rows=list(csv.DictReader(io.StringIO(txt)))
  keys=sorted({(int(r["レース場コード"]),int(str(r["レース回"]).replace("R",""))) for r in rows})
  od=os.path.join(OUT,y,m,dd); os.makedirs(od,exist_ok=True)
  for jo,race in keys:
   n+=1; u=f"https://race.boatcast.jp/hp_txt/{jo:02d}/bc_j_waku10_{ds}_{jo:02d}_{race:02d}.txt"; b=get(u)
   if b and b.startswith("data="):
    open(os.path.join(od,f"{jo:02d}_{race:02d}.txt"),"w",encoding="utf-8").write(b); ok+=1
 print("DAY",day,"scheduled",len(keys) if txt else 0)
 day+=datetime.timedelta(days=1)
print("FETCH_SUMMARY",{"requested":n,"saved":ok,"missing":n-ok})
print("SEPTEMBER_OUTCOMES_READ",False)
print("RESULT_FILES_READ",False)
print("RECONSTRUCT_OK")
