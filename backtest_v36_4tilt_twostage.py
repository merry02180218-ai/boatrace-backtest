import csv
from collections import defaultdict
from backtest_v35_tilt_interaction import *

# v36: 4号艇だけを対象にチルトを2段階化。
# stage1 = tilt>=+0.5 AND 展示ST順位>=0.60
# stage2 = stage1 AND オリジナル展示直線順位>=0.60
# 加点は学習期間だけで決定。実進入/コースは一切使わない。

def stage4(code,tkz,stt,orig):
    tr=tkz.get(code,{}); sr=stt.get(code,{}); orr=orig.get(code,{})
    t=tiltval(tr.get('艇4_チルト'))
    stvals={b:f(sr.get(f'艇{b}_スタート展示')) for b in range(1,7)}
    st=rank_score(stvals,4,True)
    straight=original_scores(orr,4)['straight']
    s1=int(t is not None and t>=0.5 and st>=0.60)
    s2=int(s1 and straight>=0.60)
    return {'tilt4':t,'st4':st,'straight4':straight,'stage1':s1,'stage2':s2}

def learn_stage_bonus(rows0):
    a=[z for z in rows0 if z['model']=='4カドまくり']
    base=sum(z['y'] for z in a)/len(a) if a else .05
    out={}
    for key in ['stage1','stage2']:
        g=[z for z in a if z[key]]; n=len(g); h=sum(z['y'] for z in g)
        shr=(h+30*base)/(n+30) if n+30 else base
        rel=(shr-base)/max(base,.03)
        pts=max(0.0,min(5.0,8.0*rel))
        out[key]=(pts,n,shr,base)
    # stage2はstage1に追加する上乗せ分だけにする
    total2=out['stage2'][0]
    add2=max(0.0,total2-out['stage1'][0])
    return out['stage1'][0],add2,out

def main():
    cache={};hist=defaultdict(list);seen=set();d=PRELOAD_START
    while d<TR0:
        ingest_motor(hist,seen,d)
        if d>=TR0-timedelta(days=12):ingest_prior_day_preview(cache,d)
        d+=timedelta(days=1)

    raw=[];c4vals=[]
    d=TR0
    while d<=TR1:
        feats=process_features(d,cache,hist);ymd=d.strftime('%Y/%m/%d')
        res={r['レースコード']:r for r in rows(f'data/results/realtime/{ymd}.csv')}
        pay={r['レースコード']:r for r in rows(f'data/results/payouts/{ymd}.csv')}
        tkz=by_code(f'data/previews/tkz/{ymd}.csv');stt=by_code(f'data/previews/stt/{ymd}.csv');orig=by_code(f'data/previews/original_exhibition/{ymd}.csv')
        for r,x,s4,s5,dc in feats:
            fr32,z32=feat32(x)
            if fr32['3スタート先行度']>=.72:c4vals.append(z32['counter4'])
            s3=score3v4(x)
            for m in MODELS:
                fr=get_fr(x,s3,s4,dc,m)
                if m!='4刺され' and not eligible(fr,m,0):continue
                if m=='4刺され' and fr['3スタート先行度']<.72:continue
                sg=stage4(r['レースコード'],tkz,stt,orig) if m=='4カドまくり' else {'tilt4':None,'st4':.5,'straight4':.5,'stage1':0,'stage2':0}
                raw.append({'model':m,'score':raw_score(x,s3,s4,m),'y':target34(res.get(r['レースコード'],{}),m),'combo':(pay.get(r['レースコード'],{}).get('3連単_組番') or '').strip(),'counter4':fr.get('counter4',0),**sg})
        ingest_prior_day_preview(cache,d);ingest_motor(hist,seen,d);d+=timedelta(days=1)

    c4q3=qv(c4vals,.75);raw=[z for z in raw if z['model']!='4刺され' or z['counter4']>=c4q3]
    b1,b2,diag=learn_stage_bonus(raw)
    train_base={m:[] for m in MODELS};train_v36={m:[] for m in MODELS};pairs={m:defaultdict(int) for m in MODELS}
    for z in raw:
        m=z['model'];train_base[m].append((z['score'],z['y']))
        adj=z['score']+(b1*z['stage1']+b2*z['stage2'] if m=='4カドまくり' else 0);train_v36[m].append((adj,z['y']))
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
            ods={r['レースコード']:r for r in rows(f'data/previews/od3/{ymd}.csv')};tkz=by_code(f'data/previews/tkz/{ymd}.csv');stt=by_code(f'data/previews/stt/{ymd}.csv');orig=by_code(f'data/previews/original_exhibition/{ymd}.csv');frozen=[]
            for r,x,s4,s5,dc in feats:
                s3=score3v4(x)
                for m in MODELS:
                    fr=get_fr(x,s3,s4,dc,m)
                    if not eligible(fr,m,c4q3):continue
                    sg=stage4(r['レースコード'],tkz,stt,orig) if m=='4カドまくり' else {'tilt4':None,'st4':.5,'straight4':.5,'stage1':0,'stage2':0}
                    base_sc=raw_score(x,s3,s4,m);pts=(b1*sg['stage1']+b2*sg['stage2']) if m=='4カドまくり' else 0
                    for variant,sc,trset in [('baseline',base_sc,train_base[m]),('v36',base_sc+pts,train_v36[m])]:
                        p=cal_prob(trset,sc);chosen=select_set(HEAD[m],p,ods.get(r['レースコード'],{}),pairs[m])
                        if not chosen:continue
                        allocate(chosen);rr={'period':label,'variant':variant,'model':m,'date':str(d),'race_code':r['レースコード'],'score':round(sc,2),'stage1':sg['stage1'],'stage2':sg['stage2'],'tilt4':sg['tilt4'],'st4':round(sg['st4'],2),'straight4':round(sg['straight4'],2),'bonus':round(pts,2)};races.append(rr)
                        for z in chosen:z.update({'period':label,'variant':variant,'model':m,'date':str(d),'race_code':r['レースコード']});frozen.append(z)
            pay={r['レースコード']:r for r in rows(f'data/results/payouts/{ymd}.csv')};res={r['レースコード']:r for r in rows(f'data/results/realtime/{ymd}.csv')}
            for b in frozen:
                pr=pay.get(b['race_code'],{});act=(pr.get('3連単_組番') or '').strip();hit=act==b['combo'];b['hit']=int(hit);b['return']=i(pr.get('3連単_払戻金'))*(b['stake']//100) if hit else 0;bets.append(b)
            for rr in [z for z in races if z['date']==str(d)]:rr['target_hit']=target34(res.get(rr['race_code'],{}),rr['model'])
            ingest_prior_day_preview(cache,d);ingest_motor(hist,seen,d);d+=timedelta(days=1)
        for rr in races:
            bs=[b for b in bets if b['race_code']==rr['race_code'] and b['model']==rr['model'] and b['variant']==rr['variant']];rr['bet_hit']=int(any(b['hit'] for b in bs));rr['return']=sum(b['return'] for b in bs)
        return races,bets

    vr,vb=run_period(VA0,VA1,'validation');tr,tb=run_period(TE0,TE1,'latest_month');races=vr+tr;bets=vb+tb
    with open('races_v36_4tilt_twostage.csv','w',newline='',encoding='utf-8-sig') as f0:
        w=csv.DictWriter(f0,fieldnames=sorted(set().union(*(r.keys() for r in races))));w.writeheader();w.writerows(races)
    L=['# v36 4号艇チルト2段階テスト','',f'学習 {TR0}〜{TR1}。検証 {VA0}〜{VA1} / 最新月 {TE0}〜{TE1}。実進入・コース不使用。','',f'stage1: 4号艇チルト>=+0.5 ＆ 展示ST順位>=0.60。stage2: stage1 ＆ 直線順位>=0.60。','',f'学習加点 stage1=+{b1:.2f}, stage2追加=+{b2:.2f}','', '|段階|学習R|縮小推定成立率|学習ベース率|','|---|---:|---:|---:|']
    for k in ['stage1','stage2']:
        pts,n,shr,base=diag[k];L.append(f'|{k}|{n}|{shr*100:.1f}%|{base*100:.1f}%|')
    for label in ['validation','latest_month']:
        L+=['',f'## {label}','|モデル|版|候補R|stage1 R|stage2 R|狙い成立|成立率|3連単的中|的中率|投資|払戻|ROI|','|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
        for m in MODELS+['合計']:
            for v in ['baseline','v36']:
                rs=[r for r in races if r['period']==label and r['variant']==v and (m=='合計' or r['model']==m)];bs=[b for b in bets if b['period']==label and b['variant']==v and (m=='合計' or b['model']==m)];n=len(rs);s1=sum(r['stage1'] for r in rs);s2=sum(r['stage2'] for r in rs);h=sum(r['target_hit'] for r in rs);bh=sum(r['bet_hit'] for r in rs);st=sum(b['stake'] for b in bs);ret=sum(b['return'] for b in bs);L.append(f'|{m}|{v}|{n}|{s1}|{s2}|{h}|{100*h/n if n else 0:.1f}%|{bh}|{100*bh/n if n else 0:.1f}%|{st:,}円|{ret:,}円|{100*ret/st if st else 0:.1f}%|')
        L+=['',f'### {label} 4カド段階別実績','|段階|R|狙い成立|成立率|','|---|---:|---:|---:|']
        base4=[r for r in races if r['period']==label and r['variant']=='baseline' and r['model']=='4カドまくり']
        groups=[('stage1のみ',[r for r in base4 if r['stage1'] and not r['stage2']]),('stage2',[r for r in base4 if r['stage2']]),('非シグナル',[r for r in base4 if not r['stage1']])]
        for name,g in groups:
            n=len(g);h=sum(r['target_hit'] for r in g);L.append(f'|{name}|{n}|{h}|{100*h/n if n else 0:.1f}%|')
    open('summary_v36_4tilt_twostage.md','w',encoding='utf-8').write('\n'.join(L)+'\n')

if __name__=='__main__':main()
