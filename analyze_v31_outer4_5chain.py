from analyze_v30_highjump_outerrisk import *

# v31: analyse both requested branches after a strong 3 attack:
# A) 3 attack -> 4 counter / outside win
# B) 3 attack -> 4 follows/pressures -> 5 makurizashi or 5-head
# Pre-race features only; results are joined after feature freezing.

def take5(z):
    return c01x(.30*sx(z)+.18*fastx(z)+.32*c01x(z['turnfoot'])+.12*c01x(z['stretch'])+.08*c01x((z['wr']-4.0)/3.5))

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
        feats=process_features(d,cache,hist);ymd=d.strftime('%Y/%m/%d');frozen=[]
        for r,x,s4,s5,dc in feats:
            fr=features29(x)
            if fr['3スタート先行度']<.72:continue
            o4=outer_take(x[4]);o5=take5(x[5]);o6=outer_take(x[6])
            # 4-follow pressure: 4 has enough start/strength to move with 3, while 5 has turn/take ability behind it.
            follow4=c01x(.42*fastx(x[4])+.33*sx(x[4])+.25*c01x(x[4]['stretch']))
            chain5=c01x(.34*fr['3スタート先行度']+.26*follow4+.30*o5+.10*(1-c01x(x[4]['turnfoot'])))
            counter4=c01x(.38*o4+.22*(1-fr['3旋回足'])+.18*(1-fr['3伸び'])+.12*fr['3スタート先行度']+.10*fr['2壁弱さ'])
            frozen.append({'date':str(d),'race_code':r['レースコード'],'venue':r.get('レース場コード',''),'race':r.get('レース回',''),
             'jump3':fr['3スタート先行度'],'threat3':fr['3脅威度'],'turn3':fr['3旋回足'],'stretch3':fr['3伸び'],'wallweak2':fr['2壁弱さ'],
             'o4':o4,'o5':o5,'o6':o6,'follow4':follow4,'chain5':chain5,'counter4':counter4,
             's4':sx(x[4]),'f4':fastx(x[4]),'t4':c01x(x[4]['turnfoot']),'s5':sx(x[5]),'f5':fastx(x[5]),'t5':c01x(x[5]['turnfoot']),'stretch5':c01x(x[5]['stretch'])})
        res={r['レースコード']:r for r in rows(f'data/results/realtime/{ymd}.csv')}
        for z in frozen:
            rr=res.get(z['race_code'],{});w=i(rr.get('1着_艇番'));s=i(rr.get('2着_艇番'));t=i(rr.get('3着_艇番'));kim=(rr.get('決まり手') or '').replace(' ','').replace('　','')
            z.update({'winner':w,'second':s,'third':t,'kimarite':kim,'three_attack_win':int(w==3 and kim in ('まくり','まくり差し')),
                      'four_counter':int(w==4 and s==3),'four_win':int(w==4),'five_win':int(w==5),'five_ms':int(w==5 and kim=='まくり差し'),
                      'five_win_3in23':int(w==5 and 3 in (s,t)),'five_ms_3in23':int(w==5 and kim=='まくり差し' and 3 in (s,t))})
            out.append(z)
        ingest_prior_day_preview(cache,d);ingest_motor(hist,seen,d);d+=timedelta(days=1)
    with open('analysis_v31_outer4_5chain.csv','w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=list(out[0].keys()));w.writeheader();w.writerows(out)
    def rate(rs,k):return 100*sum(r[k] for r in rs)/len(rs) if rs else 0
    def grp_quart(k):
        vs=[r[k] for r in out];cs=[q(vs,.25),q(vs,.5),q(vs,.75)]
        return cs,[[r for r in out if (r[k]<=cs[0] if j==0 else (r[k]>cs[j-1] and r[k]<=cs[j] if j<3 else r[k]>cs[2]))] for j in range(4)]
    L=['# v31 3攻め起点：4刺され＋5まくり差し連鎖解析','',f'対象: {START}〜{END} / 3スタート先行度>=0.72。実進入不使用。事前特徴を固定後に結果照合。','',
       '5連鎖は「3が攻める→4が追走/外へ圧力→5に内の差し場」という仮説を、4追走指数と5取り切り指数の合成で検証する。因果そのものは観測できないため代理指標。','',
       '## 全320Rの実績',f'- 3まくり/まくり差し勝ち: {sum(r["three_attack_win"] for r in out)}R ({rate(out,"three_attack_win"):.1f}%)',
       f'- 4号艇1着: {sum(r["four_win"] for r in out)}R ({rate(out,"four_win"):.1f}%) / うち4-3: {sum(r["four_counter"] for r in out)}R ({rate(out,"four_counter"):.1f}%)',
       f'- 5号艇1着: {sum(r["five_win"] for r in out)}R ({rate(out,"five_win"):.1f}%) / 5まくり差し: {sum(r["five_ms"] for r in out)}R ({rate(out,"five_ms"):.1f}%)',
       f'- 5号艇1着かつ3が2/3着: {sum(r["five_win_3in23"] for r in out)}R ({rate(out,"five_win_3in23"):.1f}%) / そのうち5まくり差し: {sum(r["five_ms_3in23"] for r in out)}R ({rate(out,"five_ms_3in23"):.1f}%)']
    for key,title in [('counter4','4刺されリスク指数'),('chain5','3→4→5連鎖指数')]:
        cs,gs=grp_quart(key);L+=['',f'## {title} 四分位','|帯|R|3攻め勝ち|4-3|4頭|5頭|5まくり差し|5頭+3が2/3着|','|---|---:|---:|---:|---:|---:|---:|---:|']
        for name,rs in zip(['低Q1','Q2','Q3','高Q4'],gs):
            L.append(f'|{name}|{len(rs)}|{rate(rs,"three_attack_win"):.1f}%|{rate(rs,"four_counter"):.1f}%|{rate(rs,"four_win"):.1f}%|{rate(rs,"five_win"):.1f}%|{rate(rs,"five_ms"):.1f}%|{rate(rs,"five_win_3in23"):.1f}%|')
        L.append(f'境界: {cs[0]:.3f} / {cs[1]:.3f} / {cs[2]:.3f}')
    # Compare actual 5 MS to other cases on pre-race features.
    ms=[r for r in out if r['five_ms']];notms=[r for r in out if not r['five_ms']]
    L+=['','## 5まくり差し成立時の事前特徴','|群|R|3ST先行|4追走|5取り切り|5旋回|5ST|3→4→5指数|','|---|---:|---:|---:|---:|---:|---:|']
    for name,rs in [('5まくり差し',ms),('それ以外',notms)]:
        L.append(f"|{name}|{len(rs)}|{avg(rs,'jump3'):.3f}|{avg(rs,'follow4'):.3f}|{avg(rs,'o5'):.3f}|{avg(rs,'t5'):.3f}|{avg(rs,'f5'):.3f}|{avg(rs,'chain5'):.3f}|")
    open('summary_v31_outer4_5chain.md','w',encoding='utf-8').write('\n'.join(L)+'\n')
if __name__=='__main__':main()
