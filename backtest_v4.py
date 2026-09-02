from backtest import *
from backtest_v3 import CORR, infer_day_from_slots, ingest_motor, motor_hist_strength, expo_rows_to_records
from collections import defaultdict

# v4 adds previous standard exhibition time (tkz) with lane correction,
# makes it an explicit component of stretch/foot evaluation,
# and rebuilds 4->5 around 4 attack + 1/2 resistance + 5's turn-taking.

def clean_name(s): return (s or '').replace('　',' ').strip()

def rank_strength(vals):
    vals=sorted(vals,key=lambda z:z[1]); n=len(vals)
    return {b:1-(k/(n-1) if n>1 else .5) for k,(b,_) in enumerate(vals)}

def ingest_prior_day_preview(cache, day):
    ymd=day.strftime('%Y/%m/%d')
    cards={r['レースコード']:r for r in rows(f'data/programs/race_cards/{ymd}.csv')}
    exmap={r['レースコード']:r for r in rows(f'data/previews/original_exhibition/{ymd}.csv')}
    tkz={r['レースコード']:r for r in rows(f'data/previews/tkz/{ymd}.csv')}
    for code,card in cards.items():
        er=exmap.get(code); tr=tkz.get(code)
        orig={}
        if er:
            recs=expo_rows_to_records([er])
            orig={clean_name(z['name']):z for z in recs}
        tks={}
        if tr:
            vals=[]
            for b in range(1,7):
                raw=tr.get(f'艇{b}_展示タイム','')
                if raw!='': vals.append((b,f(raw,99)+CORR[b]['展示']))
            rs=rank_strength(vals) if vals else {}
            for b,s in rs.items(): tks[clean_name(card.get(f'艇{b}_選手名'))]=s
        venue=str(card.get('レース場コード','')).zfill(2)
        for b in range(1,7):
            name=clean_name(card.get(f'艇{b}_選手名'))
            if not name: continue
            z=orig.get(name,{})
            cache[(venue,name)]={
                'overall':z.get('overall',.5),'turn':z.get('turn',.5),'straight':z.get('straight',.5),
                'display':tks.get(name,.5)
            }

def add_features(x,r,cache,hist):
    venue=str(r.get('レース場コード','')).zfill(2)
    for b in range(1,7):
        z=x[b]; ex=cache.get((venue,clean_name(z['name'])),{})
        z['mhist']=motor_hist_strength(hist,venue,str(r.get(f'艇{b}_モーター番号','')))
        z['pexpo']=ex.get('overall',.5); z['pturn']=ex.get('turn',.5); z['pstraight']=ex.get('straight',.5); z['pdisplay']=ex.get('display',.5)
        # stretch gets explicit prior standard exhibition time contribution
        z['stretch']=clamp(.50*z['pstraight']+.30*z['pdisplay']+.20*z['pexpo'])
        z['turnfoot']=clamp(.65*z['pturn']+.35*z['pexpo'])
        if z['stretch']-z['turnfoot']>=.15: z['ptype']='伸び寄り'
        elif z['turnfoot']-z['stretch']>=.15: z['ptype']='出足・回り足寄り'
        else: z['ptype']='バランス'
    return x

def motor_attack(z):
    return clamp(.45*pct_motor(z['motor2'])+.15*pct_motor(z['motor3'])+.20*z['mhist']+.20*z['stretch'])

def score3v4(x):
    a,b,c=x[1],x[2],x[3]
    st=.55*norm_st_edge(b['waku_st'],c['waku_st'])+.45*norm_st_edge(b['nst'],c['nst'])
    attack=clamp(.55*c['past_win']/.25+.45*(6-c['waku_sr'])/5)
    wall=.55*clamp((5.5-b['waku_wr'])/4.5)+.45*norm_st_edge(b['waku_st'],c['waku_st'])
    meet=.5 if c['meet_st'] is None else clamp((.22-c['meet_st'])/.12)
    response=clamp((7.5-a['waku_wr'])/6)
    context=.6*clamp((c['wr']-3.5)/4)+.4*clamp((c['local']-3)/5)
    return 100*(.20*st+.18*attack+.15*motor_attack(c)+.15*response+.12*wall+.08*meet+.07*c['pexpo']+.05*context)

def score4v4(x):
    a,c,d=x[1],x[3],x[4]
    st=.60*norm_st_edge(c['waku_st'],d['waku_st'])+.40*norm_st_edge(c['nst'],d['nst'])
    attack=clamp(.55*d['past_win']/.25+.45*(6-d['waku_sr'])/5)
    wall=.60*clamp((5.5-c['waku_wr'])/4.5)+.40*norm_st_edge(c['waku_st'],d['waku_st'])
    meet=.5 if d['meet_st'] is None else clamp((.22-d['meet_st'])/.12)
    inside=clamp((7.5-a['waku_wr'])/6)
    context=.6*clamp((d['wr']-3.5)/4)+.4*clamp((d['local']-3)/5)
    return 100*(.22*st+.18*attack+.15*motor_attack(d)+.15*wall+.10*meet+.07*inside+.08*d['pexpo']+.05*context)

def resistance12(x):
    a,b=x[1],x[2]
    r1=.55*clamp(a['waku_wr']/8)+.25*clamp((a['wr']-3)/5)+.20*clamp((.22-a['waku_st'])/.12)
    r2=.45*clamp(b['waku_wr']/7)+.30*clamp((b['wr']-3)/5)+.25*clamp((.22-b['waku_st'])/.12)
    return clamp(.60*r1+.40*r2)

def attack4_component(x,s4):
    c,d=x[3],x[4]
    st=.60*norm_st_edge(c['waku_st'],d['waku_st'])+.40*norm_st_edge(c['nst'],d['nst'])
    wall=.60*clamp((5.5-c['waku_wr'])/4.5)+.40*norm_st_edge(c['waku_st'],d['waku_st'])
    return clamp(.40*(s4/100)+.25*st+.20*wall+.15*d['stretch'])

def score45v4(x,s4):
    d,e=x[4],x[5]
    attack4=attack4_component(x,s4)
    resist=resistance12(x)
    take=clamp(.50*e['turnfoot']+.25*clamp(e['past_win']/.22)+.25*(.55*pct_motor(e['motor2'])+.45*e['mhist']))
    # 5 ST deliberately reduced to 5%; only severe lag is penalized.
    st5=clamp((.10-abs(e['waku_st']-d['waku_st']))/.10)
    return 100*(.45*attack4+.30*resist+.20*take+.05*st5)

def main():
    cache={}; hist=defaultdict(list); seen=set()
    d=START-timedelta(days=35)
    while d<START:
        ingest_motor(hist,seen,d)
        if d>=START-timedelta(days=10): ingest_prior_day_preview(cache,d)
        d+=timedelta(days=1)
    candidates=[]; daily=START
    while daily<=END:
        ymd=daily.strftime('%Y/%m/%d')
        cards=rows(f'data/programs/race_cards/{ymd}.csv')
        w10={r['レースコード']:r for r in rows(f'data/programs/waku10/{ymd}.csv')}
        titles={r['レースコード']:r for r in rows(f'data/programs/title/{ymd}.csv')}
        frozen=[]
        for r in cards:
            code=r['レースコード']; x=add_features(race_features(r,w10.get(code,{})),r,cache,hist)
            s3=score3v4(x); s4=score4v4(x); s45=score45v4(x,s4)
            dn=daynum(titles.get(code,{}).get('日次','')) or infer_day_from_slots(r); dc='初日' if dn==1 else ('2日目' if dn==2 else '3日目以降')
            for model,boat,sc in [('3攻め',3,s3),('4カド',4,s4),('4→5展開',5,s45)]:
                if sc>=60:
                    z=x[boat]
                    frozen.append({'date':str(daily),'race_code':code,'venue':r.get('レース場コード',''),'race':r.get('レース回',''),'day_cat':dc,'model':model,'target_boat':boat,'score':round(sc,2),'rank':label(sc),'target_name':z['name'],'target_grade':z['grade'],'motor2':z['motor2'],'motor_history':round(z['mhist'],3),'prior_expo':round(z['pexpo'],3),'prior_display':round(z['pdisplay'],3),'prior_straight':round(z['pstraight'],3),'prior_turn':round(z['pturn'],3),'stretch_score':round(z['stretch'],3),'turn_score':round(z['turnfoot'],3),'foot_type':z['ptype']})
        res={r['レースコード']:r for r in rows(f'data/results/realtime/{ymd}.csv')}
        for c in frozen:
            rr=res.get(c['race_code'],{}); win=i(rr.get('1着_艇番')); sec=i(rr.get('2着_艇番')); kim=(rr.get('決まり手') or '').replace('　','').replace(' ','')
            c['winner']=win;c['second']=sec;c['kimarite']=kim
            if c['model']=='3攻め': c['head_hit']=int(win==3 and kim in ('まくり','まくり差し'));c['involved_hit']=int(win==3 or sec==3)
            elif c['model']=='4カド': c['head_hit']=int(win==4 and kim in ('まくり','まくり差し'));c['involved_hit']=int(win==4 or sec==4)
            else: c['head_hit']=int(win==5);c['involved_hit']=int(win==5 or sec==5)
            candidates.append(c)
        ingest_prior_day_preview(cache,daily); ingest_motor(hist,seen,daily); daily+=timedelta(days=1)
    with open('candidates_v4.csv','w',newline='',encoding='utf-8-sig') as fo:
        w=csv.DictWriter(fo,fieldnames=list(candidates[0].keys()));w.writeheader();w.writerows(candidates)
    groups=defaultdict(lambda:[0,0,0]); types=defaultdict(lambda:[0,0,0])
    for c in candidates:
        if c['rank'] not in ('S','A'): continue
        for key in [(c['model'],'ALL'),(c['model'],c['day_cat'])]:
            groups[key][0]+=1;groups[key][1]+=c['head_hit'];groups[key][2]+=c['involved_hit']
        tk=(c['model'],c['foot_type']);types[tk][0]+=1;types[tk][1]+=c['head_hit'];types[tk][2]+=c['involved_hit']
    L=['# 2026-08-03〜2026-09-02 バックテスト v4','',
       '前回通常展示タイム(tkz)を枠補正して伸び足へ追加。4→5は 4攻め45%・1/2抵抗30%・5展開取得20%・5ST5% に再設計。候補は結果読み込み前に固定。','',
       '|モデル|日次|候補|頭的中|頭率|2連関与|関与率|','|---|---:|---:|---:|---:|---:|---:|']
    for (m,d),v in sorted(groups.items()):
        n,h,iv=v;L.append(f'|{m}|{d}|{n}|{h}|{h/n*100:.1f}%|{iv}|{iv/n*100:.1f}%|')
    L+=['','## 足質別（S/A）','|モデル|足質|候補|頭率|関与率|','|---|---|---:|---:|---:|']
    for (m,t),v in sorted(types.items()):
        n,h,iv=v;L.append(f'|{m}|{t}|{n}|{h/n*100:.1f}%|{iv/n*100:.1f}%|')
    L+=['','## v4定義','- 伸び足 = 前回直線50% + 補正済み前回通常展示タイム30% + 前回オリジナル展示総合20%。','- 通常展示タイム補正: 1:+0.02, 2:+0.01, 3:0, 4:-0.01, 5:-0.01, 6:-0.02。補正後に同レース内相対順位化。','- 4→5の5STは5%のみ。主因は4カド攻め成立と1/2の抵抗を置いた。']
    open('summary_v4.md','w',encoding='utf-8').write('\n'.join(L)+'\n')
if __name__=='__main__': main()
