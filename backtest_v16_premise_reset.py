from backtest import *
from backtest_v4 import ingest_prior_day_preview, score3v4, motor_attack
from backtest_v3 import ingest_motor
from backtest_v5_ev import PRELOAD_START, TEST_START, TEST_END, cal_prob, process_features, market_conditional
from backtest_v11_3pair import build_pair_dist, composite
from collections import defaultdict
from datetime import date,timedelta
import csv,itertools

TRAIN_START=date(2026,6,1); TRAIN_END=date(2026,7,15)
SEL_START=date(2026,7,16); SEL_END=date(2026,8,2)
BUDGET=5000


def head_market_share(od, head=3):
    total=0.0; h=0.0
    for a in range(1,7):
        for b in range(1,7):
            if b==a: continue
            for c in range(1,7):
                if c in (a,b): continue
                o=f(od.get(f'3連単_{a}-{b}-{c}'),0)
                if o>0:
                    v=1/o; total+=v
                    if a==head: h+=v
    return h/total if total>0 else 0.0


def comps(x,s3,dc,p3,od):
    a,b,c=x[1],x[2],x[3]
    st=.55*norm_st_edge(b['waku_st'],c['waku_st'])+.45*norm_st_edge(b['nst'],c['nst'])
    wall=.55*clamp((5.5-b['waku_wr'])/4.5)+.45*norm_st_edge(b['waku_st'],c['waku_st'])
    inside=clamp((7.5-a['waku_wr'])/6)
    mh=head_market_share(od,3)
    value=p3/mh if mh>0 else 0
    return {'score':s3,'st':st,'wallweak':wall,'insideweak':inside,'motor':motor_attack(c),'stretch':c['stretch'],'day3':1 if dc=='3日目以降' else 0,'value':value}


def passes(z,r):
    return z['score']>=r['score'] and z['st']>=r['st'] and z['wallweak']>=r['wallweak'] and z['insideweak']>=r['insideweak'] and z['motor']>=r['motor'] and z['stretch']>=r['stretch'] and z['day3']>=r['day3'] and z['value']>=r['value']


def make_bets(p3,od,pair_counts):
    mr=market_conditional(od,3); dist=build_pair_dist(pair_counts,mr)
    cand=[]
    for combo,o,q,share,cnt in dist:
        cand.append({'combo':combo,'odds':o,'combo_prob':p3*q})
    cand.sort(key=lambda z:z['combo_prob'],reverse=True)
    chosen=[]
    for z in cand:
        if composite(chosen+[z])>=5.0: chosen.append(z)
    return chosen


def allocate(chosen,budget=BUDGET):
    if not chosen:return
    n=len(chosen)
    for z in chosen:z['stake']=100
    rem=budget-100*n
    if rem<=0:return
    units=rem//100; sw=sum(z['combo_prob'] for z in chosen)
    raw=[units*z['combo_prob']/sw for z in chosen]; add=[int(v) for v in raw]
    left=units-sum(add); order=sorted(range(n),key=lambda k:raw[k]-add[k],reverse=True)
    for k in order[:left]:add[k]+=1
    for z,a in zip(chosen,add):z['stake']+=100*a


def build_state_to(day):
    cache={};hist=defaultdict(list);seen=set();d=PRELOAD_START
    while d<day:
        ingest_motor(hist,seen,d)
        if d>=day-timedelta(days=12): ingest_prior_day_preview(cache,d)
        d+=timedelta(days=1)
    return cache,hist,seen


def main():
    cache={};hist=defaultdict(list);seen=set();d=PRELOAD_START
    while d<TRAIN_START:
        ingest_motor(hist,seen,d)
        if d>=TRAIN_START-timedelta(days=12):ingest_prior_day_preview(cache,d)
        d+=timedelta(days=1)

    train3=[]; pair_counts=defaultdict(int)
    d=TRAIN_START
    while d<=TRAIN_END:
        feats=process_features(d,cache,hist); ymd=d.strftime('%Y/%m/%d')
        res={r['レースコード']:r for r in rows(f'data/results/realtime/{ymd}.csv')}; pay={r['レースコード']:r for r in rows(f'data/results/payouts/{ymd}.csv')}
        for r,x,s4,s5,dc in feats:
            s3=score3v4(x); rr=res.get(r['レースコード'],{}); win=i(rr.get('1着_艇番')); kim=(rr.get('決まり手') or '').replace('　','').replace(' ','')
            y=int(win==3 and kim in ('まくり','まくり差し')); train3.append((s3,y))
            if y:
                combo=(pay.get(r['レースコード'],{}).get('3連単_組番') or '').strip().split('-')
                if len(combo)==3: pair_counts[(int(combo[1]),int(combo[2]))]+=1
        ingest_prior_day_preview(cache,d);ingest_motor(hist,seen,d);d+=timedelta(days=1)

    # calibration records, rules selected before test
    cal=[];d=SEL_START
    while d<=SEL_END:
        feats=process_features(d,cache,hist);ymd=d.strftime('%Y/%m/%d')
        ods={r['レースコード']:r for r in rows(f'data/previews/od3/{ymd}.csv')};res={r['レースコード']:r for r in rows(f'data/results/realtime/{ymd}.csv')};pay={r['レースコード']:r for r in rows(f'data/results/payouts/{ymd}.csv')}
        for r,x,s4,s5,dc in feats:
            s3=score3v4(x);p3=cal_prob(train3,s3);od=ods.get(r['レースコード'],{});z=comps(x,s3,dc,p3,od)
            chosen=make_bets(p3,od,pair_counts);actual=(pay.get(r['レースコード'],{}).get('3連単_組番') or '').strip();payout=i(pay.get(r['レースコード'],{}).get('3連単_払戻金'))
            rr=res.get(r['レースコード'],{});win=i(rr.get('1着_艇番'));kim=(rr.get('決まり手') or '').replace('　','').replace(' ','');head=int(win==3 and kim in ('まくり','まくり差し'))
            cal.append((z,chosen,actual,payout,head))
        ingest_prior_day_preview(cache,d);ingest_motor(hist,seen,d);d+=timedelta(days=1)

    grids={'score':[66,68,70],'st':[.45,.55,.65],'wallweak':[.35,.50,.65],'insideweak':[.35,.50,.65],'motor':[.40,.50,.60],'stretch':[.40,.50,.60],'day3':[0,1],'value':[.9,1.0,1.1,1.2]}
    keys=list(grids); candidates=[]
    for vals in itertools.product(*(grids[k] for k in keys)):
        rule=dict(zip(keys,vals)); sub=[q for q in cal if passes(q[0],rule)];n=len(sub);proj=n*31/18
        if n<6 or not (10<=proj<=25):continue
        head=sum(q[4] for q in sub); hit=0; ret=0
        for z,ch,actual,payout,h in sub:
            if any(b['combo']==actual for b in ch):hit+=1;ret+=payout
        stake=5000*n;roi=ret/stake*100 if stake else 0
        # conservative objective: shrink ROI toward 100 and reward head signal; avoids pure payout chasing
        shr_roi=(ret+50000)/(stake+50000)*100
        headrate=head/n
        objective=.65*shr_roi+.35*(100*headrate)
        candidates.append((objective,shr_roi,roi,n,head,hit,rule,proj))
    candidates.sort(key=lambda q:(q[0],q[1],q[4]),reverse=True)
    if candidates: best=candidates[0]
    else: best=(0,0,0,0,0,0,{'score':68,'st':0,'wallweak':0,'insideweak':0,'motor':0,'stretch':0,'day3':0,'value':0},0)
    rule=best[6]

    bets=[];races=[];d=TEST_START
    while d<=TEST_END:
        feats=process_features(d,cache,hist);ymd=d.strftime('%Y/%m/%d');ods={r['レースコード']:r for r in rows(f'data/previews/od3/{ymd}.csv')};frozen=[]
        for r,x,s4,s5,dc in feats:
            s3=score3v4(x);p3=cal_prob(train3,s3);od=ods.get(r['レースコード'],{});z=comps(x,s3,dc,p3,od)
            if not passes(z,rule):continue
            chosen=make_bets(p3,od,pair_counts)
            if not chosen:continue
            allocate(chosen);co=composite(chosen)
            race={'date':str(d),'race_code':r['レースコード'],'venue':r.get('レース場コード',''),'race':r.get('レース回',''),'day_cat':dc,'score3':round(s3,2),'p3':round(p3,4),'head_value':round(z['value'],2),'st':round(z['st'],3),'wallweak':round(z['wallweak'],3),'insideweak':round(z['insideweak'],3),'motor':round(z['motor'],3),'stretch':round(z['stretch'],3),'tickets':len(chosen),'composite':round(co,2)};races.append(race)
            for b in chosen:b.update({'date':str(d),'race_code':r['レースコード'],'venue':r.get('レース場コード',''),'race':r.get('レース回','')});frozen.append(b)
        pay={r['レースコード']:r for r in rows(f'data/results/payouts/{ymd}.csv')}
        for b in frozen:
            pr=pay.get(b['race_code'],{});actual=(pr.get('3連単_組番') or '').strip();hit=actual==b['combo'];b['actual']=actual;b['hit']=int(hit);b['payout100']=i(pr.get('3連単_払戻金')) if hit else 0;b['return']=b['payout100']*(b['stake']//100) if hit else 0;bets.append(b)
        ingest_prior_day_preview(cache,d);ingest_motor(hist,seen,d);d+=timedelta(days=1)

    for r in races:
        bs=[b for b in bets if b['race_code']==r['race_code']];r['bet_hit']=int(any(b['hit'] for b in bs));r['return']=sum(b['return'] for b in bs)
    # head check after freeze
    for ds in sorted(set(r['date'] for r in races)):
        ymd=ds.replace('-','/');res={z['レースコード']:z for z in rows(f'data/results/realtime/{ymd}.csv')}
        for r in [x for x in races if x['date']==ds]:
            rr=res.get(r['race_code'],{});win=i(rr.get('1着_艇番'));kim=(rr.get('決まり手') or '').replace('　','').replace(' ','');r['head_hit']=int(win==3 and kim in ('まくり','まくり差し'))

    if bets:
        with open('bets_v16.csv','w',newline='',encoding='utf-8-sig') as f0:w=csv.DictWriter(f0,fieldnames=list(bets[0].keys()));w.writeheader();w.writerows(bets)
    if races:
        with open('races_v16.csv','w',newline='',encoding='utf-8-sig') as f0:w=csv.DictWriter(f0,fieldnames=list(races[0].keys()));w.writeheader();w.writerows(races)
    st=sum(b['stake'] for b in bets);ret=sum(b['return'] for b in bets);hh=sum(r.get('head_hit',0) for r in races);bh=sum(r['bet_hit'] for r in races)
    L=['# v16 前提条件見直し 1か月完全テスト','',f'学習 {TRAIN_START}〜{TRAIN_END}、条件決定 {SEL_START}〜{SEL_END}、完全テスト {TEST_START}〜{TEST_END}。','狙いは「3が強い」ではなく、1・2崩れ＋3のST/伸び/モーター＋3頭市場過小評価。テスト結果は条件決定に不使用。','', '## 事前固定条件']
    for k,v in rule.items():L.append(f'- {k} >= {v}')
    L += [f'- 条件決定期間: {best[3]}R / 3頭成立{best[4]}R / 3連単的中{best[5]}R / ROI {best[2]:.1f}% / 月換算{best[7]:.1f}R','', '## 1か月テスト','|項目|結果|','|---|---:|',f'|購入レース|{len(races)}|',f'|3頭成立|{hh}|',f'|頭成立率|{(hh/len(races)*100 if races else 0):.1f}%|',f'|3連単的中|{bh}|',f'|3連単的中率|{(bh/len(races)*100 if races else 0):.1f}%|',f'|投資|{st:,}円|',f'|払戻|{ret:,}円|',f'|利益|{ret-st:+,}円|',f'|回収率|{(ret/st*100 if st else 0):.1f}%|',f'|平均点数|{(len(bets)/len(races) if races else 0):.1f}|','', '## 条件決定期間 上位5ルール','|順位|月換算R|cal ROI|cal頭率|score|ST|2壁弱|1弱|motor|stretch|day3|value|','|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for j,q in enumerate(candidates[:5],1):
        r=q[6];L.append(f"|{j}|{q[7]:.1f}|{q[2]:.1f}%|{(q[4]/q[3]*100 if q[3] else 0):.1f}%|{r['score']}|{r['st']}|{r['wallweak']}|{r['insideweak']}|{r['motor']}|{r['stretch']}|{r['day3']}|{r['value']}|")
    open('summary_v16.md','w',encoding='utf-8').write('\n'.join(L)+'\n')

if __name__=='__main__':main()
