#!/usr/bin/env python3
"""v205: reproduce actual 3-head operation: v191 PRE -> v165/v166 -> PICK UP -> 10k Dutch.

Uses frozen v191 PRE scores (July tune / August untouched), production v195 Top10,
current exhibition margins from v108, and combined archived odds for settlement.
BoatraceCSV od3 is preferred when available; corrected official closing odds fills gaps.
Per user instruction these are treated as one settlement odds series. Prediction/race
selection never uses odds/result/payout.
"""
from pathlib import Path
import pandas as pd, numpy as np
ROOT=Path(__file__).resolve().parent
PRE=ROOT/'analysis_v191_3head_clean_pre_validation.csv'
PROD=ROOT/'analysis_v195_3head_production_6month_backtest.csv'
FEAT=ROOT/'analysis_v108_1head_feasibility.csv'
OD_OFF=ROOT/'data/official_closing_odds3t'
OD3=ROOT/'data/previews/od3'
OUT=ROOT/'analysis_v205_3head_operational_replay.csv'
SUM=ROOT/'summary_v205_3head_operational_replay.md'
CUT_PRE=.072608; BANK=10000

def load_official():
    xs=[]
    for p in sorted(OD_OFF.glob('*/*/*.csv')):
        try:
            x=pd.read_csv(p,dtype={'jcd':str,'rno':int})
            if 'odds_mapping_version' in x.columns:
                x=x[x.odds_mapping_version.fillna('')=='official_table_v2']
            if x.empty: continue
            x['jcd']=x.jcd.astype(str).str.zfill(2)
            x['date']=pd.to_datetime(x.date).dt.strftime('%Y%m%d')
            x['race_code']=x['date']+x['jcd']+x.rno.astype(str).str.zfill(2)
            x['odds_source']='official_closing'
            xs.append(x)
        except Exception as e: print('skip official',p,e)
    return pd.concat(xs,ignore_index=True).drop_duplicates('race_code',keep='last') if xs else pd.DataFrame()

def load_od3():
    xs=[]
    for p in sorted(OD3.glob('*/*/*.csv')):
        try:
            x=pd.read_csv(p,dtype={'レースコード':str})
            if x.empty or 'レースコード' not in x.columns: continue
            x['race_code']=x['レースコード'].astype(str).str.zfill(12)
            ren={c:c.replace('3連単_','') for c in x.columns if str(c).startswith('3連単_')}
            x=x.rename(columns=ren)
            x['odds_source']='boatracecsv_od3'
            xs.append(x)
        except Exception as e: print('skip od3',p,e)
    return pd.concat(xs,ignore_index=True).drop_duplicates('race_code',keep='last') if xs else pd.DataFrame()

def load_odds():
    off=load_official(); od3=load_od3()
    if off.empty and od3.empty:return pd.DataFrame()
    # user-approved unified series: official first, od3 appended second so od3 wins duplicates.
    return pd.concat([off,od3],ignore_index=True,sort=False).drop_duplicates('race_code',keep='last')

def round_dutch(odds,total=BANK):
    a=np.array(odds,float); inv=1/a; raw=total*inv/inv.sum()
    units=np.floor(raw/100).astype(int); rem=total//100-units.sum(); frac=raw/100-units
    for i in np.argsort(-frac)[:rem]: units[i]+=1
    return units*100

def settle(r,o):
    ts=[t for t in str(r.top10).split(';') if t]
    if len(ts)!=10:return None
    vals=[]
    for t in ts:
        try:v=float(o[t])
        except:return None
        if not np.isfinite(v) or v<=0:return None
        vals.append(v)
    stakes=round_dutch(vals); actual=str(r.actual_combo); ret=0.0; actual_stake=0
    if actual in ts:
        i=ts.index(actual); actual_stake=int(stakes[i]); ret=float(stakes[i])*vals[i]
    comp=1/sum(1/x for x in vals)
    return dict(hit=int(actual in ts and actual_stake>0),composite_odds=comp,cost=BANK,return_yen=ret,profit=ret-BANK,actual_stake=actual_stake,odds_source=str(o.get('odds_source','unknown')))

def stat(g):
    if g.empty:return dict(R=0,hit=0,comp=0,cost=0,ret=0,roi=0)
    c=float(g.cost.sum()); r=float(g.return_yen.sum())
    return dict(R=len(g),hit=100*g.hit.mean(),comp=g.composite_odds.mean(),cost=c,ret=r,roi=100*r/c if c else 0)
def row(label,g):
    m=stat(g);return f"|{label}|{m['R']}|{m['hit']:.2f}%|{m['comp']:.3f}|{m['cost']:.0f}|{m['ret']:.0f}|{m['roi']:.1f}%|"

def main():
    pre=pd.read_csv(PRE,dtype={'race_code':str})[['race_code','pre_prob_eval','split']].drop_duplicates('race_code',keep='last')
    prod=pd.read_csv(PROD,dtype={'race_code':str})
    prod=prod[prod.month.isin(['2026-07','2026-08'])].copy()
    feat=pd.read_csv(FEAT,dtype={'race_code':str},usecols=['race_code','turn_margin23','st_margin23','straight_margin23','ex_margin23']).drop_duplicates('race_code',keep='last')
    d=prod.merge(pre,on='race_code',how='inner').merge(feat,on='race_code',how='left')
    d['pre_watch']=pd.to_numeric(d.pre_prob_eval,errors='coerce')>=CUT_PRE
    d['pickup']=d.pre_watch & (pd.to_numeric(d.p3head,errors='coerce')>=.30) & (pd.to_numeric(d.turn_margin23,errors='coerce')>=-.2) & (pd.to_numeric(d.st_margin23,errors='coerce')>=-.2)
    od=load_odds(); oi=od.set_index('race_code',drop=False) if not od.empty else pd.DataFrame()
    rows=[]
    for _,r in d.iterrows():
        if str(r.race_code) not in oi.index:continue
        o=oi.loc[str(r.race_code)]; o=o.iloc[-1] if isinstance(o,pd.DataFrame) else o
        s=settle(r,o)
        if s is None:continue
        rows.append({**r.to_dict(),**s})
    z=pd.DataFrame(rows)
    if z.empty:raise SystemExit('no evaluable operational replay rows')
    z.to_csv(OUT,index=False)
    L=['# v205 3-head actual operational replay','',
       '- pipeline: frozen v191 PRE watch -> actual v165 production pass (v195) -> frozen v166 Top10 -> optional PICK UP gate -> 10,000-yen Dutch settlement',
       f'- PRE cut: {CUT_PRE:.6f} (chosen on July, frozen for August)',
       '- PICK UP: p3head>=0.30 & turn_margin23>=-0.2 & st_margin23>=-0.2, only after PRE watch',
       '- odds: unified settlement series per user instruction; BoatraceCSV od3 preferred where available, corrected official closing used as fallback',
       '- July is TUNE/DESCRIPTIVE because PRE cut was selected on July',
       '- August is the clean untouched PRE test and the primary operational result','',
       '## Results','|segment|R|hit|avg composite|cost|return|ROI|','|---|---:|---:|---:|---:|---:|---:|']
    for mon,label in [('2026-07','JUL tune'),('2026-08','AUG untouched')]:
        g=z[z.month==mon]
        L += [row(label+' all production',g),row(label+' PRE pass',g[g.pre_watch]),row(label+' PICK UP',g[g.pickup])]
    L += ['', '## Odds-source coverage','|month|source|R|','|---|---|---:|']
    for (mon,src),g in z.groupby(['month','odds_source']):L.append(f'|{mon}|{src}|{len(g)}|')
    L += ['', '## PICK UP races','|split|date|race_code|source|PRE p|p3head|turn|ST|hit|comp|return|profit|','|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    p=z[z.pickup].sort_values(['month','date','race_code'])
    for _,r in p.iterrows():
        L.append(f"|{r['split']}|{r.date}|{r.race_code}|{r.odds_source}|{r.pre_prob_eval:.4f}|{r.p3head:.4f}|{r.turn_margin23:.3f}|{r.st_margin23:.3f}|{int(r.hit)}|{r.composite_odds:.3f}|{r.return_yen:.0f}|{r.profit:.0f}|")
    if p.empty:L.append('|-|-|-|-|-|-|-|-|-|-|-|-|')
    L += ['', '## Interpretation','- Production adoption must be judged primarily from August untouched, not July tune.','- PICK UP remains SHADOW unless the untouched sample is sufficiently large and stable.']
    SUM.write_text('\n'.join(L)+'\n',encoding='utf-8');print('\n'.join(L))
if __name__=='__main__':main()
