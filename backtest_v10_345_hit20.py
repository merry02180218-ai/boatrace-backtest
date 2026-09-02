from backtest import *
from backtest_v4 import ingest_prior_day_preview, score3v4
from backtest_v3 import ingest_motor
from backtest_v5_ev import PRELOAD_START, TEST_START, TEST_END, cal_prob, market_conditional, process_features
from collections import defaultdict
from datetime import date, timedelta
import math

HEAD_TRAIN_START=date(2026,6,1)
HEAD_TRAIN_END=date(2026,7,15)
SET_CAL_START=date(2026,7,16)
SET_CAL_END=date(2026,8,2)
MIN_COMPOSITE=5.0
MIN_SET_PROB=0.20
RACE_BUDGET=5000
S3_MIN=65.0
S4_MIN=60.0
S5_MIN=60.0


def composite_odds(items):
    s=sum(1/x['odds_pre'] for x in items if x['odds_pre']>0)
    return 1/s if s>0 else 999.0


def build_set(r,x,s3,s4,s5,dc,od,train3,train4,train5,d):
    p3=cal_prob(train3,s3); p4=cal_prob(train4,s4); p5=cal_prob(train5,s5)
    cand=[]
    for head,sc,p,mn in [(3,s3,p3,S3_MIN),(4,s4,p4,S4_MIN),(5,s5,p5,S5_MIN)]:
        if sc<mn: continue
        for combo,o,share in market_conditional(od,head):
            pc=p*share
            ev=pc*o
            cand.append({'date':str(d),'race_code':r['レースコード'],'venue':r.get('レース場コード',''),'race':r.get('レース回',''),'day_cat':dc,'head':head,'combo':combo,'score':round(sc,2),'head_prob':p,'combo_prob':pc,'odds_pre':o,'ev_pre':ev})
    # Coverage first, but retain market-value signal as tiebreaker.
    cand.sort(key=lambda z:(z['combo_prob'],z['ev_pre']),reverse=True)
    chosen=[]
    for z in cand:
        trial=chosen+[z]
        if composite_odds(trial)>=MIN_COMPOSITE:
            chosen=trial
    return chosen,p3,p4,p5


def set_raw_prob(chosen):
    return min(.95,sum(x['combo_prob'] for x in chosen))


def calibrate_set_prob(samples, rawp, co, tickets, heads_count):
    if not samples: return rawp
    vals=[]
    for rp,c,t,hc,y in samples:
        dist=(abs(rp-rawp)/0.08 +
              abs(math.log(max(c,1.01))-math.log(max(co,1.01)))/0.7 +
              abs(t-tickets)/20.0 + abs(hc-heads_count)*0.35)
        vals.append((dist,y))
    vals.sort(key=lambda x:x[0])
    near=vals[:min(100,len(vals))]
    sw=sy=0.0
    for dist,y in near:
        w=1/(1+dist)
        sw+=w; sy+=w*y
    base=sum(y for *_,y in samples)/len(samples)
    prior_n=15.0
    return (sy+prior_n*base)/(sw+prior_n)


def allocate(chosen):
    if not chosen: return
    # Budget is max 5,000 yen. Keep all tickets only while 100 yen each is possible.
    if len(chosen)>50:
        chosen.sort(key=lambda z:(z['combo_prob'],z['ev_pre']),reverse=True)
        del chosen[50:]
    n=len(chosen)
    for z in chosen: z['stake_v10']=100
    remain=RACE_BUDGET-100*n
    if remain<=0: return
    # Allocation emphasizes probability and then EV, rather than longshot EV alone.
    weights=[max(.0001,z['combo_prob']*max(1.0,min(3.0,z['ev_pre']))) for z in chosen]
    sw=sum(weights); units=remain//100
    raw=[units*w/sw for w in weights]; add=[int(a) for a in raw]
    left=units-sum(add)
    order=sorted(range(n),key=lambda k:raw[k]-add[k],reverse=True)
    for k in order[:left]: add[k]+=1
    for z,a in zip(chosen,add): z['stake_v10']+=100*a


def main():
    cache={}; hist=defaultdict(list); seen=set(); d=PRELOAD_START
    while d<HEAD_TRAIN_START:
        ingest_motor(hist,seen,d)
        if d>=HEAD_TRAIN_START-timedelta(days=12): ingest_prior_day_preview(cache,d)
        d+=timedelta(days=1)

    train3=[]; train4=[]; train5=[]
    d=HEAD_TRAIN_START
    while d<=HEAD_TRAIN_END:
        feats=process_features(d,cache,hist); ymd=d.strftime('%Y/%m/%d')
        res={r['レースコード']:r for r in rows(f'data/results/realtime/{ymd}.csv')}
        for r,x,s4,s5,dc in feats:
            s3=score3v4(x)
            rr=res.get(r['レースコード'],{}); win=i(rr.get('1着_艇番')); kim=(rr.get('決まり手') or '').replace('　','').replace(' ','')
            # For 3, train specifically on the intended event: 3 head by makuri/makuri-sashi.
            train3.append((s3,1 if win==3 and kim in ('まくり','まくり差し') else 0))
            train4.append((s4,1 if win==4 else 0)); train5.append((s5,1 if win==5 else 0))
        ingest_prior_day_preview(cache,d); ingest_motor(hist,seen,d); d+=timedelta(days=1)

    set_samples=[]
    d=SET_CAL_START
    while d<=SET_CAL_END:
        feats=process_features(d,cache,hist); ymd=d.strftime('%Y/%m/%d')
        odds={r['レースコード']:r for r in rows(f'data/previews/od3/{ymd}.csv')}
        pay={r['レースコード']:r for r in rows(f'data/results/payouts/{ymd}.csv')}
        for r,x,s4,s5,dc in feats:
            s3=score3v4(x)
            chosen,p3,p4,p5=build_set(r,x,s3,s4,s5,dc,odds.get(r['レースコード'],{}),train3,train4,train5,d)
            if not chosen: continue
            actual=(pay.get(r['レースコード'],{}).get('3連単_組番') or '').strip()
            y=1 if any(z['combo']==actual for z in chosen) else 0
            set_samples.append((set_raw_prob(chosen),composite_odds(chosen),len(chosen),len(set(z['head'] for z in chosen)),y))
        ingest_prior_day_preview(cache,d); ingest_motor(hist,seen,d); d+=timedelta(days=1)

    bets=[]; races=[]; d=TEST_START
    while d<=TEST_END:
        feats=process_features(d,cache,hist); ymd=d.strftime('%Y/%m/%d')
        odds={r['レースコード']:r for r in rows(f'data/previews/od3/{ymd}.csv')}
        frozen=[]
        for r,x,s4,s5,dc in feats:
            s3=score3v4(x)
            chosen,p3,p4,p5=build_set(r,x,s3,s4,s5,dc,odds.get(r['レースコード'],{}),train3,train4,train5,d)
            if not chosen: continue
            rawp=set_raw_prob(chosen); co=composite_odds(chosen); hc=len(set(z['head'] for z in chosen))
            cp=calibrate_set_prob(set_samples,rawp,co,len(chosen),hc)
            if cp<MIN_SET_PROB: continue
            allocate(chosen)
            if not chosen: continue
            co=composite_odds(chosen); heads=''.join(str(h) for h in sorted(set(z['head'] for z in chosen)))
            for z in chosen:
                z['set_prob_raw']=round(rawp,4); z['set_prob_cal']=round(cp,4); z['composite_odds_race']=round(co,2); z['tickets_race']=len(chosen)
            races.append({'date':str(d),'race_code':r['レースコード'],'venue':r.get('レース場コード',''),'race':r.get('レース回',''),'day_cat':dc,'score3':round(s3,2),'score4':round(s4,2),'score5':round(s5,2),'p3':round(p3,4),'p4':round(p4,4),'p5':round(p5,4),'set_prob_raw':round(rawp,4),'set_prob_cal':round(cp,4),'heads_bet':heads,'tickets':len(chosen),'composite_odds':round(co,2)})
            frozen.extend(chosen)
        pay={r['レースコード']:r for r in rows(f'data/results/payouts/{ymd}.csv')}
        for b in frozen:
            pr=pay.get(b['race_code'],{}); actual=(pr.get('3連単_組番') or '').strip(); hit=actual==b['combo']
            b['hit']=int(hit); b['actual_combo']=actual; b['payout100']=i(pr.get('3連単_払戻金')) if hit else 0
            b['return_v10']=b['payout100']*(b['stake_v10']//100) if hit else 0
            bets.append(b)
        ingest_prior_day_preview(cache,d); ingest_motor(hist,seen,d); d+=timedelta(days=1)

    for r in races:
        bs=[b for b in bets if b['race_code']==r['race_code']]
        r['hit']=1 if any(b['hit'] for b in bs) else 0

    if bets:
        with open('bets_v10.csv','w',newline='',encoding='utf-8-sig') as f:
            w=csv.DictWriter(f,fieldnames=list(bets[0].keys())); w.writeheader(); w.writerows(bets)
    if races:
        with open('races_v10.csv','w',newline='',encoding='utf-8-sig') as f:
            w=csv.DictWriter(f,fieldnames=list(races[0].keys())); w.writeheader(); w.writerows(races)

    st=sum(b['stake_v10'] for b in bets); ret=sum(b['return_v10'] for b in bets); hits=sum(r['hit'] for r in races)
    rate=hits/len(races)*100 if races else 0; roi=ret/st*100 if st else 0
    cal_n=len(set_samples); cal_hit=sum(y for *_,y in set_samples); cal_rate=cal_hit/cal_n*100 if cal_n else 0
    L=['# v10 3/4/5統合・的中率20%優先・合成5倍・1R5000円','',
       f'頭確率学習: {HEAD_TRAIN_START}〜{HEAD_TRAIN_END}。集合校正: {SET_CAL_START}〜{SET_CAL_END}。テスト: {TEST_START}〜{TEST_END}。',
       f'3頭score>={S3_MIN:.0f}、4頭>={S4_MIN:.0f}、5頭>={S5_MIN:.0f}。購入条件は校正済み集合的中確率>={MIN_SET_PROB*100:.0f}%かつ合成オッズ>={MIN_COMPOSITE}倍。結果は購入固定後に照合。','',
       '|項目|結果|','|---|---:|',f'|購入レース数|{len(races)}|',f'|的中レース数|{hits}|',f'|レース的中率|{rate:.1f}%|',f'|総投資|{st:,}円|',f'|総払戻|{ret:,}円|',f'|回収率|{roi:.1f}%|',f'|平均点数/レース|{(len(bets)/len(races) if races else 0):.1f}|',f'|平均合成オッズ|{(sum(r["composite_odds"] for r in races)/len(races) if races else 0):.2f}倍|',f'|平均校正的中確率|{(sum(r["set_prob_cal"] for r in races)/len(races)*100 if races else 0):.1f}%|','',
       '## 校正期間','|項目|結果|','|---|---:|',f'|集合サンプル|{cal_n}|',f'|集合実測的中|{cal_hit}|',f'|集合実測的中率|{cal_rate:.1f}%|','',
       '## 頭別の的中買い目','|頭|的中数|払戻寄与|','|---|---:|---:|']
    for h in [3,4,5]:
        hb=[b for b in bets if b['head']==h and b['hit']]
        L.append(f'|{h}頭|{len(hb)}|{sum(b["return_v10"] for b in hb):,}円|')
    L+=['','## 日次別','|日次|レース|的中|的中率|回収率|','|---|---:|---:|---:|---:|']
    for dc in ['初日','2日目','3日目以降']:
        rs=[r for r in races if r['day_cat']==dc]; codes={r['race_code'] for r in rs}; bs=[b for b in bets if b['race_code'] in codes]
        h=sum(r['hit'] for r in rs); s=sum(b['stake_v10'] for b in bs); rr=sum(b['return_v10'] for b in bs)
        L.append(f'|{dc}|{len(rs)}|{h}|{(h/len(rs)*100 if rs else 0):.1f}%|{(rr/s*100 if s else 0):.1f}%|')
    open('summary_v10.md','w',encoding='utf-8').write('\n'.join(L)+'\n')

if __name__=='__main__': main()
