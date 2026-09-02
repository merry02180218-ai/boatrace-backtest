from backtest import *
from backtest_v3 import ingest_motor, infer_day_from_slots
from backtest_v4 import ingest_prior_day_preview, add_features, score4v4, score45v4, resistance12, attack4_component
from collections import defaultdict
from datetime import date,timedelta

TARGET=date(2026,9,2)

def odds_head_share(od3, head):
    ws=[]; allw=[]
    for a in range(1,7):
      for b in range(1,7):
        if b==a: continue
        for c in range(1,7):
          if c in (a,b): continue
          o=f(od3.get(f'3連単_{a}-{b}-{c}'),0)
          if o>0:
            w=1/o; allw.append((a,w));
            if a==head: ws.append(w)
    den=sum(w for _,w in allw)
    return sum(ws)/den if den else 0

def top_combos(od3,head,n=5):
    arr=[]
    for b in range(1,7):
      if b==head: continue
      for c in range(1,7):
        if c in (head,b): continue
        o=f(od3.get(f'3連単_{head}-{b}-{c}'),0)
        if o>0: arr.append((o,f'{head}-{b}-{c}'))
    arr.sort(reverse=True) # high odds for value browsing
    return arr[:n]

def main():
    cache={}; hist=defaultdict(list); seen=set()
    d=TARGET-timedelta(days=45)
    while d<TARGET:
        ingest_motor(hist,seen,d)
        if d>=TARGET-timedelta(days=14): ingest_prior_day_preview(cache,d)
        d+=timedelta(days=1)
    ymd=TARGET.strftime('%Y/%m/%d')
    cards=rows(f'data/programs/race_cards/{ymd}.csv')
    w10={r['レースコード']:r for r in rows(f'data/programs/waku10/{ymd}.csv')}
    titles={r['レースコード']:r for r in rows(f'data/programs/title/{ymd}.csv')}
    od3={r['レースコード']:r for r in rows(f'data/previews/od3/{ymd}.csv')}
    res={r['レースコード']:r for r in rows(f'data/results/realtime/{ymd}.csv')}
    out=[]
    for r in cards:
        code=r['レースコード']; x=add_features(race_features(r,w10.get(code,{})),r,cache,hist)
        s4=score4v4(x); s5=score45v4(x,s4)
        if max(s4,s5)<60: continue
        o=od3.get(code,{})
        p4=odds_head_share(o,4); p5=odds_head_share(o,5)
        rr=res.get(code,{})
        attack=attack4_component(x,s4); resist=resistance12(x)
        # Scenario-value index: score relative to market head share. Not a calibrated EV/probability.
        v4=s4/(100*p4) if p4>0 else 0; v5=s5/(100*p5) if p5>0 else 0
        out.append({'race_code':code,'venue':r.get('レース場コード',''),'race':r.get('レース回',''),
          'boat4':x[4]['name'],'boat5':x[5]['name'],'s4':round(s4,1),'s5':round(s5,1),
          'attack4':round(attack,3),'resist12':round(resist,3),'4stretch':round(x[4]['stretch'],3),'5turn':round(x[5]['turnfoot'],3),
          'market4_head':round(p4,4),'market5_head':round(p5,4),'value_index4':round(v4,2),'value_index5':round(v5,2),
          'winner':i(rr.get('1着_艇番')),'second':i(rr.get('2着_艇番')),'third':i(rr.get('3着_艇番')),'kimarite':(rr.get('決まり手') or '').replace('　','').replace(' ',''),
          'top4_longshots':' / '.join(f'{c}@{o:.1f}' for o,c in top_combos(o,4,3)),
          'top5_longshots':' / '.join(f'{c}@{o:.1f}' for o,c in top_combos(o,5,3))})
    out.sort(key=lambda z:max(z['value_index4'],z['value_index5']),reverse=True)
    import csv
    with open('yesterday_v4.csv','w',newline='',encoding='utf-8-sig') as f1:
        w=csv.DictWriter(f1,fieldnames=list(out[0].keys()));w.writeheader();w.writerows(out)
    L=['# 2026-09-02 4攻め→4頭/5頭 両シナリオ試算','',
       'v4事前情報のみで4頭スコアと5頭スコアを算出し、締切約5分前の3連単集計中オッズから4頭/5頭の市場シェアを算出。value_indexはスコア÷市場head shareで、未校正の比較指標（EVそのものではない）。結果は最後に照合。','',
       '|場|R|4号艇|5号艇|4頭score|5頭score|4攻め|1/2抵抗|市場4頭|市場5頭|V4|V5|結果|','|---|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|']
    for z in out[:20]:
        L.append(f"|{z['venue']}|{z['race']}|{z['boat4']}|{z['boat5']}|{z['s4']:.1f}|{z['s5']:.1f}|{z['attack4']:.3f}|{z['resist12']:.3f}|{z['market4_head']*100:.1f}%|{z['market5_head']*100:.1f}%|{z['value_index4']:.2f}|{z['value_index5']:.2f}|{z['winner']}-{z['second']}-{z['third']} {z['kimarite']}|")
    open('yesterday_v4.md','w',encoding='utf-8').write('\n'.join(L)+'\n')
if __name__=='__main__':main()
