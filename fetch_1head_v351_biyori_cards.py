#!/usr/bin/env python3
"""Build result-blind v351 daily race_cards.csv from BoatRace Biyori entry/detail API.

Fetches only pre-race entry/profile/motor data. Result/payout/odds are never requested.
"""
from __future__ import annotations
import argparse,csv,json,re,time
from pathlib import Path
import requests
from bs4 import BeautifulSoup

BASE='https://kyoteibiyori.com'
RETRIES=5

def norm_st(x):
    try:
        v=float(x)
        return v/100.0 if v>1 else v
    except:return ''

def retry_get(s,u,timeout=30):
    last=None
    for n in range(RETRIES):
        try:
            r=s.get(u,timeout=timeout); r.raise_for_status(); return r
        except Exception as e:
            last=e; time.sleep(1.5*(n+1))
    raise last

def retry_post(s,u,*,data,headers,timeout=35):
    last=None
    for n in range(RETRIES):
        try:
            r=s.post(u,data=data,headers=headers,timeout=timeout); r.raise_for_status(); return r
        except Exception as e:
            last=e; time.sleep(1.5*(n+1))
    raise last

def get_meta(s,day,jo):
    u=f'{BASE}/race_shusso.php?hiduke={day}&place_no={jo}&race_no=1&slider=1'
    h=retry_get(s,u).text; soup=BeautifulSoup(h,'html.parser')
    def v(n):
        z=soup.find('input',{'name':n}); return z.get('value','') if z else ''
    m=re.search(r'var\s+CSRF_TOKEN\s*=\s*"([^"]+)"',h)
    meta={k:v(k) for k in ['race_name','kaisai_key','taikai_count','group_no','race_year','race_date','place_name']}
    if not m or not meta['kaisai_key']: return None
    return u,m.group(1),meta

def detail(s,day,jo,rno,referer,token,meta):
    d={'place_no':str(jo),'race_no':str(rno),'hiduke':day,'race_name':meta['race_name'],'season':2021,'term':1,
       'kaisai_key':meta['kaisai_key'],'taikai_count':meta['taikai_count'],'group_no':meta['group_no'],'type':0,'grade':0}
    payload={'data':json.dumps(d,ensure_ascii=False),'token':token}
    r=retry_post(s,f'{BASE}/request_race_shusso_detail_v4.php',data=payload,
                 headers={'Referer':referer,'X-Requested-With':'XMLHttpRequest'})
    z=r.json()
    return z if len(z.get('race_list',[]))==6 else None

def make_card(day,jo,rno,z):
    iso=f'{day[:4]}-{day[4:6]}-{day[6:8]}'
    c={'レースコード':f'{day}{jo:02d}{rno:02d}','レース日':iso,'レース場コード':f'{jo:02d}','レース回':str(rno)}
    ps=sorted(z['race_list'],key=lambda x:int(x.get('course') or 99))
    for b,p in enumerate(ps,1):
        q=f'艇{b}_'
        c.update({q+'登録番号':p.get('player_no',''),q+'選手名':p.get('player_name',''),q+'級別':p.get('kyubetsu',''),
          q+'全国平均ST':norm_st(p.get('ave_start')),q+'全国勝率':p.get('zenkoku_shoritsu',''),q+'全国2連対率':p.get('zenkoku_niren',''),q+'全国3連対率':p.get('zenkoku_sanren',''),
          q+'当地勝率':p.get('touchi_shoritsu',''),q+'当地2連対率':p.get('touchi_niren',''),q+'当地3連対率':p.get('touchi_sanren',''),
          q+'モーター番号':p.get('motor',''),q+'モーター2連対率':p.get('motor_niren',''),q+'モーター3連対率':p.get('motor_sanren',''),
          q+'ボート番号':p.get('boat',''),q+'ボート2連対率':p.get('boat_niren',''),q+'ボート3連対率':p.get('boat_sanren',''),
          q+'早見':p.get('hayami',''),q+'F本数':p.get('flying','') or 0,q+'L本数':p.get('late0','') or 0})
    return c

def write_csv(path,rows):
    fields=[]; seen=set()
    for r in rows:
        for k in r:
            if k not in seen: seen.add(k); fields.append(k)
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--date',required=True); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args()
    day=a.date.replace('-','')
    if not re.fullmatch(r'20\d{6}',day): raise SystemExit('bad date')
    s=requests.Session(); s.headers.update({'User-Agent':'Mozilla/5.0 (compatible; v351-live-pre-card/2.1)','Accept':'text/html,application/json'})
    rows=[]; venues=[]; failed=[]
    for jo in range(1,25):
        try: meta=get_meta(s,day,jo)
        except Exception as e: failed.append((jo,'meta',str(e))); continue
        if not meta: continue
        referer,token,m=meta; vr=[]
        for rno in range(1,13):
            try:
                z=detail(s,day,jo,rno,referer,token,m)
                if not z: raise RuntimeError('detail empty')
                vr.append(make_card(day,jo,rno,z)); time.sleep(.05)
            except Exception as e: failed.append((jo,rno,str(e)))
        if len(vr)==12: rows.extend(vr); venues.append(jo)
        elif vr: failed.append((jo,'grid',f'{len(vr)}/12'))
    if not rows: raise RuntimeError(f'BIYORI detail API returned no complete target-date cards for {day}; failures={failed[:8]}')
    if len(rows)!=12*len(venues): raise RuntimeError(f'incomplete BIYORI grid venues={venues} R={len(rows)}')
    a.out.parent.mkdir(parents=True,exist_ok=True); write_csv(a.out,rows)
    print(f'BIYORI_CARDS date={day} venues={venues} races={len(rows)} result_or_payout_used=False chronology_guard=True')
    if failed: print('BIYORI_SKIPPED',failed[:20])
    return 0
if __name__=='__main__': raise SystemExit(main())
