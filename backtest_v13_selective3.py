from backtest import *
from backtest_v4 import ingest_prior_day_preview, score3v4, motor_attack
from backtest_v3 import ingest_motor
from backtest_v5_ev import PRELOAD_START, TEST_START, TEST_END, cal_prob, process_features
from backtest_v11_3pair import build_pair_dist, composite
from collections import defaultdict
from datetime import date,timedelta
import csv,itertools,math

TRAIN_START=date(2026,6,1); TRAIN_END=date(2026,7,15)
SEL_START=date(2026,7,16); SEL_END=date(2026,8,2)
BUDGET=5000; MIN_COMPOSITE=5.0


def pair_key(combo):
    a=(combo or '').split('-')
    return (int(a[1]),int(a[2])) if len(a)==3 and all(x.isdigit() for x in a) else None


def components(x,s3):
    a,b,c=x[1],x[2],x[3]
    st=.55*norm_st_edge(b['waku_st'],c['waku_st'])+.45*norm_st_edge(b['nst'],c['nst'])
    attack=clamp(.55*c['past_win']/.25+.45*(6-c['waku_sr'])/5)
    inside=clamp((7.5-a['waku_wr'])/6)
    return {
        'score':s3,
        'st':st,
        'motor':motor_attack(c),
        'inside':inside,
        'attack':attack,
        'stretch':c['stretch'],
        'pexpo':c['pexpo'],
    }


def passes(comp,rule):
    return (comp['score']>=rule['score'] and comp['st']>=rule['st'] and
            comp['motor']>=rule['motor'] and comp['inside']>=rule['inside'] and
            comp['attack']>=rule['attack'] and comp['stretch']>=rule['stretch'])


def choose_rule(samples):
    # Target roughly 30-40 races/month: selection window is 18 days, test is 31 days.
    # Keep rule families with 16-26 candidates in selection (~28-45/month projected).
    base=sum(y for _,y in samples)/len(samples) if samples else 0
    grids={
      'score':[66,67,68,69,70],
      'st':[0.40,0.50,0.60],
      'motor':[0.40,0.50,0.60],
      'inside':[0.30,0.45,0.60],
      'attack':[0.40,0.50,0.60],
      'stretch':[0.35,0.45,0.55],
    }
    cand=[]
    keys=list(grids)
    for vals in itertools.product(*(grids[k] for k in keys)):
        r=dict(zip(keys,vals)); sub=[y for c,y in samples if passes(c,r)]; n=len(sub)
        if not (16<=n<=26): continue
        h=sum(sub); raw=h/n
        shr=(h+12*base)/(n+12)
        projected=n*31/18
        size_pen=abs(projected-35)/35
        objective=shr-0.04*size_pen
        cand.append((objective,shr,raw,n,h,r,projected))
    if not cand:
        # fallback to score-only around 68
        r={'score':68,'st':0,'motor':0,'inside':0,'attack':0,'stretch':0}
        sub=[y for c,y in samples if passes(c,r)]
        return r,len(sub),sum(sub),(sum(sub)/len(sub) if sub else 0),len(sub)*31/18,[]
    cand.sort(key=lambda z:(z[0],z[1],z[4],-abs(z[6]-35)),reverse=True)
    best=cand[0]
    top=[{'shr':z[1],'raw':z[2],'n':z[3],'hit':z[4],'rule':z[5],'proj':z[6]} for z in cand[:10]]
    return best[5],best[3],best[4],best[2],best[6],top


def make_bets(s3,p3,od,pair_counts):
    from backtest_v5_ev import market_conditional
    mr=market_conditional(od,3)
    dist=build_pair_dist(pair_counts,mr)
    cand=[]
    for combo,o,q,share,cnt in dist:
        pc=p3*q; ev=pc*o
        cand.append({'combo':combo,'odds':o,'pair_prob':q,'combo_prob':pc,'ev':ev,'train_pair_count':cnt})
    # keep v11 probability-first construction; selection model is the thing being tested here
    cand.sort(key=lambda z:(z['combo_prob'],z['ev']),reverse=True)
    chosen=[]
    for z in cand:
        if composite(chosen+[z])>=MIN_COMPOSITE:
            chosen.append(z)
    return chosen


def allocate(chosen):
    if not chosen:return
    n=len(chosen)
    for z in chosen:z['stake']=100
    remain=BUDGET-100*n
    if remain<=0:return
    units=remain//100; sw=sum(z['combo_prob'] for z in chosen)
    raw=[units*z['combo_prob']/sw for z in chosen]; add=[int(v) for v in raw]
    left=units-sum(add); order=sorted(range(n),key=lambda k:raw[k]-add[k],reverse=True)
    for k in order[:left]:add[k]+=1
    for z,a in zip(chosen,add):z['stake']+=100*a


def main():
    cache={};hist=defaultdict(list);seen=set();d=PRELOAD_START
    while d<TRAIN_START:
        ingest_motor(hist,seen,d)
        if d>=TRAIN_START-timedelta(days=12): ingest_prior_day_preview(cache,d)
        d+=timedelta(days=1)

    train3=[];pair_counts=defaultdict(int)
    d=TRAIN_START
    while d<=TRAIN_END:
        feats=process_features(d,cache,hist);ymd=d.strftime('%Y/%m/%d')
        res={r['レースコード']:r for r in rows(f'data/results/realtime/{ymd}.csv')}
        pay={r['レースコード']:r for r in rows(f'data/results/payouts/{ymd}.csv')}
        for r,x,s4,s5,dc in feats:
            s3=score3v4(x);rr=res.get(r['レースコード'],{});win=i(rr.get('1着_艇番'));kim=(rr.get('決まり手') or '').replace('　','').replace(' ','')
            y=int(win==3 and kim in ('まくり','まくり差し'));train3.append((s3,y))
            if y:
                k=pair_key((pay.get(r['レースコード'],{}).get('3連単_組番') or '').strip())
                if k:pair_counts[k]+=1
        ingest_prior_day_preview(cache,d);ingest_motor(hist,seen,d);d+=timedelta(days=1)

    # rule selection period: select only the race-screening rule, not test-period outcomes
    samples=[];d=SEL_START
    while d<=SEL_END:
        feats=process_features(d,cache,hist);ymd=d.strftime('%Y/%m/%d')
        res={r['レースコード']:r for r in rows(f'data/results/realtime/{ymd}.csv')}
        for r,x,s4,s5,dc in feats:
            s3=score3v4(x);rr=res.get(r['レースコード'],{});win=i(rr.get('1着_艇番'));kim=(rr.get('決まり手') or '').replace('　','').replace(' ','')
            samples.append((components(x,s3),int(win==3 and kim in ('まくり','まくり差し'))))
        ingest_prior_day_preview(cache,d);ingest_motor(hist,seen,d);d+=timedelta(days=1)

    rule,seln,selh,selrate,proj,top=choose_rule(samples)

    bets=[];races=[];d=TEST_START
    while d<=TEST_END:
        feats=process_features(d,cache,hist);ymd=d.strftime('%Y/%m/%d')
        ods={r['レースコード']:r for r in rows(f'data/previews/od3/{ymd}.csv')}
        frozen=[]
        for r,x,s4,s5,dc in feats:
            s3=score3v4(x);comp=components(x,s3)
            if not passes(comp,rule):continue
            p3=cal_prob(train3,s3);chosen=make_bets(s3,p3,ods.get(r['レースコード'],{}),pair_counts)
            if not chosen:continue
            allocate(chosen);co=composite(chosen);n=len(chosen)
            race={'date':str(d),'race_code':r['レースコード'],'venue':r.get('レース場コード',''),'race':r.get('レース回',''),'day_cat':dc,'score3':round(s3,2),'p3':round(p3,4),'st_edge':round(comp['st'],3),'motor_attack':round(comp['motor'],3),'inside_weak':round(comp['inside'],3),'attack3':round(comp['attack'],3),'stretch':round(comp['stretch'],3),'tickets':n,'composite_odds':round(co,2)}
            races.append(race)
            for z in chosen:
                z.update({'date':str(d),'race_code':r['レースコード'],'venue':r.get('レース場コード',''),'race':r.get('レース回',''),'score3':round(s3,2),'composite_odds':round(co,2),'tickets':n});frozen.append(z)
        pay={r['レースコード']:r for r in rows(f'data/results/payouts/{ymd}.csv')}
        for b in frozen:
            pr=pay.get(b['race_code'],{});actual=(pr.get('3連単_組番') or '').strip();hit=actual==b['combo']
            b['actual_combo']=actual;b['hit']=int(hit);b['payout100']=i(pr.get('3連単_払戻金')) if hit else 0;b['return']=b['payout100']*(b['stake']//100) if hit else 0;bets.append(b)
        ingest_prior_day_preview(cache,d);ingest_motor(hist,seen,d);d+=timedelta(days=1)

    # head-event results are read only now for selected frozen test races
    byday=defaultdict(dict)
    for r in races:byday[r['date']][r['race_code']]=r
    for ds,mp in byday.items():
        ymd=ds.replace('-','/');res={z['レースコード']:z for z in rows(f'data/results/realtime/{ymd}.csv')}
        for code,r in mp.items():
            rr=res.get(code,{});win=i(rr.get('1着_艇番'));kim=(rr.get('決まり手') or '').replace('　','').replace(' ','')
            r['head_hit']=int(win==3 and kim in ('まくり','まくり差し'))
    for r in races:
        bs=[b for b in bets if b['race_code']==r['race_code']];r['bet_hit']=int(any(b['hit'] for b in bs));r['return']=sum(b['return'] for b in bs)

    if bets:
        with open('bets_v13.csv','w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=list(bets[0].keys()));w.writeheader();w.writerows(bets)
    if races:
        with open('races_v13.csv','w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=list(races[0].keys()));w.writeheader();w.writerows(races)

    st=sum(b['stake'] for b in bets);ret=sum(b['return'] for b in bets);hh=sum(r['head_hit'] for r in races);bh=sum(r['bet_hit'] for r in races)
    L=['# v13 3号艇 選別モデル（月30〜40R狙い）','',f'学習 {TRAIN_START}〜{TRAIN_END}、選別ルール決定 {SEL_START}〜{SEL_END}、完全テスト {TEST_START}〜{TEST_END}。','テスト結果は選別条件の決定に不使用。3頭まくり/まくり差し成立レースを先に絞り、3連単相手はv11型。1R最大5,000円、合成5倍以上。','',
       '## 事前固定した選別条件']
    for k,v in rule.items():L.append(f'- {k} >= {v}')
    L += [f'- 選別期間候補: {seln}R / 3頭成立 {selh}R ({selrate*100:.1f}%) / 月換算 {proj:.1f}R','',
       '## 1か月完全テスト','|項目|結果|','|---|---:|',f'|購入レース|{len(races)}|',f'|3頭まくり/MS成立|{hh}|',f'|頭成立率|{(hh/len(races)*100 if races else 0):.1f}%|',f'|3連単的中レース|{bh}|',f'|3連単的中率|{(bh/len(races)*100 if races else 0):.1f}%|',f'|投資|{st:,}円|',f'|払戻|{ret:,}円|',f'|回収率|{(ret/st*100 if st else 0):.1f}%|',f'|平均点数|{(len(bets)/len(races) if races else 0):.1f}|',f'|平均合成オッズ|{(sum(r["composite_odds"] for r in races)/len(races) if races else 0):.2f}倍|','',
       '## 選別期間の上位候補ルール','|n|hit|raw率|月換算|score|ST|motor|1弱|attack|stretch|','|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for z in top:
        q=z['rule'];L.append(f"|{z['n']}|{z['hit']}|{z['raw']*100:.1f}%|{z['proj']:.1f}|{q['score']}|{q['st']}|{q['motor']}|{q['inside']}|{q['attack']}|{q['stretch']}|")
    L += ['','## テスト的中レース','|日付|場|R|score3|結果|払戻/100円|','|---|---:|---:|---:|---|---:|']
    for r in races:
        if not r['bet_hit']:continue
        b=[b for b in bets if b['race_code']==r['race_code'] and b['hit']][0]
        L.append(f"|{r['date']}|{r['venue']}|{r['race']}|{r['score3']:.2f}|{b['actual_combo']}|{b['payout100']:,}円|")
    open('summary_v13.md','w',encoding='utf-8').write('\n'.join(L)+'\n')

if __name__=='__main__':main()
