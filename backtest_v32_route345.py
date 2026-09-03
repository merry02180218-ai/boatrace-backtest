from analyze_v31_outer4_5chain import *
from backtest_v20_week import select_set, allocate, composite, pair_key, cal_prob

TR0=date(2026,6,1);TR1=date(2026,7,15);VA0=date(2026,7,16);VA1=date(2026,8,2);TE0=date(2026,8,3);TE1=date(2026,9,2)
MODELS=['3攻め頭','4刺され','5まくり差し']
HEAD={'3攻め頭':3,'4刺され':4,'5まくり差し':5}

def feat32(x):
    fr=features29(x);o4=outer_take(x[4]);o5=take5(x[5]);follow4=c01x(.42*fastx(x[4])+.33*sx(x[4])+.25*c01x(x[4]['stretch']))
    counter4=c01x(.38*o4+.22*(1-fr['3旋回足'])+.18*(1-fr['3伸び'])+.12*fr['3スタート先行度']+.10*fr['2壁弱さ'])
    chain5=c01x(.34*fr['3スタート先行度']+.26*follow4+.30*o5+.10*(1-c01x(x[4]['turnfoot'])))
    s3=c01x(.55*fr['直まくり指数v29']+.45*fr['まくり差し指数v29'])
    return fr,{'counter4':counter4,'chain5':chain5,'score3':s3,'follow4':follow4,'o5':o5}

def outcome(rr,m):
    w=i(rr.get('1着_艇番'));s=i(rr.get('2着_艇番'));kim=(rr.get('決まり手') or '').replace(' ','').replace('　','')
    if m=='3攻め頭':return int(w==3 and kim in ('まくり','まくり差し'))
    if m=='4刺され':return int(w==4 and s==3)
    return int(w==5 and kim=='まくり差し')

def score(z,m):return 100*(z['score3'] if m=='3攻め頭' else z['counter4'] if m=='4刺され' else z['chain5'])

def route(fr,z,c4q,chainq):
    if fr['3スタート先行度']<.72:return None
    # strongest 4-counter zone first
    if z['counter4']>=c4q[2]:return '4刺され'
    # middle 4 pressure + non-extreme 5 chain zone
    if c4q[1]<=z['counter4']<c4q[2] and chainq[0]<=z['chain5']<=chainq[2]:return '5まくり差し'
    # otherwise retain 3 head if attack quality is adequate
    if fr['3脅威度']>=.48 and (fr['3旋回足']>=.44 or fr['3伸び']>=.44):return '3攻め頭'
    return None

def prep_until(cache,hist,seen,target):
    d=PRELOAD_START
    while d<target:
        ingest_motor(hist,seen,d)
        if d>=target-timedelta(days=12):ingest_prior_day_preview(cache,d)
        d+=timedelta(days=1)

def main():
    cache={};hist=defaultdict(list);seen=set();d=PRELOAD_START
    while d<TR0:
        ingest_motor(hist,seen,d)
        if d>=TR0-timedelta(days=12):ingest_prior_day_preview(cache,d)
        d+=timedelta(days=1)
    train_raw=[];train={m:[] for m in MODELS};pairs={m:defaultdict(int) for m in MODELS}
    d=TR0
    while d<=TR1:
        feats=process_features(d,cache,hist);ymd=d.strftime('%Y/%m/%d');res={r['レースコード']:r for r in rows(f'data/results/realtime/{ymd}.csv')};pay={r['レースコード']:r for r in rows(f'data/results/payouts/{ymd}.csv')}
        for r,x,s4,s5,dc in feats:
            fr,z=feat32(x)
            if fr['3スタート先行度']<.72:continue
            train_raw.append((fr,z,r['レースコード'],res.get(r['レースコード'],{}),pay.get(r['レースコード'],{})))
        ingest_prior_day_preview(cache,d);ingest_motor(hist,seen,d);d+=timedelta(days=1)
    c4s=[z['counter4'] for fr,z,_,_,_ in train_raw];chs=[z['chain5'] for fr,z,_,_,_ in train_raw];c4q=[q(c4s,p) for p in (.25,.5,.75)];chainq=[q(chs,p) for p in (.25,.5,.75)]
    for fr,z,code,rr,pr in train_raw:
        m=route(fr,z,c4q,chainq)
        if not m:continue
        y=outcome(rr,m);train[m].append((score(z,m),y))
        if y:
            k=pair_key((pr.get('3連単_組番') or '').strip())
            if k:pairs[m][k]+=1
    def run_period(start,end,label):
        nonlocal d,cache,hist,seen
        while d<start:
            process_features(d,cache,hist);ingest_prior_day_preview(cache,d);ingest_motor(hist,seen,d);d+=timedelta(days=1)
        races=[];bets=[]
        while d<=end:
            feats=process_features(d,cache,hist);ymd=d.strftime('%Y/%m/%d');ods={r['レースコード']:r for r in rows(f'data/previews/od3/{ymd}.csv')};frozen=[]
            for r,x,s4,s5,dc in feats:
                fr,z=feat32(x);m=route(fr,z,c4q,chainq)
                if not m:continue
                sc=score(z,m);p=cal_prob(train[m],sc);chosen=select_set(HEAD[m],p,ods.get(r['レースコード'],{}),pairs[m])
                if not chosen:continue
                allocate(chosen);rr={'period':label,'model':m,'date':str(d),'race_code':r['レースコード'],'venue':r.get('レース場コード',''),'race':r.get('レース回',''),'score':round(sc,2),'p':round(p,4),'counter4':round(z['counter4'],3),'chain5':round(z['chain5'],3),'jump3':round(fr['3スタート先行度'],3),'tickets':len(chosen)};races.append(rr)
                for b in chosen:b.update({'period':label,'model':m,'date':str(d),'race_code':r['レースコード']});frozen.append(b)
            pay={r['レースコード']:r for r in rows(f'data/results/payouts/{ymd}.csv')};res={r['レースコード']:r for r in rows(f'data/results/realtime/{ymd}.csv')}
            for b in frozen:
                pr=pay.get(b['race_code'],{});actual=(pr.get('3連単_組番') or '').strip();hit=actual==b['combo'];b['hit']=int(hit);b['return']=i(pr.get('3連単_払戻金'))*(b['stake']//100) if hit else 0;bets.append(b)
            for rr in [x for x in races if x['date']==str(d)]:rr['target_hit']=outcome(res.get(rr['race_code'],{}),rr['model'])
            ingest_prior_day_preview(cache,d);ingest_motor(hist,seen,d);d+=timedelta(days=1)
        for rr in races:
            bs=[b for b in bets if b['race_code']==rr['race_code'] and b['model']==rr['model']];rr['bet_hit']=int(any(b['hit'] for b in bs));rr['return']=sum(b['return'] for b in bs)
        return races,bets
    vr,vb=run_period(VA0,VA1,'validation');tr,tb=run_period(TE0,TE1,'latest_month');races=vr+tr;bets=vb+tb
    with open('races_v32_route345.csv','w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=sorted(set().union(*(r.keys() for r in races))));w.writeheader();w.writerows(races)
    with open('bets_v32_route345.csv','w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=sorted(set().union(*(b.keys() for b in bets))));w.writeheader();w.writerows(bets)
    L=['# v32 3→4→5 展開分岐モデル','',f'学習 {TR0}〜{TR1}。閾値は学習期間の四分位のみで固定。検証 {VA0}〜{VA1} / 最新月 {TE0}〜{TE1}。実進入不使用。','','分岐: 4刺されリスクが学習Q4なら4-3狙い、4リスク中間＋5連鎖が非極端なら5まくり差し、それ以外の高ST3攻めは3頭。','','学習境界: counter4 Q1={:.3f}, Q2={:.3f}, Q3={:.3f}; chain5 Q1={:.3f}, Q2={:.3f}, Q3={:.3f}'.format(*(c4q+chainq))]
    for label in ['validation','latest_month']:
        L+=['',f'## {label}','|モデル|候補R|狙い成立|成立率|3連単的中|的中率|投資|払戻|回収率|','|---|---:|---:|---:|---:|---:|---:|---:|---:|']
        rs0=[r for r in races if r['period']==label];bs0=[b for b in bets if b['period']==label]
        for m in MODELS+['合計']:
            rs=rs0 if m=='合計' else [r for r in rs0 if r['model']==m];bs=bs0 if m=='合計' else [b for b in bs0 if b['model']==m];n=len(rs);h=sum(r['target_hit'] for r in rs);bh=sum(r['bet_hit'] for r in rs);st=sum(b['stake'] for b in bs);ret=sum(b['return'] for b in bs);L.append(f'|{m}|{n}|{h}|{100*h/n if n else 0:.1f}%|{bh}|{100*bh/n if n else 0:.1f}%|{st:,}円|{ret:,}円|{100*ret/st if st else 0:.1f}%|')
    open('summary_v32_route345.md','w',encoding='utf-8').write('\n'.join(L)+'\n')
if __name__=='__main__':main()
