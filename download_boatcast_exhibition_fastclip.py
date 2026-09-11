#!/usr/bin/env python3
"""Low-latency BOATCAST exhibition clip fetcher for live use.

Goal: obtain only the start-exhibition analysis window fast enough to score before
betting close. Uses a normal browser session on the Japan self-hosted runner,
waits only until playback metadata is available, then asks ffmpeg for a short VOD
slice instead of downloading the full exhibition program.

No race-result endpoint is accessed.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from pathlib import Path
from urllib.parse import urlencode

from playwright.sync_api import sync_playwright

DATE = os.environ.get("RACE_DATE", "20260910")
STADIUM = os.environ.get("STADIUM", "01kiryu")
RACE = os.environ.get("RACE", "12")
CLIP_START = float(os.environ.get("CLIP_START_SEC", "82"))
CLIP_DURATION = float(os.environ.get("CLIP_DURATION_SEC", "52"))
WAIT_SEC = float(os.environ.get("PLAYBACK_WAIT_SEC", "8"))
POLL_SEC = float(os.environ.get("PLAYBACK_POLL_SEC", "0.25"))
OUT = Path(os.environ.get("VIDEO_OUT", f"boatcast_{DATE}_{STADIUM}_{int(RACE):02d}_startclip.mp4"))
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
    for ext in (".m3u8", ".mpd", ".mp4"):
        for x in candidates:
            if ext in x["url"].lower():
                return x["url"]
    return ""


def download_slice(url: str, referer: str, user_agent: str):
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise SystemExit("ffmpeg is required")
    headers = (
        f"Referer: {referer}\r\n"
        "Origin: https://front.player.boatrace-cdn.jp\r\n"
        f"User-Agent: {user_agent}\r\n"
    )
    # Input-side seek is intentional: on VOD HLS it can jump to the segment near
    # the requested timestamp instead of reading the whole program from t=0.
    cmd = [
        ffmpeg, "-y", "-loglevel", "warning",
        "-headers", headers,
        "-ss", f"{CLIP_START:.3f}",
        "-i", url,
        "-t", f"{CLIP_DURATION:.3f}",
        "-c", "copy",
        str(OUT),
    ]
    subprocess.run(cmd, check=True)


def main():
    t0 = time.perf_counter()
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
        page.goto(PLAYER, wait_until="domcontentloaded", timeout=15000)
        deadline = time.perf_counter() + WAIT_SEC
        while time.perf_counter() < deadline and playback_status is None:
            page.wait_for_timeout(max(50, int(POLL_SEC * 1000)))
        browser.close()

    candidates = scan_urls(playback)
    for u in browser_media_requests:
        if not any(x["url"] == u for x in candidates):
            candidates.append({"path": "$browser_response", "url": u})
    media_url = pick_media(candidates)

    resolved_at = time.perf_counter()
    if playback_status != 200:
        msg = playback.get("message") if isinstance(playback, dict) else None
        raise SystemExit(f"Playback not ready/permitted: status={playback_status}, message={msg!r}")
    if not media_url:
        raise SystemExit("Playback succeeded but no media URL found")

    download_slice(media_url, PLAYER, ua)
    done_at = time.perf_counter()
    meta = {
        "race_date": DATE,
        "stadium": STADIUM,
        "race": int(RACE),
        "clip_start_sec": CLIP_START,
        "clip_duration_sec": CLIP_DURATION,
        "player_url": PLAYER,
        "playback_url": playback_url,
        "playback_status": playback_status,
        "selected_media_url": media_url,
        "timing_sec": {
            "resolve_playback": round(resolved_at - t0, 3),
            "download_clip": round(done_at - resolved_at, 3),
            "total": round(done_at - t0, 3),
        },
        "result_blind": True,
        "race_results_read": False,
    }
    META.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "video": str(OUT), "metadata": str(META), "timing_sec": meta["timing_sec"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
