#!/usr/bin/env python3
"""Probe BOATCAST exhibition VOD and discover underlying media/source mapping.

Experimental infrastructure only. This does not change any prediction model.
Jul/Aug remain NON-PRISTINE; default probe is a September 2026 race.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from urllib.parse import urlencode

from playwright.sync_api import sync_playwright

DATE=os.environ.get("RACE_DATE","20260907")
JO=os.environ.get("JO","01")
STADIUM=os.environ.get("STADIUM","01kiryu")
RACE=os.environ.get("RACE","12")
OUT=Path(os.environ.get("OUT","boatcast_exhibition_probe.json"))
SHOT=Path(os.environ.get("SHOT","boatcast_exhibition_probe.png"))

q=urlencode({"raceDate":DATE,"raceNumber":RACE,"raceType":"exhibition","service":"boatcast","stadium":STADIUM})
URL=f"https://front.player.boatrace-cdn.jp/player/vod?{q}"
MEDIA_RE=re.compile(r"(?:https?:)?//[^\"'\\\s<>]+?(?:\.m3u8|\.mp4)(?:\?[^\"'\\\s<>]*)?",re.I)
URL_RE=re.compile(r"https?://[^\"'\\\s<>]+",re.I)


def norm(u:str)->str:
    return "https:"+u if u.startswith("//") else u


def scan_strings(obj, path="$"):
    out=[]
    if isinstance(obj,dict):
        for k,v in obj.items(): out += scan_strings(v,f"{path}.{k}")
    elif isinstance(obj,list):
        for i,v in enumerate(obj): out += scan_strings(v,f"{path}[{i}]")
    elif isinstance(obj,str):
        low=obj.lower()
        if any(x in low for x in ["http://","https://",".mp4",".m3u8","movie","video","stream","path","file","src"]):
            out.append({"path":path,"value":obj})
    return out


def main():
    media=[]; network=[]; errors=[]; html=""; title=""; video_state={}; perf=[]
    setting={}; setting_strings=[]; vod_js=""; vod_js_urls=[]
    def add_media(u):
        if u and u not in media: media.append(u)
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,args=["--no-sandbox","--autoplay-policy=no-user-gesture-required"])
        page=browser.new_page(viewport={"width":1280,"height":720})
        def on_request(req):
            u=req.url
            if any(k in u.lower() for k in ["m3u8","mp4","playlist","manifest","stream","vod","video","movie","hls","setting.json"]):
                network.append({"type":"request","url":u,"resource_type":req.resource_type})
            if "m3u8" in u.lower() or ".mp4" in u.lower(): add_media(u)
        page.on("request",on_request)
        page.on("pageerror",lambda exc: errors.append(str(exc)))
        try:
            page.goto(URL,wait_until="domcontentloaded",timeout=45000)
            page.wait_for_timeout(5000)
            # Fetch setting.json and vod.js from the same browser context so cookies/origin match the player.
            resources=page.evaluate("""() => performance.getEntriesByType('resource').map(x=>x.name)""")
            setting_url=next((u for u in resources if '/setting/vod/' in u and 'setting.json' in u),None)
            vod_js_url=next((u for u in resources if '/js/vod.js' in u),None)
            if setting_url:
                try:
                    r=page.request.get(setting_url,timeout=30000)
                    setting=r.json()
                    setting_strings=scan_strings(setting)
                    network.append({"type":"setting-fetch","url":setting_url,"status":r.status})
                    for x in setting_strings:
                        v=x["value"]
                        for m in MEDIA_RE.findall(v): add_media(norm(m))
                except Exception as e: errors.append("setting-fetch: "+repr(e))
            if vod_js_url:
                try:
                    r=page.request.get(vod_js_url,timeout=30000)
                    vod_js=r.text()
                    vod_js_urls=sorted(set(URL_RE.findall(vod_js)))[:100]
                    network.append({"type":"vod-js-fetch","url":vod_js_url,"status":r.status})
                except Exception as e: errors.append("vod-js-fetch: "+repr(e))
            try:
                page.evaluate("""() => { const v=document.querySelector('video'); if(v){ v.muted=true; const p=v.play(); if(p&&p.catch)p.catch(()=>{}); } }""")
            except Exception as e: errors.append("evaluate-play: "+repr(e))
            for selector in [".vjs-big-play-button","button[aria-label*='play' i]","button:has-text('再生')","video"]:
                try:
                    loc=page.locator(selector).first
                    if loc.count() and loc.is_visible(): loc.click(timeout=1500,force=True); break
                except Exception: pass
            page.wait_for_timeout(7000)
            try:
                video_state=page.evaluate("""() => { const v=document.querySelector('video'); if(!v)return {}; return {src:v.getAttribute('src')||'',currentSrc:v.currentSrc||'',readyState:v.readyState,networkState:v.networkState,paused:v.paused,duration:v.duration,currentTime:v.currentTime,error:v.error?{code:v.error.code,message:v.error.message}:null}; }""")
                for k in ["src","currentSrc"]:
                    u=video_state.get(k) or ""
                    if u and not u.startswith("blob:"): add_media(u)
            except Exception as e: errors.append("video-state: "+repr(e))
            try:
                perf=page.evaluate("""() => performance.getEntriesByType('resource').map(x=>({name:x.name,initiatorType:x.initiatorType})).filter(x=>/m3u8|mp4|playlist|manifest|stream|vod|video|movie|hls|setting\.json/i.test(x.name))""")
                for x in perf:
                    u=x.get("name","")
                    if "m3u8" in u.lower() or ".mp4" in u.lower(): add_media(u)
            except Exception as e: errors.append("performance: "+repr(e))
            # Capture candidate responses after playback using Resource Timing plus CDP-unavailable diagnostics.
            html=page.content(); title=page.title()
            try: page.screenshot(path=str(SHOT),full_page=False)
            except Exception as e: errors.append("screenshot: "+repr(e))
        except Exception as e: errors.append("goto: "+repr(e))
        finally: browser.close()
    for m in MEDIA_RE.findall(html): add_media(norm(m))
    result={
        "race_date":DATE,"jo":JO,"stadium":STADIUM,"race":int(RACE),"player_url":URL,"title":title,
        "media_urls":media,"media_count":len(media),"video_state":video_state,
        "setting":setting,"setting_strings":setting_strings,"vod_js_urls":vod_js_urls,
        "vod_js_media_literals":sorted(set(norm(m) for m in MEDIA_RE.findall(vod_js)))[:100],
        "network_candidates":network[-200:],"performance_candidates":perf[-200:],"errors":errors,
        "html_has_video_tag":"<video" in html.lower(),
    }
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)
    if not setting:
        raise SystemExit("setting.json not captured")

if __name__=="__main__": main()
