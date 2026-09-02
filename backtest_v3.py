from backtest import *
from datetime import datetime
import re

# v3: prior original exhibition + historical motor sections. No current-race exhibition is used.
CORR={
  1:{'展示':.02,'一周':.40,'まわり足':.20,'回り足':.20,'直線':.00},
  2:{'展示':.01,'一周':.30,'まわり足':.10,'回り足':.10,'直線':.00},
  3:{'展示':.00,'一周':.20,'まわり足':.00,'回り足':.00,'直線':.00},
  4:{'展示':-.01,'一周':.10,'まわり足':-.05,'回り足':-.05,'直線':-.01},
  5:{'展示':-.01,'一周':.05,'まわり足':-.10,'回り足':-.10,'直線':-.02},
  6:{'展示':-.02,'一周':.00,'まわり足':-.15,'回り足':-.15,'直線':-.02},
}
EW={'展示':.252,'一周':.407,'まわり足':.412,'回り足':.412,'直線':.134}

def infer_day_from_slots(r):
    maxd=0
    for b in range(1,7):
        for d in range(1,8):
            if any((r.get(f'艇{b}_節D{d}走{s}_R番号') or '').strip() for s in range(1,3)):
                maxd=max(maxd,d)
    return maxd+1 if maxd else 1

def expo_rows_to_records(exrows):
    out=[]
    for r in exrows:
        metrics=[]
        for j in range(1,5):
            m=(r.get(f'計測項目{j}') or '').strip()
            if m: metrics.append((j,m))
        if not metrics: continue
        strengths={b:{} for b in range(1,7)}
        for j,m in metrics:
            vals=[]
            for b in range(1,7):
                raw=r.get(f'艇{b}_値{j}','')
                if raw!='': vals.append((b,f(raw,999)+CORR[b].get(m,0)))
            vals.sort(key=lambda z:z[1])
            n=len(vals)
            for rank,(b,v) in enumerate(vals):
                strengths[b][m]=1-(rank/(n-1) if n>1 else .5)
        for b in range(1,7):
            sm=strengths[b]
            if not sm: continue
            ww=sum(EW.get(m,0) for m in sm)
            overall=sum(EW.get(m,0)*v for m,v in sm.items())/ww if ww else .5
            turn=[]
            for m in ('一周','まわり足','回り足'):
                if m in sm: turn.append(sm[m])
            turn_s=sum(turn)/len(turn) if turn else overall
            straight=sm.get('直線',overall)
            if straight-turn_s>=.18: typ='伸び寄り'
            elif turn_s-straight>=.18: typ='出足・回り足寄り'
            else: typ='バランス'
            out.append({'venue':str(r.get('レース場','')).zfill(2),'date':r.get('レース日',''),
                        'name':(r.get(f'艇{b}_選手名') or '').replace('　',' ').strip(),
                        'overall':overall,'turn':turn_s,'straight':straight,'type':typ})
    return out

def ingest_expo(cache, day):
    ymd=day.strftime('%Y/%m/%d')
    for z in expo_rows_to_records(rows(f'data/previews/original_exhibition/{ymd}.csv')):
        cache[(z['venue'],z['name'])]=z

def ingest_motor(hist, seen, day):
    ymd=day.strftime('%Y/%m/%d')
    for r in rows(f'data/programs/motor_history/{ymd}.csv'):
        key=(str(r.get('場コード','')).zfill(2),str(r.get('モーター番号','')),r.get('使用開始日',''),r.get('使用終了日',''),r.get('使用者名',''))
        if key in seen: continue
        seen.add(key)
        digs=[int(x) for x in re.findall(r'[1-6１-６]', (r.get('着順列') or '').translate(str.maketrans('１２３４５６','123456')))]
        pts={1:1,2:.78,3:.58,4:.36,5:.18,6:0}
        strength=sum(pts[x] for x in digs)/len(digs) if digs else .5
        hist[(key[0],key[1])].append((r.get('使用終了日',''),strength))

def motor_hist_strength(hist,venue,motor):
    a=sorted(hist.get((str(venue).zfill(2),str(motor)),[]),reverse=True)[:4]
    if not a:return .5
    ws=[1,.75,.55,.4][:len(a)]
    return sum(w*x[1] for w,x in zip(ws,a))/sum(ws)

def prior_expo(cache,venue,name):
    return cache.get((str(venue).zfill(2),(name or '').replace('　',' ').strip()))

def add_v3_features(x,r,cache,hist):
    venue=str(r.get('レース場コード','')).zfill(2)
    for b in range(1,7):
        motor=str(r.get(f'艇{b}_モーター番号',''))
        x[b]['mhist']=motor_hist_strength(hist,venue,motor)
        ex=prior_expo(cache,venue,x[b]['name'])
        x[b]['pexpo']=ex['overall'] if ex else .5
        x[b]['pturn']=ex['turn'] if ex else .5
        x[b]['pstraight']=ex['straight'] if ex else .5
        x[b]['ptype']=ex['type'] if ex else '不明'
    return x

def motor_mix(z,attack=True):
    base=.55*pct_motor(z['motor2'])+.20*pct_motor(z['motor3'])+.25*z['mhist']
    if attack:
        if z['ptype']=='伸び寄り': base+=.08
        elif z['ptype']=='出足・回り足寄り': base-=.02
    return clamp(base)

def score3v3(x):
    a,b,c=x[1],x[2],x[3]
    st=.55*norm_st_edge(b['waku_st'],c['waku_st'])+.45*norm_st_edge(b['nst'],c['nst'])
    attack=clamp(.55*c['past_win']/.25+.45*(6-c['waku_sr'])/5)
    wall=.55*clamp((5.5-b['waku_wr'])/4.5)+.45*norm_st_edge(b['waku_st'],c['waku_st'])
    meet=.5 if c['meet_st'] is None else clamp((.22-c['meet_st'])/.12)
    response=clamp((7.5-a['waku_wr'])/6)
    context=.6*clamp((c['wr']-3.5)/4)+.4*clamp((c['local']-3)/5)
    return 100*(.20*st+.18*attack+.15*motor_mix(c)+.15*response+.12*wall+.08*meet+.07*c['pexpo']+.05*context)

def score4v3(x):
    a,c,d=x[1],x[3],x[4]
    st=.60*norm_st_edge(c['waku_st'],d['waku_st'])+.40*norm_st_edge(c['nst'],d['nst'])
    attack=clamp(.55*d['past_win']/.25+.45*(6-d['waku_sr'])/5)
    wall=.60*clamp((5.5-c['waku_wr'])/4.5)+.40*norm_st_edge(c['waku_st'],d['waku_st'])
    meet=.5 if d['meet_st'] is None else clamp((.22-d['meet_st'])/.12)
    inside=clamp((7.5-a['waku_wr'])/6)
    context=.6*clamp((d['wr']-3.5)/4)+.4*clamp((d['local']-3)/5)
    return 100*(.22*st+.18*attack+.15*motor_mix(d)+.15*wall+.10*meet+.07*inside+.08*d['pexpo']+.05*context)

def score45v3(x,s4):
    d,e=x[4],x[5]
    follow=clamp((.04-abs(e['waku_st']-d['waku_st']))/.04)
    efoot=.55*motor_mix(e,False)+.45*e['pturn']
    return .50*s4+100*(.23*follow+.17*efoot+.10*clamp(e['past_win']/.22))

def branch(model,z):
    if model=='4→5展開': return '4攻め→5展開'
    if z['ptype']=='伸び寄り': return 'まくり寄り'
    if z['ptype']=='出足・回り足寄り': return 'まくり差し寄り'
    return '両にらみ'

def main():
    cache={}; hist=defaultdict(list); seen=set()
    # preload only information that existed before test start
    d=START-timedelta(days=35)
    while d<START:
        ingest_motor(hist,seen,d)
        if d>=START-timedelta(days=10): ingest_expo(cache,d)
        d+=timedelta(days=1)
    candidates=[]; daily=START
    while daily<=END:
        # At this point cache contains prior dates only; current exhibition is never loaded before scoring.
        ymd=daily.strftime('%Y/%m/%d')
        cards=rows(f'data/programs/race_cards/{ymd}.csv')
        w10={r['レースコード']:r for r in rows(f'data/programs/waku10/{ymd}.csv')}
        titles={r['レースコード']:r for r in rows(f'data/programs/title/{ymd}.csv')}
        frozen=[]
        for r in cards:
            code=r['レースコード']; x=add_v3_features(race_features(r,w10.get(code,{})),r,cache,hist)
            s3=score3v3(x); s4=score4v3(x); s45=score45v3(x,s4)
            dn=daynum(titles.get(code,{}).get('日次','')) or infer_day_from_slots(r)
            dc='初日' if dn==1 else ('2日目' if dn==2 else '3日目以降')
            for model,boat,sc in [('3攻め',3,s3),('4カド',4,s4),('4→5展開',5,s45)]:
                if sc>=60:
                    z=x[boat]
                    frozen.append({'date':str(daily),'race_code':code,'venue':r.get('レース場コード',''),'race':r.get('レース回',''),'day_no':dn,'day_cat':dc,'model':model,'target_boat':boat,'score':round(sc,2),'rank':label(sc),'target_name':z['name'],'target_grade':z['grade'],'motor2':z['motor2'],'motor_history':round(z['mhist'],3),'prior_expo':round(z['pexpo'],3),'prior_turn':round(z['pturn'],3),'prior_straight':round(z['pstraight'],3),'foot_type':z['ptype'],'branch':branch(model,z)})
        # only after freezing all candidates load results
        res={r['レースコード']:r for r in rows(f'data/results/realtime/{ymd}.csv')}
        for c in frozen:
            rr=res.get(c['race_code'],{}); win=i(rr.get('1着_艇番')); sec=i(rr.get('2着_艇番')); kim=(rr.get('決まり手') or '').replace('　','').replace(' ','')
            c['winner']=win;c['second']=sec;c['kimarite']=kim
            if c['model']=='3攻め': c['head_hit']=int(win==3 and kim in ('まくり','まくり差し'));c['involved_hit']=int(win==3 or sec==3)
            elif c['model']=='4カド': c['head_hit']=int(win==4 and kim in ('まくり','まくり差し'));c['involved_hit']=int(win==4 or sec==4)
            else: c['head_hit']=int(win==5);c['involved_hit']=int(win==5 or sec==5)
            candidates.append(c)
        # now today becomes prior information for tomorrow
        ingest_expo(cache,daily); ingest_motor(hist,seen,daily)
        daily+=timedelta(days=1)
    with open('candidates_v3.csv','w',newline='',encoding='utf-8-sig') as fo:
        w=csv.DictWriter(fo,fieldnames=list(candidates[0].keys()));w.writeheader();w.writerows(candidates)
    groups=defaultdict(lambda:[0,0,0])
    types=defaultdict(lambda:[0,0,0])
    for c in candidates:
        if c['rank'] not in ('S','A'): continue
        for key in [(c['model'],'ALL'),(c['model'],c['day_cat']),(c['model']+'_'+c['rank'],c['day_cat'])]:
            groups[key][0]+=1;groups[key][1]+=c['head_hit'];groups[key][2]+=c['involved_hit']
        tk=(c['model'],c['foot_type']);types[tk][0]+=1;types[tk][1]+=c['head_hit'];types[tk][2]+=c['involved_hit']
    L=['# 2026-08-03〜2026-09-02 バックテスト v3','',
       '結果を読む前に候補固定。現在レースの展示は不使用。前日以前のオリジナル展示を枠補正し、一周40.7%・回り足41.2%・展示25.2%・直線13.4%の相対重みで評価。モーターは2/3連率に過去節着順履歴を加え、前走展示から伸び寄り/出足・回り足寄りを推定。','',
       '|モデル|日次|候補|頭的中|頭率|2連関与|関与率|','|---|---:|---:|---:|---:|---:|---:|']
    for (m,d),v in sorted(groups.items()):
        n,h,iv=v;L.append(f'|{m}|{d}|{n}|{h}|{h/n*100:.1f}%|{iv}|{iv/n*100:.1f}%|')
    L+=['','## 足質別（S/A候補）','|モデル|推定足質|候補|頭的中率|2連関与率|','|---|---|---:|---:|---:|']
    for (m,t),v in sorted(types.items()):
        n,h,iv=v;L.append(f'|{m}|{t}|{n}|{h/n*100:.1f}%|{iv/n*100:.1f}%|')
    L+=['','## 注意','- 足質は専門紙コメントの直接ラベルではなく、前日以前の枠補正済みオリジナル展示における直線 vs 一周/回り足の相対順位から推定。','- 4→5は結果CSVに「4が攻めた」ラベルがないため、5号艇1着/2連関与を代理目的変数としている。','- 1号艇の張る/締めるはWaku10の1枠勝率を代理にしており、映像確認は未実装。']
    open('summary_v3.md','w',encoding='utf-8').write('\n'.join(L)+'\n')

if __name__=='__main__': main()
