"""v57: current head-first model + pre-race trifecta odds EV + variable tickets/stakes.

No-leak protocol
- Candidate/direct features are frozen for the entire date range before outcomes are read.
- Model calibration: 2026-06-01..2026-07-18 only.
- Odds validation: 2026-07-19..2026-08-02 only. This period chooses market-blend and EV threshold.
- Test: 2026-08-03..2026-09-02 untouched until all rules above are fixed.
- od3 is pre-close odds (取得日時 before 締切時刻); payouts/results are read only after EV tickets are frozen.
- Actual entry/course and STT entry/course columns are never used.
"""
import csv, math
from collections import defaultdict
from datetime import date

from backtest import rows, race_features
from analyze_v23_20260902_daypreview import by_code, venue_map
from backtest_v51_lane_corrected_tickets import ff, ii, tilt_band, learn_st_frame_bias, corrected_direct
from backtest_v52_scenario_tickets import TILT_BONUS, preview_comp, base_place, structure_bonus
from backtest_v53_pair_and_0902_flow import learn_fit_priors, tune_pair_weights

D0='2026-06-01'; CAL1='2026-07-18'; VAL0='2026-07-19'; VAL1='2026-08-02'; TEST0='2026-08-03'; TEST1='2026-09-02'
MODELS=['3まくり','3まくり差し','5頭展開']
HEAD={'3まくり':3,'3まくり差し':3,'5頭展開':5}
MAIN_HEADS=[3,5]
TEMP_GRID=[0.06,0.10,0.15,0.22,0.32,0.50]
BLEND_GRID=[0.0,0.25,0.50,0.75]
EV_GRID=[1.05,1.10,1.15,1.20,1.30,1.40]
INITIAL_BANK=100000
KELLY_FRACTION=.25
MAX_RACE_FRAC=.03
MAX_TICKET_FRAC=.01
UNIT=100


def period(d):
    if d<=CAL1:return 'calibration'
    if d<=VAL1:return 'validation'
    return 'test'


def combos_for_head(h):
    return [f'{h}-{a}-{b}' for a in range(1,7) if a!=h for b in range(1,7) if b not in (h,a)]


def load_source():
    with open('analysis_v46_history_softscore.csv',encoding='utf-8-sig') as f:
        return [{k:v for k,v in r.items() if k!='target'} for r in csv.DictReader(f)
                if r.get('model') in MODELS and D0<=r.get('date','')<=TEST1]


def pair_scores(m,x,ex,st,os,pri,wp):
    h=HEAD[m];out={}
    for a in range(1,7):
        if a==h:continue
        for b in range(1,7):
            if b in (h,a):continue
            s=(.36*base_place(x,a,ex,st,os)+.25*base_place(x,b,ex,st,os)
               +.14*pri[m]['sec'].get(a,.5)+.10*pri[m]['third'].get(b,.5)
               +wp*pri[m]['pair'].get((a,b),.5)
               +.55*structure_bonus(m,'sec',a)+.35*structure_bonus(m,'third',b))
            out[f'{h}-{a}-{b}']=s
    return out


def softmax(scores,temp):
    if not scores:return {}
    mx=max(scores.values());vals={k:math.exp((v-mx)/max(temp,1e-6)) for k,v in scores.items()};z=sum(vals.values())
    return {k:v/z for k,v in vals.items()}


def market_q(od,h):
    vals={}
    for c in combos_for_head(h):
        o=ff(od.get('3連単_'+c),0) or 0
        if o>0:vals[c]=1/o
    z=sum(vals.values())
    return {c:v/z for c,v in vals.items()} if z else {}


def local_prob(samples,score):
    if not samples:return .10
    base=sum(y for _,y in samples)/len(samples);rad=8.0;sw=sy=0.0
    for s,y in samples:
        d=abs(s-score)
        if d<=rad:
            w=max(.05,1-d/rad);sw+=w;sy+=w*y
    prior=24.0
    p=(sy+prior*base)/(sw+prior)
    return min(.80,max(.02,p))


def freeze_all():
    stbias=learn_st_frame_bias();pri,_=learn_fit_priors();chosen,_=tune_pair_weights(pri,stbias);vidx=venue_map()
    src=load_source();cache={};groups=defaultdict(list)
    for r in src:
        d=r['date'];ymd=d.replace('-','/');code=r['race_code'];m=r['model'];h=HEAD[m];venue=code[8:10]
        if d not in cache:
            cache[d]=(by_code(f'data/previews/tkz/{ymd}.csv'),by_code(f'data/previews/stt/{ymd}.csv'),
                      by_code(f'data/previews/original_exhibition/{ymd}.csv'),by_code(f'data/programs/race_cards/{ymd}.csv'),
                      by_code(f'data/programs/waku10/{ymd}.csv'))
        tkz,stt,orig,cards,w10=cache[d];card=cards.get(code,{})
        if not card:continue
        ex,st,os=corrected_direct(code,tkz,stt,orig,stbias);x=race_features(card,w10.get(code,{}));tr=tkz.get(code,{})
        hist=ff(r.get('history_adjust'),0) or 0;tilt=ff(tr.get(f'艇{h}_チルト'),0) or 0
        sc=100*preview_comp(m,venue,ex,st,os,vidx)+hist+TILT_BONUS[m][tilt_band(tilt)]
        wp=chosen.get(m,0.0) if m in ('3まくり','5頭展開') else 0.0
        ps=pair_scores(m,x,ex,st,os,pri,wp)
        groups[(d,code,h)].append({'date':d,'race_code':code,'model':m,'head':h,'score':sc,'history_adjust':hist,
                                  'pair_weight':wp,'pair_scores':ps,'period':period(d)})
    out=[]
    for _,arr in groups.items():out.append(max(arr,key=lambda z:z['score']))
    return out


def label_outcomes(frozen):
    byday=defaultdict(list)
    for z in frozen:byday[z['date']].append(z)
    out=[]
    for d,arr in sorted(byday.items()):
        ymd=d.replace('-','/');res={r['レースコード']:r for r in rows(f'data/results/realtime/{ymd}.csv')};pay={r['レースコード']:r for r in rows(f'data/results/payouts/{ymd}.csv')}
        for z in arr:
            rr=res.get(z['race_code'],{});pr=pay.get(z['race_code'],{});q=dict(z)
            q['winner']=ii(rr.get('1着_艇番'));q['head_hit']=int(q['winner']==q['head']);q['actual_combo']=(pr.get('3連単_組番') or '').strip();q['payout100']=ii(pr.get('3連単_払戻金'))
            out.append(q)
    return out


def choose_temp(rows0,head):
    rs=[z for z in rows0 if z['period']=='calibration' and z['head']==head and z['head_hit'] and z['actual_combo']]
    best=None;table=[]
    for t in TEMP_GRID:
        ll=0;n=0
        for z in rs:
            q=softmax(z['pair_scores'],t);p=q.get(z['actual_combo'],1e-9);ll-=math.log(max(p,1e-9));n+=1
        avg=ll/n if n else 999;table.append((t,n,avg))
        if best is None or avg<best[0]:best=(avg,t)
    return best[1] if best else .22,table


def load_odds(d):
    ymd=d.replace('-','/');return {r['レースコード']:r for r in rows(f'data/previews/od3/{ymd}.csv')}


def choose_blend(rows0,head,temp):
    rs=[z for z in rows0 if z['period']=='validation' and z['head']==head and z['head_hit'] and z['actual_combo']]
    cache={};best=None;table=[]
    for w in BLEND_GRID:
        ll=0;n=0
        for z in rs:
            if z['date'] not in cache:cache[z['date']]=load_odds(z['date'])
            od=cache[z['date']].get(z['race_code'],{});qm=market_q(od,head);qp=softmax(z['pair_scores'],temp)
            if not qm:continue
            c=z['actual_combo'];p=(1-w)*qp.get(c,0)+w*qm.get(c,0);ll-=math.log(max(p,1e-9));n+=1
        avg=ll/n if n else 999;table.append((w,n,avg))
        if best is None or avg<best[0]:best=(avg,w)
    return best[1] if best else .25,table


def prepare_ev_rows(rows0,head,temp,blend):
    train=[(z['score'],z['head_hit']) for z in rows0 if z['period']=='calibration' and z['head']==head]
    cache={};out=[]
    for z in rows0:
        if z['head']!=head or z['period']=='calibration':continue
        if z['date'] not in cache:cache[z['date']]=load_odds(z['date'])
        od=cache[z['date']].get(z['race_code'],{})
        if not od:continue
        ph=local_prob(train,z['score']);qp=softmax(z['pair_scores'],temp);qm=market_q(od,head)
        if not qm:continue
        for c in combos_for_head(head):
            o=ff(od.get('3連単_'+c),0) or 0
            if o<=0:continue
            q=(1-blend)*qp.get(c,0)+blend*qm.get(c,0);pc=ph*q;ev=pc*o
            out.append({'date':z['date'],'period':z['period'],'race_code':z['race_code'],'model':z['model'],'head':head,'score':z['score'],
                        'band':'A' if z['score']>=55 else ('preA' if z['score']>=50 else 'low'),'combo':c,'odds_pre':o,
                        'head_prob':ph,'conditional_prob':q,'combo_prob':pc,'ev':ev,'actual_combo':z['actual_combo'],'payout100':z['payout100']})
    return out


def equal_stat(bs):
    st=len(bs)*100;ret=sum(b['payout100'] for b in bs if b['combo']==b['actual_combo']);hits=sum(1 for b in bs if b['combo']==b['actual_combo'])
    return len(set(b['race_code'] for b in bs)),len(bs),hits,st,ret,(100*ret/st if st else 0)


def choose_ev_threshold(evrows,head):
    table=[];best=None
    for th in EV_GRID:
        bs=[b for b in evrows if b['period']=='validation' and b['band']=='A' and b['ev']>=th]
        rc,n,h,st,ret,roi=equal_stat(bs);table.append((th,rc,n,h,roi))
        # require enough tickets; then prefer ROI, profit, and lower threshold on ties
        if n>=20:
            key=(roi,ret-st,-th)
            if best is None or key>best[0]:best=(key,th)
    return best[1] if best else 1.15,table


def kelly_allocate(bs,bank):
    if not bs:return [],bank
    cap=max(UNIT,int(bank*MAX_RACE_FRAC)//UNIT*UNIT);targets=[]
    for b in bs:
        p=b['combo_prob'];o=b['odds_pre'];k=max(0.0,(p*o-1)/(o-1)) if o>1 else 0
        raw=min(bank*MAX_TICKET_FRAC,bank*KELLY_FRACTION*k);stake=max(UNIT,int(raw)//UNIT*UNIT)
        targets.append([b,stake,k])
    if len(targets)*UNIT>cap:
        targets=sorted(targets,key=lambda x:x[0]['ev'],reverse=True)[:cap//UNIT]
    total=sum(x[1] for x in targets)
    if total>cap and total>0:
        scale=cap/total
        for x in targets:x[1]=max(UNIT,int(x[1]*scale)//UNIT*UNIT)
        while sum(x[1] for x in targets)>cap:
            j=max(range(len(targets)),key=lambda i:targets[i][1])
            if targets[j][1]<=UNIT:break
            targets[j][1]-=UNIT
    return targets,bank


def bankroll_run(bs):
    bank=INITIAL_BANK;peak=bank;maxdd=0;ledger=[]
    by=defaultdict(list)
    for b in bs:by[(b['date'],b['race_code'])].append(b)
    for key in sorted(by):
        alloc,_=kelly_allocate(by[key],bank);invest=sum(x[1] for x in alloc);ret=0
        for b,stake,k in alloc:
            hit=b['combo']==b['actual_combo'];r=b['payout100']*(stake//100) if hit else 0;ret+=r
            z=dict(b);z.update({'stake_kelly':stake,'kelly_raw':k,'hit':int(hit),'return_kelly':r});ledger.append(z)
        bank+=ret-invest;peak=max(peak,bank);maxdd=max(maxdd,(peak-bank)/peak if peak else 0)
    return ledger,bank,maxdd


def write_csv(path,rs):
    if not rs:return
    clean=[]
    for r in rs:clean.append({k:v for k,v in r.items() if k!='pair_scores'})
    fs=sorted(set().union(*(r.keys() for r in clean)))
    with open(path,'w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=fs);w.writeheader();w.writerows(clean)


def main():
    frozen=freeze_all();lab=label_outcomes(frozen)
    temps={};blends={};thresholds={};evall=[];tinfo={};binfo={};einfo={}
    for h in MAIN_HEADS:
        temps[h],tinfo[h]=choose_temp(lab,h);blends[h],binfo[h]=choose_blend(lab,h,temps[h]);er=prepare_ev_rows(lab,h,temps[h],blends[h]);evall+=er
        thresholds[h],einfo[h]=choose_ev_threshold(er,h)
    # live/test A tickets only; number of tickets is determined solely by EV threshold.
    live=[b for b in evall if b['period']=='test' and b['band']=='A' and b['ev']>=thresholds[b['head']]]
    kledger,final_bank,maxdd=bankroll_run(live)
    write_csv('analysis_v57_ev_candidates.csv',evall);write_csv('bets_v57_ev_kelly.csv',kledger)

    L=['# v57 オッズ期待値・可変点数・資金配分バックテスト','',
       '締切前od3を使い、各3連単のモデル確率×オッズでEVを算出。点数は固定せず、EV閾値を超えた買い目だけ購入。',
       '相手確率はモデル相手scoreのsoftmaxと市場の頭内構成比を混合。softmax温度は6/1-7/18、混合率とEV閾値は7/19-8/2だけで決定。8/3-9/2は完全固定。',
       '資金配分は1/4 Kelly、初期10万円、1買い目最大1%、1レース最大3%、100円単位。','','## 固定されたパラメータ','|頭|softmax温度|市場blend|EV閾値|','|---:|---:|---:|---:|']
    for h in MAIN_HEADS:L.append(f'|{h}|{temps[h]:.2f}|{blends[h]:.2f}|{thresholds[h]:.2f}|')
    L+=['','## EV閾値 validation','|頭|閾値|レース|点数|的中|ROI|','|---:|---:|---:|---:|---:|---:|']
    for h in MAIN_HEADS:
        for th,rc,n,hit,roi in einfo[h]:L.append(f'|{h}|{th:.2f}|{rc}|{n}|{hit}|{roi:.1f}%|')
    L+=['','## Test 8/3-9/2 可変点数（均等100円）','|頭|レース|点数|平均点/レース|的中|投資|払戻|ROI|','|---:|---:|---:|---:|---:|---:|---:|---:|']
    for h in MAIN_HEADS:
        bs=[b for b in live if b['head']==h];rc,n,hit,st,ret,roi=equal_stat(bs);L.append(f'|{h}|{rc}|{n}|{n/rc if rc else 0:.2f}|{hit}|{st:,}円|{ret:,}円|{roi:.1f}%|')
    rc,n,hit,st,ret,roi=equal_stat(live);L.append(f'|合計|{rc}|{n}|{n/rc if rc else 0:.2f}|{hit}|{st:,}円|{ret:,}円|{roi:.1f}%|')
    kinv=sum(x['stake_kelly'] for x in kledger);kret=sum(x['return_kelly'] for x in kledger);kh=sum(x['hit'] for x in kledger)
    L+=['','## Test 1/4 Kelly資金配分',f'- 初期資金: {INITIAL_BANK:,}円',f'- 最終資金: **{final_bank:,}円**',f'- 投資累計: {kinv:,}円',f'- 払戻累計: {kret:,}円',f'- 購入買い目: {len(kledger)}点 / 的中 {kh}点',f'- 資金配分ROI: **{100*kret/kinv if kinv else 0:.1f}%**',f'- 最大ドローダウン: **{100*maxdd:.1f}%**']
    L+=['','## 準A(score 50-55) 独立確認','|頭|期間|レース|点数|的中|ROI|','|---:|---|---:|---:|---:|---:|']
    for h in MAIN_HEADS:
        for per in ['validation','test']:
            bs=[b for b in evall if b['head']==h and b['period']==per and b['band']=='preA' and b['ev']>=thresholds[h]];rc,n,hit,st,ret,roi=equal_stat(bs);L.append(f'|{h}|{per}|{rc}|{n}|{hit}|{roi:.1f}%|')
    L+=['','## 2026-08-20 当日EV選定','|レース|頭|score|点数|EV範囲|結果|','|---|---:|---:|---:|---|---|']
    day=[b for b in live if b['date']=='2026-08-20'];by=defaultdict(list)
    for b in day:by[(b['race_code'],b['head'])].append(b)
    for (code,h),bs in sorted(by.items()):
        evs=[b['ev'] for b in bs];actual=bs[0]['actual_combo'];L.append(f'|{code}|{h}|{bs[0]["score"]:.1f}|{len(bs)}|{min(evs):.2f}〜{max(evs):.2f}|{actual}|')
    L+=['','## 注意','- od3アーカイブは2026-07-19開始のため、それ以前はオッズEV検証不可。','- 確率校正は頭的中と相手softmaxを結果期間より前で行う。払戻額はEV閾値validationと最終ROI評価以外には使わない。','- 1か月程度のテストなので、Kelly配分は利益額より最大DDと再現性を重視して判断する。']
    open('summary_v57_ev_variable_staking.md','w',encoding='utf-8').write('\n'.join(L)+'\n')

if __name__=='__main__':main()
