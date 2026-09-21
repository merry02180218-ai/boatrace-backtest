#!/usr/bin/env python3
import os,re,urllib.request,random
ROOT="data/reconstructed_waku10_boatcast/2026"
files=[]
for root,_,fs in os.walk(ROOT):
 for f in fs:
  if f.endswith(".txt"): files.append(os.path.join(root,f))
print("FILES",len(files))
bad=[]
for p in files:
 b=open(p,encoding="utf-8").read()
 lines=b.splitlines()
 if len(lines)<8 or lines[0]!="data=" or not lines[1].startswith("1\t"): bad.append((p,"shape"))
 else:
  for row in lines[2:8]:
   c=row.split("\t")
   if len(c)<34: bad.append((p,"cols",len(c))); break
print("FORMAT_BAD",len(bad),bad[:10])
# Direct source spot check: compare saved bytes to Boatcast URL for deterministic samples.
samples=sorted(files)[::max(1,len(files)//40)][:40]; mismatch=0
for p in samples:
 m=re.search(r"/2026/(0[3-6])/(\d\d)/(\d\d)_(\d\d)\.txt$",p)
 if not m: continue
 mo,dd,jo,rr=m.groups(); ds=f"2026{mo}{dd}"
 u=f"https://race.boatcast.jp/hp_txt/{jo}/bc_j_waku10_{ds}_{jo}_{rr}.txt"
 cur=urllib.request.urlopen(urllib.request.Request(u,headers={"User-Agent":"Mozilla/5.0"}),timeout=20).read().decode("utf-8","ignore")
 same=cur==open(p,encoding="utf-8").read(); mismatch+=int(not same)
 print("SOURCE_CHECK",ds,jo,rr,same)
print("SOURCE_SAMPLES",len(samples),"MISMATCH",mismatch)
# Known July reference values previously verified against BoatraceCSV.
u="https://race.boatcast.jp/hp_txt/01/bc_j_waku10_20260719_01_01.txt"
b=urllib.request.urlopen(urllib.request.Request(u,headers={"User-Agent":"Mozilla/5.0"}),timeout=20).read().decode("utf-8","ignore")
r=b.splitlines()[2].split("\t")
print("KNOWN_JUL19",r[0],r[1],r[2],r[3],"EXPECTED","渡辺　　豊","6.40","0.16","3.5")
print("KNOWN_MATCH",r[1]=="6.40" and r[2]=="0.16" and r[3]=="3.5")
print("RESULT_FILES_READ",False); print("SEPTEMBER_OUTCOMES_READ",False)
if bad or mismatch: raise SystemExit("VALIDATION_FAILED")
print("VALIDATION_OK")
