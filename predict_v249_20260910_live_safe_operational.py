#!/usr/bin/env python3
"""2026-09-10 LIVE-safe operational PRE classifier for 3-head.

IMPORTANT: this is an operational bridge, not byte-identical historical v249.
It uses only pre-exhibition/static inputs available before the race, builds a 3-head
structural score on the same official-data primitives used by the daily v107 scanner,
and calibrates percentile against Aug 1..Sep 9 historical races plus Sep 10 current
universe. Historical v249 grade cuts are preserved: S>=0.70, A>=0.20, B<0.20.
No current exhibition/result/payout/odds are used.
"""
from datetime import date,timedelta
from concurrent.futures import ThreadPoolExecutor,as_completed
import csv,io,requests
import pandas as pd
import predict_v107_20260905_official_fullscan as m

m.HD='20260910'
S_CUT=.70; A_CUT=.20
OUT='pred_v249_20260910_live_safe_operational.csv'
SUM='prediction_v249_20260910_live_safe_operational.md'
UA={'User-Agent':'Mozilla/5.0 (compatible; boatrace-research/1.0)'}
BASE='https://raw.githubusercontent.com/BoatraceCSV/boatracecsv.github.io/main/'

def get_csv(url):
    try:
        r=requests.get(url,headers=UA,timeout=15)
        if r.status_code!=200:return []
        return list(csv.DictReader(io.StringIO(r.content.decode('utf-8-sig'))))
    except Exception:return []

def f(x,d=0.):
    try:return float(x)
    except:return d

def i(x,d=0):
    try:return int(float(x))
    except:return d

def score3(x):
    a,b,c=x[1],x[2],x[3]
    s3=m.strength(c); se3=m.st_edge(b,c); ww2=m.wallweak(b,c); iw1=m.c01((7.5-a['waku_wr'])/6)
    score_m=(s3+se3+ww2)/3
    score_s=(s3+se3+iw1+ww2)/4
    return max(score_m,score_s),('3まくり' if score_m>=score_s else '3まくり差し')

def hist_day(d):
    y=d.strftime('%Y/%m/%d')
    cards=get_csv(BASE+f'data/programs/race_cards/{y}.csv')
    waku=get_csv(BASE+f'data/programs/waku10/{y}.csv')
    wm={r.get('レースコード'):r for r in waku}
    out=[]
    for card in cards:
        code=str(card.get('レースコード','')).zfill(12); w=wm.get(card.get('レースコード'),{})
        lanes={}
        for b in range(1,7):
            wr=f(card.get(f'艇{b}_全国勝率'),5.0); nst=f(card.get(f'艇{b}_全国平均ST'),.18)
            # historical CSV locality is not guaranteed stable across schema versions;
            # use national win rate as deterministic PRE fallback for both reference/current bridge score.
            lanes[b]={'wr':wr,'local':wr,'nst':nst,
                      'waku_wr':f(w.get(f'艇{b}_枠番別勝率'),wr),
                      'waku_st':f(w.get(f'艇{b}_枠番別平均ST'),nst)}
        sc,route=score3(lanes); out.append({'date':d.isoformat(),'race_code':code,'score':sc,'route':route})
    return out

def main():
    names=m.racer_names(); active,_=m.discover_active(names)
    # Current races from BOAT RACE official.
    races=[]
    with ThreadPoolExecutor(max_workers=16) as ex:
        fs={ex.submit(m.parse_race,j,r,names):(j,r) for j in active for r in range(1,13)}
        for z in as_completed(fs):
            try:races.append(z.result())
            except Exception:pass
    # Waku reference strictly ends Sep 9.
    ds=[];d=date(2026,9,9)
    for _ in range(45):ds.append(d);d-=timedelta(days=1)
    got=[]
    with ThreadPoolExecutor(max_workers=10) as ex:
        fs=[ex.submit(m.fetch_hist_day,d) for d in ds]
        for z in as_completed(fs):
            try:got.append(z.result())
            except Exception:pass
    got.sort(key=lambda z:z[0]); lookup={}
    for _,items in got:
        for rid,b,z in items:lookup[(rid,b)]=z
    m.attach_waku(races,lookup)

    cur=[]
    for r in races:
        # normalize current locality to national to match historical operational bridge reference.
        xx={b:dict(z) for b,z in r['lanes'].items()}
        for b in xx:xx[b]['local']=xx[b]['wr']
        sc,route=score3(xx)
        cur.append({'date':'2026-09-10','venue':r['venue'],'jcd':r['jcd'],'race':r['rno'],'deadline':r['deadline'],
                    'race_code':f"20260910{int(r['jcd']):02d}{int(r['rno']):02d}",'score':sc,'route':route,
                    'name3':r['lanes'][3]['name'],'grade3':r['lanes'][3]['grade']})

    # LIVE-safe percentile reference: all Aug races + Sep 1..9 completed static programs + today's 132 static rows.
    h=[]; d=date(2026,8,1)
    days=[]
    while d<=date(2026,9,9):days.append(d);d+=timedelta(days=1)
    with ThreadPoolExecutor(max_workers=12) as ex:
        fs=[ex.submit(hist_day,d) for d in days]
        for z in as_completed(fs):
            try:h.extend(z.result())
            except Exception:pass
    ref_scores=[z['score'] for z in h]+[z['score'] for z in cur]
    ref=pd.Series(ref_scores,dtype=float)
    def pct(s):
        # empirical CDF, LIVE-safe: no future September rows.
        return float((ref<=s).mean()) if len(ref) else float('nan')
    for z in cur:
        z['pct']=pct(z['score']); z['grade']='S' if z['pct']>=S_CUT else ('A' if z['pct']>=A_CUT else 'B')
        z['selected']=int(z['grade'] in ('S','A'))
    q=pd.DataFrame(cur).sort_values(['selected','pct'],ascending=[False,False]);q.to_csv(OUT,index=False,encoding='utf-8-sig')
    sel=q[q.selected==1]
    L=['# 2026-09-10 3頭モデル 展示前候補（v249 LIVE-safe運用版）','',
       '- BOAT RACE公式の9/10出走表を使用。結果・払戻・実進入・当日展示・当日オッズは不使用。',
       '- Percentile reference = 2026-08-01..09-09 historical static programs + 09-10 current static universe only。未来9月レースは不使用。',
       '- Historical v249 grade cuts preserved: S>=0.70, A>=0.20, B<0.20。',
       '- IMPORTANT: historical v249の全f__特徴量を今日へ完全再現したものではなく、daily official scannerのPRE primitivesを用いたLIVE-safe operational bridge。正式historical v249と同一とは扱わない。','',
       f'- current universe: {len(q)}R / reference historical rows: {len(h)} / S+A: {len(sel)}R','',
       '|場|R|締切|3号艇|級|route|score|pct|grade|','|---|---:|---|---|---|---|---:|---:|---|']
    for _,z in sel.sort_values('pct',ascending=False).iterrows():
        L.append(f"|{z.venue}|{int(z.race)}R|{z.deadline}|{z.name3}|{z.grade3}|{z.route}|{z.score:.4f}|{z.pct:.4f}|{z.grade}|")
    open(SUM,'w',encoding='utf-8').write('\n'.join(L)+'\n');print('\n'.join(L))
if __name__=='__main__':main()
