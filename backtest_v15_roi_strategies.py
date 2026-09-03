from backtest import *
from backtest_v4 import ingest_prior_day_preview, score3v4
from backtest_v3 import ingest_motor
from backtest_v5_ev import PRELOAD_START, TEST_START, TEST_END, cal_prob, process_features
from backtest_v13_selective3 import make_bets, composite
from collections import defaultdict
from datetime import date,timedelta
import csv

TRAIN_START=date(2026,6,1); TRAIN_END=date(2026,7,15)
SEL_START=date(2026,7,16); SEL_END=date(2026,8,2)
BASE_SCORE=68.0
BUDGET_A=5000; BUDGET_B=2000


def pair_key(combo):
    a=(combo or '').split('-')
    return (int(a[1]),int(a[2])) if len(a)==3 and all(x.isdigit() for x in a) else None


def alloc_prob(chosen,budget):
    if not chosen:return []
    out=[dict(z) for z in chosen]
    n=len(out); base=100*n
    if base>budget:
        out=out[:budget//100]; n=len(out); base=100*n
    for z in out:z['stake']=100
    rem=budget-base
    if rem<=0:return out
    units=rem//100; sw=sum(z['combo_prob'] for z in out) or 1
    raw=[units*z['combo_prob']/sw for z in out]; add=[int(v) for v in raw]
    left=units-sum(add); order=sorted(range(n),key=lambda k:raw[k]-add[k],reverse=True)
    for k in order[:left]:add[k]+=1
    for z,a in zip(out,add):z['stake']+=100*a
    return out


def alloc_thick(chosen,budget):
    if not chosen:return []
    out=[dict(z) for z in chosen]
    n=len(out); base=100*n
    if base>budget:
        out=out[:budget//100]; n=len(out); base=100*n
    for z in out:z['stake']=100
    rem=budget-base
    if rem<=0:return out
    main=[i for i,z in enumerate(out) if pair_key(z['combo']) and pair_key(z['combo'])[0] in (1,4)]
    sub=[i for i in range(n) if i not in main]
    # 70% of discretionary bankroll to 3-1 / 3-4, 30% to other coverage.
    buckets=[(main,int((rem//100)*0.70)),(sub,(rem//100)-int((rem//100)*0.70))]
    for idxs,units in buckets:
        if not idxs or units<=0:continue
        sw=sum(out[i]['combo_prob'] for i in idxs) or 1
        raw=[units*out[i]['combo_prob']/sw for i in idxs]; add=[int(v) for v in raw]
        left=units-sum(add); order=sorted(range(len(idxs)),key=lambda k:raw[k]-add[k],reverse=True)
        for k in order[:left]:add[k]+=1
        for i,a in zip(idxs,add):out[i]['stake']+=100*a
    return out


def choose_a_threshold(sel_scores):
    # Freeze threshold using selection period only. Target ~15-20 races per 31-day month.
    best=None
    for th in [68,69,70,71,72,73,74,75]:
        n=sum(1 for s in sel_scores if s>=th); proj=n*31/18
        if n==0:continue
        penalty=abs(proj-17.5)
        cand=(penalty,-th,th,n,proj)
        if best is None or cand<best:best=cand
    return best[2],best[3],best[4]


def max_losing_streak(rows):
    m=c=0
    for r in rows:
        if r['hit']:c=0
        else:c+=1;m=max(m,c)
    return m


def main():
    cache={};hist=defaultdict(list);seen=set();d=PRELOAD_START
    while d<TRAIN_START:
        ingest_motor(hist,seen,d)
        if d>=TRAIN_START-timedelta(days=12):ingest_prior_day_preview(cache,d)
        d+=timedelta(days=1)

    train3=[];pair_counts=defaultdict(int)
    d=TRAIN_START
    while d<=TRAIN_END:
        feats=process_features(d,cache,hist);ymd=d.strftime('%Y/%m/%d')
        res={r['レースコード']:r for r in rows(f'data/results/realtime/{ymd}.csv')}
        pay={r['レースコード']:r for r in rows(f'data/results/payouts/{ymd}.csv')}
        for r,x,s4,s5,dc in feats:
            s3=score3v4(x); rr=res.get(r['レースコード'],{}); win=i(rr.get('1着_艇番')); kim=(rr.get('決まり手') or '').replace('　','').replace(' ','')
            y=int(win==3 and kim in ('まくり','まくり差し')); train3.append((s3,y))
            if y:
                k=pair_key((pay.get(r['レースコード'],{}).get('3連単_組番') or '').strip())
                if k:pair_counts[k]+=1
        ingest_prior_day_preview(cache,d);ingest_motor(hist,seen,d);d+=timedelta(days=1)

    sel_scores=[];d=SEL_START
    while d<=SEL_END:
        feats=process_features(d,cache,hist)
        for r,x,s4,s5,dc in feats:
            s3=score3v4(x)
            if s3>=BASE_SCORE:sel_scores.append(s3)
        ingest_prior_day_preview(cache,d);ingest_motor(hist,seen,d);d+=timedelta(days=1)
    a_th,a_n,a_proj=choose_a_threshold(sel_scores)

    racebase=[];d=TEST_START
    while d<=TEST_END:
        feats=process_features(d,cache,hist);ymd=d.strftime('%Y/%m/%d')
        ods={r['レースコード']:r for r in rows(f'data/previews/od3/{ymd}.csv')}
        frozen=[]
        for r,x,s4,s5,dc in feats:
            s3=score3v4(x)
            if s3<BASE_SCORE:continue
            p3=cal_prob(train3,s3); chosen=make_bets(s3,p3,ods.get(r['レースコード'],{}),pair_counts)
            if not chosen:continue
            frozen.append({'date':str(d),'race_code':r['レースコード'],'venue':r.get('レース場コード',''),'race':r.get('レース回',''),'score3':s3,'p3':p3,'rank':'A' if s3>=a_th else 'B','chosen':chosen})
        # outcomes joined only after all race decisions on the date are frozen
        pay={r['レースコード']:r for r in rows(f'data/results/payouts/{ymd}.csv')}
        for q in frozen:
            pr=pay.get(q['race_code'],{}); q['actual']=(pr.get('3連単_組番') or '').strip(); q['payout100']=i(pr.get('3連単_払戻金'))
            racebase.append(q)
        ingest_prior_day_preview(cache,d);ingest_motor(hist,seen,d);d+=timedelta(days=1)

    strategies={
      '①現行v13': lambda q: alloc_prob(q['chosen'],5000),
      '②A限定': lambda q: alloc_prob(q['chosen'],5000) if q['rank']=='A' else [],
      '③A5000/B2000': lambda q: alloc_prob(q['chosen'],5000 if q['rank']=='A' else 2000),
      '④A限定+3-1/3-4厚張り': lambda q: alloc_thick(q['chosen'],5000) if q['rank']=='A' else [],
    }
    summaries=[];detail=[]
    for name,fn in strategies.items():
        rr=[]
        for q in racebase:
            bets=fn(q)
            if not bets:continue
            stake=sum(z['stake'] for z in bets); ret=0; hit=0
            for z in bets:
                if z['combo']==q['actual']:
                    hit=1; ret=q['payout100']*(z['stake']//100)
            rr.append({'strategy':name,'date':q['date'],'race_code':q['race_code'],'venue':q['venue'],'race':q['race'],'score3':round(q['score3'],2),'rank':q['rank'],'tickets':len(bets),'stake':stake,'actual':q['actual'],'hit':hit,'return':ret})
        st=sum(z['stake'] for z in rr); ret=sum(z['return'] for z in rr); hits=sum(z['hit'] for z in rr)
        summaries.append({'strategy':name,'races':len(rr),'hits':hits,'hit_rate':hits/len(rr)*100 if rr else 0,'stake':st,'return':ret,'profit':ret-st,'roi':ret/st*100 if st else 0,'max_losing_streak':max_losing_streak(rr),'avg_tickets':sum(z['tickets'] for z in rr)/len(rr) if rr else 0})
        detail.extend(rr)

    with open('races_v15_strategies.csv','w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=list(detail[0].keys()));w.writeheader();w.writerows(detail)
    L=['# v15 回収率改善4戦略比較','',f'学習 {TRAIN_START}〜{TRAIN_END}、A/B境界決定 {SEL_START}〜{SEL_END}、完全テスト {TEST_START}〜{TEST_END}。','v13のscore3>=68選別とv11型買い目を土台に、テスト結果を見ずにA/B境界を固定。','',f'- Aランク閾値: score3 >= {a_th:.1f}',f'- 選別期間A候補: {a_n}R / 月換算 {a_proj:.1f}R','',
       '|戦略|購入R|的中|的中率|投資|払戻|利益|回収率|最大連敗|平均点数|','|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for s in summaries:
        L.append(f"|{s['strategy']}|{s['races']}|{s['hits']}|{s['hit_rate']:.1f}%|{s['stake']:,}円|{s['return']:,}円|{s['profit']:+,}円|{s['roi']:.1f}%|{s['max_losing_streak']}|{s['avg_tickets']:.1f}|")
    L+=['','## 注記','- ④は選択買い目を増減せず、裁量資金の70%を3-1/3-4系、30%をその他へ配分。','- 1R上限5,000円。③のBランクのみ2,000円。','- 結果・払戻は各日の買い目凍結後に照合。']
    open('summary_v15_strategies.md','w',encoding='utf-8').write('\n'.join(L)+'\n')

if __name__=='__main__':main()
