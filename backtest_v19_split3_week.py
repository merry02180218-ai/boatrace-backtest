from backtest import *
from backtest_v3 import ingest_motor
from backtest_v4 import ingest_prior_day_preview, score3v4
from backtest_v5_ev import PRELOAD_START, cal_prob, process_features
from backtest_v11_3pair import build_pair_dist, composite, pair_key
from backtest_v17_core3 import allocate
from analyze_3attack_feature_correlations import feature_row
from collections import defaultdict
from datetime import date,timedelta
import csv

TRAIN_START=date(2026,6,1); TRAIN_END=date(2026,7,15)
TEST_START=date(2026,8,27); TEST_END=date(2026,9,2)
MIN_COMPOSITE=5.0
# Fixed before the 8/27-9/2 outcomes are read.
RULES={
 '3まくり':{'3選手力':.50,'3_ST優位':.55,'2壁弱さ':.55,'3伸び':.50},
 '3まくり差し':{'3選手力':.50,'3回り足':.50,'1弱さ':.45,'2壁弱さ':.45},
}

def target(rr,model):
    win=i(rr.get('1着_艇番')); kim=(rr.get('決まり手') or '').replace('　','').replace(' ','')
    return int(win==3 and kim==('まくり' if model=='3まくり' else 'まくり差し'))

def passes(fr,rule): return all(fr[k]>=v for k,v in rule.items())

def select_set(p3,od,pairs):
    from backtest_v5_ev import market_conditional
    dist=build_pair_dist(pairs,market_conditional(od,3)); cand=[]
    for combo,o,q,share,cnt in dist:
        pc=p3*q; cand.append({'combo':combo,'odds':o,'pair_prob':q,'combo_prob':pc,'market_share':share,'train_pair_count':cnt,'ev':pc*o})
    cand.sort(key=lambda z:(z['combo_prob'],z['ev']),reverse=True); chosen=[]
    for z in cand:
        if composite(chosen+[z])>=MIN_COMPOSITE: chosen.append(z)
    return chosen

def main():
    cache={};hist=defaultdict(list);seen=set();d=PRELOAD_START
    while d<TRAIN_START:
        ingest_motor(hist,seen,d)
        if d>=TRAIN_START-timedelta(days=12): ingest_prior_day_preview(cache,d)
        d+=timedelta(days=1)
    train={m:[] for m in RULES}; pairs={m:defaultdict(int) for m in RULES}
    d=TRAIN_START
    while d<=TRAIN_END:
        feats=process_features(d,cache,hist); ymd=d.strftime('%Y/%m/%d');res={r['レースコード']:r for r in rows(f'data/results/realtime/{ymd}.csv')};pay={r['レースコード']:r for r in rows(f'data/results/payouts/{ymd}.csv')}
        for r,x,s4,s5,dc in feats:
            s3=score3v4(x)
            for m in RULES:
                y=target(res.get(r['レースコード'],{}),m);train[m].append((s3,y))
                if y:
                    k=pair_key((pay.get(r['レースコード'],{}).get('3連単_組番') or '').strip())
                    if k:pairs[m][k]+=1
        ingest_prior_day_preview(cache,d);ingest_motor(hist,seen,d);d+=timedelta(days=1)
    bets=[];races=[]
    # advance state through 8/26 without using outcomes for model fitting
    while d<TEST_START:
        process_features(d,cache,hist);ingest_prior_day_preview(cache,d);ingest_motor(hist,seen,d);d+=timedelta(days=1)
    while d<=TEST_END:
        feats=process_features(d,cache,hist);ymd=d.strftime('%Y/%m/%d');ods={r['レースコード']:r for r in rows(f'data/previews/od3/{ymd}.csv')};frozen=[]
        for r,x,s4,s5,dc in feats:
            s3=score3v4(x);fr=feature_row(x,s3,dc)
            for m,rule in RULES.items():
                if not passes(fr,rule):continue
                p=cal_prob(train[m],s3);chosen=select_set(p,ods.get(r['レースコード'],{}),pairs[m])
                if not chosen:continue
                allocate(chosen);co=composite(chosen)
                rr={'model':m,'date':str(d),'race_code':r['レースコード'],'venue':r.get('レース場コード',''),'race':r.get('レース回',''),'score3':round(s3,2),'tickets':len(chosen),'composite_odds':round(co,2)};rr.update({k:round(fr[k],3) for k in rule});races.append(rr)
                for z in chosen:z.update({'model':m,'date':str(d),'race_code':r['レースコード'],'venue':r.get('レース場コード',''),'race':r.get('レース回','')});frozen.append(z)
        pay={r['レースコード']:r for r in rows(f'data/results/payouts/{ymd}.csv')};res={r['レースコード']:r for r in rows(f'data/results/realtime/{ymd}.csv')}
        for b in frozen:
            pr=pay.get(b['race_code'],{});actual=(pr.get('3連単_組番') or '').strip();hit=actual==b['combo'];b['actual_combo']=actual;b['hit']=int(hit);b['payout100']=i(pr.get('3連単_払戻金')) if hit else 0;b['return']=b['payout100']*(b['stake']//100) if hit else 0;bets.append(b)
        for rr in [q for q in races if q['date']==str(d)]:rr['head_hit']=target(res.get(rr['race_code'],{}),rr['model'])
        ingest_prior_day_preview(cache,d);ingest_motor(hist,seen,d);d+=timedelta(days=1)
    for r in races:
        bs=[b for b in bets if b['race_code']==r['race_code'] and b['model']==r['model']];r['bet_hit']=int(any(b['hit'] for b in bs));r['return']=sum(b['return'] for b in bs)
    if bets:
        with open('bets_v19.csv','w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=sorted(set().union(*(b.keys() for b in bets))));w.writeheader();w.writerows(bets)
    if races:
        with open('races_v19.csv','w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=sorted(set().union(*(r.keys() for r in races))));w.writeheader();w.writerows(races)
    L=['# v19 3号艇まくり/まくり差し分離 直近1週間','',f'テスト {TEST_START}〜{TEST_END}。学習は{TRAIN_START}〜{TRAIN_END}のみ。テスト結果で閾値調整なし。','', '|モデル|候補R|頭成立|頭率|3連単的中|的中率|投資|払戻|回収率|','|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for m in RULES:
        rs=[r for r in races if r['model']==m];bs=[b for b in bets if b['model']==m];hh=sum(r['head_hit'] for r in rs);bh=sum(r['bet_hit'] for r in rs);st=sum(b['stake'] for b in bs);ret=sum(b['return'] for b in bs)
        L.append(f'|{m}|{len(rs)}|{hh}|{hh/len(rs)*100 if rs else 0:.1f}%|{bh}|{bh/len(rs)*100 if rs else 0:.1f}%|{st:,}円|{ret:,}円|{ret/st*100 if st else 0:.1f}%|')
    L+=['','## 固定条件']
    for m,r in RULES.items():L.append('- '+m+': '+', '.join(f'{k}>={v}' for k,v in r.items()))
    open('summary_v19.md','w',encoding='utf-8').write('\n'.join(L)+'\n')
if __name__=='__main__':main()
