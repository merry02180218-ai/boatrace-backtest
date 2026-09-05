"""One-off no-leak live judgment for 2026-09-05 Suminoe 11R. Screenshot inputs only."""
import math, numpy as np
from predict_v116_20260905_1head_live import read_csv, fit_model, pred, grade, exact_prior_st_bias
from analyze_v108_1head_feasibility import feature_row, bycode
from analyze_v110b_1head_role_tickets import fit_roles, second_vec, third_vec, rankof, zmap
from backtest import rows
DS='2026-09-05';Y='2026/09/05';CODE='202609051211';SRC='analysis_v108_1head_feasibility.csv';OUT='live_suminoe11_20260905_1head.md'
EX=[6.90,6.94,6.95,6.87,6.91,7.03];ST=[.09,-.04,.12,-.01,.01,.01];LAP=[37.12,37.53,37.75,37.64,37.51,37.74];TURN=[11.41,11.80,11.80,11.88,11.52,11.72]
def main():
 src=read_csv(SRC); train=[r for r in src if int(float(r.get('valid_result') or 0))==1 and r.get('date','')<DS]; model=fit_model(train); bias,days=exact_prior_st_bias(); cards=bycode(rows(f'data/programs/race_cards/{Y}.csv')); waku=bycode(rows(f'data/programs/waku10/{Y}.csv')); card=cards[CODE];w=waku[CODE]
 tkz={CODE:{**{f'艇{i+1}_展示タイム':EX[i] for i in range(6)}}}; sr={f'艇{i+1}_スタート展示':ST[i] for i in range(6)};sr['艇1_コース']=1
 orow={'計測項目1':'一周','計測項目2':'まわり足'}
 for i in range(6):orow[f'艇{i+1}_値1']=LAP[i];orow[f'艇{i+1}_値2']=TURN[i]
 r=feature_row(DS,card,w,tkz,{CODE:sr},{CODE:orow},bias);p=pred(model,r);g=grade(p)
 role_train=[x for x in src if x.get('date','')<DS];m2,m3,ntrain=fit_roles(role_train);sec={b:float(m2.predict_proba(np.asarray([second_vec(r,b)],dtype=float))[0,1]) for b in range(2,7)};den=sum(sec.values()) or 1.;p2={b:max(sec[b]/den,1e-12) for b in range(2,7)};pr={};pc={}
 for s in range(2,7):
  rem=[t for t in range(2,7) if t!=s];vals={t:float(m3.predict_proba(np.asarray([third_vec(r,s,t)],dtype=float))[0,1]) for t in rem};d=sum(vals.values()) or 1.
  for t in rem:pr[(s,t)]=math.log(p2[s])+math.log(max(vals[t]/d,1e-12));pc[(s,t)]=-(rankof(r,s)+.7*rankof(r,t))
 rz=zmap(pr);cz=zmap(pc);arr=sorted(pc,key=lambda k:(-(.5*cz[k]+.5*rz[k]),k[0],k[1]));top7=[f'1-{s}-{t}' for s,t in arr[:7]]
 L=['# 2026-09-05 住之江11R 1号艇 live','','- Screenshot values frozen pre-race.','- No result / payout / odds read.','- Original exhibition straight not shown -> v109 feature code neutral 0.5.',f'- prior ST-bias days: {days}',f'- role train head-win rows: {ntrain}',f'- p109: **{100*p:.1f}%**',f'- grade: **{g}**',f'- BUY(S-only operation): **{"BUY" if g=="S" else "SKIP"}**','','## v110 top7']+[f'{i}. **{t}**' for i,t in enumerate(top7,1)];open(OUT,'w',encoding='utf-8').write('\n'.join(L)+'\n');print('\n'.join(L))
if __name__=='__main__':main()
