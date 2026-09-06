from __future__ import annotations
import csv
from collections import defaultdict

SRC='analysis_v160_v109_st_context_shadow.csv'
SUMMARY='summary_v161_st_context_confirmation_gate.md'
CURRENT_S=.72
THRESH=[.64,.66,.68,.70,.72,.74,.76]
MIN_JUL_N=600
MIN_COVERAGE=.70

def ff(x,d=0.0):
    try:return float(x)
    except:return d

def ii(x,d=0):
    try:return int(float(x))
    except:return d

def pct(n,d):return 100*n/d if d else 0.0

def read_csv(path):
    with open(path,encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def build():
    by=defaultdict(dict)
    for r in read_csv(SRC):
        key=(r['month'],r['race_code'])
        by[key][r['variant']]=r
    out=[]
    for (mo,code),d in by.items():
        if not all(k in d for k in ('CURRENT','FSTATE','NEIGHBOR','FSTATE_NEIGHBOR')):continue
        out.append({
          'month':mo,'race_code':code,'head_hit':ii(d['CURRENT']['head_hit']),
          'cur':ff(d['CURRENT']['p']),'f':ff(d['FSTATE']['p']),'n':ff(d['NEIGHBOR']['p']),'fn':ff(d['FSTATE_NEIGHBOR']['p'])})
    return out

def select(rs,kind,t):
    q=[r for r in rs if r['cur']>=CURRENT_S]
    if kind=='FSTATE':return [r for r in q if r['f']>=t]
    if kind=='NEIGHBOR':return [r for r in q if r['n']>=t]
    if kind=='BOTH_MIN':return [r for r in q if min(r['f'],r['n'])>=t]
    if kind=='BOTH_AVG':return [r for r in q if (r['f']+r['n'])/2>=t]
    if kind=='COMBINED':return [r for r in q if r['fn']>=t]
    raise ValueError(kind)

def met(q):
    n=len(q);h=sum(r['head_hit'] for r in q)
    return n,h,pct(h,n)

def main():
    rs=build();jul=[r for r in rs if r['month']=='2026-07'];aug=[r for r in rs if r['month']=='2026-08']
    jb=[r for r in jul if r['cur']>=CURRENT_S];ab=[r for r in aug if r['cur']>=CURRENT_S]
    jbn,jbh,jbr=met(jb);abn,abh,abr=met(ab)
    kinds=['FSTATE','NEIGHBOR','BOTH_MIN','BOTH_AVG','COMBINED']
    tuned=[]
    for k in kinds:
        cand=[]
        for t in THRESH:
            q=select(jul,k,t);n,h,hr=met(q);cov=n/jbn if jbn else 0
            if n>=MIN_JUL_N and cov>=MIN_COVERAGE:cand.append((hr,cov,n,t))
        if not cand:continue
        # tune on July only: maximize head rate, then coverage
        hr,cov,n,t=max(cand,key=lambda z:(z[0],z[1]))
        qa=select(aug,k,t);an,ah,ahr=met(qa);acov=an/abn if abn else 0
        tuned.append((k,t,n,hr,cov,an,ahr,acov))
    L=['# v161 ST-context confirmation gate','',
       '- v160でST contextをv109へ直接追加するとS頭率が低下したため、**CURRENT v109のS判定は固定したまま補助確認/vetoとして使えるか**を検証。',
       '- Julyだけで補助閾値を選び、Augustは untouched holdout。',
       f'- CURRENT S={CURRENT_S:.2f}固定。July候補は600R以上かつCURRENT Sの70%以上を残す条件。',
       '- Julyで頭率最大（同率ならcoverage最大）の閾値を選択し、Augustへそのまま適用。','',
       '## baseline','|月|R|頭率|','|---|---:|---:|',
       f'|2026-07 CURRENT S|{jbn}|{jbr:.2f}%|',f'|2026-08 CURRENT S|{abn}|{abr:.2f}%|','',
       '## July tune → August holdout','|policy|閾値|July R|July頭率|July coverage|Aug R|Aug頭率|Aug coverage|Aug Δ頭率|','|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for k,t,jn,jhr,jcov,an,ahr,acov in tuned:
        L.append(f'|{k}|{t:.2f}|{jn}|{jhr:.2f}%|{jcov*100:.1f}%|{an}|{ahr:.2f}%|{acov*100:.1f}%|{ahr-abr:+.2f}pt|')
    good=[x for x in tuned if x[6]>abr and x[7]>=MIN_COVERAGE]
    L+=['','## 判定']
    if good:
        best=max(good,key=lambda x:(x[6]-abr,x[7]))
        L.append(f'- Augustでも改善維持: **{best[0]} threshold {best[1]:.2f}** / Aug頭率 {best[6]:.2f}% ({best[6]-abr:+.2f}pt), coverage {best[7]*100:.1f}%。')
        L.append('- ただしproduction切替はせず、次はSep unseen shadowで同じ固定ルールを再確認する。')
    else:
        L.append('- AugustでCURRENTを上回りつつcoverage 70%以上を維持するpolicyなし。ST contextは説明用補助に留める。')
    open(SUMMARY,'w',encoding='utf-8').write('\n'.join(L)+'\n');print('\n'.join(L))

if __name__=='__main__':main()
