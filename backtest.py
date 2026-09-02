from __future__ import annotations
import csv, io, math, urllib.request
from datetime import date, timedelta
from collections import defaultdict, Counter

BASE='https://raw.githubusercontent.com/BoatraceCSV/boatracecsv.github.io/main/'
START=date(2026,8,3); END=date(2026,9,2)

def fetch(path):
    try:
        with urllib.request.urlopen(BASE+path, timeout=30) as r:
            return r.read().decode('utf-8-sig')
    except Exception:
        return ''

def rows(path):
    s=fetch(path)
    return list(csv.DictReader(io.StringIO(s))) if s else []

def f(x, default=0.0):
    try:return float(x)
    except:return default

def i(x, default=0):
    try:return int(float(x))
    except:return default

def daynum(s):
    mp={'初日':1,'２日目':2,'３日目':3,'４日目':4,'５日目':5,'６日目':6,'７日目':7,'８日目':8,'９日目':9}
    return mp.get((s or '').strip(),0)

def grade_score(g):
    return {'A1':1.0,'A2':0.72,'B1':0.38,'B2':0.15}.get((g or '').strip(),0.3)

def clamp(x,a=0,b=1): return max(a,min(b,x))

def norm_st_edge(inside, outside):
    # positive when outside is faster; +0.05 or more ~ full credit
    return clamp((inside-outside+0.01)/0.06)

def pct_motor(m2):
    return clamp((m2-20)/35)

def past_win_rate(w, boat):
    vals=[]
    for k in range(1,11):
        z=(w.get(f'艇{boat}_過去{k}走_着順') or '').strip()
        if z.isdigit(): vals.append(int(z))
    return sum(v==1 for v in vals)/len(vals) if vals else 0

def recent_meeting_st(r, boat):
    vals=[]
    for d in range(1,8):
      for s in range(1,3):
        x=r.get(f'艇{boat}_節D{d}走{s}_ST','')
        if x!='':
          v=f(x,9)
          if -0.2 < v < 1: vals.append(v)
    if not vals:return None
    return sum(vals[-6:])/len(vals[-6:])

def race_features(r,w):
    out={}
    for b in range(1,7):
        out[b]={
          'name':r.get(f'艇{b}_選手名',''), 'grade':r.get(f'艇{b}_級別',''),
          'nst':f(r.get(f'艇{b}_全国平均ST'),0.20),
          'wr':f(r.get(f'艇{b}_全国勝率'),0),
          'local':f(r.get(f'艇{b}_当地勝率'),0),
          'motor2':f(r.get(f'艇{b}_モーター2連対率'),0),
          'motor3':f(r.get(f'艇{b}_モーター3連対率'),0),
          'waku_st':f(w.get(f'艇{b}_枠番別平均ST'), f(r.get(f'艇{b}_全国平均ST'),0.20)),
          'waku_wr':f(w.get(f'艇{b}_枠番別勝率'),0),
          'waku_sr':f(w.get(f'艇{b}_枠番別平均スタート順'),3.5),
          'past_win':past_win_rate(w,b),
          'meet_st':recent_meeting_st(r,b),
        }
    return out

def score3(x):
    a,b,c=x[1],x[2],x[3]
    st=0.55*norm_st_edge(b['waku_st'],c['waku_st'])+0.45*norm_st_edge(b['nst'],c['nst'])
    attack=clamp(0.55*c['past_win']/0.25 + 0.45*(6-c['waku_sr'])/5)
    # weak wall = low frame winrate and slow ST
    wall=0.55*clamp((5.5-b['waku_wr'])/4.5)+0.45*norm_st_edge(b['waku_st'],c['waku_st'])
    motor=0.7*pct_motor(c['motor2'])+0.3*pct_motor(c['motor3'])
    inside=clamp((7.5-a['waku_wr'])/6.0) # weaker 1 is better for 3-head
    meet=0.5 if c['meet_st'] is None else clamp((0.22-c['meet_st'])/0.12)
    # fixed pre-result model. grade is only light; not a hard B1 condition
    quality=clamp((c['wr']-3.5)/4.0)
    s=100*(.20*st+.18*attack+.15*motor+.15*wall+.10*meet+.08*inside+.09*quality+.05*clamp((c['local']-3)/5))
    return s

def score4(x):
    a,b,c,d,e=x[1],x[2],x[3],x[4],x[5]
    st=0.60*norm_st_edge(c['waku_st'],d['waku_st'])+0.40*norm_st_edge(c['nst'],d['nst'])
    attack=clamp(0.55*d['past_win']/0.25 + 0.45*(6-d['waku_sr'])/5)
    wall=0.60*clamp((5.5-c['waku_wr'])/4.5)+0.40*norm_st_edge(c['waku_st'],d['waku_st'])
    motor=0.7*pct_motor(d['motor2'])+0.3*pct_motor(d['motor3'])
    meet=0.5 if d['meet_st'] is None else clamp((0.22-d['meet_st'])/0.12)
    inside=clamp((7.5-a['waku_wr'])/6.0)
    quality=clamp((d['wr']-3.5)/4.0)
    s=100*(.22*st+.18*attack+.15*motor+.15*wall+.10*meet+.07*inside+.08*quality+.05*clamp((d['local']-3)/5))
    return s

def score45(x, s4):
    d,e=x[4],x[5]
    follow=clamp((0.04-abs(e['waku_st']-d['waku_st']))/0.04)
    emotor=0.7*pct_motor(e['motor2'])+0.3*pct_motor(e['motor3'])
    eturn=clamp(e['past_win']/0.22)
    return 0.48*s4+100*(.24*follow+.16*emotor+.12*eturn)

def label(s):
    if s>=80:return 'S'
    if s>=70:return 'A'
    if s>=60:return 'B'
    return 'C'

def main():
    candidates=[]; all_actual=Counter(); daily=START
    while daily<=END:
        ymd=daily.strftime('%Y/%m/%d')
        cards=rows(f'data/programs/race_cards/{ymd}.csv')
        w10={r['レースコード']:r for r in rows(f'data/programs/waku10/{ymd}.csv')}
        titles={r['レースコード']:r for r in rows(f'data/programs/title/{ymd}.csv')}
        # IMPORTANT: scores are frozen here, before results are loaded
        frozen=[]
        for r in cards:
            code=r['レースコード']; w=w10.get(code,{})
            x=race_features(r,w); s3=score3(x); s4=score4(x); s45=score45(x,s4)
            dn=daynum(titles.get(code,{}).get('日次',''))
            daycat='初日' if dn==1 else ('2日目' if dn==2 else ('3日目以降' if dn>=3 else '不明'))
            for model,boat,sc in [('3攻め',3,s3),('4カド',4,s4),('4→5展開',5,s45)]:
                if sc>=60:
                    frozen.append({'date':str(daily),'race_code':code,'venue':r.get('レース場コード',''),'race':r.get('レース回',''),'day_no':dn,'day_cat':daycat,'model':model,'target_boat':boat,'score':round(sc,2),'rank':label(sc),'target_name':x[boat]['name'],'target_grade':x[boat]['grade'],'motor2':x[boat]['motor2'],'target_waku_st':x[boat]['waku_st']})
        # only now load outcomes
        res={r['レースコード']:r for r in rows(f'data/results/realtime/{ymd}.csv')}
        for rr in res.values():
            win=i(rr.get('1着_艇番')) ; kim=(rr.get('決まり手') or '').replace('　','').replace(' ','')
            if win==3 and kim in ('まくり','まくり差し'): all_actual['3攻め']+=1
            if win==4 and kim in ('まくり','まくり差し'): all_actual['4カド']+=1
            if win==5: all_actual['4→5展開']+=1
        for c in frozen:
            rr=res.get(c['race_code'],{})
            win=i(rr.get('1着_艇番')); second=i(rr.get('2着_艇番')); kim=(rr.get('決まり手') or '').replace('　','').replace(' ','')
            tb=c['target_boat']
            c['winner']=win; c['second']=second; c['kimarite']=kim
            if c['model']=='3攻め':
                c['head_hit']=int(win==3 and kim in ('まくり','まくり差し'))
                c['involved_hit']=int(win==3 or second==3)
            elif c['model']=='4カド':
                c['head_hit']=int(win==4 and kim in ('まくり','まくり差し'))
                c['involved_hit']=int(win==4 or second==4)
            else:
                c['head_hit']=int(win==5)
                c['involved_hit']=int(win==5 or second==5)
            candidates.append(c)
        daily+=timedelta(days=1)

    fields=list(candidates[0].keys()) if candidates else []
    with open('candidates.csv','w',newline='',encoding='utf-8-sig') as f1:
        w=csv.DictWriter(f1,fieldnames=fields);w.writeheader();w.writerows(candidates)

    groups=defaultdict(lambda: [0,0,0])
    for c in candidates:
        if c['rank'] not in ('S','A'): continue
        for key in [(c['model'],'ALL'),(c['model'],c['day_cat']),(c['model']+'_'+c['rank'],c['day_cat'])]:
            groups[key][0]+=1;groups[key][1]+=c['head_hit'];groups[key][2]+=c['involved_hit']
    lines=['# 2026-08-03〜2026-09-02 事前固定バックテスト','',
           '候補スコアは結果CSVを読み込む前に固定。S/Aのみ主要集計。','',
           '|モデル|開催日次|候補数|頭的中|頭的中率|2連関与|関与率|','|---|---:|---:|---:|---:|---:|---:|']
    for (m,d),v in sorted(groups.items()):
        n,h,iv=v
        lines.append(f'|{m}|{d}|{n}|{h}|{h/n*100:.1f}%|{iv}|{iv/n*100:.1f}%|')
    lines += ['', '## 実際の発生数（期間全体）']
    for k,v in all_actual.items():lines.append(f'- {k}: {v}')
    lines += ['', '## 注意', '- 「4→5展開」は結果CSVに4号艇が攻めたかの直接ラベルがないため、5号艇1着を頭的中としている。', '- モーターの「伸び型/出足型」は公開日次CSVだけでは直接ラベル化されていないため、この第1回テストではモーター2/3連率を事前機力として使用。足質は次段階でmotor_history/前走オリジナル展示を追加する。', '- 1号艇の「張る/締める」も結果CSVに直接ラベルがないため、この第1回テストでは1枠Waku10勝率を防御力代理指標としている。']
    open('summary.md','w',encoding='utf-8').write('\n'.join(lines)+'\n')

if __name__=='__main__': main()
