"""v115: 1号艇 v109+v110 fixed-7 pre-odds race filter diagnostic.

Purpose
- Keep v109 head selection and v110 7-ticket order frozen.
- Do NOT use any current/final odds.
- Learn whether pre-race strength / threat / exhibition / ticket-structure features can identify
  races where the fixed v110 7 tickets are more likely to hit, and thereby improve equal-stake ROI.

Sequential design
- June 2026: fit one conservative logistic filter on A+ races only.
- July 2026: choose ONE probability threshold using both A and S with sample/selection guards.
- August 2026: apply the June-fitted model + July-fixed threshold without refitting.

Important
- August has already been inspected in v111-v114, so v115 is a historical diagnostic, NOT a
  pristine adoption test. Even a strong result must be confirmed prospectively from 2026-09-05.
- Outcome/payout are labels/settlement only after all input features and v110 ticket order were frozen.
"""
from __future__ import annotations

import csv, math
from collections import Counter
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer

SRC='analysis_v110_1head_role_tickets.csv'
OUT='analysis_v115_1head_preodds_race_filter.csv'
SUMMARY='summary_v115_1head_preodds_race_filter.md'
A_CUT=.65
S_CUT=.72
THRESHOLDS=[round(x,3) for x in np.arange(.30,.751,.025)]

NUM=[
 'p109','one_grade','one_wr','one_local','one_motor','one_waku_wr','one_nst_strength',
 'one_waku_sr_strength','one_past_win','one_meet_st_strength',
 'one_ex','one_st','one_lap','one_turn','one_straight','one_orig_avg','one_direct','one_score',
 'threat2','threat3','threat4','threat5','threat6','threat23_max','threat_all_max',
 'margin2','margin3','margin23','margin_all','st_margin2','st_margin3','st_margin23',
 'ex_margin23','turn_margin23','straight_margin23'
]


def ff(x,d=0.0):
    try:return float(x)
    except Exception:return d

def ii(x,d=0):
    try:return int(float(x))
    except Exception:return d

def pct(n,d):return 100*n/d if d else 0.0

def read_csv(path):
    with open(path,encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def split20(s):return [x.strip() for x in (s or '').split(';') if x.strip()]

def ticket_structure(r):
    v=split20(r.get('v110_20'));c=split20(r.get('current20'))
    v7=v[:7];c7=c[:7]
    def parts(k):
        try:
            a=[int(x) for x in k.split('-')]
            return a if len(a)==3 else [0,0,0]
        except Exception:return [0,0,0]
    s2=[parts(k)[1] for k in v7];s3=[parts(k)[2] for k in v7]
    f2=Counter(s2);f3=Counter(s3)
    overlap=len(set(v7)&set(c7))/7 if v7 else 0.0
    curpos={k:i+1 for i,k in enumerate(c)}
    vpos={k:i+1 for i,k in enumerate(v)}
    cur_r=[curpos.get(k,20) for k in v7]
    common=[k for k in v if k in curpos]
    disp=[abs(vpos[k]-curpos[k]) for k in common]
    return [
      overlap,
      len(set(s2))/5 if s2 else 0.0,
      len(set(s3))/5 if s3 else 0.0,
      (max(f2.values())/7 if f2 else 0.0),
      (max(f3.values())/7 if f3 else 0.0),
      (sum(cur_r)/len(cur_r)/20 if cur_r else 1.0),
      (sum(disp)/len(disp)/20 if disp else 0.0),
    ]

def vec(r):
    a=[ff(r.get(k),0.0) for k in NUM]
    a.extend(ticket_structure(r))
    vv=str(r.get('venue','')).zfill(2)
    a.extend(1.0 if vv==f'{i:02d}' else 0.0 for i in range(1,25))
    return a

def grade_ok(r,g):return ff(r.get('p109'),-1)>=(S_CUT if g=='S' else A_CUT)
def hit7(r):return 1 if 0<ii(r.get('v110_rank20'))<=7 else 0

def valid(r):return ii(r.get('valid_payout'))==1 and ff(r.get('p109'),-1)>=A_CUT

def fit_filter(rs):
    q=[r for r in rs if valid(r)]
    X=np.asarray([vec(r) for r in q],dtype=float);y=np.asarray([hit7(r) for r in q],dtype=int)
    if len(q)<300 or len(set(y))<2:raise RuntimeError(f'not enough June filter rows: {len(q)}')
    m=Pipeline([
      ('imp',SimpleImputer(strategy='median')),
      ('scale',StandardScaler()),
      ('lr',LogisticRegression(C=.15,max_iter=2000,solver='lbfgs')),
    ])
    m.fit(X,y)
    return m,len(q),int(y.sum())

def attach_score(model,rs):
    q=[]
    for r0 in rs:
        r=dict(r0)
        if ff(r.get('p109'),-1)<0:continue
        r['v115_filter_p']=float(model.predict_proba(np.asarray([vec(r)],dtype=float))[0,1])
        q.append(r)
    return q

def metric(rs,g,thr=None):
    q=[r for r in rs if ii(r.get('valid_payout'))==1 and grade_ok(r,g)]
    base_n=len(q)
    if thr is not None:q=[r for r in q if ff(r.get('v115_filter_p'))>=thr]
    n=len(q);hits=sum(hit7(r) for r in q);heads=sum(ii(r.get('head_hit'))==1 for r in q)
    ret=sum(ii(r.get('payout100')) for r in q if hit7(r))
    roi=pct(ret,n*700)
    return {'base_n':base_n,'n':n,'sel_pct':pct(n,base_n),'hits':hits,'hit_pct':pct(hits,n),
            'head_pct':pct(heads,n),'roi_pct':roi}

def choose_threshold(jul):
    ba=metric(jul,'A');bs=metric(jul,'S')
    rows=[]
    for th in THRESHOLDS:
        a=metric(jul,'A',th);s=metric(jul,'S',th)
        sample=(a['n']>=150 and s['n']>=90 and 20<=a['sel_pct']<=80 and 20<=s['sel_pct']<=80)
        hit_guard=(a['hit_pct']>=ba['hit_pct']-1.0 and s['hit_pct']>=bs['hit_pct']-1.0)
        admissible=sample and hit_guard
        da=a['roi_pct']-ba['roi_pct'];ds=s['roi_pct']-bs['roi_pct']
        rows.append((th,admissible,min(da,ds),(da+ds)/2,a,s))
    good=[x for x in rows if x[1]]
    if good:
        best=max(good,key=lambda x:(x[2],x[3],-x[0]))
    else:
        sample=[x for x in rows if x[4]['n']>=150 and x[5]['n']>=90]
        best=max(sample or rows,key=lambda x:(x[2],x[3],-x[0]))
    return best,rows,ba,bs

def main():
    src=read_csv(SRC)
    jun=[r for r in src if r.get('month')=='2026-06']
    jul=[r for r in src if r.get('month')=='2026-07']
    aug=[r for r in src if r.get('month')=='2026-08']
    model,ntrain,htrain=fit_filter(jun)
    jul_s=attach_score(model,jul);aug_s=attach_score(model,aug)
    selected,sweep,jba,jbs=choose_threshold(jul_s)
    th=selected[0]

    # Save July/Aug scored rows for audit. No result-derived field enters vec().
    out=[]
    for phase,rs in [('VALIDATION',jul_s),('HISTORICAL_TEST',aug_s)]:
        for r in rs:
            q=dict(r);q['v115_phase']=phase;q['v115_threshold']=th
            q['v115_selected_A']=int(grade_ok(q,'A') and ff(q.get('v115_filter_p'))>=th)
            q['v115_selected_S']=int(grade_ok(q,'S') and ff(q.get('v115_filter_p'))>=th)
            out.append(q)
    fs=sorted(set().union(*(r.keys() for r in out)))
    with open(OUT,'w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fs);w.writeheader();w.writerows(out)

    aba=metric(aug_s,'A');abs_=metric(aug_s,'S')
    aa=metric(aug_s,'A',th);ass=metric(aug_s,'S',th)
    pass_sample=(aa['n']>=200 and ass['n']>=100 and aa['sel_pct']>=20 and ass['sel_pct']>=20)
    pass_hit=(aa['hit_pct']>=aba['hit_pct'] and ass['hit_pct']>=abs_['hit_pct'])
    pass_roi=(aa['roi_pct']>=aba['roi_pct']+5 and ass['roi_pct']>=abs_['roi_pct']+5)
    op=(aa['roi_pct']>=100 and ass['roi_pct']>=100 and pass_sample and pass_hit)
    candidate=(pass_sample and pass_hit and pass_roi and aa['roi_pct']>=90 and ass['roi_pct']>=90)

    L=['# v115 1号艇 fixed7 事前レースfilter（オッズ不使用）','',
       '- v109の頭判定、v110 λ=0.50の7点順位は固定。**買うレース/見送るレースだけ**を事前特徴で判定。',
       '- current/final/pre-closeを含め **オッズは一切featureに使わない**。',
       '- filter feature: p109、1号艇選手/モーター/枠/ST/展示/オリジナル展示、2〜6号艇threatとmargin、v110 top7の構造・current7との重なり、場コード。',
       '- Juneだけでfilter学習 → Julyだけで閾値1個を固定 → Augustへそのまま適用。Augustで再学習・再調整なし。',
       '- 注意: August結果はv111-v114ですでに確認済みなので、このv115は **historical diagnostic**。良くてもproduction即採用は禁止。','',
       f'- June filter学習: **{ntrain:,}R** / fixed7 hit **{pct(htrain,ntrain):.1f}%**','',
       '## July threshold selection','|閾値|A選択R|A選択率|A的中率|A ROI|S選択R|S選択率|S的中率|S ROI|admissible|','|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|']
    for x in sweep:
        t,ok,_,_,a,s=x
        L.append(f'|{t:.3f}|{a["n"]}|{a["sel_pct"]:.1f}%|{a["hit_pct"]:.1f}%|{a["roi_pct"]:.1f}%|{s["n"]}|{s["sel_pct"]:.1f}%|{s["hit_pct"]:.1f}%|{s["roi_pct"]:.1f}%|{"YES" if ok else "NO"}|')
    L+=['',f'選択閾値 = **{th:.3f}**（Julyで固定）','',
        '## August historical test','|層|方式|R|購入率|7点的中率|頭率|均等買いROI|ROI差|','|---|---|---:|---:|---:|---:|---:|---:|']
    for g,b,a in [('A',aba,aa),('S',abs_,ass)]:
        L.append(f'|{g}|v110固定7点 全買い|{b["n"]}|100.0%|{b["hit_pct"]:.1f}%|{b["head_pct"]:.1f}%|{b["roi_pct"]:.1f}%|-|')
        L.append(f'|{g}|v115 filter|{a["n"]}|{a["sel_pct"]:.1f}%|{a["hit_pct"]:.1f}%|{a["head_pct"]:.1f}%|{a["roi_pct"]:.1f}%|{a["roi_pct"]-b["roi_pct"]:+.1f}pt|')
    L+=['','## 判定',
        f'- sample guard: **{"PASS" if pass_sample else "FAIL"}**',
        f'- A/Sとも7点的中率 非悪化: **{"PASS" if pass_hit else "FAIL"}**',
        f'- A/SともROI +5pt以上: **{"PASS" if pass_roi else "FAIL"}**',
        f'- A/SともROI100%以上: **{"YES" if op else "NO"}**',
        f'- **V115 HISTORICAL CANDIDATE = {"YES" if candidate else "NO"}**',
        '- candidate YESでも2026-09-05以降のprospective shadowで確認するまでproduction採用しない。',
        '- candidate NOならv109/v110は維持し、固定7点の事前レースfilterも不採用。']
    open(SUMMARY,'w',encoding='utf-8').write('\n'.join(L)+'\n')

if __name__=='__main__':main()
