"""v61: trifecta opponent probabilities + synthetic set odds, long OOS.

Core:
- Estimate P(head wins) walk-forward.
- Estimate conditional P(2nd-3rd combo | head wins) from model pair scores only.
- For each race, rank 20 head-fixed trifectas by conditional_prob * pre-close odds.
- Evaluate every prefix 1..20:
    set_prob = P(head) * sum(conditional_prob in set)
    synthetic_set_odds = 1 / sum(1/odds_i)
    set_EV = set_prob * synthetic_set_odds
- Baseline rule is FIXED before OOS result inspection:
    minimum conditional coverage 50%, set_EV >= 1.20, choose prefix with maximum set_EV.
- Also report sensitivity for min coverage 30/40/50/60/70% and EV threshold 1.10/1.20/1.30/1.40.

No leak:
- Pair-score temperature is calibrated only with races <= 2026-07-18.
- OOS odds period 2026-07-19..2026-09-02.
- Head probability samples update after each OOS day's selections are frozen and settled.
- Odds are pre-close od3; results/payouts loaded only after selections and dutch stakes freeze.
- Actual entry/course and STT course fields are not used.
"""
import csv, math
from collections import defaultdict
from backtest import rows
from backtest_v57_ev_variable_staking import freeze_all, load_odds, local_prob, combos_for_head, softmax, choose_temp

CAL1='2026-07-18'; OOS0='2026-07-19'; OOS1='2026-09-02'
HEADS=[3,5]
BASE_COVER=.50
BASE_EV=1.20
COVERS=[.30,.40,.50,.60,.70]
EVS=[1.10,1.20,1.30,1.40]
UNIT=100
RACE_STAKE=2000


def syn_odds(items):
    inv=sum(1/x['odds'] for x in items if x['odds']>0)
    return 1/inv if inv>0 else 0


def dutch(items,total=RACE_STAKE):
    n=len(items)
    if not items or n*UNIT>total:return {}
    base=n*UNIT;rem=total-base
    inv={x['combo']:1/x['odds'] for x in items};z=sum(inv.values())
    raw={c:(rem*inv[c]/z if z else 0) for c in inv}
    ext={c:int(raw[c]//UNIT)*UNIT for c in inv};left=rem-sum(ext.values())
    order=sorted(inv,key=lambda c:raw[c]-ext[c],reverse=True);j=0
    while left>=UNIT and order:
        ext[order[j%len(order)]]+=UNIT;left-=UNIT;j+=1
    return {c:UNIT+ext[c] for c in inv}


def choose_set(z,od,phead,temp,mincov=BASE_COVER,minev=BASE_EV):
    qc=softmax(z['pair_scores'],temp)
    cand=[]
    for c in combos_for_head(z['head']):
        try:o=float(od.get('3連単_'+c) or 0)
        except:o=0
        if o<=0:continue
        q=qc.get(c,0.0)
        cand.append({'combo':c,'odds':o,'cond_prob':q,'cond_value':q*o})
    if len(cand)!=20:return None
    # Ratio q / implied_weight = q*odds. Prefixes in this ordering are natural candidates
    # for maximizing probability mass per unit synthetic price.
    cand.sort(key=lambda x:(x['cond_value'],x['cond_prob']),reverse=True)
    best=None;cum=0.0
    for k in range(1,21):
        cum+=cand[k-1]['cond_prob'];ss=cand[:k];so=syn_odds(ss);sp=phead*cum;ev=sp*so
        if cum+1e-12<mincov or ev+1e-12<minev:continue
        key=(ev,cum,-k)
        if best is None or key>best[0]:
            best=(key,{'tickets':ss,'n':k,'coverage':cum,'set_prob':sp,'synthetic_odds':so,'set_ev':ev})
    if not best:return None
    out=best[1];out['alloc']=dutch(out['tickets'],RACE_STAKE)
    if not out['alloc']:return None
    return out


def settle(sel,actual,payout100):
    inv=sum(sel['alloc'].values());stake=sel['alloc'].get(actual,0)
    ret=payout100*(stake//100) if stake else 0
    return inv,ret,int(stake>0)


def write_csv(path,rs):
    if not rs:return
    clean=[]
    for r in rs:
        clean.append({k:v for k,v in r.items() if k not in ('pair_scores','tickets','alloc')})
    fs=sorted(set().union(*(r.keys() for r in clean)))
    with open(path,'w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=fs);w.writeheader();w.writerows(clean)


def main():
    frozen=freeze_all();byday=defaultdict(list)
    for z in frozen:byday[z['date']].append(z)

    # Label calibration <=7/18 only for conditional-temperature selection.
    calib=[];head_samples={3:[],5:[]}
    for d in sorted(byday):
        if d>CAL1:break
        ymd=d.replace('-','/');res={r['レースコード']:r for r in rows(f'data/results/realtime/{ymd}.csv')};pay={r['レースコード']:r for r in rows(f'data/results/payouts/{ymd}.csv')}
        for z in byday[d]:
            if z['head'] not in HEADS:continue
            rr=res.get(z['race_code'],{});pr=pay.get(z['race_code'],{});win=int(float(rr.get('1着_艇番') or 0));q=dict(z)
            q['period']='calibration';q['head_hit']=int(win==z['head']);q['actual_combo']=(pr.get('3連単_組番') or '').strip();calib.append(q)
            head_samples[z['head']].append((z['score'],q['head_hit']))
    temps={h:choose_temp(calib,h)[0] for h in HEADS}

    ledger=[];sens=[]
    for d in sorted(byday):
        if d<OOS0 or d>OOS1:continue
        ods=load_odds(d);day_base=[];day_sens=[]
        # PRE-RESULT: freeze p_head, set selection, and stakes.
        for z in byday[d]:
            h=z['head']
            if h not in HEADS:continue
            od=ods.get(z['race_code'],{})
            if not od:continue
            ph=local_prob(head_samples[h],z['score'])
            sel=choose_set(z,od,ph,temps[h],BASE_COVER,BASE_EV)
            if sel:
                day_base.append({'date':d,'race_code':z['race_code'],'model':z['model'],'head':h,'score':z['score'],'head_prob':ph,
                                 'tickets_n':sel['n'],'coverage':sel['coverage'],'set_prob':sel['set_prob'],'synthetic_odds':sel['synthetic_odds'],'set_ev':sel['set_ev'],
                                 'tickets':sel['tickets'],'alloc':sel['alloc']})
            for cv in COVERS:
                for evm in EVS:
                    ss=choose_set(z,od,ph,temps[h],cv,evm)
                    if ss:
                        day_sens.append({'date':d,'race_code':z['race_code'],'head':h,'cover_rule':cv,'ev_rule':evm,'tickets_n':ss['n'],
                                         'coverage':ss['coverage'],'set_prob':ss['set_prob'],'synthetic_odds':ss['synthetic_odds'],'set_ev':ss['set_ev'],'alloc':ss['alloc']})
        # ONLY NOW outcomes.
        ymd=d.replace('-','/');res={r['レースコード']:r for r in rows(f'data/results/realtime/{ymd}.csv')};pay={r['レースコード']:r for r in rows(f'data/results/payouts/{ymd}.csv')}
        for b in day_base:
            rr=res.get(b['race_code'],{});pr=pay.get(b['race_code'],{});actual=(pr.get('3連単_組番') or '').strip();payout=int(float(pr.get('3連単_払戻金') or 0));win=int(float(rr.get('1着_艇番') or 0))
            inv,ret,hit=settle(b,actual,payout);q=dict(b);q.update({'winner':win,'head_hit':int(win==b['head']),'actual_combo':actual,'payout100':payout,'invest':inv,'return':ret,'ticket_hit':hit});ledger.append(q)
        for b in day_sens:
            pr=pay.get(b['race_code'],{});actual=(pr.get('3連単_組番') or '').strip();payout=int(float(pr.get('3連単_払戻金') or 0));inv,ret,hit=settle(b,actual,payout)
            sens.append({**{k:v for k,v in b.items() if k!='alloc'},'actual_combo':actual,'invest':inv,'return':ret,'ticket_hit':hit})
        # Update head probabilities only after the full day has been frozen/settled.
        for z in byday[d]:
            if z['head'] not in HEADS:continue
            rr=res.get(z['race_code'],{});win=int(float(rr.get('1着_艇番') or 0));head_samples[z['head']].append((z['score'],int(win==z['head'])))

    write_csv('analysis_v61_trifecta_set_ev.csv',ledger);write_csv('analysis_v61_sensitivity.csv',sens)

    def stat(rs):
        inv=sum(r['invest'] for r in rs);ret=sum(r['return'] for r in rs);n=len(rs);hit=sum(r['ticket_hit'] for r in rs);avg=sum(r['tickets_n'] for r in rs)/n if n else 0
        return n,hit,avg,inv,ret,(100*ret/inv if inv else 0)

    L=['# v61 3連単 相手確率 × 合成オッズ 長期バックテスト','',
       f'OOS: **{OOS0}〜{OOS1}**。頭確率は日々ウォークフォワード、相手条件付き確率の温度は7/18以前だけで校正。',
       '各レースで20通りを `相手条件付き確率×締切前オッズ` 順に並べ、1〜20点の各prefixについて `セット確率=頭確率×相手累積確率`、`合成オッズ=1/Σ(1/各オッズ)`、`セットEV=セット確率×合成オッズ` を計算。',
       f'固定baseline: **相手確率カバー率>={BASE_COVER*100:.0f}%、セットEV>={BASE_EV:.2f}、条件を満たす中でEV最大の点数**。1R総投資{RACE_STAKE:,}円を選択買い目へダッチ配分。結果は選択・配分固定後に読む。','','## 相手確率softmax温度','|頭|温度|','|---:|---:|']
    for h in HEADS:L.append(f'|{h}|{temps[h]:.2f}|')
    L+=['','## baseline 長期OOS','|頭|購入R|3連単的中|平均点数|投資|払戻|ROI|','|---:|---:|---:|---:|---:|---:|---:|']
    for h in HEADS:
        n,hit,avg,inv,ret,roi=stat([r for r in ledger if r['head']==h]);L.append(f'|{h}|{n}|{hit}|{avg:.2f}|{inv:,}円|{ret:,}円|{roi:.1f}%|')
    n,hit,avg,inv,ret,roi=stat(ledger);L.append(f'|合計|{n}|{hit}|{avg:.2f}|{inv:,}円|{ret:,}円|{roi:.1f}%|')

    L+=['','## baseline 前半/後半','|頭|期間|購入R|的中|平均点|ROI|','|---:|---|---:|---:|---:|---:|']
    for h in HEADS:
        for name,lo,hi in [('前半',OOS0,'2026-08-10'),('後半','2026-08-11',OOS1)]:
            q=[r for r in ledger if r['head']==h and lo<=r['date']<=hi];n,hit,avg,inv,ret,roi=stat(q);L.append(f'|{h}|{name}|{n}|{hit}|{avg:.2f}|{roi:.1f}%|')

    L+=['','## カバー率×EV閾値 感度','|頭|カバー率|EV閾値|購入R|的中|平均点|ROI|','|---:|---:|---:|---:|---:|---:|---:|']
    for h in HEADS:
        for cv in COVERS:
            for evm in EVS:
                q=[r for r in sens if r['head']==h and abs(r['cover_rule']-cv)<1e-9 and abs(r['ev_rule']-evm)<1e-9];n,hit,avg,inv,ret,roi=stat(q);L.append(f'|{h}|{cv*100:.0f}%|{evm:.2f}|{n}|{hit}|{avg:.2f}|{roi:.1f}%|')
    L+=['','## 注意','- 相手確率はモデルのみ。オッズは価格とセット合成オッズにだけ使用。','- 感度表で最良のセルを後付け採用しない。baselineの前半/後半再現性を優先する。','- 2,000円をダッチ配分するため、選択点数が20点の場合は各100円。点数が少ないほど高確率/低オッズ側へ追加配分される。']
    open('summary_v61_trifecta_set_ev_long.md','w',encoding='utf-8').write('\n'.join(L)+'\n')

if __name__=='__main__':main()
