"""v63: fix v62's zero-sample 5-head calibration using ALL pre-OOS races.

3-head calibration remains v62 candidate-conditional calibration.
5-head calibration is rebuilt from every race <= 2026-07-18 where boat 5 actually won.
For those training races, current pre-race/direct features are reconstructed and the same v53/v57
5-head pair-score formula is used to obtain a rank. Results are used only to label the actual combo
inside the calibration period. OOS 2026-07-19..09-02 stays untouched until tickets/stakes freeze.
"""
import csv
from collections import defaultdict
from datetime import date,timedelta
from backtest import rows,race_features
from analyze_v23_20260902_daypreview import by_code
from backtest_v51_lane_corrected_tickets import learn_st_frame_bias, corrected_direct
from backtest_v53_pair_and_0902_flow import learn_fit_priors, tune_pair_weights
from backtest_v57_ev_variable_staking import freeze_all,load_odds,local_prob,combos_for_head,pair_scores
from backtest_v62_calibrated_opponent_set_ev import (
    CAL1,OOS0,OOS1,HEADS,BASE_COVER,BASE_EV,COVERS,EVS,UNIT,FLAT_STAKE,BANK0,KELLY_FRAC,MAX_RACE_FRAC,
    RANK_ALPHA,ROLE_ALPHA,BLEND,parse_combo,rank_combos,build_calibration,calibrated_q,choose_set,dutch,settle,write_csv,stat
)

TR0=date(2026,6,1);TR1=date(2026,7,18)


def allrace_5_calibration():
    stbias=learn_st_frame_bias();pri,_=learn_fit_priors();chosen,_=tune_pair_weights(pri,stbias);wp=chosen.get('5頭展開',0.0)
    rank_cnt=defaultdict(int);sec_cnt=defaultdict(int);third_cnt=defaultdict(int);valid=0
    d=TR0
    while d<=TR1:
        ymd=d.strftime('%Y/%m/%d')
        res={r['レースコード']:r for r in rows(f'data/results/realtime/{ymd}.csv')};pay={r['レースコード']:r for r in rows(f'data/results/payouts/{ymd}.csv')}
        cards=by_code(f'data/programs/race_cards/{ymd}.csv');w10=by_code(f'data/programs/waku10/{ymd}.csv')
        tkz=by_code(f'data/previews/tkz/{ymd}.csv');stt=by_code(f'data/previews/stt/{ymd}.csv');orig=by_code(f'data/previews/original_exhibition/{ymd}.csv')
        for code,rr in res.items():
            try:win=int(float(rr.get('1着_艇番') or 0))
            except:win=0
            if win!=5:continue
            actual=(pay.get(code,{}).get('3連単_組番') or '').strip();a=parse_combo(actual);card=cards.get(code,{})
            if len(a)!=3 or a[0]!=5 or not card:continue
            x=race_features(card,w10.get(code,{}));ex,st,os=corrected_direct(code,tkz,stt,orig,stbias)
            ps=pair_scores('5頭展開',x,ex,st,os,pri,wp);ranked=rank_combos(ps,5)
            if actual not in ranked:continue
            rank_cnt[ranked.index(actual)+1]+=1;sec_cnt[a[1]]+=1;third_cnt[a[2]]+=1;valid+=1
        d+=timedelta(days=1)
    den_r=valid+20*RANK_ALPHA;rank_p={r:(rank_cnt[r]+RANK_ALPHA)/den_r for r in range(1,21)}
    boats=[1,2,3,4,6];den=valid+5*ROLE_ALPHA
    sec_p={b:(sec_cnt[b]+ROLE_ALPHA)/den for b in boats};third_p={b:(third_cnt[b]+ROLE_ALPHA)/den for b in boats}
    return {'n':valid,'rank_p':rank_p,'sec_p':sec_p,'third_p':third_p,'rank_cnt':dict(rank_cnt),'sec_cnt':dict(sec_cnt),'third_cnt':dict(third_cnt)}


def main():
    frozen=freeze_all();byday=defaultdict(list)
    for z in frozen:byday[z['date']].append(z)
    labeled=[];head_samples={3:[],5:[]}
    for d in sorted(byday):
        if d>CAL1:break
        ymd=d.replace('-','/');res={r['レースコード']:r for r in rows(f'data/results/realtime/{ymd}.csv')};pay={r['レースコード']:r for r in rows(f'data/results/payouts/{ymd}.csv')}
        for z in byday[d]:
            if z['head'] not in HEADS:continue
            rr=res.get(z['race_code'],{});pr=pay.get(z['race_code'],{})
            try:win=int(float(rr.get('1着_艇番') or 0))
            except:win=0
            q=dict(z);q['head_hit']=int(win==z['head']);q['actual_combo']=(pr.get('3連単_組番') or '').strip();labeled.append(q);head_samples[z['head']].append((z['score'],q['head_hit']))
    cal=build_calibration(labeled);cal[5]=allrace_5_calibration()

    ledger=[];sens=[];bank=BANK0;peak=bank;maxdd=0
    for d in sorted(byday):
        if d<OOS0 or d>OOS1:continue
        ods=load_odds(d);base=[];ssens=[]
        for z in byday[d]:
            h=z['head']
            if h not in HEADS:continue
            od=ods.get(z['race_code'],{})
            if not od:continue
            ph=local_prob(head_samples[h],z['score']);cq=calibrated_q(z,cal);sel=choose_set(z,od,ph,cq,BASE_COVER,BASE_EV)
            if sel:
                flat=dutch(sel['tickets'],FLAT_STAKE);k=max(0,(sel['set_prob']*sel['synthetic_odds']-1)/(sel['synthetic_odds']-1)) if sel['synthetic_odds']>1 else 0
                ktot=int(min(bank*MAX_RACE_FRAC,bank*KELLY_FRAC*k)//UNIT)*UNIT;kall=dutch(sel['tickets'],ktot) if ktot>=sel['n']*UNIT else {}
                base.append({'date':d,'race_code':z['race_code'],'model':z['model'],'head':h,'score':z['score'],'head_prob':ph,'tickets_n':sel['n'],'coverage':sel['coverage'],'set_prob':sel['set_prob'],'synthetic_odds':sel['synthetic_odds'],'set_ev':sel['set_ev'],'tickets':sel['tickets'],'flat_alloc':flat,'kelly_alloc':kall})
            for cv in COVERS:
                for evm in EVS:
                    s=choose_set(z,od,ph,cq,cv,evm)
                    if s:ssens.append({'date':d,'race_code':z['race_code'],'head':h,'cover_rule':cv,'ev_rule':evm,'tickets_n':s['n'],'coverage':s['coverage'],'set_prob':s['set_prob'],'synthetic_odds':s['synthetic_odds'],'set_ev':s['set_ev'],'alloc':dutch(s['tickets'],FLAT_STAKE)})
        ymd=d.replace('-','/');res={r['レースコード']:r for r in rows(f'data/results/realtime/{ymd}.csv')};pay={r['レースコード']:r for r in rows(f'data/results/payouts/{ymd}.csv')}
        kin=kret=0
        for b in base:
            rr=res.get(b['race_code'],{});pr=pay.get(b['race_code'],{});actual=(pr.get('3連単_組番') or '').strip();payout=int(float(pr.get('3連単_払戻金') or 0));win=int(float(rr.get('1着_艇番') or 0))
            inv,ret,hit=settle(b['flat_alloc'],actual,payout);ki,kr,kh=settle(b['kelly_alloc'],actual,payout) if b['kelly_alloc'] else (0,0,0);kin+=ki;kret+=kr
            q={k:v for k,v in b.items() if k not in ('tickets','flat_alloc','kelly_alloc')};q.update({'winner':win,'head_hit':int(win==b['head']),'actual_combo':actual,'payout100':payout,'invest':inv,'return':ret,'ticket_hit':hit,'kelly_invest':ki,'kelly_return':kr,'kelly_hit':kh});ledger.append(q)
        bank+=kret-kin;peak=max(peak,bank);maxdd=max(maxdd,(peak-bank)/peak if peak else 0)
        for b in ssens:
            pr=pay.get(b['race_code'],{});actual=(pr.get('3連単_組番') or '').strip();payout=int(float(pr.get('3連単_払戻金') or 0));inv,ret,hit=settle(b['alloc'],actual,payout);sens.append({**{k:v for k,v in b.items() if k!='alloc'},'invest':inv,'return':ret,'ticket_hit':hit})
        for z in byday[d]:
            if z['head'] not in HEADS:continue
            rr=res.get(z['race_code'],{});win=int(float(rr.get('1着_艇番') or 0));head_samples[z['head']].append((z['score'],int(win==z['head'])))

    write_csv('analysis_v63_allrace5_set_ev.csv',ledger);write_csv('analysis_v63_sensitivity.csv',sens)
    L=['# v63 全レース5頭校正 × 3連単セットEV','',f'3頭はv62と同じ候補条件付き校正。5頭は **{TR0}〜{TR1} の全レースで5号艇1着**を使い、同じ事前/直前特徴から相手score順位を再計算して校正。OOSは{OOS0}〜{OOS1}。','',
       '## 校正サンプル','|頭|サンプル|rank1|上位3|上位5|最大2着|最大3着|','|---:|---:|---:|---:|---:|---:|---:|']
    for h in HEADS:
        c=cal[h];L.append(f'|{h}|{c["n"]}|{100*c["rank_p"][1]:.1f}%|{100*sum(c["rank_p"][r] for r in range(1,4)):.1f}%|{100*sum(c["rank_p"][r] for r in range(1,6)):.1f}%|{100*max(c["sec_p"].values()):.1f}%|{100*max(c["third_p"].values()):.1f}%|')
    L+=['','## baseline 50% / EV1.20','|頭|R|的中|平均点|ROI|','|---:|---:|---:|---:|---:|']
    for h in HEADS:
        n,hit,avg,inv,ret,roi=stat([r for r in ledger if r['head']==h]);L.append(f'|{h}|{n}|{hit}|{avg:.2f}|{roi:.1f}%|')
    L+=['','## baseline 前半/後半','|頭|期間|R|的中|平均点|ROI|','|---:|---|---:|---:|---:|---:|']
    for h in HEADS:
        for name,lo,hi in [('前半',OOS0,'2026-08-10'),('後半','2026-08-11',OOS1)]:
            n,hit,avg,inv,ret,roi=stat([r for r in ledger if r['head']==h and lo<=r['date']<=hi]);L.append(f'|{h}|{name}|{n}|{hit}|{avg:.2f}|{roi:.1f}%|')
    L+=['','## 感度（診断）','|頭|カバー|EV|R|的中|平均点|ROI|','|---:|---:|---:|---:|---:|---:|---:|']
    for h in HEADS:
        for cv in COVERS:
            for evm in EVS:
                q=[r for r in sens if r['head']==h and abs(r['cover_rule']-cv)<1e-9 and abs(r['ev_rule']-evm)<1e-9];n,hit,avg,inv,ret,roi=stat(q);L.append(f'|{h}|{cv*100:.0f}%|{evm:.2f}|{n}|{hit}|{avg:.2f}|{roi:.1f}%|')
    kinv=sum(r['kelly_invest'] for r in ledger);kret=sum(r['kelly_return'] for r in ledger)
    L+=['',f'Kelly: 初期{BANK0:,}円 → **{bank:,}円** / 投資{kinv:,}円 / 払戻{kret:,}円 / ROI {100*kret/kinv if kinv else 0:.1f}% / 最大DD {100*maxdd:.1f}%','',
        '## 判定ルール','baselineと前半/後半を最優先。感度の良いセルは後付け採用しない。']
    open('summary_v63_allrace5_calibrated_set_ev.md','w',encoding='utf-8').write('\n'.join(L)+'\n')

if __name__=='__main__':main()
