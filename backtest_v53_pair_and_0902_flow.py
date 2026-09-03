"""v53: pair-aware opponent model + 2026-09-02 full no-leak workflow replay.

Leakage boundaries:
- Pre-race candidate source: v46 rows with target/result field discarded.
- Pair/role priors: results 2026-06-01..2026-06-30 only.
- Pair weight tuning: results/payouts 2026-07-01..2026-07-15 only.
- Validation: 2026-07-16..2026-08-02. Test: 2026-08-03..2026-09-02.
- Current direct info is frame-corrected exhibition/original exhibition and training-only ST frame bias.
- STT entry/course fields and actual entry are never used.
- For the 2026-09-02 replay, three files are emitted in order: PRE(no direct/result), DIRECT(no result), SETTLED(result only after tickets frozen).
"""
import csv,re,math
from collections import defaultdict
from datetime import date,timedelta
from backtest import rows,race_features
from analyze_v23_20260902_daypreview import by_code,venue_map
from backtest_v51_lane_corrected_tickets import ff,ii,normkim,tilt_band,learn_st_frame_bias,corrected_direct
from backtest_v52_scenario_tickets import (
    MODELS,HEAD,POINTS,TILT_BONUS,route_match,parse_combo,preview_comp,
    base_place,structure_bonus,ranked_tickets as v52_ranked
)

FIT0=date(2026,6,1);FIT1=date(2026,6,30)
TUNE0=date(2026,7,1);TUNE1=date(2026,7,15)
VA0='2026-07-16';VA1='2026-08-02';TE0='2026-08-03';TE1='2026-09-02'
PAIR_MODELS={'3まくり','5頭展開'}
PAIR_WEIGHTS=[0.00,0.08,0.16,0.24,0.32,0.40]
VENUE={1:'桐生',2:'戸田',3:'江戸川',4:'平和島',5:'多摩川',6:'浜名湖',7:'蒲郡',8:'常滑',9:'津',10:'三国',11:'びわこ',12:'住之江',13:'尼崎',14:'鳴門',15:'丸亀',16:'児島',17:'宮島',18:'徳山',19:'下関',20:'若松',21:'芦屋',22:'福岡',23:'唐津',24:'大村'}

def dayrows(path):
    return rows(path)

def norm_counts(vals):
    if not vals:return {}
    lo=min(vals.values());hi=max(vals.values())
    if hi==lo:return {k:.5 for k in vals}
    return {k:(v-lo)/(hi-lo) for k,v in vals.items()}

def learn_fit_priors():
    cnt={m:{'sec':defaultdict(lambda:1.0),'third':defaultdict(lambda:1.0),'pair':defaultdict(lambda:1.0)} for m in MODELS}
    totals={m:0 for m in MODELS};d=FIT0
    while d<=FIT1:
        ymd=d.strftime('%Y/%m/%d')
        res={r['レースコード']:r for r in dayrows(f'data/results/realtime/{ymd}.csv')}
        pay={r['レースコード']:r for r in dayrows(f'data/results/payouts/{ymd}.csv')}
        for code,rr in res.items():
            win=ii(rr.get('1着_艇番'));kim=normkim(rr.get('決まり手'));a=parse_combo(pay.get(code,{}).get('3連単_組番',''))
            if len(a)<3:continue
            for m in MODELS:
                if route_match(m,win,kim):
                    cnt[m]['sec'][a[1]]+=1;cnt[m]['third'][a[2]]+=1;cnt[m]['pair'][(a[1],a[2])]+=1;totals[m]+=1
        d+=timedelta(days=1)
    out={}
    for m in MODELS:
        h=HEAD[m];out[m]={}
        out[m]['sec']=norm_counts({b:cnt[m]['sec'][b] for b in range(1,7) if b!=h})
        out[m]['third']=norm_counts({b:cnt[m]['third'][b] for b in range(1,7) if b!=h})
        pairs={(a,b):cnt[m]['pair'][(a,b)] for a in range(1,7) if a!=h for b in range(1,7) if b not in (h,a)}
        out[m]['pair']=norm_counts(pairs)
    return out,totals

def pair_ranked(m,x,ex,st,os,pri,wp):
    h=HEAD[m];cand=[]
    for a in range(1,7):
        if a==h:continue
        for b in range(1,7):
            if b in (h,a):continue
            # 2nd place gets slightly more current-form weight than 3rd.
            s=(.36*base_place(x,a,ex,st,os)+.25*base_place(x,b,ex,st,os)
               +.14*pri[m]['sec'].get(a,.5)+.10*pri[m]['third'].get(b,.5)
               +wp*pri[m]['pair'].get((a,b),.5)
               +.55*structure_bonus(m,'sec',a)+.35*structure_bonus(m,'third',b))
            cand.append((s,f'{h}-{a}-{b}'))
    cand.sort(reverse=True)
    return [c for _,c in cand]

def direct_for_day(d,stbias):
    ymd=d.strftime('%Y/%m/%d')
    return (by_code(f'data/previews/tkz/{ymd}.csv'),by_code(f'data/previews/stt/{ymd}.csv'),
            by_code(f'data/previews/original_exhibition/{ymd}.csv'),by_code(f'data/programs/race_cards/{ymd}.csv'),
            by_code(f'data/programs/waku10/{ymd}.csv'))

def tune_pair_weights(pri,stbias):
    # Tune opponent ranking only on races where the scenario actually occurred. This isolates 2nd/3rd ranking quality.
    scores={m:{w:{p:[0,0] for p in [4,6,8]} for w in PAIR_WEIGHTS} for m in PAIR_MODELS}
    d=TUNE0
    while d<=TUNE1:
        tkz,stt,orig,cards,w10=direct_for_day(d,stbias);ymd=d.strftime('%Y/%m/%d')
        res={r['レースコード']:r for r in dayrows(f'data/results/realtime/{ymd}.csv')}
        pay={r['レースコード']:r for r in dayrows(f'data/results/payouts/{ymd}.csv')}
        for code,rr in res.items():
            card=cards.get(code,{});pr=pay.get(code,{})
            if not card:continue
            combo=(pr.get('3連単_組番') or '').strip();payout=ii(pr.get('3連単_払戻金'));win=ii(rr.get('1着_艇番'));kim=normkim(rr.get('決まり手'))
            if not combo:continue
            x=race_features(card,w10.get(code,{}));ex,st,os=corrected_direct(code,tkz,stt,orig,stbias)
            for m in PAIR_MODELS:
                if not route_match(m,win,kim):continue
                for w in PAIR_WEIGHTS:
                    ranked=pair_ranked(m,x,ex,st,os,pri,w)
                    for p in [4,6,8]:
                        scores[m][w][p][0]+=p*100
                        if combo in ranked[:p]:scores[m][w][p][1]+=payout
        d+=timedelta(days=1)
    chosen={};detail={}
    for m in PAIR_MODELS:
        best=None
        for w in PAIR_WEIGHTS:
            rois=[]
            for p in [4,6,8]:
                inv,ret=scores[m][w][p];rois.append(100*ret/inv if inv else 0)
            avg=sum(rois)/len(rois)
            detail[(m,w)]=(rois,avg)
            # Smaller pair weight wins ties to avoid unnecessary complexity.
            key=(avg,-w)
            if best is None or key>best[0]:best=(key,w)
        chosen[m]=best[1]
    return chosen,detail

def load_source():
    with open('analysis_v46_history_softscore.csv',encoding='utf-8-sig') as f:
        return [{k:v for k,v in r.items() if k!='target'} for r in csv.DictReader(f)
                if r.get('model') in MODELS and VA0<=r.get('date','')<=TE1]

def pre_rows_0902(src):
    out=[]
    for r in src:
        if r['date']!='2026-09-02':continue
        code=r['race_code'];venue=int(code[8:10]);rn=int(code[10:12])
        out.append({'date':r['date'],'race_code':code,'venue':VENUE.get(venue,str(venue)),'race_no':rn,'model':r['model'],
                    'head_boat':HEAD[r['model']],'prior1':r.get('prior1',''),'prior2':r.get('prior2',''),
                    'history_pct':r.get('history_pct',''),'history_adjust':r.get('history_adjust','')})
    return out

def freeze(src,stbias,pri,chosen):
    vidx=venue_map();cache={};groups=defaultdict(list);frozen=[]
    for r in src:
        d=r['date'];ymd=d.replace('-','/');code=r['race_code'];m=r['model'];h=HEAD[m];venue=code[8:10]
        if d not in cache:
            cache[d]=(by_code(f'data/previews/tkz/{ymd}.csv'),by_code(f'data/previews/stt/{ymd}.csv'),
                      by_code(f'data/previews/original_exhibition/{ymd}.csv'),by_code(f'data/programs/race_cards/{ymd}.csv'),
                      by_code(f'data/programs/waku10/{ymd}.csv'))
        tkz,stt,orig,cards,w10=cache[d];card=cards.get(code,{})
        if not card:continue
        x=race_features(card,w10.get(code,{}));ex,st,os=corrected_direct(code,tkz,stt,orig,stbias)
        comp=preview_comp(m,venue,ex,st,os,vidx);tr=tkz.get(code,{})
        tilt=ff(tr.get(f'艇{h}_チルト'),0) or 0;hist=ff(r.get('history_adjust'),0) or 0
        score=100*comp+hist+TILT_BONUS[m][tilt_band(tilt)]
        if m in PAIR_MODELS:ranked=pair_ranked(m,x,ex,st,os,pri,chosen[m])
        else:ranked=v52_ranked(m,x,ex,st,os,{mm:{'sec':pri[mm]['sec'],'third':pri[mm]['third']} for mm in MODELS})
        z={'date':d,'period':'validation' if d<=VA1 else 'test','race_code':code,'model':m,'head_boat':h,
           'v53_score':score,'approved_A':int(score>=55),'approved_S':int(score>=67),'preview_comp':comp,
           'history_pct':ff(r.get('history_pct'),.5),'history_adjust':hist,'tilt':tilt,
           'ex_head':ex.get(h,.5),'st_head':st.get(h,.5),'orig_turn_head':os[h]['turn'],'orig_straight_head':os[h]['straight'],
           'pair_weight':chosen.get(m,''),'prior1':r.get('prior1',''),'prior2':r.get('prior2','')}
        for p in POINTS:z[f'tickets_{p}']=';'.join(ranked[:p])
        groups[(d,code,h)].append(z)
    for _,arr in groups.items():
        frozen.append(max(arr,key=lambda z:z['v53_score']))
    return frozen

def settle(frozen):
    byday=defaultdict(list)
    for z in frozen:byday[z['date']].append(z)
    out=[]
    for d,arr in sorted(byday.items()):
        ymd=d.replace('-','/');res={r['レースコード']:r for r in dayrows(f'data/results/realtime/{ymd}.csv')};pay={r['レースコード']:r for r in dayrows(f'data/results/payouts/{ymd}.csv')}
        for z in arr:
            rr=res.get(z['race_code'],{});pr=pay.get(z['race_code'],{});win=ii(rr.get('1着_艇番'));kim=normkim(rr.get('決まり手'))
            combo=(pr.get('3連単_組番') or '').strip();payout=ii(pr.get('3連単_払戻金'))
            q=dict(z);q.update({'winner':win,'kimarite':kim,'head_hit':int(win==z['head_boat']),
                               'method_hit':int(route_match(z['model'],win,kim)),'actual_combo':combo,'payout':payout})
            for p in POINTS:
                ts=q[f'tickets_{p}'].split(';') if q[f'tickets_{p}'] else []
                q[f'invest_{p}']=len(ts)*100;q[f'hit_{p}']=int(combo in ts);q[f'return_{p}']=payout if combo in ts else 0
            out.append(q)
    return out

def stat(rs,p):
    n=len(rs);hh=sum(z['head_hit'] for z in rs);mh=sum(z['method_hit'] for z in rs);bh=sum(z[f'hit_{p}'] for z in rs)
    inv=sum(z[f'invest_{p}'] for z in rs);ret=sum(z[f'return_{p}'] for z in rs)
    return (n,100*hh/n if n else 0,100*mh/n if n else 0,100*bh/n if n else 0,inv,ret,100*ret/inv if inv else 0)

def write_csv(path,rs):
    if not rs:return
    with open(path,'w',newline='',encoding='utf-8-sig') as f:
        fs=sorted(set().union(*(r.keys() for r in rs)));w=csv.DictWriter(f,fieldnames=fs);w.writeheader();w.writerows(rs)

def validation_rule(out,m):
    # Exploratory live rule: chosen only from the pre-test validation window, never from 8/3-9/2.
    cand=[]
    for band in ['A','S']:
        for p in POINTS:
            rs=[z for z in out if z['period']=='validation' and z['model']==m and (z['approved_A'] if band=='A' else z['approved_S'])]
            n,hr,mr,br,inv,ret,roi=stat(rs,p)
            min_n=15 if band=='A' else 10
            if n>=min_n:cand.append((roi,n,band,p,hr,br))
    if not cand:return ('A',20,0,0)
    cand.sort(reverse=True)
    roi,n,band,p,hr,br=cand[0]
    return band,p,roi,n

def fmt_code(code):
    v=int(code[8:10]);r=int(code[10:12]);return f'{VENUE.get(v,v)}{r}R'

def main():
    pri,fit_tot=learn_fit_priors();stbias=learn_st_frame_bias();chosen,tuned=tune_pair_weights(pri,stbias)
    src=load_source();pre0902=pre_rows_0902(src);frozen=freeze(src,stbias,pri,chosen)
    # DIRECT snapshot is serialized before settle, proving it has no results/payouts.
    direct0902=[dict(z) for z in frozen if z['date']=='2026-09-02']
    write_csv('v53_20260902_pre.csv',pre0902);write_csv('v53_20260902_direct.csv',direct0902)
    out=settle(frozen);write_csv('analysis_v53_pair_tickets.csv',out)

    L=['# v53 pair-aware相手モデル + 4角S再現性検証','',
       '6/1-6/30だけで2着・3着・2着→3着の組み合わせ傾向を学習。7/1-7/15だけでpair重みを選択。7/16以降は固定後に結果照合。',
       '3まくり・5頭だけpair-aware相手順位へ変更。3まくり差し・4カドはv52相手順位を維持。直前情報は枠補正済み。実進入/ST展示コース列は不使用。','',
       '## pair重み（7/1-7/15のみで決定）']
    for m in sorted(PAIR_MODELS):
        L.append(f'- {m}: {chosen[m]:.2f}')
    L+=['','## 4カドまくり 直前S validation再現性','|点数|候補R|頭率|決まり手率|3連単的中率|ROI|','|---:|---:|---:|---:|---:|---:|']
    rs=[z for z in out if z['period']=='validation' and z['model']=='4カドまくり' and z['approved_S']]
    for p in POINTS:
        n,hr,mr,br,inv,ret,roi=stat(rs,p);L.append(f'|{p}|{n}|{hr:.1f}%|{mr:.1f}%|{br:.1f}%|{roi:.1f}%|')
    for period in ['validation','test']:
        L+=['',f'## {period} 直前A以上','|モデル|点数|候補R|頭率|3連単的中率|ROI|','|---|---:|---:|---:|---:|---:|']
        for m in MODELS:
            rr=[z for z in out if z['period']==period and z['model']==m and z['approved_A']]
            for p in POINTS:
                n,hr,mr,br,inv,ret,roi=stat(rr,p);L.append(f'|{m}|{p}|{n}|{hr:.1f}%|{br:.1f}%|{roi:.1f}%|')
    with open('summary_v53_pair_tickets.md','w',encoding='utf-8') as f:f.write('\n'.join(L)+'\n')

    # Choose an exploratory live rule using VALIDATION ONLY, then apply it to Sep 2 direct snapshot.
    rules={m:validation_rule(out,m) for m in MODELS}
    live=[]
    settled0902={ (z['race_code'],z['head_boat']):z for z in out if z['date']=='2026-09-02' }
    for z in direct0902:
        band,p,vroi,vn=rules[z['model']]
        ok=z['approved_A'] if band=='A' else z['approved_S']
        if not ok:continue
        s=settled0902[(z['race_code'],z['head_boat'])]
        live.append({'race_code':z['race_code'],'race':fmt_code(z['race_code']),'model':z['model'],'head_boat':z['head_boat'],
                     'validation_rule':f'{band}/{p}点','validation_roi':round(vroi,1),'validation_n':vn,'v53_score':round(z['v53_score'],2),
                     'tickets':z[f'tickets_{p}'],'actual_combo':s['actual_combo'],'winner':s['winner'],'kimarite':s['kimarite'],
                     'payout':s['payout'],'hit':s[f'hit_{p}'],'invest':s[f'invest_{p}'],'return':s[f'return_{p}']})
    write_csv('v53_20260902_settled.csv',live)

    F=['# 2026-09-02 一連フロー再現（v53 / no-leak）','',
       'PRE: v46事前候補だけ。DIRECT: 枠補正済み直前情報でA/S・買い目まで固定。SETTLE: その後にだけ着順/払戻を結合。',
       f'前日候補 {len(pre0902)}行 → 頭重複統合後の直前評価 {len(direct0902)}R。','',
       '## 前日候補','|レース|モデル|頭|履歴pct|履歴加点|','|---|---|---:|---:|---:|']
    for r in sorted(pre0902,key=lambda x:(x['race_code'],x['model'])):
        F.append(f"|{fmt_code(r['race_code'])}|{r['model']}|{r['head_boat']}|{r['history_pct']}|{r['history_adjust']}|")
    F+=['','## 直前評価（結果未読）','|レース|モデル|score|A|S|4点買い目|','|---|---|---:|---:|---:|---|']
    for z in sorted(direct0902,key=lambda x:x['race_code']):
        F.append(f"|{fmt_code(z['race_code'])}|{z['model']}|{z['v53_score']:.1f}|{z['approved_A']}|{z['approved_S']}|{z['tickets_4']}|")
    F+=['','## validationだけで選んだ仮実戦ルール','|モデル|ルール|validation R|validation ROI|','|---|---|---:|---:|']
    for m in MODELS:
        band,p,roi,n=rules[m];F.append(f'|{m}|{band}/{p}点|{n}|{roi:.1f}%|')
    F+=['','## 9/2 仮実戦結果','|レース|モデル|ルール|買い目|結果|払戻|的中|投資|回収|','|---|---|---|---|---|---:|---:|---:|---:|']
    for z in sorted(live,key=lambda x:x['race_code']):
        F.append(f"|{z['race']}|{z['model']}|{z['validation_rule']}|{z['tickets']}|{z['actual_combo']}|{z['payout']:,}円|{z['hit']}|{z['invest']:,}円|{z['return']:,}円|")
    inv=sum(z['invest'] for z in live);ret=sum(z['return'] for z in live);roi=100*ret/inv if inv else 0
    F+=['',f'仮実戦合計: {len(live)}R / 投資 {inv:,}円 / 回収 {ret:,}円 / ROI {roi:.1f}%']
    with open('summary_v53_20260902_flow.md','w',encoding='utf-8') as f:f.write('\n'.join(F)+'\n')

if __name__=='__main__':main()
