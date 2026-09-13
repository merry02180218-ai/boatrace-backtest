#!/usr/bin/env python3
"""Build the six current-exhibition rows used by frozen HEAD4 v283.

Result-blind sources only:
- official BOAT RACE beforeinfo: display time
- BOATCAST start display
- BOATCAST original exhibition
Prior-only ST lane bias is rebuilt from repository STT snapshots strictly before
the target day using the v90 update order. No result/payout/odds endpoint is read.
"""
from __future__ import annotations
import argparse,json,math
from collections import defaultdict
from datetime import date,timedelta
from pathlib import Path
from statistics import mean
from typing import Any
from bs4 import BeautifulSoup

from backtest import rows
from backtest_v3 import CORR
from backtest_v51_lane_corrected_tickets import norm_metric,rank_scores
from build_4head_post_live import (_fetch,beforeinfo_url,boatcast_st_url,boatcast_orig_url,
    parse_boatcast_st,parse_boatcast_original,BOATCAST)
from fetch_4head_beforeinfo_live import validate_target

PRELOAD=date(2025,10,1)
class ExhibitionBuildError(RuntimeError): pass

def _clean(v:Any)->str:return ' '.join(str(v or '').replace('\u3000',' ').split())
def _num(v:Any)->float|None:
    s=_clean(v).replace('度','').replace('+','')
    if not s or s in {'-','--','－'}:return None
    if s.startswith('.'):s='0'+s
    if s.startswith('-.'):s='-0'+s[1:]
    try:
        x=float(s);return x if math.isfinite(x) else None
    except Exception:return None

def parse_display_times(html:str)->dict[int,float]:
    soup=BeautifulSoup(html,'html.parser');found=[]
    for table in soup.find_all('table'):
        trs=table.find_all('tr');idx=None
        for tr in trs:
            cells=[_clean(c.get_text(' ',strip=True)) for c in tr.find_all(['th','td'])]
            for i,x in enumerate(cells):
                if '展示タイム' in x:idx=i;break
            if idx is not None:break
        if idx is None:continue
        z={}
        for tr in trs:
            cells=[_clean(c.get_text(' ',strip=True)) for c in tr.find_all(['th','td'])]
            if not cells or idx>=len(cells):continue
            try:b=int(cells[0])
            except Exception:continue
            if 1<=b<=6:
                v=_num(cells[idx])
                if v is not None:z[b]=v
        if set(z)==set(range(1,7)):found.append(z)
    if len(found)!=1:raise ExhibitionBuildError(f'display time table ambiguous/missing: {len(found)}')
    return found[0]

def st_bias_before(target:date)->dict[int,float]:
    sums=defaultdict(list);allv=[];d=PRELOAD
    while d<target:
        ymd=d.strftime('%Y/%m/%d')
        for r in rows(f'data/previews/stt/{ymd}.csv'):
            for b in range(1,7):
                v=_num(r.get(f'艇{b}_スタート展示'))
                if v is not None and -.30<v<1.0:sums[b].append(v);allv.append(v)
        d+=timedelta(days=1)
    g=mean(allv) if allv else .15
    return {b:(mean(sums[b])-g if sums[b] else 0.0) for b in range(1,7)}

def original_corrected(labels:list[str],raw:dict[int,list[float|None]])->dict[int,dict[str,float]]:
    out={b:{'lap':.5,'turn':.5,'straight':.5,'avg':.5} for b in range(1,7)};per={b:[] for b in range(1,7)}
    for k,label in enumerate(labels):
        mk=norm_metric(label);vals={}
        for b in range(1,7):
            v=raw[b][k] if k<len(raw[b]) else None
            vals[b]=(v+CORR[b].get(mk,0)) if v is not None else None
        sc=rank_scores(vals,True)
        for b in range(1,7):
            if vals[b] is None:continue
            per[b].append(float(sc[b]))
            if mk=='直線':out[b]['straight']=float(sc[b])
            elif mk=='一周':out[b]['lap']=float(sc[b])
            elif mk in ('まわり足','回り足'):out[b]['turn']=float(sc[b])
    for b in range(1,7):
        if per[b]:out[b]['avg']=sum(per[b])/len(per[b])
    return out

def build_from_sources(hd:str,jcd:int,rno:int,before_html:str,st_text:str,orig_text:str,bias:dict[int,float])->dict[str,Any]:
    validate_target(hd,jcd,rno)
    disp=parse_display_times(before_html)
    exraw={b:disp[b]+CORR[b]['展示'] for b in range(1,7)};ex=rank_scores(exraw,True)
    st_raw=parse_boatcast_st(st_text)
    if any(st_raw[b] is None for b in range(1,7)):raise ExhibitionBuildError('start display incomplete/L')
    corr={b:float(st_raw[b])-float(bias.get(b,0.0)) for b in range(1,7)}
    st_strength=rank_scores(corr,True)
    labels,oraw=parse_boatcast_original(orig_text);os=original_corrected(labels,oraw)
    boats={}
    for b in range(1,7):
        boats[str(b)]={
          'cur_ex':float(ex[b]),'cur_st':float(st_strength[b]),
          'cur_orig_lap':float(os[b]['lap']),'cur_orig_turn':float(os[b]['turn']),
          'cur_orig_straight':float(os[b]['straight']),'cur_orig_avg':float(os[b]['avg']),
        }
    return {'schema':'head4_v283_current_exhibition_live_v1','race_code':f'{hd}{jcd:02d}{rno:02d}','current_boats':boats,
            'st_bias':{str(k):float(v) for k,v in bias.items()},'result_blind':True,'odds_used':False}

def fetch_and_build(hd:str,jcd:int,rno:int,timeout:int=20)->dict[str,Any]:
    target=date(int(hd[:4]),int(hd[4:6]),int(hd[6:8]));bias=st_bias_before(target)
    bu=beforeinfo_url(hd,jcd,rno);su=boatcast_st_url(hd,jcd,rno);ou=boatcast_orig_url(hd,jcd,rno)
    before=_fetch(bu,'https://www.boatrace.jp/owpc/pc/race/beforeinfo',timeout)
    st=_fetch(su,f'{BOATCAST}/hp_txt/{jcd:02d}/bc_j_stt_',timeout)
    orig=_fetch(ou,f'{BOATCAST}/txt/{jcd:02d}/bc_oriten_',timeout)
    return build_from_sources(hd,jcd,rno,before,st,orig,bias)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--date',required=True);ap.add_argument('--jcd',type=int,required=True);ap.add_argument('--race',type=int,required=True);ap.add_argument('--out',required=True);ap.add_argument('--timeout',type=int,default=20);a=ap.parse_args()
    z=fetch_and_build(a.date,a.jcd,a.race,a.timeout);Path(a.out).write_text(json.dumps(z,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({'status':'READY','race_code':z['race_code'],'out':a.out},ensure_ascii=False))
if __name__=='__main__':main()
