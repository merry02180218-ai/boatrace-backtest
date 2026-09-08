#!/usr/bin/env python3
"""v207: leak-audited enhanced PRE monitor for 3-head production.

Temporal protocol is fixed before August inspection:
  June train -> July tune/model selection -> August untouched test.
The extra features come from analysis_3attack_rows.csv. Its generator computes
features before loading target-day outcomes, and only ingests preview/motor state
after each day, so prior-exhibition/motor features are strictly earlier-day state.
PRE remains monitoring only. Canonical FINAL remains v165 p3head>=.30 -> v166 Top10.
August monetary replay uses BoatraceCSV od3 pre-deadline snapshots only and a fixed
10,000-yen inverse-odds Dutch allocation in 100-yen units.
"""
from __future__ import annotations
from pathlib import Path
import math
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

import analyze_v190_3head_clean_pre_monitor as base
import analyze_v191_3head_clean_pre_restore_june as restore

ROOT=Path(__file__).resolve().parent
ATT=ROOT/'analysis_3attack_rows.csv'
V191=ROOT/'analysis_v191_3head_clean_pre_validation.csv'
V195=ROOT/'analysis_v195_3head_production_6month_backtest.csv'
V108=ROOT/'analysis_v108_1head_feasibility.csv'
ODROOT=ROOT/'data/previews/od3/2026/08'
OUT=ROOT/'analysis_v207_3head_enhanced_pre.csv'
ROI_OUT=ROOT/'analysis_v207_3head_enhanced_pre_roi.csv'
SUMMARY=ROOT/'summary_v207_3head_enhanced_pre.md'
BANK=10000
UNIT=100
TIERS=[.10,.08,.07]

TACTICS=[
 '3_ST優位','3コース攻撃実績','2壁弱さ','1弱さ','3節間ST','3選手力',
 '3コース1着率','3コースST_速いほど高','3全国ST_速いほど高',
 '1コース1着率_低いほど高','1コースST_遅いほど高',
 '2コース1着率_低いほど高','2コースST_遅いほど高','3日目以降'
]
PRIOR_EX=[
 '3前回展示総合','3前回直線','3前回通常展示','3前回回り足',
 '3伸び','3回り足','3モーター攻撃'
]
SETS={
 'base':[],
 'base+tactics':TACTICS,
 'base+prior_ex':PRIOR_EX,
 'base+all_audited':TACTICS+PRIOR_EX,
}


def norm_code(x):
    try:return str(int(float(x))).zfill(12)
    except:return str(x).strip().replace('.0','').zfill(12)

def fit_model(df, extras):
    nums=base.NUM+extras
    pre=ColumnTransformer([('n',StandardScaler(),nums),('v',OneHotEncoder(handle_unknown='ignore'),['venue'])])
    m=Pipeline([('pre',pre),('lr',LogisticRegression(C=.30,max_iter=1800,class_weight='balanced'))])
    m.fit(df[nums+['venue']],df['label'].astype(int))
    return m

def probs(m,df,extras):
    return m.predict_proba(df[base.NUM+extras+['venue']])[:,1]

def cut_for_rate(p,rate):
    # Frozen July quantile. >= cut may be slightly above target on ties.
    return float(np.quantile(np.asarray(p,float),1-rate,method='higher'))

def metr(df,p,cut):
    y=df.label.to_numpy(int); sel=np.asarray(p)>=cut
    pos=int(y.sum()); n=int(sel.sum()); tp=int(((y==1)&sel).sum())
    return {'R':len(df),'formal':pos,'watch':n,'watch_rate':n/len(df) if len(df) else 0,
            'recall':tp/pos if pos else 0,'precision':tp/n if n else 0,'tp':tp}

def round_dutch(odds):
    vals=np.array([float(x) for x in odds],float)
    if len(vals)==0 or np.any(~np.isfinite(vals)) or np.any(vals<=0): return None
    w=(1/vals); w=w/w.sum(); units=BANK//UNIT
    raw=w*units; floor=np.floor(raw).astype(int); rem=int(units-floor.sum())
    frac=raw-floor
    order=np.argsort(-frac,kind='stable')
    for i in order[:rem]:floor[i]+=1
    stakes=(floor*UNIT).astype(int)
    return stakes, float(1/(1/vals).sum())

def load_od3():
    frames=[]
    for p in sorted(ODROOT.glob('*.csv')):
        try:
            d=pd.read_csv(p,dtype={'レースコード':str})
            if len(d):frames.append(d)
        except Exception as e:print('od3 read fail',p,e,flush=True)
    if not frames:return pd.DataFrame()
    d=pd.concat(frames,ignore_index=True)
    codecol='レースコード' if 'レースコード' in d.columns else ('race_code' if 'race_code' in d.columns else None)
    if codecol is None:raise RuntimeError('od3 race code column missing')
    d['_code']=d[codecol].map(norm_code)
    return d.drop_duplicates('_code',keep='last').set_index('_code')

def settle(prod, pass_codes, od, tag, final=None):
    rows=[]
    sub=prod[prod['_code'].isin(pass_codes)].copy()
    for _,r in sub.iterrows():
        code=r['_code']
        if code not in od.index:continue
        tickets=[x.strip() for x in str(r.top10).split(';') if x.strip()]
        if len(tickets)!=10:continue
        rr=od.loc[code]
        vals=[]; ok=True
        for t in tickets:
            col='3連単_'+t
            try:o=float(rr[col])
            except:ok=False;break
            if not math.isfinite(o) or o<=0:ok=False;break
            vals.append(o)
        if not ok:continue
        dut=round_dutch(vals)
        if dut is None:continue
        stakes,comp=dut
        actual=str(r.actual_combo).strip(); ret=0.0; actual_stake=0
        if actual in tickets:
            k=tickets.index(actual);actual_stake=int(stakes[k]);ret=actual_stake*vals[k]
        z={'tag':tag,'race_code':code,'date':str(r.date),'p3head':float(r.p3head),
           'actual_combo':actual,'top10_hit':int(actual in tickets),'actual_stake':actual_stake,
           'zero_stake_tickets':int((stakes==0).sum()),'composite_odds':comp,'cost_yen':BANK,
           'return_yen':ret,'profit_yen':ret-BANK,'top10':';'.join(tickets),
           'stakes':';'.join(map(str,stakes.tolist())),'odds':';'.join(f'{x:g}' for x in vals)}
        if final is not None and code in final.index:
            fr=final.loc[code]
            z['turn_margin23']=float(fr.get('turn_margin23',np.nan));z['st_margin23']=float(fr.get('st_margin23',np.nan))
            z['pickup']=int(float(r.p3head)>=.30 and z['turn_margin23']>=-.2 and z['st_margin23']>=-.2)
        else:z['pickup']=0
        rows.append(z)
    return rows

def agg(rows):
    n=len(rows);cost=sum(x['cost_yen'] for x in rows);ret=sum(x['return_yen'] for x in rows)
    return {'R':n,'hit':sum(x['top10_hit'] for x in rows),'hit_rate':sum(x['top10_hit'] for x in rows)/n if n else 0,
            'avg_comp':sum(x['composite_odds'] for x in rows)/n if n else 0,'cost':cost,'return':ret,
            'roi':ret/cost*100 if cost else 0,'zero_ticket_races':sum(x['zero_stake_tickets']>0 for x in rows)}

def main():
    # Reconstruct the canonical v191 June/July/Aug rows using the exact current loader.
    hist,miss,cover,missing_dates=restore.hist_rows()
    h=pd.DataFrame(hist);h['_code']=h.race_code.map(norm_code)
    att=pd.read_csv(ATT);att['_code']=att.race_code.map(norm_code)
    keep=['_code']+TACTICS+PRIOR_EX
    h=h.merge(att[keep],on='_code',how='inner',validate='one_to_one')
    for c in TACTICS+PRIOR_EX:h[c]=pd.to_numeric(h[c],errors='coerce').fillna(.5)
    h['venue']=h['venue'].astype(str)
    tr=h[h.month=='2026-06'].copy();tu=h[h.month=='2026-07'].copy();te=h[h.month=='2026-08'].copy()
    if min(len(tr),len(tu),len(te))<1000:raise RuntimeError(f'bad merge sizes {[len(tr),len(tu),len(te)]}')

    records=[]; july_scores=[]; frozen={}
    for name,extras in SETS.items():
        m=fit_model(tr,extras);pj=probs(m,tu,extras);pa=probs(m,te,extras)
        for rate in TIERS:
            cut=cut_for_rate(pj,rate);mj=metr(tu,pj,cut)
            july_scores.append({'model':name,'tier':rate,'cut':cut,**{f'jul_{k}':v for k,v in mj.items()}})
            # Save predictions now, but model selection below uses July metrics only.
            frozen[(name,rate)]={'cut':cut,'pj':pj,'pa':pa,'mj':mj,'ma':metr(te,pa,cut)}
    # Choose one feature set independently per tier using JULY ONLY: recall, precision, then smaller watch.
    selected={}
    for rate in TIERS:
        cand=[x for x in july_scores if x['tier']==rate]
        cand.sort(key=lambda x:(x['jul_recall'],x['jul_precision'],-x['jul_watch_rate']),reverse=True)
        selected[rate]=cand[0]['model']

    # Output all July/Aug diagnostics, marking the pre-August frozen selected model.
    for name in SETS:
        for rate in TIERS:
            z=frozen[(name,rate)]
            for split,df,p,mm in [('tune_july',tu,z['pj'],z['mj']),('untouched_aug',te,z['pa'],z['ma'])]:
                records.append({'model':name,'tier_target':rate,'selected_on_july':int(selected[rate]==name),'split':split,
                    'cut':z['cut'],**mm})
    pd.DataFrame(records).to_csv(OUT,index=False,encoding='utf-8-sig')

    # Monetary replay: same August od3 source for canonical v191 and each July-selected enhanced tier.
    prod=pd.read_csv(V195);prod=prod[prod.month=='2026-08'].copy();prod['_code']=prod.race_code.map(norm_code)
    od=load_od3()
    fin=pd.read_csv(V108,usecols=['race_code','turn_margin23','st_margin23']);fin['_code']=fin.race_code.map(norm_code);fin=fin.drop_duplicates('_code').set_index('_code')
    v191=pd.read_csv(V191);v191=v191[v191.split=='untouched_aug'].copy();v191['_code']=v191.race_code.map(norm_code)
    base_codes=set(v191.loc[pd.to_numeric(v191.pre_prob_eval)>=.072608,'_code'])
    money=[]
    money+=settle(prod,base_codes,od,'v191_cut_0.072608',fin)
    for rate in TIERS:
        name=selected[rate];z=frozen[(name,rate)];sel=set(te.loc[np.asarray(z['pa'])>=z['cut'],'_code'])
        money+=settle(prod,sel,od,f'v207_{int(rate*100)}pct_{name}',fin)
    pd.DataFrame(money).to_csv(ROI_OUT,index=False,encoding='utf-8-sig')

    L=['# v207 enhanced 3-head PRE — strict July select / August untouched','',
       '**SHADOW検証。productionは変更しない。PREは監視候補のみで、正式判定は展示後 v165 p3head>=30% -> v166 Top10。**','',
       '## Leak audit','- `analysis_3attack_rows.csv` generator computes target-day features before reading outcomes.',
       '- prior exhibition / prior straight / prior display / prior turn and motor history are inserted into cache only after each day, so target day cannot enter its own PRE features.',
       f'- reconstructed rows: June {len(tr)}, July {len(tu)}, August {len(te)}; unmatched {miss}; waku sources {cover}; missing dates {missing_dates or "none"}.','',
       '## July-only model selection -> frozen August test','|tier|July-selected model|cut|July watch|July recall|July precision|Aug watch|Aug recall|Aug precision|',
       '|---:|---|---:|---:|---:|---:|---:|---:|---:|']
    for rate in TIERS:
        name=selected[rate];z=frozen[(name,rate)];a=z['mj'];b=z['ma']
        L.append(f'|{rate*100:.0f}%|{name}|{z["cut"]:.6f}|{a["watch"]} ({a["watch_rate"]*100:.1f}%)|{a["recall"]*100:.1f}%|{a["precision"]*100:.1f}%|{b["watch"]} ({b["watch_rate"]*100:.1f}%)|{b["recall"]*100:.1f}%|{b["precision"]*100:.1f}%|')
    L+=['','### All feature-set diagnostics (August is report-only, never used for selection)','|model|tier|July recall|July watch|Aug recall|Aug watch|selected on July|','|---|---:|---:|---:|---:|---:|---|']
    for name in SETS:
        for rate in TIERS:
            z=frozen[(name,rate)];a=z['mj'];b=z['ma']
            L.append(f'|{name}|{rate*100:.0f}%|{a["recall"]*100:.1f}%|{a["watch_rate"]*100:.1f}%|{b["recall"]*100:.1f}%|{b["watch_rate"]*100:.1f}%|{"YES" if selected[rate]==name else ""}|')
    L+=['','## August untouched operational replay — BoatraceCSV od3 only','','¥10,000/race, inverse-odds Dutch, 100-yen units. Same source/method for every row.','',
        '|PRE rule|settled R|Top10 hit|avg composite|cost|return|ROI|zero-stake-ticket races|','|---|---:|---:|---:|---:|---:|---:|---:|']
    tags=['v191_cut_0.072608']+[f'v207_{int(r*100)}pct_{selected[r]}' for r in TIERS]
    for tag in tags:
        rr=[x for x in money if x['tag']==tag];a=agg(rr)
        L.append(f'|{tag}|{a["R"]}|{a["hit_rate"]*100:.1f}%|{a["avg_comp"]:.3f}|¥{a["cost"]:,}|¥{a["return"]:,.0f}|**{a["roi"]:.1f}%**|{a["zero_ticket_races"]}|')
    L+=['','## PICK UP subset inside each PRE rule','|PRE rule|PICK UP R|hit|ROI|','|---|---:|---:|---:|']
    for tag in tags:
        rr=[x for x in money if x['tag']==tag and x.get('pickup')==1];a=agg(rr)
        L.append(f'|{tag}|{a["R"]}|{a["hit_rate"]*100:.1f}%|{a["roi"]:.1f}%|')
    L+=['','## Decision rule','- Feature-set choice and cut are locked using July only. August is untouched evaluation only.','- A better August number is not enough to production-adopt; this remains SHADOW until an additional future period confirms it.','- Do not compare these od3 ROI values directly with official-closing-odds v202/v205 as if they had the same odds provenance.']
    SUMMARY.write_text('\n'.join(L)+'\n',encoding='utf-8')
    print('\n'.join(L),flush=True)

if __name__=='__main__':main()
