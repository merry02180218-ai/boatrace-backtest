import csv
from collections import defaultdict
from backtest_v34_tilt_compare import *
from analyze_v23_20260902_daypreview import by_code, original_scores, rank_score

TR0=date(2026,6,1);TR1=date(2026,7,15);VA0=date(2026,7,16);VA1=date(2026,8,2);TE0=date(2026,8,3);TE1=date(2026,9,2)

# Fixed pre-result interaction definition. No actual entry/course fields are used.
def interaction_features(model, code, tkz, stt, orig):
    boat=tboat(model)
    tr=tkz.get(code,{}); sr=stt.get(code,{}); orr=orig.get(code,{})
    t=tiltval(tr.get(f'艇{boat}_チルト'))
    stvals={b:f(sr.get(f'艇{b}_スタート展示')) for b in range(1,7)}
    st=rank_score(stvals,boat,True)
    straight=original_scores(orr,boat)['straight']
    high_tilt=(t is not None and t>=0.5)
    strong=int(high_tilt and st>=0.60 and straight>=0.60)
    return {'tilt':t,'st_rank':st,'straight_rank':straight,'strong':strong}

def qv(vals,p):
    a=sorted(vals)
    if not a:return 0.0
    x=(len(a)-1)*p; lo=int(x); hi=min(lo+1,len(a)-1); w=x-lo
    return a[lo]*(1-w)+a[hi]*w

def learn_bonus(rows0):
    # Learn only from training. Strong interaction is shrunk toward base and only gets a positive support bonus.
    out={}
    for m in MODELS:
        a=[z for z in rows0 if z['model']==m]
        base=sum(z['y'] for z in a)/len(a) if a else .05
        g=[z for z in a if z['strong']]
        n=len(g); h=sum(z['y'] for z in g)
        shr=(h+30*base)/(n+30) if n+30 else base
        rel=(shr-base)/max(base,.03)
        pts=max(0.0,min(5.0,8.0*rel))
        out[m]=(pts,n,shr,base)
    return out

def main():
    cache={};hist=defaultdict(list);seen=set();d=PRELOAD_START
    while d<TR0:
        ingest_motor(hist,seen,d)
        if d>=TR0-timedelta(days=12):ingest_prior_day_preview(cache,d)
        d+=timedelta(days=1)

    raw=[]; c4vals=[]
    d=TR0
    while d<=TR1:
        feats=process_features(d,cache,hist); ymd=d.strftime('%Y/%m/%d')
        res={r['レースコード']:r for r in rows(f'data/results/realtime/{ymd}.csv')}
        pay={r['レースコード']:r for r in rows(f'data/results/payouts/{ymd}.csv')}
        tkz=by_code(f'data/previews/tkz/{ymd}.csv'); stt=by_code(f'data/previews/stt/{ymd}.csv'); orig=by_code(f'data/previews/original_exhibition/{ymd}.csv')
        for r,x,s4,s5,dc in feats:
            fr32,z32=feat32(x)
            if fr32['3スタート先行度']>=.72:c4vals.append(z32['counter4'])
            s3=score3v4(x)
            for m in MODELS:
                fr=get_fr(x,s3,s4,dc,m)
                if m!='4刺され' and not eligible(fr,m,0):continue
                if m=='4刺され' and fr['3スタート先行度']<.72:continue
                it=interaction_features(m,r['レースコード'],tkz,stt,orig)
                raw.append({'model':m,'score':raw_score(x,s3,s4,m),'y':target34(res.get(r['レースコード'],{}),m),
                            'combo':(pay.get(r['レースコード'],{}).get('3連単_組番') or '').strip(),'counter4':fr.get('counter4',0),**it})
        ingest_prior_day_preview(cache,d);ingest_motor(hist,seen,d);d+=timedelta(days=1)

    c4q3=qv(c4vals,.75)
    raw=[z for z in raw if z['model']!='4刺され' or z['counter4']>=c4q3]
    bonus=learn_bonus(raw)
    train_base={m:[] for m in MODELS};train_int={m:[] for m in MODELS};pairs={m:defaultdict(int) for m in MODELS}
    for z in raw:
        m=z['model'];train_base[m].append((z['score'],z['y']))
        adj=z['score']+(bonus[m][0] if z['strong'] else 0);train_int[m].append((adj,z['y']))
        if z['y']:
            k=pair_key(z['combo'])
            if k:pairs[m][k]+=1

    def run_period(start,end,label):
        nonlocal d
        while d<start:
            process_features(d,cache,hist);ingest_prior_day_preview(cache,d);ingest_motor(hist,seen,d);d+=timedelta(days=1)
        races=[];bets=[]
        while d<=end:
            feats=process_features(d,cache,hist);ymd=d.strftime('%Y/%m/%d')
            ods={r['レースコード']:r for r in rows(f'data/previews/od3/{ymd}.csv')}
            tkz=by_code(f'data/previews/tkz/{ymd}.csv'); stt=by_code(f'data/previews/stt/{ymd}.csv'); orig=by_code(f'data/previews/original_exhibition/{ymd}.csv'); frozen=[]
            for r,x,s4,s5,dc in feats:
                s3=score3v4(x)
                for m in MODELS:
                    fr=get_fr(x,s3,s4,dc,m)
                    if not eligible(fr,m,c4q3):continue
                    it=interaction_features(m,r['レースコード'],tkz,stt,orig);base_sc=raw_score(x,s3,s4,m);bpts=bonus[m][0] if it['strong'] else 0
                    for variant,sc,trset in [('baseline',base_sc,train_base[m]),('interaction',base_sc+bpts,train_int[m])]:
                        p=cal_prob(trset,sc);chosen=select_set(HEAD[m],p,ods.get(r['レースコード'],{}),pairs[m])
                        if not chosen:continue
                        allocate(chosen);rr={'period':label,'variant':variant,'model':m,'date':str(d),'race_code':r['レースコード'],'score':round(sc,2),'interaction':it['strong'],'tilt':it['tilt'],'st_rank':round(it['st_rank'],2),'straight_rank':round(it['straight_rank'],2),'bonus':round(bpts,2),'tickets':len(chosen)};races.append(rr)
                        for z in chosen:z.update({'period':label,'variant':variant,'model':m,'date':str(d),'race_code':r['レースコード']});frozen.append(z)
            pay={r['レースコード']:r for r in rows(f'data/results/payouts/{ymd}.csv')};res={r['レースコード']:r for r in rows(f'data/results/realtime/{ymd}.csv')}
            for b0 in frozen:
                pr=pay.get(b0['race_code'],{});act=(pr.get('3連単_組番') or '').strip();hit=act==b0['combo'];b0['hit']=int(hit);b0['return']=i(pr.get('3連単_払戻金'))*(b0['stake']//100) if hit else 0;bets.append(b0)
            for rr in [z for z in races if z['date']==str(d)]:rr['target_hit']=target34(res.get(rr['race_code'],{}),rr['model'])
            ingest_prior_day_preview(cache,d);ingest_motor(hist,seen,d);d+=timedelta(days=1)
        for rr in races:
            bs=[b for b in bets if b['race_code']==rr['race_code'] and b['model']==rr['model'] and b['variant']==rr['variant']];rr['bet_hit']=int(any(b['hit'] for b in bs));rr['return']=sum(b['return'] for b in bs)
        return races,bets

    vr,vb=run_period(VA0,VA1,'validation');tr,tb=run_period(TE0,TE1,'latest_month');races=vr+tr;bets=vb+tb
    with open('races_v35_tilt_interaction.csv','w',newline='',encoding='utf-8-sig') as f0:
        w=csv.DictWriter(f0,fieldnames=sorted(set().union(*(r.keys() for r in races))));w.writeheader();w.writerows(races)
    L=['# v35 チルト×展示ST×直線 相互作用テスト','',f'学習 {TR0}〜{TR1} のみ。検証 {VA0}〜{VA1} / 最新月 {TE0}〜{TE1}。実進入不使用。強シグナルはチルト>=+0.5、展示ST順位スコア>=0.60、オリジナル展示直線順位スコア>=0.60の同時成立。','',f'4刺され counter4 学習Q3境界={c4q3:.3f}','', '## 学習で決まった強シグナル加点','|モデル|加点|学習強シグナルR|強シグナル推定率|学習ベース率|','|---|---:|---:|---:|---:|']
    for m in MODELS:
        pts,n,shr,base=bonus[m];L.append(f'|{m}|+{pts:.2f}|{n}|{shr*100:.1f}%|{base*100:.1f}%|')
    for label in ['validation','latest_month']:
        L+=['',f'## {label}','|モデル|版|候補R|強シグナルR|狙い成立|成立率|3連単的中|的中率|投資|払戻|ROI|','|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
        for m in MODELS+['合計']:
            for v in ['baseline','interaction']:
                rs=[r for r in races if r['period']==label and r['variant']==v and (m=='合計' or r['model']==m)];bs=[b for b in bets if b['period']==label and b['variant']==v and (m=='合計' or b['model']==m)];n=len(rs);sg=sum(r['interaction'] for r in rs);h=sum(r['target_hit'] for r in rs);bh=sum(r['bet_hit'] for r in rs);st=sum(b['stake'] for b in bs);ret=sum(b['return'] for b in bs);L.append(f'|{m}|{v}|{n}|{sg}|{h}|{100*h/n if n else 0:.1f}%|{bh}|{100*bh/n if n else 0:.1f}%|{st:,}円|{ret:,}円|{100*ret/st if st else 0:.1f}%|')
        # signal-only diagnostic independent of ticket changes
        L+=['',f'### {label} 強シグナル実績','|モデル|R|狙い成立|成立率|','|---|---:|---:|---:|']
        for m in MODELS:
            rs=[r for r in races if r['period']==label and r['variant']=='baseline' and r['model']==m and r['interaction']];n=len(rs);h=sum(r['target_hit'] for r in rs);L.append(f'|{m}|{n}|{h}|{100*h/n if n else 0:.1f}%|')
    open('summary_v35_tilt_interaction.md','w',encoding='utf-8').write('\n'.join(L)+'\n')

if __name__=='__main__':main()
