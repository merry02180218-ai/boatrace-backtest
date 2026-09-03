from backtest import *
from backtest_v3 import ingest_motor
from backtest_v4 import ingest_prior_day_preview, score4v4, score45v4, resistance12, attack4_component
from backtest_v5_ev import PRELOAD_START, TEST_START, TEST_END, cal_prob, market_conditional, process_features
from backtest_v11_3pair import composite, pair_key
from collections import defaultdict
from datetime import date,timedelta
import csv

TRAIN_START=date(2026,6,1); TRAIN_END=date(2026,7,15)
CAL_START=date(2026,7,16); CAL_END=date(2026,8,2)
BUDGET=5000; MIN_COMPOSITE=5.0

# v17の中心条件を横展開。閾値値そのものはv17の事前固定値を流用し、TESTで調整しない。
RULE4={'4選手力':0.50,'4_ST優位':0.55,'3壁弱さ':0.55}
RULE5={'4攻撃力':0.55,'1_2抵抗力':0.55,'5取り切り力':0.50}

def c01(v): return max(0.0,min(1.0,v))

def strength(z): return .6*c01((z['wr']-3.5)/4)+.4*c01((z['local']-3)/5)

def st_edge(left,right): return .60*norm_st_edge(left['waku_st'],right['waku_st'])+.40*norm_st_edge(left['nst'],right['nst'])

def wallweak(left,right): return .60*c01((5.5-left['waku_wr'])/4.5)+.40*norm_st_edge(left['waku_st'],right['waku_st'])

def take5(x):
    e=x[5]
    return c01(.50*e['turnfoot']+.25*c01(e['past_win']/.22)+.25*(.55*pct_motor(e['motor2'])+.45*e['mhist']))

def features4(x):
    c,d=x[3],x[4]
    return {'4選手力':strength(d),'4_ST優位':st_edge(c,d),'3壁弱さ':wallweak(c,d)}

def features5(x,s4):
    return {'4攻撃力':attack4_component(x,s4),'1_2抵抗力':resistance12(x),'5取り切り力':take5(x)}

def passes(fr,rule): return all(fr[k]>=v for k,v in rule.items())

def target4(rr):
    win=i(rr.get('1着_艇番')); kim=(rr.get('決まり手') or '').replace('　','').replace(' ','')
    return int(win==4 and kim in ('まくり','まくり差し'))

def target5(rr): return int(i(rr.get('1着_艇番'))==5)

def pair_distribution(pair_counts,market_rows,alpha=8.0):
    total=sum(pair_counts.values()); out=[]
    for combo,o,share in market_rows:
        k=pair_key(combo); cnt=pair_counts.get(k,0)
        q=(cnt+alpha*share)/(total+alpha) if total+alpha>0 else share
        out.append((combo,o,q,share,cnt))
    s=sum(z[2] for z in out)
    return [(c,o,q/s if s else sh,sh,cnt) for c,o,q,sh,cnt in out]

def select_set(head,phead,od,pair_counts):
    mr=market_conditional(od,head); dist=pair_distribution(pair_counts,mr)
    cand=[]
    for combo,o,q,share,cnt in dist:
        pc=phead*q
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

def run_model(model,head,rule,targetfn):
    cache={};hist=defaultdict(list);seen=set();d=PRELOAD_START
    while d<TRAIN_START:
        ingest_motor(hist,seen,d)
        if d>=TRAIN_START-timedelta(days=12):ingest_prior_day_preview(cache,d)
        d+=timedelta(days=1)

    train_prob=[];pairs=defaultdict(int)
    d=TRAIN_START
    while d<=TRAIN_END:
        feats=process_features(d,cache,hist);ymd=d.strftime('%Y/%m/%d')
        res={r['レースコード']:r for r in rows(f'data/results/realtime/{ymd}.csv')}
        pay={r['レースコード']:r for r in rows(f'data/results/payouts/{ymd}.csv')}
        for r,x,s4,s5,dc in feats:
            score=s4 if head==4 else score45v4(x,s4); y=targetfn(res.get(r['レースコード'],{}));train_prob.append((score,y))
            if y:
                actual=(pay.get(r['レースコード'],{}).get('3連単_組番') or '').strip();k=pair_key(actual)
                if k:pairs[k]+=1
        ingest_prior_day_preview(cache,d);ingest_motor(hist,seen,d);d+=timedelta(days=1)

    # calibration: rule is fixed from v17 logic; only report its rate, no tuning.
    caln=calh=0;d=CAL_START
    while d<=CAL_END:
        feats=process_features(d,cache,hist);ymd=d.strftime('%Y/%m/%d');res={r['レースコード']:r for r in rows(f'data/results/realtime/{ymd}.csv')}
        for r,x,s4,s5,dc in feats:
            fr=features4(x) if head==4 else features5(x,s4)
            if passes(fr,rule):caln+=1;calh+=targetfn(res.get(r['レースコード'],{}))
        ingest_prior_day_preview(cache,d);ingest_motor(hist,seen,d);d+=timedelta(days=1)

    bets=[];races=[];d=TEST_START
    while d<=TEST_END:
        feats=process_features(d,cache,hist);ymd=d.strftime('%Y/%m/%d');ods={r['レースコード']:r for r in rows(f'data/previews/od3/{ymd}.csv')}
        frozen=[]
        for r,x,s4,s5,dc in feats:
            fr=features4(x) if head==4 else features5(x,s4)
            if not passes(fr,rule):continue
            score=s4 if head==4 else score45v4(x,s4);p=cal_prob(train_prob,score)
            chosen=select_set(head,p,ods.get(r['レースコード'],{}),pairs)
            if not chosen:continue
            allocate(chosen);co=composite(chosen);n=len(chosen)
            rr={'model':model,'date':str(d),'race_code':r['レースコード'],'venue':r.get('レース場コード',''),'race':r.get('レース回',''),'score':round(score,2),'head_prob':round(p,4),'tickets':n,'composite_odds':round(co,2)};rr.update({k:round(v,3) for k,v in fr.items()});races.append(rr)
            for z in chosen:
                z.update({'model':model,'head':head,'date':str(d),'race_code':r['レースコード'],'venue':r.get('レース場コード',''),'race':r.get('レース回',''),'score':round(score,2),'tickets':n,'composite_odds':round(co,2)});frozen.append(z)
        # outcomes only after choices are frozen
        pay={r['レースコード']:r for r in rows(f'data/results/payouts/{ymd}.csv')};res={r['レースコード']:r for r in rows(f'data/results/realtime/{ymd}.csv')}
        for b in frozen:
            pr=pay.get(b['race_code'],{});actual=(pr.get('3連単_組番') or '').strip();hit=actual==b['combo'];b['actual_combo']=actual;b['hit']=int(hit);b['payout100']=i(pr.get('3連単_払戻金')) if hit else 0;b['return']=b['payout100']*(b['stake']//100) if hit else 0;bets.append(b)
        for rr in [q for q in races if q['date']==str(d)]:rr['head_hit']=targetfn(res.get(rr['race_code'],{}))
        ingest_prior_day_preview(cache,d);ingest_motor(hist,seen,d);d+=timedelta(days=1)

    for r in races:
        bs=[b for b in bets if b['race_code']==r['race_code']];r['bet_hit']=int(any(b['hit'] for b in bs));r['return']=sum(b['return'] for b in bs)
    return {'model':model,'head':head,'rule':rule,'caln':caln,'calh':calh,'bets':bets,'races':races}

def summary(z):
    races=z['races'];bets=z['bets'];st=sum(b['stake'] for b in bets);ret=sum(b['return'] for b in bets);hh=sum(r['head_hit'] for r in races);bh=sum(r['bet_hit'] for r in races)
    return {'n':len(races),'hh':hh,'hr':hh/len(races)*100 if races else 0,'bh':bh,'br':bh/len(races)*100 if races else 0,'stake':st,'ret':ret,'profit':ret-st,'roi':ret/st*100 if st else 0,'tickets':len(bets)/len(races) if races else 0}

def main():
    z4=run_model('4カド攻め',4,RULE4,target4);z5=run_model('5頭展開',5,RULE5,target5)
    allbets=z4['bets']+z5['bets'];allraces=z4['races']+z5['races']
    if allbets:
        with open('bets_v18.csv','w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=sorted(set().union(*(b.keys() for b in allbets))));w.writeheader();w.writerows(allbets)
    if allraces:
        fields=sorted(set().union(*(r.keys() for r in allraces)))
        with open('races_v18.csv','w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(allraces)
    a=summary(z4);b=summary(z5)
    L=['# v18 v17発想の4カド・5頭横展開','',f'学習 {TRAIN_START}〜{TRAIN_END}、確認 {CAL_START}〜{CAL_END}、完全テスト {TEST_START}〜{TEST_END}。','閾値はv17の中心値をそのまま横展開し、8/3〜9/2の結果では調整していない。3連単相手は学習期間の頭成立時ペア分布を当日市場へ縮約、合成5倍以上、1R最大5,000円。','',
       '## 固定条件','### 4カド',f"- 4選手力 >= {RULE4['4選手力']}",f"- 4_ST優位(対3) >= {RULE4['4_ST優位']}",f"- 3壁弱さ >= {RULE4['3壁弱さ']}",f"- 確認期間: {z4['caln']}R / 4頭まくり・MS {z4['calh']}R ({z4['calh']/z4['caln']*100 if z4['caln'] else 0:.1f}%)",'',
       '### 5頭',f"- 4攻撃力 >= {RULE5['4攻撃力']}",f"- 1・2抵抗力 >= {RULE5['1_2抵抗力']}",f"- 5取り切り力 >= {RULE5['5取り切り力']}",f"- 確認期間: {z5['caln']}R / 5頭 {z5['calh']}R ({z5['calh']/z5['caln']*100 if z5['caln'] else 0:.1f}%)",'',
       '## 1か月完全テスト','|モデル|購入R|頭成立|頭率|3連単的中|3連単率|投資|払戻|利益|回収率|平均点数|','|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|',
       f"|4カド攻め|{a['n']}|{a['hh']}|{a['hr']:.1f}%|{a['bh']}|{a['br']:.1f}%|{a['stake']:,}円|{a['ret']:,}円|{a['profit']:,}円|{a['roi']:.1f}%|{a['tickets']:.1f}|",
       f"|5頭展開|{b['n']}|{b['hh']}|{b['hr']:.1f}%|{b['bh']}|{b['br']:.1f}%|{b['stake']:,}円|{b['ret']:,}円|{b['profit']:,}円|{b['roi']:.1f}%|{b['tickets']:.1f}|",'',
       '## 注意','- 4カドの頭成立は4号艇1着かつ決まり手がまくり/まくり差し。','- 5頭は5号艇1着を目的変数にしており、「4が攻めて1/2が抵抗して5が取った」という因果を結果データから直接ラベル付けしてはいない。既存4→5モデルと同じく展開代理変数。']
    open('summary_v18.md','w',encoding='utf-8').write('\n'.join(L)+'\n')

if __name__=='__main__':main()
