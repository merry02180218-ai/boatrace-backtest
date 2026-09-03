from backtest import *
from backtest_v3 import ingest_motor
from backtest_v4 import ingest_prior_day_preview, score3v4, score4v4, score45v4, resistance12, attack4_component
from backtest_v5_ev import PRELOAD_START, cal_prob, process_features, market_conditional
from backtest_v11_3pair import build_pair_dist, composite, pair_key
from backtest_v17_core3 import allocate
from analyze_3attack_feature_correlations import feature_row
from backtest_v18_core45 import features4, target4, target5, strength, st_edge, wallweak, c01
from collections import defaultdict
from datetime import date,timedelta
import csv

TRAIN_START=date(2026,6,1); TRAIN_END=date(2026,7,15)
TEST_START=date(2026,8,27); TEST_END=date(2026,9,2)
MIN_COMPOSITE=5.0
# v20: motor/foot metrics are NOT hard gates. Selection is driven by racer/ST/wall/attack structure.
RULES={
 '3まくり':{'3選手力':.50,'3_ST優位':.55,'2壁弱さ':.55},
 '3まくり差し':{'3選手力':.50,'3_ST優位':.45,'1弱さ':.45,'2壁弱さ':.45},
 '4カドまくり':{'4選手力':.50,'4_ST優位':.55,'3壁弱さ':.55},
 '5頭展開':{'4攻撃力_非motor':.55,'1_2抵抗力':.55,'5選手力':.50},
}
HEAD={'3まくり':3,'3まくり差し':3,'4カドまくり':4,'5頭展開':5}

def target(rr,m):
    win=i(rr.get('1着_艇番')); kim=(rr.get('決まり手') or '').replace('　','').replace(' ','')
    if m=='3まくり': return int(win==3 and kim=='まくり')
    if m=='3まくり差し': return int(win==3 and kim=='まくり差し')
    if m=='4カドまくり': return int(win==4 and kim=='まくり')
    return int(win==5)

def features(x,s3,s4,dc,m):
    if m.startswith('3'):
        fr=feature_row(x,s3,dc)
        return fr
    if m=='4カドまくり': return features4(x)
    # 5-head: remove motor/turn-foot hard gate. 4 attack proxy uses ST edge + 3 wall weakness + 4 racer strength only.
    c,d,e=x[3],x[4],x[5]
    f4=features4(x)
    atk=c01(.40*f4['4_ST優位']+.35*f4['3壁弱さ']+.25*f4['4選手力'])
    return {'4攻撃力_非motor':atk,'1_2抵抗力':resistance12(x),'5選手力':strength(e)}

def passes(fr,rule): return all(fr.get(k,0)>=v for k,v in rule.items())

def score_for(x,s3,s4,m):
    if m.startswith('3'): return s3
    if m=='4カドまくり': return s4
    # retain existing probability score for ticket ranking; motor is not a candidate gate.
    return score45v4(x,s4)

def pair_dist(pair_counts,market_rows,alpha=8.0):
    total=sum(pair_counts.values());out=[]
    for combo,o,share in market_rows:
        k=pair_key(combo);cnt=pair_counts.get(k,0);q=(cnt+alpha*share)/(total+alpha) if total+alpha else share;out.append((combo,o,q,share,cnt))
    s=sum(z[2] for z in out);return [(c,o,q/s if s else sh,sh,cnt) for c,o,q,sh,cnt in out]

def select_set(head,p,od,pairs):
    dist=pair_dist(pairs,market_conditional(od,head));cand=[]
    for combo,o,q,share,cnt in dist:
        pc=p*q;cand.append({'combo':combo,'odds':o,'pair_prob':q,'combo_prob':pc,'market_share':share,'train_pair_count':cnt,'ev':pc*o})
    cand.sort(key=lambda z:(z['combo_prob'],z['ev']),reverse=True);chosen=[]
    for z in cand:
        if composite(chosen+[z])>=MIN_COMPOSITE:chosen.append(z)
    return chosen

def main():
    cache={};hist=defaultdict(list);seen=set();d=PRELOAD_START
    while d<TRAIN_START:
        ingest_motor(hist,seen,d)
        if d>=TRAIN_START-timedelta(days=12):ingest_prior_day_preview(cache,d)
        d+=timedelta(days=1)
    train={m:[] for m in RULES};pairs={m:defaultdict(int) for m in RULES}
    d=TRAIN_START
    while d<=TRAIN_END:
        feats=process_features(d,cache,hist);ymd=d.strftime('%Y/%m/%d');res={r['レースコード']:r for r in rows(f'data/results/realtime/{ymd}.csv')};pay={r['レースコード']:r for r in rows(f'data/results/payouts/{ymd}.csv')}
        for r,x,s4,s5,dc in feats:
            s3=score3v4(x)
            for m in RULES:
                sc=score_for(x,s3,s4,m);y=target(res.get(r['レースコード'],{}),m);train[m].append((sc,y))
                if y:
                    k=pair_key((pay.get(r['レースコード'],{}).get('3連単_組番') or '').strip())
                    if k:pairs[m][k]+=1
        ingest_prior_day_preview(cache,d);ingest_motor(hist,seen,d);d+=timedelta(days=1)
    while d<TEST_START:
        process_features(d,cache,hist);ingest_prior_day_preview(cache,d);ingest_motor(hist,seen,d);d+=timedelta(days=1)
    bets=[];races=[]
    while d<=TEST_END:
        feats=process_features(d,cache,hist);ymd=d.strftime('%Y/%m/%d');ods={r['レースコード']:r for r in rows(f'data/previews/od3/{ymd}.csv')};frozen=[]
        for r,x,s4,s5,dc in feats:
            s3=score3v4(x)
            for m,rule in RULES.items():
                fr=features(x,s3,s4,dc,m)
                if not passes(fr,rule):continue
                sc=score_for(x,s3,s4,m);p=cal_prob(train[m],sc);chosen=select_set(HEAD[m],p,ods.get(r['レースコード'],{}),pairs[m])
                if not chosen:continue
                allocate(chosen);rr={'model':m,'date':str(d),'race_code':r['レースコード'],'venue':r.get('レース場コード',''),'race':r.get('レース回',''),'score':round(sc,2),'tickets':len(chosen),'composite_odds':round(composite(chosen),2)};rr.update({k:round(fr[k],3) for k in rule});races.append(rr)
                for z in chosen:z.update({'model':m,'date':str(d),'race_code':r['レースコード']});frozen.append(z)
        pay={r['レースコード']:r for r in rows(f'data/results/payouts/{ymd}.csv')};res={r['レースコード']:r for r in rows(f'data/results/realtime/{ymd}.csv')}
        for b in frozen:
            pr=pay.get(b['race_code'],{});actual=(pr.get('3連単_組番') or '').strip();hit=actual==b['combo'];b['actual_combo']=actual;b['hit']=int(hit);b['payout100']=i(pr.get('3連単_払戻金')) if hit else 0;b['return']=b['payout100']*(b['stake']//100) if hit else 0;bets.append(b)
        for rr in [q for q in races if q['date']==str(d)]:rr['head_hit']=target(res.get(rr['race_code'],{}),rr['model'])
        ingest_prior_day_preview(cache,d);ingest_motor(hist,seen,d);d+=timedelta(days=1)
    for r in races:
        bs=[b for b in bets if b['race_code']==r['race_code'] and b['model']==r['model']];r['bet_hit']=int(any(b['hit'] for b in bs));r['return']=sum(b['return'] for b in bs)
    if bets:
        with open('bets_v20.csv','w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=sorted(set().union(*(b.keys() for b in bets))));w.writeheader();w.writerows(bets)
    if races:
        with open('races_v20.csv','w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=sorted(set().union(*(r.keys() for r in races))));w.writeheader();w.writerows(races)
    L=['# v20 モーター必須条件なし 4モデル 直近1週間','',f'テスト {TEST_START}〜{TEST_END}。学習 {TRAIN_START}〜{TRAIN_END}。モーター/足は候補抽出の必須条件から除外。テスト結果で閾値調整なし。','', '|モデル|候補R|頭成立|頭率|3連単的中|的中率|投資|払戻|回収率|','|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for m in RULES:
        rs=[r for r in races if r['model']==m];bs=[b for b in bets if b['model']==m];hh=sum(r['head_hit'] for r in rs);bh=sum(r['bet_hit'] for r in rs);st=sum(b['stake'] for b in bs);ret=sum(b['return'] for b in bs)
        L.append(f'|{m}|{len(rs)}|{hh}|{hh/len(rs)*100 if rs else 0:.1f}%|{bh}|{bh/len(rs)*100 if rs else 0:.1f}%|{st:,}円|{ret:,}円|{ret/st*100 if st else 0:.1f}%|')
    L+=['','## 固定条件']
    for m,r in RULES.items():L.append('- '+m+': '+', '.join(f'{k}>={v}' for k,v in r.items()))
    L+=['','注: 5頭の確率スコア/買い目順位には既存score45v4を残すが、候補抽出の必須条件にはモーター/回り足を使用しない。']
    open('summary_v20.md','w',encoding='utf-8').write('\n'.join(L)+'\n')
if __name__=='__main__':main()
