"""v116: 2026-09-05 v109 1-head operational live scan.

NOT a new model. v109 architecture/cuts are fixed and refit only on the already-settled
v108 table through 2026-08-31. No Sep-5 result/payout/odds file is read. Final A/S is
emitted only after TKZ + STT + original exhibition are all present and boat 1 remains
course 1. Incomplete races are neutral-preview PRIORITY only, never formal A/S.
"""
from __future__ import annotations
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta, datetime
from zoneinfo import ZoneInfo
import requests
from bs4 import BeautifulSoup
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from backtest import rows
from analyze_v108_1head_feasibility import feature_row, bycode, st_bias, update_st

HD=date(2026,9,5); HD8='20260905'; TRAIN_END='2026-08-31'
SRC='analysis_v108_1head_feasibility.csv'
OUT='prediction_v116_20260905_1head_live.csv'; SUMMARY='summary_v116_20260905_1head_live.md'
A_CUT=.65; S_CUT=.72
VENUE_NAMES={'01':'桐生','02':'戸田','03':'江戸川','04':'平和島','05':'多摩川','06':'浜名湖','07':'蒲郡','08':'常滑','09':'津','10':'三国','11':'びわこ','12':'住之江','13':'尼崎','14':'鳴門','15':'丸亀','16':'児島','17':'宮島','18':'徳山','19':'下関','20':'若松','21':'芦屋','22':'福岡','23':'唐津','24':'大村'}
NUM_FEATURES=['one_grade','one_wr','one_local','one_motor','one_waku_wr','one_nst_strength','one_waku_sr_strength','one_past_win','one_meet_st_strength','one_ex','one_st','one_lap','one_turn','one_straight','one_orig_avg','one_direct','one_score','threat2','threat3','threat4','threat5','threat6','threat23_max','threat_all_max','margin2','margin3','margin23','margin_all','st_margin2','st_margin3','st_margin23','ex_margin23','turn_margin23','straight_margin23']
VENUES=[f'{i:02d}' for i in range(1,25)]
UA={'User-Agent':'Mozilla/5.0 (compatible; boatrace-research/1.0)'}

def ff(x,d=0.0):
    try:return float(x)
    except Exception:return d

def ii(x,d=0):
    try:return int(float(x))
    except Exception:return d

def race_no(x):
    s=str(x or '').strip().upper().replace('R','')
    return ii(s,0)
def read_csv(path):
    with open(path,encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def xmatrix(rs):
    out=[]
    for r in rs:
        row=[ff(r.get(k),0) for k in NUM_FEATURES]; vv=str(r.get('venue','')).zfill(2)
        row.extend(1.0 if vv==v else 0.0 for v in VENUES); out.append(row)
    return np.asarray(out,dtype=float)
def fit_model(train):
    p=Pipeline([('scale',StandardScaler()),('lr',LogisticRegression(C=.5,max_iter=1500,solver='lbfgs'))])
    p.fit(xmatrix(train),[ii(r.get('head_hit')) for r in train]); return p
def pred(model,r):return float(model.predict_proba(xmatrix([r]))[0,1])
def grade(p):return 'S' if p>=S_CUT else ('A' if p>=A_CUT else 'B')

def fetch_st_day(d):return d,rows(f"data/previews/stt/{d.strftime('%Y/%m/%d')}.csv")
def exact_prior_st_bias():
    ds=[];d=date(2025,10,1)
    while d<HD:ds.append(d);d+=timedelta(days=1)
    got={}
    with ThreadPoolExecutor(max_workers=14) as ex:
        fs=[ex.submit(fetch_st_day,d) for d in ds]
        for i,f in enumerate(as_completed(fs),1):
            try:dd,z=f.result();got[dd]=z
            except Exception:pass
            if i%50==0:print('prior STT days',i,'/',len(ds),flush=True)
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
def official_deadlines(cards):
    jobs=[]
    for c in cards:
        j=str(c.get('レース場コード','')).zfill(2);r=race_no(c.get('レース回'))
        if j and r:jobs.append((j,r))
    out={}
    with ThreadPoolExecutor(max_workers=18) as ex:
        fs={ex.submit(official_deadline,j,r):(j,r) for j,r in jobs}
        for f in as_completed(fs):
            j,r=fs[f]
            try:out[(j,r)]=f.result()
            except Exception:out[(j,r)]=''
    return out

def main():
    train=[r for r in read_csv(SRC) if ii(r.get('valid_result'))==1 and r.get('date','')<=TRAIN_END]
    model=fit_model(train); bias,bias_days=exact_prior_st_bias()
    y=HD.strftime('%Y/%m/%d')
    cards=rows(f'data/programs/race_cards/{y}.csv'); waku=bycode(rows(f'data/programs/waku10/{y}.csv'))
    tkz=bycode(rows(f'data/previews/tkz/{y}.csv')); stt=bycode(rows(f'data/previews/stt/{y}.csv')); orig=bycode(rows(f'data/previews/original_exhibition/{y}.csv'))
    deadlines=official_deadlines(cards); now=datetime.now(ZoneInfo('Asia/Tokyo')); out=[]
    for card in cards:
        code=card.get('レースコード','')
        if not code or code not in waku:continue
        venue=str(card.get('レース場コード','')).zfill(2); rno=race_no(card.get('レース回'))
        name=(card.get('艇1_選手名') or '').strip(); g1=(card.get('艇1_級別') or '').strip()
        complete=code in tkz and code in stt and code in orig
        dl=''
        for m in (tkz,stt,orig):
            x=(m.get(code,{}).get('締切時刻') or '').strip()
            if x:dl=x;break
        if not dl:dl=deadlines.get((venue,rno),'')
        provisional=feature_row(HD.isoformat(),card,waku[code],{},{},{},bias)
        ppre=pred(model,provisional) if provisional is not None else float('nan'); ppre_grade=grade(ppre) if np.isfinite(ppre) else '-'
        status='PENDING_EXHIBITION';plive='';glive='';entry='missing'
        if complete:
            entry='same' if ii(stt[code].get('艇1_コース'))==1 else 'changed'
            live=feature_row(HD.isoformat(),card,waku[code],tkz,stt,orig,bias)
            if live is None:status='ENTRY_CHANGED_EXCLUDE'
            else:
                p=pred(model,live);plive=f'{p:.8f}';glive=grade(p);status='LIVE_FINAL'
        past=''
        if dl:
            try:
                t=datetime.strptime(HD.isoformat()+' '+dl,'%Y-%m-%d %H:%M').replace(tzinfo=ZoneInfo('Asia/Tokyo'));past='1' if t<=now else '0'
            except Exception:pass
        out.append({'race_code':code,'venue':venue,'venue_name':VENUE_NAMES.get(venue,venue),'race':rno,'deadline':dl,'boat1_name':name,'boat1_grade':g1,'status':status,'entry_status':entry,'preview_complete':int(complete),'p109_live':plive,'grade_live':glive,'p109_neutral_pre':f'{ppre:.8f}' if np.isfinite(ppre) else '','grade_neutral_pre':ppre_grade,'closed_at_scan':past})
    out.sort(key=lambda r:(r['deadline'] or '99:99',r['venue'],r['race']))
    fs=list(out[0].keys()) if out else []
    with open(OUT,'w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=fs);w.writeheader();w.writerows(out)
    live_targets=[r for r in out if r['status']=='LIVE_FINAL' and r['grade_live'] in ('A','S')]
    pending_pre=[r for r in out if r['status']=='PENDING_EXHIBITION' and r['grade_neutral_pre'] in ('A','S')]
    changed=[r for r in out if r['status']=='ENTRY_CHANGED_EXCLUDE']
    L=['# v116 2026-09-05 1号艇モデル live scan','', '**モデル変更なし**。v109 architecture、A=65% / S=72%を固定。学習ラベルは2026-08-31まで。','当日結果・払戻・オッズは読んでいない。LIVE_FINALはTKZ/STT/オリジナル展示が全て公開済みで、1号艇が展示1コースのレースだけ。','展示未公開レースの neutral-pre は展示系を0.5に置いた「確認優先度」で、正式A/Sではない。展示公開後に必ず再計算する。','',f'- scan JST: **{now:%Y-%m-%d %H:%M:%S}**',f'- historical train: **{len(train):,}R** through {TRAIN_END}',f'- prior ST-bias days fetched: **{bias_days}**',f'- today cards: **{len(out)}R**',f'- live final A/S targets at scan: **{len(live_targets)}R**',f'- pending neutral-pre A/S priority: **{len(pending_pre)}R**',f'- entry changed exclusions: **{len(changed)}R**','', '## 現時点で正式A/S','|締切|場|R|1号艇|級|p109|判定|締切済|','|---|---|---:|---|---|---:|---|---|']
    for r in live_targets:L.append(f"|{r['deadline']}|{r['venue_name']}|{r['race']}R|{r['boat1_name']}|{r['boat1_grade']}|{100*float(r['p109_live']):.1f}%|{r['grade_live']}|{'済' if r['closed_at_scan']=='1' else '未'}|")
    if not live_targets:L.append('|-|-|-|-|-|-|-|-|')
    L+=['','## 今後の展示待ち・neutral-pre A/S（正式判定ではない）','|締切|場|R|1号艇|級|neutral p|仮層|','|---|---|---:|---|---|---:|---|']
    for r in pending_pre:L.append(f"|{r['deadline']}|{r['venue_name']}|{r['race']}R|{r['boat1_name']}|{r['boat1_grade']}|{100*float(r['p109_neutral_pre']):.1f}%|{r['grade_neutral_pre']}|")
    if not pending_pre:L.append('|-|-|-|-|-|-|-|')
    if changed:
        L+=['','## 1コース変更で除外']
        for r in changed:L.append(f"- {r['deadline']} {r['venue_name']}{r['race']}R ①{r['boat1_name']}")
    open(SUMMARY,'w',encoding='utf-8').write('\n'.join(L)+'\n')
if __name__=='__main__':main()
