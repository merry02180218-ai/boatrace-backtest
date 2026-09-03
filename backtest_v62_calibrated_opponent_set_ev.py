"""v62: empirically calibrated opponent probabilities + trifecta set EV.

Goal
- Fix v61 softmax overconfidence, especially 5-head.
- Conditional opponent probability is NOT the raw softmax.
- Using only races <= 2026-07-18 where the target head actually won:
  1) calibrate model pair-score rank -> empirical actual-combo frequency,
  2) calibrate empirical 2nd-boat and 3rd-boat frequencies,
  3) blend rank-calibrated and role-calibrated joint distributions 50:50.
- Laplace/Dirichlet smoothing is applied so tiny samples cannot create extreme probabilities.

OOS / no-leak
- Calibration outcomes: <= 2026-07-18 only.
- OOS odds/results: 2026-07-19..2026-09-02.
- Head probability is walk-forward; each OOS day's result is added only after that day's
  selections/stakes are frozen.
- od3 is used before result/payout load. Actual entry/course and STT course fields are not used.

Set EV
- Rank 20 head-fixed trifectas by calibrated_conditional_probability * pre-close odds.
- For every prefix 1..20:
    set_prob = P(head) * cumulative calibrated conditional probability
    synthetic_odds = 1 / sum(1/odds_i)
    set_EV = set_prob * synthetic_odds
- Fixed baseline retained from v61 for fair comparison:
    coverage >= 50%, set_EV >= 1.20, choose maximum-EV prefix.
"""
import csv, math
from collections import defaultdict
from backtest import rows
from backtest_v57_ev_variable_staking import freeze_all, load_odds, local_prob, combos_for_head

CAL1='2026-07-18'; OOS0='2026-07-19'; OOS1='2026-09-02'
HEADS=[3,5]
BASE_COVER=.50; BASE_EV=1.20
COVERS=[.30,.40,.50,.60,.70]
EVS=[1.10,1.20,1.30,1.40]
UNIT=100; FLAT_STAKE=2000
BANK0=100000; KELLY_FRAC=.125; MAX_RACE_FRAC=.03
RANK_ALPHA=1.0     # uniform prior: 20 pseudo observations total
ROLE_ALPHA=2.0     # 2 pseudo observations per eligible boat in each role
BLEND=.50          # fixed before OOS: rank calibration / role calibration


def parse_combo(c):
    try:return tuple(int(x) for x in c.split('-'))
    except:return ()


def rank_combos(pair_scores, head):
    cs=combos_for_head(head)
    return sorted(cs,key=lambda c:(pair_scores.get(c,-1e9),c),reverse=True)


def build_calibration(labeled):
    """Build conditional P(combo | head wins) calibrators from <=CAL1 only."""
    out={}
    for h in HEADS:
        hrs=[z for z in labeled if z['head']==h and z['head_hit'] and z['actual_combo']]
        rank_cnt=defaultdict(int); sec_cnt=defaultdict(int); third_cnt=defaultdict(int)
        valid=0
        for z in hrs:
            ranked=rank_combos(z['pair_scores'],h)
            if z['actual_combo'] not in ranked:continue
            a=parse_combo(z['actual_combo'])
            if len(a)!=3 or a[0]!=h:continue
            rank_cnt[ranked.index(z['actual_combo'])+1]+=1
            sec_cnt[a[1]]+=1;third_cnt[a[2]]+=1;valid+=1
        # Rank distribution sums to 1 over 20 possible ranks.
        den_r=valid+20*RANK_ALPHA
        rank_p={r:(rank_cnt[r]+RANK_ALPHA)/den_r for r in range(1,21)} if den_r else {r:.05 for r in range(1,21)}
        boats=[b for b in range(1,7) if b!=h]
        den_s=valid+len(boats)*ROLE_ALPHA
        sec_p={b:(sec_cnt[b]+ROLE_ALPHA)/den_s for b in boats} if den_s else {b:.2 for b in boats}
        third_p={b:(third_cnt[b]+ROLE_ALPHA)/den_s for b in boats} if den_s else {b:.2 for b in boats}
        out[h]={'n':valid,'rank_p':rank_p,'sec_p':sec_p,'third_p':third_p,'rank_cnt':dict(rank_cnt),'sec_cnt':dict(sec_cnt),'third_cnt':dict(third_cnt)}
    return out


def calibrated_q(z, cal):
    h=z['head']; ranked=rank_combos(z['pair_scores'],h); cc=cal[h]
    qrank={c:cc['rank_p'][i+1] for i,c in enumerate(ranked)}
    role_raw={}
    for c in ranked:
        a=parse_combo(c);role_raw[c]=cc['sec_p'].get(a[1],.2)*cc['third_p'].get(a[2],.2)
    zr=sum(role_raw.values())
    qrole={c:(role_raw[c]/zr if zr else .05) for c in ranked}
    q={c:(1-BLEND)*qrank[c]+BLEND*qrole[c] for c in ranked}
    zq=sum(q.values())
    return {c:v/zq for c,v in q.items()} if zq else {c:.05 for c in ranked}


def syn_odds(items):
    inv=sum(1/x['odds'] for x in items if x['odds']>0)
    return 1/inv if inv>0 else 0


def dutch(items,total):
    n=len(items)
    if not items or total<n*UNIT:return {}
    base=n*UNIT;rem=total-base
    inv={x['combo']:1/x['odds'] for x in items};z=sum(inv.values())
    raw={c:(rem*inv[c]/z if z else 0) for c in inv};extra={c:int(raw[c]//UNIT)*UNIT for c in inv}
    left=rem-sum(extra.values());order=sorted(inv,key=lambda c:raw[c]-extra[c],reverse=True);j=0
    while left>=UNIT and order:
        extra[order[j%len(order)]]+=UNIT;left-=UNIT;j+=1
    return {c:UNIT+extra[c] for c in inv}


def choose_set(z,od,phead,q,mincov=BASE_COVER,minev=BASE_EV):
    cand=[]
    for c in combos_for_head(z['head']):
        try:o=float(od.get('3連単_'+c) or 0)
        except:o=0
        if o<=0:continue
        qc=q.get(c,0)
        cand.append({'combo':c,'odds':o,'cond_prob':qc,'cond_value':qc*o})
    if len(cand)!=20:return None
    cand.sort(key=lambda x:(x['cond_value'],x['cond_prob']),reverse=True)
    best=None;cum=0.0
    for k in range(1,21):
        cum+=cand[k-1]['cond_prob'];ss=cand[:k];so=syn_odds(ss);sp=phead*cum;ev=sp*so
        if cum+1e-12<mincov or ev+1e-12<minev:continue
        key=(ev,cum,-k)
        if best is None or key>best[0]:best=(key,{'tickets':ss,'n':k,'coverage':cum,'set_prob':sp,'synthetic_odds':so,'set_ev':ev})
    if not best:return None
    return best[1]


def settle(alloc,actual,payout100):
    inv=sum(alloc.values());stake=alloc.get(actual,0);ret=payout100*(stake//100) if stake else 0
    return inv,ret,int(stake>0)


def write_csv(path,rs):
    if not rs:return
    clean=[{k:v for k,v in r.items() if k not in ('pair_scores','tickets','alloc')} for r in rs]
    fs=sorted(set().union(*(r.keys() for r in clean)))
    with open(path,'w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=fs);w.writeheader();w.writerows(clean)


def stat(rs):
    n=len(rs);hit=sum(r['ticket_hit'] for r in rs);avg=sum(r['tickets_n'] for r in rs)/n if n else 0
    inv=sum(r['invest'] for r in rs);ret=sum(r['return'] for r in rs)
    return n,hit,avg,inv,ret,(100*ret/inv if inv else 0)


def main():
    frozen=freeze_all();byday=defaultdict(list)
    for z in frozen:byday[z['date']].append(z)

    # Calibration labels <= 7/18 only.
    labeled=[];head_samples={3:[],5:[]}
    for d in sorted(byday):
        if d>CAL1:break
        ymd=d.replace('-','/');res={r['レースコード']:r for r in rows(f'data/results/realtime/{ymd}.csv')};pay={r['レースコード']:r for r in rows(f'data/results/payouts/{ymd}.csv')}
        for z in byday[d]:
            if z['head'] not in HEADS:continue
            rr=res.get(z['race_code'],{});pr=pay.get(z['race_code'],{});win=int(float(rr.get('1着_艇番') or 0));q=dict(z)
            q['head_hit']=int(win==z['head']);q['actual_combo']=(pr.get('3連単_組番') or '').strip();labeled.append(q)
            head_samples[z['head']].append((z['score'],q['head_hit']))
    cal=build_calibration(labeled)

    ledger=[];sens=[];bank=BANK0;peak=bank;maxdd=0.0
    for d in sorted(byday):
        if d<OOS0 or d>OOS1:continue
        ods=load_odds(d);day_base=[];day_sens=[]
        # PRE-RESULT phase.
        for z in byday[d]:
            h=z['head']
            if h not in HEADS:continue
            od=ods.get(z['race_code'],{})
            if not od:continue
            ph=local_prob(head_samples[h],z['score']);cq=calibrated_q(z,cal)
            sel=choose_set(z,od,ph,cq,BASE_COVER,BASE_EV)
            if sel:
                flat=dutch(sel['tickets'],FLAT_STAKE)
                # Fractional Kelly on the SET, then dutch that total across selected combos.
                k=max(0,(sel['set_prob']*sel['synthetic_odds']-1)/(sel['synthetic_odds']-1)) if sel['synthetic_odds']>1 else 0
                ktot=int(min(bank*MAX_RACE_FRAC,bank*KELLY_FRAC*k)//UNIT)*UNIT
                kall=dutch(sel['tickets'],ktot) if ktot>=sel['n']*UNIT else {}
                day_base.append({'date':d,'race_code':z['race_code'],'model':z['model'],'head':h,'score':z['score'],'head_prob':ph,
                                 'tickets_n':sel['n'],'coverage':sel['coverage'],'set_prob':sel['set_prob'],'synthetic_odds':sel['synthetic_odds'],'set_ev':sel['set_ev'],
                                 'tickets':sel['tickets'],'flat_alloc':flat,'kelly_alloc':kall,'kelly_raw':k,'kelly_total':sum(kall.values()) if kall else 0})
            for cv in COVERS:
                for evm in EVS:
                    ss=choose_set(z,od,ph,cq,cv,evm)
                    if ss:
                        day_sens.append({'date':d,'race_code':z['race_code'],'head':h,'cover_rule':cv,'ev_rule':evm,'tickets_n':ss['n'],
                                         'coverage':ss['coverage'],'set_prob':ss['set_prob'],'synthetic_odds':ss['synthetic_odds'],'set_ev':ss['set_ev'],'alloc':dutch(ss['tickets'],FLAT_STAKE)})
        # ONLY NOW load outcomes/payouts.
        ymd=d.replace('-','/');res={r['レースコード']:r for r in rows(f'data/results/realtime/{ymd}.csv')};pay={r['レースコード']:r for r in rows(f'data/results/payouts/{ymd}.csv')}
        day_kin=day_kret=0
        for b in day_base:
            rr=res.get(b['race_code'],{});pr=pay.get(b['race_code'],{});actual=(pr.get('3連単_組番') or '').strip();payout=int(float(pr.get('3連単_払戻金') or 0));win=int(float(rr.get('1着_艇番') or 0))
            inv,ret,hit=settle(b['flat_alloc'],actual,payout);kin,kret,khit=settle(b['kelly_alloc'],actual,payout) if b['kelly_alloc'] else (0,0,0)
            q={k:v for k,v in b.items() if k not in ('tickets','flat_alloc','kelly_alloc')};q.update({'winner':win,'head_hit':int(win==b['head']),'actual_combo':actual,'payout100':payout,'invest':inv,'return':ret,'ticket_hit':hit,'kelly_invest':kin,'kelly_return':kret,'kelly_hit':khit});ledger.append(q)
            day_kin+=kin;day_kret+=kret
        bank+=day_kret-day_kin;peak=max(peak,bank);maxdd=max(maxdd,(peak-bank)/peak if peak else 0)
        for b in day_sens:
            pr=pay.get(b['race_code'],{});actual=(pr.get('3連単_組番') or '').strip();payout=int(float(pr.get('3連単_払戻金') or 0));inv,ret,hit=settle(b['alloc'],actual,payout)
            sens.append({**{k:v for k,v in b.items() if k!='alloc'},'actual_combo':actual,'invest':inv,'return':ret,'ticket_hit':hit})
        # Walk-forward head update after day is settled.
        for z in byday[d]:
            if z['head'] not in HEADS:continue
            rr=res.get(z['race_code'],{});win=int(float(rr.get('1着_艇番') or 0));head_samples[z['head']].append((z['score'],int(win==z['head'])))

    write_csv('analysis_v62_calibrated_set_ev.csv',ledger);write_csv('analysis_v62_sensitivity.csv',sens)

    L=['# v62 校正済み相手確率 × 3連単合成オッズ','',
       f'校正: **〜{CAL1}のみ**。OOS: **{OOS0}〜{OOS1}**。v61のraw softmax確率を廃止し、実測の「相手score順位別的中率」＋「2着/3着の実出現率」を50:50で混合。',
       f'固定baselineは比較のためv61と同じ: **相手カバー>={BASE_COVER*100:.0f}% / セットEV>={BASE_EV:.2f} / EV最大点数**。flatは1R {FLAT_STAKE:,}円ダッチ。','','## 校正サンプルと過信チェック','|頭|頭成立サンプル|rank1確率|rank上位3累積|rank上位5累積|最大2着率|最大3着率|','|---:|---:|---:|---:|---:|---:|---:|']
    for h in HEADS:
        c=cal[h];top1=c['rank_p'][1];top3=sum(c['rank_p'][r] for r in range(1,4));top5=sum(c['rank_p'][r] for r in range(1,6));ms=max(c['sec_p'].values());mt=max(c['third_p'].values())
        L.append(f'|{h}|{c["n"]}|{100*top1:.1f}%|{100*top3:.1f}%|{100*top5:.1f}%|{100*ms:.1f}%|{100*mt:.1f}%|')

    L+=['','## baseline 長期OOS','|頭|購入R|3連単的中|平均点数|投資|払戻|ROI|','|---:|---:|---:|---:|---:|---:|---:|']
    for h in HEADS:
        n,hit,avg,inv,ret,roi=stat([r for r in ledger if r['head']==h]);L.append(f'|{h}|{n}|{hit}|{avg:.2f}|{inv:,}円|{ret:,}円|{roi:.1f}%|')
    n,hit,avg,inv,ret,roi=stat(ledger);L.append(f'|合計|{n}|{hit}|{avg:.2f}|{inv:,}円|{ret:,}円|{roi:.1f}%|')

    L+=['','## baseline 前半/後半','|頭|期間|R|的中|平均点|ROI|','|---:|---|---:|---:|---:|---:|']
    for h in HEADS:
        for name,lo,hi in [('前半',OOS0,'2026-08-10'),('後半','2026-08-11',OOS1)]:
            q=[r for r in ledger if r['head']==h and lo<=r['date']<=hi];n,hit,avg,inv,ret,roi=stat(q);L.append(f'|{h}|{name}|{n}|{hit}|{avg:.2f}|{roi:.1f}%|')

    L+=['','## カバー率×EV感度（診断のみ）','|頭|カバー|EV|R|的中|平均点|ROI|','|---:|---:|---:|---:|---:|---:|---:|']
    for h in HEADS:
        for cv in COVERS:
            for evm in EVS:
                q=[r for r in sens if r['head']==h and abs(r['cover_rule']-cv)<1e-9 and abs(r['ev_rule']-evm)<1e-9];n,hit,avg,inv,ret,roi=stat(q);L.append(f'|{h}|{cv*100:.0f}%|{evm:.2f}|{n}|{hit}|{avg:.2f}|{roi:.1f}%|')

    kinv=sum(r['kelly_invest'] for r in ledger);kret=sum(r['kelly_return'] for r in ledger);kh=sum(r['kelly_hit'] for r in ledger)
    L+=['','## baseline 1/8 Kelly（セット単位）',f'- 初期資金: {BANK0:,}円 / 最終資金: **{bank:,}円**',f'- 投資 {kinv:,}円 / 払戻 {kret:,}円 / ROI **{100*kret/kinv if kinv else 0:.1f}%** / 的中 {kh}',f'- 最大DD **{100*maxdd:.1f}%**','',
        '## 判定','- baselineと前半/後半を優先する。感度表の最大ROIセルを後付け採用しない。','- v61より平均点数と5頭の確率集中が正常化しているかを最初に確認する。']
    open('summary_v62_calibrated_opponent_set_ev.md','w',encoding='utf-8').write('\n'.join(L)+'\n')

if __name__=='__main__':main()
