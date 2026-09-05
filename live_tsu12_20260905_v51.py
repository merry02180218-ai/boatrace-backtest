from backtest import rows, race_features
from backtest_v3 import CORR
from backtest_v51_lane_corrected_tickets import rank_scores, opp_place_score, tickets_for, learn_st_frame_bias

DATE='2026/09/05'; VENUE='09'; RACE='12'; HEAD=5
EX={1:6.82,2:6.81,3:6.85,4:6.83,5:6.81,6:6.83}
ST={1:.07,2:.02,3:.10,4:.01,5:.02,6:.06}
LAP={1:36.97,2:37.07,3:37.50,4:37.03,5:37.57,6:37.37}
TURN={1:4.43,2:4.72,3:4.83,4:4.53,5:4.73,6:5.07}
STRAIGHT={1:8.52,2:8.37,3:8.68,4:8.42,5:8.54,6:8.41}

def main():
    cards=rows(f'data/programs/race_cards/{DATE}.csv')
    w10={r['レースコード']:r for r in rows(f'data/programs/waku10/{DATE}.csv')}
    card=None
    for r in cards:
        if str(r.get('レース場コード','')).zfill(2)==VENUE and str(r.get('レース回','')).replace('R','').zfill(2)==RACE:
            card=r;break
    if not card: raise RuntimeError('Tsu12 card not found')
    code=card['レースコード']; x=race_features(card,w10.get(code,{}))
    stbias=learn_st_frame_bias()
    exraw={b:EX[b]+CORR[b]['展示'] for b in range(1,7)}
    ex=rank_scores(exraw,True)
    straw={b:ST[b]-stbias[b] for b in range(1,7)}
    st=rank_scores(straw,True)
    lapraw={b:LAP[b]+CORR[b]['一周'] for b in range(1,7)}
    turnraw={b:TURN[b]+CORR[b]['回り足'] for b in range(1,7)}
    sraw={b:STRAIGHT[b]+CORR[b]['直線'] for b in range(1,7)}
    lap=rank_scores(lapraw,True);turn=rank_scores(turnraw,True);straight=rank_scores(sraw,True)
    os={b:{'lap':lap[b],'turn':turn[b],'straight':straight[b],'avg':(lap[b]+turn[b]+straight[b])/3} for b in range(1,7)}
    scores={b:opp_place_score(x,b,ex,st,os) for b in range(1,7) if b!=HEAD}
    ranked=sorted(scores,key=scores.get,reverse=True)
    tickets=tickets_for(HEAD,ranked,6)
    lines=['# 津12R 2026-09-05 v51 LIVE ticket calculation','',f'- race_code: {code}',f'- head: {HEAD}',f'- ranked opponents: {" > ".join(map(str,ranked))}','', '## opponent scores']
    for b in ranked: lines.append(f'- {b}: {scores[b]:.6f}')
    lines+=['','## fixed 6 tickets']+[f'- {t}' for t in tickets]
    open('live_tsu12_20260905_v51.md','w',encoding='utf-8').write('\n'.join(lines)+'\n')
    print('\n'.join(lines))

if __name__=='__main__': main()
