#!/usr/bin/env python3
"""v202: revalue v198/v200 3-head Top10 using 10,000-yen Dutch staking.
Rebuilds the exact monthly v166 Top10 from the same historical feature rows and earlier-only pair training used by v198.
Odds are used only for Dutch allocation / settlement, never for race or ticket selection.
"""
from pathlib import Path
from datetime import date
import pandas as pd, numpy as np
import analyze_v166_3head_pair_direct as v166
ROOT=Path(__file__).resolve().parent
BASE=ROOT/'analysis_v198_3head_long_history_base.csv'
SRC=ROOT/'analysis_v108_1head_feasibility.csv'
OD=ROOT/'data/official_closing_odds3t'
BANK=10000; CUT=-0.2; TOPN=10; LAM=1.0

def load_odds():
    xs=[]
    for p in sorted(OD.glob('*/*/*.csv')):
        try:
            x=pd.read_csv(p,dtype={'jcd':str,'rno':int})
            x['jcd']=x.jcd.str.zfill(2)
            x['date']=pd.to_datetime(x.date).dt.strftime('%Y%m%d')
            x=x.assign(race_code=x['date']+x['jcd']+x.rno.astype(str).str.zfill(2))
            xs.append(x)
        except Exception as e: print('skip',p,e)
    return pd.concat(xs,ignore_index=True).drop_duplicates('race_code',keep='last') if xs else pd.DataFrame()

def round_dutch(odds,total=BANK):
    a=np.array(odds,float); inv=1/a; raw=total*inv/inv.sum()
    units=np.floor(raw/100).astype(int); rem=total//100-units.sum(); frac=raw/100-units
    for i in np.argsort(-frac)[:rem]: units[i]+=1
    return units*100

def rebuild_tickets(b):
    src=v166.read(str(SRC)); by_code={str(r.get('race_code')):r for r in src}; cache={}; out=[]
    for _,r in b.iterrows():
        mon=str(r.month); code=str(r.race_code); rr=by_code.get(code)
        if rr is None: out.append(''); continue
        if mon not in cache:
            pair_train=[x for x in src if x.get('date') and date.fromisoformat(x['date'])<date.fromisoformat(mon+'-01')]
            pm,_=v166.fit(pair_train); cache[mon]=pm
        top=v166.order(dict(rr),cache[mon],LAM)[:TOPN]
        out.append(';'.join(top))
    b=b.copy(); b['tickets_top10']=out; return b

def evaluate(d,od):
    rows=[]
    oi=od.set_index('race_code',drop=False) if not od.empty else pd.DataFrame()
    for _,r in d.iterrows():
        code=str(r.race_code)
        if code not in oi.index: continue
        o=oi.loc[code]
        if isinstance(o,pd.DataFrame): o=o.iloc[-1]
        tickets=[t for t in str(r.tickets_top10).split(';') if t]
        if len(tickets)!=TOPN: continue
        vals=[]; good=True
        for t in tickets:
            try: v=float(o[t])
            except: good=False; break
            if not np.isfinite(v) or v<=0: good=False; break
            vals.append(v)
        if not good: continue
        stakes=round_dutch(vals); actual=str(r.actual_combo); ret=0.0
        if actual in tickets:
            i=tickets.index(actual); ret=float(stakes[i])*vals[i]
        comp=1/sum(1/x for x in vals)
        rows.append({'month':r.month,'race_code':code,'turn_margin23':r.turn_margin23,'actual_combo':actual,'hit':int(actual in tickets),'composite_odds':comp,'cost':BANK,'return':ret,'profit':ret-BANK,'tickets_n':len(tickets),'tickets_top10':';'.join(tickets)})
    return pd.DataFrame(rows)

def stat(g):
    if g.empty:return {'R':0,'hit':0,'comp':0,'cost':0,'ret':0,'roi':0}
    return {'R':len(g),'hit':100*g.hit.mean(),'comp':g.composite_odds.mean(),'cost':g.cost.sum(),'ret':g['return'].sum(),'roi':100*g['return'].sum()/g.cost.sum()}
def line(label,g):
    m=stat(g); return f"|{label}|{m['R']}|{m['hit']:.2f}%|{m['comp']:.3f}|{m['cost']:.0f}|{m['ret']:.0f}|{m['roi']:.1f}%|"
def main():
    b=pd.read_csv(BASE,dtype={'race_code':str}); b=b[(b.month>='2025-12')&(b.month<='2026-06')].copy(); b=rebuild_tickets(b)
    od=load_odds(); z=evaluate(b,od)
    if z.empty: raise SystemExit('no evaluable races after exact v166 ticket rebuild + odds join')
    z.to_csv(ROOT/'analysis_v202_3head_dutch10k_roi.csv',index=False)
    cut=z[pd.to_numeric(z.turn_margin23,errors='coerce')>=CUT]
    L=['# v202 3-head 10,000-yen Dutch ROI','',
       '- stake: exactly 10,000 yen per evaluated race','- tickets: exact monthly v166 Top10 rebuilt with earlier-only pair training, matching v198 protocol',
       '- odds: archived official closing-displayed trifecta odds','- allocation: equal-gross Dutch, rounded to 100-yen units; total remains 10,000 yen',
       '- odds never select races/tickets','- window: 2025-12..2026-06','',
       '## Overall','|rule|odds-covered R|hit|avg composite odds|cost|return|ROI|','|---|---:|---:|---:|---:|---:|---:|',line('BASE',z),line('turn>=-0.2',cut),'',
       '## Monthly','|month|BASE R|BASE ROI|turn R|turn ROI|','|---|---:|---:|---:|---:|']
    for mon in sorted(z.month.unique()):
        mb=stat(z[z.month==mon]); mc=stat(cut[cut.month==mon]); L.append(f"|{mon}|{mb['R']}|{mb['roi']:.1f}%|{mc['R']}|{mc['roi']:.1f}%|")
    (ROOT/'summary_v202_3head_dutch10k_roi.md').write_text('\n'.join(L)+'\n',encoding='utf-8'); print('\n'.join(L))
if __name__=='__main__':main()
