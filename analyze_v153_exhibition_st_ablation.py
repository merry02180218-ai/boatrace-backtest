from __future__ import annotations
import csv
from datetime import date
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score,brier_score_loss
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

SRC='analysis_v108_1head_feasibility.csv'
OUT='analysis_v153_exhibition_st_ablation.csv'
SUMMARY='summary_v153_exhibition_st_ablation.md'
MONTHS=['2026-06','2026-07','2026-08']
S_CUT=.72
VENUES=[f'{i:02d}' for i in range(1,25)]
BASE=[
 'one_grade','one_wr','one_local','one_motor','one_waku_wr','one_nst_strength',
 'one_waku_sr_strength','one_past_win','one_meet_st_strength',
 'one_ex','one_st','one_lap','one_turn','one_straight','one_orig_avg','one_direct','one_score',
 'threat2','threat3','threat4','threat5','threat6','threat23_max','threat_all_max',
 'margin2','margin3','margin23','margin_all','st_margin2','st_margin3','st_margin23',
 'ex_margin23','turn_margin23','straight_margin23'
]
EXST={'one_st','st_margin2','st_margin3','st_margin23'}
HISTST={'one_nst_strength','one_waku_sr_strength','one_meet_st_strength'}
VARIANTS={
 'CURRENT':BASE,
 'NO_EXHIBITION_ST':[x for x in BASE if x not in EXST],
 'NO_ALL_ST':[x for x in BASE if x not in (EXST|HISTST)],
}

def ff(x,d=0.0):
    try:return float(x)
    except:return d

def ii(x,d=0):
    try:return int(float(x))
    except:return d

def read():
    with open(SRC,encoding='utf-8-sig',newline='') as f:return [r for r in csv.DictReader(f) if ii(r.get('valid_result'))==1]

def xm(rows,features):
    out=[]
    for r in rows:
        z=[ff(r.get(k)) for k in features]
        v=str(r.get('venue','')).zfill(2)
        z += [1.0 if v==vv else 0.0 for vv in VENUES]
        out.append(z)
    return np.asarray(out,float)

def fit(train,features):
    p=Pipeline([('scale',StandardScaler()),('lr',LogisticRegression(C=.5,max_iter=1800,solver='lbfgs'))])
    p.fit(xm(train,features),[ii(r.get('head_hit')) for r in train])
    return p

def pct(n,d):return 100*n/d if d else 0.0

def main():
    src=read(); out=[]; L=['# v153 展示STの寄与アブレーション','',
      '- 対象: v108で既にfreeze済みのno-leak feature table。Jun/Jul/Augを月次walk-forward。','- CURRENTはv109と同じ全特徴。','- NO_EXHIBITION_STは当該レースの展示ST明示特徴 one_st / st_margin2 / st_margin3 / st_margin23 を除外して再学習。','- NO_ALL_STはさらに過去/今節ST系 one_nst_strength / one_waku_sr_strength / one_meet_st_strength も除外。','- one_direct / one_score / threat系には現行設計上STが一部内包されるため、NO_EXHIBITION_STは「展示STの明示的な追加価値」を測る保守的アブレーション。','- S閾値72%は固定。結果・払戻は特徴に不使用。','',
      '## Jun-Aug aggregate','|variant|R|AUC|Brier|S件数|S頭率|S平均p|','|---|---:|---:|---:|---:|---:|---:|']
    agg={}
    for name,features in VARIANTS.items():
        preds=[]
        for mo in MONTHS:
            first=date.fromisoformat(mo+'-01')
            tr=[r for r in src if date.fromisoformat(r['date'])<first]
            te=[r for r in src if r.get('month')==mo]
            m=fit(tr,features); pp=m.predict_proba(xm(te,features))[:,1]
            for r,p in zip(te,pp):
                out.append({'variant':name,'month':mo,'race_code':r.get('race_code',''),'p':p,'head_hit':ii(r.get('head_hit'))})
                preds.append((r,p))
        y=[ii(r.get('head_hit')) for r,p in preds]; p=np.asarray([p for r,p in preds])
        auc=roc_auc_score(y,p); br=brier_score_loss(y,p)
        s=[(r,pp) for r,pp in preds if pp>=S_CUT]; sh=sum(ii(r.get('head_hit')) for r,pp in s); sm=np.mean([pp for r,pp in s]) if s else 0
        agg[name]=(len(preds),auc,br,len(s),pct(sh,len(s)),sm*100)
        L.append(f'|{name}|{len(preds):,}|{auc:.4f}|{br:.5f}|{len(s):,}|{pct(sh,len(s)):.2f}%|{sm*100:.2f}%|')
    L += ['','## 月別S比較','|月|variant|S件数|S頭率|','|---|---|---:|---:|']
    for mo in MONTHS:
        for name in VARIANTS:
            q=[r for r in out if r['month']==mo and r['variant']==name and float(r['p'])>=S_CUT]
            h=sum(ii(r['head_hit']) for r in q);L.append(f'|{mo}|{name}|{len(q):,}|{pct(h,len(q)):.2f}%|')
    cur=agg['CURRENT']; no=agg['NO_EXHIBITION_ST']; allst=agg['NO_ALL_ST']
    L += ['','## 差分','',f'- 展示ST明示特徴を外したとき: AUC **{no[1]-cur[1]:+.4f}** / Brier **{no[2]-cur[2]:+.5f}** / S頭率 **{no[4]-cur[4]:+.2f}pt** / S件数 **{no[3]-cur[3]:+d}R**',
          f'- 全ST系を外したとき: AUC **{allst[1]-cur[1]:+.4f}** / Brier **{allst[2]-cur[2]:+.5f}** / S頭率 **{allst[4]-cur[4]:+.2f}pt** / S件数 **{allst[3]-cur[3]:+d}R**','',
          '## 判定ルール','- NO_EXHIBITION_STがCURRENTと同等以上なら、展示STの明示ウェイトは下げる余地あり。','- CURRENTがBrier/AUC/S頭率で一貫して優位なら、展示STは現状程度の情報価値あり。','- 差が小さい場合は「展示STは補助情報」で、直前判定で単独強調しない。']
    with open(OUT,'w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['variant','month','race_code','p','head_hit']);w.writeheader();w.writerows(out)
    open(SUMMARY,'w',encoding='utf-8').write('\n'.join(L)+'\n')
    print('\n'.join(L))
if __name__=='__main__':main()
