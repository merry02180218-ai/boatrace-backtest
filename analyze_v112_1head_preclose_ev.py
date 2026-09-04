"""v112: strict pre-close EV selection for the v109+v110 1-head model.

Goal
- Keep the predictive side frozen: v109 head probability + v110 role-ticket order (lambda=.50).
- Use only verified BoatraceCSV od3 snapshots acquired before cutoff to decide which exact
  1-x-y tickets to buy.
- Ticket count is dynamic: buy every ticket whose model EV = calibrated ticket probability
  * pre-close odds exceeds a fixed threshold. Races may be skipped when no ticket qualifies.

No-leak design
- Current-race odds come only from data/previews/od3 rows with acquisition time < cutoff.
- No final/deadline odds are used for selection.
- Realized payout100 is settlement-only after selection.
- Head calibration and conditional v110-rank probabilities use only prior MONTHS.
- Threshold is selected on 2026-07-19..07-31 and frozen for 2026-08-01..08-31 holdout.
"""
from __future__ import annotations

import csv
from collections import Counter
from datetime import date, datetime

from backtest import rows

SRC='analysis_v110_1head_role_tickets.csv'
OUT='analysis_v112_1head_preclose_ev.csv'
SUMMARY='summary_v112_1head_preclose_ev.md'

DEV_START='2026-07-19'; DEV_END='2026-07-31'
TEST_START='2026-08-01'; TEST_END='2026-08-31'
A_CUT=.65; S_CUT=.72
EV_GRID=[1.00,1.05,1.10,1.15,1.20,1.25,1.30,1.40,1.50,1.75,2.00]
ALPHA=.5


def ff(x,d=0.0):
    try:return float(x)
    except Exception:return d

def ii(x,d=0):
    try:return int(float(x))
    except Exception:return d

def pct(n,d):return 100*n/d if d else 0.0

def read_csv(path):
    with open(path,encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def cutoff_for(ds,cut,acq):
    hh,mm=map(int,cut.split(':')[:2]); y,m,d=map(int,ds.split('-'))
    return datetime(y,m,d,hh,mm,tzinfo=acq.tzinfo)

def preclose_lead(r,ds):
    acq=(r.get('取得日時') or '').strip(); cut=(r.get('締切時刻') or '').strip()
    if not acq or not cut:return None
    try:
        a=datetime.fromisoformat(acq); c=cutoff_for(ds,cut,a)
        lead=(c-a).total_seconds()/60.0
        return lead if lead>0 else None
    except Exception:return None

def load_odds_map(dates):
    om={}; leads={}
    for ds in sorted(dates):
        ymd=ds.replace('-','/')
        for r in rows(f'data/previews/od3/{ymd}.csv'):
            code=(r.get('レースコード') or '').strip(); lead=preclose_lead(r,ds)
            if not code or lead is None:continue
            # If duplicate snapshots exist, keep the one closest to the operational T-10 target.
            if code not in om or abs(lead-10.0) < abs(leads[code]-10.0):
                om[code]=r; leads[code]=lead
    return om,leads

def order20(r):
    s=(r.get('order_l50') or '').strip()
    a=[x.strip() for x in s.split(';') if x.strip()]
    return a if len(a)==20 else []

def odds20(orow,order):
    out={}
    for t in order:
        o=ff(orow.get('3連単_'+t),0)
        if o<=1.0:return None
        out[t]=o
    return out

def grade_sel(r,g):
    return ff(r.get('p109')) >= (S_CUT if g=='S' else A_CUT)

def month_start(mo):return date.fromisoformat(mo+'-01')

def prior_rows(src,mo):
    first=month_start(mo)
    return [r for r in src if date.fromisoformat(r['date']) < first]

def calibration(src,mo,g):
    tr=[r for r in prior_rows(src,mo) if grade_sel(r,g)]
    if not tr:raise RuntimeError(f'no calibration rows for {mo} {g}')
    avgp=sum(ff(r.get('p109')) for r in tr)/len(tr)
    hr=sum(ii(r.get('head_hit')) for r in tr)/len(tr)
    scale=(hr/avgp) if avgp>0 else 1.0
    # Conservative guard against unstable extrapolation. In practice v109 needs only a small correction.
    scale=max(.85,min(1.05,scale))
    heads=[r for r in tr if ii(r.get('head_hit'))==1 and 1<=ii(r.get('v110_rank20'))<=20]
    cnt=Counter(ii(r.get('v110_rank20')) for r in heads)
    den=len(heads)+20*ALPHA
    rp={k:(cnt[k]+ALPHA)/den for k in range(1,21)}
    return {'rows':len(tr),'headwins':len(heads),'avgp':avgp,'actual':hr,'scale':scale,'rankp':rp}

def prepare_phase(src,start,end,odds_map,leads):
    out=[]
    for r in src:
        ds=r.get('date','')
        if not (start<=ds<=end):continue
        if ii(r.get('valid_payout'))!=1:continue
        order=order20(r)
        if not order:continue
        orow=odds_map.get(r.get('race_code',''))
        if not orow:continue
        od=odds20(orow,order)
        if od is None:continue
        z=dict(r); z['_order']=order; z['_odds']=od; z['_lead']=leads.get(r.get('race_code',''),0.0)
        out.append(z)
    return out

def enrich_probs(rs,src,g):
    out=[]; cals={}
    for r in rs:
        if not grade_sel(r,g):continue
        mo=r.get('date','')[:7]
        if mo not in cals:cals[mo]=calibration(src,mo,g)
        cal=cals[mo]
        ph=max(.01,min(.99,ff(r.get('p109'))*cal['scale']))
        probs={t:ph*cal['rankp'][j] for j,t in enumerate(r['_order'],1)}
        z=dict(r); z['_phead_cal']=ph; z['_ticket_probs']=probs
        out.append(z)
    return out,cals

def metric(rs,thr):
    bet_r=0;tickets=0;hits=0;ret=0;lead=[];point_hist=Counter();evsum=0.0
    fixed_hits=0;fixed_ret=0
    for r in rs:
        act=(r.get('actual_combo') or '').strip(); order=r['_order']; od=r['_odds']; pr=r['_ticket_probs']
        if act in order[:7]:
            fixed_hits+=1; fixed_ret+=ii(r.get('payout100'))
        sel=[t for t in order if pr[t]*od[t] >= thr]
        point_hist[len(sel)]+=1
        if not sel:continue
        bet_r+=1;tickets+=len(sel);lead.append(r['_lead'])
        evsum+=sum(pr[t]*od[t] for t in sel)
        if act in sel:
            hits+=1;ret+=ii(r.get('payout100'))
    inv=tickets*100
    fixed_inv=len(rs)*7*100
    return {
        'odds_races':len(rs),'bet_races':bet_r,'bet_race_pct':pct(bet_r,len(rs)),
        'tickets':tickets,'avg_tickets_bet':tickets/bet_r if bet_r else 0.0,
        'hits':hits,'hit_rate_bet_pct':pct(hits,bet_r),
        'roi_pct':pct(ret,inv),
        'avg_selected_model_ev':evsum/tickets if tickets else 0.0,
        'fixed7_hits':fixed_hits,'fixed7_hit_pct':pct(fixed_hits,len(rs)),
        'fixed7_roi_pct':pct(fixed_ret,fixed_inv),
        'avg_lead_min':sum(lead)/len(lead) if lead else 0.0,
        'point_hist':point_hist,
    }

def choose_threshold(dev_by_grade):
    cand=[]
    for th in EV_GRID:
        ma=metric(dev_by_grade['A'],th); ms=metric(dev_by_grade['S'],th)
        ok=(ma['bet_races']>=100 and ms['bet_races']>=80 and
            ma['tickets']>=250 and ms['tickets']>=200 and
            ma['avg_tickets_bet']<=7.0 and ms['avg_tickets_bet']<=7.0)
        worst=min(ma['roi_pct'],ms['roi_pct']); avg=(ma['roi_pct']+ms['roi_pct'])/2
        cand.append((th,ok,worst,avg,ma,ms))
    good=[x for x in cand if x[1]]
    selected=max(good,key=lambda x:(x[2],x[3],-x[0]))[0] if good else 1.10
    return selected,cand

def hist_text(h):
    return ', '.join(f'{k}点:{v}R' for k,v in sorted(h.items()) if v)

def main():
    src=[r for r in read_csv(SRC) if r.get('date','') and '2026-06-01'<=r.get('date','')<='2026-08-31']
    need_dates={r.get('date','') for r in src if DEV_START<=r.get('date','')<=TEST_END}
    odds_map,leads=load_odds_map(need_dates)
    dev0=prepare_phase(src,DEV_START,DEV_END,odds_map,leads)
    test0=prepare_phase(src,TEST_START,TEST_END,odds_map,leads)
    dev={};test={};calstats={}
    for g in ('A','S'):
        dev[g],c1=enrich_probs(dev0,src,g); test[g],c2=enrich_probs(test0,src,g)
        calstats[g]={**c1,**c2}

    selected,sweep=choose_threshold(dev)
    out=[]
    for phase,by in [('DEV',dev),('HOLDOUT',test)]:
        for g in ('A','S'):
            for th in EV_GRID:
                m=metric(by[g],th)
                out.append({
                    'phase':phase,'grade':g,'ev_threshold':th,
                    **{k:v for k,v in m.items() if k!='point_hist'},
                    'point_hist':';'.join(f'{k}:{v}' for k,v in sorted(m['point_hist'].items())),
                    'selected_threshold':int(abs(th-selected)<1e-9),
                })
    with open(OUT,'w',encoding='utf-8-sig',newline='') as f:
        fs=list(out[0].keys());w=csv.DictWriter(f,fieldnames=fs);w.writeheader();w.writerows(out)

    all_leads=[v for k,v in leads.items() if k in {r.get('race_code','') for r in dev0+test0}]
    L=['# v112 1号艇 strict pre-close EV選別','',
       '- 予想側は **v109頭 + v110 role順位(λ=.50)** を固定。現在レースのオッズで頭・順位は変更しない。',
       '- 買い判定だけ `EV = 校正済みP(その3連単) × pre-close odds` を使用。EV閾値以上の買い目だけ100円均等購入し、0点なら見送り。',
       '- `P(ticket)=calibrated p109 × prior-month v110実順位分布`。head補正・順位分布は対象月より前の月だけで作成。',
       '- オッズは BoatraceCSV `data/previews/od3` の **取得日時 < 締切時刻** の行だけ。締切/最終オッズは選別に不使用。',
       f'- threshold validation: **{DEV_START}〜{DEV_END}** / frozen holdout: **{TEST_START}〜{TEST_END}**。','']
    if all_leads:
        srt=sorted(all_leads);med=srt[len(srt)//2]
        L += [f'- 利用pre-close snapshot: {len(all_leads)}R、平均 **{sum(all_leads)/len(all_leads):.2f}分前** / 中央 **{med:.2f}分前** / 最短 **{min(all_leads):.2f}分前** / 最長 **{max(all_leads):.2f}分前**。','']

    L += ['## prior-month calibration','|対象月|層|学習R|頭的中R|平均p109|実頭率|head scale|','|---|---|---:|---:|---:|---:|---:|']
    for mo in ('2026-07','2026-08'):
        for g in ('A','S'):
            c=calstats[g].get(mo)
            if c:L.append(f'|{mo}|{g}|{c["rows"]:,}|{c["headwins"]:,}|{c["avgp"]*100:.1f}%|{c["actual"]*100:.1f}%|{c["scale"]:.4f}|')

    L += ['','## Jul19-31 validation threshold sweep','|EV閾値|A betR|A平均点|A ROI|S betR|S平均点|S ROI|admissible|','|---:|---:|---:|---:|---:|---:|---:|---|']
    for th,ok,worst,avg,ma,ms in sweep:
        L.append(f'|{th:.2f}|{ma["bet_races"]}|{ma["avg_tickets_bet"]:.2f}|{ma["roi_pct"]:.1f}%|{ms["bet_races"]}|{ms["avg_tickets_bet"]:.2f}|{ms["roi_pct"]:.1f}%|{"YES" if ok else "NO"}|')
    L += ['',f'選択EV閾値 = **{selected:.2f}**（validationで固定、Augustで再調整しない）','']

    L += ['## August strict holdout','|層|odds R|買うR|購入率|平均点|的中率/買うR|EV選別ROI|固定7点的中率|固定7点ROI|','|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    hold={}
    for g in ('A','S'):
        m=metric(test[g],selected);hold[g]=m
        L.append(f'|{g}|{m["odds_races"]}|{m["bet_races"]}|{m["bet_race_pct"]:.1f}%|{m["avg_tickets_bet"]:.2f}|{m["hit_rate_bet_pct"]:.1f}%|{m["roi_pct"]:.1f}%|{m["fixed7_hit_pct"]:.1f}%|{m["fixed7_roi_pct"]:.1f}%|')
    L += ['','### August 動的点数分布']
    for g in ('A','S'):
        L.append(f'- {g}: {hist_text(hold[g]["point_hist"])}')

    passed=(hold['A']['bet_races']>=300 and hold['S']['bet_races']>=180 and
            hold['A']['roi_pct']>=100.0 and hold['S']['roi_pct']>=100.0 and
            hold['A']['avg_tickets_bet']<=7.0 and hold['S']['avg_tickets_bet']<=7.0)
    L += ['','## v112判定',
          f'- A ROI **{hold["A"]["roi_pct"]:.1f}%** / S ROI **{hold["S"]["roi_pct"]:.1f}%**。',
          f'- A平均点 **{hold["A"]["avg_tickets_bet"]:.2f}** / S平均点 **{hold["S"]["avg_tickets_bet"]:.2f}**。',
          f'- **V112 PRECLOSE-EV = {"PASS" if passed else "FAIL"}**',
          '- PASSでもproduction即採用はしない。pre-close od3の履歴が7/19以降しかないため、まずprospective shadowで追加検証する。',
          '- FAILなら「p109×順位別経験確率」の確率化を見直し、オッズ自体を予想特徴へ混ぜることはしない。']
    open(SUMMARY,'w',encoding='utf-8').write('\n'.join(L)+'\n')
    print('\n'.join(L))

if __name__=='__main__':main()
