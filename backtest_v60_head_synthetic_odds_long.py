"""v60: head probability x synthetic head odds, long out-of-sample backtest.

Core idea:
- Do NOT estimate each trifecta combination probability.
- Estimate only P(target boat wins) from the pre-race/direct score.
- Convert all 20 trifecta odds with that head into one synthetic head price:
      O_head = 1 / sum_i(1/O_i)
  This is the equal-return dutching price for covering all 20 head-fixed combinations.
- EV_head = P(head) * O_head.

No-leak protocol:
- OOS betting period: 2026-07-19..2026-09-02 (od3 archive available).
- Candidate/direct rows are pre-race only.
- Head-probability samples are updated walk-forward: a day's outcomes are added only AFTER that day's bets are frozen.
- od3 is loaded before results/payouts; results/payouts are loaded only after selections/stakes are frozen.
- Actual entry/course and STT course columns are not used by the underlying direct model.
"""
import csv, math
from collections import defaultdict
from backtest import rows
from backtest_v57_ev_variable_staking import freeze_all, load_odds, local_prob, combos_for_head

OOS0='2026-07-19'; OOS1='2026-09-02'
HEADS=[3,5]
EV_LEVELS=[1.00,1.10,1.20,1.30,1.40,1.50]
FLAT_RACE_STAKE=2000   # 20 combos x minimum 100 yen
UNIT=100
BANK0=100000
KELLY_FRAC=.125
MAX_RACE_FRAC=.05


def synthetic_head_odds(od, head):
    inv=0.0; vals={}
    for c in combos_for_head(head):
        try:o=float(od.get('3連単_'+c) or 0)
        except:o=0
        if o<=0:return 0.0,{}
        vals[c]=o; inv+=1.0/o
    return (1.0/inv if inv>0 else 0.0), vals


def alloc_dutch(odds, total):
    """Cover all 20 combos. 100 yen baseline each, remainder inverse-odds weighted."""
    n=len(odds)
    if n!=20 or total<n*UNIT:return {}
    base=n*UNIT; rem=total-base
    inv={c:1/o for c,o in odds.items()}; z=sum(inv.values())
    raw={c:(rem*inv[c]/z if z else 0) for c in odds}
    extra={c:int(raw[c]//UNIT)*UNIT for c in odds}
    left=rem-sum(extra.values())
    order=sorted(odds,key=lambda c:raw[c]-extra[c],reverse=True)
    j=0
    while left>=UNIT and order:
        extra[order[j%len(order)]]+=UNIT;left-=UNIT;j+=1
    return {c:UNIT+extra[c] for c in odds}


def settle_alloc(alloc, actual, payout100):
    inv=sum(alloc.values())
    stake=alloc.get(actual,0)
    ret=payout100*(stake//100) if stake else 0
    return inv,ret,int(stake>0)


def kelly_fraction(p,o):
    return max(0.0,(p*o-1)/(o-1)) if o>1 else 0.0


def write_csv(path, rs):
    if not rs:return
    fs=sorted(set().union(*(r.keys() for r in rs)))
    with open(path,'w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=fs);w.writeheader();w.writerows(rs)


def month_key(d):return d[:7]


def main():
    frozen=freeze_all()
    byday=defaultdict(list)
    for z in frozen:byday[z['date']].append(z)

    # Walk-forward probability samples. They are updated only after each date is settled.
    samples={3:[],5:[]}
    ledger=[]; head_history=[]
    bank=BANK0; peak=bank; maxdd=0.0

    for d in sorted(byday):
        arr=byday[d]
        # For calibration dates, there is no odds bet. Freeze features already exist; now load result and update past samples.
        if d<OOS0:
            ymd=d.replace('-','/')
            res={r['レースコード']:r for r in rows(f'data/results/realtime/{ymd}.csv')}
            for z in arr:
                if z['head'] not in HEADS:continue
                rr=res.get(z['race_code'],{}); win=int(float(rr.get('1着_艇番') or 0)); hit=int(win==z['head'])
                samples[z['head']].append((z['score'],hit))
                head_history.append({'date':d,'month':month_key(d),'period':'calibration','head':z['head'],'score':z['score'],'head_hit':hit})
            continue
        if d>OOS1:continue

        # PRE-RESULT phase: calculate p_head, synthetic odds, EV, and both flat/Kelly allocations.
        ods=load_odds(d); frozen_bets=[]
        for z in arr:
            h=z['head']
            if h not in HEADS:continue
            od=ods.get(z['race_code'],{})
            syn,ovals=synthetic_head_odds(od,h)
            if syn<=0:continue
            p=local_prob(samples[h],z['score'])
            ev=p*syn
            flat=alloc_dutch(ovals,FLAT_RACE_STAKE)
            k=kelly_fraction(p,syn)
            raw=bank*KELLY_FRAC*k
            cap=bank*MAX_RACE_FRAC
            total=int(min(raw,cap)//UNIT)*UNIT
            # Covering all 20 combos is only practical when Kelly budget is at least 2,000 yen.
            kall=alloc_dutch(ovals,total) if total>=FLAT_RACE_STAKE else {}
            frozen_bets.append({'date':d,'race_code':z['race_code'],'model':z['model'],'head':h,'score':z['score'],
                                'head_prob':p,'synthetic_odds':syn,'head_ev':ev,'flat_alloc':flat,'kelly_alloc':kall,
                                'kelly_raw':k,'kelly_total':sum(kall.values()) if kall else 0})

        # ONLY NOW load outcomes/payouts for the day.
        ymd=d.replace('-','/')
        res={r['レースコード']:r for r in rows(f'data/results/realtime/{ymd}.csv')}
        pay={r['レースコード']:r for r in rows(f'data/results/payouts/{ymd}.csv')}
        day_k_in=day_k_ret=0
        for b in frozen_bets:
            rr=res.get(b['race_code'],{});pr=pay.get(b['race_code'],{})
            win=int(float(rr.get('1着_艇番') or 0));actual=(pr.get('3連単_組番') or '').strip();payout=int(float(pr.get('3連単_払戻金') or 0))
            head_hit=int(win==b['head'])
            finv,fret,_=settle_alloc(b['flat_alloc'],actual,payout)
            kinv,kret,_=settle_alloc(b['kelly_alloc'],actual,payout) if b['kelly_alloc'] else (0,0,0)
            q={k:v for k,v in b.items() if k not in ('flat_alloc','kelly_alloc')}
            q.update({'winner':win,'head_hit':head_hit,'actual_combo':actual,'payout100':payout,
                      'flat_invest':finv,'flat_return':fret,'kelly_invest':kinv,'kelly_return':kret})
            ledger.append(q);day_k_in+=kinv;day_k_ret+=kret
        bank+=day_k_ret-day_k_in;peak=max(peak,bank);maxdd=max(maxdd,(peak-bank)/peak if peak else 0)

        # After the entire day's selections are settled, update probability samples for future days.
        for z in arr:
            if z['head'] not in HEADS:continue
            rr=res.get(z['race_code'],{});win=int(float(rr.get('1着_艇番') or 0));hit=int(win==z['head'])
            samples[z['head']].append((z['score'],hit))
            head_history.append({'date':d,'month':month_key(d),'period':'oos','head':z['head'],'score':z['score'],'head_hit':hit})

    write_csv('analysis_v60_head_synthetic_odds.csv',ledger)
    write_csv('analysis_v60_head_history.csv',head_history)

    def stat(rs,evmin,kind='flat'):
        q=[r for r in rs if r['head_ev']>=evmin]
        inv=sum(r[kind+'_invest'] for r in q);ret=sum(r[kind+'_return'] for r in q)
        races=len(q);hits=sum(r['head_hit'] for r in q)
        return races,hits,inv,ret,(100*ret/inv if inv else 0)

    L=['# v60 頭確率 × 合成オッズ 長期バックテスト','',
       f'OOS期間: **{OOS0}〜{OOS1}**（締切前od3が利用できる長期区間）。頭確率は6/1からウォークフォワード更新。',
       '3連単20通りの相手確率は推定しない。対象艇頭の20通りを全てカバーし、締切前オッズから `合成頭オッズ = 1 / Σ(1/各3連単オッズ)` を計算。',
       '`頭EV = 頭確率 × 合成頭オッズ`。例: 頭25%ならEV100%の損益分岐は4.0倍、EV130%なら5.2倍。',
       '買い目・配分を固定してから結果/払戻を読む。','','## 頭モデルの月別安定性（候補全体）','|頭|月|候補R|頭的中|頭率|','|---:|---|---:|---:|---:|']
    for h in HEADS:
        for m in sorted(set(r['month'] for r in head_history)):
            q=[r for r in head_history if r['head']==h and r['month']==m];n=len(q);hh=sum(r['head_hit'] for r in q)
            if n:L.append(f'|{h}|{m}|{n}|{hh}|{100*hh/n:.1f}%|')

    L+=['','## OOS 46日間: EV閾値別・1R 2,000円ダッチ','|頭|EV閾値|購入R|頭的中|投資|払戻|ROI|','|---:|---:|---:|---:|---:|---:|---:|']
    for h in HEADS:
        rr=[r for r in ledger if r['head']==h]
        for th in EV_LEVELS:
            n,hh,inv,ret,roi=stat(rr,th,'flat');L.append(f'|{h}|{th:.2f}|{n}|{hh}|{inv:,}円|{ret:,}円|{roi:.1f}%|')
    for th in EV_LEVELS:
        n,hh,inv,ret,roi=stat(ledger,th,'flat');L.append(f'|合計|{th:.2f}|{n}|{hh}|{inv:,}円|{ret:,}円|{roi:.1f}%|')

    # Split stability: first/second half without retuning.
    split='2026-08-11'
    L+=['','## EV>=1.30 前半/後半の再現性（2,000円ダッチ）','|頭|期間|購入R|頭的中|ROI|','|---:|---|---:|---:|---:|']
    for h in HEADS:
        for name,lo,hi in [('前半',OOS0,'2026-08-10'),('後半',split,OOS1)]:
            rr=[r for r in ledger if r['head']==h and lo<=r['date']<=hi];n,hh,inv,ret,roi=stat(rr,1.30,'flat');L.append(f'|{h}|{name}|{n}|{hh}|{roi:.1f}%|')

    # Practical Kelly is shown only for bets whose synthetic Kelly budget can cover all 20 tickets.
    kb=[r for r in ledger if r['head_ev']>=1.30 and r['kelly_invest']>0]
    kinv=sum(r['kelly_invest'] for r in kb);kret=sum(r['kelly_return'] for r in kb)
    L+=['','## EV>=1.30・1/8 Kelly（20点を全て100円以上でカバーできる時のみ）',
        f'- 初期資金: {BANK0:,}円',f'- 最終資金: **{bank:,}円**',f'- 対象R: {len(kb)}',
        f'- 投資: {kinv:,}円 / 払戻: {kret:,}円 / ROI **{100*kret/kinv if kinv else 0:.1f}%**',f'- 最大DD: **{100*maxdd:.1f}%**','',
        '## 注意','- 20通り全カバーなので、頭確率だけでEVを評価できる。部分買いにすると「頭確率=選択買い目の的中確率」ではなくなるため、このv60では行わない。',
        '- od3は締切前の集計中オッズ。実際の払戻は確定払戻を使用するため、ダッチ時の想定均等リターンと実収益にはオッズ変動差が出る。',
        '- EV閾値別の表は感度確認であり、最も良い閾値を後から選んで正式採用するものではない。前半/後半の再現性を重視する。']
    open('summary_v60_head_synthetic_odds_long.md','w',encoding='utf-8').write('\n'.join(L)+'\n')

if __name__=='__main__':main()
