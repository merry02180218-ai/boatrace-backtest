#!/usr/bin/env python3
from __future__ import annotations
import json, math
from pathlib import Path
import numpy as np
import pandas as pd
from research.run_3head_close_margin_fourth_ticket import SOURCE, MONTHS, model_and_features
from research.run_3head_exhibition_v5 import EX, STATIC, load_direct, pair_rows
from analyze_v205_3head_operational_replay import load_odds

BANK=10000
MARGIN=.075
OUT='research_v289_3head_close_margin_fourth_ticket_roi.json'
DETAIL='research_v289_3head_close_margin_fourth_ticket_roi_detail.csv'

def odds_row(oi,code):
    if code not in oi.index:return None
    r=oi.loc[code]
    return r.iloc[-1] if isinstance(r,pd.DataFrame) else r

def ticket_key(second,third): return f'3-{int(second)}-{int(third)}'

def get_odd(row,ticket):
    # load_odds() uses trifecta ticket columns; tolerate common naming variants.
    for k in (ticket,ticket.replace('-','_'),f'odds_{ticket}',f'odds__{ticket}',f'trifecta_{ticket}'):
        if k in row.index:
            v=pd.to_numeric(pd.Series([row[k]]),errors='coerce').iloc[0]
            if pd.notna(v) and float(v)>0:return float(v)
    return None

def dutch(tickets,odr):
    odds=[get_odd(odr,t) for t in tickets]
    if any(o is None for o in odds): return None
    inv=np.array([1.0/o for o in odds]); comp=1.0/inv.sum()
    raw=BANK*inv/inv.sum()/100.0
    base=np.floor(raw).astype(int); rem=BANK//100-int(base.sum())
    frac=raw-base
    order=np.argsort(-frac,kind='stable')
    for i in order[:rem]:base[i]+=1
    stakes=(base*100).astype(int)
    assert int(stakes.sum())==BANK
    return float(comp),dict(zip(tickets,stakes)),dict(zip(tickets,odds))

def settle(tickets,odr,actual):
    z=dutch(tickets,odr)
    if z is None:return None
    comp,stakes,odds=z
    if actual in stakes:return comp,float(stakes[actual]*odds[actual]),1
    return comp,0.0,0

def prep():
    use=['date','race_code_norm','settle__actual_combo','settle__winner','settle__usable','closing_odds__ok']+[f'card__艇{i}_{m}' for i in range(1,7) for m in STATIC]
    df=pd.read_csv(SOURCE,usecols=use,low_memory=False);df.date=pd.to_datetime(df.date);df['rc']=pd.to_numeric(df.race_code_norm,errors='coerce').astype('Int64')
    # September hard-cut before any outcome filtering.
    df=df[df.date<'2026-09-01'].copy();df=df[(df.settle__usable==1)&(df.closing_odds__ok==1)&(~df.rc.isin(EX))].copy()
    feb=df[(df.date>='2026-02-01')&(df.date<'2026-03-01')].copy();assert len(feb)==3970
    heads=feb[feb.settle__winner==3].copy();assert len(heads)==478
    codes=[str(int(x)).zfill(12) for x in df.rc.dropna().unique()];direct=load_direct(codes)
    common=heads[heads.rc.map(lambda x:direct.get(str(int(x)).zfill(12),{}).get('common',False))].copy();assert len(common)==390
    train=pair_rows(common,direct,'A',{});model,feats=model_and_features(train);model.fit(train[feats],train.y)
    return df,direct,model,feats

def main():
    df,direct,model,feats=prep();od=load_odds().copy();od['race_code']=od.race_code.astype(str).str.zfill(12);oi=od.set_index('race_code',drop=False)
    rows=[]
    for month in MONTHS:
        st=pd.Timestamp(2026,month,1);en=st+pd.offsets.MonthBegin(1)
        h=df[(df.date>=st)&(df.date<en)&(df.settle__winner==3)].copy();h=h[h.rc.map(lambda x:direct.get(str(int(x)).zfill(12),{}).get('common',False))]
        x=pair_rows(h,direct,'A',{});x['p']=model.predict_proba(x[feats])[:,1]
        x=x.sort_values(['race_code','p','second','third'],ascending=[True,False,True,True]).copy();x['rank']=x.groupby('race_code').cumcount()+1
        actual_map=h.set_index(h.rc.map(lambda v:str(int(v)).zfill(12)))['settle__actual_combo'].astype(str).to_dict()
        for code,g in x.groupby('race_code'):
            code=str(code).zfill(12);g=g.sort_values('rank');r3=g[g['rank']==3];r4=g[g['rank']==4]
            if r3.empty or r4.empty:continue
            gap=float(r3.p.iloc[0]-r4.p.iloc[0]);add=gap<=MARGIN
            base=[ticket_key(r.second,r.third) for _,r in g[g['rank']<=3].iterrows()]
            four=base+([ticket_key(r4.second.iloc[0],r4.third.iloc[0])] if add else [])
            odr=odds_row(oi,code)
            if odr is None:continue
            actual=str(actual_map.get(code,''));actual=actual.replace('>','-').replace('_','-').replace(' ','')
            sb=settle(base,odr,actual);sf=settle(four,odr,actual)
            if sb is None or sf is None:continue
            rows.append({'month':month,'race_code':code,'gap':gap,'add4':int(add),'actual':actual,'base_tickets':'|'.join(base),'four_tickets':'|'.join(four),'base_comp_odds':sb[0],'base_return_yen':sb[1],'base_hit':sb[2],'four_comp_odds':sf[0],'four_return_yen':sf[1],'four_hit':sf[2]})
    q=pd.DataFrame(rows);q.to_csv(DETAIL,index=False)
    def agg(g):
        n=len(g);bc=n*BANK;fc=n*BANK;br=float(g.base_return_yen.sum());fr=float(g.four_return_yen.sum())
        return {'R':n,'added_races':int(g.add4.sum()),'base_hits':int(g.base_hit.sum()),'four_hits':int(g.four_hit.sum()),'base_avg_comp_odds':float(g.base_comp_odds.mean()),'four_avg_comp_odds':float(g.four_comp_odds.mean()),'base_investment_yen':bc,'base_return_yen':br,'base_roi_pct':100*br/bc if bc else None,'four_investment_yen':fc,'four_return_yen':fr,'four_roi_pct':100*fr/fc if fc else None,'roi_delta_pt':100*(fr-br)/bc if bc else None,'incremental_return_yen':fr-br}
    monthly={str(m):{**agg(q[q.month==m]),'non_pristine':m in (7,8)} for m in MONTHS}
    oos=agg(q[q.month.isin([4,5,6])])
    out={'phase':'3HEAD_CLOSE_MARGIN_FOURTH_TICKET_COMPOSITE_ODDS_ROI','margin':MARGIN,'bank_per_race_yen':BANK,'staking':'inverse-odds Dutch with 100-yen Hamilton rounding','monthly':monthly,'apr_jun_frozen':oos,'candidate_retuned':False,'july_august_non_pristine':True,'september_outcomes_read':False,'production_changed':False}
    Path(OUT).write_text(json.dumps(out,ensure_ascii=False,indent=2));print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
