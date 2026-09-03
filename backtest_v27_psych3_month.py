from backtest_v20_week import *
from backtest_v4 import norm_st_edge
from datetime import date,timedelta
from collections import defaultdict
import csv

TEST_START=date(2026,8,3); TEST_END=date(2026,9,2)
MODELS=['3まくり心理','3まくり差し心理']
HEAD2={'3まくり心理':3,'3まくり差し心理':3}

# v27 is specified BEFORE reading the test-period results.
# It models the user's hypothesis as behavioral proxies rather than unverifiable mental state:
#  - 3 threat: racer strength + 3-course attack history + start ability
#  - 1 block: 1-course strength + start ability
#  - start jump: expected relative launch of 3 vs 1/2
#  - pressure: strong 3 + block-capable 1 + roughly matched start => 1 is more likely to defend

def c01(v): return max(0.0,min(1.0,v))
def fast(st):
    if st is None:return .5
    return c01((.22-st)/.12)
def strength3(z): return c01(.60*c01((z['wr']-3.5)/4)+.40*c01((z['local']-3)/5))
def attack_hist(z): return c01(.55*z['past_win']/.25+.45*(6-z['waku_sr'])/5)
def one_strength(a): return c01(.55*c01(a['waku_wr']/8)+.25*c01((a['wr']-3)/5)+.20*fast(a['waku_st']))

def psych_features(x):
    a,b,c=x[1],x[2],x[3]
    edge31=.55*norm_st_edge(a['waku_st'],c['waku_st'])+.45*norm_st_edge(a['nst'],c['nst'])
    edge32=.55*norm_st_edge(b['waku_st'],c['waku_st'])+.45*norm_st_edge(b['nst'],c['nst'])
    jump=c01(.55*edge31+.45*edge32)
    threat=c01(.50*strength3(c)+.30*attack_hist(c)+.20*fast(c['waku_st']))
    block=one_strength(a)
    wall2=c01(.55*c01((5.5-b['waku_wr'])/4.5)+.45*norm_st_edge(b['waku_st'],c['waku_st']))
    close31=c01(1-abs(edge31-.5)*2)
    pressure=c01(threat*block*close31*2.0)
    turn=c01(c['turnfoot'])
    stretch=c01(c['stretch'])
    # Direct makuri: jump is the main driver. Block risk matters only when 1 can match the launch.
    makuri=c01(.34*jump+.22*wall2+.18*threat+.12*attack_hist(c)+.09*stretch+.05*(1-block)*(1-jump))
    # Makurizashi: 3 is threatening, 1 is capable/likely to defend, starts are close enough to create pressure,
    # and 3 needs turning/inside-taking quality. Excessive jump is a negative because that points to direct makuri.
    moderate_jump=c01(1-abs(jump-.55)/.45)
    ms=c01(.24*pressure+.20*threat+.18*turn+.14*moderate_jump+.12*wall2+.07*attack_hist(c)+.05*block)
    return {'3脅威度':threat,'1ブロック力':block,'3スタート先行度':jump,'1対3圧力':pressure,'2壁弱さ':wall2,'3旋回足':turn,'3伸び':stretch,'直まくり指数':makuri,'まくり差し指数':ms}

def score_new(fr,m): return 100*(fr['直まくり指数'] if m=='3まくり心理' else fr['まくり差し指数'])
def target_new(rr,m):
    win=i(rr.get('1着_艇番'));kim=(rr.get('決まり手') or '').replace(' ','').replace('　','')
    return int(win==3 and kim==('まくり' if m=='3まくり心理' else 'まくり差し'))

def pass_new(fr,m):
    # Fixed structural gates; not tuned on Aug3-Sep2.
    if m=='3まくり心理':
        return fr['直まくり指数']>=.58 and fr['3スタート先行度']>=.58 and fr['2壁弱さ']>=.50 and fr['3脅威度']>=.48
    return fr['まくり差し指数']>=.56 and fr['3脅威度']>=.50 and fr['1対3圧力']>=.32 and fr['3旋回足']>=.45

def eval_group(rows_,bets_,m):
    rs=[r for r in rows_ if r['model']==m];bs=[b for b in bets_ if b['model']==m]
    h=sum(r['head_hit'] for r in rs);bh=sum(r['bet_hit'] for r in rs);st=sum(b['stake'] for b in bs);ret=sum(b['return'] for b in bs)
    return len(rs),h,(100*h/len(rs) if rs else 0),bh,(100*bh/len(rs) if rs else 0),st,ret,(100*ret/st if st else 0)

def main():
    cache={};hist=defaultdict(list);seen=set();d=PRELOAD_START
    while d<TRAIN_START:
        ingest_motor(hist,seen,d)
        if d>=TRAIN_START-timedelta(days=12):ingest_prior_day_preview(cache,d)
        d+=timedelta(days=1)
    train={m:[] for m in MODELS};pairs={m:defaultdict(int) for m in MODELS}
    d=TRAIN_START
    while d<=TRAIN_END:
        feats=process_features(d,cache,hist);ymd=d.strftime('%Y/%m/%d');res={r['レースコード']:r for r in rows(f'data/results/realtime/{ymd}.csv')};pay={r['レースコード']:r for r in rows(f'data/results/payouts/{ymd}.csv')}
        for r,x,s4,s5,dc in feats:
            fr=psych_features(x)
            for m in MODELS:
                sc=score_new(fr,m);y=target_new(res.get(r['レースコード'],{}),m);train[m].append((sc,y))
                if y:
                    k=pair_key((pay.get(r['レースコード'],{}).get('3連単_組番') or '').strip())
                    if k:pairs[m][k]+=1
        ingest_prior_day_preview(cache,d);ingest_motor(hist,seen,d);d+=timedelta(days=1)
    while d<TEST_START:
        process_features(d,cache,hist);ingest_prior_day_preview(cache,d);ingest_motor(hist,seen,d);d+=timedelta(days=1)
    races=[];bets=[]
    while d<=TEST_END:
        feats=process_features(d,cache,hist);ymd=d.strftime('%Y/%m/%d');ods={r['レースコード']:r for r in rows(f'data/previews/od3/{ymd}.csv')};frozen=[]
        for r,x,s4,s5,dc in feats:
            fr=psych_features(x)
            for m in MODELS:
                if not pass_new(fr,m):continue
                sc=score_new(fr,m);p=cal_prob(train[m],sc);chosen=select_set(3,p,ods.get(r['レースコード'],{}),pairs[m])
                if not chosen:continue
                allocate(chosen)
                rr={'model':m,'date':str(d),'race_code':r['レースコード'],'venue':r.get('レース場コード',''),'race':r.get('レース回',''),'score':round(sc,2),'prob':round(p,4),'tickets':len(chosen),'composite_odds':round(composite(chosen),2)}
                rr.update({k:round(v,3) for k,v in fr.items()});races.append(rr)
                for z in chosen:z.update({'model':m,'date':str(d),'race_code':r['レースコード']});frozen.append(z)
        # Results are read only AFTER candidates/tickets for that day are frozen.
        pay={r['レースコード']:r for r in rows(f'data/results/payouts/{ymd}.csv')};res={r['レースコード']:r for r in rows(f'data/results/realtime/{ymd}.csv')}
        for b in frozen:
            pr=pay.get(b['race_code'],{});actual=(pr.get('3連単_組番') or '').strip();hit=actual==b['combo'];b['actual_combo']=actual;b['hit']=int(hit);b['payout100']=i(pr.get('3連単_払戻金')) if hit else 0;b['return']=b['payout100']*(b['stake']//100) if hit else 0;bets.append(b)
        for rr in [q for q in races if q['date']==str(d)]:rr['head_hit']=target_new(res.get(rr['race_code'],{}),rr['model'])
        ingest_prior_day_preview(cache,d);ingest_motor(hist,seen,d);d+=timedelta(days=1)
    for r in races:
        bs=[b for b in bets if b['race_code']==r['race_code'] and b['model']==r['model']];r['bet_hit']=int(any(b['hit'] for b in bs));r['return']=sum(b['return'] for b in bs)
    with open('races_v27_psych3_month.csv','w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=sorted(set().union(*(r.keys() for r in races))));w.writeheader();w.writerows(races)
    with open('bets_v27_psych3_month.csv','w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=sorted(set().union(*(b.keys() for b in bets))));w.writeheader();w.writerows(bets)
    L=['# v27 3号艇 心理・相対展開モデル 1か月バックテスト','',f'テスト: {TEST_START}〜{TEST_END} / 学習: {TRAIN_START}〜{TRAIN_END}','',
       '「心理」を直接推定せず、3号艇脅威度・1号艇ブロック力・3の1/2に対する予測ST先行度・両者の圧力として事前情報だけで代理変数化。実進入・当日結果は候補抽出に未使用。候補と買い目を先に固定してから結果を照合。','',
       '|モデル|候補R|狙い成立|成立率|3連単的中|的中率|投資|払戻|回収率|','|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for m in MODELS:
        n,h,hr,bh,bhr,st,ret,roi=eval_group(races,bets,m);L.append(f'|{m}|{n}|{h}|{hr:.1f}%|{bh}|{bhr:.1f}%|{st:,}円|{ret:,}円|{roi:.1f}%|')
    # combined exact 3 attack
    n=len(races);h=sum(r['head_hit'] for r in races);bh=sum(r['bet_hit'] for r in races);st=sum(b['stake'] for b in bets);ret=sum(b['return'] for b in bets)
    L.append(f'|合計|{n}|{h}|{100*h/n if n else 0:.1f}%|{bh}|{100*bh/n if n else 0:.1f}%|{st:,}円|{ret:,}円|{100*ret/st if st else 0:.1f}%|')
    L += ['','## 固定ロジック','- 3まくり: 3のST先行を主因。2壁弱さ・3脅威度・3伸びを加点し、1がスタートを合わせられる局面では1ブロック力を間接的に減点。','- 3まくり差し: 強い3を1が警戒しやすい「1対3圧力」、3脅威度、3旋回足、中程度のST先行を重視。3が大きくST先行する場合は直まくり側へ寄せる。','- モーターは伸び/旋回足の一部として補助的に残すが、単独の必須条件にはしていない。','',
       '## 候補上位（score順）','|モデル|日付|場|R|score|脅威|1ブロック|ST先行|圧力|2壁弱|成立|','|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for r in sorted(races,key=lambda z:z['score'],reverse=True)[:30]:
        L.append(f"|{r['model']}|{r['date']}|{r['venue']}|{r['race']}|{r['score']}|{r['3脅威度']}|{r['1ブロック力']}|{r['3スタート先行度']}|{r['1対3圧力']}|{r['2壁弱さ']}|{r['head_hit']}|")
    open('summary_v27_psych3_month.md','w',encoding='utf-8').write('\n'.join(L)+'\n')
if __name__=='__main__':main()
