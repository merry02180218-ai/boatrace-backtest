#!/usr/bin/env python3
import csv,io,json,urllib.parse,urllib.request
DATE="20260719"; CSVURL="https://raw.githubusercontent.com/BoatraceCSV/boatracecsv.github.io/main/data/programs/waku10/2026/07/19.csv"
EP="https://kyoteibiyori.com/request_race_shusso_detail_v4.php"
def get(u):
 req=urllib.request.Request(u,headers={"User-Agent":"Mozilla/5.0"})
 return urllib.request.urlopen(req,timeout=30).read().decode("utf-8","ignore")
rows=list(csv.DictReader(io.StringIO(get(CSVURL))))
targets=rows[:6]
ok=tot=0
for row in targets:
 place=int(row["レース場コード"]); race=int(row["レース回"].replace("R",""))
 p={"place_no":str(place),"race_no":str(race),"hiduke":DATE,"race_name":"","season":2026,"term":1,"kaisai_key":DATE+f"{place:02d}","taikai_count":"0","group_no":"0","type":0,"grade":0}
 body=urllib.parse.urlencode({"data":json.dumps(p,separators=(",",":"))}).encode()
 req=urllib.request.Request(EP,data=body,headers={"User-Agent":"Mozilla/5.0","Content-Type":"application/x-www-form-urlencoded","Referer":"https://kyoteibiyori.com/"})
 obj=json.loads(urllib.request.urlopen(req,timeout=30).read())
 race_list=obj["race_list"]; pk=obj["kako_list"]["player_kako10"]
 by_player_course={(int(x["player_no"]),int(x["course"])):x for x in pk}
 print("RACE",place,race)
 for lane,ent in enumerate(race_list,1):
  player=int(ent["player_no"]); x=by_player_course.get((player,lane))
  if not x: print(" MISS",lane,player); continue
  csv_ranks=[str(row.get(f"艇{lane}_過去{i}走_着順","")).strip() for i in range(1,11)]
  kb_ranks=[str(x.get(f"rank_{i:02d}","")).strip() for i in range(1,11)]
  csv_st=str(row.get(f"艇{lane}_枠番別平均ST","")).strip()
  kb_st=x.get("start_ave"); kb_st_s="" if kb_st is None else f"{float(kb_st)/100:.2f}"
  csv_sr=str(row.get(f"艇{lane}_枠番別平均スタート順","")).strip()
  kb_sr=x.get("st_junban_ave"); kb_sr_s="" if kb_sr is None else f"{float(kb_sr)/100:.1f}"
  same=csv_ranks==kb_ranks and csv_st==kb_st_s and csv_sr==kb_sr_s
  tot+=1; ok+=int(same)
  print(" LANE",lane,"PLAYER",player,"SAME",same,"CSV_ST",csv_st,"KB_ST",kb_st_s,"CSV_SR",csv_sr,"KB_SR",kb_sr_s)
  if not same: print("  CSV_R",csv_ranks,"KB_R",kb_ranks)
print("SUMMARY",ok,tot,"RATE",ok/tot if tot else 0)
print("COMPARE_OK")
