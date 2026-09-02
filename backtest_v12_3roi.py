from backtest import *
from backtest_v4 import ingest_prior_day_preview, score3v4
from backtest_v3 import ingest_motor
from backtest_v5_ev import PRELOAD_START, TEST_START, TEST_END, cal_prob, market_conditional, process_features
from backtest_v11_3pair import build_pair_dist
from collections import defaultdict
from datetime import date,timedelta

TRAIN_START=date(2026,6,1); TRAIN_END=date(2026,7,15)
CAL_START=date(2026,7,16); CAL_END=date(2026,8,2)
BUDGET=5000

GRID_S=[60.0,62.5,65.0,67.5,70.0]
GRID_EV=[0.9,1.0,1.1,1.2,1.4,1.6]
GRID_CO=[5.0,7.0,10.0,15.0]
GRID_MAX=[3,5,8,10,15,20]

def composite(items):
    s=sum(1/z['odds'] for z in items if z['odds']>0)
    return 1/s if s>0 else 999.0

def make_candidates(s3,p3,od,pair_counts):
    mr=market_conditional(od,3)
    dist=build_pair_dist(pair_counts,mr)
    out=[]
    for combo,o,q,share,cnt in dist:
        pc=p3*q; ev=pc*o
        out.append({'combo':combo,'odds':o,'pair_prob':q,'combo_prob':pc,'market_share':share,'train_pair_count':cnt,'ev':ev})
    return out

def choose(cand,s3,smin,evmin,minco,maxn):
    if s3<smin: return []
    xs=[dict(z) for z in cand if z['ev']>=evmin]
    xs.sort(key=lambda z:(z['ev'],z['combo_prob']),reverse=True)
    chosen=[]
    for z in xs:
        if len(chosen)>=maxn: break
        tr=chosen+[z]
        if composite(tr)>=minco: chosen=tr
    return chosen

def allocate(chosen):
    if not chosen: return
    n=len(chosen)
    for z in chosen: z['stake']=100
    remain=BUDGET-100*n
    if remain<=0:return
    # ROI first: positive EV excess gets most of the stake; small floor prevents one-ticket concentration.
    ws=[max(.03,z['ev']-1.0) for z in chosen]
    sw=sum(ws); units=remain//100
    raw=[units*w/sw for w in ws]; add=[int(x) for x in raw]
    left=units-sum(add); order=sorted(range(n),key=lambda k:raw[k]-add[k],reverse=True)
    for k in order[:left]: add[k]+=1
    for z,a in zip(chosen,add): z['stake']+=100*a

def init_state():
    cache={}; hist=defaultdict(list); seen=set(); d=PRELOAD_START
    while d<TRAIN_START:
        ingest_motor(hist,seen,d)
        if d>=TRAIN_START-timedelta(days=12): ingest_prior_day_preview(cache,d)
        d+=timedelta(days=1)
    return cache,hist,seen

def train(cache,hist,seen):
    train3=[]; pair_counts=defaultdict(int); d=TRAIN_START
    while d<=TRAIN_END:
        feats=process_features(d,cache,hist); ymd=d.strftime('%Y/%m/%d')
        res={r['レースコード']:r for r in rows(f'data/results/realtime/{ymd}.csv')}
        pay={r['レースコード']:r for r in rows(f'data/results/payouts/{ymd}.csv')}
        for r,x,s4,s5,dc in feats:
            s3=score3v4(x); rr=res.get(r['レースコード'],{}); win=i(rr.get('1着_艇番')); kim=(rr.get('決まり手') or '').replace('　','').replace(' ','')
            y=1 if win==3 and kim in ('まくり','まくり差し') else 0
            train3.append((s3,y))
            if y:
                actual=(pay.get(r['レースコード'],{}).get('3連単_組番') or '').strip().split('-')
                if len(actual)==3: pair_counts[(i(actual[1]),i(actual[2]))]+=1
        ingest_prior_day_preview(cache,d); ingest_motor(hist,seen,d); d+=timedelta(days=1)
    return train3,pair_counts

def collect_period(start,end,cache,hist,seen,train3,pair_counts,with_results):
    out=[]; d=start
    while d<=end:
        feats=process_features(d,cache,hist); ymd=d.strftime('%Y/%m/%d')
        ods={r['レースコード']:r for r in rows(f'data/previews/od3/{ymd}.csv')}
        pay={r['レースコード']:r for r in rows(f'data/results/payouts/{ymd}.csv')} if with_results else {}
        for r,x,s4,s5,dc in feats:
            s3=score3v4(x); p3=cal_prob(train3,s3); cand=make_candidates(s3,p3,ods.get(r['レースコード'],{}),pair_counts)
            actual=''; payout=0
            if with_results:
                pr=pay.get(r['レースコード'],{}); actual=(pr.get('3連単_組番') or '').strip(); payout=i(pr.get('3連単_払戻金'))
            out.append({'date':str(d),'race_code':r['レースコード'],'venue':r.get('レース場コード',''),'race':r.get('レース回',''),'day_cat':dc,'s3':s3,'p3':p3,'cand':cand,'actual':actual,'payout100':payout})
        ingest_prior_day_preview(cache,d); ingest_motor(hist,seen,d); d+=timedelta(days=1)
    return out

def eval_rule(data,rule):
    smin,evmin,minco,maxn=rule
    races=hits=stake=ret=tickets=0
    for q in data:
        ch=choose(q['cand'],q['s3'],smin,evmin,minco,maxn)
        if not ch: continue
        allocate(ch); races+=1; tickets+=len(ch); stake+=sum(z['stake'] for z in ch)
        for z in ch:
            if z['combo']==q['actual']:
                hits+=1; ret+=q['payout100']*(z['stake']//100); break
    roi=ret/stake*100 if stake else 0
    return {'rule':rule,'races':races,'hits':hits,'stake':stake,'ret':ret,'roi':roi,'tickets':tickets}

def main():
    cache,hist,seen=init_state(); train3,pair_counts=train(cache,hist,seen)
    cal=collect_period(CAL_START,CAL_END,cache,hist,seen,train3,pair_counts,True)
    results=[]
    for s in GRID_S:
      for ev in GRID_EV:
       for co in GRID_CO:
        for mx in GRID_MAX:
         z=eval_rule(cal,(s,ev,co,mx))
         if z['races']>=8 and z['hits']>=1: results.append(z)
    # Pre-test selection only. Penalize tiny samples by shrinking ROI toward 100 with 8 virtual races.
    for z in results:
        z['select_score']=(z['roi']*z['races'] + 100*8)/(z['races']+8)
    results.sort(key=lambda z:(z['select_score'],z['roi'],z['races']),reverse=True)
    best=results[0] if results else {'rule':(65.0,1.0,5.0,10),'races':0,'hits':0,'stake':0,'ret':0,'roi':0,'select_score':0}

    test=collect_period(TEST_START,TEST_END,cache,hist,seen,train3,pair_counts,True)
    smin,evmin,minco,maxn=best['rule']
    bets=[]; races=[]
    for q in test:
        ch=choose(q['cand'],q['s3'],smin,evmin,minco,maxn)
        if not ch: continue
        allocate(ch); co=composite(ch); hit=0; rr=0
        for z in ch:
            h=int(z['combo']==q['actual']); r=q['payout100']*(z['stake']//100) if h else 0
            if h: hit=1; rr+=r
            b=dict(z); b.update({'date':q['date'],'race_code':q['race_code'],'venue':q['venue'],'race':q['race'],'day_cat':q['day_cat'],'score3':round(q['s3'],2),'p3':round(q['p3'],4),'actual_combo':q['actual'],'hit':h,'payout100':q['payout100'] if h else 0,'return':r,'composite_odds':round(co,2),'tickets':len(ch)})
            bets.append(b)
        races.append({'date':q['date'],'race_code':q['race_code'],'venue':q['venue'],'race':q['race'],'day_cat':q['day_cat'],'score3':round(q['s3'],2),'p3':round(q['p3'],4),'tickets':len(ch),'composite_odds':round(co,2),'hit':hit,'return':rr})

    if bets:
      with open('bets_v12_3roi.csv','w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=list(bets[0].keys()));w.writeheader();w.writerows(bets)
    if races:
      with open('races_v12_3roi.csv','w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=list(races[0].keys()));w.writeheader();w.writerows(races)

    st=sum(b['stake'] for b in bets); ret=sum(b['return'] for b in bets); hits=sum(r['hit'] for r in races); roi=ret/st*100 if st else 0
    top=results[:10]
    L=['# v12 3号艇 ROI最優先','',f'学習 {TRAIN_START}〜{TRAIN_END}、ルール選択 {CAL_START}〜{CAL_END}、完全テスト {TEST_START}〜{TEST_END}。','テスト期間の結果はルール選択に不使用。1R最大5,000円。','',
       '## 事前選択されたルール',f'- score3 >= {smin}',f'- 個別EV >= {evmin}',f'- 合成オッズ >= {minco}倍',f'- 最大 {maxn}点',f'- 校正期間: {best["races"]}R / {best["hits"]}的中 / ROI {best["roi"]:.1f}%','',
       '## 1か月テスト結果','|項目|値|','|---|---:|',f'|購入レース|{len(races)}|',f'|的中レース|{hits}|',f'|的中率|{(hits/len(races)*100 if races else 0):.1f}%|',f'|投資|{st:,}円|',f'|払戻|{ret:,}円|',f'|回収率|{roi:.1f}%|',f'|平均点数|{(len(bets)/len(races) if races else 0):.1f}|',f'|平均合成オッズ|{(sum(r["composite_odds"] for r in races)/len(races) if races else 0):.2f}倍|','',
       '## 校正期間 上位ルール','|score|EV下限|合成下限|最大点|R|的中|ROI|','|---:|---:|---:|---:|---:|---:|---:|']
    for z in top:
        a,b,c,d=z['rule']; L.append(f'|{a}|{b}|{c}|{d}|{z["races"]}|{z["hits"]}|{z["roi"]:.1f}%|')
    L+=['','## テスト的中レース','|日付|場|R|score3|結果|払戻/100円|点数|合成|','|---|---:|---:|---:|---|---:|---:|---:|']
    for r in races:
        if not r['hit']: continue
        bb=[b for b in bets if b['race_code']==r['race_code'] and b['hit']][0]
        L.append(f'|{r["date"]}|{r["venue"]}|{r["race"]}|{r["score3"]:.2f}|{bb["actual_combo"]}|{bb["payout100"]:,}円|{r["tickets"]}|{r["composite_odds"]:.2f}倍|')
    open('summary_v12_3roi.md','w',encoding='utf-8').write('\n'.join(L)+'\n')

if __name__=='__main__': main()
