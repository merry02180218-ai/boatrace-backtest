#!/usr/bin/env python3
"""Download a BOATCAST exhibition replay through a normal browser session.

This does not bypass geo/access controls. It only proceeds when BOATCAST/Streaks
returns a successful playback response to the browser in the current network.
Designed for a Japan-based PC/VPS/self-hosted runner.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from urllib.parse import urlencode

from playwright.sync_api import sync_playwright

DATE = os.environ.get("RACE_DATE", "20260907")
STADIUM = os.environ.get("STADIUM", "01kiryu")
RACE = os.environ.get("RACE", "12")
OUT = Path(os.environ.get("VIDEO_OUT", f"boatcast_{DATE}_{STADIUM}_{int(RACE):02d}_exhibition.mp4"))
META = Path(os.environ.get("META_OUT", OUT.with_suffix(".json")))

PLAYER = "https://front.player.boatrace-cdn.jp/player/vod?" + urlencode({
    "raceDate": DATE,
    "raceNumber": RACE,
    "raceType": "exhibition",
    "service": "boatcast",
    "stadium": STADIUM,
    "autoplay": "1",
})


def scan_urls(obj, path="$"):
    found = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            found.extend(scan_urls(v, f"{path}.{k}"))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            found.extend(scan_urls(v, f"{path}[{i}]"))
    elif isinstance(obj, str):
        low = obj.lower()
        if obj.startswith(("http://", "https://")) and any(x in low for x in (".m3u8", ".mpd", ".mp4")):
            found.append({"path": path, "url": obj})
    return found


def pick_media(candidates):
    # Prefer HLS, then DASH, then direct MP4.
    for ext in (".m3u8", ".mpd", ".mp4"):
        for x in candidates:
            if ext in x["url"].lower():
                return x["url"]
    return ""


def download_with_ffmpeg(url: str, referer: str, user_agent: str):
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise SystemExit("ffmpeg is required")
    headers = f"Referer: {referer}\r\nOrigin: https://front.player.boatrace-cdn.jp\r\nUser-Agent: {user_agent}\r\n"
    cmd = [
        ffmpeg, "-y", "-loglevel", "warning",
        "-headers", headers,
        "-i", url,
        "-c", "copy",
        str(OUT),
    ]
    subprocess.run(cmd, check=True)


def main():
    playback = {}
    playback_status = None
    playback_url = ""
    browser_media_requests = []
    ua = ""

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--autoplay-policy=no-user-gesture-required"])
        page = browser.new_page(viewport={"width": 1280, "height": 720})
        ua = page.evaluate("navigator.userAgent")

        def on_response(res):
            nonlocal playback, playback_status, playback_url
            u = res.url
            if "playback.api.streaks.jp/" in u:
                playback_url = u
                playback_status = res.status
                try:
                    body = res.json()
                    if isinstance(body, dict):
                        playback = body
                except Exception:
                    pass
            if any(x in u.lower() for x in (".m3u8", ".mpd", ".mp4")):
                browser_media_requests.append(u)

        page.on("response", on_response)
        page.goto(PLAYER, wait_until="domcontentloaded", timeout=45000)
        page.wait_for_timeout(12000)
        try:
            page.evaluate("() => {const v=document.querySelector('video'); if(v){v.muted=true; v.play().catch(()=>{});}}")
        except Exception:
            pass
        page.wait_for_timeout(8000)
        browser.close()

    candidates = scan_urls(playback)
    for u in browser_media_requests:
        if not any(x["url"] == u for x in candidates):
            candidates.append({"path": "$browser_response", "url": u})

    media_url = pick_media(candidates)
    meta = {
        "race_date": DATE,
        "stadium": STADIUM,
        "race": int(RACE),
        "player_url": PLAYER,
        "playback_url": playback_url,
        "playback_status": playback_status,
        "playback": playback,
        "media_candidates": candidates,
        "selected_media_url": media_url,
    }
    META.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if playback_status != 200:
        msg = playback.get("message") if isinstance(playback, dict) else None
        raise SystemExit(f"Playback not permitted in this network: status={playback_status}, message={msg!r}")
    if not media_url:
        raise SystemExit("Playback succeeded but no m3u8/mpd/mp4 URL was found; inspect metadata JSON")

    download_with_ffmpeg(media_url, PLAYER, ua)
    print(json.dumps({"ok": True, "video": str(OUT), "metadata": str(META), "media_url": media_url}, ensure_ascii=False))


if __name__ == "__main__":
    main()
