from backtest import *
from backtest_v4 import ingest_prior_day_preview
from backtest_v3 import ingest_motor
from backtest_v5_ev import TRAIN_START,TRAIN_END,TEST_START,TEST_END,PRELOAD_START,EV_MIN,HEAD_SCORE_MIN,cal_prob,market_conditional,process_features
from collections import defaultdict
from datetime import timedelta

MIN_COMPOSITE=5.0

def composite_odds(items):
    s=sum(1/x['odds_pre'] for x in items if x['odds_pre']>0)
    return 1/s if s>0 else 999.0

def main():
    cache={}; hist=defaultdict(list); seen=set(); d=PRELOAD_START
    while d<TRAIN_START:
        ingest_motor(hist,seen,d)
        if d>=TRAIN_START-timedelta(days=12): ingest_prior_day_preview(cache,d)
        d+=timedelta(days=1)

    train4=[]; train5=[]
    d=TRAIN_START
    while d<=TRAIN_END:
        feats=process_features(d,cache,hist); ymd=d.strftime('%Y/%m/%d')
        res={r['レースコード']:r for r in rows(f'data/results/realtime/{ymd}.csv')}
        for r,x,s4,s5,dc in feats:
            win=i(res.get(r['レースコード'],{}).get('1着_艇番'))
            train4.append((s4,1 if win==4 else 0)); train5.append((s5,1 if win==5 else 0))
        ingest_prior_day_preview(cache,d); ingest_motor(hist,seen,d); d+=timedelta(days=1)

    bets=[]; races=[]; d=TEST_START
    while d<=TEST_END:
        feats=process_features(d,cache,hist); ymd=d.strftime('%Y/%m/%d')
        odds={r['レースコード']:r for r in rows(f'data/previews/od3/{ymd}.csv')}
        frozen=[]
        for r,x,s4,s5,dc in feats:
            code=r['レースコード']; od=odds.get(code,{})
            p4=cal_prob(train4,s4); p5=cal_prob(train5,s5)
            cand=[]
            for head,sc,p in [(4,s4,p4),(5,s5,p5)]:
                if sc<HEAD_SCORE_MIN: continue
                for combo,o,share in market_conditional(od,head):
                    pc=p*share; ev=pc*o
                    if ev>=EV_MIN:
                        cand.append({'date':str(d),'race_code':code,'venue':r.get('レース場コード',''),'race':r.get('レース回',''),'day_cat':dc,'head':head,'combo':combo,'score':round(sc,2),'head_prob':round(p,4),'combo_prob':round(pc,5),'odds_pre':o,'ev_pre':round(ev,3),'market_within_head':round(share,5),'stake':100})
            cand.sort(key=lambda z:z['ev_pre'],reverse=True)
            chosen=[]
            for z in cand:
                trial=chosen+[z]
                if composite_odds(trial)>=MIN_COMPOSITE:
                    chosen=trial
            if chosen:
                co=composite_odds(chosen); heads=''.join(str(h) for h in sorted(set(z['head'] for z in chosen)))
                for z in chosen: z['composite_odds_race']=round(co,2); z['tickets_race']=len(chosen)
                races.append({'date':str(d),'race_code':code,'venue':r.get('レース場コード',''),'race':r.get('レース回',''),'day_cat':dc,'score4':round(s4,2),'score5':round(s5,2),'p4':round(p4,4),'p5':round(p5,4),'heads_bet':heads,'tickets':len(chosen),'composite_odds':round(co,2)})
                frozen.extend(chosen)
        pay={r['レースコード']:r for r in rows(f'data/results/payouts/{ymd}.csv')}
        for b in frozen:
            pr=pay.get(b['race_code'],{}); hit=(pr.get('3連単_組番') or '').strip()==b['combo']
            b['hit']=int(hit); b['payout']=i(pr.get('3連単_払戻金')) if hit else 0; b['actual_combo']=(pr.get('3連単_組番') or '').strip(); bets.append(b)
        ingest_prior_day_preview(cache,d); ingest_motor(hist,seen,d); d+=timedelta(days=1)

    with open('bets_v7.csv','w',newline='',encoding='utf-8-sig') as f1:
        w=csv.DictWriter(f1,fieldnames=list(bets[0].keys())); w.writeheader(); w.writerows(bets)
    with open('races_v7.csv','w',newline='',encoding='utf-8-sig') as f1:
        w=csv.DictWriter(f1,fieldnames=list(races[0].keys())); w.writeheader(); w.writerows(races)

    def agg(bs):
        st=sum(x['stake'] for x in bs); ret=sum(x['payout'] for x in bs)
        return len(bs),sum(x['hit'] for x in bs),st,ret,(ret/st*100 if st else 0)
    dual={r['race_code'] for r in races if r['heads_bet']=='45'}
    L=['# 2026-08-03〜2026-09-02 v7 点数上限なし・4/5完全混合・合成5倍','',
       '校正は6/1〜8/2のみ。テスト期間の結果は買い目固定後に読み込み。',
       f'固定ルール: 4/5頭score>=60、個別EV>={EV_MIN}。4頭・5頭候補を同一EV順に混合し、点数上限なしで、追加後も合成オッズ{MIN_COMPOSITE}倍以上を維持する買い目だけ採用。1点100円。','',
       '|区分|購入点数|的中|投資|払戻|回収率|','|---|---:|---:|---:|---:|---:|']
    for name,bs in [('全体',bets),('4頭',[x for x in bets if x['head']==4]),('5頭',[x for x in bets if x['head']==5]),('4+5両展開レース',[x for x in bets if x['race_code'] in dual])]:
        n,h,st,ret,roi=agg(bs); L.append(f'|{name}|{n}|{h}|{st:,}円|{ret:,}円|{roi:.1f}%|')
    avg_t=len(bets)/len(races) if races else 0; avg_c=sum(r['composite_odds'] for r in races)/len(races) if races else 0
    max_t=max((r['tickets'] for r in races),default=0); min_c=min((r['composite_odds'] for r in races),default=0)
    L+=['','## レース単位','|項目|値|','|---|---:|',f'|購入レース数|{len(races)}|',f'|両展開購入レース|{len(dual)}|',f'|平均点数/レース|{avg_t:.2f}|',f'|最大点数/レース|{max_t}|',f'|平均合成オッズ|{avg_c:.2f}倍|',f'|最低合成オッズ|{min_c:.2f}倍|']
    L+=['','## 日次別','|日次|点数|的中|回収率|','|---|---:|---:|---:|']
    for dc in ['初日','2日目','3日目以降']:
        bs=[x for x in bets if x['day_cat']==dc]; n,h,st,ret,roi=agg(bs); L.append(f'|{dc}|{n}|{h}|{roi:.1f}%|')
    L+=['','## 注意','- 合成オッズ=1/Σ(1/各買い目オッズ)。締切約5分前od3で計算。','- 払戻は確定払戻。','- 点数上限は設定していない。4頭・5頭を同じ候補列でEV順に扱う。']
    open('summary_v7.md','w',encoding='utf-8').write('\n'.join(L)+'\n')

if __name__=='__main__': main()
