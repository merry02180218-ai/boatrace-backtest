from backtest import *
from backtest_v4 import ingest_prior_day_preview, score3v4, motor_attack
from backtest_v3 import ingest_motor
from backtest_v5_ev import PRELOAD_START, process_features
from collections import defaultdict
from datetime import date, timedelta
import csv, math

START=date(2026,6,1)
END=date(2026,9,2)
PERIODS=[
    ('学習',date(2026,6,1),date(2026,7,15)),
    ('確認',date(2026,7,16),date(2026,8,2)),
    ('直近1か月',date(2026,8,3),date(2026,9,2)),
]


def c01(v): return max(0.0,min(1.0,v))

def safe_st(v):
    return .22 if v is None else v

def feature_row(x,s3,dc):
    a,b,c=x[1],x[2],x[3]
    st_edge=.55*norm_st_edge(b['waku_st'],c['waku_st'])+.45*norm_st_edge(b['nst'],c['nst'])
    attack3=c01(.55*c['past_win']/.25+.45*(6-c['waku_sr'])/5)
    wallweak=.55*c01((5.5-b['waku_wr'])/4.5)+.45*norm_st_edge(b['waku_st'],c['waku_st'])
    insideweak=c01((7.5-a['waku_wr'])/6)
    meet=.5 if c['meet_st'] is None else c01((.22-c['meet_st'])/.12)
    context=.6*c01((c['wr']-3.5)/4)+.4*c01((c['local']-3)/5)
    # Direct/raw features are kept as well; sign is interpreted later.
    return {
        'score3':s3,
        '3_ST優位':st_edge,
        '3コース攻撃実績':attack3,
        '2壁弱さ':wallweak,
        '1弱さ':insideweak,
        '3モーター攻撃':motor_attack(c),
        '3伸び':c['stretch'],
        '3回り足':c['turnfoot'],
        '3前回展示総合':c['pexpo'],
        '3前回直線':c['pstraight'],
        '3前回通常展示':c['pdisplay'],
        '3前回回り足':c['pturn'],
        '3節間ST':meet,
        '3選手力':context,
        '3全国勝率':c['wr'],
        '3当地勝率':c['local'],
        '3コース1着率':c['waku_wr'],
        '3コースST_速いほど高':c01((.22-safe_st(c['waku_st']))/.12),
        '3全国ST_速いほど高':c01((.22-safe_st(c['nst']))/.12),
        '1コース1着率_低いほど高':c01((8.0-a['waku_wr'])/8.0),
        '1コースST_遅いほど高':c01((safe_st(a['waku_st'])-.08)/.16),
        '2コース1着率_低いほど高':c01((7.0-b['waku_wr'])/7.0),
        '2コースST_遅いほど高':c01((safe_st(b['waku_st'])-.08)/.16),
        '3日目以降':1.0 if dc=='3日目以降' else 0.0,
    }


def pearson(xs,ys):
    n=len(xs)
    if n<3:return 0.0
    mx=sum(xs)/n; my=sum(ys)/n
    vx=sum((x-mx)**2 for x in xs); vy=sum((y-my)**2 for y in ys)
    if vx<=0 or vy<=0:return 0.0
    return sum((x-mx)*(y-my) for x,y in zip(xs,ys))/math.sqrt(vx*vy)


def quantile(vs,q):
    if not vs:return 0
    a=sorted(vs); pos=(len(a)-1)*q; lo=int(pos); hi=min(lo+1,len(a)-1); w=pos-lo
    return a[lo]*(1-w)+a[hi]*w


def stats(rows_,feat):
    vals=[r[feat] for r in rows_]; ys=[r['target'] for r in rows_]
    corr=pearson(vals,ys)
    hit=[r[feat] for r in rows_ if r['target']]; miss=[r[feat] for r in rows_ if not r['target']]
    hm=sum(hit)/len(hit) if hit else 0; mm=sum(miss)/len(miss) if miss else 0
    q25=quantile(vals,.25); q75=quantile(vals,.75)
    low=[r for r in rows_ if r[feat]<=q25]; high=[r for r in rows_ if r[feat]>=q75]
    lr=sum(r['target'] for r in low)/len(low) if low else 0
    hr=sum(r['target'] for r in high)/len(high) if high else 0
    lift=(hr/lr if lr>0 else (999 if hr>0 else 1))
    return {'corr':corr,'hit_mean':hm,'miss_mean':mm,'low_rate':lr,'high_rate':hr,'lift':lift,'n':len(rows_),'hits':sum(ys)}


def main():
    cache={}; hist=defaultdict(list); seen=set(); d=PRELOAD_START
    while d<START:
        ingest_motor(hist,seen,d)
        if d>=START-timedelta(days=12): ingest_prior_day_preview(cache,d)
        d+=timedelta(days=1)

    allrows=[]; d=START
    while d<=END:
        feats=process_features(d,cache,hist); ymd=d.strftime('%Y/%m/%d')
        res={r['レースコード']:r for r in rows(f'data/results/realtime/{ymd}.csv')}
        for r,x,s4,s5,dc in feats:
            s3=score3v4(x); rr=res.get(r['レースコード'],{})
            win=i(rr.get('1着_艇番')); kim=(rr.get('決まり手') or '').replace('　','').replace(' ','')
            z={'date':str(d),'race_code':r['レースコード'],'venue':r.get('レース場コード',''),'race':r.get('レース回',''),'day_cat':dc,'winner':win,'kimarite':kim,'target':int(win==3 and kim in ('まくり','まくり差し'))}
            z.update(feature_row(x,s3,dc)); allrows.append(z)
        ingest_prior_day_preview(cache,d); ingest_motor(hist,seen,d); d+=timedelta(days=1)

    if allrows:
        with open('analysis_3attack_rows.csv','w',newline='',encoding='utf-8-sig') as f:
            w=csv.DictWriter(f,fieldnames=list(allrows[0].keys())); w.writeheader(); w.writerows(allrows)

    feats=[k for k in allrows[0].keys() if k not in ('date','race_code','venue','race','day_cat','winner','kimarite','target')]
    per={}
    for name,lo,hi in PERIODS:
        rs=[r for r in allrows if lo<=date.fromisoformat(r['date'])<=hi]
        per[name]={'rows':rs,'stats':{f:stats(rs,f) for f in feats}}

    # Stability score: reward same correlation sign and useful magnitude in train and latest month.
    rank=[]
    for f in feats:
        a=per['学習']['stats'][f]; b=per['直近1か月']['stats'][f]; c=per['確認']['stats'][f]
        same=(a['corr']*b['corr']>0)
        stable=(a['corr']*c['corr']>0 and a['corr']*b['corr']>0)
        score=(abs(a['corr'])+abs(b['corr'])+.5*abs(c['corr']))*(1.25 if stable else (1.0 if same else .45))
        rank.append((score,f,a,b,c,stable))
    rank.sort(reverse=True,key=lambda z:z[0])

    L=['# 3号艇まくり／まくり差し頭と事前特徴の相関分析','',
       '対象は全レース。目的変数は「3号艇が1着かつ決まり手がまくり/まくり差し」。事前に分かる特徴だけを使用。相関は因果関係を意味しない。','']
    for name,lo,hi in PERIODS:
        rs=per[name]['rows']; h=sum(r['target'] for r in rs)
        L.append(f'- {name} {lo}〜{hi}: {len(rs)}R / 3頭まくり・MS {h}R ({h/len(rs)*100 if rs else 0:.2f}%)')
    L += ['','## 安定相関ランキング','|順位|特徴|学習corr|確認corr|直近corr|学習 成功/失敗平均|直近 成功/失敗平均|直近 上位25%率|直近 下位25%率|方向安定|','|---:|---|---:|---:|---:|---:|---:|---:|---:|---|']
    for idx,(sc,f,a,b,c,stable) in enumerate(rank[:15],1):
        L.append(f"|{idx}|{f}|{a['corr']:+.3f}|{c['corr']:+.3f}|{b['corr']:+.3f}|{a['hit_mean']:.3f}/{a['miss_mean']:.3f}|{b['hit_mean']:.3f}/{b['miss_mean']:.3f}|{b['high_rate']*100:.1f}%|{b['low_rate']*100:.1f}%|{'○' if stable else '△'}|")

    # Single-factor bins for top stable features.
    stable_feats=[z[1] for z in rank if z[5]][:8]
    L += ['','## 直近1か月：安定特徴の四分位比較']
    for f in stable_feats:
        s=per['直近1か月']['stats'][f]
        L.append(f"- **{f}**: 下位25% {s['low_rate']*100:.1f}% → 上位25% {s['high_rate']*100:.1f}%（corr {s['corr']:+.3f}）")

    # Success-race profile for latest month.
    latest=per['直近1か月']['rows']; hits=[r for r in latest if r['target']]
    L += ['','## 直近1か月の3頭まくり/MSレース一覧','|日付|場|R|決まり手|score3|3ST優位|2壁弱|1弱|motor|伸び|回り足|','|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|']
    for r in hits:
        L.append(f"|{r['date']}|{r['venue']}|{r['race']}|{r['kimarite']}|{r['score3']:.1f}|{r['3_ST優位']:.3f}|{r['2壁弱さ']:.3f}|{r['1弱さ']:.3f}|{r['3モーター攻撃']:.3f}|{r['3伸び']:.3f}|{r['3回り足']:.3f}|")

    L += ['','## 読み方','- corrの絶対値が大きいほど単変量として結果との線形な結び付きが強い。競艇のような低頻度事象では0.1前後でも無視できない場合があるが、サンプル外確認が必要。','- 上位25%率/下位25%率は、その特徴が強いレースと弱いレースで3頭まくり/MS率がどれだけ変わるかを見るためのもの。','- 学習・確認・直近の3期間で符号が揃う特徴を、次モデルの優先候補とする。']
    open('summary_3attack_correlations.md','w',encoding='utf-8').write('\n'.join(L)+'\n')

if __name__=='__main__': main()
