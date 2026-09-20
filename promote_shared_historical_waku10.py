#!/usr/bin/env python3
"""Promote reconstructed historical Boatcast Waku10 into a shared canonical tree.
Input artifact must be unpacked at data/reconstructed_waku10_boatcast.
No result/outcome files are read.
"""
import os,shutil,hashlib,json
SRC="data/reconstructed_waku10_boatcast"
DST="data/shared_historical/waku10_boatcast"
if not os.path.isdir(SRC): raise SystemExit("MISSING_RECONSTRUCTED_WAKU10")
os.makedirs(DST,exist_ok=True)
manifest=[]
for root,_,files in os.walk(SRC):
 for fn in files:
  if not fn.endswith(".txt"): continue
  sp=os.path.join(root,fn); rel=os.path.relpath(sp,SRC); dp=os.path.join(DST,rel)
  os.makedirs(os.path.dirname(dp),exist_ok=True); shutil.copy2(sp,dp)
  b=open(dp,"rb").read(); manifest.append({"path":rel,"bytes":len(b),"sha256":hashlib.sha256(b).hexdigest()})
with open(os.path.join(DST,"manifest.json"),"w",encoding="utf-8") as f: json.dump({"source":"Boatcast bc_j_waku10 historical date-fixed files","result_files_read":False,"september_outcomes_read":False,"files":manifest},f,ensure_ascii=False,indent=2)
print("SHARED_WAKU10_FILES",len(manifest))
print("SHARED_PATH",DST)
print("RESULT_FILES_READ",False)
print("SEPTEMBER_OUTCOMES_READ",False)
print("PROMOTE_SHARED_OK")
