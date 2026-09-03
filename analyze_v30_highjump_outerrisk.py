from backtest_v29_psych3_zones_month import *
from datetime import date,timedelta
from collections import defaultdict
import csv, math

START=date(2026,8,3); END=date(2026,9,2)

def c01x(v): return max(0.0,min(1.0,v))
def fastx(z):
    st=z.get('waku_st')
    return .5 if st is None else c01x((.22-st)/.12)
def sx(z): return c01x(.60*c01x((z['wr']-3.5)/4)+.40*c01x((z['local']-3)/5))
def outer_take(z):
    return c01x(.34*sx(z)+.24*fastx(z)+.24*c01x(z['turnfoot'])+.18*c01x(z['stretch']))

def q(vs,p):
    if not vs:return 0
    a=sorted(vs);x=(len(a)-1)*p;lo=int(x);hi=min(lo+1,len(a)-1);w=x-lo
    return a[lo]*(1-w)+a[hi]*w

def avg(rs,k): return sum(r[k] for r in rs)/len(rs) if rs else 0

def main():
    cache={};hist=defaultdict(list);seen=set();d=PRELOAD_START
    while d<TRAIN_START:
        ingest_motor(hist,seen,d)
        if d>=TRAIN_START-timedelta(days=12):ingest_prior_day_preview(cache,d)
        d+=timedelta(days=1)
    while d<START:
        process_features(d,cache,hist);ingest_prior_day_preview(cache,d);ingest_motor(hist,seen,d);d+=timedelta(days=1)

    out=[]
    while d<=END:
        feats=process_features(d,cache,hist);ymd=d.strftime('%Y/%m/%d'); frozen=[]
        for r,x,s4,s5,dc in feats:
            fr=features29(x)
            if fr['3スタート先行度']<.72:continue
            ots={b:outer_take(x[b]) for b in (4,5,6)}
            r4,r5,r6=x[4],x[5],x[6]
            z={'date':str(d),'race_code':r['レースコード'],'venue':r.get('レース場コード',''),'race':r.get('レース回',''),
               'jump3':fr['3スタート先行度'],'threat3':fr['3脅威度'],'wallweak2':fr['2壁弱さ'],'turn3':fr['3旋回足'],'stretch3':fr['3伸び'],'block1':fr['1ブロック成功指数'],
               'outer4':ots[4],'outer5':ots[5],'outer6':ots[6],'outer_max':max(ots.values()),'outer_avg':sum(ots.values())/3,
               'outer4_strength':sx(r4),'outer4_fast':fastx(r4),'outer4_turn':c01x(r4['turnfoot']),'outer4_stretch':c01x(r4['stretch']),
               'outer5_strength':sx(r5),'outer6_strength':sx(r6)}
            frozen.append(z)
        res={r['レースコード']:r for r in rows(f'data/results/realtime/{ymd}.csv')}
        for z in frozen:
            rr=res.get(z['race_code'],{});win=i(rr.get('1着_艇番'));sec=i(rr.get('2着_艇番'));kim=(rr.get('決まり手') or '').replace(' ','').replace('　','')
            z['winner']=win;z['second']=sec;z['kimarite']=kim
            z['cat']='3まくり' if win==3 and kim=='まくり' else ('3まくり差し' if win==3 and kim=='まくり差し' else ('外刺され' if win in (4,5,6) and sec==3 else ('外勝ち' if win in (4,5,6) else 'その他')))
            out.append(z)
        ingest_prior_day_preview(cache,d);ingest_motor(hist,seen,d);d+=timedelta(days=1)

    with open('analysis_v30_highjump_outerrisk.csv','w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=list(out[0].keys()));w.writeheader();w.writerows(out)

    cats=['3まくり','3まくり差し','外刺され','外勝ち','その他']
    L=['# v30 大幅ST先行時の3号艇攻め分岐と外刺され解析','',f'対象: {START}〜{END}。3スタート先行度>=0.72のレースのみ。実進入は不使用。特徴量は結果照合前に固定。','',
       '「外刺され」は4〜6号艇が1着かつ3号艇が2着になったケース。3の攻めで内が崩れた後に外艇が頭まで届いた可能性が高い代理指標として扱う。因果を直接観測したものではない。','',
       '## 結果分岐','|結果|R|率|','|---|---:|---:|']
    for c in cats:
        rs=[r for r in out if r['cat']==c];L.append(f'|{c}|{len(rs)}|{100*len(rs)/len(out):.1f}%|')
    L+=['','## 各結果の事前特徴平均','|結果|R|3脅威|3ST先行|2壁弱|3旋回|3伸び|1ブロック|外最大脅威|4号艇脅威|','|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for c in cats:
        rs=[r for r in out if r['cat']==c]
        L.append(f"|{c}|{len(rs)}|{avg(rs,'threat3'):.3f}|{avg(rs,'jump3'):.3f}|{avg(rs,'wallweak2'):.3f}|{avg(rs,'turn3'):.3f}|{avg(rs,'stretch3'):.3f}|{avg(rs,'block1'):.3f}|{avg(rs,'outer_max'):.3f}|{avg(rs,'outer4'):.3f}|")

    # Outer-risk quartiles
    vals=[r['outer_max'] for r in out];cuts=[q(vals,.25),q(vals,.50),q(vals,.75)]
    def binname(v):
        if v<=cuts[0]:return '低Q1'
        if v<=cuts[1]:return 'Q2'
        if v<=cuts[2]:return 'Q3'
        return '高Q4'
    L+=['','## 外最大脅威の四分位','|外脅威帯|R|3まくり/MS勝ち|率|外刺され|率|外艇1着全体|率|','|---|---:|---:|---:|---:|---:|---:|---:|']
    for bn in ['低Q1','Q2','Q3','高Q4']:
        rs=[r for r in out if binname(r['outer_max'])==bn];three=sum(r['cat'] in ('3まくり','3まくり差し') for r in rs);stab=sum(r['cat']=='外刺され' for r in rs);ow=sum(r['winner'] in (4,5,6) for r in rs)
        L.append(f'|{bn}|{len(rs)}|{three}|{100*three/len(rs) if rs else 0:.1f}%|{stab}|{100*stab/len(rs) if rs else 0:.1f}%|{ow}|{100*ow/len(rs) if rs else 0:.1f}%|')
    L+=['',f'四分位境界 outer_max: Q1={cuts[0]:.3f}, median={cuts[1]:.3f}, Q3={cuts[2]:.3f}','','## 外刺され艇番','|勝ち艇|R|率(外刺され内)|','|---:|---:|---:|']
    stabs=[r for r in out if r['cat']=='外刺され']
    for b in (4,5,6):
        n=sum(r['winner']==b for r in stabs);L.append(f'|{b}|{n}|{100*n/len(stabs) if stabs else 0:.1f}%|')

    # Focus 4 boat danger, because immediately outside 3 is tactically most relevant.
    vals4=[r['outer4'] for r in out];c4=q(vals4,.75)
    hi=[r for r in out if r['outer4']>=c4];lo=[r for r in out if r['outer4']<c4]
    def fmtgrp(name,rs):
        three=sum(r['cat'] in ('3まくり','3まくり差し') for r in rs);stab=sum(r['cat']=='外刺され' for r in rs);ow=sum(r['winner'] in (4,5,6) for r in rs)
        return f'|{name}|{len(rs)}|{100*three/len(rs):.1f}%|{100*stab/len(rs):.1f}%|{100*ow/len(rs):.1f}%|'
    L+=['','## 4号艇脅威 上位25%','|区分|R|3攻め勝ち率|外刺され率|外艇1着率|','|---|---:|---:|---:|---:|',fmtgrp('4脅威上位25%',hi),fmtgrp('それ以外',lo),f'','4号艇脅威の上位25%境界: {c4:.3f}']
    open('summary_v30_highjump_outerrisk.md','w',encoding='utf-8').write('\n'.join(L)+'\n')
if __name__=='__main__':main()
