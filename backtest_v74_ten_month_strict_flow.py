"""v74: strict 10-month locked-rule replay, 2025-11-01..2026-08-31.

No odds/EV. Current v20 candidate rules + v64 direct A/S score + v65 deterministic
20-combination display ranking. Historical waku10 uses saved BoatraceCSV when present,
otherwise overlap-validated direct BOATCAST fallback. Results/payouts are read only
after candidate, route, grade, head, opponent rank and tickets are frozen.
"""
from __future__ import annotations
import csv, re
from collections import defaultdict, deque
from datetime import date, timedelta
from statistics import mean

from backtest import rows, race_features
from backtest_v3 import CORR, expo_rows_to_records, ingest_motor
from backtest_v4 import add_features, score3v4, score4v4, clean_name, rank_strength
from backtest_v20_week import RULES, features, passes
from backtest_v51_lane_corrected_tickets import ff, ii, normkim, tilt_band, corrected_direct, opp_place_score, tickets_for
from backtest_v52_scenario_tickets import TILT_BONUS
from historical_data_loader import waku10_rows

PRELOAD=date(2025,10,1)
START=date(2025,11,1)
END=date(2026,8,31)
MODELS=['3まくり','3まくり差し','4カドまくり','5頭展開']
HEAD={'3まくり':3,'3まくり差し':3,'4カドまくり':4,'5頭展開':5}
A_CUT=55.0; S_CUT=67.0; HIST_P=2.0


def bycode(rs): return {r['レースコード']:r for r in rs if r.get('レースコード')}

def history_value(r):
    p1=ff(r.get('prior1'),.5); p2=ff(r.get('prior2'),p1); has2=ii(r.get('has2'))
    m=r['model']
    if m=='4カドまくり': return .4*p1+.6*p2 if has2 else p1
    if m=='5頭展開': return p2 if has2 else p1
    return p1

def pct_rank_online(x, vals):
    return .5 if not vals else sum(v<=x for v in vals)/len(vals)

def st_bias(sums, allv):
    g=mean(allv) if allv else .15
    return {b:(mean(sums[b])-g if sums[b] else 0.0) for b in range(1,7)}

def update_st(strows, sums, allv):
    for r in strows:
        for b in range(1,7):
            v=ff(r.get(f'艇{b}_スタート展示'))
            if v is not None and -.30<v<1.0:
                sums[b].append(v); allv.append(v)

def hf(ph,key,n):
    a=list(ph.get(key,[]))[-n:]
    if not a:return {'display':.5,'overall':.5,'turn':.5,'straight':.5}
    ws=[1.] if len(a)==1 else [.4,.6]
    return {k:sum(w*z[k] for w,z in zip(ws,a))/sum(ws) for k in ('display','overall','turn','straight')}

def ps(z,m):
    if m in ('3まくり','4カドまくり'):return .35*z['display']+.15*z['overall']+.15*z['turn']+.35*z['straight']
    if m=='3まくり差し':return .15*z['display']+.15*z['overall']+.40*z['turn']+.30*z['straight']
    return .10*z['display']+.20*z['overall']+.45*z['turn']+.25*z['straight']

def update_preview_states(cards,tkz,orig,cache,ph):
    tm=bycode(tkz); om=bycode(orig)
    for card in cards:
        code=card.get('レースコード',''); venue=str(card.get('レース場コード','')).zfill(2)
        er=om.get(code,{}); tr=tm.get(code,{})
        orecs=expo_rows_to_records([er]) if er else []
        oz={clean_name(z['name']):z for z in orecs}
        vals=[]
        for b in range(1,7):
            v=ff(tr.get(f'艇{b}_展示タイム'))
            if v is not None:vals.append((b,v+CORR[b]['展示']))
        dr=rank_strength(vals) if vals else {}
        for b in range(1,7):
            name=clean_name(card.get(f'艇{b}_選手名'))
            if not name:continue
            q=oz.get(name,{})
            z={'display':dr.get(b,.5),'overall':q.get('overall',.5),'turn':q.get('turn',.5),'straight':q.get('straight',.5)}
            cache[(venue,name)]=z; ph[(venue,name)].append(z)

def raw_candidates(cards,w10,cache,mhist,ph):
    out=[]; missing_w10=0
    for card in cards:
        code=card.get('レースコード','')
        if not code or code not in w10:
            missing_w10+=1; continue
        try:x=add_features(race_features(card,w10[code]),card,cache,mhist)
        except Exception:continue
        s3=score3v4(x); s4=score4v4(x); venue=str(card.get('レース場コード','')).zfill(2)
        for m in MODELS:
            try:fr=features(x,s3,s4,'',m)
            except Exception:continue
            if not passes(fr,RULES[m]):continue
            h=HEAD[m]; name=clean_name(card.get(f'艇{h}_選手名')); key=(venue,name)
            p1=ps(hf(ph,key,1),m); p2=ps(hf(ph,key,2),m); has2=int(len(ph.get(key,[]))>=2)
            out.append({'race_code':code,'model':m,'head':h,'prior1':p1,'prior2':p2,'has2':has2,'_x':x})
    return out,missing_w10

def direct_comp(m,ex,st,os):
    if m=='3まくり':
        z=os[3];return .28*ex.get(3,.5)+.28*st.get(3,.5)+.22*z['straight']+.17*z['avg']+.05*.5
    if m=='3まくり差し':
        z=os[3];return .17*ex.get(3,.5)+.22*st.get(3,.5)+.17*z['lap']+.27*z['turn']+.12*z['avg']+.05*.5
    if m=='4カドまくり':
        z=os[4];return .28*ex.get(4,.5)+.30*st.get(4,.5)+.22*z['straight']+.15*z['avg']+.05*.5
    z4=os[4];z5=os[5]
    attack4=.32*ex.get(4,.5)+.38*st.get(4,.5)+.18*z4['straight']+.12*z4['avg']
    take5=.22*ex.get(5,.5)+.17*st.get(5,.5)+.27*z5['lap']+.27*z5['turn']+.07*z5['avg']
    return .43*attack4+.52*take5+.05*.5

def safe_direct(code,tkz,stt,orig,bias):
    ex,st,os=corrected_direct(code,tkz,stt,orig,bias)
    for b in range(1,7):
        ex.setdefault(b,.5);st.setdefault(b,.5);os.setdefault(b,{'lap':.5,'turn':.5,'straight':.5,'avg':.5})
        for k in ('lap','turn','straight','avg'):os[b].setdefault(k,.5)
    return ex,st,os

def route_hit(m,win,kim):
    if m=='3まくり':return int(win==3 and kim=='まくり')
    if m=='3まくり差し':return int(win==3 and kim=='まくり差し')
    if m=='4カドまくり':return int(win==4 and kim=='まくり')
    return int(win==5)

def combos20(head,ranked):
    out=[]
    for ia,a in enumerate(ranked,1):
        for ib,b in enumerate(ranked,1):
            if a==b:continue
            out.append((ia+.7*ib,ia,ib,f'{head}-{a}-{b}'))
    out.sort(key=lambda z:(z[0],z[1],z[2],z[3]))
    return out

def parse_combo(s):
    a=[int(x) for x in re.findall(r'[1-6]',s or '')]
    return a[:3] if len(a)>=3 else []

def freeze_day(ds,raw,tkz,stt,orig,bias,histvals):
    candidates=[]
    for r in raw:
        code=r['race_code'];m=r['model'];h=r['head'];x=r['_x']
        ex,st,os=safe_direct(code,tkz,stt,orig,bias)
        hv=history_value(r);hp=pct_rank_online(hv,histvals[m]);hadj=HIST_P*(2*hp-1)
        comp=direct_comp(m,ex,st,os);tr=tkz.get(code,{})
        tilt=ff(tr.get(f'艇{h}_チルト'),0) or 0;tbonus=TILT_BONUS[m][tilt_band(tilt)]
        score=100*comp+hadj+tbonus
        try:ranked=sorted([b for b in range(1,7) if b!=h],key=lambda b:opp_place_score(x,b,ex,st,os),reverse=True)
        except Exception:continue
        c20=combos20(h,ranked);t6=tickets_for(h,ranked,6)
        candidates.append({'date':ds,'race_code':code,'model':m,'head':h,'score':round(score,4),
            'grade':'S' if score>=S_CUT else ('A' if score>=A_CUT else 'B'),'approved_A':int(score>=A_CUT),'approved_S':int(score>=S_CUT),
            'history_pct_online':round(hp,4),'history_adjust_online':round(hadj,4),'preview_comp':round(comp,5),'tilt':tilt,'tilt_bonus':tbonus,
            'ranked_others':'-'.join(map(str,ranked)),'tickets6':';'.join(t6),'tickets20_display':';'.join(z[3] for z in c20),
            'has_tkz':int(code in tkz),'has_stt':int(code in stt),'has_orig':int(code in orig)})
    grp=defaultdict(list)
    for z in candidates:grp[(z['race_code'],z['head'])].append(z)
    return [max(a,key=lambda z:z['score']) for a in grp.values()]

def settle_day(frozen,res,pay):
    out=[]
    for z in frozen:
        rr=res.get(z['race_code'],{});pr=pay.get(z['race_code'],{})
        win=ii(rr.get('1着_艇番'));kim=normkim(rr.get('決まり手'));combo=(pr.get('3連単_組番') or '').strip();payout=ii(pr.get('3連単_払戻金'))
        arr=parse_combo(combo); ranked=[int(x) for x in z['ranked_others'].split('-') if x]
        c20=z['tickets20_display'].split(';') if z['tickets20_display'] else []
        rank20=(c20.index(combo)+1) if combo in c20 else 0
        sec_rank=(ranked.index(arr[1])+1) if len(arr)>=3 and arr[1] in ranked else 0
        third_rank=(ranked.index(arr[2])+1) if len(arr)>=3 and arr[2] in ranked else 0
        valid_result=int(win in range(1,7)); valid_payout=int(len(arr)==3 and payout>0)
        hh=int(valid_result and win==z['head']); hit6=int(valid_payout and combo in z['tickets6'].split(';'))
        hit20=int(valid_payout and combo in c20)
        q=dict(z);q.update({'winner':win,'kimarite':kim,'head_hit':hh,'route_hit':route_hit(z['model'],win,kim) if valid_result else 0,
            'actual_combo':combo,'payout100':payout,'actual_rank20':rank20,'actual_second_rank':sec_rank,'actual_third_rank':third_rank,
            'valid_result':valid_result,'valid_payout':valid_payout,'ticket6_hit':hit6,'ticket20_hit':hit20,
            'production_buy':int(z['approved_A'] and z['head'] in (3,5))})
        out.append(q)
    return out

def write_csv(path,rs):
    if not rs:return
    fs=sorted(set().union(*(r.keys() for r in rs)))
    with open(path,'w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=fs);w.writeheader();w.writerows(rs)

def pct(n,d):return 100*n/d if d else 0.0

def stat(rs,main=True,grade='A'):
    q=[r for r in rs if r['valid_result'] and (r['head'] in (3,5) if main else True) and (r['approved_S'] if grade=='S' else r['approved_A'])]
    n=len(q);hh=sum(r['head_hit'] for r in q);rh=sum(r['route_hit'] for r in q)
    qp=[r for r in q if r['valid_payout']];h6=sum(r['ticket6_hit'] for r in qp);h20=sum(r['ticket20_hit'] for r in qp)
    inv6=600*len(qp);ret6=sum(r['payout100'] for r in qp if r['ticket6_hit']);inv20=2000*len(qp);ret20=sum(r['payout100'] for r in qp if r['ticket20_hit'])
    return n,hh,pct(hh,n),rh,pct(rh,n),len(qp),h6,pct(h6,len(qp)),pct(ret6,inv6),h20,pct(ret20,inv20)

def main():
    cache={};mhist=defaultdict(list);seen=set();ph=defaultdict(lambda:deque(maxlen=2));histvals={m:[] for m in MODELS}
    stsums=defaultdict(list);stall=[];settled=[]
    cover=defaultdict(int);missing_dates=[];d=PRELOAD
    while d<=END:
        ds=str(d);ymd=d.strftime('%Y/%m/%d')
        cards=rows(f'data/programs/race_cards/{ymd}.csv')
        if not cards:
            if d>=START:missing_dates.append(ds)
            d+=timedelta(days=1);continue
        wrows,wsrc=waku10_rows(ds);w10=bycode(wrows)
        tkzrows=rows(f'data/previews/tkz/{ymd}.csv');strows=rows(f'data/previews/stt/{ymd}.csv');orows=rows(f'data/previews/original_exhibition/{ymd}.csv')
        tkz=bycode(tkzrows);stt=bycode(strows);orig=bycode(orows)
        raw,miss=raw_candidates(cards,w10,cache,mhist,ph)
        cover['days_'+wsrc]+=1;cover['card_races']+=len(cards);cover['waku_races']+=len(w10);cover['missing_waku_races']+=miss
        if d>=START:
            bias=st_bias(stsums,stall);frozen=freeze_day(ds,raw,tkz,stt,orig,bias,histvals)
            # Results/payouts are intentionally loaded only after the entire day is frozen.
            res=bycode(rows(f'data/results/realtime/{ymd}.csv'));pay=bycode(rows(f'data/results/payouts/{ymd}.csv'))
            settled.extend(settle_day(frozen,res,pay));cover['frozen']+=len(frozen)
            cover['frozen_tkz']+=sum(z['has_tkz'] for z in frozen);cover['frozen_stt']+=sum(z['has_stt'] for z in frozen);cover['frozen_orig']+=sum(z['has_orig'] for z in frozen)
        # Only after freeze/settlement does today's information become history for tomorrow.
        for r in raw:histvals[r['model']].append(history_value(r))
        update_preview_states(cards,tkzrows,orows,cache,ph);update_st(strows,stsums,stall);ingest_motor(mhist,seen,d)
        if d.day==1:print('processed',ds,'w10',wsrc,'cards',len(cards),'raw',len(raw),flush=True)
        d+=timedelta(days=1)

    write_csv('analysis_v74_ten_month_strict_flow.csv',settled)
    L=['# v74 10か月 厳格ノーリーク・頭固定20通り検証','',f'**期間: {START}〜{END}**（10か月）','',
       '現行v20候補条件、v64の枠補正済み直前A/S判定、v65の頭固定20通り表示順位を固定して日次順に再生。オッズ/EV/Kelly不使用。',
       'waku10は保存済みCSVを優先し、欠損期間はBOATCAST直接取得を使用（7/20重複検証で32,448/32,448項目一致）。',
       '実進入・ST展示コース列・結果由来コースは不使用。結果/払戻はその日の候補・score・grade・頭・相手順位・全20通りを固定した後にだけロード。',
       '4カドは観察枠。主評価は3頭+5頭。20点ROIは「全20通りを各100円買った場合」の診断値で、実運用ではユーザーが20通りから手動で絞る。','','## データカバレッジ',
       f"- race card読込: {cover['card_races']:,}R / waku10取得: {cover['waku_races']:,}R / waku10欠損: {cover['missing_waku_races']:,}R",
       f"- waku10 saved日: {cover['days_boatracecsv_saved']}日 / BOATCAST直接日: {cover['days_boatcast_direct']}日 / missing日: {cover['days_missing']}日",
       f"- 凍結候補: {cover['frozen']:,}R / tkzあり {cover['frozen_tkz']:,} / sttあり {cover['frozen_stt']:,} / originalあり {cover['frozen_orig']:,}",
       f"- race card欠損日: {len(missing_dates)}日"+((' ('+', '.join(missing_dates[:12])+('…' if len(missing_dates)>12 else '')+')') if missing_dates else ''),'',
       '## 月別 主候補（3頭+5頭）A以上','|月|候補R|頭的中|頭率|S候補R|S頭率|6点率|6点ROI|20点ROI|','|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    cur=date(2025,11,1)
    while cur<=END:
        lo=cur.isoformat();nxt=(date(cur.year+1,1,1) if cur.month==12 else date(cur.year,cur.month+1,1));hi=min(END,nxt-timedelta(days=1)).isoformat()
        rs=[r for r in settled if lo<=r['date']<=hi]
        n,hh,hr,_,_,pn,h6,h6r,r6,h20,r20=stat(rs,True,'A');sn,sh,shr,*_=stat(rs,True,'S')
        L.append(f'|{cur.strftime("%Y-%m")}|{n}|{hh}|{hr:.1f}%|{sn}|{shr:.1f}%|{h6r:.1f}%|{r6:.1f}%|{r20:.1f}%|')
        cur=nxt
    L+=['','## 10か月合計 主候補（3頭+5頭）','|評価|候補R|頭的中|頭率|6点的中率|6点ROI|20点ROI|','|---|---:|---:|---:|---:|---:|---:|']
    for g in ('A','S'):
        n,hh,hr,_,_,pn,h6,h6r,r6,h20,r20=stat(settled,True,g);L.append(f'|{g}以上|{n}|{hh}|{hr:.1f}%|{h6r:.1f}%|{r6:.1f}%|{r20:.1f}%|')
    L+=['','## モデル別 A以上','|モデル|候補R|頭率|予測ルート一致率|S候補R|S頭率|20点ROI|','|---|---:|---:|---:|---:|---:|---:|']
    for m in MODELS:
        rs=[r for r in settled if r['model']==m];n,hh,hr,rh,rr,pn,h6,h6r,r6,h20,r20=stat(rs,False,'A');sn,sh,shr,*_=stat(rs,False,'S')
        L.append(f'|{m}|{n}|{hr:.1f}%|{rr:.1f}%|{sn}|{shr:.1f}%|{r20:.1f}%|')
    mainhits=[r for r in settled if r['valid_result'] and r['approved_A'] and r['head'] in (3,5) and r['head_hit']]
    def le(field,k):return sum(1 for r in mainhits if 0<int(r.get(field) or 0)<=k)
    L+=['','## 頭的中時の20通り順位（主候補A以上）',f'- 頭的中: **{len(mainhits)}R**',
        f'- 実3連単が表示1〜3位: **{le("actual_rank20",3)}R ({pct(le("actual_rank20",3),len(mainhits)):.1f}%)**',
        f'- 1〜5位: **{le("actual_rank20",5)}R ({pct(le("actual_rank20",5),len(mainhits)):.1f}%)**',
        f'- 1〜8位: **{le("actual_rank20",8)}R ({pct(le("actual_rank20",8),len(mainhits)):.1f}%)**',
        f'- 1〜10位: **{le("actual_rank20",10)}R ({pct(le("actual_rank20",10),len(mainhits)):.1f}%)**',
        f'- 1〜15位: **{le("actual_rank20",15)}R ({pct(le("actual_rank20",15),len(mainhits)):.1f}%)**',
        f'- 1〜20位: **{le("actual_rank20",20)}R ({pct(le("actual_rank20",20),len(mainhits)):.1f}%)**','',
        '## 相手順位診断（頭的中時）',
        f'- 実2着が相手1位: {le("actual_second_rank",1)}R ({pct(le("actual_second_rank",1),len(mainhits)):.1f}%) / top2: {le("actual_second_rank",2)}R ({pct(le("actual_second_rank",2),len(mainhits)):.1f}%) / top3: {le("actual_second_rank",3)}R ({pct(le("actual_second_rank",3),len(mainhits)):.1f}%)',
        f'- 実3着が相手1位: {le("actual_third_rank",1)}R ({pct(le("actual_third_rank",1),len(mainhits)):.1f}%) / top2: {le("actual_third_rank",2)}R ({pct(le("actual_third_rank",2),len(mainhits)):.1f}%) / top3: {le("actual_third_rank",3)}R ({pct(le("actual_third_rank",3),len(mainhits)):.1f}%)','',
        '## 解釈上の注意','- これは現行ルールを過去へ固定適用した retrospective locked-rule replay。今回の10か月結果を使って閾値・重みは変更していない。','- 2026年6〜8月はモデル開発・反復確認で既に触れている期間を含むため、完全未見OOSとは扱わない。11月〜5月の安定性を特に重視して読む。','- 20点ROIは手動絞り前の上限確認用。実運用の成績を意味しない。']
    open('summary_v74_ten_month_strict_flow.md','w',encoding='utf-8').write('\n'.join(L)+'\n')
    print('DONE frozen',cover['frozen'],'settled',len(settled),flush=True)

if __name__=='__main__':main()
