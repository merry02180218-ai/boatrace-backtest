#!/usr/bin/env python3
"""Probe BOATCAST exhibition VOD and discover underlying media/source mapping.

Experimental infrastructure only. This does not change any prediction model.
Jul/Aug remain NON-PRISTINE; default probe is a September 2026 race.
"""
from __future__ import annotations
import json, os, re
from pathlib import Path
from urllib.parse import urlencode
from playwright.sync_api import sync_playwright

DATE=os.environ.get('RACE_DATE','20260907'); JO=os.environ.get('JO','01')
STADIUM=os.environ.get('STADIUM','01kiryu'); RACE=os.environ.get('RACE','12')
OUT=Path(os.environ.get('OUT','boatcast_exhibition_probe.json')); SHOT=Path(os.environ.get('SHOT','boatcast_exhibition_probe.png'))
q=urlencode({'raceDate':DATE,'raceNumber':RACE,'raceType':'exhibition','service':'boatcast','stadium':STADIUM})
URL=f'https://front.player.boatrace-cdn.jp/player/vod?{q}'
MEDIA_RE=re.compile(r'(?:https?:)?//[^\"\'\\\s<>]+?(?:\.m3u8|\.mp4)(?:\?[^\"\'\\\s<>]*)?',re.I)

def snippets(text, terms, radius=350):
    out=[]
    for term in terms:
        for m in re.finditer(re.escape(term),text,re.I):
            s=max(0,m.start()-radius); e=min(len(text),m.end()+radius)
            z=text[s:e].replace('\n',' ')
            if z not in out: out.append(z)
            if len(out)>=30:return out
    return out

def main():
    errors=[]; setting={}; vod_js=''; resources=[]; video_state={}; html=''
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,args=['--no-sandbox','--autoplay-policy=no-user-gesture-required'])
        page=browser.new_page(viewport={'width':1280,'height':720})
        page.on('pageerror',lambda exc: errors.append(str(exc)))
        try:
            page.goto(URL,wait_until='domcontentloaded',timeout=45000); page.wait_for_timeout(5000)
            resources=page.evaluate("() => performance.getEntriesByType('resource').map(x=>x.name)")
            su=next((u for u in resources if '/setting/vod/' in u and 'setting.json' in u),None)
            ju=next((u for u in resources if '/js/vod.js' in u),None)
            if su:
                try: setting=page.request.get(su,timeout=30000).json()
                except Exception as e: errors.append('setting:'+repr(e))
            if ju:
                try: vod_js=page.request.get(ju,timeout=30000).text()
                except Exception as e: errors.append('vodjs:'+repr(e))
            try:
                page.evaluate("() => {const v=document.querySelector('video');if(v){v.muted=true;v.play().catch(()=>{});}}")
                page.wait_for_timeout(7000)
                video_state=page.evaluate("() => {const v=document.querySelector('video');return v?{src:v.getAttribute('src')||'',currentSrc:v.currentSrc||'',readyState:v.readyState,paused:v.paused,currentTime:v.currentTime}:{};}")
            except Exception as e: errors.append('play:'+repr(e))
            html=page.content(); page.screenshot(path=str(SHOT),full_page=False)
        except Exception as e: errors.append('goto:'+repr(e))
        browser.close()
    race=setting.get('races',{}).get(str(int(RACE)),{}) or setting.get('races',{}).get(str(int(RACE)).zfill(2),{})
    js_snips=snippets(vod_js,['ref_id','source_type','mix','MediaSource','blob','fetch(','XMLHttpRequest','createObjectURL','video.src','player.src'])
    result={'race_date':DATE,'jo':JO,'stadium':STADIUM,'race':int(RACE),'player_url':URL,'race_setting':race,
            'setting':setting,'video_state':video_state,'resource_urls':resources,'vod_js_snippets':js_snips,
            'vod_js_media_literals':sorted(set(MEDIA_RE.findall(vod_js)))[:100],'html_media_literals':sorted(set(MEDIA_RE.findall(html)))[:100],'errors':errors}
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)
    if not setting or not vod_js: raise SystemExit('missing setting or vod.js')
if __name__=='__main__': main()
