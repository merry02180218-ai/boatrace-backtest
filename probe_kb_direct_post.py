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
            try:
                obj=json.loads(b)
                print("TOP_KEYS",list(obj.keys()))
                kl=obj.get("kako_list",{})
                for kk,vv in kl.items():
                    print("KAKO",kk,"TYPE",type(vv).__name__,"LEN",len(vv) if hasattr(vv,"__len__") else None)
                    if isinstance(vv,list):
                        for z in vv[:3]: print("KAKO_SAMPLE",kk,json.dumps(z,ensure_ascii=False)[:3000])
                    elif isinstance(vv,dict):
                        print("KAKO_KEYS",kk,list(vv.keys())[:50])
                        print("KAKO_SAMPLE",kk,json.dumps(vv,ensure_ascii=False)[:5000])
                for k,v in obj.items():
                    if isinstance(v,list):
                        print("LIST",k,"LEN",len(v),"SAMPLE_KEYS",list(v[0].keys())[:80] if v and isinstance(v[0],dict) else [])
                    elif isinstance(v,dict):
                        print("DICT",k,"KEYS",list(v.keys())[:80])
            except Exception as je: print("JSON_PARSE_ERROR",repr(je))
    except Exception as e: print("CASE",i,"ERROR",repr(e))
print("DIRECT_POST_PROBE_OK")
