#!/usr/bin/env python3
"""Probe BOATCAST exhibition VOD and discover underlying media URLs.

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

q=urlencode({
    "raceDate":DATE,
    "raceNumber":RACE,
    "raceType":"exhibition",
    "service":"boatcast",
    "stadium":STADIUM,
})
URL=f"https://front.player.boatrace-cdn.jp/player/vod?{q}"
MEDIA_RE=re.compile(r"(?:https?:)?//[^\"'\\\s<>]+?(?:\.m3u8|\.mp4)(?:\?[^\"'\\\s<>]*)?",re.I)


def norm(u:str)->str:
    return "https:"+u if u.startswith("//") else u


def main():
    media=[]; network=[]; errors=[]; html=""; title=""; video_state={}; perf=[]
    def add_media(u):
        if u and u not in media: media.append(u)
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,args=["--no-sandbox","--autoplay-policy=no-user-gesture-required"])
        page=browser.new_page(viewport={"width":1280,"height":720})
        def on_request(req):
            u=req.url
            if any(k in u.lower() for k in ["m3u8","mp4","playlist","manifest","stream","vod","video","movie","hls"]):
                network.append({"type":"request","url":u,"resource_type":req.resource_type})
            if "m3u8" in u.lower() or ".mp4" in u.lower(): add_media(u)
        def on_response(res):
            u=res.url
            ct=""
            try: ct=(res.headers.get("content-type") or "").lower()
            except Exception: pass
            if any(x in ct for x in ["mpegurl","video/","application/vnd.apple.mpegurl"]): add_media(u)
            if any(k in u.lower() for k in ["m3u8","mp4","playlist","manifest","stream","vod","video","movie","hls"]) or "mpegurl" in ct or ct.startswith("video/"):
                network.append({"type":"response","url":u,"status":res.status,"content_type":ct})
        page.on("request",on_request)
        page.on("response",on_response)
        page.on("pageerror",lambda exc: errors.append(str(exc)))
        try:
            page.goto(URL,wait_until="domcontentloaded",timeout=45000)
            page.wait_for_timeout(7000)
            # Directly ask HTMLMediaElement to play; also click visible controls as fallback.
            try:
                page.evaluate("""() => { const v=document.querySelector('video'); if(v){ v.muted=true; const p=v.play(); if(p&&p.catch)p.catch(()=>{}); } }""")
            except Exception as e: errors.append("evaluate-play: "+repr(e))
            for selector in [".vjs-big-play-button","button[aria-label*='play' i]","button:has-text('再生')","video"]:
                try:
                    loc=page.locator(selector).first
                    if loc.count() and loc.is_visible():
                        loc.click(timeout=1500,force=True)
                        break
                except Exception: pass
            page.wait_for_timeout(10000)
            try:
                video_state=page.evaluate("""() => { const v=document.querySelector('video'); if(!v)return {}; return {src:v.getAttribute('src')||'', currentSrc:v.currentSrc||'', readyState:v.readyState, networkState:v.networkState, paused:v.paused, duration:v.duration, currentTime:v.currentTime, error:v.error ? {code:v.error.code,message:v.error.message}:null}; }""")
                for k in ["src","currentSrc"]:
                    u=video_state.get(k) or ""
                    if u and not u.startswith("blob:"): add_media(u)
            except Exception as e: errors.append("video-state: "+repr(e))
            try:
                perf=page.evaluate("""() => performance.getEntriesByType('resource').map(x=>({name:x.name,initiatorType:x.initiatorType})).filter(x=>/m3u8|mp4|playlist|manifest|stream|vod|video|movie|hls/i.test(x.name))""")
                for x in perf:
                    u=x.get("name","")
                    if "m3u8" in u.lower() or ".mp4" in u.lower(): add_media(u)
            except Exception as e: errors.append("performance: "+repr(e))
            html=page.content(); title=page.title()
            try: page.screenshot(path=str(SHOT),full_page=False)
            except Exception as e: errors.append("screenshot: "+repr(e))
        except Exception as e:
            errors.append("goto: "+repr(e))
        finally:
            browser.close()
    for m in MEDIA_RE.findall(html): add_media(norm(m))
    result={
        "race_date":DATE,"jo":JO,"stadium":STADIUM,"race":int(RACE),
        "player_url":URL,"title":title,"media_urls":media,"media_count":len(media),
        "video_state":video_state,"network_candidates":network[-200:],"performance_candidates":perf[-200:],
        "errors":errors,"html_has_video_tag":"<video" in html.lower(),
    }
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)
    if not media:
        raise SystemExit("No media URL discovered; diagnostics recorded")

if __name__=="__main__":
    main()
