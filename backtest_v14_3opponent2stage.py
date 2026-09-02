from backtest import *
from backtest_v4 import ingest_prior_day_preview, score3v4, motor_attack
from backtest_v3 import ingest_motor
from backtest_v5_ev import PRELOAD_START, TEST_START, TEST_END, cal_prob, process_features, market_conditional
from collections import defaultdict
from datetime import date,timedelta
import csv,math,itertools

TRAIN_START=date(2026,6,1); TRAIN_END=date(2026,7,15)
SEL_START=date(2026,7,16); SEL_END=date(2026,8,2)
SCORE_MIN=68.0; BUDGET=5000
LANES=[1,2,4,5,6]


def clamp01(v): return max(0.0,min(1.0,v))

def boat_base_feats(z,lane):
    # All inputs are pre-race / prior-known only.
    fs=[1.0]
    fs += [1.0 if lane==k else 0.0 for k in LANES]
    fs += [
        clamp01((z['wr']-3.0)/5.0),
        clamp01(z['waku_wr']/8.0),
        clamp01((.22-z['waku_st'])/.12),
        clamp01((.22-z['nst'])/.12),
        motor_attack(z), z['turnfoot'], z['stretch'], z['pexpo'],
        clamp01((z['local']-3.0)/5.0), clamp01(z['past_win']/.25),
    ]
    return fs


def second_feats(x,lane):
    return boat_base_feats(x[lane],lane)


def third_feats(x,second,lane):
    fs=boat_base_feats(x[lane],lane)
    # Candidate-specific second->third pair interactions.
    fs += [1.0 if (second==s and lane==t) else 0.0 for s in LANES for t in LANES if t!=s]
    return fs


def softmax_scores(weights, rows):
    vals=[]
    for lane,fs in rows:
        z=sum(w*v for w,v in zip(weights,fs)); vals.append((lane,z))
    m=max(z for _,z in vals); ex=[(lane,math.exp(z-m)) for lane,z in vals]; den=sum(v for _,v in ex)
    return {lane:v/den for lane,v in ex}


def fit_choice(obs, feat_fn, epochs=120, lr=.035, l2=.015):
    if not obs: return []
    # obs: [(x, chosen, optional_second)]
    x0,chosen,*rest=obs[0]
    rows=[(l,feat_fn(x0,*(rest or []),l) if rest else feat_fn(x0,l)) for l in LANES if not rest or l!=rest[0]]
    w=[0.0]*len(rows[0][1])
    for ep in range(epochs):
        eta=lr/(1+.018*ep)
        for ob in obs:
            x,chosen,*r=ob; sec=r[0] if r else None
            lanes=[l for l in LANES if l!=sec]
            rows=[(l,feat_fn(x,sec,l) if sec is not None else feat_fn(x,l)) for l in lanes]
            ps=softmax_scores(w,rows)
            grad=[-l2*q for q in w]
            for l,fs in rows:
                err=(1.0 if l==chosen else 0.0)-ps[l]
                for j,v in enumerate(fs): grad[j]+=err*v
            for j in range(len(w)): w[j]+=eta*grad[j]
    return w


def pair_probs(x,w2,w3):
    p2=softmax_scores(w2,[(l,second_feats(x,l)) for l in LANES])
    out=[]
    for s in LANES:
        p3=softmax_scores(w3,[(t,third_feats(x,s,t)) for t in LANES if t!=s])
        for t in LANES:
            if t==s: continue
            out.append((f'3-{s}-{t}',p2[s]*p3[t],p2[s],p3[t]))
    sm=sum(z[1] for z in out)
    return [(c,p/sm,p2x,p3x) for c,p,p2x,p3x in out]


def odds_map(od):
    return {c:o for c,o,_ in market_conditional(od,3)}


def composite(items):
    s=sum(1/z['odds'] for z in items if z['odds']>0)
    return 1/s if s>0 else 999.0


def build_tickets(x,phead,od,min_comp,max_tickets):
    om=odds_map(od); cand=[]
    for combo,q,p2,p3 in pair_probs(x,W2,W3):
        o=om.get(combo,0)
        if o<=0: continue
        pc=phead*q
        cand.append({'combo':combo,'odds':o,'pair_prob_model':q,'second_prob':p2,'third_prob_cond':p3,'combo_prob':pc,'model_ev':pc*o})
    # Own model probability ranks the opponents; market odds are used only for price/composite control.
    cand.sort(key=lambda z:(z['combo_prob'],z['model_ev']),reverse=True)
    chosen=[]
    for z in cand:
        if len(chosen)>=max_tickets: break
        if composite(chosen+[z])>=min_comp: chosen.append(z)
    return chosen


def allocate(chosen):
    if not chosen:return
    n=len(chosen)
    for z in chosen:z['stake']=100
    remain=BUDGET-100*n
    if remain<=0:return
    # Conservative probability-weighted allocation, 100-yen units.
    units=remain//100; sw=sum(z['combo_prob'] for z in chosen)
    raw=[units*z['combo_prob']/sw for z in chosen]; add=[int(v) for v in raw]
    left=units-sum(add); order=sorted(range(n),key=lambda k:raw[k]-add[k],reverse=True)
    for k in order[:left]:add[k]+=1
    for z,a in zip(chosen,add):z['stake']+=100*a


def train_models(cache,hist,seen):
    train3=[]; obs2=[]; obs3=[]; d=TRAIN_START
    while d<=TRAIN_END:
        feats=process_features(d,cache,hist); ymd=d.strftime('%Y/%m/%d')
        res={r['レースコード']:r for r in rows(f'data/results/realtime/{ymd}.csv')}
        pay={r['レースコード']:r for r in rows(f'data/results/payouts/{ymd}.csv')}
        for r,x,s4,s5,dc in feats:
            s3=score3v4(x); rr=res.get(r['レースコード'],{}); win=i(rr.get('1着_艇番')); kim=(rr.get('決まり手') or '').replace('　','').replace(' ','')
            y=int(win==3 and kim in ('まくり','まくり差し')); train3.append((s3,y))
            if y:
                a=(pay.get(r['レースコード'],{}).get('3連単_組番') or '').strip().split('-')
                if len(a)==3 and all(v.isdigit() for v in a):
                    sec,thr=int(a[1]),int(a[2])
                    if sec in LANES and thr in LANES and sec!=thr:
                        obs2.append((x,sec)); obs3.append((x,thr,sec))
        ingest_prior_day_preview(cache,d); ingest_motor(hist,seen,d); d+=timedelta(days=1)
    return train3,fit_choice(obs2,second_feats),fit_choice(obs3,third_feats),len(obs2)


def evaluate_period(start,end,cache,hist,seen,train3,min_comp,max_tickets,save=False):
    bets=[]; races=[]; d=start
    while d<=end:
        feats=process_features(d,cache,hist); ymd=d.strftime('%Y/%m/%d')
        ods={r['レースコード']:r for r in rows(f'data/previews/od3/{ymd}.csv')}
        frozen=[]
        for r,x,s4,s5,dc in feats:
            s3=score3v4(x)
            if s3<SCORE_MIN: continue
            phead=cal_prob(train3,s3); chosen=build_tickets(x,phead,ods.get(r['レースコード'],{}),min_comp,max_tickets)
            if not chosen:continue
            allocate(chosen); co=composite(chosen)
            race={'date':str(d),'race_code':r['レースコード'],'venue':r.get('レース場コード',''),'race':r.get('レース回',''),'score3':round(s3,2),'p3':round(phead,4),'tickets':len(chosen),'composite_odds':round(co,2)}
            races.append(race)
            for z in chosen:
                z.update({'date':str(d),'race_code':r['レースコード'],'venue':r.get('レース場コード',''),'race':r.get('レース回',''),'score3':round(s3,2),'composite_odds':round(co,2)}); frozen.append(z)
        pay={r['レースコード']:r for r in rows(f'data/results/payouts/{ymd}.csv')}
        res={r['レースコード']:r for r in rows(f'data/results/realtime/{ymd}.csv')}
        for b in frozen:
            pr=pay.get(b['race_code'],{}); actual=(pr.get('3連単_組番') or '').strip(); hit=actual==b['combo']
            b['actual_combo']=actual; b['hit']=int(hit); b['payout100']=i(pr.get('3連単_払戻金')) if hit else 0; b['return']=b['payout100']*(b['stake']//100) if hit else 0; bets.append(b)
        # after tickets frozen, label head event for diagnostics
        for race in [q for q in races if q['date']==str(d)]:
            rr=res.get(race['race_code'],{}); win=i(rr.get('1着_艇番')); kim=(rr.get('決まり手') or '').replace('　','').replace(' ','')
            race['head_hit']=int(win==3 and kim in ('まくり','まくり差し'))
        ingest_prior_day_preview(cache,d); ingest_motor(hist,seen,d); d+=timedelta(days=1)
    for r in races:
        bs=[b for b in bets if b['race_code']==r['race_code']]; r['bet_hit']=int(any(b['hit'] for b in bs)); r['return']=sum(b['return'] for b in bs)
    st=sum(b['stake'] for b in bets); ret=sum(b['return'] for b in bets)
    return bets,races,st,ret


def main():
    global W2,W3
    cache={};hist=defaultdict(list);seen=set();d=PRELOAD_START
    while d<TRAIN_START:
        ingest_motor(hist,seen,d)
        if d>=TRAIN_START-timedelta(days=12): ingest_prior_day_preview(cache,d)
        d+=timedelta(days=1)
    train3,W2,W3,ntrain=train_models(cache,hist,seen)

    # Pre-test only: choose opponent breadth / composite threshold by ROI, requiring >=8 races.
    configs=[]
    cache_snap={k:(v.copy() if isinstance(v,dict) else v) for k,v in cache.items()}; hist_snap=defaultdict(list,{k:list(v) for k,v in hist.items()}); seen_snap=set(seen)
    for mc,mt in itertools.product([5.0,7.0,10.0,15.0],[3,5,7,9,12]):
        c={k:(v.copy() if isinstance(v,dict) else v) for k,v in cache_snap.items()}; h=defaultdict(list,{k:list(v) for k,v in hist_snap.items()}); s=set(seen_snap)
        b,r,st,ret=evaluate_period(SEL_START,SEL_END,c,h,s,train3,mc,mt)
        if len(r)>=8 and st>0:
            roi=ret/st; configs.append((roi,ret-st,len(r),mc,mt,len(b)/len(r)))
    configs.sort(reverse=True)
    if configs: _,_,_,BEST_COMP,BEST_MAX,_=configs[0]
    else: BEST_COMP,BEST_MAX=5.0,9

    # Restore state at end of training, then advance through selection period without using its results for model fitting.
    cache={k:(v.copy() if isinstance(v,dict) else v) for k,v in cache_snap.items()}; hist=defaultdict(list,{k:list(v) for k,v in hist_snap.items()}); seen=set(seen_snap)
    d=SEL_START
    while d<=SEL_END:
        ingest_prior_day_preview(cache,d); ingest_motor(hist,seen,d); d+=timedelta(days=1)

    bets,races,st,ret=evaluate_period(TEST_START,TEST_END,cache,hist,seen,train3,BEST_COMP,BEST_MAX)
    hh=sum(r['head_hit'] for r in races); bh=sum(r['bet_hit'] for r in races)
    if bets:
        with open('bets_v14.csv','w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=list(bets[0].keys()));w.writeheader();w.writerows(bets)
    if races:
        with open('races_v14.csv','w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=list(races[0].keys()));w.writeheader();w.writerows(races)

    L=['# v14 3号艇 二段階相手モデル','',f'学習 {TRAIN_START}〜{TRAIN_END}、買い目幅選択 {SEL_START}〜{SEL_END}、完全テスト {TEST_START}〜{TEST_END}。',
       'v13のレース選別 score3>=68 を固定。相手は市場構成比ではなく、事前特徴から 2着→3着を別々に学習する条件付きsoftmax。オッズは最終的な価格/合成制約だけに使用。1R最大5,000円。','',
       '## 事前固定設定',f'- 学習した3頭成功サンプル: {ntrain}',f'- 合成オッズ下限: {BEST_COMP:.1f}倍',f'- 最大点数: {BEST_MAX}点','',
       '## 1か月完全テスト','|項目|結果|','|---|---:|',f'|購入レース|{len(races)}|',f'|3頭まくり/MS成立|{hh}|',f'|頭成立率|{(hh/len(races)*100 if races else 0):.1f}%|',f'|3連単的中|{bh}|',f'|3連単的中率|{(bh/len(races)*100 if races else 0):.1f}%|',f'|投資|{st:,}円|',f'|払戻|{ret:,}円|',f'|回収率|{(ret/st*100 if st else 0):.1f}%|',f'|平均点数|{(len(bets)/len(races) if races else 0):.1f}|',f'|平均合成オッズ|{(sum(r["composite_odds"] for r in races)/len(races) if races else 0):.2f}倍|','',
       '## 事前期間で比較した上位設定','|ROI|損益|R|合成下限|最大点|平均点|','|---:|---:|---:|---:|---:|---:|']
    for roi,profit,n,mc,mt,av in configs[:10]:L.append(f'|{roi*100:.1f}%|{profit:,}円|{n}|{mc:.1f}|{mt}|{av:.1f}|')
    L+=['','## テスト的中レース','|日付|場|R|score3|結果|払戻/100円|点数|合成|','|---|---:|---:|---:|---|---:|---:|---:|']
    for r in races:
        if not r['bet_hit']:continue
        b=[z for z in bets if z['race_code']==r['race_code'] and z['hit']][0]
        L.append(f"|{r['date']}|{r['venue']}|{r['race']}|{r['score3']:.2f}|{b['actual_combo']}|{b['payout100']:,}円|{r['tickets']}|{r['composite_odds']:.2f}倍|")
    open('summary_v14.md','w',encoding='utf-8').write('\n'.join(L)+'\n')

if __name__=='__main__':main()
