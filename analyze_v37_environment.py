import csv
from collections import defaultdict
from datetime import date,timedelta
from backtest_v34_tilt_compare import *

TR0=date(2026,6,1);TR1=date(2026,7,15);VA0=date(2026,7,16);VA1=date(2026,8,2);TE0=date(2026,8,3);TE1=date(2026,9,2)
DIR={1:'N',2:'NE',3:'E',4:'SE',5:'S',6:'SW',7:'W',8:'NW'}
VENUE={1:'桐生',2:'戸田',3:'江戸川',4:'平和島',5:'多摩川',6:'浜名湖',7:'蒲郡',8:'常滑',9:'津',10:'三国',11:'びわこ',12:'住之江',13:'尼崎',14:'鳴門',15:'丸亀',16:'児島',17:'宮島',18:'徳山',19:'下関',20:'若松',21:'芦屋',22:'福岡',23:'唐津',24:'大村'}
# Tide is intentionally not fabricated from results. Current repo has no tide snapshot family.
# v37 therefore validates wind/wave using cutoff-5min sui only and reports tide as unavailable for historical model backtest.

def spdbin(x):
    if x is None:return 'missing'
    return '0-2m' if x<=2 else '3-4m' if x<=4 else '5m+'

def envrow(code,sui):
    s=sui.get(code,{})
    try: ws=float(s.get('風速(m)'))
    except: ws=None
    try: wd=int(float(s.get('風向')))
    except: wd=None
    try: wave=float(s.get('波の高さ(cm)'))
    except: wave=None
    try: v=int(s.get('レース場'))
    except:
        try:v=int(code[8:10])
        except:v=0
    return {'venue':VENUE.get(v,str(v)),'venue_code':v,'wind_speed':ws,'wind_bin':spdbin(ws),'wind_dir':DIR.get(wd,'missing'),'wind_code':wd,'wave_cm':wave}

def collect():
    cache={};hist=defaultdict(list);seen=set();d=PRELOAD_START
    while d<TR0:
        ingest_motor(hist,seen,d)
        if d>=TR0-timedelta(days=12):ingest_prior_day_preview(cache,d)
        d+=timedelta(days=1)
    c4=[];tmp=[]
    while d<=TR1:
        feats=process_features(d,cache,hist);ymd=d.strftime('%Y/%m/%d')
        res={r['レースコード']:r for r in rows(f'data/results/realtime/{ymd}.csv')};sui={r['レースコード']:r for r in rows(f'data/previews/sui/{ymd}.csv')}
        for r,x,s4,s5,dc in feats:
            fr32,z32=feat32(x)
            if fr32['3スタート先行度']>=.72:c4.append(z32['counter4'])
            s3=score3v4(x)
            for m in MODELS:
                fr=get_fr(x,s3,s4,dc,m)
                if m!='4刺され' and not eligible(fr,m,0):continue
                if m=='4刺され' and fr['3スタート先行度']<.72:continue
                tmp.append({'period':'train','date':str(d),'race_code':r['レースコード'],'model':m,'target':target34(res.get(r['レースコード'],{}),m),'counter4':fr.get('counter4',0),**envrow(r['レースコード'],sui)})
        ingest_prior_day_preview(cache,d);ingest_motor(hist,seen,d);d+=timedelta(days=1)
    q3=q(c4,.75);tmp=[z for z in tmp if z['model']!='4刺され' or z['counter4']>=q3]
    out=tmp[:]
    for start,end,label in [(VA0,VA1,'validation'),(TE0,TE1,'latest_month')]:
        while d<start:
            process_features(d,cache,hist);ingest_prior_day_preview(cache,d);ingest_motor(hist,seen,d);d+=timedelta(days=1)
        while d<=end:
            feats=process_features(d,cache,hist);ymd=d.strftime('%Y/%m/%d')
            res={r['レースコード']:r for r in rows(f'data/results/realtime/{ymd}.csv')};sui={r['レースコード']:r for r in rows(f'data/previews/sui/{ymd}.csv')}
            for r,x,s4,s5,dc in feats:
                s3=score3v4(x)
                for m in MODELS:
                    fr=get_fr(x,s3,s4,dc,m)
                    if not eligible(fr,m,q3):continue
                    out.append({'period':label,'date':str(d),'race_code':r['レースコード'],'model':m,'target':target34(res.get(r['レースコード'],{}),m),'counter4':fr.get('counter4',0),**envrow(r['レースコード'],sui)})
            ingest_prior_day_preview(cache,d);ingest_motor(hist,seen,d);d+=timedelta(days=1)
    return out,q3

def rate(a):
    n=len(a);h=sum(z['target'] for z in a);return n,h,(100*h/n if n else 0)

def main():
    data,q3=collect()
    with open('analysis_v37_environment.csv','w',newline='',encoding='utf-8-sig') as f0:
        w=csv.DictWriter(f0,fieldnames=sorted(set().union(*(r.keys() for r in data))));w.writeheader();w.writerows(data)
    L=['# v37 場別・風向/風速/潮 検証','',f'学習 {TR0}〜{TR1} / 検証 {VA0}〜{VA1} / 最新月 {TE0}〜{TE1}。実進入・コース不使用。','',
       '風は previews/sui の締切約5分前スナップショットのみ使用。したがって事前候補抽出には使わず、直前補正専用の検証。',
       '潮位は現行BoatraceCSVに履歴スナップショットが無いため、結果から逆算・捏造せず、このv37では統計バックテスト対象外。別途JMA天文潮位等の「事前に取得可能な予測値」だけで作る必要がある。','',f'4刺され counter4 学習Q3={q3:.3f}','']
    for p in ['train','validation','latest_month']:
        L += [f'## {p} 風速帯','|モデル|風速帯|R|狙い成立|成立率|','|---|---|---:|---:|---:|']
        for m in MODELS:
            for b in ['0-2m','3-4m','5m+']:
                a=[z for z in data if z['period']==p and z['model']==m and z['wind_bin']==b];n,h,r=rate(a);L.append(f'|{m}|{b}|{n}|{h}|{r:.1f}%|')
        L += ['',f'## {p} 風向','|モデル|風向|R|狙い成立|成立率|','|---|---|---:|---:|---:|']
        for m in MODELS:
            for d0 in DIR.values():
                a=[z for z in data if z['period']==p and z['model']==m and z['wind_dir']==d0];n,h,r=rate(a)
                if n>=5:L.append(f'|{m}|{d0}|{n}|{h}|{r:.1f}%|')
    # venue-specific stable cells: enough samples in train and post, same direction vs venue-model base
    post=[z for z in data if z['period'] in ('validation','latest_month')]
    sig=[]
    for m in MODELS:
      for v in sorted({z['venue'] for z in data}):
        trbase=[z for z in data if z['period']=='train' and z['model']==m and z['venue']==v];pobase=[z for z in post if z['model']==m and z['venue']==v]
        if len(trbase)<12 or len(pobase)<8:continue
        _,_,rb1=rate(trbase);_,_,rb2=rate(pobase)
        for b in ['0-2m','3-4m','5m+']:
            tr=[z for z in trbase if z['wind_bin']==b];po=[z for z in pobase if z['wind_bin']==b]
            if len(tr)>=6 and len(po)>=4:
                _,_,r1=rate(tr);_,_,r2=rate(po);up=(r1>rb1 and r2>rb2);dn=(r1<rb1 and r2<rb2)
                if up or dn:sig.append((m,v,'風速'+b,len(tr),r1,rb1,len(po),r2,rb2,'↑' if up else '↓'))
        for d0 in DIR.values():
            tr=[z for z in trbase if z['wind_dir']==d0];po=[z for z in pobase if z['wind_dir']==d0]
            if len(tr)>=6 and len(po)>=4:
                _,_,r1=rate(tr);_,_,r2=rate(po);up=(r1>rb1 and r2>rb2);dn=(r1<rb1 and r2<rb2)
                if up or dn:sig.append((m,v,'風向'+d0,len(tr),r1,rb1,len(po),r2,rb2,'↑' if up else '↓'))
    sig.sort(key=lambda x:abs((x[4]-x[5])+(x[7]-x[8])),reverse=True)
    L += ['','## 場別で学習→後半が同方向だった条件（サンプル条件あり）','|モデル|場|条件|学習R|学習率|場ベース|後半R|後半率|場ベース|方向|','|---|---|---|---:|---:|---:|---:|---:|---:|---|']
    for x in sig[:40]:L.append(f'|{x[0]}|{x[1]}|{x[2]}|{x[3]}|{x[4]:.1f}%|{x[5]:.1f}%|{x[6]}|{x[7]:.1f}%|{x[8]:.1f}%|{x[9]}|')
    open('summary_v37_environment.md','w',encoding='utf-8').write('\n'.join(L)+'\n')
if __name__=='__main__':main()
