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
    if u.startswith("//"):
        return "https:"+u
    return u


def main():
    seen=[]
    errors=[]
    html=""
    title=""
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,args=["--no-sandbox"])
        page=browser.new_page(viewport={"width":1280,"height":720})
        def remember(u):
            if ("m3u8" in u.lower() or ".mp4" in u.lower()) and u not in seen:
                seen.append(u)
        page.on("request",lambda req: remember(req.url))
        page.on("response",lambda res: remember(res.url))
        page.on("pageerror",lambda exc: errors.append(str(exc)))
        try:
            page.goto(URL,wait_until="domcontentloaded",timeout=45000)
            page.wait_for_timeout(10000)
            # Try common play controls; autoplay restrictions may prevent media request until click.
            for selector in ["video","button[aria-label*='play' i]","button:has-text('再生')",".vjs-big-play-button"]:
                try:
                    loc=page.locator(selector).first
                    if loc.count():
                        loc.click(timeout=2000,force=True)
                        page.wait_for_timeout(5000)
                        break
                except Exception:
                    pass
            html=page.content()
            title=page.title()
            try: page.screenshot(path=str(SHOT),full_page=False)
            except Exception as e: errors.append("screenshot: "+repr(e))
        except Exception as e:
            errors.append("goto: "+repr(e))
        finally:
            browser.close()
    for m in MEDIA_RE.findall(html):
        u=norm(m)
        if u not in seen: seen.append(u)
    result={
        "race_date":DATE,"jo":JO,"stadium":STADIUM,"race":int(RACE),
        "player_url":URL,"title":title,"media_urls":seen,
        "media_count":len(seen),"errors":errors,
        "html_has_video_tag":"<video" in html.lower(),
    }
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)
    if not seen:
        raise SystemExit("No m3u8/mp4 media URL discovered")

if __name__=="__main__":
    main()
