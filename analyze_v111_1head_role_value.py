"""v111: 1号艇 v110 role順位 + strictly-prior price overlay.

Goal
- Keep the strong v109 head selection and v110 role ticket hit rate.
- Lower race-level composite implied rate (100*sum(1/final_odds)) using only
  historical final-odds tendencies from STRICTLY EARLIER DATES.

No-leak
- Head selection: v108 p1 for Mar-May validation, v109 monthly-WF p109 for Jun-Aug.
- Role order: v110 lambda=.50, refit monthly using strictly earlier 1-head wins.
- Current race final odds NEVER enter ranking.
- All races on a date are scored before that date's odds are added to price history.
- Mar-May chooses ONE value lambda; Jun-Aug is untouched frozen holdout.
- Current-race final odds are used only after ranking for composite-rate evaluation.
"""
from __future__ import annotations

import csv, os
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from statistics import mean

import analyze_v110b_1head_role_tickets as r110
import analyze_v104b_role_value_hybrid_cached as ocache

SRC='analysis_v108_1head_feasibility.csv'
HEADSRC='analysis_v109_1head_monthly_walkforward.csv'
OLD_CACHE='cache_v104_final_odds.csv'
CACHE='cache_v111_1head_final_odds.csv'
OUT='analysis_v111_1head_role_value.csv'
SUMMARY='summary_v111_1head_role_value.md'
VAL_MONTHS=['2026-03','2026-04','2026-05']
TEST_MONTHS=['2026-06','2026-07','2026-08']
ALL_MONTHS=VAL_MONTHS+TEST_MONTHS
A_CUT=.65; S_CUT=.72
ROLE_LAMBDA=.50
VLAMS=[0.00,0.02,0.05,0.08,0.10,0.12,0.15,0.20]
TUNE_POINTS=[6,7,8]
REPORT_POINTS=[4,6,7,8,10]
MIN_PRICE_N=15


def ii(x,d=0):
    try:return int(float(x))
    except Exception:return d

def ff(x,d=0.0):
    try:return float(x)
    except Exception:return d

def pct(n,d):return 100*n/d if d else 0.0

def read_csv(path):
    with open(path,encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def load_odds(path):
    out={}
    if not os.path.exists(path):return out
    with open(path,encoding='utf-8-sig',newline='') as f:
        for r in csv.DictReader(f):
            c=(r.get('race_code') or '').strip();t=(r.get('combo') or '').strip();o=ff(r.get('odds'),0)
            if len(c)>=12 and t and o>1:out.setdefault(c,{})[t]=o
    return {c:d for c,d in out.items() if len(d)>=100}

def save_odds(path,fmap):
    with open(path,'w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['race_code','combo','odds']);w.writeheader()
        for c in sorted(fmap):
            for t in sorted(fmap[c],key=lambda x:tuple(map(int,x.split('-')))):
                w.writerow({'race_code':c,'combo':t,'odds':fmap[c][t]})

def truth_map(src):
    z={}
    for r in src:
        c=(r.get('race_code') or '').strip();a=(r.get('actual_combo') or '').strip();p=ii(r.get('payout100'))
        if len(c)>=12 and a and p>100:z[c]=(a,p/100.0)
    return z

def eligible_head(r,phase,grade='A'):
    p=ff(r.get('p1' if phase=='val' else 'p109'),0)
    return p >= (S_CUT if grade=='S' else A_CUT)

def fetch_needed(src):
    need=[]
    for r in src:
        mo=r.get('month','')
        if mo in VAL_MONTHS and eligible_head(r,'val','A'):need.append((r.get('race_code') or '').strip())
        elif mo in TEST_MONTHS and eligible_head(r,'test','A'):need.append((r.get('race_code') or '').strip())
    return sorted({c for c in need if len(c)>=12})

def get_odds(src):
    old=load_odds(OLD_CACHE); own=load_odds(CACHE); truth=truth_map(src)
    need=fetch_needed(src); needset=set(need)
    fmap=dict(old);fmap.update(own)
    missing=[c for c in need if c not in fmap]
    print(f'v111 odds need={len(need)} old_seed={sum(c in old for c in need)} own_cache={sum(c in own for c in need)} missing={len(missing)}',flush=True)
    new=dict(own)
    for bi in range(0,len(missing),100):
        batch=missing[bi:bi+100];gained=0;errs=[]
        with ThreadPoolExecutor(max_workers=24) as ex:
            futs={ex.submit(ocache.fetch_one,c,truth):c for c in batch}
            for f in as_completed(futs):
                c,od,url,err=f.result()
                if od:
                    fmap[c]=od;new[c]=od;gained+=1
                elif len(errs)<3:errs.append((c,err))
        save_odds(CACHE,new)
        print(f'v111 odds {min(bi+len(batch),len(missing))}/{len(missing)} gained={gained} total_candidate={sum(c in fmap for c in need)}',flush=True)
        if errs:print('sample errors',errs,flush=True)
        if bi==0 and batch and gained==0:raise RuntimeError('v111: provider returned zero validated odds in first batch')
    return fmap,need

def role_order(r):
    s=(r.get('order_l50') or '').strip()
    return [x for x in s.split(';') if x][:20]

def value_order(base,lam,hs,hn):
    if lam==0:return list(base)
    bscore={t:1.0-i/19.0 for i,t in enumerate(base)}
    vals=[]
    for i,t in enumerate(base):
        n=hn.get(t,0);v=hs.get(t,0.0)/n if n>=MIN_PRICE_N else None
        vals.append((t,v,i))
    known=sorted([x for x in vals if x[1] is not None],key=lambda x:(x[1],x[2]))
    rk={t:i for i,(t,_,_) in enumerate(known)};den=max(1,len(known)-1)
    vs={}
    for t,v,i in vals:vs[t]=(1-rk[t]/den) if v is not None else bscore[t]
    return sorted(base,key=lambda t:((1-lam)*bscore[t]+lam*vs[t],bscore[t]),reverse=True)

def build_scored(target,fmap):
    bytarget=defaultdict(list)
    for r in target:bytarget[r['date']].append(r)
    byodds=defaultdict(list)
    for c,od in fmap.items():
        if len(c)>=8:
            ds=f'{c[:4]}-{c[4:6]}-{c[6:8]}';byodds[ds].append((c,od))
    hs=defaultdict(float);hn=defaultdict(int);out=[]
    all_dates=sorted(set(bytarget)|set(byodds))
    for ds in all_dates:
        # Score all target races before this date enters history.
        for r0 in bytarget.get(ds,[]):
            r=dict(r0);base=role_order(r)
            if len(base)<20:continue
            actual=(r.get('actual_combo') or '').strip()
            for lam in VLAMS:
                order=value_order(base,lam,hs,hn)
                tag=int(round(lam*100));r[f'order_v{tag:02d}']=';'.join(order)
                r[f'rank_v{tag:02d}']=order.index(actual)+1 if actual in order else 0
            out.append(r)
        # Only now update with every cached race on date; only 1-head exact patterns.
        for c,od in byodds.get(ds,[]):
            for s in range(2,7):
                for t in range(2,7):
                    if s==t:continue
                    k=f'1-{s}-{t}';o=od.get(k)
                    if o and o>1:hs[k]+=1.0/o;hn[k]+=1
    return out

def composite_rate(od,tickets):
    vals=[]
    for t in tickets:
        o=od.get(t)
        if not o or o<=1:return None
        vals.append(o)
    return 100*sum(1/o for o in vals)

def select(rs,phase,grade):return [r for r in rs if eligible_head(r,phase,grade)]

def metrics(q,lam,n,fmap):
    tag=int(round(lam*100));hits=0;ret=0;rates=[];cov_hits=0;odn=0
    for r in q:
        order=[x for x in (r.get(f'order_v{tag:02d}') or '').split(';') if x]
        if len(order)<n:continue
        sel=order[:n];act=(r.get('actual_combo') or '').strip();hit=act in sel
        if hit:hits+=1;ret+=ii(r.get('payout100'))
        od=fmap.get((r.get('race_code') or '').strip(),{})
        cr=composite_rate(od,sel) if od else None
        if cr is not None:
            odn+=1;rates.append(cr);cov_hits+=int(hit)
    inv=len(q)*n*100
    return {'r':len(q),'hits':hits,'hit':pct(hits,len(q)),'roi':pct(ret,inv) if inv else 0,
            'odn':odn,'odcov':pct(odn,len(q)),'comp':mean(rates) if rates else 0,'covered_hit':pct(cov_hits,odn) if odn else 0}

def choose_lambda(val,fmap):
    q=select(val,'val','A');base={n:metrics(q,0,n,fmap) for n in TUNE_POINTS}
    bh=mean(x['hit'] for x in base.values());bc=mean(x['comp'] for x in base.values())
    rows=[]
    for lam in VLAMS:
        mm={n:metrics(q,lam,n,fmap) for n in TUNE_POINTS};ah=mean(x['hit'] for x in mm.values());ac=mean(x['comp'] for x in mm.values())
        worst=max(base[n]['hit']-mm[n]['hit'] for n in TUNE_POINTS)
        seven_drop=base[7]['hit']-mm[7]['hit']
        red=bc-ac
        ok=(ah>=bh-.30-1e-9 and worst<=.50+1e-9 and seven_drop<=.30+1e-9 and red>0)
        rows.append((lam,ok,ah-bh,red,worst,seven_drop,mm))
    good=[x for x in rows if x[1]]
    best=max(good,key=lambda x:(x[3],-x[0])) if good else rows[0]
    return best,rows,base

def main():
    src=read_csv(SRC);hp={(r.get('date'),r.get('race_code')):r.get('p109','') for r in read_csv(HEADSRC)}
    for r in src:
        if r.get('month') in TEST_MONTHS:r['p109']=hp.get((r.get('date'),r.get('race_code')),'')

    # Rebuild v110 role ordering exactly, month by month, before any price overlay.
    bymo={}
    for mo in ALL_MONTHS:
        print('v111 role prepare',mo,flush=True);bymo[mo]=r110.prepare_month(src,mo)
    target=sum((bymo[m] for m in ALL_MONTHS),[])

    fmap,need=get_odds(src)
    scored=build_scored(target,fmap)
    val=[r for r in scored if r.get('month') in VAL_MONTHS];test=[r for r in scored if r.get('month') in TEST_MONTHS]
    best,tuning,base=choose_lambda(val,fmap);lam=best[0]
    print('v111 selected lambda',lam,'stats',best[:6],flush=True)

    result=[]
    for g in ['A','S']:
        q=select(test,'test',g)
        for n in REPORT_POINTS:
            b=metrics(q,0,n,fmap);v=metrics(q,lam,n,fmap)
            result.append({'grade':g,'tickets':n,'value_lambda':lam,'races':len(q),'odds_races':v['odn'],'odds_coverage_pct':v['odcov'],
                'base_hit_pct':b['hit'],'value_hit_pct':v['hit'],'hit_diff_pt':v['hit']-b['hit'],
                'base_comp_pct':b['comp'],'value_comp_pct':v['comp'],'comp_reduction_pt':b['comp']-v['comp'],
                'base_gap_pt':b['covered_hit']-b['comp'],'value_gap_pt':v['covered_hit']-v['comp'],
                'base_roi_pct':b['roi'],'value_roi_pct':v['roi']})
    with open(OUT,'w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(result[0]));w.writeheader();w.writerows(result)

    L=['# v111 1号艇 role順位 × prior-only価格補正','',
       '- 頭: v109固定。相手: v110 role λ=0.50固定。',
       '- 価格補正は当該レース/同日オッズを使わず、**前日まで**の確定オッズから exact `1-x-y` 市場人気傾向を作る。',
       '- Mar-Mayでvalue λを1個だけ選択し、Jun-Augは完全固定holdout。',
       '- 合成オッズ率は各レース `100×Σ(1/odds)` を計算してから平均。`100/平均合成オッズ` は使わない。','',
       '## validation λ selection','|value λ|平均的中率差(6/7/8)|平均合成率低下|最悪的中率低下|7点低下|admissible|','|---:|---:|---:|---:|---:|---|']
    for x in tuning:L.append(f'|{x[0]:.2f}|{x[2]:+.2f}pt|{x[3]:+.2f}pt|{-x[4]:+.2f}pt|{-x[5]:+.2f}pt|{"YES" if x[1] else "NO"}|')
    L += ['',f'選択 value λ = **{lam:.2f}**','',
          '## Jun-Aug holdout','|層|点数|実的中率 v110→v111|合成オッズ率 v110→v111|乖離 v110→v111|ROI v110→v111|odds coverage|','|---|---:|---:|---:|---:|---:|---:|']
    for x in result:
        L.append(f'|{x["grade"]}|{x["tickets"]}|{x["base_hit_pct"]:.1f}%→{x["value_hit_pct"]:.1f}% ({x["hit_diff_pt"]:+.1f})|{x["base_comp_pct"]:.1f}%→{x["value_comp_pct"]:.1f}% (低下{x["comp_reduction_pt"]:+.1f})|{x["base_gap_pt"]:+.1f}→{x["value_gap_pt"]:+.1f}pt|{x["base_roi_pct"]:.1f}%→{x["value_roi_pct"]:.1f}%|{x["odds_coverage_pct"]:.1f}%|')

    L += ['','## 月別7点 stability','|月|層|的中率 v110→v111|合成率 v110→v111|低下幅|ROI v110→v111|','|---|---|---:|---:|---:|---:|']
    month_cells=[]
    for mo in TEST_MONTHS:
        qm=[r for r in test if r.get('month')==mo]
        for g in ['A','S']:
            q=select(qm,'test',g);b=metrics(q,0,7,fmap);v=metrics(q,lam,7,fmap)
            hd=v['hit']-b['hit'];red=b['comp']-v['comp'];month_cells.append((hd,red))
            L.append(f'|{mo}|{g}|{b["hit"]:.1f}%→{v["hit"]:.1f}% ({hd:+.1f})|{b["comp"]:.1f}%→{v["comp"]:.1f}%|{red:+.1f}pt|{b["roi"]:.1f}%→{v["roi"]:.1f}%|')

    core=[x for x in result if x['tickets'] in TUNE_POINTS]
    avg_hit=mean(x['hit_diff_pt'] for x in core);comp_good=sum(x['comp_reduction_pt']>0 for x in core)
    a7=next(x for x in result if x['grade']=='A' and x['tickets']==7);s7=next(x for x in result if x['grade']=='S' and x['tickets']==7)
    monthly_hit_ok=sum(h>=-1.0 for h,r in month_cells);monthly_comp_ok=sum(r>0 for h,r in month_cells)
    roi_ok=(a7['value_roi_pct']>=a7['base_roi_pct']-5 and s7['value_roi_pct']>=s7['base_roi_pct']-5)
    passed=(lam>0 and avg_hit>=-.30 and comp_good>=5 and a7['hit_diff_pt']>=-.5 and s7['hit_diff_pt']>=-.5 and a7['comp_reduction_pt']>=.5 and s7['comp_reduction_pt']>=.5 and monthly_hit_ok>=5 and monthly_comp_ok>=5 and roi_ok and min(x['odds_coverage_pct'] for x in core)>=80)
    L += ['','## v111判定',f'- 6/7/8 A/S平均的中率差: **{avg_hit:+.2f}pt**',f'- 合成率改善セル: **{comp_good}/6**',
          f'- 月別7点 的中率許容(>-1pt): **{monthly_hit_ok}/6** / 合成率改善: **{monthly_comp_ok}/6**',
          f'- 7点 A: hit {a7["hit_diff_pt"]:+.2f}pt / comp低下 {a7["comp_reduction_pt"]:+.2f}pt / ROI {a7["base_roi_pct"]:.1f}→{a7["value_roi_pct"]:.1f}',
          f'- 7点 S: hit {s7["hit_diff_pt"]:+.2f}pt / comp低下 {s7["comp_reduction_pt"]:+.2f}pt / ROI {s7["base_roi_pct"]:.1f}→{s7["value_roi_pct"]:.1f}',
          f'- **V111 ROLE+VALUE = {"PASS" if passed else "FAIL"}**',
          '- PASSでも即production採用はしない。PASSなら9/5以降のprospective shadowをfreezeする。FAILなら価格補正を捨てv110 role順位へ戻す。']
    open(SUMMARY,'w',encoding='utf-8').write('\n'.join(L)+'\n')
    print('\n'.join(L),flush=True)

if __name__=='__main__':main()
