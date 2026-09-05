"""One-off no-leak live judgment for 2026-09-05 Gamagori 11R, 5-head model."""
from backtest_v51_lane_corrected_tickets import learn_st_frame_bias, corrected_direct, preview_comp, opp_place_score, tickets_for
from analyze_v23_20260902_daypreview import venue_map
from backtest import rows, race_features
from analyze_v23_20260902_daypreview import by_code
DS='2026-09-05';Y='2026/09/05';CODE='202609050711';VENUE='07';HEAD=5;OUT='live_gamagori11_20260905_v51_5head.md'
EX=[6.72,6.75,6.73,6.69,6.77,6.75];ST=[.05,.11,.18,.03,.11,.08];LAP=[36.43,37.27,37.84,37.59,37.83,38.62];TURN=[4.83,5.05,5.53,5.26,5.28,5.13];STRAIGHT=[6.31,6.45,6.22,6.37,6.33,6.46]
def main():
 stbias=learn_st_frame_bias();tkz={CODE:{**{f'艇{i+1}_展示タイム':EX[i] for i in range(6)}}};stt={CODE:{**{f'艇{i+1}_スタート展示':ST[i] for i in range(6)}}};orow={'計測項目1':'一周','計測項目2':'まわり足','計測項目3':'直線'}
 for i in range(6):orow[f'艇{i+1}_値1']=LAP[i];orow[f'艇{i+1}_値2']=TURN[i];orow[f'艇{i+1}_値3']=STRAIGHT[i]
 ex,st,os=corrected_direct(CODE,tkz,stt,{CODE:orow},stbias);vidx=venue_map();comp=preview_comp('5頭展開',HEAD,VENUE,ex,st,os,vidx)
 g='S' if comp>=.67 else ('A' if comp>=.55 else 'B');buy='BUY' if g in ('A','S') else 'SKIP'
 cards=by_code(f'data/programs/race_cards/{Y}.csv');w10=by_code(f'data/programs/waku10/{Y}.csv');x=race_features(cards[CODE],w10.get(CODE,{}));ranked=sorted([b for b in range(1,7) if b!=HEAD],key=lambda b:opp_place_score(x,b,ex,st,os),reverse=True);ts=tickets_for(HEAD,ranked,6)
 L=['# 2026-09-05 蒲郡11R v51 ⑤頭 live','','- PRE model: ⑤頭（⑤高倉孝太）','- Screenshot values frozen pre-race.','- No result / payout / odds read.',f'- direct component: **{comp:.6f} ({100*comp:.1f})**',f'- grade: **{g}**',f'- BUY: **{buy}**','',f'- opponent rank: **{" > ".join(map(str,ranked))}**','','## frozen 6 tickets']+[f'{i}. **{t}**' for i,t in enumerate(ts,1)];open(OUT,'w',encoding='utf-8').write('\n'.join(L)+'\n');print('\n'.join(L))
if __name__=='__main__':main()
