from backtest import *
from backtest_v4 import ingest_prior_day_preview, score3v4
from backtest_v3 import ingest_motor
from backtest_v5_ev import PRELOAD_START, TEST_START, TEST_END, cal_prob, market_conditional, process_features
from collections import defaultdict
from datetime import date,timedelta

TRAIN_START=date(2026,6,1); TRAIN_END=date(2026,7,15)
CAL_START=date(2026,7,16); CAL_END=date(2026,8,2)
S3_MIN=65.0; MIN_COMPOSITE=5.0; BUDGET=5000


def composite(items):
    s=sum(1/z['odds'] for z in items if z['odds']>0)
    return 1/s if s>0 else 999.0


def pair_key(combo):
    a=combo.split('-')
    return (int(a[1]),int(a[2])) if len(a)==3 else None


def build_pair_dist(pair_counts, market_rows, alpha=8.0):
    # empirical conditional pair distribution among 3-head makuri/MS, shrunk to current market conditional distribution
    total=sum(pair_counts.values())
    out=[]
    for combo,o,share in market_rows:
        k=pair_key(combo)
        cnt=pair_counts.get(k,0)
        q=(cnt + alpha*share)/(total+alpha) if total+alpha>0 else share
        out.append((combo,o,q,share,cnt))
    s=sum(z[2] for z in out)
    return [(c,o,q/s if s else sh,sh,cnt) for c,o,q,sh,cnt in out]


def select_set(r,s3,p3,od,pair_counts):
    if s3<S3_MIN: return []
    mr=market_conditional(od,3)
    dist=build_pair_dist(pair_counts,mr)
    cand=[]
    for combo,o,q,share,cnt in dist:
        pc=p3*q
        cand.append({'combo':combo,'odds':o,'pair_prob':q,'combo_prob':pc,'market_share':share,'train_pair_count':cnt,'ev':pc*o})
    # prioritize probability coverage; use EV as tiebreaker
    cand.sort(key=lambda z:(z['combo_prob'],z['ev']),reverse=True)
    chosen=[]
    for z in cand:
        tr=chosen+[z]
        if composite(tr)>=MIN_COMPOSITE:
            chosen=tr
    return chosen


def load_period_features(start,end,cache,hist,seen,train3=None,pair_counts=None,collect_results=False):
    rowsout=[]; d=start
    while d<=end:
        feats=process_features(d,cache,hist); ymd=d.strftime('%Y/%m/%d')
        res={r['レースコード']:r for r in rows(f'data/results/realtime/{ymd}.csv')} if collect_results else {}
        pay={r['レースコード']:r for r in rows(f'data/results/payouts/{ymd}.csv')} if collect_results else {}
        for r,x,s4,s5,dc in feats:
            s3=score3v4(x)
            if collect_results:
                rr=res.get(r['レースコード'],{}); win=i(rr.get('1着_艇番')); kim=(rr.get('決まり手') or '').replace('　','').replace(' ','')
                y=1 if win==3 and kim in ('まくり','まくり差し') else 0
                if train3 is not None: train3.append((s3,y))
                if pair_counts is not None and y:
                    actual=(pay.get(r['レースコード'],{}).get('3連単_組番') or '').strip()
                    k=pair_key(actual)
                    if k: pair_counts[k]+=1
            rowsout.append((d,r,x,s3,dc))
        ingest_prior_day_preview(cache,d); ingest_motor(hist,seen,d); d+=timedelta(days=1)
    return rowsout


def main():
    cache={}; hist=defaultdict(list); seen=set(); d=PRELOAD_START
    while d<TRAIN_START:
        ingest_motor(hist,seen,d)
        if d>=TRAIN_START-timedelta(days=12): ingest_prior_day_preview(cache,d)
        d+=timedelta(days=1)

    train3=[]; pair_counts=defaultdict(int)
    load_period_features(TRAIN_START,TRAIN_END,cache,hist,seen,train3,pair_counts,True)

    # pre-test calibration period: use frozen rules and measure actual race hit rate, but do not alter pair counts
    cal=[]; d=CAL_START
    while d<=CAL_END:
        feats=process_features(d,cache,hist); ymd=d.strftime('%Y/%m/%d')
        ods={r['レースコード']:r for r in rows(f'data/previews/od3/{ymd}.csv')}
        pay={r['レースコード']:r for r in rows(f'data/results/payouts/{ymd}.csv')}
        for r,x,s4,s5,dc in feats:
            s3=score3v4(x); p3=cal_prob(train3,s3)
            chosen=select_set(r,s3,p3,ods.get(r['レースコード'],{}),pair_counts)
            if not chosen: continue
            actual=(pay.get(r['レースコード'],{}).get('3連単_組番') or '').strip()
            cal.append((s3,p3,composite(chosen),len(chosen),1 if any(z['combo']==actual for z in chosen) else 0))
        ingest_prior_day_preview(cache,d); ingest_motor(hist,seen,d); d+=timedelta(days=1)

    bets=[]; races=[]; d=TEST_START
    while d<=TEST_END:
        feats=process_features(d,cache,hist); ymd=d.strftime('%Y/%m/%d')
        ods={r['レースコード']:r for r in rows(f'data/previews/od3/{ymd}.csv')}
        frozen=[]
        for r,x,s4,s5,dc in feats:
            s3=score3v4(x); p3=cal_prob(train3,s3)
            chosen=select_set(r,s3,p3,ods.get(r['レースコード'],{}),pair_counts)
            if not chosen: continue
            co=composite(chosen); n=len(chosen)
            # 100 yen minimum, distribute rest by combo probability
            for z in chosen: z['stake']=100
            remain=BUDGET-100*n
            if remain>0:
                units=remain//100; sw=sum(z['combo_prob'] for z in chosen)
                raw=[units*z['combo_prob']/sw for z in chosen]; add=[int(v) for v in raw]
                left=units-sum(add); order=sorted(range(n),key=lambda k:raw[k]-add[k],reverse=True)
                for k in order[:left]: add[k]+=1
                for z,a in zip(chosen,add): z['stake']+=100*a
            for z in chosen:
                z.update({'date':str(d),'race_code':r['レースコード'],'venue':r.get('レース場コード',''),'race':r.get('レース回',''),'day_cat':dc,'score3':round(s3,2),'p3':round(p3,4),'composite_odds':round(co,2),'tickets':n})
            races.append({'date':str(d),'race_code':r['レースコード'],'venue':r.get('レース場コード',''),'race':r.get('レース回',''),'day_cat':dc,'score3':round(s3,2),'p3':round(p3,4),'composite_odds':round(co,2),'tickets':n})
            frozen.extend(chosen)
        pay={r['レースコード']:r for r in rows(f'data/results/payouts/{ymd}.csv')}
        for b in frozen:
            pr=pay.get(b['race_code'],{}); actual=(pr.get('3連単_組番') or '').strip(); hit=actual==b['combo']
            b['actual_combo']=actual; b['hit']=int(hit); b['payout100']=i(pr.get('3連単_払戻金')) if hit else 0
            b['return']=b['payout100']*(b['stake']//100) if hit else 0; bets.append(b)
        ingest_prior_day_preview(cache,d); ingest_motor(hist,seen,d); d+=timedelta(days=1)

    for r in races:
        bs=[b for b in bets if b['race_code']==r['race_code']]; r['hit']=int(any(b['hit'] for b in bs)); r['return']=sum(b['return'] for b in bs)

    with open('bets_v11_3pair.csv','w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=list(bets[0].keys())); w.writeheader(); w.writerows(bets)
    with open('races_v11_3pair.csv','w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=list(races[0].keys())); w.writeheader(); w.writerows(races)

    st=sum(b['stake'] for b in bets); ret=sum(b['return'] for b in bets); hits=sum(r['hit'] for r in races)
    calhits=sum(x[-1] for x in cal)
    # pattern table among successful training 3-head races
    pattern=[]
    for (s,t),cnt in sorted(pair_counts.items(), key=lambda kv:kv[1], reverse=True): pattern.append((f'3-{s}-{t}',cnt))
    L=['# v11 3号艇まくり/MS 相手モデル','',f'学習 {TRAIN_START}〜{TRAIN_END}、校正 {CAL_START}〜{CAL_END}、テスト {TEST_START}〜{TEST_END}。','3号艇score>=65。3頭の条件付き2・3着分布を学習期間の実績から作り、当日市場構成比へ縮約。買い目は予測確率順に追加し、合成オッズ5倍以上を維持。1R最大5,000円。テスト結果は買い目固定後に照合。','',
       '## 結果','|項目|値|','|---|---:|',f'|購入レース|{len(races)}|',f'|的中レース|{hits}|',f'|レース的中率|{(hits/len(races)*100 if races else 0):.1f}%|',f'|総投資|{st:,}円|',f'|総払戻|{ret:,}円|',f'|回収率|{(ret/st*100 if st else 0):.1f}%|',f'|平均点数|{(len(bets)/len(races) if races else 0):.1f}|',f'|平均合成オッズ|{(sum(r["composite_odds"] for r in races)/len(races) if races else 0):.2f}倍|','',
       '## 校正期間','|レース|的中|的中率|','|---:|---:|---:|',f'|{len(cal)}|{calhits}|{(calhits/len(cal)*100 if cal else 0):.1f}%|','',
       '## 学習期間の3頭的中時 2・3着パターン上位','|組み合わせ|回数|','|---|---:|']
    for combo,cnt in pattern[:12]: L.append(f'|{combo}|{cnt}|')
    L+=['','## テスト的中レース','|日付|場|R|score3|結果|払戻/100円|点数|合成|','|---|---:|---:|---:|---|---:|---:|---:|']
    for r in races:
        if not r['hit']: continue
        bs=[b for b in bets if b['race_code']==r['race_code'] and b['hit']]; b=bs[0]
        L.append(f'|{r["date"]}|{r["venue"]}|{r["race"]}|{r["score3"]:.2f}|{b["actual_combo"]}|{b["payout100"]:,}円|{r["tickets"]}|{r["composite_odds"]:.2f}倍|')
    open('summary_v11_3pair.md','w',encoding='utf-8').write('\n'.join(L)+'\n')

if __name__=='__main__': main()
