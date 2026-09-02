import csv
from collections import defaultdict

CAP_PER_RACE=5000
UNIT=100


def allocate(stakes_rows):
    # Allocate full 5,000 yen per race proportional to positive edge (EV-1),
    # rounded to 100 yen. Minimum 100 yen for every selected ticket.
    by=defaultdict(list)
    for r in stakes_rows:
        by[r['race_code']].append(r)
    out=[]
    for code,rs in by.items():
        n=len(rs)
        if n*UNIT>CAP_PER_RACE:
            # This should not occur with the present v7 selected ticket counts.
            rs=sorted(rs,key=lambda x:float(x['ev_pre']),reverse=True)[:CAP_PER_RACE//UNIT]
            n=len(rs)
        base=n*UNIT
        remain=CAP_PER_RACE-base
        weights=[max(0.0001,float(r['ev_pre'])-1.0) for r in rs]
        sw=sum(weights)
        extras=[0]*n
        if remain>0 and sw>0:
            raw=[remain*w/sw for w in weights]
            extras=[int(x//UNIT)*UNIT for x in raw]
            used=sum(extras)
            left=remain-used
            # distribute remaining 100-yen units by largest fractional remainder
            order=sorted(range(n), key=lambda i:(raw[i]-extras[i]), reverse=True)
            k=0
            while left>=UNIT and order:
                extras[order[k%len(order)]]+=UNIT
                left-=UNIT; k+=1
        for i,r in enumerate(rs):
            z=dict(r); z['stake_v8']=UNIT+extras[i]
            out.append(z)
    return out


def main():
    with open('bets_v7.csv',encoding='utf-8-sig') as f:
        rows=list(csv.DictReader(f))
    bets=allocate(rows)
    for b in bets:
        hit=int(b.get('hit','0') or 0)
        final100=int(float(b.get('payout','0') or 0))
        b['return_v8']=final100*(int(b['stake_v8'])//100) if hit else 0
        b['profit_v8']=int(b['return_v8'])-int(b['stake_v8'])
    with open('bets_v8.csv','w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=list(bets[0].keys()));w.writeheader();w.writerows(bets)

    def agg(bs):
        st=sum(int(x['stake_v8']) for x in bs); ret=sum(int(x['return_v8']) for x in bs)
        hits=sum(int(x.get('hit','0') or 0) for x in bs)
        races=len(set(x['race_code'] for x in bs))
        return races,len(bs),hits,st,ret,(ret/st*100 if st else 0)

    all_codes=set(x['race_code'] for x in bets)
    dual=set()
    by=defaultdict(set)
    for x in bets: by[x['race_code']].add(int(x['head']))
    dual={c for c,s in by.items() if s=={4,5}}

    L=['# 2026-08-03〜2026-09-02 v8 1レース5,000円上限・EV比例配分','',
       'v7の買い目（4/5完全混合・合成オッズ5倍以上）を固定したまま資金配分のみ変更。各買い目最低100円、残額は事前EVの超過分(EV-1)に比例して100円単位で配分。1レース総投資は最大5,000円。結果を見て配分は変更していない。','',
       '|区分|レース数|購入点数|的中|投資|払戻|回収率|','|---|---:|---:|---:|---:|---:|---:|']
    groups=[('全体',bets),('4頭',[x for x in bets if int(x['head'])==4]),('5頭',[x for x in bets if int(x['head'])==5]),('4+5両展開レース',[x for x in bets if x['race_code'] in dual])]
    for name,bs in groups:
        rc,n,h,st,ret,roi=agg(bs);L.append(f'|{name}|{rc}|{n}|{h}|{st:,}円|{ret:,}円|{roi:.1f}%|')
    L+=['','## 日次別','|日次|レース数|投資|払戻|回収率|','|---|---:|---:|---:|---:|']
    for dc in ['初日','2日目','3日目以降']:
        bs=[x for x in bets if x['day_cat']==dc];rc,n,h,st,ret,roi=agg(bs);L.append(f'|{dc}|{rc}|{st:,}円|{ret:,}円|{roi:.1f}%|')
    stakes=defaultdict(int)
    for x in bets: stakes[x['race_code']]+=int(x['stake_v8'])
    L+=['','## 資金配分','- 購入レース数: '+str(len(all_codes)),f'- 最大投資/レース: {max(stakes.values()):,}円',f'- 最小投資/レース: {min(stakes.values()):,}円',f'- 平均投資/レース: {sum(stakes.values())/len(stakes):,.0f}円','- 選定買い目と合成オッズ条件はv7から変更なし。']
    open('summary_v8.md','w',encoding='utf-8').write('\n'.join(L)+'\n')

if __name__=='__main__': main()
