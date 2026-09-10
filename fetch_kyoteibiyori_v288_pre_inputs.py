#!/usr/bin/env python3
from __future__ import annotations
import csv,json,re,time
from collections import defaultdict
from pathlib import Path
import requests
from bs4 import BeautifulSoup

# 2026-09-11 operational PRE scan: Kyoteibiyori supplies current race-card/Waku10-equivalent inputs.
DAY='20260911'
VENUES=[2,3,5,6,12,13,14,16,17,20,21,24]
OUT=Path('current_input'); OUT.mkdir(exist_ok=True)
BASE='https://kyoteibiyori.com'


def valnum(x,scale=1.0):
    try:return float(x)/scale
    except:return ''
def norm_st(x):
    try:
        v=float(x)
        if v>1: v/=100.0
        return v
    except:return ''

def get_meta(s,jo):
    u=f'{BASE}/race_shusso.php?hiduke={DAY}&place_no={jo}&race_no=1&slider=1'
    h=s.get(u,timeout=25).text
    soup=BeautifulSoup(h,'html.parser')
    def v(n):
        z=soup.find('input',{'name':n}); return z.get('value','') if z else ''
    m=re.search(r'var\s+CSRF_TOKEN\s*=\s*"([^"]+)"',h)
    if not m: raise RuntimeError(f'CSRF missing JCD{jo:02d}')
    return u,m.group(1),{k:v(k) for k in ['race_name','kaisai_key','taikai_count','group_no','race_year','race_date','place_name']}

def detail(s,jo,rno,referer,token,meta):
    d={'place_no':str(jo),'race_no':str(rno),'hiduke':DAY,'race_name':meta['race_name'],'season':2021,'term':1,
       'kaisai_key':meta['kaisai_key'],'taikai_count':meta['taikai_count'],'group_no':meta['group_no'],'type':0,'grade':0}
    r=s.post(f'{BASE}/request_race_shusso_detail_v4.php',data={'data':json.dumps(d,ensure_ascii=False),'token':token},
             headers={'Referer':referer,'X-Requested-With':'XMLHttpRequest'},timeout=30)
    z=r.json()
    if len(z.get('race_list',[]))!=6:return None
    return z

def meeting(s,jo,rno,referer,meta,players):
    d={'race_year':int(meta['race_year'] or 2026),'race_name':meta['race_name'],'race_date':meta['race_date'],'place_no':str(jo),
       'race_no':str(rno),'hiduke':DAY,'kaisai_key':meta['kaisai_key']}
    for i,p in enumerate(players): d['player_no' if i==0 else f'player_no{i+1}']=p['player_no']
    r=s.post(f'{BASE}/request_konsetsu_all.php',data={'data':json.dumps(d,ensure_ascii=False)},
             headers={'Referer':referer,'X-Requested-With':'XMLHttpRequest'},timeout=30)
    x=r.json(); return x if isinstance(x,list) else []

def make_card(jo,rno,z,meet):
    code=f'{DAY}{jo:02d}{rno:02d}'; card={'レースコード':code,'レース日':'2026-09-11','レース場コード':f'{jo:02d}','レース回':str(rno)}
    mh=defaultdict(list)
    for a in meet:
        try:pn=int(a.get('player_no'))
        except:continue
        st=a.get('start')
        try:float(st)
        except:continue
        if int(a.get('hiduke') or 0)>=int(DAY):continue
        mh[pn].append(a)
    for b,p in enumerate(sorted(z['race_list'],key=lambda x:int(x.get('course') or 99)),1):
        pre=f'艇{b}_'
        card.update({
          pre+'登録番号':p.get('player_no',''), pre+'選手名':p.get('player_name',''), pre+'級別':p.get('kyubetsu',''),
          pre+'全国平均ST':norm_st(p.get('ave_start')), pre+'全国勝率':p.get('zenkoku_shoritsu',''), pre+'全国2連対率':p.get('zenkoku_niren',''), pre+'全国3連対率':p.get('zenkoku_sanren',''),
          pre+'当地勝率':p.get('touchi_shoritsu',''), pre+'当地2連対率':p.get('touchi_niren',''), pre+'当地3連対率':p.get('touchi_sanren',''),
          pre+'モーター番号':p.get('motor',''), pre+'モーター2連対率':p.get('motor_niren',''), pre+'モーター3連対率':p.get('motor_sanren',''),
          pre+'ボート番号':p.get('boat',''), pre+'ボート2連対率':p.get('boat_niren',''), pre+'ボート3連対率':p.get('boat_sanren',''),
          pre+'早見':p.get('hayami',''), pre+'F本数':p.get('flying',''), pre+'L本数':p.get('late0','') or 0,
        })
        hist=sorted(mh.get(int(p['player_no']),[]),key=lambda a:(int(a.get('hiduke') or 0),int(a.get('race_no') or 0)))
        for j,a in enumerate(hist[-14:]):
            d=j//2+1; ss=j%2+1
            card[f'{pre}節D{d}走{ss}_R番号']=a.get('race_no','')
            card[f'{pre}節D{d}走{ss}_進入']=a.get('shinnyu','')
            card[f'{pre}節D{d}走{ss}_枠']=a.get('course','')
            card[f'{pre}節D{d}走{ss}_ST']=a.get('start','')
            card[f'{pre}節D{d}走{ss}_着順']=a.get('rank','')
    return card

def find_kako(entries,pn,course):
    cand=[x for x in entries if str(x.get('player_no'))==str(pn) and int(x.get('course') or 0)==course and int(x.get('type') or 0)==0 and int(x.get('grade') or 0)==0]
    return cand[0] if cand else None

def make_waku(jo,rno,z):
    code=f'{DAY}{jo:02d}{rno:02d}'; w={'レースコード':code,'レース日':'2026-09-11','レース場コード':f'{jo:02d}','レース回':str(rno)}
    kk=z.get('kako_list',{}).get('player_kako10',[])
    players=sorted(z['race_list'],key=lambda x:int(x.get('course') or 99))
    for b,p in enumerate(players,1):
        a=find_kako(kk,p.get('player_no'),b)
        if not a: raise RuntimeError(f'kako missing {code} b{b} pn={p.get("player_no")}')
        pre=f'艇{b}_'; w[pre+'選手名']=p.get('player_name','')
        w[pre+'枠番別勝率']=valnum(a.get('shoritsu_ave'),100)
        w[pre+'枠番別平均ST']=valnum(a.get('start_ave'),100)
        w[pre+'枠番別平均スタート順']=valnum(a.get('st_junban_ave'),100)
        for k in range(1,11):
            s=f'{k:02d}'; w[f'{pre}過去{k}走_着順']=a.get(f'rank_{s}',''); w[f'{pre}過去{k}走_進入']=a.get(f'shinnyuu_{s}',''); w[f'{pre}過去{k}走_グレード']=''
    return w

def write_csv(path,rs):
    fields=[]; seen=set()
    for r in rs:
        for k in r:
            if k not in seen:seen.add(k);fields.append(k)
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rs)

def main():
    s=requests.Session(); s.headers.update({'User-Agent':'Mozilla/5.0 (compatible; v288-pre-scan/1.0)','Accept':'text/html,application/json'})
    cards=[];waku=[]; failed=[]; detail_n=0
    for jo in VENUES:
        try:referer,token,meta=get_meta(s,jo)
        except Exception as e:failed.append((jo,'meta',str(e)));continue
        got=0
        for rno in range(1,13):
            try:
                z=detail(s,jo,rno,referer,token,meta)
                if not z: failed.append((jo,rno,'detail empty'));continue
                detail_n+=1
                players=sorted(z['race_list'],key=lambda x:int(x.get('course') or 99)); mt=meeting(s,jo,rno,referer,meta,players)
                c=make_card(jo,rno,z,mt); w=make_waku(jo,rno,z)
                cards.append(c); waku.append(w); got+=1
                time.sleep(.05)
            except Exception as e:failed.append((jo,rno,str(e)))
        print(f'JCD{jo:02d}: {got}/12 complete PRE rows',flush=True)
    write_csv(OUT/'race_cards.csv',cards);write_csv(OUT/'waku10.csv',waku)
    print('DETAIL_TOTAL',detail_n,'COMPLETE',len(cards),'WAKU',len(waku),'SKIPPED',len(failed),flush=True)
    for x in failed[:30]:print('SKIP',x,flush=True)
    if len(cards)<120 or len(waku)!=len(cards):raise RuntimeError('insufficient complete current inputs')
if __name__=='__main__':main()
