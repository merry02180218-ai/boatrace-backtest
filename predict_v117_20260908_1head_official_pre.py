"""2026-09-08 1-head pre-priority scan from BOAT RACE official racelist.

No new model. Uses the frozen v116/v109 fit/cuts, but obtains today's race cards
directly from boatrace.jp because BoatraceCSV's same-day race_cards can lag around midnight.
Current-race exhibition/result/payout/odds are NOT used. Same-frame waku priors are taken
only from dates <= 2026-09-07; missing values fall back to current national figures/defaults.
The output is neutral-pre confirmation PRIORITY only, never formal A/S/BUY.
"""
from __future__ import annotations
import csv, io, re, requests
from bs4 import BeautifulSoup
from datetime import date, timedelta, datetime
from zoneinfo import ZoneInfo
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np
import predict_v116_20260905_1head_live as m

HD=date(2026,9,8); HD8='20260908'; TRAIN_END='2026-08-31'
OUT='prediction_v117_20260908_1head_official_pre.csv'
SUMMARY='summary_v117_20260908_1head_official_pre.md'
BASECSV='https://raw.githubusercontent.com/BoatraceCSV/boatracecsv.github.io/main/'
UA={'User-Agent':'Mozilla/5.0 (compatible; boatrace-research/1.0)'}
VENUES=m.VENUE_NAMES

def ff(x,d=0.0):
    try:return float(x)
    except:return d

def ii(x,d=0):
    try:return int(float(x))
    except:return d

def get_text(url,timeout=20):
    r=requests.get(url,headers=UA,timeout=timeout);r.raise_for_status();return r.text

def csv_rows(url):
    try:
        r=requests.get(url,headers=UA,timeout=15)
        if r.status_code!=200:return []
        return list(csv.DictReader(io.StringIO(r.content.decode('utf-8-sig'))))
    except Exception:return []

def racer_names():
    txt=get_text('https://raw.githubusercontent.com/ryuriki/boatrace-v2/main/config/racers_name.yaml')
    out={}
    for ln in txt.splitlines():
        mm=re.match(r"'?(\d{4})'?:\s*(.+?)\s*$",ln)
        if mm:out[int(mm.group(1))]=mm.group(2).strip()
    return out

def parse_race(jcd,rno,names):
    url=f'https://www.boatrace.jp/owpc/pc/race/racelist?rno={rno}&jcd={jcd}&hd={HD8}'
    soup=BeautifulSoup(get_text(url),'html.parser')
    tables=soup.find_all('div',class_='table1')
    if len(tables)<2:raise ValueError('racelist table missing')
    tds=tables[0].find('tbody').find_all('td')
    deadline=tds[rno].get_text(strip=True) if len(tds)>rno else ''
    bodies=tables[1].find_all('tbody')
    if len(bodies)<6:raise ValueError(f'lane bodies={len(bodies)}')
    lanes={}
    for lane in range(1,7):
        cells=bodies[lane-1].find_all('td')
        if len(cells)<8:raise ValueError(f'cells lane{lane}={len(cells)}')
        info=cells[2].find_all('div',class_='is-fs11')
        racer_text=info[0].get_text(strip=True)
        rid=ii(racer_text.split('/')[0].strip())
        grade=racer_text.split('/')[1].strip() if '/' in racer_text else ''
        c3=[z.strip() for z in cells[3].get_text('\n',strip=True).split('\n') if z.strip()]
        zn=[z.strip() for z in cells[4].get_text('\n',strip=True).split('\n') if z.strip()]
        jl=[z.strip() for z in cells[5].get_text('\n',strip=True).split('\n') if z.strip()]
        mo=[z.strip() for z in cells[6].get_text('\n',strip=True).split('\n') if z.strip()]
        lanes[lane]={'rid':rid,'name':names.get(rid,str(rid)),'grade':grade,
                     'nst':ff(c3[2] if len(c3)>2 else .20,.20),'wr':ff(zn[0] if zn else 0),
                     'local':ff(jl[0] if jl else 0),'motor2':ff(mo[1] if len(mo)>1 else 0),
                     'motor3':ff(mo[2] if len(mo)>2 else 0)}
    return {'jcd':jcd,'rno':rno,'deadline':deadline,'lanes':lanes,'url':url}

def discover_active(names):
    active=[];errs={}
    with ThreadPoolExecutor(max_workers=12) as ex:
        fs={ex.submit(parse_race,j,1,names):j for j in VENUES}
        for f in as_completed(fs):
            j=fs[f]
            try:f.result();active.append(j)
            except Exception as e:errs[j]=str(e)
    return sorted(active),errs

def fetch_hist_day(d):
    y=d.strftime('%Y/%m/%d')
    cards=csv_rows(BASECSV+f'data/programs/race_cards/{y}.csv')
    w10=csv_rows(BASECSV+f'data/programs/waku10/{y}.csv')
    wm={r.get('レースコード',''):r for r in w10}
    got=[]
    for c in cards:
        w=wm.get(c.get('レースコード',''),{})
        for b in range(1,7):
            rid=ii(c.get(f'艇{b}_登録番号'))
            if not rid:continue
            z={'waku_wr':w.get(f'艇{b}_枠番別勝率',''),'waku_st':w.get(f'艇{b}_枠番別平均ST',''),
               'waku_sr':w.get(f'艇{b}_枠番別平均スタート順','')}
            for k in range(1,11):z[f'past{k}']=w.get(f'艇{b}_過去{k}走_着順','')
            got.append((rid,b,z))
    return d,got

def load_latest_same_frame(days=60):
    ds=[HD-timedelta(days=i) for i in range(1,days+1)]
    byday={}
    with ThreadPoolExecutor(max_workers=10) as ex:
        fs=[ex.submit(fetch_hist_day,d) for d in ds]
        for f in as_completed(fs):
            try:d,z=f.result();byday[d]=z
            except Exception:pass
    lookup={}
    for d in sorted(byday,reverse=True):
        for rid,b,z in byday[d]:
            lookup.setdefault((rid,b),z)
    return lookup,len(byday)

def synthetic(r,lookup):
    code=f'{HD8}{r["jcd"]}{r["rno"]:02d}'
    card={'レースコード':code,'レース場コード':r['jcd'],'レース回':str(r['rno'])}
    w={'レースコード':code}
    for b,z in r['lanes'].items():
        card[f'艇{b}_登録番号']=str(z['rid']);card[f'艇{b}_選手名']=z['name'];card[f'艇{b}_級別']=z['grade']
        card[f'艇{b}_全国平均ST']=str(z['nst']);card[f'艇{b}_全国勝率']=str(z['wr']);card[f'艇{b}_当地勝率']=str(z['local'])
        card[f'艇{b}_モーター2連対率']=str(z['motor2']);card[f'艇{b}_モーター3連対率']=str(z['motor3'])
        h=lookup.get((z['rid'],b),{})
        w[f'艇{b}_枠番別勝率']=h.get('waku_wr','') or str(z['wr'])
        w[f'艇{b}_枠番別平均ST']=h.get('waku_st','') or str(z['nst'])
        w[f'艇{b}_枠番別平均スタート順']=h.get('waku_sr','') or '3.5'
        for k in range(1,11):w[f'艇{b}_過去{k}走_着順']=h.get(f'past{k}','')
    return card,w

def main():
    names=racer_names();active,probe_errs=discover_active(names)
    lookup,hist_days=load_latest_same_frame()
    races=[];errs=[]
    with ThreadPoolExecutor(max_workers=16) as ex:
        fs={ex.submit(parse_race,j,r,names):(j,r) for j in active for r in range(1,13)}
        for f in as_completed(fs):
            j,r=fs[f]
            try:races.append(f.result())
            except Exception as e:errs.append((j,r,str(e)))
    races.sort(key=lambda x:(x['jcd'],x['rno']))
    train=[r for r in m.read_csv(m.SRC) if m.ii(r.get('valid_result'))==1 and r.get('date','')<=TRAIN_END]
    model=m.fit_model(train);bias,bias_days=m.exact_prior_st_bias()
    out=[];same=0;total=0
    for r in races:
        card,w=synthetic(r,lookup)
        for b,z in r['lanes'].items():total+=1;same+=int((z['rid'],b) in lookup)
        fr=m.feature_row(HD.isoformat(),card,w,{},{},{},bias)
        p=m.pred(model,fr) if fr is not None else float('nan')
        out.append({'venue':r['jcd'],'venue_name':VENUES[r['jcd']],'race':r['rno'],'deadline':r['deadline'],
                    'boat1_name':r['lanes'][1]['name'],'boat1_grade':r['lanes'][1]['grade'],
                    'p109_neutral_pre':f'{p:.8f}' if np.isfinite(p) else '',
                    'grade_neutral_pre':m.grade(p) if np.isfinite(p) else '-',
                    'source':'BOAT_RACE_OFFICIAL+prior_same_frame_waku'})
    out.sort(key=lambda z:(z['deadline'] or '99:99',z['venue'],z['race']))
    with open(OUT,'w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(out[0].keys()) if out else ['venue']);w.writeheader();w.writerows(out)
    cand=[z for z in out if z['grade_neutral_pre'] in ('A','S')]
    L=['# v117 2026-09-08 1号艇 公式サイト直接取得 PRE優先候補','',
       'BOAT RACE公式 racelist を直接取得し、現行v116/v109モデルへ通した。モデル変更なし。',
       '当日結果・払戻・当日オッズ・当日展示は使用していない。neutral-preは正式A/S/BUYではなく、展示後再計算の優先候補。','',
       f'- scan JST: **{datetime.now(ZoneInfo("Asia/Tokyo")):%Y-%m-%d %H:%M:%S}**',
       f'- active venues: **{len(active)}** ({", ".join(VENUES[j] for j in active)})',f'- official races: **{len(races)}/{len(active)*12}R**',
       f'- active-race fetch errors: **{len(errs)}R**',f'- historical train: **{len(train):,}R** through {TRAIN_END}',
       f'- prior ST-bias days: **{bias_days}**',f'- prior same-frame waku coverage: **{same}/{total} ({100*same/total if total else 0:.1f}%)**',
       f'- neutral-pre A/S priority: **{len(cand)}R**','',
       '## 展示後チェック優先候補','|締切|場|R|1号艇|級|neutral p|仮層|','|---|---|---:|---|---|---:|---|']
    for z in cand:L.append(f"|{z['deadline']}|{z['venue_name']}|{z['race']}R|{z['boat1_name']}|{z['boat1_grade']}|{100*float(z['p109_neutral_pre']):.1f}%|{z['grade_neutral_pre']}|")
    if not cand:L.append('|-|-|-|-|-|-|-|')
    if errs:L+=['','## 取得エラー']+[f'- {VENUES.get(j,j)} {r}R: {e}' for j,r,e in errs]
    open(SUMMARY,'w',encoding='utf-8').write('\n'.join(L)+'\n')
if __name__=='__main__':main()
