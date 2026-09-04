"""v103: value-aware opponent/ticket reranking without current-race odds leakage.

Goal
- Lower final composite implied-rate while preserving trifecta hit rate as much as possible.
- Candidate/head/grade remain frozen from v83/v101.
- Current-race final odds are NEVER used to rank that race.

Value feature
- For each model + exact trifecta ticket, maintain the mean final implied probability
  (1/final_odds) using STRICTLY PRIOR DATES only.
- On each race date, convert the 20 exact tickets into a prior-price rank:
  historically lower implied probability (higher price) = higher value score.
- Blend current fixed ticket rank with this prior-only value score.

Tuning / holdout
- Warmup: 2025-11-01..2026-02-28
- Validation: 2026-03-01..2026-05-31; choose one lambda per model on A+ only.
- Holdout: 2026-06-01..2026-08-31; lambda frozen; report A/S separately.
- Lambda grid: 0, .05, .10, .15, .20, .25, .30.
- Validation non-inferiority across N in {4,6,7,8,10}:
    average overall hit rate >= baseline - 0.5pt
    no individual N drop > 1.0pt
  Among admissible lambdas choose the largest average composite implied-rate reduction;
  tie -> smaller lambda.

Final odds are historical training labels / post-hoc evaluation only; no same-race
final odds enter prediction-side reranking.
"""
from __future__ import annotations

import csv
import re
import time
import urllib.request
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from statistics import mean

SRC='analysis_v83_wind_entry_gate.csv'
OUT='analysis_v103_value_aware_opponent_ranking.csv'
SUMMARY='summary_v103_value_aware_opponent_ranking.md'
START='2025-11-01'; END='2026-08-31'; A=55.0; S=67.0
WARM_END='2026-02-28'; VAL_START='2026-03-01'; VAL_END='2026-05-31'; TEST_START='2026-06-01'; TEST_END='2026-08-31'
MODELS=['3まくり','3まくり差し','4カドまくり','5頭展開']
LAMBDAS=[0.0,0.05,0.10,0.15,0.20,0.25,0.30]
TUNE_N=[4,6,7,8,10]

SLUG={'01':'kiryu','02':'toda','03':'edogawa','04':'heiwajima','05':'tamagawa','06':'hamanako','07':'gamagori','08':'tokoname','09':'tsu','10':'mikuni','11':'biwako','12':'suminoe','13':'amagasaki','14':'naruto','15':'marugame','16':'kojima','17':'miyajima','18':'tokuyama','19':'shimonoseki','20':'wakamatsu','21':'ashiya','22':'fukuoka','23':'karatsu','24':'omura'}
PAT=re.compile(r'<div id="dm-(\d+)"[^>]*>\s*([1-6]-[1-6]-[1-6])\s*</div>.*?<div id="od-\1"[^>]*>\s*([^<]+?)\s*</div>',re.S)

def ff(x,d=None):
    try:
        if x is None or str(x).strip()=='': return d
        return float(x)
    except Exception:return d

def ii(x,d=0):
    try:return int(float(x))
    except Exception:return d

def pct(n,d):return 100*n/d if d else 0.0

def read_csv(path):
    with open(path,encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def tickets(r):
    return [x.strip() for x in (r.get('tickets20_display') or '').split(';') if x.strip()][:20]

def code(r):return (r.get('race_code') or '').strip()

def final_url(c):
    if len(c)<12 or c[8:10] not in SLUG:return None
    return f'https://odds.kyotei24.jp/odds3t-{SLUG[c[8:10]]}-{c[:8]}-{int(c[10:12])}.html'

def parse_final(html):
    if '締切時オッズ' not in html:return {}
    d={}
    for _,t,v in PAT.findall(html):
        try:
            z=float(v.replace(',','').strip())
            if z>1:d[t]=z
        except Exception:pass
    return d

def fetch_final(c):
    u=final_url(c)
    if not u:return c,{}
    for k in range(3):
        try:
            req=urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0 (compatible; boatrace-backtest/1.0)'})
            with urllib.request.urlopen(req,timeout=20) as resp: html=resp.read().decode('utf-8','replace')
            d=parse_final(html)
            if len(d)>=100:return c,d
        except Exception:pass
        time.sleep(.2*(k+1))
    return c,{}

def composite_rate(od, ts):
    vals=[]
    for t in ts:
        o=od.get(t)
        if o is None or o<=1:return None
        vals.append(o)
    return 100.0*sum(1.0/o for o in vals)

def rerank(base_tickets, model, lam, hist_sum, hist_n):
    # Baseline score: rank1=1, rank20=0.
    bscore={t:1.0-(i/19.0) for i,t in enumerate(base_tickets)}
    # Prior-only mean implied probability for exact ticket within model.
    # Warm period supplies enough observations; missing keys stay neutral by baseline order.
    vals=[]
    for i,t in enumerate(base_tickets):
        k=(model,t); n=hist_n.get(k,0)
        p=(hist_sum.get(k,0.0)/n) if n>=15 else None
        vals.append((t,p,i))
    known=[x for x in vals if x[1] is not None]
    known_sorted=sorted(known,key=lambda x:(x[1],x[2])) # low implied = high value
    vrank={t:i for i,(t,_,_) in enumerate(known_sorted)}
    denom=max(1,len(known_sorted)-1)
    vscore={}
    for t,p,i in vals:
        if p is None:
            vscore[t]=bscore[t]  # neutral fallback = no movement pressure
        else:
            vscore[t]=1.0-(vrank[t]/denom)
    scored=[((1-lam)*bscore[t]+lam*vscore[t], -i, t) for i,t in enumerate(base_tickets)]
    scored.sort(reverse=True)
    return [x[2] for x in scored]

def build_rows(base, fmap):
    # Strict prior-date histories: score a full day, then update history with that day's final odds.
    bydate=defaultdict(list)
    for r in base:bydate[r['date']].append(r)
    hist_sum=defaultdict(float); hist_n=defaultdict(int)
    allrows=[]
    for ds in sorted(bydate):
        day=bydate[ds]
        for r in day:
            bt=tickets(r); od=fmap.get(code(r),{})
            if len(bt)<20:continue
            rec={'date':ds,'model':r['model'],'score':ff(r.get('score'),-999),'head':ii(r.get('head')),
                 'winner':ii(r.get('winner')),'actual_combo':(r.get('actual_combo') or '').strip(),
                 'payout100':ii(r.get('payout100')),'base':bt,'od':od}
            rec['orders']={lam:rerank(bt,r['model'],lam,hist_sum,hist_n) for lam in LAMBDAS}
            allrows.append(rec)
        # update only after all races of date were scored
        for r in day:
            od=fmap.get(code(r),{})
            if not od:continue
            m=r['model']
            for t,o in od.items():
                if o>1:
                    hist_sum[(m,t)] += 1.0/o
                    hist_n[(m,t)] += 1
    return allrows

def eligible(rows,model,grade,start,end):
    th=S if grade=='S' else A
    return [r for r in rows if r['model']==model and start<=r['date']<=end and r['score']>=th]

def metrics(q, lam, n):
    hits=0; rates=[]; ret=0
    for r in q:
        order=r['orders'][lam]
        sel=order[:n]
        hit=(r['winner']==r['head'] and r['actual_combo'] in sel)
        if hit:
            hits+=1; ret += r['payout100']
        cr=composite_rate(r['od'],sel) if r['od'] else None
        if cr is not None:rates.append(cr)
    return {'races':len(q),'hits':hits,'hit_rate':pct(hits,len(q)),'avg_comp_rate':mean(rates) if rates else None,
            'odds_races':len(rates),'roi':pct(ret,len(q)*n*100) if q else 0.0}

def choose_lambda(rows,model):
    q=eligible(rows,model,'A',VAL_START,VAL_END)
    base={n:metrics(q,0.0,n) for n in TUNE_N}
    base_hit=mean(x['hit_rate'] for x in base.values())
    base_imp=mean(x['avg_comp_rate'] for x in base.values() if x['avg_comp_rate'] is not None)
    cand=[]
    for lam in LAMBDAS:
        mm={n:metrics(q,lam,n) for n in TUNE_N}
        avg_hit=mean(x['hit_rate'] for x in mm.values())
        avg_imp=mean(x['avg_comp_rate'] for x in mm.values() if x['avg_comp_rate'] is not None)
        max_drop=max(base[n]['hit_rate']-mm[n]['hit_rate'] for n in TUNE_N)
        admiss=(avg_hit>=base_hit-0.5-1e-9 and max_drop<=1.0+1e-9)
        cand.append((lam,admiss,avg_hit,avg_imp,base_imp-avg_imp,max_drop,mm))
    ok=[x for x in cand if x[1]]
    best=max(ok,key=lambda x:(x[4],-x[0])) if ok else cand[0]
    return best,cand,base

def main():
    raw=[r for r in read_csv(SRC) if START<=r.get('date','')<=END and r.get('model') in MODELS]
    base=[r for r in raw if ii(r.get('entry_gate_keep'))==1 and ii(r.get('valid_payout'))==1 and len(tickets(r))>=20 and ff(r.get('score'),-999)>=A]
    need=sorted({code(r) for r in base if len(code(r))>=12})
    print('need odds',len(need),flush=True)
    fmap={}
    with ThreadPoolExecutor(max_workers=12) as ex:
        futs={ex.submit(fetch_final,c):c for c in need}
        done=0
        for f in as_completed(futs):
            c,d=f.result(); done+=1
            if d:fmap[c]=d
            if done%100==0 or done==len(need):print('odds',done,'/',len(need),'ok',len(fmap),flush=True)
    rows=build_rows(base,fmap)
    selected={}; tuning={}
    for m in MODELS:
        best,cand,b=choose_lambda(rows,m); selected[m]=best[0]; tuning[m]=(best,cand,b)
        print('selected',m,best[:6],flush=True)

    out=[]
    for g in ('A','S'):
        for m in MODELS:
            q=eligible(rows,m,g,TEST_START,TEST_END); lam=selected[m]
            for n in range(1,21):
                b=metrics(q,0.0,n); v=metrics(q,lam,n)
                out.append({'grade':g,'model':m,'lambda':lam,'tickets_n':n,'races':len(q),
                    'base_hits':b['hits'],'value_hits':v['hits'],'base_hit_rate_pct':b['hit_rate'],'value_hit_rate_pct':v['hit_rate'],
                    'hit_rate_diff_pt':v['hit_rate']-b['hit_rate'],'base_comp_rate_pct':b['avg_comp_rate'] or 0,
                    'value_comp_rate_pct':v['avg_comp_rate'] or 0,'comp_rate_diff_pt':(v['avg_comp_rate'] or 0)-(b['avg_comp_rate'] or 0),
                    'base_roi_pct':b['roi'],'value_roi_pct':v['roi'],'odds_races':v['odds_races']})
    with open(OUT,'w',encoding='utf-8-sig',newline='') as f:
        fs=list(out[0].keys());w=csv.DictWriter(f,fieldnames=fs);w.writeheader();w.writerows(out)

    L=['# v103 的中率維持 × 合成オッズ率低下 相手選び検証','',
       f'- warmup: {START}〜{WARM_END}',f'- λ選定(validation): {VAL_START}〜{VAL_END}',f'- 完全固定holdout: {TEST_START}〜{TEST_END}',
       '- 当該レースの確定オッズは相手順位に不使用。価格補正は **その日より前の確定オッズだけ** から作った「モデル×3連単パターン」の平均市場人気傾向。',
       '- candidate/head/score/grade/entry gateは現行のまま。変更するのは20通りの順序だけ。',
       '- 合成オッズ率 = 100 / 合成オッズ = 100×Σ(1/各買い目オッズ)。低いほど高配当側。','']
    L += ['## validationで選ばれたλ','', '|モデル|λ|平均的中率差条件|平均合成率低下|最大1点数的中率低下|','|---|---:|---:|---:|---:|']
    for m in MODELS:
        best=tuning[m][0]
        L.append(f'|{m}|{best[0]:.2f}|{best[2]-mean(x["hit_rate"] for x in tuning[m][2].values()):+.2f}pt|{best[4]:+.2f}pt|{-best[5]:+.2f}pt|')
    L += ['', '## holdout（2026-06〜08）代表点数', '']
    for g in ('A','S'):
        L += [f'### {g}以上','', '|モデル|λ|点数|現行的中率|value的中率|差|現行合成率|value合成率|低下幅|現行ROI|value ROI|','|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
        for m in MODELS:
            rr=[x for x in out if x['grade']==g and x['model']==m and x['tickets_n'] in TUNE_N]
            for x in rr:
                L.append(f'|{m}|{x["lambda"]:.2f}|{x["tickets_n"]}|{x["base_hit_rate_pct"]:.1f}%|{x["value_hit_rate_pct"]:.1f}%|{x["hit_rate_diff_pt"]:+.1f}pt|{x["base_comp_rate_pct"]:.1f}%|{x["value_comp_rate_pct"]:.1f}%|{-x["comp_rate_diff_pt"]:+.1f}pt|{x["base_roi_pct"]:.1f}%|{x["value_roi_pct"]:.1f}%|')
        L.append('')
    L += ['## 判定ルール','- holdoutで的中率が大きく落ちるモデルは不採用。','- 合成オッズ率が下がっても、的中率低下がそれ以上なら価値なし。','- v103は診断/候補でありproduction自動採用ではない。']
    with open(SUMMARY,'w',encoding='utf-8') as f:f.write('\n'.join(L)+'\n')
    print('\n'.join(L),flush=True)

if __name__=='__main__':main()
