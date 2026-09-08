#!/usr/bin/env python3
"""v202: revalue v198/v200 3-head Top10 using 10,000-yen Dutch staking.
Uses archived official closing-displayed trifecta odds. No odds are used to select races/tickets.
BASE and predeclared turn_margin23>=-0.2 are compared on 2025-12..2026-06.
"""
from pathlib import Path
import pandas as pd, numpy as np
ROOT=Path(__file__).resolve().parent
BASE=ROOT/'analysis_v198_3head_long_history_base.csv'
OD=ROOT/'data/official_closing_odds3t'
BANK=10000
CUT=-0.2

def load_odds():
    xs=[]
    for p in sorted(OD.glob('*/*/*.csv')):
        try:
            x=pd.read_csv(p,dtype={'jcd':str,'rno':int})
            x['jcd']=x.jcd.str.zfill(2); x['date']=pd.to_datetime(x.date).dt.strftime('%Y%m%d')
            x['race_code']=x['date']+x['jcd']+x.rno.astype(str).str.zfill(2)
            xs.append(x)
        except Exception as e: print('skip',p,e)
    return pd.concat(xs,ignore_index=True).drop_duplicates('race_code',keep='last') if xs else pd.DataFrame()

def round_dutch(odds,total=BANK):
    # target equal gross return, then convert to legal 100-yen units while preserving total exactly.
    a=np.array(odds,float); inv=1/a; raw=total*inv/inv.sum()
    units=np.floor(raw/100).astype(int); rem=total//100-units.sum()
    frac=raw/100-units
    for i in np.argsort(-frac)[:rem]: units[i]+=1
    return units*100

def evaluate(d,od):
    rows=[]
    for _,r in d.iterrows():
        o=od[od.race_code==str(r.race_code)]
        if o.empty: continue
        tickets=str(r.get('tickets_top10','')).split(';') if 'tickets_top10' in d.columns else []
        if not tickets or tickets==['']:
            # v198 base may not store Top10 tickets; try canonical v166 display field if present.
            tickets=str(r.get('tickets10','')).split(';') if 'tickets10' in d.columns else []
        if not tickets or tickets==['']: continue
        vals=[]; good=True
        for t in tickets:
            if t not in o.columns or pd.isna(o.iloc[0][t]) or float(o.iloc[0][t])<=0: good=False; break
            vals.append(float(o.iloc[0][t]))
        if not good: continue
        stakes=round_dutch(vals)
        actual=str(r.actual_combo); ret=0
        if actual in tickets:
            i=tickets.index(actual); ret=float(stakes[i])*vals[i]
        comp=1/sum(1/x for x in vals)
        rows.append({'month':r.month,'race_code':r.race_code,'turn_margin23':r.turn_margin23,'actual_combo':actual,'hit':int(actual in tickets),'composite_odds':comp,'cost':BANK,'return':ret,'profit':ret-BANK,'tickets_n':len(tickets)})
    return pd.DataFrame(rows)

def stat(g):
    if g.empty:return {'R':0,'hit':0,'comp':0,'cost':0,'ret':0,'roi':0}
    return {'R':len(g),'hit':100*g.hit.mean(),'comp':g.composite_odds.mean(),'cost':g.cost.sum(),'ret':g['return'].sum(),'roi':100*g['return'].sum()/g.cost.sum()}
def line(label,g):
    m=stat(g); return f"|{label}|{m['R']}|{m['hit']:.2f}%|{m['comp']:.3f}|{m['cost']:.0f}|{m['ret']:.0f}|{m['roi']:.1f}%|"
def main():
    b=pd.read_csv(BASE,dtype={'race_code':str}); b=b[(b.month>='2025-12')&(b.month<='2026-06')].copy()
    # v198 file did not historically guarantee ticket strings. Join a v166/v198 detail file if available.
    candidates=['analysis_v195_3head_6month_production_replay.csv','analysis_v166_3head_pair_direct_lambda.csv','analysis_v166_3head_pair_direct.csv']
    if not any(c in b.columns for c in ['tickets_top10','tickets10']):
        for fn in candidates:
            p=ROOT/fn
            if p.exists():
                q=pd.read_csv(p,dtype={'race_code':str})
                tc=next((c for c in ['tickets_top10','tickets10','top10','tickets'] if c in q.columns),None)
                if tc:
                    b=b.merge(q[['race_code',tc]].drop_duplicates('race_code'),on='race_code',how='left'); b=b.rename(columns={tc:'tickets_top10'}); break
    od=load_odds(); z=evaluate(b,od)
    z.to_csv(ROOT/'analysis_v202_3head_dutch10k_roi.csv',index=False)
    base=z; cut=z[pd.to_numeric(z.turn_margin23,errors='coerce')>=CUT]
    L=['# v202 3-head 10,000-yen Dutch ROI','',
       '- stake: exactly 10,000 yen per evaluated race','- tickets: frozen v166 Top10 only; odds do not select tickets/races',
       '- odds: archived official closing-displayed trifecta odds','- allocation: equal-gross Dutch, rounded to 100-yen units, total remains 10,000 yen',
       '- window: 2025-12..2026-06','',
       '## Overall','|rule|odds-covered R|hit|avg composite odds|cost|return|ROI|','|---|---:|---:|---:|---:|---:|---:|',line('BASE',base),line('turn>=-0.2',cut),'',
       '## Monthly','|month|BASE R|BASE ROI|turn R|turn ROI|','|---|---:|---:|---:|---:|']
    for mon in sorted(z.month.unique()):
        mb=stat(z[z.month==mon]); mc=stat(cut[cut.month==mon]); L.append(f"|{mon}|{mb['R']}|{mb['roi']:.1f}%|{mc['R']}|{mc['roi']:.1f}%|")
    if z.empty:
        L += ['','## ERROR','No races could be evaluated. Most likely the frozen v198 table lacks Top10 ticket strings and no compatible detail file was found. Do not infer ROI; fix the ticket join and rerun.']
    (ROOT/'summary_v202_3head_dutch10k_roi.md').write_text('\n'.join(L)+'\n',encoding='utf-8'); print('\n'.join(L))
if __name__=='__main__':main()
