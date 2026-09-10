#!/usr/bin/env python3
"""Probe BOATCAST exhibition VOD and resolve the authenticated playback media.

Experimental infrastructure only. This does not change any prediction model.
Jul/Aug remain NON-PRISTINE; default probe is a September 2026 race.
"""
from __future__ import annotations
import json, os
from pathlib import Path
from urllib.parse import urlencode
from playwright.sync_api import sync_playwright

DATE=os.environ.get('RACE_DATE','20260907'); JO=os.environ.get('JO','01')
STADIUM=os.environ.get('STADIUM','01kiryu'); RACE=os.environ.get('RACE','12')
OUT=Path(os.environ.get('OUT','boatcast_exhibition_probe.json')); SHOT=Path(os.environ.get('SHOT','boatcast_exhibition_probe.png'))
q=urlencode({'raceDate':DATE,'raceNumber':RACE,'raceType':'exhibition','service':'boatcast','stadium':STADIUM})
URL=f'https://front.player.boatrace-cdn.jp/player/vod?{q}'

def scan_urls(obj,path='$'):
    out=[]
    if isinstance(obj,dict):
        for k,v in obj.items(): out += scan_urls(v,f'{path}.{k}')
    elif isinstance(obj,list):
        for i,v in enumerate(obj): out += scan_urls(v,f'{path}[{i}]')
    elif isinstance(obj,str):
        if obj.startswith(('http://','https://')) or '.mp4' in obj.lower() or '.m3u8' in obj.lower(): out.append({'path':path,'value':obj})
    return out

def main():
    errors=[]; setting={}; playback={}; resources=[]; auth_request_headers={}; playback_url=''
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,args=['--no-sandbox','--autoplay-policy=no-user-gesture-required'])
        page=browser.new_page(viewport={'width':1280,'height':720})
        def on_request(req):
            nonlocal playback_url, auth_request_headers
            if 'playback.api.streaks.jp/' in req.url:
                playback_url=req.url
                try: auth_request_headers=req.all_headers()
                except Exception as e: errors.append('request-headers:'+repr(e))
        def on_response(res):
            nonlocal playback
            if 'playback.api.streaks.jp/' in res.url:
                try:
                    body=res.json()
                    if isinstance(body,dict): playback=body
                except Exception as e: errors.append('authenticated-playback-response:'+repr(e))
        page.on('request',on_request); page.on('response',on_response)
        try:
            page.goto(URL,wait_until='domcontentloaded',timeout=45000)
            page.wait_for_timeout(10000)
            resources=page.evaluate("() => performance.getEntriesByType('resource').map(x=>x.name)")
            su=next((u for u in resources if '/setting/vod/' in u and 'setting.json' in u),None)
            if su: setting=page.request.get(su,timeout=30000).json()
            try:
                page.evaluate("() => {const v=document.querySelector('video');if(v){v.muted=true;v.play().catch(()=>{});}}")
                page.wait_for_timeout(5000); page.screenshot(path=str(SHOT),full_page=False)
            except Exception as e: errors.append('play:'+repr(e))
        except Exception as e: errors.append('goto:'+repr(e))
        browser.close()
    race=setting.get('races',{}).get(str(int(RACE)).zfill(2),{}) or setting.get('races',{}).get(str(int(RACE)),{})
    candidates=scan_urls(playback)
    # Do not print bearer/cookie values; only names prove what auth is needed.
    result={'race_date':DATE,'jo':JO,'stadium':STADIUM,'race':int(RACE),'player_url':URL,'race_setting':race,
            'playback_url':playback_url,'playback':playback,'source_candidates':candidates,
            'authenticated_request_header_names':sorted(auth_request_headers.keys()),'resource_urls':resources,'errors':errors}
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)
    if not playback or playback.get('status')==401: raise SystemExit('authenticated playback response not captured')
if __name__=='__main__': main()
