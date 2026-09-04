"""v102: all-model ticket-count hit probability + deadline/final composite odds.

User-approved reporting policy
- Final/deadline odds are allowed ONLY for post-hoc descriptive statistics.
- They must never affect candidate selection, score/grade, head selection,
  opponent ranking, ticket ordering, or any claimed no-leak prediction metric.

Prediction side remains frozen exactly as v101:
- source: v83 entry-gate analysis
- BASE score thresholds A>=55, S>=67
- v51 fixed 20-ticket ranking
- entry_gate_keep==1
- head truth recomputed as winner == predicted head

Final-odds source
- Kyotei24 Odds Bank historical 3T pages explicitly labelled 締切時オッズ.
- All 120 trifecta odds are parsed per race; composite odds for top N tickets are
  1 / sum(1/odds_i).
"""
from __future__ import annotations

import csv
import re
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from statistics import mean, median

SRC='analysis_v83_wind_entry_gate.csv'
OUT='analysis_v102_allmodels_final_composite_odds.csv'
SUMMARY='summary_v102_allmodels_final_composite_odds.md'
COVERAGE='coverage_v102_final_odds.csv'
START='2025-11-01'; END='2026-08-31'; A=55.0; S=67.0
MODELS=['3まくり','3まくり差し','4カドまくり','5頭展開']

SLUG={
'01':'kiryu','02':'toda','03':'edogawa','04':'heiwajima','05':'tamagawa','06':'hamanako',
'07':'gamagori','08':'tokoname','09':'tsu','10':'mikuni','11':'biwako','12':'suminoe',
'13':'amagasaki','14':'naruto','15':'marugame','16':'kojima','17':'miyajima','18':'tokuyama',
'19':'shimonoseki','20':'wakamatsu','21':'ashiya','22':'fukuoka','23':'karatsu','24':'omura'}
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

def compact_date(ds):return ds.replace('-','')

def normalized_code(r):
    code=(r.get('race_code') or r.get('レースコード') or '').strip()
    return code

def final_url(code):
    code=str(code).strip()
    if len(code)<12 or code[8:10] not in SLUG:return None
    slug=SLUG[code[8:10]]
    rn=int(code[10:12])
    return f'https://odds.kyotei24.jp/odds3t-{slug}-{code[:8]}-{rn}.html'

def parse_final_odds(html):
    if '締切時オッズ' not in html:return {},False
    vals={}
    for _,t,v in PAT.findall(html):
        try:
            z=float(v.replace(',','').strip())
            if z>1.0:vals[t]=z
        except Exception:pass
    return vals,True

def fetch_final(code):
    url=final_url(code)
    if not url:return code,{},False,'bad_code',''
    last=''
    for attempt in range(3):
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 (compatible; boatrace-backtest/1.0)'})
            with urllib.request.urlopen(req,timeout=20) as r:
                html=r.read().decode('utf-8','replace')
            vals,label=parse_final_odds(html)
            if label and len(vals)>=100:return code,vals,label,'',url
            last=f'parsed={len(vals)} label={label}'
        except Exception as e:last=f'{type(e).__name__}: {e}'
        time.sleep(0.25*(attempt+1))
    return code,{},False,last,url

def combo_odds(od,ts):
    vals=[]
    for t in ts:
        v=od.get(t)
        if v is None or v<=1.0:return None
        vals.append(v)
    den=sum(1.0/v for v in vals)
    return 1.0/den if den>0 else None

def grade_ok(r,g):
    s=ff(r.get('score'),-999)
    return s >= (S if g=='S' else A)

def main():
    raw=[r for r in read_csv(SRC) if START<=r.get('date','')<=END and r.get('model') in MODELS]
    base=[r for r in raw if ii(r.get('entry_gate_keep'))==1 and ii(r.get('valid_payout'))==1 and len(tickets(r))>=20]

    # Only A-or-better races need final odds because S is a subset of A.
    need=sorted({normalized_code(r) for r in base if ff(r.get('score'),-999)>=A and len(normalized_code(r))>=12})
    print('unique A+ races requiring final odds:',len(need),flush=True)
    fmap={}; cov=[]
    with ThreadPoolExecutor(max_workers=10) as ex:
        futs={ex.submit(fetch_final,c):c for c in need}
        done=0
        for fut in as_completed(futs):
            c,od,label,err,url=fut.result()
            done+=1
            if od:fmap[c]=od
            cov.append({'race_code':c,'final_odds_ok':1 if od else 0,'parsed_odds':len(od),'deadline_label':1 if label else 0,'error':err,'url':url})
            if done%100==0 or done==len(need):
                print(f'final odds {done}/{len(need)} ok={len(fmap)}',flush=True)

    cov.sort(key=lambda x:x['race_code'])
    with open(COVERAGE,'w',encoding='utf-8-sig',newline='') as f:
        fs=list(cov[0].keys()) if cov else ['race_code','final_odds_ok','parsed_odds','deadline_label','error','url']
        w=csv.DictWriter(f,fieldnames=fs);w.writeheader();w.writerows(cov)

    out=[]
    for g in ('A','S'):
        for m in MODELS:
            q=[r for r in base if r.get('model')==m and grade_ok(r,g)]
            head_hits=sum(ii(r.get('winner'))==ii(r.get('head')) for r in q)
            for n in range(1,21):
                hits=[r for r in q if ii(r.get('winner'))==ii(r.get('head')) and 1<=ii(r.get('actual_rank20'))<=n]
                hit=len(hits)
                ret=sum(ii(r.get('payout100')) for r in hits)
                inv=len(q)*n*100
                codds=[]
                for r in q:
                    od=fmap.get(normalized_code(r))
                    if not od:continue
                    co=combo_odds(od,tickets(r)[:n])
                    if co is not None:codds.append(co)
                rec={
                    'grade':g,'model':m,'tickets_n':n,'candidate_races':len(q),'head_hits':head_hits,
                    'head_rate_pct':pct(head_hits,len(q)),
                    'ticket_hits':hit,'overall_hit_rate_pct':pct(hit,len(q)),
                    'coverage_given_head_pct':pct(hit,head_hits),
                    'equal_stake_roi_pct':pct(ret,inv),
                    'avg_hit_payout_yen':mean([ii(r.get('payout100')) for r in hits]) if hits else 0,
                    'final_odds_races':len(codds),'final_odds_coverage_pct':pct(len(codds),len(q)),
                    'avg_final_composite_odds':mean(codds) if codds else 0,
                    'median_final_composite_odds':median(codds) if codds else 0,
                }
                out.append(rec)

    with open(OUT,'w',encoding='utf-8-sig',newline='') as f:
        fs=list(out[0].keys());w=csv.DictWriter(f,fieldnames=fs);w.writeheader();w.writerows(out)

    ok=len(fmap); total=len(need)
    L=['# v102 全モデル 点数別 頭率・総合的中率・確定合成オッズ','',
       f'- 集計期間: **{START}〜{END}**。',
       '- 予測側はv101と同じく **現行BASE score + 現行v51固定20通り順位 + v83進入変更除外**。',
       '- 頭率は **winner == 予測head** から再計算。',
       '- 「総合的中率」= 予測頭が1着かつ実3連単が上位N点以内 ÷ 対象レース数。',
       '- 「頭内カバー」= 実3連単が上位N点以内 ÷ 頭的中数。',
       '- 確定合成オッズ = **1 / Σ(1/各買い目の締切時確定オッズ)**。',
       '- 確定オッズ出典: Kyotei24 Odds Bankの歴史3連単ページ（ページ表記 `締切時オッズ`）。',
       '- **確定オッズは事後集計専用。候補抽出・score・grade・頭選択・相手順位・買い目順位には一切使用していない。**',
       f'- A以上ユニーク対象レースの確定オッズ取得: **{ok}/{total} = {pct(ok,total):.1f}%**。','']

    for g in ('A','S'):
        L += [f'## {g}以上','']
        for m in MODELS:
            rr=[x for x in out if x['grade']==g and x['model']==m]
            if not rr:continue
            h=rr[0]
            L += [f'### {m} — {h["candidate_races"]}R / 頭率 {h["head_rate_pct"]:.1f}%',
                  '|点数|総合的中率|頭内カバー|平均確定合成オッズ|中央値|odds R|oddsカバー|等額ROI|',
                  '|---:|---:|---:|---:|---:|---:|---:|---:|']
            for x in rr:
                a=f'{x["avg_final_composite_odds"]:.2f}倍' if x['final_odds_races'] else '-'
                md=f'{x["median_final_composite_odds"]:.2f}倍' if x['final_odds_races'] else '-'
                L.append(f'|{x["tickets_n"]}|{x["overall_hit_rate_pct"]:.1f}%|{x["coverage_given_head_pct"]:.1f}%|{a}|{md}|{x["final_odds_races"]}|{x["final_odds_coverage_pct"]:.1f}%|{x["equal_stake_roi_pct"]:.1f}%|')
            L.append('')

    L += ['## 読み方',
          '- 確定合成オッズは、上位N点を同一払戻になるようダッチングした場合の理論倍率。',
          '- 等額ROIは各買い目100円均等購入の実払戻ベースで、確定合成オッズとは別指標。',
          '- 確定オッズは結果後にしか確定しないため、モデル性能の事後評価には使えるが、予測時の選別条件には使わない。']
    with open(SUMMARY,'w',encoding='utf-8') as f:f.write('\n'.join(L)+'\n')
    print('\n'.join(L),flush=True)

if __name__=='__main__':main()
