from backtest import *
from backtest_v4 import ingest_prior_day_preview
from backtest_v3 import ingest_motor
from backtest_v5_ev import PRELOAD_START,TEST_START,TEST_END,EV_MIN,HEAD_SCORE_MIN,cal_prob,market_conditional,process_features
from collections import defaultdict
from datetime import date,timedelta

HEAD_TRAIN_START=date(2026,6,1); HEAD_TRAIN_END=date(2026,7,15)
SET_CAL_START=date(2026,7,16); SET_CAL_END=date(2026,8,2)
MIN_COMPOSITE=5.0
MIN_SET_PROB=0.20
RACE_BUDGET=5000

def composite_odds(items):
    s=sum(1/x['odds_pre'] for x in items if x['odds_pre']>0)
    return 1/s if s>0 else 999.0

def build_set(r,s4,s5,dc,od,train4,train5,d):
    p4=cal_prob(train4,s4); p5=cal_prob(train5,s5)
    cand=[]
    for head,sc,p in [(4,s4,p4),(5,s5,p5)]:
        if sc<HEAD_SCORE_MIN: continue
        for combo,o,share in market_conditional(od,head):
            pc=p*share; ev=pc*o
            if ev>=EV_MIN:
                cand.append({'date':str(d),'race_code':r['レースコード'],'venue':r.get('レース場コード',''),'race':r.get('レース回',''),'day_cat':dc,'head':head,'combo':combo,'score':round(sc,2),'head_prob':p,'combo_prob':pc,'odds_pre':o,'ev_pre':ev})
    cand.sort(key=lambda z:z['ev_pre'],reverse=True)
    chosen=[]
    for z in cand:
        trial=chosen+[z]
        if composite_odds(trial)>=MIN_COMPOSITE:
            chosen=trial
    return chosen,p4,p5

def set_raw_prob(chosen):
    return min(.95,sum(x['combo_prob'] for x in chosen))

def calibrate_set_prob(samples, rawp, co, tickets):
    if not samples: return rawp
    # Similarity calibration on only the pre-test set-calibration period.
    # Distance combines raw model coverage, log composite odds, and ticket count.
    vals=[]
    for rp,c,t,y in samples:
        d=abs(rp-rawp)/0.08 + abs(__import__('math').log(max(c,1.01))-__import__('math').log(max(co,1.01)))/0.7 + abs(t-tickets)/20.0
        vals.append((d,y))
    vals.sort(key=lambda x:x[0])
    near=vals[:min(80,len(vals))]
    sw=sy=0.0
    for d,y in near:
        w=1/(1+d)
        sw+=w; sy+=w*y
    base=sum(y for *_,y in samples)/len(samples)
    prior_n=12.0
    return (sy+prior_n*base)/(sw+prior_n)

def allocate(chosen):
    n=len(chosen)
    if n==0: return
    # Minimum 100 each. If >50 tickets, budget cannot cover all at 100; retain top-EV 50.
    if n>50:
        del chosen[50:]
        n=50
    for z in chosen: z['stake_v9']=100
    remain=RACE_BUDGET-100*n
    if remain<=0: return
    weights=[max(.01,z['ev_pre']-1.0) for z in chosen]
    sw=sum(weights)
    units=remain//100
    raw=[units*w/sw for w in weights]
    add=[int(x) for x in raw]
    left=units-sum(add)
    order=sorted(range(n),key=lambda k:raw[k]-add[k],reverse=True)
    for k in order[:left]: add[k]+=1
    for z,a in zip(chosen,add): z['stake_v9']+=100*a

def main():
    cache={}; hist=defaultdict(list); seen=set(); d=PRELOAD_START
    while d<HEAD_TRAIN_START:
        ingest_motor(hist,seen,d)
        if d>=HEAD_TRAIN_START-timedelta(days=12): ingest_prior_day_preview(cache,d)
        d+=timedelta(days=1)

    train4=[]; train5=[]
    d=HEAD_TRAIN_START
    while d<=HEAD_TRAIN_END:
        feats=process_features(d,cache,hist); ymd=d.strftime('%Y/%m/%d')
        res={r['レースコード']:r for r in rows(f'data/results/realtime/{ymd}.csv')}
        for r,x,s4,s5,dc in feats:
            win=i(res.get(r['レースコード'],{}).get('1着_艇番'))
            train4.append((s4,1 if win==4 else 0)); train5.append((s5,1 if win==5 else 0))
        ingest_prior_day_preview(cache,d); ingest_motor(hist,seen,d); d+=timedelta(days=1)

    set_samples=[]
    d=SET_CAL_START
    while d<=SET_CAL_END:
        feats=process_features(d,cache,hist); ymd=d.strftime('%Y/%m/%d')
        odds={r['レースコード']:r for r in rows(f'data/previews/od3/{ymd}.csv')}
        pay={r['レースコード']:r for r in rows(f'data/results/payouts/{ymd}.csv')}
        for r,x,s4,s5,dc in feats:
            chosen,p4,p5=build_set(r,s4,s5,dc,odds.get(r['レースコード'],{}),train4,train5,d)
            if not chosen: continue
            actual=(pay.get(r['レースコード'],{}).get('3連単_組番') or '').strip()
            y=1 if any(z['combo']==actual for z in chosen) else 0
            set_samples.append((set_raw_prob(chosen),composite_odds(chosen),len(chosen),y))
        ingest_prior_day_preview(cache,d); ingest_motor(hist,seen,d); d+=timedelta(days=1)

    bets=[]; races=[]; d=TEST_START
    while d<=TEST_END:
        feats=process_features(d,cache,hist); ymd=d.strftime('%Y/%m/%d')
        odds={r['レースコード']:r for r in rows(f'data/previews/od3/{ymd}.csv')}
        frozen=[]
        for r,x,s4,s5,dc in feats:
            chosen,p4,p5=build_set(r,s4,s5,dc,odds.get(r['レースコード'],{}),train4,train5,d)
            if not chosen: continue
            rawp=set_raw_prob(chosen); co=composite_odds(chosen); cp=calibrate_set_prob(set_samples,rawp,co,len(chosen))
            if cp<MIN_SET_PROB: continue
            allocate(chosen)
            if not chosen: continue
            co=composite_odds(chosen)
            heads=''.join(str(h) for h in sorted(set(z['head'] for z in chosen)))
            for z in chosen:
                z['set_prob_raw']=round(rawp,4); z['set_prob_cal']=round(cp,4); z['composite_odds_race']=round(co,2); z['tickets_race']=len(chosen)
            races.append({'date':str(d),'race_code':r['レースコード'],'venue':r.get('レース場コード',''),'race':r.get('レース回',''),'day_cat':dc,'score4':round(s4,2),'score5':round(s5,2),'p4':round(p4,4),'p5':round(p5,4),'set_prob_raw':round(rawp,4),'set_prob_cal':round(cp,4),'heads_bet':heads,'tickets':len(chosen),'composite_odds':round(co,2)})
            frozen.extend(chosen)
        pay={r['レースコード']:r for r in rows(f'data/results/payouts/{ymd}.csv')}
        for b in frozen:
            pr=pay.get(b['race_code'],{}); actual=(pr.get('3連単_組番') or '').strip(); hit=actual==b['combo']
            b['hit']=int(hit); b['actual_combo']=actual; b['payout100']=i(pr.get('3連単_払戻金')) if hit else 0
            b['return_v9']=b['payout100']*(b['stake_v9']//100) if hit else 0
            bets.append(b)
        ingest_prior_day_preview(cache,d); ingest_motor(hist,seen,d); d+=timedelta(days=1)

    race_hit={}
    for r in races:
        bs=[b for b in bets if b['race_code']==r['race_code']]
        race_hit[r['race_code']]=1 if any(b['hit'] for b in bs) else 0
    for r in races: r['hit']=race_hit[r['race_code']]

    if bets:
        with open('bets_v9.csv','w',newline='',encoding='utf-8-sig') as f1:
            w=csv.DictWriter(f1,fieldnames=list(bets[0].keys()));w.writeheader();w.writerows(bets)
    if races:
        with open('races_v9.csv','w',newline='',encoding='utf-8-sig') as f1:
            w=csv.DictWriter(f1,fieldnames=list(races[0].keys()));w.writeheader();w.writerows(races)

    st=sum(b['stake_v9'] for b in bets); ret=sum(b['return_v9'] for b in bets); hits=sum(r['hit'] for r in races)
    rate=hits/len(races)*100 if races else 0; roi=ret/st*100 if st else 0
    L=['# v9 的中率20%優先・合成5倍・1R5000円','',
       f'頭確率学習: {HEAD_TRAIN_START}〜{HEAD_TRAIN_END}。集合的中率校正: {SET_CAL_START}〜{SET_CAL_END}。テスト: {TEST_START}〜{TEST_END}。',
       f'購入条件: 校正済み買い目集合的中確率>={MIN_SET_PROB*100:.0f}% かつ合成オッズ>={MIN_COMPOSITE}倍。テスト期間の結果は購入固定後にのみ照合。','',
       '|項目|結果|','|---|---:|',f'|購入レース数|{len(races)}|',f'|的中レース数|{hits}|',f'|レース的中率|{rate:.1f}%|',f'|総投資|{st:,}円|',f'|総払戻|{ret:,}円|',f'|回収率|{roi:.1f}%|',f'|平均点数/レース|{(len(bets)/len(races) if races else 0):.1f}|',f'|平均合成オッズ|{(sum(r["composite_odds"] for r in races)/len(races) if races else 0):.2f}倍|',f'|平均校正的中確率|{(sum(r["set_prob_cal"] for r in races)/len(races)*100 if races else 0):.1f}%|','',
       '## 日次別','|日次|レース|的中|的中率|回収率|','|---|---:|---:|---:|---:|']
    for dc in ['初日','2日目','3日目以降']:
        rs=[r for r in races if r['day_cat']==dc]; codes={r['race_code'] for r in rs}; bs=[b for b in bets if b['race_code'] in codes]
        h=sum(r['hit'] for r in rs); s=sum(b['stake_v9'] for b in bs); rr=sum(b['return_v9'] for b in bs)
        L.append(f'|{dc}|{len(rs)}|{h}|{(h/len(rs)*100 if rs else 0):.1f}%|{(rr/s*100 if s else 0):.1f}%|')
    L+=['','## 校正期間の集合サンプル',f'- サンプル数: {len(set_samples)}',f'- 実測的中率: {(sum(y for *_,y in set_samples)/len(set_samples)*100 if set_samples else 0):.1f}%','- 20%は市場の合成オッズから直接仮定せず、テスト前の集合実績から校正して判定。']
    open('summary_v9.md','w',encoding='utf-8').write('\n'.join(L)+'\n')

if __name__=='__main__': main()
