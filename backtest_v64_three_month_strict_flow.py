"""v64: 2026-06-01..2026-09-02 strict execution-order point-buy backtest.

Operational order, every day:
1) pre-race candidates from v46 source with result target discarded;
2) build online prior-exhibition percentile from prior dates only;
3) correct current exhibition/original exhibition and ST timing using only prior-day ST frame bias;
4) freeze head/method score, A/S approval and 6 trifecta tickets;
5) consolidate duplicate head=3 routes by higher pre-result score;
6) ONLY THEN read results/payouts and settle;
7) update ST-frame history for the next day.

Production ledger: unified head=3 A+ and head=5 A+, fixed 6 tickets x 100 yen.
4-corner is observation only. No odds/EV/Kelly.
Actual entry/course and STT course fields are never used.
"""
import csv, math
from collections import defaultdict
from datetime import date,timedelta
from statistics import mean

from backtest import rows,race_features
from analyze_v23_20260902_daypreview import by_code
from backtest_v51_lane_corrected_tickets import ff,ii,normkim,tilt_band,corrected_direct,opp_place_score,tickets_for
from backtest_v52_scenario_tickets import TILT_BONUS

START=date(2026,6,1); END=date(2026,9,2)
MODELS=['3まくり','3まくり差し','4カドまくり','5頭展開']
HEAD={'3まくり':3,'3まくり差し':3,'4カドまくり':4,'5頭展開':5}
A_CUT=55.0; S_CUT=67.0; HIST_P=2.0


def history_value(r):
    p1=ff(r.get('prior1'),.5);p2=ff(r.get('prior2'),p1);has2=ii(r.get('has2'))
    m=r['model']
    if m=='4カドまくり':return .4*p1+.6*p2 if has2 else p1
    if m=='5頭展開':return p2 if has2 else p1
    return p1

def pct_rank_online(x,vals):
    if not vals:return .5
    return sum(v<=x for v in vals)/len(vals)

def st_bias(sums,allv):
    g=mean(allv) if allv else .15
    return {b:(mean(sums[b])-g if sums[b] else 0.0) for b in range(1,7)}

def ingest_stt(d,sums,allv):
    ymd=d.strftime('%Y/%m/%d')
    for r in rows(f'data/previews/stt/{ymd}.csv'):
        for b in range(1,7):
            v=ff(r.get(f'艇{b}_スタート展示'))
            if v is not None and -.30<v<1.0:
                sums[b].append(v);allv.append(v)

def direct_comp(m,ex,st,os):
    # Same current direct structure, venue term neutralized to .5 to avoid full-period venue fitting.
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

def route_hit(m,win,kim):
    if m=='3まくり':return int(win==3 and kim=='まくり')
    if m=='3まくり差し':return int(win==3 and kim=='まくり差し')
    if m=='4カドまくり':return int(win==4 and kim=='まくり')
    return int(win==5)

def safe_direct(code,tkz,stt,orig,bias):
    ex,st,os=corrected_direct(code,tkz,stt,orig,bias)
    for b in range(1,7):
        ex.setdefault(b,.5);st.setdefault(b,.5);os.setdefault(b,{'lap':.5,'turn':.5,'straight':.5,'avg':.5})
        for k in ('lap','turn','straight','avg'):os[b].setdefault(k,.5)
    return ex,st,os

def load_source():
    out=[]
    with open('analysis_v46_history_softscore.csv',encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            if r.get('model') not in MODELS:continue
            if not ('2026-06-01'<=r.get('date','')<='2026-09-02'):continue
            out.append({k:v for k,v in r.items() if k not in ('target','history_pct','history_adjust')})
    return out

def write_csv(path,rs):
    if not rs:return
    fs=sorted(set().union(*(r.keys() for r in rs)))
    with open(path,'w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=fs);w.writeheader();w.writerows(rs)

def main():
    src=load_source();byday=defaultdict(list)
    for r in src:byday[r['date']].append(r)
    histvals={m:[] for m in MODELS};stsums=defaultdict(list);stall=[]
    frozen_all=[];settled_all=[]
    d=START
    while d<=END:
        ds=str(d);ymd=d.strftime('%Y/%m/%d');bias=st_bias(stsums,stall)
        tkz=by_code(f'data/previews/tkz/{ymd}.csv');stt=by_code(f'data/previews/stt/{ymd}.csv');orig=by_code(f'data/previews/original_exhibition/{ymd}.csv')
        cards=by_code(f'data/programs/race_cards/{ymd}.csv');w10=by_code(f'data/programs/waku10/{ymd}.csv')
        candidates=[]
        for r in byday.get(ds,[]):
            code=r['race_code'];m=r['model'];h=HEAD[m];card=cards.get(code,{})
            if not card:continue
            try:x=race_features(card,w10.get(code,{}))
            except Exception:continue
            ex,st,os=safe_direct(code,tkz,stt,orig,bias)
            hv=history_value(r);hp=pct_rank_online(hv,histvals[m]);hadj=HIST_P*(2*hp-1)
            comp=direct_comp(m,ex,st,os);tr=tkz.get(code,{})
            tilt=ff(tr.get(f'艇{h}_チルト'),0) or 0
            tbonus=TILT_BONUS[m][tilt_band(tilt)]
            score=100*comp+hadj+tbonus
            others=[b for b in range(1,7) if b!=h]
            try:ranked=sorted(others,key=lambda b:opp_place_score(x,b,ex,st,os),reverse=True)
            except Exception:continue
            t6=tickets_for(h,ranked,6)
            candidates.append({'date':ds,'race_code':code,'model':m,'head':h,'score':round(score,4),'grade':'S' if score>=S_CUT else ('A' if score>=A_CUT else 'B'),
                'approved_A':int(score>=A_CUT),'approved_S':int(score>=S_CUT),'history_pct_online':round(hp,4),'history_adjust_online':round(hadj,4),
                'preview_comp':round(comp,5),'tilt':tilt,'tilt_bonus':tbonus,'ranked_others':'-'.join(map(str,ranked)),'tickets6':';'.join(t6)})
        # Head-first: one route per race/head, selected before outcomes.
        grp=defaultdict(list)
        for z in candidates:grp[(z['race_code'],z['head'])].append(z)
        frozen=[max(a,key=lambda z:z['score']) for a in grp.values()]
        frozen_all.extend(frozen)
        # Results are loaded only after all selections/tickets for the day are frozen.
        res={r['レースコード']:r for r in rows(f'data/results/realtime/{ymd}.csv')};pay={r['レースコード']:r for r in rows(f'data/results/payouts/{ymd}.csv')}
        for z in frozen:
            rr=res.get(z['race_code'],{});pr=pay.get(z['race_code'],{});win=ii(rr.get('1着_艇番'));kim=normkim(rr.get('決まり手'));combo=(pr.get('3連単_組番') or '').strip();payout=ii(pr.get('3連単_払戻金'))
            q=dict(z);q.update({'winner':win,'kimarite':kim,'head_hit':int(win==z['head']),'route_hit':route_hit(z['model'],win,kim),'actual_combo':combo,'payout100':payout,
                'ticket6_hit':int(combo in z['tickets6'].split(';')),'invest6':600 if z['approved_A'] else 0,'return6':payout if z['approved_A'] and combo in z['tickets6'].split(';') else 0,
                'production_buy':int(z['approved_A'] and z['head'] in (3,5))})
            settled_all.append(q)
        # Update only information available after this day for future dates.
        for r in byday.get(ds,[]):histvals[r['model']].append(history_value(r))
        ingest_stt(d,stsums,stall)
        d+=timedelta(days=1)

    write_csv('analysis_v64_three_month_strict_flow.csv',settled_all)

    def stat(rs,buy_only=False):
        q=[r for r in rs if (r['production_buy'] if buy_only else r['approved_A'])]
        n=len(q);hh=sum(r['head_hit'] for r in q);rh=sum(r['route_hit'] for r in q);th=sum(r['ticket6_hit'] for r in q)
        inv=sum(r['invest6'] for r in q);ret=sum(r['return6'] for r in q)
        return n,hh,100*hh/n if n else 0,rh,100*rh/n if n else 0,th,100*th/n if n else 0,inv,ret,100*ret/inv if inv else 0
    def max_losing_streak(rs):
        cur=best=0
        for r in sorted(rs,key=lambda x:(x['date'],x['race_code'])):
            if not r['production_buy']:continue
            if r['ticket6_hit']:cur=0
            else:cur+=1;best=max(best,cur)
        return best

    L=['# v64 実運用順 3か月ポイント買いバックテスト','',
       '**期間: 2026-06-01〜2026-09-02**','',
       '毎日、事前候補→過去日だけで履歴percentile/ST枠バイアス→当日展示/オリジナル展示→A/S判定→頭固定6点を完全固定し、その後にだけ結果/払戻を結合。実進入・ST展示コース欄は不使用。',
       '3まくり/3まくり差しが同一レースで重なれば、結果を見る前にscore上位1本へ統合。主購入は **3頭A以上 + 5頭A以上、6点×100円**。4頭は観察枠。オッズ/EV/Kellyは不使用。',
       '履歴percentileは未来期間を使わず、その日より前の候補だけでオンライン計算。場指数は全期間学習を避けるため中立0.5。','','## 主購入 3頭+5頭','|期間|購入R|頭的中|頭率|3連単的中|的中率|投資|払戻|ROI|','|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    periods=[('6月','2026-06-01','2026-06-30'),('7月','2026-07-01','2026-07-31'),('8月','2026-08-01','2026-08-31'),('9/1-2','2026-09-01','2026-09-02'),('全期間','2026-06-01','2026-09-02')]
    for name,lo,hi in periods:
        rs=[r for r in settled_all if lo<=r['date']<=hi];n,hh,hr,rh,rr,th,tr,inv,ret,roi=stat(rs,True)
        L.append(f'|{name}|{n}|{hh}|{hr:.1f}%|{th}|{tr:.1f}%|{inv:,}円|{ret:,}円|{roi:.1f}%|')
    L+=['','## 頭別・A以上6点','|頭|候補R|頭的中|頭率|3連単的中|的中率|投資|払戻|ROI|','|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for h in [3,5,4]:
        rs=[r for r in settled_all if r['head']==h and r['approved_A']];n=len(rs);hh=sum(r['head_hit'] for r in rs);th=sum(r['ticket6_hit'] for r in rs);inv=n*600;ret=sum(r['payout100'] for r in rs if r['ticket6_hit']);roi=100*ret/inv if inv else 0
        L.append(f'|{h}|{n}|{hh}|{100*hh/n if n else 0:.1f}%|{th}|{100*th/n if n else 0:.1f}%|{inv:,}円|{ret:,}円|{roi:.1f}%|')
    L+=['','## 選択された3頭ルート','|予測ルート|A以上R|頭率|ルート一致率|6点ROI|','|---|---:|---:|---:|---:|']
    for m in ['3まくり','3まくり差し']:
        rs=[r for r in settled_all if r['head']==3 and r['model']==m and r['approved_A']];n=len(rs);hh=sum(r['head_hit'] for r in rs);rh=sum(r['route_hit'] for r in rs);ret=sum(r['payout100'] for r in rs if r['ticket6_hit']);inv=n*600
        L.append(f'|{m}|{n}|{100*hh/n if n else 0:.1f}%|{100*rh/n if n else 0:.1f}%|{100*ret/inv if inv else 0:.1f}%|')
    buys=[r for r in settled_all if r['production_buy']]
    L+=['','## リスク指標',f'- 主購入総数: **{len(buys)}R**',f'- 最大連続不的中: **{max_losing_streak(settled_all)}R**',
        f'- S評価購入: **{sum(r["approved_S"] and r["head"] in (3,5) for r in settled_all)}R**','',
        '## 解釈上の注意','- 実行順の結果リークは防いでいるが、現在のモデル構造・固定係数自体はこの3か月を含む開発過程で作られたものもある。したがって「完全な未使用3か月OOS」ではなく、現在モデルを過去に同じ手順で適用した運用再現バックテスト。','- 月別の再現性と、既存の独立Validation/Test結果を合わせて採否判断する。']
    open('summary_v64_three_month_strict_flow.md','w',encoding='utf-8').write('\n'.join(L)+'\n')

if __name__=='__main__':main()
