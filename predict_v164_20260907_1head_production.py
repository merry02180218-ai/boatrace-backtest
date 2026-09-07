"""v164: 2026-09-07 production 1-head scan.

Canonical production pipeline:
Legacy PRE top5 -> v109 S-only (p>=.72, boat1 exhibition course1) -> v162 top7.
No result/payout/current final odds are read.
"""
from __future__ import annotations
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta, datetime
from zoneinfo import ZoneInfo
import requests
from bs4 import BeautifulSoup

from backtest import rows
from analyze_v108_1head_feasibility import feature_row, bycode, st_bias, update_st
from analyze_v109_1head_monthly_walkforward import fit as fit109, xmatrix, ii, ff
from analyze_v121_1head_six_month_top5 import fit_pre, xpre
from analyze_v162_1head_pair_direct import fit_pair, pair_order

HD=date(2026,9,7); HD8='20260907'; TRAIN_END='2026-08-31'
SRC='analysis_v108_1head_feasibility.csv'
OUT='prediction_v164_20260907_1head_production.csv'
SUMMARY='summary_v164_20260907_1head_production.md'
S_CUT=.72
VENUE_NAMES={'01':'桐生','02':'戸田','03':'江戸川','04':'平和島','05':'多摩川','06':'浜名湖','07':'蒲郡','08':'常滑','09':'津','10':'三国','11':'びわこ','12':'住之江','13':'尼崎','14':'鳴門','15':'丸亀','16':'児島','17':'宮島','18':'徳山','19':'下関','20':'若松','21':'芦屋','22':'福岡','23':'唐津','24':'大村'}
UA={'User-Agent':'Mozilla/5.0 (compatible; boatrace-research/1.0)'}

def read_csv(path):
    with open(path,encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def race_no(x):
    s=str(x or '').strip().upper().replace('R','')
    return ii(s,0)

def fetch_st_day(d):
    return d,rows(f"data/previews/stt/{d.strftime('%Y/%m/%d')}.csv")

def exact_prior_st_bias():
    ds=[];d=date(2025,10,1)
    while d<HD:
        ds.append(d);d+=timedelta(days=1)
    got={}
    with ThreadPoolExecutor(max_workers=14) as ex:
        fs=[ex.submit(fetch_st_day,d) for d in ds]
        for i,f in enumerate(as_completed(fs),1):
            try:
                dd,z=f.result();got[dd]=z
            except Exception:
                pass
            if i%60==0:print('prior STT days',i,'/',len(ds),flush=True)
    sums={b:[] for b in range(1,7)};allv=[]
    for d in sorted(got):update_st(got[d],sums,allv)
    return st_bias(sums,allv),len(got)

def official_deadline(jcd,rno):
    try:
        u=f'https://www.boatrace.jp/owpc/pc/race/racelist?rno={rno}&jcd={jcd}&hd={HD8}'
        s=BeautifulSoup(requests.get(u,headers=UA,timeout=15).text,'html.parser')
        tables=s.find_all('div',class_='table1')
        if not tables:return ''
        tds=tables[0].find('tbody').find_all('td')
        return tds[rno].get_text(strip=True) if len(tds)>rno else ''
    except Exception:return ''

def main():
    train=[r for r in read_csv(SRC) if ii(r.get('valid_result'))==1 and r.get('date','')<=TRAIN_END]
    pre_model=fit_pre(train)
    live_model=fit109(train)
    pair_model,pair_train_n=fit_pair(train)
    bias,bias_days=exact_prior_st_bias()

    y=HD.strftime('%Y/%m/%d')
    cards=rows(f'data/programs/race_cards/{y}.csv')
    waku=bycode(rows(f'data/programs/waku10/{y}.csv'))
    tkz=bycode(rows(f'data/previews/tkz/{y}.csv'))
    stt=bycode(rows(f'data/previews/stt/{y}.csv'))
    orig=bycode(rows(f'data/previews/original_exhibition/{y}.csv'))

    pool=[]
    for card in cards:
        code=card.get('レースコード','')
        if not code or code not in waku:continue
        pre_row=feature_row(HD.isoformat(),card,waku[code],{},{},{},bias)
        if pre_row is None:continue
        pp=float(pre_model.predict_proba(xpre([pre_row]))[0,1])
        venue=str(card.get('レース場コード','')).zfill(2)
        rno=race_no(card.get('レース回'))
        pool.append((pp,code,card,pre_row,venue,rno))

    pool.sort(key=lambda z:(-z[0],z[1]))
    watch=pool[:5]
    now=datetime.now(ZoneInfo('Asia/Tokyo'))
    out=[]
    for rank,(pp,code,card,pre_row,venue,rno) in enumerate(watch,1):
        complete=code in tkz and code in stt and code in orig
        deadline=''
        for m in (tkz,stt,orig):
            x=(m.get(code,{}).get('締切時刻') or '').strip()
            if x:deadline=x;break
        if not deadline:deadline=official_deadline(venue,rno)
        name=(card.get('艇1_選手名') or '').strip()
        status='PENDING_EXHIBITION';p109='';decision='WAIT';tickets='';entry='missing'
        if complete:
            entry='same' if ii(stt[code].get('艇1_コース'))==1 else 'changed'
            live=feature_row(HD.isoformat(),card,waku[code],tkz,stt,orig,bias)
            if live is None:
                status='ENTRY_CHANGED_EXCLUDE';decision='SKIP'
            else:
                p=float(live_model.predict_proba(xmatrix([live]))[0,1]);p109=f'{p:.8f}'
                status='LIVE_FINAL'
                if p>=S_CUT:
                    decision='BUY'
                    tickets=';'.join(pair_order(live,pair_model,1.0)[:7])
                else:
                    decision='SKIP'
        out.append({'pre_rank':rank,'pre_p':f'{pp:.8f}','race_code':code,'venue':venue,'venue_name':VENUE_NAMES.get(venue,venue),'race':rno,'deadline':deadline,'boat1_name':name,'status':status,'entry_status':entry,'p109':p109,'decision':decision,'v162_top7':tickets})

    out.sort(key=lambda r:(r['deadline'] or '99:99',r['pre_rank']))
    with open(OUT,'w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(out[0].keys()));w.writeheader();w.writerows(out)

    L=['# v164 2026-09-07 1号艇 production scan','',
       '- Production: **Legacy PRE top5 -> v109 S-only (>=72%) -> v162 top7**.',
       '- No result/payout/final odds used.','',
       f'- scan JST: **{now:%Y-%m-%d %H:%M:%S}**',
       f'- historical train: **{len(train):,}R** through {TRAIN_END}',
       f'- v162 pair training head wins: **{pair_train_n:,}**',
       f'- prior ST-bias days fetched: **{bias_days}**','',
       '## 今日のPRE top5（締切順）','|締切|場|R|PRE順位|①|PRE p|状態|p109|判定|','|---|---|---:|---:|---|---:|---|---:|---|']
    for r in out:
        ptxt=f"{100*float(r['p109']):.1f}%" if r['p109'] else '-'
        L.append(f"|{r['deadline']}|{r['venue_name']}|{r['race']}R|{r['pre_rank']}|{r['boat1_name']}|{100*float(r['pre_p']):.1f}%|{r['status']}|{ptxt}|{r['decision']}|")
        if r['decision']=='BUY':
            L.append('')
            L.append(f"### {r['venue_name']}{r['race']}R v162 上位7点")
            for i,t in enumerate(r['v162_top7'].split(';'),1):L.append(f'{i}. {t}')
    L+=['','## 運用','- PENDING_EXHIBITION はまだ正式判定しない。展示・オリジナル展示公開後に再計算。','- LIVE_FINAL でも p109<72% は見送り。','- BUYは結果確認前にv162上位7点を凍結する。']
    open(SUMMARY,'w',encoding='utf-8').write('\n'.join(L)+'\n')
    print('\n'.join(L))

if __name__=='__main__':main()
