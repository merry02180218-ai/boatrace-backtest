from backtest_v20_week import *
from backtest_v32_route345 import feat32
from analyze_v33_tilt_effect import tiltval, band

TR0=date(2026,6,1);TR1=date(2026,7,15);VA0=date(2026,7,16);VA1=date(2026,8,2);TE0=date(2026,8,3);TE1=date(2026,9,2)
MODELS=['3まくり','3まくり差し','4カドまくり','4刺され','5頭展開']
HEAD={'3まくり':3,'3まくり差し':3,'4カドまくり':4,'4刺され':4,'5頭展開':5}
BANDS=['-0.5以下','0','+0.5','+1.0以上']

def q(a,p):
    a=sorted(a)
    if not a:return 0.0
    x=(len(a)-1)*p; lo=int(x); hi=min(lo+1,len(a)-1); w=x-lo
    return a[lo]*(1-w)+a[hi]*w

def tboat(m):
    return 3 if m.startswith('3') else 4 if m in ('4カドまくり','4刺され') else 5

def target34(rr,m):
    w=i(rr.get('1着_艇番'));s=i(rr.get('2着_艇番'));kim=(rr.get('決まり手') or '').replace(' ','').replace('　','')
    if m=='3まくり':return int(w==3 and kim=='まくり')
    if m=='3まくり差し':return int(w==3 and kim=='まくり差し')
    if m=='4カドまくり':return int(w==4 and kim=='まくり')
    if m=='4刺され':return int(w==4 and s==3)
    return int(w==5)

def get_fr(x,s3,s4,dc,m):
    if m=='4刺され':
        fr,z=feat32(x)
        return {'3スタート先行度':fr['3スタート先行度'],'counter4':z['counter4']}
    return features(x,s3,s4,dc,m)

def eligible(fr,m,c4q3):
    if m=='4刺され':return fr['3スタート先行度']>=.72 and fr['counter4']>=c4q3
    return passes(fr,RULES[m])

def raw_score(x,s3,s4,m):
    if m=='4刺され':
        fr,z=feat32(x);return 100*z['counter4']
    return score_for(x,s3,s4,m)

def tilt_bonus_table(train_rows):
    out={}
    for m in MODELS:
        a=[z for z in train_rows if z['model']==m]
        base=sum(z['y'] for z in a)/len(a) if a else .05
        out[m]={}
        for b in BANDS:
            g=[z for z in a if z['band']==b]
            h=sum(z['y'] for z in g); n=len(g)
            shr=(h+25*base)/(n+25) if n+25 else base
            rel=(shr-base)/max(base,.03)
            pts=max(-3.0,min(3.0,6.0*rel))
            out[m][b]=(pts,n,shr,base)
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
        feats=process_features(d,cache,hist);ymd=d.strftime('%Y/%m/%d');res={r['レースコード']:r for r in rows(f'data/results/realtime/{ymd}.csv')};pay={r['レースコード']:r for r in rows(f'data/results/payouts/{ymd}.csv')};tk={r['レースコード']:r for r in rows(f'data/previews/tkz/{ymd}.csv')}
        for r,x,s4,s5,dc in feats:
            fr32,z32=feat32(x)
            if fr32['3スタート先行度']>=.72:c4vals.append(z32['counter4'])
            s3=score3v4(x)
            for m in MODELS:
                fr=get_fr(x,s3,s4,dc,m)
                if m!='4刺され' and not eligible(fr,m,0):continue
                if m=='4刺され' and fr['3スタート先行度']<.72:continue
                t=tiltval(tk.get(r['レースコード'],{}).get(f'艇{tboat(m)}_チルト')); b=band(t)
                raw.append({'model':m,'score':raw_score(x,s3,s4,m),'band':b,'y':target34(res.get(r['レースコード'],{}),m),'combo':(pay.get(r['レースコード'],{}).get('3連単_組番') or '').strip(),'counter4':fr.get('counter4',0)})
        ingest_prior_day_preview(cache,d);ingest_motor(hist,seen,d);d+=timedelta(days=1)
    c4q3=q(c4vals,.75)
    raw=[z for z in raw if z['model']!='4刺され' or z['counter4']>=c4q3]
    bonuses=tilt_bonus_table(raw)
    train_base={m:[] for m in MODELS};train_tilt={m:[] for m in MODELS};pairs={m:defaultdict(int) for m in MODELS}
    for z in raw:
        m=z['model'];train_base[m].append((z['score'],z['y']));adj=z['score']+bonuses[m].get(z['band'],(0,0,0,0))[0];train_tilt[m].append((adj,z['y']))
        if z['y']:
            k=pair_key(z['combo'])
            if k:pairs[m][k]+=1
    def run_period(start,end,label):
        nonlocal d
        while d<start:
            process_features(d,cache,hist);ingest_prior_day_preview(cache,d);ingest_motor(hist,seen,d);d+=timedelta(days=1)
        races=[];bets=[]
        while d<=end:
            feats=process_features(d,cache,hist);ymd=d.strftime('%Y/%m/%d');ods={r['レースコード']:r for r in rows(f'data/previews/od3/{ymd}.csv')};tk={r['レースコード']:r for r in rows(f'data/previews/tkz/{ymd}.csv')};frozen=[]
            for r,x,s4,s5,dc in feats:
                s3=score3v4(x)
                for m in MODELS:
                    fr=get_fr(x,s3,s4,dc,m)
                    if not eligible(fr,m,c4q3):continue
                    t=tiltval(tk.get(r['レースコード'],{}).get(f'艇{tboat(m)}_チルト'));b=band(t);base_sc=raw_score(x,s3,s4,m);bonus=bonuses[m].get(b,(0,0,0,0))[0]
                    for variant,sc,trset in [('baseline',base_sc,train_base[m]),('tilt',base_sc+bonus,train_tilt[m])]:
                        p=cal_prob(trset,sc);chosen=select_set(HEAD[m],p,ods.get(r['レースコード'],{}),pairs[m])
                        if not chosen:continue
                        allocate(chosen);rr={'period':label,'variant':variant,'model':m,'date':str(d),'race_code':r['レースコード'],'score':round(sc,2),'tilt':t,'tilt_band':b,'tilt_bonus':round(bonus,2),'tickets':len(chosen)};races.append(rr)
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
    with open('races_v34_tilt_compare.csv','w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=sorted(set().union(*(r.keys() for r in races))));w.writeheader();w.writerows(races)
    L=['# v34 チルト補正あり/なし比較','',f'学習 {TR0}〜{TR1} のみでチルト補正値を学習。検証 {VA0}〜{VA1} / 最新月 {TE0}〜{TE1}。実進入不使用。チルトは候補の必須条件にはせず、スコアへ最大±3点の補助補正のみ。','',f'4刺され counter4 学習Q3境界={c4q3:.3f}','', '## 学習チルト補正（点）','|モデル|-0.5以下|0|+0.5|+1.0以上|','|---|---:|---:|---:|---:|']
    for m in MODELS:L.append('|'+m+'|'+'|'.join(f'{bonuses[m][b][0]:+.2f}' for b in BANDS)+'|')
    for label in ['validation','latest_month']:
        L+=['',f'## {label}','|モデル|版|候補R|狙い成立|成立率|3連単的中|的中率|投資|払戻|ROI|','|---|---|---:|---:|---:|---:|---:|---:|---:|---:|']
        for m in MODELS+['合計']:
            for v in ['baseline','tilt']:
                rs=[r for r in races if r['period']==label and r['variant']==v and (m=='合計' or r['model']==m)];bs=[b for b in bets if b['period']==label and b['variant']==v and (m=='合計' or b['model']==m)];n=len(rs);h=sum(r['target_hit'] for r in rs);bh=sum(r['bet_hit'] for r in rs);st=sum(b['stake'] for b in bs);ret=sum(b['return'] for b in bs);L.append(f'|{m}|{v}|{n}|{h}|{100*h/n if n else 0:.1f}%|{bh}|{100*bh/n if n else 0:.1f}%|{st:,}円|{ret:,}円|{100*ret/st if st else 0:.1f}%|')
    open('summary_v34_tilt_compare.md','w',encoding='utf-8').write('\n'.join(L)+'\n')
if __name__=='__main__':main()
