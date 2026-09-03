from backtest_v28_psych3_blockfilter_month import *

MODELS29=['3直まくりv29','3まくり差しv29']

# v29: classify the 3-boat attack by predicted start-position relationship BEFORE scoring.
# High jump -> direct makuri; middle jump -> makurizashi; low/no jump with block conditions -> kill 3.
# Thresholds are structural/frozen before Aug3-Sep2 result comparison.

def zone29(fr):
    j=fr['3スタート先行度']
    if j>=.72:return '大幅先行'
    if j>=.46:return '中間先行'
    return '先行なし'

def kill29(fr):
    # Strong 1/2 resistance in the no-jump region. Keep v28 hard kill as a second route.
    nojump=(fr['3スタート先行度']<.46 and fr['1ブロック成功指数']>=.56 and fr['2壁弱さ']<.58)
    return nojump or kill3(fr)

def features29(x):
    fr=psych_features28(x); j=fr['3スタート先行度']; z=zone29(fr)
    # Peak around .58: enough launch to enter the first turn aggressively, but not enough to simply swallow 1/2.
    middle=c01(1-abs(j-.58)/.18)
    # Direct score is intentionally dominated by the high-jump state.
    direct=c01(.40*j+.18*fr['2壁弱さ']+.15*fr['3脅威度']+.10*fr['3伸び']+.07*attack_hist(x[3])+.06*(1-fr['1ブロック成功指数'])+.04*(1-fr['1ブロック力']))
    # Makurizashi: middle launch + pressure + turn. Too weak a wall can convert to direct attack, too strong a wall can shut 3 out.
    wall_mid=c01(1-abs(fr['2壁弱さ']-.56)/.34)
    ms=c01(.27*middle+.19*fr['1対3圧力']+.18*fr['3旋回足']+.13*fr['3脅威度']+.10*wall_mid+.08*fr['差し場生成指数']+.05*(1-fr['1ブロック成功指数']))
    fr.update({'STゾーン':z,'中間ST適合':middle,'2壁中間適合':wall_mid,'直まくり指数v29':direct,'まくり差し指数v29':ms})
    return fr

def score29(fr,m):return 100*(fr['直まくり指数v29'] if m=='3直まくりv29' else fr['まくり差し指数v29'])
def target29(rr,m):
    win=i(rr.get('1着_艇番'));kim=(rr.get('決まり手') or '').replace(' ','').replace('　','')
    return int(win==3 and kim==('まくり' if m=='3直まくりv29' else 'まくり差し'))

def pass29(fr,m):
    if kill29(fr):return False
    if m=='3直まくりv29':
        return fr['STゾーン']=='大幅先行' and fr['直まくり指数v29']>=.61 and fr['2壁弱さ']>=.50 and fr['3脅威度']>=.48
    return (fr['STゾーン']=='中間先行' and fr['まくり差し指数v29']>=.57 and fr['中間ST適合']>=.50 and
            fr['3脅威度']>=.48 and fr['3旋回足']>=.44 and fr['1対3圧力']>=.25 and fr['2壁中間適合']>=.45)

def ev(rs,bs,m):
    a=[r for r in rs if r['model']==m];b=[q for q in bs if q['model']==m];h=sum(r['head_hit'] for r in a);bh=sum(r['bet_hit'] for r in a);st=sum(q['stake'] for q in b);ret=sum(q['return'] for q in b)
    return len(a),h,100*h/len(a) if a else 0,bh,100*bh/len(a) if a else 0,st,ret,100*ret/st if st else 0

def main():
    cache={};hist=defaultdict(list);seen=set();d=PRELOAD_START
    while d<TRAIN_START:
        ingest_motor(hist,seen,d)
        if d>=TRAIN_START-timedelta(days=12):ingest_prior_day_preview(cache,d)
        d+=timedelta(days=1)
    train={m:[] for m in MODELS29};pairs={m:defaultdict(int) for m in MODELS29}
    d=TRAIN_START
    while d<=TRAIN_END:
        feats=process_features(d,cache,hist);ymd=d.strftime('%Y/%m/%d');res={r['レースコード']:r for r in rows(f'data/results/realtime/{ymd}.csv')};pay={r['レースコード']:r for r in rows(f'data/results/payouts/{ymd}.csv')}
        for r,x,s4,s5,dc in feats:
            fr=features29(x)
            for m in MODELS29:
                sc=score29(fr,m);y=target29(res.get(r['レースコード'],{}),m);train[m].append((sc,y))
                if y:
                    k=pair_key((pay.get(r['レースコード'],{}).get('3連単_組番') or '').strip())
                    if k:pairs[m][k]+=1
        ingest_prior_day_preview(cache,d);ingest_motor(hist,seen,d);d+=timedelta(days=1)
    while d<TEST_START:
        process_features(d,cache,hist);ingest_prior_day_preview(cache,d);ingest_motor(hist,seen,d);d+=timedelta(days=1)
    races=[];bets=[];zones=defaultdict(lambda:[0,0,0,0]);kills=[0,0]
    while d<=TEST_END:
        feats=process_features(d,cache,hist);ymd=d.strftime('%Y/%m/%d');ods={r['レースコード']:r for r in rows(f'data/previews/od3/{ymd}.csv')};frozen=[];meta=[]
        for r,x,s4,s5,dc in feats:
            fr=features29(x);meta.append((r['レースコード'],fr['STゾーン'],kill29(fr)))
            if kill29(fr):kills[0]+=1;continue
            for m in MODELS29:
                if not pass29(fr,m):continue
                sc=score29(fr,m);p=cal_prob(train[m],sc);chosen=select_set(3,p,ods.get(r['レースコード'],{}),pairs[m])
                if not chosen:continue
                allocate(chosen);rr={'model':m,'date':str(d),'race_code':r['レースコード'],'venue':r.get('レース場コード',''),'race':r.get('レース回',''),'score':round(sc,2),'prob':round(p,4),'zone':fr['STゾーン']};rr.update({k:round(v,3) if isinstance(v,float) else v for k,v in fr.items()});races.append(rr)
                for q in chosen:q.update({'model':m,'date':str(d),'race_code':r['レースコード']});frozen.append(q)
        pay={r['レースコード']:r for r in rows(f'data/results/payouts/{ymd}.csv')};res={r['レースコード']:r for r in rows(f'data/results/realtime/{ymd}.csv')}
        for code,z,killed in meta:
            rr=res.get(code,{});win=i(rr.get('1着_艇番'));kim=(rr.get('決まり手') or '').replace(' ','').replace('　','');mk=int(win==3 and kim=='まくり');ms=int(win==3 and kim=='まくり差し');zones[z][0]+=1;zones[z][1]+=mk;zones[z][2]+=ms;zones[z][3]+=mk+ms
            if killed and (mk or ms):kills[1]+=1
        for b in frozen:
            pr=pay.get(b['race_code'],{});actual=(pr.get('3連単_組番') or '').strip();hit=actual==b['combo'];b['hit']=int(hit);b['return']=(i(pr.get('3連単_払戻金'))*(b['stake']//100)) if hit else 0;bets.append(b)
        for rr in [q for q in races if q['date']==str(d)]:rr['head_hit']=target29(res.get(rr['race_code'],{}),rr['model'])
        ingest_prior_day_preview(cache,d);ingest_motor(hist,seen,d);d+=timedelta(days=1)
    for r in races:
        bs=[b for b in bets if b['race_code']==r['race_code'] and b['model']==r['model']];r['bet_hit']=int(any(b['hit'] for b in bs));r['return']=sum(b['return'] for b in bs)
    with open('races_v29_psych3_zones_month.csv','w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=sorted(set().union(*(r.keys() for r in races))));w.writeheader();w.writerows(races)
    with open('bets_v29_psych3_zones_month.csv','w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=sorted(set().union(*(b.keys() for b in bets))));w.writeheader();w.writerows(bets)
    L=['# v29 3号艇 ST3ゾーン心理展開モデル 1か月バックテスト','',f'テスト: {TEST_START}〜{TEST_END} / 学習: {TRAIN_START}〜{TRAIN_END}','','実進入なし。候補・買い目を先に固定し、その後結果照合。ST先行度を「大幅先行」「中間先行」「先行なし」に先に分岐してから、直まくり/まくり差し/3消しを判定。','','|モデル|候補R|狙い成立|成立率|3連単的中|的中率|投資|払戻|回収率|','|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for m in MODELS29:
        n,h,hr,bh,bhr,st,ret,roi=ev(races,bets,m);L.append(f'|{m}|{n}|{h}|{hr:.1f}%|{bh}|{bhr:.1f}%|{st:,}円|{ret:,}円|{roi:.1f}%|')
    n=len(races);h=sum(r['head_hit'] for r in races);bh=sum(r['bet_hit'] for r in races);st=sum(b['stake'] for b in bets);ret=sum(b['return'] for b in bets);L.append(f'|合計|{n}|{h}|{100*h/n if n else 0:.1f}%|{bh}|{100*bh/n if n else 0:.1f}%|{st:,}円|{ret:,}円|{100*ret/st if st else 0:.1f}%|')
    L+=['','## STゾーン別の実際の3号艇決まり手','|ゾーン|全R|3まくり|率|3まくり差し|率|合計率|','|---|---:|---:|---:|---:|---:|---:|']
    for z in ['大幅先行','中間先行','先行なし']:
        n,mk,ms,tot=zones[z];L.append(f'|{z}|{n}|{mk}|{100*mk/n if n else 0:.1f}%|{ms}|{100*ms/n if n else 0:.1f}%|{100*tot/n if n else 0:.1f}%|')
    L+=['','## 3消し',f'- 判定 {kills[0]}R / その中の3まくり・まくり差し成立 {kills[1]}R ({100*kills[1]/kills[0] if kills[0] else 0:.1f}%)','','## v29の固定分岐','- 大幅先行: 3スタート先行度 >= 0.72 → 直まくり側のみ。','- 中間先行: 0.46〜0.72未満 → まくり差し側のみ。ST適合は0.58付近をピーク化。','- 先行なし: <0.46。1ブロック成功+2壁が残る条件なら3消し。','- まくり差しでは2壁弱さを「弱いほど良い」にせず、中間帯を評価する。']
    open('summary_v29_psych3_zones_month.md','w',encoding='utf-8').write('\n'.join(L)+'\n')
if __name__=='__main__':main()
