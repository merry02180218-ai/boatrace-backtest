from backtest import *
from backtest_v4 import add_features, score4v4, score45v4, ingest_prior_day_preview
from backtest_v3 import infer_day_from_slots, ingest_motor
from collections import defaultdict
from datetime import date, timedelta

TRAIN_START=date(2026,6,1); TRAIN_END=date(2026,8,2)
TEST_START=date(2026,8,3); TEST_END=date(2026,9,2)
PRELOAD_START=date(2026,5,1)
EV_MIN=1.15
MAX_TICKETS_PER_HEAD=3
HEAD_SCORE_MIN=60.0

def combos_for_head(h):
    out=[]
    for b in range(1,7):
        if b==h: continue
        for c in range(1,7):
            if c==h or c==b: continue
            out.append(f'{h}-{b}-{c}')
    return out

def cal_prob(samples, score):
    # Local empirical calibration with shrinkage to overall training head rate.
    if not samples: return .08
    base=sum(y for _,y in samples)/len(samples)
    radius=8.0
    sw=sy=0.0
    for s,y in samples:
        d=abs(s-score)
        if d<=radius:
            w=max(.05,1-d/radius)
            sw+=w; sy+=w*y
    prior_n=18.0
    return (sy+prior_n*base)/(sw+prior_n)

def market_conditional(odrow, head):
    arr=[]
    for combo in combos_for_head(head):
        o=f(odrow.get('3連単_'+combo),0)
        if o>0: arr.append((combo,o,1/o))
    z=sum(x[2] for x in arr)
    return [(c,o,imp/z if z else 0) for c,o,imp in arr]

def daycat(r,titles):
    code=r['レースコード']
    dn=daynum(titles.get(code,{}).get('日次','')) or infer_day_from_slots(r)
    return '初日' if dn==1 else ('2日目' if dn==2 else '3日目以降')

def process_features(day, cache, hist):
    ymd=day.strftime('%Y/%m/%d')
    cards=rows(f'data/programs/race_cards/{ymd}.csv')
    w10={r['レースコード']:r for r in rows(f'data/programs/waku10/{ymd}.csv')}
    titles={r['レースコード']:r for r in rows(f'data/programs/title/{ymd}.csv')}
    feats=[]
    for r in cards:
        x=add_features(race_features(r,w10.get(r['レースコード'],{})),r,cache,hist)
        s4=score4v4(x); s5=score45v4(x,s4)
        feats.append((r,x,s4,s5,daycat(r,titles)))
    return feats

def main():
    cache={}; hist=defaultdict(list); seen=set()
    # Build only historical state that exists before each day.
    d=PRELOAD_START
    while d<TRAIN_START:
        ingest_motor(hist,seen,d)
        if d>=TRAIN_START-timedelta(days=12): ingest_prior_day_preview(cache,d)
        d+=timedelta(days=1)

    train4=[]; train5=[]
    d=TRAIN_START
    while d<=TRAIN_END:
        feats=process_features(d,cache,hist)
        ymd=d.strftime('%Y/%m/%d')
        res={r['レースコード']:r for r in rows(f'data/results/realtime/{ymd}.csv')}
        for r,x,s4,s5,dc in feats:
            rr=res.get(r['レースコード'],{})
            win=i(rr.get('1着_艇番'))
            train4.append((s4,1 if win==4 else 0))
            train5.append((s5,1 if win==5 else 0))
        ingest_prior_day_preview(cache,d); ingest_motor(hist,seen,d)
        d+=timedelta(days=1)

    bets=[]; race_rows=[]
    d=TEST_START
    while d<=TEST_END:
        feats=process_features(d,cache,hist)
        ymd=d.strftime('%Y/%m/%d')
        odds={r['レースコード']:r for r in rows(f'data/previews/od3/{ymd}.csv')}
        # Freeze ALL bets before outcomes/payouts are loaded.
        frozen=[]
        for r,x,s4,s5,dc in feats:
            code=r['レースコード']; od=odds.get(code,{})
            p4=cal_prob(train4,s4); p5=cal_prob(train5,s5)
            chosen=[]
            for head,sc,p in [(4,s4,p4),(5,s5,p5)]:
                if sc<HEAD_SCORE_MIN: continue
                cand=[]
                for combo,o,share in market_conditional(od,head):
                    pc=p*share; ev=pc*o
                    if ev>=EV_MIN:
                        cand.append((ev,combo,o,pc,share))
                cand.sort(reverse=True)
                for ev,combo,o,pc,share in cand[:MAX_TICKETS_PER_HEAD]:
                    chosen.append({'date':str(d),'race_code':code,'venue':r.get('レース場コード',''),'race':r.get('レース回',''),'day_cat':dc,'head':head,'combo':combo,'score':round(sc,2),'head_prob':round(p,4),'combo_prob':round(pc,5),'odds_pre':o,'ev_pre':round(ev,3),'market_within_head':round(share,5),'stake':100})
            if chosen:
                race_rows.append({'date':str(d),'race_code':code,'venue':r.get('レース場コード',''),'race':r.get('レース回',''),'day_cat':dc,'score4':round(s4,2),'score5':round(s5,2),'p4':round(p4,4),'p5':round(p5,4),'heads_bet':''.join(str(h) for h in sorted(set(z['head'] for z in chosen))),'tickets':len(chosen)})
                frozen.extend(chosen)
        # Outcomes are loaded only after all bets for the date are frozen.
        pay={r['レースコード']:r for r in rows(f'data/results/payouts/{ymd}.csv')}
        for b in frozen:
            pr=pay.get(b['race_code'],{}); hit=(pr.get('3連単_組番') or '').strip()==b['combo']
            payout=i(pr.get('3連単_払戻金')) if hit else 0
            b['hit']=int(hit); b['payout']=payout; b['profit']=payout-b['stake']
            b['actual_combo']=(pr.get('3連単_組番') or '').strip(); bets.append(b)
        ingest_prior_day_preview(cache,d); ingest_motor(hist,seen,d)
        d+=timedelta(days=1)

    if bets:
        with open('bets_v5.csv','w',newline='',encoding='utf-8-sig') as fo:
            w=csv.DictWriter(fo,fieldnames=list(bets[0].keys()));w.writeheader();w.writerows(bets)
    if race_rows:
        with open('races_v5.csv','w',newline='',encoding='utf-8-sig') as fo:
            w=csv.DictWriter(fo,fieldnames=list(race_rows[0].keys()));w.writeheader();w.writerows(race_rows)

    def agg(bs):
        n=len(bs); hits=sum(x['hit'] for x in bs); st=sum(x['stake'] for x in bs); ret=sum(x['payout'] for x in bs)
        return n,hits,st,ret,(ret/st*100 if st else 0)
    L=['# 2026-08-03〜2026-09-02 3連単EVバックテスト v5','',
       f'校正期間: {TRAIN_START}〜{TRAIN_END}。テスト期間: {TEST_START}〜{TEST_END}。テスト期間の結果は買い目固定後にのみ読み込み。',
       f'固定ルール: 4頭/5頭スコア60以上、締切約5分前od3使用、校正済み頭確率×頭内市場構成比×オッズでEV算出、EV>={EV_MIN}、各頭EV上位{MAX_TICKETS_PER_HEAD}点、1点100円。','',
       '|区分|購入点数|的中|投資|払戻|回収率|','|---|---:|---:|---:|---:|---:|']
    for name,bs in [('全体',bets),('4頭',[x for x in bets if x['head']==4]),('5頭',[x for x in bets if x['head']==5]),('両頭を買ったレース',[x for x in bets if any(r['race_code']==x['race_code'] and r['heads_bet']=='45' for r in race_rows)])]:
        n,h,st,ret,roi=agg(bs);L.append(f'|{name}|{n}|{h}|{st:,}円|{ret:,}円|{roi:.1f}%|')
    L+=['','## 日次別','|日次|点数|的中|回収率|','|---|---:|---:|---:|']
    for dc in ['初日','2日目','3日目以降']:
        bs=[x for x in bets if x['day_cat']==dc];n,h,st,ret,roi=agg(bs);L.append(f'|{dc}|{n}|{h}|{roi:.1f}%|')
    L+=['','## EV帯別','|事前EV|点数|的中|回収率|','|---|---:|---:|---:|']
    bands=[(1.15,1.30),(1.30,1.50),(1.50,2.00),(2.00,999)]
    for lo,hi in bands:
        bs=[x for x in bets if lo<=x['ev_pre']<hi];n,h,st,ret,roi=agg(bs);lab=f'{lo:.2f}〜{hi:.2f}' if hi<900 else f'{lo:.2f}以上';L.append(f'|{lab}|{n}|{h}|{roi:.1f}%|')
    dual=set(r['race_code'] for r in race_rows if r['heads_bet']=='45')
    L+=['','## レース数',f'- 購入レース: {len(set(x["race_code"] for x in bets))}',f'- 4頭と5頭の両方を購入したレース: {len(dual)}',f'- 総購入点数: {len(bets)}','','## 注意','- od3は確定オッズではなく締切約5分前の集計中オッズ。払戻は実際の確定払戻を使用。','- 頭確率の校正はテスト期間より前の6/1〜8/2のみ。','- 3連単の相手順位確率は、その頭の20通り内で1/オッズを正規化した市場構成比を使用。市場情報を相手選びに使い、4頭/5頭の根本確率をモデル側で上書きする設計。','- これは1か月の試験であり、閾値1.15や3点上限をテスト結果に合わせて最適化していない。']
    open('summary_v5.md','w',encoding='utf-8').write('\n'.join(L)+'\n')

if __name__=='__main__': main()
