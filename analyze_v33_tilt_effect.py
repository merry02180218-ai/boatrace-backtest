from analyze_v30_highjump_outerrisk import *
from collections import defaultdict

START=date(2026,6,1); END=date(2026,9,2)

def tiltval(v):
    try:return float(str(v).replace('度','').replace('+','').strip())
    except:return None

def band(t):
    if t is None:return '欠損'
    if t<=-.5:return '-0.5以下'
    if t<.5:return '0'
    if t<1.0:return '+0.5'
    return '+1.0以上'

def main():
    cache={};hist=defaultdict(list);seen=set();d=PRELOAD_START
    while d<START:
        ingest_motor(hist,seen,d)
        if d>=START-timedelta(days=12):ingest_prior_day_preview(cache,d)
        d+=timedelta(days=1)
    rec=[];prev={}
    while d<=END:
        feats=process_features(d,cache,hist);ymd=d.strftime('%Y/%m/%d')
        tk={r['レースコード']:r for r in rows(f'data/previews/tkz/{ymd}.csv')}
        res={r['レースコード']:r for r in rows(f'data/results/realtime/{ymd}.csv')}
        for r,x,s4,s5,dc in feats:
            code=r['レースコード']; rr=res.get(code,{}); w=i(rr.get('1着_艇番')); kim=(rr.get('決まり手') or '').replace(' ','').replace('　','')
            row=tk.get(code,{})
            for boat in (3,4,5):
                t=tiltval(row.get(f'艇{boat}_チルト'))
                racer=str(x[boat].get('racer','') or x[boat].get('選手登録番号',''))
                p=prev.get(racer); delta=None if t is None or p is None else t-p
                rec.append({'date':str(d),'race_code':code,'boat':boat,'tilt':t,'band':band(t),'delta':delta,
                    'up':int(delta is not None and delta>0),'down':int(delta is not None and delta<0),'same':int(delta==0) if delta is not None else 0,
                    'win':int(w==boat),'makuri':int(w==boat and kim=='まくり'),'ms':int(w==boat and kim=='まくり差し'),
                    'attack':int(w==boat and kim in ('まくり','まくり差し')),'stfast':fastx(x[boat]),'strength':sx(x[boat]),
                    'turn':c01x(x[boat]['turnfoot']),'stretch':c01x(x[boat]['stretch'])})
                if t is not None and racer:prev[racer]=t
        ingest_prior_day_preview(cache,d);ingest_motor(hist,seen,d);d+=timedelta(days=1)
    import csv
    with open('analysis_v33_tilt_effect.csv','w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=list(rec[0].keys()));w.writeheader();w.writerows(rec)
    def rate(a,k):return 100*sum(z[k] for z in a)/len(a) if a else 0
    L=['# v33 チルト角度・変更効果解析','',f'期間 {START}〜{END}。実進入不使用。チルトは締切前の展示情報として使用。前回値が取得できる場合は変更方向も集計。','']
    for boat in (3,4,5):
        a=[z for z in rec if z['boat']==boat and z['tilt'] is not None]
        L += [f'## {boat}号艇 チルト絶対値','|チルト|R|1着|まくり|まくり差し|攻め合計|','|---|---:|---:|---:|---:|---:|']
        for b in ['-0.5以下','0','+0.5','+1.0以上']:
            g=[z for z in a if z['band']==b];L.append(f'|{b}|{len(g)}|{rate(g,"win"):.1f}%|{rate(g,"makuri"):.1f}%|{rate(g,"ms"):.1f}%|{rate(g,"attack"):.1f}%|')
        L += ['',f'## {boat}号艇 チルト変更','|変更|R|1着|まくり|まくり差し|攻め合計|','|---|---:|---:|---:|---:|---:|']
        for name,fn in [('上げ',lambda z:z['up']),('据置',lambda z:z['same']),('下げ',lambda z:z['down'])]:
            g=[z for z in a if z['delta'] is not None and fn(z)];L.append(f'|{name}|{len(g)}|{rate(g,"win"):.1f}%|{rate(g,"makuri"):.1f}%|{rate(g,"ms"):.1f}%|{rate(g,"attack"):.1f}%|')
        L.append('')
    open('summary_v33_tilt_effect.md','w',encoding='utf-8').write('\n'.join(L)+'\n')
if __name__=='__main__':main()
