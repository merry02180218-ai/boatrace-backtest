#!/usr/bin/env python3
import csv,io,urllib.request,datetime
BASE="https://raw.githubusercontent.com/BoatraceCSV/boatracecsv.github.io/main/data/programs/waku10/2026/{m}/{d}.csv"
def get(u):
 try:return urllib.request.urlopen(urllib.request.Request(u,headers={"User-Agent":"Mozilla/5.0"}),timeout=20).read().decode("utf-8-sig","ignore")
 except:return None
def norm_text(x):
 return " ".join((x or "").replace("　"," ").split())
def norm_num(x):
 try:
  return str(float(x))
 except:
  return (x or "").strip()
tot=mis=files=0; examples=[]
day=datetime.date(2026,7,19); end=datetime.date(2026,8,31)
while day<=end:
 m,d=day.strftime("%m"),day.strftime("%d"); c=get(BASE.format(m=m,d=d))
 if not c: day+=datetime.timedelta(days=1); continue
 files+=1
 for row in csv.DictReader(io.StringIO(c)):
  jo=int(row["レース場コード"]); rr=int(str(row["レース回"]).replace("R","")); ds=day.strftime("%Y%m%d")
  b=get(f"https://race.boatcast.jp/hp_txt/{jo:02d}/bc_j_waku10_{ds}_{jo:02d}_{rr:02d}.txt")
  if not b or not b.startswith("data="): mis+=1; examples.append((ds,jo,rr,"missing")); continue
  lines=b.splitlines()[2:8]
  for lane,line in enumerate(lines,1):
   cols=line.split("\t"); checks=[("text",cols[0],row[f"艇{lane}_選手名"]),("num",cols[1],row[f"艇{lane}_枠番別勝率"]),("num",cols[2],row[f"艇{lane}_枠番別平均ST"]),("num",cols[3],row[f"艇{lane}_枠番別平均スタート順"])]
   for k in range(10):
    base=4+k*3
    checks += [("text",cols[base].translate(str.maketrans("１２３４５６７８９ＦＬ","123456789FL")),row[f"艇{lane}_過去{k+1}走_着順"]),("text",cols[base+1],row[f"艇{lane}_過去{k+1}走_進入"]),("text",cols[base+2],row[f"艇{lane}_過去{k+1}走_グレード"])]
   for typ,a,z in checks:
    tot+=1
    aa,zz=(norm_num(a),norm_num(z)) if typ=="num" else (norm_text(a),norm_text(z))
    if aa!=zz:
     mis+=1
     if len(examples)<30: examples.append((ds,jo,rr,lane,typ,a,z,aa,zz))
 day+=datetime.timedelta(days=1)
print("CSV_DAYS",files,"CELLS",tot,"MISMATCH",mis,"RATE",0 if not tot else mis/tot)
print("EXAMPLES",examples)
print("RESULT_FILES_READ",False); print("SEPTEMBER_OUTCOMES_READ",False)
if mis: raise SystemExit("PARITY_MISMATCH")
print("FULL_PARITY_OK")
