import backtest_v14_3opponent2stage as v14
from backtest_v14_3opponent2stage import *

MIN_COMP=5.0
MAX_TICKETS=9


def main():
    v14.W2=[]; v14.W3=[]
    cache={};hist=defaultdict(list);seen=set();d=PRELOAD_START
    while d<TRAIN_START:
        ingest_motor(hist,seen,d)
        if d>=TRAIN_START-timedelta(days=12): ingest_prior_day_preview(cache,d)
        d+=timedelta(days=1)
    train3,w2,w3,ntrain=train_models(cache,hist,seen)
    v14.W2=w2; v14.W3=w3

    # Advance through the pre-test selection window without using outcomes for fitting.
    d=SEL_START
    while d<=SEL_END:
        ingest_prior_day_preview(cache,d); ingest_motor(hist,seen,d); d+=timedelta(days=1)

    bets,races,st,ret=evaluate_period(TEST_START,TEST_END,cache,hist,seen,train3,MIN_COMP,MAX_TICKETS)
    hh=sum(r['head_hit'] for r in races); bh=sum(r['bet_hit'] for r in races)
    if bets:
        with open('bets_v14b.csv','w',newline='',encoding='utf-8-sig') as f:
            w=csv.DictWriter(f,fieldnames=list(bets[0].keys()));w.writeheader();w.writerows(bets)
    if races:
        with open('races_v14b.csv','w',newline='',encoding='utf-8-sig') as f:
            w=csv.DictWriter(f,fieldnames=list(races[0].keys()));w.writeheader();w.writerows(races)
    L=['# v14b 3号艇 二段階相手モデル（固定条件）','',
       f'学習 {TRAIN_START}〜{TRAIN_END}。テスト {TEST_START}〜{TEST_END}。v13と同じ score3>=68、合成5倍以上、最大9点、1R最大5,000円。',
       '2着→3着の相手確率は事前特徴だけで学習し、市場オッズは価格/合成制約だけに使用。テスト結果は買い目固定後に照合。','',
       f'- 学習した3頭成功サンプル: {ntrain}','',
       '|項目|結果|','|---|---:|',f'|購入レース|{len(races)}|',f'|3頭まくり/MS成立|{hh}|',f'|頭成立率|{(hh/len(races)*100 if races else 0):.1f}%|',f'|3連単的中|{bh}|',f'|3連単的中率|{(bh/len(races)*100 if races else 0):.1f}%|',f'|投資|{st:,}円|',f'|払戻|{ret:,}円|',f'|回収率|{(ret/st*100 if st else 0):.1f}%|',f'|平均点数|{(len(bets)/len(races) if races else 0):.1f}|',f'|平均合成オッズ|{(sum(r["composite_odds"] for r in races)/len(races) if races else 0):.2f}倍|','',
       '## 的中レース','|日付|場|R|score3|結果|払戻/100円|点数|合成|','|---|---:|---:|---:|---|---:|---:|---:|']
    for r in races:
        if not r['bet_hit']:continue
        b=[z for z in bets if z['race_code']==r['race_code'] and z['hit']][0]
        L.append(f"|{r['date']}|{r['venue']}|{r['race']}|{r['score3']:.2f}|{b['actual_combo']}|{b['payout100']:,}円|{r['tickets']}|{r['composite_odds']:.2f}倍|")
    open('summary_v14b.md','w',encoding='utf-8').write('\n'.join(L)+'\n')

if __name__=='__main__':main()
