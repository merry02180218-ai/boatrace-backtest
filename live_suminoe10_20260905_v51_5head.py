"""One-off no-leak v51 direct judgment for 2026-09-05 Suminoe 10R, head=5.
Uses screenshot pre-race exhibition/ST/original exhibition only. No result/payout/odds.
"""
from backtest import rows, race_features
from analyze_v23_20260902_daypreview import by_code, venue_map
from backtest_v51_lane_corrected_tickets import learn_st_frame_bias, corrected_direct, preview_comp, opp_place_score, tickets_for

DS='2026/09/05'; CODE='202609051210'; HEAD=5; MODEL='5頭展開'; VENUE='12'
OUT='live_suminoe10_20260905_v51_5head.md'
EX=[6.99,6.82,6.96,6.92,6.96,6.86]
ST=[.01,.18,-.06,.09,.06,.13]
LAP=[37.51,37.26,38.10,37.48,37.86,37.57]
TURN=[11.56,11.50,11.85,11.54,11.70,11.58]

def main():
    stbias=learn_st_frame_bias()
    cards=by_code(f'data/programs/race_cards/{DS}.csv')
    w10=by_code(f'data/programs/waku10/{DS}.csv')
    card=cards[CODE]
    x=race_features(card,w10[CODE])
    tkz={CODE:{**{f'艇{i+1}_展示タイム':EX[i] for i in range(6)}}}
    stt={CODE:{**{f'艇{i+1}_スタート展示':ST[i] for i in range(6)}}}
    # Screenshot shows lap + turn only; straight is not published, so v51 keeps neutral 0.5 for straight.
    orow={'計測項目1':'一周','計測項目2':'まわり足'}
    for i in range(6):
        orow[f'艇{i+1}_値1']=LAP[i]
        orow[f'艇{i+1}_値2']=TURN[i]
    orig={CODE:orow}
    ex,st,os=corrected_direct(CODE,tkz,stt,orig,stbias)
    comp=preview_comp(MODEL,HEAD,VENUE,ex,st,os,venue_map())
    grade='S' if comp>=.67 else ('A' if comp>=.55 else 'B')
    ranked=sorted([b for b in range(1,7) if b!=HEAD],key=lambda b:opp_place_score(x,b,ex,st,os),reverse=True)
    t6=tickets_for(HEAD,ranked,6)
    L=['# 2026-09-05 住之江10R v51 ⑤頭 live','',
       '- Screenshot values frozen pre-race.','- No result / payout / odds read.',
       '- Original exhibition straight: not shown -> neutral 0.5 in v51 direct component.',
       f'- direct component: **{comp:.6f} ({100*comp:.1f})**',f'- grade: **{grade}**',
       f'- BUY: **{"BUY" if grade in ("S","A") else "SKIP"}**','',
       f'- opponent rank: **{" > ".join(map(str,ranked))}**','','## frozen 6 tickets']
    L += [f'{i}. **{t}**' for i,t in enumerate(t6,1)]
    open(OUT,'w',encoding='utf-8').write('\n'.join(L)+'\n')
    print('\n'.join(L))
if __name__=='__main__': main()
