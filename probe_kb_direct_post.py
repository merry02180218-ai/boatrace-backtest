#!/usr/bin/env python3
import json, urllib.parse, urllib.request
URL="https://kyoteibiyori.com/request_race_shusso_detail_v4.php"
cases=[
 {"place_no":"11","race_no":"1","hiduke":"20260716","race_name":"","season":2026,"term":1,"kaisai_key":"2026071611","taikai_count":"0","group_no":"0","type":0,"grade":0},
 {"place_no":"11","race_no":"1","hiduke":"20260716","race_name":"","season":2026,"term":2,"kaisai_key":"2026071611","taikai_count":"0","group_no":"0","type":0,"grade":0},
]
for i,p in enumerate(cases,1):
    body=urllib.parse.urlencode({"data":json.dumps(p,ensure_ascii=False,separators=(",",":"))}).encode()
    req=urllib.request.Request(URL,data=body,headers={"User-Agent":"Mozilla/5.0","Content-Type":"application/x-www-form-urlencoded","Referer":"https://kyoteibiyori.com/"})
    try:
        with urllib.request.urlopen(req,timeout=30) as r:
            b=r.read().decode("utf-8","ignore")
            print("CASE",i,"STATUS",r.status,"BYTES",len(b),"CTYPE",r.headers.get("content-type"))
            print("HEAD",b[:1500].replace("\n"," "))
            print("KEYS",{k:(k in b) for k in ["枠別","10走","1着率","データ取得中","waku"]})
    except Exception as e: print("CASE",i,"ERROR",repr(e))
print("DIRECT_POST_PROBE_OK")
