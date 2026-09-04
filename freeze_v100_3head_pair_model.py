"""v100: freeze the 3HEAD second/third role model for prospective use.

Prospective start: 2026-09-05.
Source rows stop at 2026-08-31, so no future/prospective outcome can enter training.
This freezes only opponent 2nd/3rd ordering. Head candidate/grade logic is unchanged.
5HEAD is unchanged.
"""
from __future__ import annotations
import csv,json,math,hashlib
from pathlib import Path

SRC='analysis_v97_3head5head_second_third.csv'
OUT='v100_3head_pair_frozen_20260905.json'
SUMMARY='summary_v100_3head_pair_freeze.md'
LAM=.2
HEAD=3
BOATS=(1,2,4,5,6)
FEATS=('grade','national','local','motor','waku','nst','direct')
L2=.15
ITERS=700
LR=.22
TRAIN_END='2026-08-31'
PROSPECTIVE_START='2026-09-05'


def ff(x,d=0.):
    try:
        if x is None or str(x).strip()=='': return d
        return float(x)
    except Exception:return d

def ii(x,d=0):
    try:return int(float(x))
    except Exception:return d

def read():
    with open(SRC,encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def elig(r):
    return (r.get('group_v97')=='3HEAD' and ii(r.get('entry_gate_keep'))==1 and
            ii(r.get('valid_result'))==1 and r.get('date','')<=TRAIN_END)
def rawfeat(r,b):
    return [ff(r.get(f'opp_{k}_b{b}_v97'),.5) for k in FEATS]
def trainrows(rs):
    return [r for r in rs if elig(r) and ii(r.get('winner'))==HEAD and
            ii(r.get('second')) in BOATS and ii(r.get('third')) in BOATS]

def scalers(tr):
    vals=[[] for _ in FEATS]
    for r in tr:
        for b in BOATS:
            for j,v in enumerate(rawfeat(r,b)): vals[j].append(v)
    mu=[];sd=[]
    for a in vals:
        m=sum(a)/len(a) if a else 0.
        s=math.sqrt(sum((v-m)**2 for v in a)/len(a)) if a else 1.
        mu.append(m);sd.append(s if s>1e-9 else 1.)
    return mu,sd

def xvec(r,b,mu,sd):
    z=[(v-mu[j])/sd[j] for j,v in enumerate(rawfeat(r,b))]
    z += [1. if b==k else 0. for k in BOATS]
    return z

def fit(tr,target,mu,sd):
    p=len(FEATS)+len(BOATS);w=[0.]*p
    for it in range(ITERS):
        g=[0.]*p;n=0
        for r in tr:
            y=ii(r.get(target));xs=[xvec(r,b,mu,sd) for b in BOATS]
            ss=[sum(w[j]*x[j] for j in range(p)) for x in xs]
            mx=max(ss);es=[math.exp(s-mx) for s in ss];den=sum(es)
            for bi,b in enumerate(BOATS):
                e=es[bi]/den-(1. if b==y else 0.)
                for j in range(p): g[j]+=e*xs[bi][j]
            n+=1
        if not n: break
        lr=LR/math.sqrt(1+it/120)
        for j in range(p): w[j]-=lr*(g[j]/n+L2*w[j])
    return w

def main():
    rs=read();tr=trainrows(rs);mu,sd=scalers(tr)
    w2=fit(tr,'second',mu,sd);w3=fit(tr,'third',mu,sd)
    src_sha=hashlib.sha256(Path(SRC).read_bytes()).hexdigest()
    model={
      'version':'v100','status':'PROSPECTIVE_CANDIDATE_NOT_PRODUCTION',
      'prospective_start':PROSPECTIVE_START,'training_end':TRAIN_END,
      'training_head_hit_rows':len(tr),'lambda':LAM,'head':HEAD,
      'boats':list(BOATS),'features':list(FEATS),'l2':L2,'iters':ITERS,'lr':LR,
      'mu':dict(zip(FEATS,mu)),'sd':dict(zip(FEATS,sd)),
      'weight_labels':list(FEATS)+[f'boat_{b}' for b in BOATS],
      'w_second':w2,'w_third':w3,
      'source_file':SRC,'source_sha256':src_sha,
      'rules':{
        'head_selection':'UNCHANGED','grade_thresholds':'UNCHANGED',
        'entry_gate':'target boat 3 must remain exhibition course 3',
        'current_anchor_weight':0.8,'role_weight':0.2,
        'five_head':'UNCHANGED_CURRENT_V51'
      }
    }
    Path(OUT).write_text(json.dumps(model,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    L=['# v100 3頭 2着/3着 prospective固定モデル','',
       f'- prospective開始: **{PROSPECTIVE_START}**',
       f'- 学習データ最終日: **{TRAIN_END}**',
       f'- 学習対象（3頭が実際に1着、entry gate通過）: **{len(tr)}R**',
       f'- λ: **{LAM}固定**（現行相手点80% + 役割別20%）',
       '- 変更対象: **3頭の2着/3着の並びだけ**',
       '- 3まくり/3まくり差しの候補抽出、頭score、A/S、進入除外、風評価は変更しない。',
       '- 5頭は変更しない。現行v51相手順位を維持。','',
       '## prospective運用',
       '- 9/5以降の3頭A/Sで、結果を見る前にCURRENTとV100の4点/6点を両方凍結して記録する。',
       '- 同一レースの3まくり/3まくり差し重複は、結果前の頭score上位だけを採用する。',
       '- V100の重み・λはprospective期間中に変更しない。変更した場合は別versionとして再スタートする。',
       '- 正式production採用まではV100はshadow候補扱い。','',
       '## 正式採用の事前条件',
       '- prospectiveでA以上 **100R以上** かつ3号艇頭的中 **30R以上** を最低観測数とする。',
       '- CURRENTと同点数で比較し、Aの4点・6点coverageがともに非悪化。',
       '- 4点/6点のどちらかでcoverage **+3.0pt以上**。',
       '- equal-stake ROIは4点・6点ともCURRENT比 **-5pt以内**。',
       '- 条件達成後にのみ正式production採用を再判定する。']
    Path(SUMMARY).write_text('\n'.join(L)+'\n',encoding='utf-8')
    print('\n'.join(L))

if __name__=='__main__': main()
