"""v59: model-only combo probability; odds are used only as price.

Fixes v57's key failure: market inverse-odds share is NOT blended into combo probability.
No-leak:
- Direct/candidate features freeze before outcomes.
- Probability calibration (head and conditional temperature): <= 2026-07-18.
- Rule itself is pre-fixed: A score>=55, combo conditional probability>=2.5%, EV>=1.10.
- Validation 2026-07-19..08-02 and test 2026-08-03..09-02 are report-only, not used to tune the rule.
- od3 pre-close odds only; results/payouts after tickets freeze.
"""
import csv, math
from collections import defaultdict
from backtest_v57_ev_variable_staking import (
    freeze_all,label_outcomes,choose_temp,softmax,local_prob,load_odds,combos_for_head,
    INITIAL_BANK,UNIT
)

HEADS=[3,5]
SCORE_MIN=55.0
PREA_MIN=50.0
COND_MIN=.025
EV_MIN=1.10
BANK0=100000
KELLY_FRAC=.125
MAX_RACE_FRAC=.02
MAX_TICKET_FRAC=.005


def make_rows(lab,head,temp):
    train=[(z['score'],z['head_hit']) for z in lab if z['period']=='calibration' and z['head']==head]
    odcache={};out=[]
    for z in lab:
        if z['head']!=head or z['period']=='calibration':continue
        if z['date'] not in odcache:odcache[z['date']]=load_odds(z['date'])
        od=odcache[z['date']].get(z['race_code'],{})
        if not od:continue
        ph=local_prob(train,z['score']);qc=softmax(z['pair_scores'],temp)
        for c in combos_for_head(head):
            o=float(od.get('3連単_'+c) or 0)
            q=qc.get(c,0);pc=ph*q;ev=pc*o if o>0 else 0
            out.append({'date':z['date'],'period':z['period'],'race_code':z['race_code'],'model':z['model'],'head':head,'score':z['score'],
                        'band':'A' if z['score']>=SCORE_MIN else ('preA' if z['score']>=PREA_MIN else 'low'),
                        'combo':c,'odds_pre':o,'head_prob':ph,'conditional_prob':q,'combo_prob':pc,'ev':ev,
                        'actual_combo':z['actual_combo'],'payout100':z['payout100']})
    return out


def selected(rs,band='A',evmin=EV_MIN):
    return [r for r in rs if r['band']==band and r['conditional_prob']>=COND_MIN and r['ev']>=evmin]


def agg(bs):
    st=len(bs)*100;hit=sum(b['combo']==b['actual_combo'] for b in bs);ret=sum(b['payout100'] for b in bs if b['combo']==b['actual_combo'])
    rc=len(set((b['date'],b['race_code']) for b in bs));return rc,len(bs),hit,st,ret,100*ret/st if st else 0


def kelly_run(bs):
    bank=BANK0;peak=bank;maxdd=0;led=[];by=defaultdict(list)
    for b in bs:by[(b['date'],b['race_code'])].append(b)
    for key in sorted(by):
        cand=[]
        for b in by[key]:
            p=b['combo_prob'];o=b['odds_pre'];k=max(0,(p*o-1)/(o-1)) if o>1 else 0
            raw=min(bank*MAX_TICKET_FRAC,bank*KELLY_FRAC*k);stake=max(UNIT,int(raw)//UNIT*UNIT);cand.append([b,stake,k])
        cap=max(UNIT,int(bank*MAX_RACE_FRAC)//UNIT*UNIT)
        total=sum(x[1] for x in cand)
        if total>cap:
            scale=cap/total
            for x in cand:x[1]=max(UNIT,int(x[1]*scale)//UNIT*UNIT)
            while sum(x[1] for x in cand)>cap:
                j=max(range(len(cand)),key=lambda i:cand[i][1])
                if cand[j][1]<=UNIT:break
                cand[j][1]-=UNIT
        inv=sum(x[1] for x in cand);ret=0
        for b,stake,k in cand:
            hit=b['combo']==b['actual_combo'];r=b['payout100']*(stake//100) if hit else 0;ret+=r
            z=dict(b);z.update({'stake':stake,'kelly_raw':k,'hit':int(hit),'return':r});led.append(z)
        bank+=ret-inv;peak=max(peak,bank);maxdd=max(maxdd,(peak-bank)/peak if peak else 0)
    return led,bank,maxdd


def write_csv(path,rs):
    if not rs:return
    fs=sorted(set().union(*(r.keys() for r in rs)))
    with open(path,'w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=fs);w.writeheader();w.writerows(rs)


def main():
    frozen=freeze_all();lab=label_outcomes(frozen);temps={};allr=[]
    for h in HEADS:
        temps[h],_=choose_temp(lab,h);allr+=make_rows(lab,h,temps[h])
    live=[r for r in allr if r['period']=='test' and r['band']=='A' and r['conditional_prob']>=COND_MIN and r['ev']>=EV_MIN]
    led,bank,dd=kelly_run(live);write_csv('analysis_v59_model_ev.csv',allr);write_csv('bets_v59_model_ev_kelly.csv',led)
    L=['# v59 モデル確率 × 締切前オッズ EVバックテスト','',
       'v57で市場構成比を確率側に混ぜた問題を修正。v59では**相手確率はモデルだけ**で作り、od3は価格(EV)判定にのみ使用。',
       f'固定ルール: 直前score>={SCORE_MIN:.0f}、相手条件付き確率>={COND_MIN*100:.1f}%、EV>={EV_MIN:.2f}。Validation/Testを見て閾値変更なし。',
       f'資金配分: 1/8 Kelly、初期{BANK0:,}円、1点最大{MAX_TICKET_FRAC*100:.1f}%、1R最大{MAX_RACE_FRAC*100:.1f}%。','','## 校正済みsoftmax温度','|頭|温度|','|---:|---:|']
    for h in HEADS:L.append(f'|{h}|{temps[h]:.2f}|')
    L+=['','## 固定ルールのValidation / Test','|頭|期間|レース|点数|平均点/R|的中|投資|払戻|ROI|','|---:|---|---:|---:|---:|---:|---:|---:|---:|']
    for h in HEADS:
        for per in ['validation','test']:
            bs=selected([r for r in allr if r['head']==h and r['period']==per]);rc,n,hit,st,ret,roi=agg(bs);L.append(f'|{h}|{per}|{rc}|{n}|{n/rc if rc else 0:.2f}|{hit}|{st:,}円|{ret:,}円|{roi:.1f}%|')
    for per in ['validation','test']:
        bs=selected([r for r in allr if r['period']==per]);rc,n,hit,st,ret,roi=agg(bs);L.append(f'|合計|{per}|{rc}|{n}|{n/rc if rc else 0:.2f}|{hit}|{st:,}円|{ret:,}円|{roi:.1f}%|')
    inv=sum(x['stake'] for x in led);ret=sum(x['return'] for x in led);hits=sum(x['hit'] for x in led)
    L+=['','## Test 1/8 Kelly',f'- 最終資金: **{bank:,}円**（初期 {BANK0:,}円）',f'- 投資累計: {inv:,}円 / 払戻: {ret:,}円 / ROI **{100*ret/inv if inv else 0:.1f}%**',f'- 的中 {hits}点 / 最大DD **{100*dd:.1f}%**']
    L+=['','## EV閾値感度（ルール変更ではなく診断）','|頭|期間|EV>=1.00|1.10|1.20|1.30|1.50|','|---:|---|---:|---:|---:|---:|---:|']
    for h in HEADS:
        for per in ['validation','test']:
            vals=[]
            rr=[r for r in allr if r['head']==h and r['period']==per and r['band']=='A' and r['conditional_prob']>=COND_MIN]
            for th in [1.0,1.1,1.2,1.3,1.5]:vals.append(agg([r for r in rr if r['ev']>=th])[-1])
            L.append(f'|{h}|{per}|'+'|'.join(f'{v:.1f}%' for v in vals)+'|')
    L+=['','## 準A(score 50-55) 同じ固定EVルール','|頭|期間|レース|点数|的中|ROI|','|---:|---|---:|---:|---:|---:|']
    for h in HEADS:
        for per in ['validation','test']:
            rr=[r for r in allr if r['head']==h and r['period']==per];bs=selected(rr,'preA');rc,n,hit,st,ret,roi=agg(bs);L.append(f'|{h}|{per}|{rc}|{n}|{hit}|{roi:.1f}%|')
    L+=['','## 8/20 EV選定','|レース|頭|score|点数|買い目(EV)|結果|','|---|---:|---:|---:|---|---|']
    by=defaultdict(list)
    for b in live:
        if b['date']=='2026-08-20':by[(b['race_code'],b['head'])].append(b)
    for (code,h),bs in sorted(by.items()):
        desc='; '.join(f'{b["combo"]}({b["ev"]:.2f})' for b in sorted(bs,key=lambda z:z['ev'],reverse=True));L.append(f'|{code}|{h}|{bs[0]["score"]:.1f}|{len(bs)}|{desc}|{bs[0]["actual_combo"]}|')
    L+=['','## 判定基準','- ValidationとTestの両方で100%を超えない場合は実戦採用しない。','- KellyはEV選定がプラスであることを確認してから採用する。資金配分だけで負の期待値を救うことはできない。']
    open('summary_v59_model_probability_ev.md','w',encoding='utf-8').write('\n'.join(L)+'\n')

if __name__=='__main__':main()
