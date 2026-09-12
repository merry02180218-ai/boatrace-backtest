#!/usr/bin/env python3
"""Recover missing exact A-LIVE N=2..20 curves for v291 rescue research.

Uses only Apr-Jun historical pre-result features, the frozen v291 downstream
artifact/pair policy, and the repository's immutable official closing-odds
archive. Jul/Aug are excluded; September outcomes are never read. The existing
v288 OOF table remains untouched and is augmented only in a temporary research
CSV with rows marked A_LIVE_RECOVERED.
"""
from __future__ import annotations
from pathlib import Path
import json, math
import numpy as np
import pandas as pd

import analyze_4head_v291_a_targetcomp_rescue as target
import analyze_v270_4head_win_feature_importance as v270
import analyze_v271_4head_arank_expansion as v271
import analyze_v274_4head_opponent_feature_audit as v274
import analyze_v278_4head_opponent_current_exhibition_audit as v278
import analyze_v279_4head_opponent_listwise_rebuild as v279
import analyze_v281_4head_opponent_third_scenario as v281
import analyze_v282_4head_conditional_third as v282
import analyze_v283_4head_conditional_pair_order as v283
from head4_v273_a_live_inference import load_artifact as load_a_artifact, score_a
from head4_v291_downstream_inference import load_artifact, score_second, score_conditional_third

ROOT=Path(__file__).resolve().parent
BASE=ROOT/'analysis_v288_4head_composite_odds_alln_detail.csv'
AUG=ROOT/'analysis_v291_4head_composite_odds_alln_exactalive.csv'
AUD=ROOT/'audit_4head_v291_a_live_curve_recovery.json'
MONTHS=('2026-04','2026-05','2026-06')
BOATS=v279.BOATS


def exact_ids():
    art=load_a_artifact();o=v271.oof_a_scores().copy();o['race_code']=o.race_code.astype(str).str.zfill(12)
    o=o[o.month.astype(str).isin(MONTHS)].copy();pre=pd.to_numeric(o.PRE);post=pd.to_numeric(o.POST);env=pd.to_numeric(o.ENV_ENTRY)
    sg=art['S_gate'];ag=art['A_gate'];outside=~((pre>=sg['PRE'])&(post>=sg['POST'])&(env>=sg['ENV_ENTRY']))
    e=o[(pre>=ag['PRE'])&(post>=ag['POST'])&outside][['race_code']].copy()
    d,_,_=v270.prepare();d=d[d._date<=pd.Timestamp('2026-06-30')].copy();fs=list(art['A_SCORE']['features'])
    r=d[['race_code',*fs]].copy();r['race_code']=r.race_code.astype(str).str.zfill(12);z=e.merge(r,on='race_code',validate='one_to_one')
    z['score']=[score_a(x,art) for x in z[fs].to_dict('records')]
    return set(z.loc[z.score>=float(art['A_gate']['A_SCORE_LIVE']),'race_code'])


def generic_long(d,codes):
    specs=v274.feature_specs(d);rec=[]
    for _,r in d[d.race_code.astype(str).str.zfill(12).isin(codes)].iterrows():
        code=str(r.race_code).zfill(12);date=str(r.date);month=date[:7]
        for b in BOATS:
            x={'date':date,'month':month,'race_code':code,'boat':int(b)}
            for n,s in specs.items():x[n]=v274.fval(r,b,s)
            rec.append(x)
    q=pd.DataFrame(rec)
    if q.groupby('race_code').size().eq(5).all() is False:raise RuntimeError('generic opponent row count mismatch')
    q=v278.add_current(q);q=v281.add_scenario(q)
    rel=[c for c in list(v279.ABILITY)+list(v279.PLAYER)+list(v279.PRIOR_HINTS)+list(v279.START_HINTS)+list(v279.POSITION)+list(v279.CURRENT) if c in q]
    q=v279.add_relative(q,rel);return q,v279.family_map(q)


def conditional_rows(z,base):
    tbase=[c for c in base['PLAYER_START'] if c in z]
    scenario=[c for c in z.columns if c.startswith('is_boat') or c in ('is_inner123','is_outer56','is_inner_edge3','is_outer_edge5','h4_attack','h4_turning') or '__vs4' in c or '__abs4' in c or c.startswith('h4_attack_x_')]
    out=[]
    for code,g in z.groupby('race_code'):
        by={int(r.boat):r for _,r in g.iterrows()}
        for s in BOATS:
            sr=by[s]
            for t in BOATS:
                if t==s:continue
                tr=by[t];x={'race_code':str(code).zfill(12),'second_boat':s,'third_boat':t}
                for c in tbase:x[f't_{c}']=tr.get(c,np.nan)
                for c in scenario:x[f't_{c}']=tr.get(c,np.nan)
                x['pair_same_side4']=float((s<4 and t<4) or (s>4 and t>4));x['pair_second_inner']=float(s<4);x['pair_second_outer']=float(s>4)
                x['pair_third_inner']=float(t<4);x['pair_third_outer']=float(t>4);x['pair_adjacent']=float(abs(t-s)==1);x['pair_distance']=float(abs(t-s));x['pair_third_minus_second']=float(t-s)
                for b in (1,2,3,5,6):x[f'pair_second_is{b}']=float(s==b)
                for c in v282.PAIR_KEYS:
                    if c in z:
                        tv=pd.to_numeric(pd.Series([tr.get(c,np.nan)]),errors='coerce').iloc[0];sv=pd.to_numeric(pd.Series([sr.get(c,np.nan)]),errors='coerce').iloc[0]
                        x[f'diff_{c}']=tv-sv if pd.notna(tv) and pd.notna(sv) else np.nan;x[f'prod_{c}']=tv*sv if pd.notna(tv) and pd.notna(sv) else np.nan
                out.append(x)
    return pd.DataFrame(out)


def odds_map(code):
    ds=f'{code[:4]}/{code[4:6]}/{code[6:8]}';p=ROOT/'data'/'official_closing_odds3t'/f'{ds}.csv'
    q=pd.read_csv(p,dtype=str);j=int(code[8:10]);r=int(code[10:12]);row=q[(pd.to_numeric(q.jcd)==j)&(pd.to_numeric(q.rno)==r)]
    if len(row)!=1:raise RuntimeError(f'closing odds row missing {code}')
    rr=row.iloc[0];om={}
    for k in q.columns:
        if k.count('-')==2:
            try:v=float(rr[k])
            except:continue
            if math.isfinite(v) and v>0:om[k]=v
    if len(om)!=120:raise RuntimeError(f'need 120 closing odds {code}, got {len(om)}')
    return om,str(rr.get('source_type','')),str(rr.get('snapshot_type','')),str(rr.get('source_url',''))


def full_order(p2,pc):return v283.order_policy(p2,pc,0.60,'TOP2XTOP2',1.5)

def dutch_return(odds,actual):
    inv=np.array([1.0/x for x in odds],float);comp=1.0/inv.sum();ideal=100.0*inv/inv.sum();u=np.floor(ideal).astype(int);left=100-int(u.sum())
    frac=ideal-u;order=np.argsort(-frac,kind='stable');u[order[:left]]+=1
    stakes=u*100;ret=0.0
    if actual is not None:
        for i,(combo,o) in enumerate(actual[0]):
            if combo==actual[1]:ret=float(stakes[i])*float(o);break
    return comp,ret


def build_rows(missing,d,z,base,cart):
    cr=conditional_rows(z,base);rows=[];prov=[]
    for code in sorted(missing):
        g=z[z.race_code.astype(str).str.zfill(12)==code].copy();cg=cr[cr.race_code==code].copy()
        p2=score_second(g.to_dict('records'),cart);pc=score_conditional_third(cg.to_dict('records'),cart);order=full_order(p2,pc)
        om,stype,snap,url=odds_map(code);rr=d[d.race_code.astype(str).str.zfill(12)==code]
        if len(rr)!=1:raise RuntimeError(f'result row mismatch {code}')
        r=rr.iloc[0];winner=int(float(r.winner)) if pd.notna(r.winner) else 0;second=int(float(r.second)) if pd.notna(r.second) else 0;third=int(float(r.third)) if pd.notna(r.third) else 0
        actual=f'4-{second}-{third}' if winner==4 else None
        combos=[f'4-{s}-{t}' for s,t in order]
        for n in range(2,21):
            sel=combos[:n];ods=[om[x] for x in sel];inv=np.array([1.0/x for x in ods]);comp=float(1.0/inv.sum())
            ideal=100.0*inv/inv.sum();u=np.floor(ideal).astype(int);left=100-int(u.sum());frac=ideal-u;idx=np.argsort(-frac,kind='stable');u[idx[:left]]+=1;stakes=u*100
            hit=int(actual in sel) if actual else 0;ret=float(stakes[sel.index(actual)]*om[actual]) if hit else 0.0
            rows.append({'date':str(r.date),'month':str(r.date)[:7],'race_code':code,'layer':'A_LIVE_RECOVERED','n':n,'winner':winner,'second':second,'third':third,'head4_win':int(winner==4),'hit':hit,'return_yen':ret,'profit_yen':ret-10000.0,'comp_odds':comp,'comp_band':'RECOVERED','tickets':'|'.join(sel)})
        prov.append({'race_code':code,'source_type':stype,'snapshot_type':snap,'source_url':url,'pair_policy':'TOP2XTOP2','alpha2':0.60,'curve_rows':19})
    return pd.DataFrame(rows),prov


def flexible_load():
    q=pd.read_csv(AUG,dtype={'race_code':str});q['race_code']=q.race_code.astype(str).str.zfill(12)
    if set(q.month.astype(str).unique())!=set(MONTHS):raise RuntimeError('forbidden month in augmented source')
    if set(q.n.astype(int).unique())!=set(range(2,21)):raise RuntimeError('N universe mismatch')
    for code,g in q.groupby('race_code'):
        z=g.sort_values('n')
        if len(z)!=19 or z.n.nunique()!=19:raise RuntimeError(f'incomplete N curve {code}')
        if np.any(np.diff(z.comp_odds.to_numpy(float))>1e-9):raise RuntimeError(f'non-monotone composite curve {code}')
    return q


def main():
    q=pd.read_csv(BASE,dtype={'race_code':str});q['race_code']=q.race_code.astype(str).str.zfill(12);ids=exact_ids();have=set(q.race_code);missing=sorted(ids-have)
    d,_,_=v270.prepare();d=d[d._date<=pd.Timestamp('2026-06-30')].copy();d['race_code']=d.race_code.astype(str).str.zfill(12)
    z,base=generic_long(d,set(missing));cart=load_artifact();add,prov=build_rows(missing,d,z,base,cart) if missing else (pd.DataFrame(columns=q.columns),[])
    aug=pd.concat([q,add[q.columns]],ignore_index=True);aug.to_csv(AUG,index=False)
    audit={'schema':'head4_v291_exact_a_live_curve_recovery_v1','development_months':list(MONTHS),'jul_aug_outcomes_used':False,'september_outcomes_used':False,'v96_used':False,'base_curve_races':int(q.race_code.nunique()),'exact_a_live_R':len(ids),'missing_before_R':len(missing),'recovered_R':len(prov),'recovered_race_codes':missing,'odds_snapshot_class':'official_closing/closing_displayed','provenance':prov,'status':'PASS' if len(prov)==len(missing) else 'FAIL'}
    AUD.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    target.SRC=AUG;target.load_curves=flexible_load;target.main()
    print(json.dumps(audit,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
