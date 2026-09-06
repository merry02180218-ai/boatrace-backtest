from __future__ import annotations
import csv
from datetime import date
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score,brier_score_loss
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

SRC='analysis_v108_1head_feasibility.csv'
OUT='analysis_v154_direct_feature_value_audit.csv'
SUMMARY='summary_v154_direct_feature_value_audit.md'
MONTHS=['2026-06','2026-07','2026-08']; CUT=.72
VENUES=[f'{i:02d}' for i in range(1,25)]
PRE=['one_grade','one_wr','one_local','one_motor','one_waku_wr','one_nst_strength','one_waku_sr_strength','one_past_win','one_meet_st_strength']
DIRECT=['one_ex','one_st','one_lap','one_turn','one_straight','one_orig_avg','one_direct','one_score','threat2','threat3','threat4','threat5','threat6','threat23_max','threat_all_max','margin2','margin3','margin23','margin_all','st_margin2','st_margin3','st_margin23','ex_margin23','turn_margin23','straight_margin23']
ALL=PRE+DIRECT
GROUPS={
 'EXHIBITION_TIME':{'one_ex','ex_margin23'},
 'EXHIBITION_ST':{'one_st','st_margin2','st_margin3','st_margin23'},
 'LAP':{'one_lap'},
 'TURN':{'one_turn','turn_margin23'},
 'STRAIGHT':{'one_straight','straight_margin23'},
 'ORIG_AVG':{'one_orig_avg'},
 'DIRECT_COMPOSITE':{'one_direct'},
 'OPP_THREAT_SCORE':{'one_score','threat2','threat3','threat4','threat5','threat6','threat23_max','threat_all_max','margin2','margin3','margin23','margin_all'},
}
VAR={'CURRENT':ALL,'PRE_ONLY':PRE}
for g,cols in GROUPS.items():VAR['DROP_'+g]=[x for x in ALL if x not in cols]
# clean block removals to expose hidden reuse of components in composites/threats
VAR['NO_ST_ANYWHERE']=[x for x in ALL if x not in GROUPS['EXHIBITION_ST'] and x not in {'one_direct','one_score','threat2','threat3','threat4','threat5','threat6','threat23_max','threat_all_max','margin2','margin3','margin23','margin_all'}]
VAR['RAW_DIRECT_ONLY']=PRE+['one_ex','one_st','one_lap','one_turn','one_straight','one_orig_avg','ex_margin23','turn_margin23','straight_margin23','st_margin2','st_margin3','st_margin23']

def ff(x,d=0.):
 try:return float(x)
 except:return d
def ii(x,d=0):
 try:return int(float(x))
 except:return d
def pct(n,d):return 100*n/d if d else 0.
def read():
 with open(SRC,encoding='utf-8-sig',newline='') as f:return [r for r in csv.DictReader(f) if ii(r.get('valid_result'))==1]
def xm(rs,fs):
 z=[]
 for r in rs:
  a=[ff(r.get(k)) for k in fs];v=str(r.get('venue','')).zfill(2);a += [1. if v==q else 0. for q in VENUES];z.append(a)
 return np.asarray(z,float)
def fit(rs,fs):
 p=Pipeline([('s',StandardScaler()),('m',LogisticRegression(C=.5,max_iter=1800,solver='lbfgs'))]);p.fit(xm(rs,fs),[ii(r.get('head_hit')) for r in rs]);return p
def main():
 src=read(); rows=[]; agg={}
 for name,fs in VAR.items():
  ps=[]
  for mo in MONTHS:
   first=date.fromisoformat(mo+'-01');tr=[r for r in src if date.fromisoformat(r['date'])<first];te=[r for r in src if r.get('month')==mo]
   pp=fit(tr,fs).predict_proba(xm(te,fs))[:,1]
   for r,p in zip(te,pp): rows.append({'variant':name,'month':mo,'race_code':r.get('race_code',''),'p':p,'head_hit':ii(r.get('head_hit'))});ps.append((r,p))
  y=np.asarray([ii(r.get('head_hit')) for r,p in ps]);p=np.asarray([p for r,p in ps]);sel=[(r,q) for r,q in ps if q>=CUT];h=sum(ii(r.get('head_hit')) for r,q in sel)
  agg[name]=(len(ps),roc_auc_score(y,p),brier_score_loss(y,p),len(sel),pct(h,len(sel)),np.mean([q for r,q in sel])*100 if sel else 0)
 cur=agg['CURRENT']
 L=['# v154 直前判定 feature-value 全面監査','', '- v108 no-leak frozen tableを使用。Jun/Jul/Aug strict monthly walk-forward。','- S=72%固定。結果/払戻は予測特徴に不使用。','- PRE_ONLYは展示前9特徴のみ。CURRENTはv109全特徴。','- DROP_* は各直前要素を1群ずつ除去して、CURRENTとの差を見る。','- one_direct / opponent threat score は複数の直前値を再内包するため、単独DROPは純粋な完全除去ではない。NO_ST_ANYWHERE / RAW_DIRECT_ONLYも併記。','', '## Jun-Aug aggregate','|variant|R|AUC|Brier|S件数|S頭率|S平均p|ΔAUC|ΔBrier|ΔS頭率|','|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
 for name,z in agg.items():
  L.append(f'|{name}|{z[0]:,}|{z[1]:.4f}|{z[2]:.5f}|{z[3]:,}|{z[4]:.2f}%|{z[5]:.2f}%|{z[1]-cur[1]:+.4f}|{z[2]-cur[2]:+.5f}|{z[4]-cur[4]:+.2f}pt|')
 L += ['','## 月別S頭率','|月|variant|S件数|S頭率|','|---|---|---:|---:|']
 for mo in MONTHS:
  for name in VAR:
   q=[r for r in rows if r['month']==mo and r['variant']==name and ff(r['p'])>=CUT];h=sum(ii(r['head_hit']) for r in q);L.append(f'|{mo}|{name}|{len(q):,}|{pct(h,len(q)):.2f}%|')
 L += ['','## 読み方','- DROPして改善する要素は、現行の使い方が過剰/ノイズの疑い。','- DROPして悪化する要素は、他要素込みでも追加価値あり。','- PRE_ONLYとの差が「直前情報全体」の追加価値。','- 本監査後に重み変更する場合も、結果を見て同じJun-Augへ再最適化せず、次の未使用期間で確認する。']
 with open(OUT,'w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=['variant','month','race_code','p','head_hit']);w.writeheader();w.writerows(rows)
 open(SUMMARY,'w',encoding='utf-8').write('\n'.join(L)+'\n');print('\n'.join(L))
if __name__=='__main__':main()
