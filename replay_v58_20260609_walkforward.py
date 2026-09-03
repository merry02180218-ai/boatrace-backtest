"""v58: 2026-06-09 strict walk-forward replay.

Purpose: replay June 9 without using any information after June 8 for model fitting.
- Base candidates: v20 structural RULES, pre-race only.
- For Jun1..Jun8: each day is frozen, then result is learned for subsequent days.
- ST exhibition frame bias for each day uses prior days only; Jun9 uses Jun1..Jun8 only.
- Current exhibition/original exhibition is frame-corrected; actual entry/course and STT course fields are unused.
- od3 archive starts Jul19, so Jun9 has NO EV/odds purchase decision. A 6-ticket proxy is shown only for diagnostic opponent accuracy.
"""
import csv, math
from collections import defaultdict
from datetime import date,timedelta
from statistics import mean

from backtest import rows
from backtest_v3 import ingest_motor
from backtest_v4 import ingest_prior_day_preview, score3v4
from backtest_v5_ev import PRELOAD_START, process_features
from backtest_v20_week import RULES, HEAD, features, passes, score_for, target
from backtest_v51_lane_corrected_tickets import ff, corrected_direct, opp_place_score, tickets_for
from analyze_v23_20260902_daypreview import by_code

START=date(2026,6,1);TARGET=date(2026,6,9)
CUTS=[50,55,60,65,70]


def wilson(k,n,z=1.0):
    if not n:return 0
    p=k/n;zz=z*z;den=1+zz/n
    return (p+zz/(2*n)-z*math.sqrt((p*(1-p)+zz/(4*n))/n))/den


def bias_from(sums,allv):
    g=mean(allv) if allv else .15
    return {b:(mean(sums[b])-g if sums[b] else 0.0) for b in range(1,7)}


def ingest_stt(day,sums,allv):
    ymd=day.strftime('%Y/%m/%d')
    for r in rows(f'data/previews/stt/{ymd}.csv'):
        for b in range(1,7):
            v=ff(r.get(f'艇{b}_スタート展示'))
            if v is not None and -.30<v<1.0:sums[b].append(v);allv.append(v)


def direct_comp(m,ex,st,os):
    if m=='3まくり':
        z=os[3];return .30*ex.get(3,.5)+.30*st.get(3,.5)+.25*z['straight']+.15*z['avg']
    if m=='3まくり差し':
        z=os[3];return .20*ex.get(3,.5)+.25*st.get(3,.5)+.18*z['lap']+.25*z['turn']+.12*z['avg']
    if m=='4カドまくり':
        z=os[4];return .30*ex.get(4,.5)+.32*st.get(4,.5)+.25*z['straight']+.13*z['avg']
    z4=os[4];z5=os[5]
    attack4=.32*ex.get(4,.5)+.38*st.get(4,.5)+.18*z4['straight']+.12*z4['avg']
    take5=.22*ex.get(5,.5)+.17*st.get(5,.5)+.27*z5['lap']+.27*z5['turn']+.07*z5['avg']
    return .45*attack4+.55*take5


def combined_score(base,direct):
    # Fixed simple blend for this early walk-forward replay; no post-Jun8 fitting.
    return .55*base+.45*(100*direct)


def choose_cut(samples,m):
    best=None;tab=[]
    for c in CUTS:
        q=[z for z in samples[m] if z['score']>=c];n=len(q);h=sum(z['target'] for z in q);wl=wilson(h,n)
        tab.append((c,n,h,100*h/n if n else 0,100*wl))
        if n>=6:
            key=(wl,h/n if n else 0,n,-c)
            if best is None or key>best[0]:best=(key,c)
    return best[1] if best else 55,tab


def freeze_day(day,cache,hist,stbias):
    feats=process_features(day,cache,hist);ymd=day.strftime('%Y/%m/%d')
    tkz=by_code(f'data/previews/tkz/{ymd}.csv');stt=by_code(f'data/previews/stt/{ymd}.csv');orig=by_code(f'data/previews/original_exhibition/{ymd}.csv')
    cards=by_code(f'data/programs/race_cards/{ymd}.csv');w10=by_code(f'data/programs/waku10/{ymd}.csv')
    out=[]
    for r,x,s4,s5,dc in feats:
        s3=score3v4(x);code=r['レースコード'];ex,st,os=corrected_direct(code,tkz,stt,orig,stbias)
        for m,rule in RULES.items():
            fr=features(x,s3,s4,dc,m)
            if not passes(fr,rule):continue
            base=score_for(x,s3,s4,m);ds=direct_comp(m,ex,st,os);sc=combined_score(base,ds);h=HEAD[m]
            ranked=sorted([b for b in range(1,7) if b!=h],key=lambda b:opp_place_score(x,b,ex,st,os),reverse=True)
            out.append({'date':str(day),'race_code':code,'model':m,'head':h,'base_score':base,'direct_comp':ds,'score':sc,
                        'tickets6':';'.join(tickets_for(h,ranked,6))})
    return out


def main():
    cache={};hist=defaultdict(list);seen=set();d=PRELOAD_START
    while d<START:
        ingest_motor(hist,seen,d)
        if d>=START-timedelta(days=12):ingest_prior_day_preview(cache,d)
        d+=timedelta(days=1)
    stsum=defaultdict(list);stall=[];samples={m:[] for m in RULES};train_rows=[]
    d=START
    while d<TARGET:
        bias=bias_from(stsum,stall);frozen=freeze_day(d,cache,hist,bias);ymd=d.strftime('%Y/%m/%d')
        # only after predictions are frozen, read outcomes.
        res={r['レースコード']:r for r in rows(f'data/results/realtime/{ymd}.csv')}
        for z in frozen:
            y=target(res.get(z['race_code'],{}),z['model']);z['target']=y;samples[z['model']].append({'score':z['score'],'target':y});train_rows.append(z)
        ingest_stt(d,stsum,stall);ingest_prior_day_preview(cache,d);ingest_motor(hist,seen,d);d+=timedelta(days=1)

    cuts={};ctabs={}
    for m in RULES:cuts[m],ctabs[m]=choose_cut(samples,m)
    # Jun9: freeze with Jun1-8 ST bias and thresholds only.
    bias=bias_from(stsum,stall);frozen=freeze_day(TARGET,cache,hist,bias)
    for z in frozen:z['threshold']=cuts[z['model']];z['approved']=int(z['score']>=z['threshold'])
    # serialize direct snapshot before outcomes.
    if frozen:
        with open('v58_20260609_direct.csv','w',newline='',encoding='utf-8-sig') as f:
            fs=sorted(frozen[0].keys());w=csv.DictWriter(f,fieldnames=fs);w.writeheader();w.writerows(frozen)
    ymd=TARGET.strftime('%Y/%m/%d');res={r['レースコード']:r for r in rows(f'data/results/realtime/{ymd}.csv')};pay={r['レースコード']:r for r in rows(f'data/results/payouts/{ymd}.csv')}
    settled=[]
    for z in frozen:
        rr=res.get(z['race_code'],{});pr=pay.get(z['race_code'],{});q=dict(z);q['winner']=int(float(rr.get('1着_艇番') or 0));q['kimarite']=(rr.get('決まり手') or '').replace(' ','').replace('　','');q['target_hit']=target(rr,z['model']);q['actual_combo']=(pr.get('3連単_組番') or '').strip();q['payout100']=int(float(pr.get('3連単_払戻金') or 0));q['proxy6_hit']=int(q['actual_combo'] in q['tickets6'].split(';'));settled.append(q)
    if settled:
        with open('v58_20260609_settled.csv','w',newline='',encoding='utf-8-sig') as f:
            fs=sorted(set().union(*(r.keys() for r in settled)));w=csv.DictWriter(f,fieldnames=fs);w.writeheader();w.writerows(settled)

    L=['# v58 2026-06-09 完全ウォークフォワード再現','',
       '6/1〜6/8を1日ずつ「事前候補+枠補正済み直前情報を固定→結果を取得→翌日へ反映」で学習。6/9は6/8までの情報のみ。',
       'ST展示枠バイアスも6/1〜6/8のみ。実進入/STTコース欄は不使用。od3は7/19開始のため6/9のEV購入判定は不可能。6点は相手精度診断用で、正式購入成績ではない。','','## 6/1-6/8だけで決めた承認閾値','|モデル|閾値|50|55|60|65|70|','|---|---:|---|---|---|---|---|']
    for m in RULES:
        cells=[]
        for c,n,h,rate,wl in ctabs[m]:cells.append(f'{n}R/{rate:.1f}%')
        L.append(f'|{m}|{cuts[m]}|'+'|'.join(cells)+'|')
    L+=['','## 6/9 事前→直前固定','|レース|モデル|base|直前comp|score|閾値|判定|proxy6|','|---|---|---:|---:|---:|---:|---|---|']
    for z in frozen:L.append(f'|{z["race_code"]}|{z["model"]}|{z["base_score"]:.1f}|{z["direct_comp"]:.3f}|{z["score"]:.1f}|{z["threshold"]}|{"BUY候補" if z["approved"] else "見送り"}|{z["tickets6"]}|')
    L+=['','## 結果照合','|レース|モデル|判定|結果|決まり手|狙い成立|proxy6的中|払戻|','|---|---|---|---|---|---:|---:|---:|']
    for z in settled:L.append(f'|{z["race_code"]}|{z["model"]}|{"BUY候補" if z["approved"] else "見送り"}|{z["actual_combo"]}|{z["kimarite"]}|{z["target_hit"]}|{z["proxy6_hit"]}|{z["payout100"]:,}円|')
    ap=[z for z in settled if z['approved']];L+=['',f'承認候補: **{len(ap)}R** / 狙い成立 **{sum(z["target_hit"] for z in ap)}R** / proxy6的中 **{sum(z["proxy6_hit"] for z in ap)}R**','',
        '注: 6/9は締切前3連単オッズが保存されていないため、EV閾値・Kelly資金配分の評価対象には含めない。']
    open('summary_v58_20260609_walkforward.md','w',encoding='utf-8').write('\n'.join(L)+'\n')

if __name__=='__main__':main()
