from backtest_v27_psych3_month import *

MODELS28=['3直まくりv28','3まくり差しv28']

# v28: split the 1-vs-3 interaction into three mutually interpretable states.
# 1) direct-makuri window: 3 gets a clear predicted launch over both 1 and 2.
# 2) makurizashi window: 1 is pressured into defending, 2 is vulnerable, and 3 can turn inside.
# 3) block-success window: 1 can match the start and 2 can remain a wall -> remove 3 from both attack models.
# All thresholds are fixed structurally before reading Aug3-Sep2 results.

def psych_features28(x):
    fr=psych_features(x)
    jump=fr['3スタート先行度']; threat=fr['3脅威度']; block=fr['1ブロック力']; wallweak=fr['2壁弱さ']
    turn=fr['3旋回足']; stretch=fr['3伸び']; pressure=fr['1対3圧力']
    wallstrong=1-wallweak
    start_match=c01(1-abs(jump-.50)/.32)
    moderate_jump=c01(1-abs(jump-.55)/.30)

    # 1 can shut 3 down when 1 is strong, launch is not lost, and 2 can remain a wall.
    block_success=c01(.42*block+.28*wallstrong+.20*start_match+.10*(1-c01((jump-.58)/.25)))

    # A defensive reaction by 1 becomes useful to 3 only when 2 is vulnerable and 3 has turning quality.
    inside_gap=c01(.34*pressure+.26*wallweak+.22*turn+.18*moderate_jump)

    # Direct makuri rewards clear launch and penalizes the block-success state explicitly.
    direct_raw=.36*jump+.20*wallweak+.17*threat+.12*stretch+.09*attack_hist(x[3])+.06*(1-block)
    direct=c01(direct_raw-.24*block_success*(1-jump))

    # Makurizashi requires pressure + a usable inside gap; excessive jump belongs to direct makuri.
    ms_raw=.27*inside_gap+.19*pressure+.17*turn+.14*threat+.10*wallweak+.08*moderate_jump+.05*attack_hist(x[3])
    ms=c01(ms_raw-.22*block_success-.10*c01((jump-.72)/.28))

    fr.update({'2壁強さ':wallstrong,'ST接近度':start_match,'1ブロック成功指数':block_success,'差し場生成指数':inside_gap,'直まくり指数v28':direct,'まくり差し指数v28':ms})
    return fr

def kill3(fr):
    return fr['1ブロック成功指数']>=.64 and fr['3スタート先行度']<.64 and fr['2壁弱さ']<.50

def score28(fr,m): return 100*(fr['直まくり指数v28'] if m=='3直まくりv28' else fr['まくり差し指数v28'])
def target28(rr,m):
    win=i(rr.get('1着_艇番')); kim=(rr.get('決まり手') or '').replace(' ','').replace('　','')
    return int(win==3 and kim==('まくり' if m=='3直まくりv28' else 'まくり差し'))

def pass28(fr,m):
    if kill3(fr): return False
    if m=='3直まくりv28':
        return fr['直まくり指数v28']>=.59 and fr['3スタート先行度']>=.64 and fr['2壁弱さ']>=.52 and fr['3脅威度']>=.48
    return (fr['まくり差し指数v28']>=.57 and fr['3脅威度']>=.50 and fr['1対3圧力']>=.34 and
            fr['差し場生成指数']>=.54 and fr['3旋回足']>=.46 and fr['3スタート先行度']<.74)

def eval_group28(rows_,bets_,m):
    rs=[r for r in rows_ if r['model']==m]; bs=[b for b in bets_ if b['model']==m]
    h=sum(r['head_hit'] for r in rs); bh=sum(r['bet_hit'] for r in rs); st=sum(b['stake'] for b in bs); ret=sum(b['return'] for b in bs)
    return len(rs),h,(100*h/len(rs) if rs else 0),bh,(100*bh/len(rs) if rs else 0),st,ret,(100*ret/st if st else 0)

def main():
    cache={};hist=defaultdict(list);seen=set();d=PRELOAD_START
    while d<TRAIN_START:
        ingest_motor(hist,seen,d)
        if d>=TRAIN_START-timedelta(days=12): ingest_prior_day_preview(cache,d)
        d+=timedelta(days=1)

    train={m:[] for m in MODELS28};pairs={m:defaultdict(int) for m in MODELS28}
    d=TRAIN_START
    while d<=TRAIN_END:
        feats=process_features(d,cache,hist);ymd=d.strftime('%Y/%m/%d')
        res={r['レースコード']:r for r in rows(f'data/results/realtime/{ymd}.csv')};pay={r['レースコード']:r for r in rows(f'data/results/payouts/{ymd}.csv')}
        for r,x,s4,s5,dc in feats:
            fr=psych_features28(x)
            for m in MODELS28:
                sc=score28(fr,m); y=target28(res.get(r['レースコード'],{}),m); train[m].append((sc,y))
                if y:
                    k=pair_key((pay.get(r['レースコード'],{}).get('3連単_組番') or '').strip())
                    if k:pairs[m][k]+=1
        ingest_prior_day_preview(cache,d);ingest_motor(hist,seen,d);d+=timedelta(days=1)

    while d<TEST_START:
        process_features(d,cache,hist);ingest_prior_day_preview(cache,d);ingest_motor(hist,seen,d);d+=timedelta(days=1)

    races=[];bets=[];kill_count=0;kill_actual=0
    while d<=TEST_END:
        feats=process_features(d,cache,hist);ymd=d.strftime('%Y/%m/%d');ods={r['レースコード']:r for r in rows(f'data/previews/od3/{ymd}.csv')};frozen=[];killed=[]
        for r,x,s4,s5,dc in feats:
            fr=psych_features28(x)
            if kill3(fr):
                kill_count+=1;killed.append(r['レースコード'])
                continue
            for m in MODELS28:
                if not pass28(fr,m):continue
                sc=score28(fr,m);p=cal_prob(train[m],sc);chosen=select_set(3,p,ods.get(r['レースコード'],{}),pairs[m])
                if not chosen:continue
                allocate(chosen)
                rr={'model':m,'date':str(d),'race_code':r['レースコード'],'venue':r.get('レース場コード',''),'race':r.get('レース回',''),'score':round(sc,2),'prob':round(p,4),'tickets':len(chosen),'composite_odds':round(composite(chosen),2)}
                rr.update({k:round(v,3) for k,v in fr.items()});races.append(rr)
                for z in chosen:z.update({'model':m,'date':str(d),'race_code':r['レースコード']});frozen.append(z)
        pay={r['レースコード']:r for r in rows(f'data/results/payouts/{ymd}.csv')};res={r['レースコード']:r for r in rows(f'data/results/realtime/{ymd}.csv')}
        for code in killed:
            rr=res.get(code,{}); win=i(rr.get('1着_艇番')); kim=(rr.get('決まり手') or '').replace(' ','').replace('　','')
            if win==3 and kim in ('まくり','まくり差し'): kill_actual+=1
        for b in frozen:
            pr=pay.get(b['race_code'],{});actual=(pr.get('3連単_組番') or '').strip();hit=actual==b['combo'];b['actual_combo']=actual;b['hit']=int(hit);b['payout100']=i(pr.get('3連単_払戻金')) if hit else 0;b['return']=b['payout100']*(b['stake']//100) if hit else 0;bets.append(b)
        for rr in [q for q in races if q['date']==str(d)]: rr['head_hit']=target28(res.get(rr['race_code'],{}),rr['model'])
        ingest_prior_day_preview(cache,d);ingest_motor(hist,seen,d);d+=timedelta(days=1)

    for r in races:
        bs=[b for b in bets if b['race_code']==r['race_code'] and b['model']==r['model']];r['bet_hit']=int(any(b['hit'] for b in bs));r['return']=sum(b['return'] for b in bs)
    if races:
        with open('races_v28_psych3_month.csv','w',newline='',encoding='utf-8-sig') as f:
            w=csv.DictWriter(f,fieldnames=sorted(set().union(*(r.keys() for r in races))));w.writeheader();w.writerows(races)
    if bets:
        with open('bets_v28_psych3_month.csv','w',newline='',encoding='utf-8-sig') as f:
            w=csv.DictWriter(f,fieldnames=sorted(set().union(*(b.keys() for b in bets))));w.writeheader();w.writerows(bets)

    L=['# v28 3号艇 心理・ブロック成功分離モデル 1か月バックテスト','',f'テスト: {TEST_START}〜{TEST_END} / 学習: {TRAIN_START}〜{TRAIN_END}','',
       'v27を「直まくり」「まくり差し」「1ブロック成功=3消し」の3状態に分離。心理そのものではなく締切前に分かる選手力・コース/ST実績・前日足を代理変数化。実進入は未使用。テスト期間の結果を候補抽出前には読まない。','',
       '|モデル|候補R|狙い成立|成立率|3連単的中|的中率|投資|払戻|回収率|','|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for m in MODELS28:
        n,h,hr,bh,bhr,st,ret,roi=eval_group28(races,bets,m);L.append(f'|{m}|{n}|{h}|{hr:.1f}%|{bh}|{bhr:.1f}%|{st:,}円|{ret:,}円|{roi:.1f}%|')
    n=len(races);h=sum(r['head_hit'] for r in races);bh=sum(r['bet_hit'] for r in races);st=sum(b['stake'] for b in bets);ret=sum(b['return'] for b in bets)
    L.append(f'|合計|{n}|{h}|{100*h/n if n else 0:.1f}%|{bh}|{100*bh/n if n else 0:.1f}%|{st:,}円|{ret:,}円|{100*ret/st if st else 0:.1f}%|')
    L += ['','## 3消し判定','- 1ブロック成功指数>=0.64、3スタート先行度<0.64、2壁弱さ<0.50を同時に満たすレースは3攻め候補から除外。',f'- 3消し判定: {kill_count}R / その中で実際に3号艇まくり・まくり差し成立 {kill_actual}R ({100*kill_actual/kill_count if kill_count else 0:.1f}%)','',
       '## 構造','- 直まくり: 3の明確なST先行を最重要化。2壁弱・3脅威・伸びを加点し、1ブロック成功指数を減点。','- まくり差し: 1対3圧力だけでなく「差し場生成指数=圧力+2壁弱+3旋回+適度なST差」を必須化。1が止め切る指数は明示的に減点。','- 3が大きくST先行する場合はまくり差しから外して直まくり側へ寄せる。','',
       '## 候補上位','|モデル|日付|場|R|score|脅威|ブロック成功|ST先行|差し場|2壁弱|成立|','|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for r in sorted(races,key=lambda z:z['score'],reverse=True)[:30]:
        L.append(f"|{r['model']}|{r['date']}|{r['venue']}|{r['race']}|{r['score']}|{r['3脅威度']}|{r['1ブロック成功指数']}|{r['3スタート先行度']}|{r['差し場生成指数']}|{r['2壁弱さ']}|{r['head_hit']}|")
    open('summary_v28_psych3_month.md','w',encoding='utf-8').write('\n'.join(L)+'\n')

if __name__=='__main__':main()
