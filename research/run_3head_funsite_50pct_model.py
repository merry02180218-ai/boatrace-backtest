from __future__ import annotations
import csv, io, json, re, urllib.request
import numpy as np, pandas as pd
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

BASE='https://boatracecsv.github.io/data'
SRC='analysis_v289_3head_wave21_allrace_feature_settled.csv'
EX={202602071007,202602120606,202602150404,202602161108,202602171607,202602171911,202602191910,202602270507,202603031807,202603080101,202603081308,202603101810,202603111810,202603122004,202603141405,202603200809,202603211406,202603241009,202603271906,202603281904}
KINDS=['programs/race_cards','programs/recent_national','programs/recent_local']
CORE=['全国平均ST','全国勝率','全国2連対率','全国3連対率','当地勝率','当地2連対率','当地3連対率','F本数','L本数','モーター2連対率','モーター3連対率','ボート2連対率','ボート3連対率']

def fetch(kind,d):
    u=f'{BASE}/{kind}/{d:%Y/%m/%d}.csv'
    try:
        with urllib.request.urlopen(u,timeout=30) as r:
            return list(csv.DictReader(io.StringIO(r.read().decode('utf-8-sig'))))
    except Exception:
        return []

def num(v):
    try: return float(v)
    except (TypeError,ValueError): return np.nan

def ranks_summary(row,boat,prefix):
    vals=[]
    for k in range(1,6):
        s=(row.get(f'艇{boat}_前{k}節_着順列') or '').strip()
        # only ordinary numeric finish ranks 1..6; F/L/K/etc are excluded
        vals += [int(x) for x in re.findall(r'(?<!\\d)[1-6](?!\\d)',s)]
    if not vals:
        return {f'{prefix}_starts':0,f'{prefix}_mean':np.nan,f'{prefix}_win':np.nan,f'{prefix}_top2':np.nan,f'{prefix}_top3':np.nan}
    a=np.array(vals,dtype=float)
    return {f'{prefix}_starts':len(a),f'{prefix}_mean':float(a.mean()),f'{prefix}_win':float((a==1).mean()),f'{prefix}_top2':float((a<=2).mean()),f'{prefix}_top3':float((a<=3).mean())}

def make_features(rc,rn,rl):
    out={'rc':int(rc['レースコード'])}
    for b in range(1,7):
        for c in CORE: out[f'b{b}__{c}']=num(rc.get(f'艇{b}_{c}'))
        out.update({f'b{b}__{k}':v for k,v in ranks_summary(rn,b,'recentN').items()})
        out.update({f'b{b}__{k}':v for k,v in ranks_summary(rl,b,'recentL').items()})
    bases=CORE+['recentN_starts','recentN_mean','recentN_win','recentN_top2','recentN_top3','recentL_starts','recentL_mean','recentL_win','recentL_top2','recentL_top3']
    for c in bases:
        b3=out.get(f'b3__{c}',np.nan)
        others=[out.get(f'b{x}__{c}',np.nan) for x in [1,2,4,5,6]]
        out[f'b3mean_gap__{c}']=b3-np.nanmean(others) if np.isfinite(b3) and np.isfinite(others).any() else np.nan
        for x in [1,2,4,5,6]: out[f'b3gap{x}__{c}']=b3-out.get(f'b{x}__{c}',np.nan)
    return out

def main():
    base=pd.read_csv(SRC,low_memory=False); base['date']=pd.to_datetime(base.date); base['rc']=pd.to_numeric(base.race_code_norm,errors='coerce').astype('Int64')
    base=base[(base.settle__usable==1)&(base.closing_odds__ok==1)&(~base.rc.isin(EX))&(base.date>='2026-02-01')&(base.date<'2026-04-01')].copy()
    rows=[]; source_days={k:0 for k in KINDS}
    for ds in pd.date_range('2026-02-01','2026-03-31'):
        day={k:fetch(k,ds.date()) for k in KINDS}
        for k in KINDS: source_days[k]+=bool(day[k])
        if not all(day[k] for k in KINDS): continue
        maps={k:{str(r.get('レースコード','')).strip():r for r in day[k]} for k in KINDS}
        common=set(maps[KINDS[0]]) & set(maps[KINDS[1]]) & set(maps[KINDS[2]])
        for code in common:
            if code.isdigit(): rows.append(make_features(maps[KINDS[0]][code],maps[KINDS[1]][code],maps[KINDS[2]][code]))
    X=pd.DataFrame(rows).drop_duplicates('rc')
    dat=base[['rc','date','settle__winner']].merge(X,on='rc',how='inner'); dat['y']=(dat.settle__winner==3).astype(int)
    feats=[c for c in X.columns if c!='rc' and X[c].notna().sum()>=20]
    feb=dat[dat.date<'2026-03-01'].sort_values(['date','rc']); mar=dat[dat.date>='2026-03-01'].sort_values(['date','rc'])
    cut=feb.date.quantile(.70); tr=feb[feb.date<=cut]; va=feb[feb.date>cut]
    candidates=[]
    for C in [.03,.1,.3,1,3]:
        m=make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),LogisticRegression(C=C,class_weight='balanced',solver='liblinear',max_iter=2000,random_state=0))
        m.fit(tr[feats],tr.y); s=m.predict_proba(va[feats])[:,1]
        order=np.argsort(-s); yy=va.y.to_numpy()[order]; ss=s[order]; cum=np.cumsum(yy); nn=np.arange(1,len(yy)+1); rates=cum/nn
        for target in [.50,.45,.40]:
            ok=np.where(rates>=target)[0]; k=int(ok[-1]+1) if len(ok) else 0
            if k: candidates.append({'C':C,'target':target,'n':k,'hits':int(cum[k-1]),'rate':float(rates[k-1]),'threshold':float(ss[k-1])})
    frozen={}
    for target in [.50,.45,.40]:
        q=[x for x in candidates if x['target']==target]; frozen[str(target)]=max(q,key=lambda x:(x['n'],x['rate'],-x['C'])) if q else None
    results={}
    for key,f in frozen.items():
        if not f: results[key]=None; continue
        m=make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),LogisticRegression(C=f['C'],class_weight='balanced',solver='liblinear',max_iter=2000,random_state=0)); m.fit(feb[feats],feb.y)
        score=m.predict_proba(mar[feats])[:,1]; sel=mar.assign(score=score)[score>=f['threshold']].sort_values(['date','rc']); n=len(sel); h=int(sel.y.sum()); half=n//2
        results[key]={'frozen':f,'march_n':n,'march_hits':h,'march_rate':h/n if n else None,'early':{'n':half,'hits':int(sel.iloc[:half].y.sum()) if half else 0},'late':{'n':n-half,'hits':int(sel.iloc[half:].y.sum()) if n-half else 0}}
    out={'policy':{'feb_selection_only':True,'march_one_shot':True,'september_outcomes_read':False,'session_current_meet_features_used':False},'source_days':source_days,'funsite_races':len(X),'joined_feb':len(feb),'joined_mar':len(mar),'feature_count':len(feats),'feature_names':feats,'validation_candidates':candidates,'results':results}
    with open('research_3head_funsite_50pct_model_result.json','w',encoding='utf-8') as g: json.dump(out,g,ensure_ascii=False,indent=2,default=str)
    print(json.dumps({k:v for k,v in out.items() if k not in ['feature_names','validation_candidates']},ensure_ascii=False,indent=2,default=str))
if __name__=='__main__': main()
