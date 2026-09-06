from __future__ import annotations
import csv
from backtest import rows,race_features
import backtest_v51_lane_corrected_tickets as v51
import analyze_v110_1head_role_tickets as v110

YMD='2026/09/05'
TRAIN_END='2026-08-31'
SRC='analysis_v146_20260905_operational_replay.csv'
ONE_LIVE='prediction_v116_20260905_1head_live.csv'
OUT='analysis_v147_20260905_operational_ticket_roi.csv'
SUMMARY='summary_v147_20260905_operational_ticket_roi.md'


def read(path):
    with open(path,encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def ii(x,d=0):
    try:return int(float(x))
    except:return d

def current_pair_order(head,ranked):
    pos={b:i+1 for i,b in enumerate(ranked)};a=[]
    for s in ranked:
        for t in ranked:
            if s==t:continue
            a.append((pos[s]+.7*pos[t],pos[s],pos[t],f'{head}-{s}-{t}'))
    a.sort();return [z[3] for z in a]

def synth_v110(x,venue,ex,st,os):
    scores={b:v51.opp_place_score(x,b,ex,st,os) for b in range(1,7)}
    ranked=sorted(range(2,7),key=lambda b:scores[b],reverse=True)
    r={'venue':venue,'one_score':scores[1],'ranked_others':'-'.join(map(str,ranked))}
    for b in range(2,7):r[f'threat{b}']=scores[b]
    return r,ranked

def main():
    pred=read(SRC)
    one_live={r.get('race_code',''):r for r in read(ONE_LIVE)}
    cards={r.get('レースコード',''):r for r in rows(f'data/programs/race_cards/{YMD}.csv')}
    waku={r.get('レースコード',''):r for r in rows(f'data/programs/waku10/{YMD}.csv')}
    tkz=v51.by_code(f'data/previews/tkz/{YMD}.csv');stt=v51.by_code(f'data/previews/stt/{YMD}.csv');orig=v51.by_code(f'data/previews/original_exhibition/{YMD}.csv')
    stbias=v51.learn_st_frame_bias()
    tr=[r for r in v110.read_csv(v110.SRC) if r.get('date','')<=TRAIN_END]
    m2,m3,_=v110.fit_roles(tr)
    frozen=[]
    for z in pred:
        code=z.get('race_code','');branch=z.get('final','')
        if branch in ('NO_DIRECT','その他',''):continue
        head={'1逃げ':1,'3まくり':3,'3まくり差し':3,'4カド':4,'5頭':5}.get(branch,0)
        if not head:continue
        c=cards.get(code);w=waku.get(code,{})
        if not c or code not in tkz or code not in stt or code not in orig:continue
        # Current production 1-head is S-only.
        p109='';g109=''
        if head==1:
            lr=one_live.get(code,{})
            p109=lr.get('p109_live','');g109=lr.get('grade_live','')
            if g109!='S':
                frozen.append({'race_code':code,'branch':branch,'head':head,'buy':'SKIP','reason':'1head_not_v109_S','p109':p109,'grade109':g109})
                continue
        ex,st,os=v51.corrected_direct(code,tkz,stt,orig,stbias)
        x=race_features(c,w);venue=str(c.get('レース場コード','')).zfill(2)
        syn,ranked=synth_v110(x,venue,ex,st,os)
        if head==1:
            tickets=v110.pair_order(syn,m2,m3,.50)[:7];logic='v110_top7'
        elif head in (3,5):
            ranked2=sorted([b for b in range(1,7) if b!=head],key=lambda b:v51.opp_place_score(x,b,ex,st,os),reverse=True)
            tickets=v51.tickets_for(head,ranked2,6);logic='current_v51_6'
        else:
            ranked2=sorted([b for b in range(1,7) if b!=4],key=lambda b:v51.opp_place_score(x,b,ex,st,os),reverse=True)
            tickets=current_pair_order(4,ranked2)[:7];logic='current4_rank_7'
        frozen.append({'race_code':code,'branch':branch,'head':head,'buy':'BUY','reason':'','p109':p109,'grade109':g109,'logic':logic,'points':len(tickets),'tickets':';'.join(tickets)})

    # settlement only after all ticket lists are frozen
    pay={r.get('レースコード',''):r for r in rows(f'data/results/payouts/{YMD}.csv')}
    for z in frozen:
        if z.get('buy')!='BUY':continue
        pr=pay.get(z['race_code'],{});combo=(pr.get('3連単_組番') or '').strip();payout=ii(pr.get('3連単_払戻金'))
        ts=z['tickets'].split(';') if z.get('tickets') else []
        hit=int(combo in ts);z['actual_combo']=combo;z['payout100']=payout;z['hit']=hit;z['invest']=len(ts)*100;z['return']=payout if hit else 0
    fs=['race_code','branch','head','buy','reason','p109','grade109','logic','points','tickets','actual_combo','payout100','hit','invest','return']
    with open(OUT,'w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fs);w.writeheader();w.writerows([{k:r.get(k,'') for k in fs} for r in frozen])
    q=[r for r in frozen if r.get('buy')=='BUY' and r.get('actual_combo')]
    h=sum(ii(r.get('hit')) for r in q);inv=sum(ii(r.get('invest')) for r in q);ret=sum(ii(r.get('return')) for r in q)
    L=['# v147 2026-09-05 実運用型 買い目・ROIリプレイ','',
       '- v146でPRE→直前v145 FINALを先に固定。','- ①逃げ分岐は現行運用どおりv109 SのみBUYし、v110上位7点。','- ③頭/⑤頭はCURRENT v51 6点。④頭はCURRENT相手順位7点。v100/v106はshadowなので使わない。','- 全買い目を凍結した後だけ9/5 payoutsを読み込んでsettlement。','',
       f'- BUY: **{len(q)}R** / 的中: **{h}R** / 3連単的中率: **{100*h/len(q) if q else 0:.1f}%**',
       f'- 投資: **{inv:,}円** / 払戻: **{ret:,}円** / ROI: **{100*ret/inv if inv else 0:.1f}%**','',
       '## レース別','|race_code|分岐|判定|logic|点数|結果|的中|投資|払戻|','|---|---|---|---|---:|---|---:|---:|---:|']
    for r in frozen:
        if r.get('buy')!='BUY':L.append(f"|{r['race_code']}|{r['branch']}|SKIP ({r.get('reason','')})|-|-|-|-|-|-|")
        else:L.append(f"|{r['race_code']}|{r['branch']}|BUY|{r['logic']}|{r['points']}|{r.get('actual_combo','')}|{r.get('hit','')}|{r.get('invest',0)}|{r.get('return',0)}|")
    L+=['','※9/5単日なので、採用判断はv148の8月branch-ticket holdoutと併せて行う。']
    open(SUMMARY,'w',encoding='utf-8').write('\n'.join(L)+'\n')

if __name__=='__main__':main()
