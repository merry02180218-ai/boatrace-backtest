from backtest import *
from backtest_v4 import ingest_prior_day_preview, score3v4
from backtest_v3 import ingest_motor
from backtest_v5_ev import PRELOAD_START, TEST_START, TEST_END, cal_prob, process_features
from backtest_v11_3pair import build_pair_dist, composite, pair_key
from analyze_3attack_feature_correlations import feature_row
from collections import defaultdict
from datetime import date,timedelta
import csv,itertools

TRAIN_START=date(2026,6,1); TRAIN_END=date(2026,7,15)
CAL_START=date(2026,7,16); CAL_END=date(2026,8,2)
BUDGET=5000; MIN_COMPOSITE=5.0

# Core hypothesis only: 3-racer strength + ST edge over 2 + weak 2-wall.
GRIDS={
    '3選手力':[0.40,0.45,0.50,0.55,0.60],
    '3_ST優位':[0.35,0.45,0.55,0.65,0.75],
    '2壁弱さ':[0.35,0.45,0.55,0.65,0.75],
}

def passes(z,r):
    return all(z[k]>=r[k] for k in r)

def target(rr):
    win=i(rr.get('1着_艇番')); kim=(rr.get('決まり手') or '').replace('　','').replace(' ','')
    return int(win==3 and kim in ('まくり','まくり差し'))

def choose_rule(train_rows,cal_rows):
    train_base=sum(z['y'] for z in train_rows)/len(train_rows)
    cand=[]
    keys=list(GRIDS)
    for vals in itertools.product(*(GRIDS[k] for k in keys)):
        r=dict(zip(keys,vals)); sub=[z for z in cal_rows if passes(z,r)]; n=len(sub)
        projected=n*31/18
        if not (10<=projected<=30) or n<6: continue
        h=sum(z['y'] for z in sub); raw=h/n
        # shrink toward pre-calibration TRAIN base; do not use test outcomes.
        shr=(h+10*train_base)/(n+10)
        # prefer useful hit-rate, then a practical center around 18/month.
        objective=shr-0.015*abs(projected-18)/18
        cand.append((objective,shr,raw,n,h,projected,r))
    if not cand:
        # predefined moderate fallback, still independent of TEST.
        r={'3選手力':0.50,'3_ST優位':0.55,'2壁弱さ':0.55}
        sub=[z for z in cal_rows if passes(z,r)]; n=len(sub); h=sum(z['y'] for z in sub)
        return r,n,h,(h/n if n else 0),n*31/18,[]
    cand.sort(key=lambda z:(z[0],z[1],z[4],-abs(z[5]-18)),reverse=True)
    b=cand[0]
    top=[{'shr':z[1],'raw':z[2],'n':z[3],'hit':z[4],'proj':z[5],'rule':z[6]} for z in cand[:10]]
    return b[6],b[3],b[4],b[2],b[5],top

def select_set(p3,od,pair_counts):
    from backtest_v5_ev import market_conditional
    mr=market_conditional(od,3); dist=build_pair_dist(pair_counts,mr)
    cand=[]
    for combo,o,q,share,cnt in dist:
        pc=p3*q
        cand.append({'combo':combo,'odds':o,'pair_prob':q,'combo_prob':pc,'market_share':share,'train_pair_count':cnt,'ev':pc*o})
    cand.sort(key=lambda z:(z['combo_prob'],z['ev']),reverse=True)
    chosen=[]
    for z in cand:
        if composite(chosen+[z])>=MIN_COMPOSITE: chosen.append(z)
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
        if d>=TRAIN_START-timedelta(days=12):ingest_prior_day_preview(cache,d)
        d+=timedelta(days=1)

    train3=[]; pair_counts=defaultdict(int); train_rows=[]
    d=TRAIN_START
    while d<=TRAIN_END:
        feats=process_features(d,cache,hist);ymd=d.strftime('%Y/%m/%d')
        res={r['レースコード']:r for r in rows(f'data/results/realtime/{ymd}.csv')}
        pay={r['レースコード']:r for r in rows(f'data/results/payouts/{ymd}.csv')}
        for r,x,s4,s5,dc in feats:
            s3=score3v4(x); y=target(res.get(r['レースコード'],{})); train3.append((s3,y))
            z=feature_row(x,s3,dc);z['y']=y;train_rows.append(z)
            if y:
                k=pair_key((pay.get(r['レースコード'],{}).get('3連単_組番') or '').strip())
                if k:pair_counts[k]+=1
        ingest_prior_day_preview(cache,d);ingest_motor(hist,seen,d);d+=timedelta(days=1)

    cal_rows=[];d=CAL_START
    while d<=CAL_END:
        feats=process_features(d,cache,hist);ymd=d.strftime('%Y/%m/%d')
        res={r['レースコード']:r for r in rows(f'data/results/realtime/{ymd}.csv')}
        for r,x,s4,s5,dc in feats:
            s3=score3v4(x);z=feature_row(x,s3,dc);z['y']=target(res.get(r['レースコード'],{}));cal_rows.append(z)
        ingest_prior_day_preview(cache,d);ingest_motor(hist,seen,d);d+=timedelta(days=1)

    rule,cn,ch,crate,proj,top=choose_rule(train_rows,cal_rows)

    bets=[];races=[];d=TEST_START
    while d<=TEST_END:
        feats=process_features(d,cache,hist);ymd=d.strftime('%Y/%m/%d')
        ods={r['レースコード']:r for r in rows(f'data/previews/od3/{ymd}.csv')}
        frozen=[]
        for r,x,s4,s5,dc in feats:
            s3=score3v4(x);fr=feature_row(x,s3,dc)
            if not passes(fr,rule):continue
            p3=cal_prob(train3,s3);chosen=select_set(p3,ods.get(r['レースコード'],{}),pair_counts)
            if not chosen:continue
            allocate(chosen);co=composite(chosen);n=len(chosen)
            rr={'date':str(d),'race_code':r['レースコード'],'venue':r.get('レース場コード',''),'race':r.get('レース回',''),'score3':round(s3,2),'strength3':round(fr['3選手力'],3),'st_edge':round(fr['3_ST優位'],3),'wallweak2':round(fr['2壁弱さ'],3),'p3':round(p3,4),'tickets':n,'composite_odds':round(co,2)}
            races.append(rr)
            for z in chosen:
                z.update({'date':str(d),'race_code':r['レースコード'],'venue':r.get('レース場コード',''),'race':r.get('レース回',''),'score3':round(s3,2),'tickets':n,'composite_odds':round(co,2)});frozen.append(z)
        # only after all choices are frozen for the date
        pay={r['レースコード']:r for r in rows(f'data/results/payouts/{ymd}.csv')}
        res={r['レースコード']:r for r in rows(f'data/results/realtime/{ymd}.csv')}
        for b in frozen:
            pr=pay.get(b['race_code'],{});actual=(pr.get('3連単_組番') or '').strip();hit=actual==b['combo']
            b['actual_combo']=actual;b['hit']=int(hit);b['payout100']=i(pr.get('3連単_払戻金')) if hit else 0;b['return']=b['payout100']*(b['stake']//100) if hit else 0;bets.append(b)
        for rr in [q for q in races if q['date']==str(d)]:
            rr['head_hit']=target(res.get(rr['race_code'],{}))
        ingest_prior_day_preview(cache,d);ingest_motor(hist,seen,d);d+=timedelta(days=1)

    for r in races:
        bs=[b for b in bets if b['race_code']==r['race_code']];r['bet_hit']=int(any(b['hit'] for b in bs));r['return']=sum(b['return'] for b in bs)
    if bets:
        with open('bets_v17.csv','w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=list(bets[0].keys()));w.writeheader();w.writerows(bets)
    if races:
        with open('races_v17.csv','w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=list(races[0].keys()));w.writeheader();w.writerows(races)

    st=sum(b['stake'] for b in bets);ret=sum(b['return'] for b in bets);hh=sum(r['head_hit'] for r in races);bh=sum(r['bet_hit'] for r in races)
    L=['# v17 3選手力×ST優位×2壁弱さ','',f'学習 {TRAIN_START}〜{TRAIN_END}、閾値決定 {CAL_START}〜{CAL_END}、完全テスト {TEST_START}〜{TEST_END}。','テスト結果は閾値決定に不使用。3連単相手はv11型、合成5倍以上、1R最大5,000円。','',
       '## 事前固定条件',f"- 3選手力 >= {rule['3選手力']}",f"- 3_ST優位 >= {rule['3_ST優位']}",f"- 2壁弱さ >= {rule['2壁弱さ']}",f'- 閾値決定期間: {cn}R / 3頭成立 {ch}R ({crate*100:.1f}%) / 月換算 {proj:.1f}R','',
       '## 1か月完全テスト','|項目|結果|','|---|---:|',f'|購入レース|{len(races)}|',f'|3頭まくり/MS成立|{hh}|',f'|頭成立率|{(hh/len(races)*100 if races else 0):.1f}%|',f'|3連単的中レース|{bh}|',f'|3連単的中率|{(bh/len(races)*100 if races else 0):.1f}%|',f'|投資|{st:,}円|',f'|払戻|{ret:,}円|',f'|利益|{ret-st:,}円|',f'|回収率|{(ret/st*100 if st else 0):.1f}%|',f'|平均点数|{(len(bets)/len(races) if races else 0):.1f}|','',
       '## 閾値決定期間 上位ルール','|n|頭的中|頭率|月換算|3選手力|ST優位|2壁弱|','|---:|---:|---:|---:|---:|---:|---:|']
    for z in top:
        q=z['rule'];L.append(f"|{z['n']}|{z['hit']}|{z['raw']*100:.1f}%|{z['proj']:.1f}|{q['3選手力']}|{q['3_ST優位']}|{q['2壁弱さ']}|")
    open('summary_v17.md','w',encoding='utf-8').write('\n'.join(L)+'\n')

if __name__=='__main__':main()
