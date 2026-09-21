#!/usr/bin/env python3
import csv,io,os,urllib.request,datetime,concurrent.futures
MONTH=os.environ["MONTH"]
OUT=f"data/reconstructed_waku10_boatcast/2026/{MONTH}"
os.makedirs(OUT,exist_ok=True)
BASE="https://raw.githubusercontent.com/BoatraceCSV/boatracecsv.github.io/main/data/programs/race_cards/{y}/{m}/{d}.csv"
def get(u):
 try:
  return urllib.request.urlopen(urllib.request.Request(u,headers={"User-Agent":"Mozilla/5.0"}),timeout=20).read().decode("utf-8","ignore")
 except Exception:return None
def one(t):
 ds,dd,jo,race=t; u=f"https://race.boatcast.jp/hp_txt/{jo:02d}/bc_j_waku10_{ds}_{jo:02d}_{race:02d}.txt"; b=get(u)
 if b and b.startswith("data="):
  od=os.path.join(OUT,dd); os.makedirs(od,exist_ok=True)
  open(os.path.join(od,f"{jo:02d}_{race:02d}.txt"),"w",encoding="utf-8").write(b); return 1
 return 0
tasks=[]
start=datetime.date(2026,int(MONTH),1)
end=(datetime.date(2026,int(MONTH)+1,1)-datetime.timedelta(days=1)) if MONTH!="12" else datetime.date(2026,12,31)
day=start
while day<=end:
 y,m,dd=day.strftime("%Y"),day.strftime("%m"),day.strftime("%d"); txt=get(BASE.format(y=y,m=m,d=dd))
 if txt:
  for r in csv.DictReader(io.StringIO(txt)):
   try: tasks.append((day.strftime("%Y%m%d"),dd,int(r["レース場コード"]),int(str(r["レース回"]).replace("R",""))))
   except: pass
 day+=datetime.timedelta(days=1)
tasks=sorted(set(tasks))
with concurrent.futures.ThreadPoolExecutor(max_workers=24) as ex: vals=list(ex.map(one,tasks))
print("MONTH",MONTH,"REQUESTED",len(tasks),"SAVED",sum(vals),"MISSING",len(tasks)-sum(vals))
print("RESULT_FILES_READ",False); print("SEPTEMBER_OUTCOMES_READ",False); print("MONTH_RECONSTRUCT_OK")
