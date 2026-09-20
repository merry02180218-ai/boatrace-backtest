#!/usr/bin/env python3
from playwright.sync_api import sync_playwright
import json, re, pathlib
URL="https://kyoteibiyori.com/race_shusso.php?hiduke=20260716&place_no=11&race_no=1&slider=1"
out=pathlib.Path("/tmp/kb_pw"); out.mkdir(exist_ok=True)
events=[]
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True)
    page=browser.new_page(viewport={"width":1280,"height":1600}, user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/140 Safari/537.36")
    def req(r):
        events.append({"type":"request","method":r.method,"url":r.url,"resource":r.resource_type,"post":(r.post_data or "")[:1000]})
    def resp(r):
        ct=(r.headers.get("content-type") or "")
        item={"type":"response","status":r.status,"url":r.url,"content_type":ct}
        if any(x in ct.lower() for x in ["json","text","javascript","html"]):
            try: item["body"]=r.text()[:5000]
            except: pass
        events.append(item)
    page.on("request",req); page.on("response",resp)
    page.goto(URL,wait_until="domcontentloaded",timeout=60000)\n    page.wait_for_timeout(12000)
    page.wait_for_timeout(5000)
    html=page.content()
    (out/"page.html").write_text(html,encoding="utf-8")
    page.screenshot(path=str(out/"page.png"),full_page=True)
    browser.close()
(out/"network.json").write_text(json.dumps(events,ensure_ascii=False,indent=2),encoding="utf-8")
print("EVENTS",len(events))
for e in events:
    u=e.get("url",""); body=e.get("body","")
    if any(k in (u+" "+body).lower() for k in ["waku","slider","race_shusso","ajax","10走","枠別"]):
        print(json.dumps({k:v for k,v in e.items() if k!="body"},ensure_ascii=False))
        if body: print("BODY",re.sub(r"\\s+"," ",body)[:1500])
print("PW_PROBE_OK")
