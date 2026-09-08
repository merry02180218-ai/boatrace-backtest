#!/usr/bin/env python3
"""v223: audit previously-unused clean pre-deadline feature families.

Starts from v222's best head family (PRIOR12+CURRENT+REL) and keeps v221 pair ranker fixed.
New families: weather/water, exhibition entry, body/adjustment weight, recent national form,
recent local-course form. Jul/Aug are never used for fitting/tuning/evaluation.
"""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import date,timedelta
from pathlib import Path
import re
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score,brier_score_loss,log_loss

import analyze_v165_3head_monthly_walkforward as v165
import analyze_v205_3head_operational_replay as v205
import analyze_v221_3head_scenario_pair as v221
import analyze_v222_3head_broad_feature_audit as v222
from backtest import rows

ROOT=Path(__file__).resolve().parent
SRC=ROOT/'analysis_v108_1head_feasibility.csv'
OUT=ROOT/'analysis_v223_3head_unused_feature_audit.csv'
SUM=ROOT/'summary_v223_3head_unused_feature_audit.md'
EVAL_MONTHS=['2025-12','2026-01','2026-02','2026-03','2026-04','2026-05','2026-06']
PRELOAD=date(2025,10,1);END=date(2026,6,30);CONTAM=pd.Timestamp('2026-07-01');BANK=10000

def ff(x,d=np.nan):
    try:return float(x)
    except:return d

def ii(x,d=0):
    try:return int(float(x))
    except:return d

def bycode(rs):return {str(r.get('レースコード','')).zfill(12):r for r in rs if r.get('レースコード')}
def uniq(a):return list(dict.fromkeys(a))
def safe_auc(y,p):
    try:return float(roc_auc_score(y,p)) if len(set(map(int,y)))>1 else float('nan')
    except:return float('nan')
def safe_ll(y,p):
    try:return float(log_loss(y,np.clip(p,1e-6,1-1e-6),labels=[0,1]))
    except:return float('nan')

def parse_places(s):
    # Keep only normal 1..6 finish digits; non-finish symbols are ignored rather than outcome-imputed.
    return [int(x) for x in re.findall(r'[1-6]',str(s or ''))]
def form_features(r,b,prefix,target_date):
    allp=[];recent=[];days=[];grades=[]
    for k in range(1,6):
        a=parse_places(r.get(f'艇{b}_前{k}節_着順列'))
        allp += a
        if k<=2:recent += a
        ed=pd.to_datetime(r.get(f'艇{b}_前{k}節_終了日'),errors='coerce')
        if pd.notna(ed):days.append(max(0,(target_date-ed).days))
        g=str(r.get(f'艇{b}_前{k}節_グレード',''))
        if g:grades.append(1. if ('SG' in g or 'ＧⅠ' in g or 'G1' in g) else .7 if ('ＧⅡ' in g or 'G2' in g) else .5 if ('ＧⅢ' in g or 'G3' in g) else .2)
    def met(a):
        if not a:return (np.nan,np.nan,np.nan,np.nan,np.nan)
        return (len(a),np.mean(a),np.mean(np.array(a)==1),np.mean(np.array(a)<=2),np.mean(np.array(a)<=3))
    n,av,w,t2,t3=met(allp);rn,rav,rw,rt2,rt3=met(recent)
    return {
      f'{prefix}_starts':n,f'{prefix}_finish_mean':av,f'{prefix}_win':w,f'{prefix}_top2':t2,f'{prefix}_top3':t3,
      f'{prefix}_recent_starts':rn,f'{prefix}_recent_finish_mean':rav,f'{prefix}_recent_win':rw,
      f'{prefix}_recent_top2':rt2,f'{prefix}_recent_top3':rt3,
      f'{prefix}_days_since':min(days) if days else np.nan,
      f'{prefix}_grade_mean':float(np.mean(grades)) if grades else np.nan,
    }

def day_fetch(d):
    y=d.strftime('%Y/%m/%d')
    return d,{
      'sui':rows(f'data/previews/sui/{y}.csv'),
      'tkz':rows(f'data/previews/tkz/{y}.csv'),
      'stt':rows(f'data/previews/stt/{y}.csv'),
      'nat':rows(f'data/programs/recent_national/{y}.csv'),
      'loc':rows(f'data/programs/recent_local/{y}.csv'),
    }

def build_unused(base,dc):
    idx={}
    for ix,r in base.iterrows():
        dt=pd.to_datetime(r[dc],errors='coerce')
        if pd.notna(dt) and dt<CONTAM:idx.setdefault(str(r.get('race_code','')).zfill(12),[]).append(ix)
    days=[];d=PRELOAD
    while d<=END:days.append(d);d+=timedelta(days=1)
    fetched={}
    with ThreadPoolExecutor(max_workers=10) as ex:
        futs=[ex.submit(day_fetch,d) for d in days]
        for j,f in enumerate(as_completed(futs),1):
            try:dd,z=f.result();fetched[dd]=z
            except Exception as e:print('fetch fail',e,flush=True)
            if j%30==0:print('unused days',j,'/',len(days),flush=True)
    exrows={}
    for d in sorted(fetched):
        z=fetched[d];sm=bycode(z['sui']);tm=bycode(z['tkz']);stm=bycode(z['stt']);nm=bycode(z['nat']);lm=bycode(z['loc'])
        for code,ixes in idx.items():
            # avoid scanning every code every day by date prefix
            if not code.startswith(d.strftime('%Y%m%d')):continue
            q={};s=sm.get(code,{});t=tm.get(code,{});st=stm.get(code,{});n=nm.get(code,{});l=lm.get(code,{})
            # Weather/water, all observed before deadline in SUI snapshot.
            q['u_wind_speed']=ff(s.get('風速(m)'));q['u_wind_dir']=ff(s.get('風向'))
            q['u_wave']=ff(s.get('波の高さ(cm)'));q['u_weather']=ff(s.get('天候'))
            q['u_air_temp']=ff(s.get('気温(℃)'));q['u_water_temp']=ff(s.get('水温(℃)'))
            q['u_temp_gap']=q['u_air_temp']-q['u_water_temp'] if np.isfinite(q['u_air_temp']) and np.isfinite(q['u_water_temp']) else np.nan
            # Exhibition entry and weights.
            courses=[];weights=[];adjust=[]
            for b in range(1,7):
                c=ii(st.get(f'艇{b}_コース'),0);q[f'u_b{b}_course']=c if c else np.nan;courses.append(c)
                w=ff(t.get(f'艇{b}_体重(kg)'));a=ff(t.get(f'艇{b}_体重調整(kg)'),0.)
                q[f'u_b{b}_weight']=w;q[f'u_b{b}_adjust']=a;q[f'u_b{b}_totalweight']=w+a if np.isfinite(w) else np.nan
                weights.append(q[f'u_b{b}_totalweight']);adjust.append(a)
            q['u_course3']=q['u_b3_course'];q['u_course3_changed']=float(np.isfinite(q['u_course3']) and q['u_course3']!=3)
            q['u_entry_changes']=sum(1 for b,c in enumerate(courses,1) if c and c!=b)
            wf=[x for x in weights if np.isfinite(x)]
            q['u_b3_weight_relmean']=q['u_b3_totalweight']-np.mean(wf) if wf and np.isfinite(q['u_b3_totalweight']) else np.nan
            q['u_b3_weight_relmin']=q['u_b3_totalweight']-min(wf) if wf and np.isfinite(q['u_b3_totalweight']) else np.nan
            q['u_adjust_total']=float(np.nansum(adjust));q['u_b3_adjust']=q['u_b3_adjust']
            # Boat3 national/local form, plus inside/outside context from the same pre-race files.
            q.update(form_features(n,3,'u_nat3',pd.Timestamp(d)));q.update(form_features(l,3,'u_loc3',pd.Timestamp(d)))
            for b in [1,2,4,5,6]:
                fn=form_features(n,b,f'_n{b}',pd.Timestamp(d));fl=form_features(l,b,f'_l{b}',pd.Timestamp(d))
                # compact opponent-context fields only
                q[f'u_nat_b{b}_win']=fn[f'_n{b}_win'];q[f'u_nat_b{b}_top2']=fn[f'_n{b}_top2']
                q[f'u_loc_b{b}_win']=fl[f'_l{b}_win'];q[f'u_loc_b{b}_top2']=fl[f'_l{b}_top2']
            inn=[q.get('u_nat_b1_win',np.nan),q.get('u_nat_b2_win',np.nan)];out=[q.get(f'u_nat_b{b}_win',np.nan) for b in [4,5,6]]
            if np.isfinite(q.get('u_nat3_win',np.nan)):
                ii0=[x for x in inn if np.isfinite(x)];oo=[x for x in out if np.isfinite(x)]
                q['u_nat3_vs_inside_win']=q['u_nat3_win']-max(ii0) if ii0 else np.nan
                q['u_nat3_vs_outside_win']=q['u_nat3_win']-max(oo) if oo else np.nan
            # Fixed, untuned weather interactions with already-frozen v222 race-shape features.
            wind=q['u_wind_speed'] if np.isfinite(q['u_wind_speed']) else 0.
            wave=q['u_wave'] if np.isfinite(q['u_wave']) else 0.
            q['u_wind_x_stretch']=wind*ff(base.loc[ixes[0]].get('c_attack3_stretch'),0.)
            q['u_wave_x_turn']=wave*ff(base.loc[ixes[0]].get('c_attack3_turn'),0.)
            for ix in ixes:exrows[ix]=q
    return base.join(pd.DataFrame.from_dict(exrows,orient='index'),how='left')

def ncols(d,prefixes):
    return [c for c in d.columns if any(c.startswith(p) for p in prefixes)]
def numeric_ok(d,fs,rate=.65):
    return [c for c in uniq(fs) if c in d.columns and pd.to_numeric(d[c],errors='coerce').notna().mean()>=rate]
def fit_head(d,fs0,vc,first,nextm):
    fs=numeric_ok(d,fs0);tr=d[d._date<first].copy();te=d[(d._date>=first)&(d._date<nextm)].copy()
    for c in fs:tr[c]=pd.to_numeric(tr[c],errors='coerce');te[c]=pd.to_numeric(te[c],errors='coerce')
    cats=[vc] if vc and vc not in fs else [];m=v165.model(fs,cats);m.fit(tr[fs+cats],tr._y.astype(int));te['_p']=m.predict_proba(te[fs+cats])[:,1]
    return te,len(fs)
def maxdd(a):
    c=np.cumsum(np.asarray(a,float));pk=np.maximum.accumulate(np.r_[0.,c]);return float((pk[1:]-c).max()) if len(c) else 0.
def robust(g):
    if g.empty:return (0.,0.,0.,0.,0.)
    roi=100*g.ret.sum()/(len(g)*BANK);md=maxdd(g.sort_values(['date','race_code']).profit);s=g.sort_values('profit',ascending=False);rr=[]
    for k in [1,3,5]:
        q=s.iloc[k:];rr.append(100*q.ret.sum()/(len(q)*BANK) if len(q) else 0.)
    return (roi,md,*rr)

def main():
    raw=pd.read_csv(SRC,dtype={'race_code':str});dc=v165.pc(raw,['date','race_date','ymd']);vc=v165.pc(raw,['venue','jcd','stadium','place']);y,_=v165.target(raw);basefs=v165.feats(raw)
    raw['_date']=pd.to_datetime(raw[dc].astype(str),errors='coerce');raw['_y']=y;raw=raw[raw._date.notna()&raw._y.notna()&(raw._date<CONTAM)].copy()
    d=v221.build(raw,dc);d=v222.build_current(d,dc);d=build_unused(d,dc)
    if (d._date>=CONTAM).any():raise RuntimeError('CONTAMINATION')
    player=v222.cols(d,'b3_pl_');hist=v222.cols(d,'b3_vh_')
    rel=[c for c in d.columns if c.startswith(('c_b3_minus_','c_b3_inside_','c_b3_outside_'))]
    cur=[c for c in v222.cols(d,'c_b3_') if not c.startswith(('c_b3_minus_','c_b3_inside_','c_b3_outside_'))]
    cur += [c for c in d.columns if c.startswith(('c_wall','c_attack3','c_outer','c_ex_spread','c_st_spread','c_turn_spread','c_straight_spread'))]
    best=uniq(list(basefs)+hist+cur+rel)
    weather=ncols(d,['u_wind','u_wave','u_weather','u_air','u_water','u_temp'])
    entry=ncols(d,['u_b1_course','u_b2_course','u_b3_course','u_b4_course','u_b5_course','u_b6_course','u_course3','u_entry'])
    weight=ncols(d,['u_b1_weight','u_b2_weight','u_b3_weight','u_b4_weight','u_b5_weight','u_b6_weight','u_b1_adjust','u_b2_adjust','u_b3_adjust','u_b4_adjust','u_b5_adjust','u_b6_adjust','u_b1_totalweight','u_b2_totalweight','u_b3_totalweight','u_b4_totalweight','u_b5_totalweight','u_b6_totalweight','u_adjust_total'])+[c for c in d.columns if c.startswith('u_b3_weight_rel')]
    nat=ncols(d,['u_nat']);loc=ncols(d,['u_loc'])
    groups={
      'V222_BEST':best,
      '+WEATHER':uniq(best+weather),
      '+ENTRY':uniq(best+entry),
      '+WEIGHT':uniq(best+weight),
      '+NATIONAL_FORM':uniq(best+nat),
      '+LOCAL_FORM':uniq(best+loc),
      '+FORM_ALL':uniq(best+nat+loc),
      '+WEATHER_WEIGHT':uniq(best+weather+weight),
      '+ALL_UNUSED':uniq(best+weather+entry+weight+nat+loc),
    }
    odds=v205.load_odds();oi=odds.set_index('race_code',drop=False);out=[]
    for mon in EVAL_MONTHS:
        first=pd.Timestamp(mon+'-01');nextm=first+pd.offsets.MonthBegin(1);tr=d[d._date<first];pair=v222.fit_pair(tr,'V221')
        base_te,_=fit_head(d,list(basefs),vc,first,nextm);k=max(1,int((base_te._p>=.30).sum()))
        for name,fs in groups.items():
            te,nfeat=fit_head(d,fs,vc,first,nextm);sel=te.nlargest(k,'_p');rv=[]
            for ix,r in sel.iterrows():
                if ii(r.get('valid_result'))!=1 or ii(r.get('course3'),3)!=3:continue
                act=v222.v166.combo(r.get('actual_combo'));actual='-'.join(map(str,act)) if len(act)==3 else '';code=str(r.get('race_code','')).zfill(12)
                if not actual or code not in oi.index:continue
                od=oi.loc[code];od=od.iloc[-1] if isinstance(od,pd.DataFrame) else od;ts=v222.order(r,pair,'V221');s=v222.settle(ts,od,actual)
                if s is None:continue
                rank=ts.index(actual)+1 if actual in ts else 0
                rv.append({'date':r._date.strftime('%Y-%m-%d'),'race_code':code,'y3':int(r._y),'rank':rank,'hit':s[0],'ret':s[1],'profit':s[2]})
            g=pd.DataFrame(rv)
            if g.empty:continue
            h=g[g.y3==1];cov=100*((h['rank']>0)&(h['rank']<=10)).mean() if len(h) else 0.;roi,md,rm1,rm3,rm5=robust(g)
            out.append({'variant':name,'month':mon,'R':len(g),'head_rate':100*g.y3.mean(),'coverage10':cov,'hit10':100*g.hit.mean(),'roi':roi,'maxdd':md,'roi_rm1':rm1,'roi_rm3':rm3,'roi_rm5':rm5,'auc':safe_auc(te._y.astype(int),te._p),'brier':float(brier_score_loss(te._y.astype(int),te._p)),'logloss':safe_ll(te._y.astype(int),te._p),'nfeat':nfeat})
    z=pd.DataFrame(out)
    if z.empty:raise SystemExit('no v223 rows')
    if set(z.month)-set(EVAL_MONTHS):raise RuntimeError('CONTAM MONTH')
    z.to_csv(OUT,index=False)
    L=['# v223 unused pre-deadline feature audit','',
       '- clean months only 2025-12..2026-06; Jul/Aug excluded',
       '- starts from v222 best `PRIOR12+CURRENT+REL`; v221 pair ranker fixed',
       '- new families: SUI weather/water, STT exhibition entry, TKZ body/adjustment weight, recent national/local five-meet form',
       '- historical odds are settlement-only; fixed Top10 exact 10,000-yen Hamilton Dutch','',
       '## Aggregate','|variant|R|3-head|cov10|hit|ROI|min monthly ROI|profitable months|rm5(w)|AUC mean|Brier mean|features|','|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    agg=[]
    for v,g in z.groupby('variant'):
        R=int(g.R.sum());roi=np.average(g.roi,weights=g.R);hr=np.average(g.head_rate,weights=g.R);cv=np.average(g.coverage10,weights=np.maximum(g.R*g.head_rate/100,1e-9));hit=np.average(g.hit10,weights=g.R);rm5=np.average(g.roi_rm5,weights=g.R)
        agg.append((v,R,hr,cv,hit,roi,float(g.roi.min()),int((g.roi>=100).sum()),rm5,float(g.auc.mean()),float(g.brier.mean()),int(g.nfeat.max())))
    agg.sort(key=lambda x:(-x[5],-x[8],-x[9]))
    for a in agg:L.append(f'|{a[0]}|{a[1]}|{a[2]:.2f}%|{a[3]:.2f}%|{a[4]:.2f}%|{a[5]:.2f}%|{a[6]:.2f}%|{a[7]}/7|{a[8]:.2f}%|{a[9]:.4f}|{a[10]:.5f}|{a[11]}|')
    L += ['','## Rule','- Feature discovery only; no automatic production adoption.', '- Prefer replicated monthly gains and rm5 resilience; do not select a family from one payout spike.', '- Motor-history program source begins only in Jul 2026 upstream, so it is deliberately not used in this clean pre-Jul audit.']
    SUM.write_text('\n'.join(L)+'\n',encoding='utf-8');print('\n'.join(L))
if __name__=='__main__':main()
