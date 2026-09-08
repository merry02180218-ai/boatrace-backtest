#!/usr/bin/env python3
"""v224: decompose v223 NATIONAL_FORM without using Jul/Aug.

Keeps v222 best head base and v221 pair ranker fixed. Splits national five-meet form
into recency, finish quality, trend, layoff and grade-context families. Historical odds
remain settlement-only. Evaluation is strict monthly prior-only 2025-12..2026-06.
"""
from __future__ import annotations
import re
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics import brier_score_loss

import analyze_v165_3head_monthly_walkforward as v165
import analyze_v205_3head_operational_replay as v205
import analyze_v221_3head_scenario_pair as v221
import analyze_v222_3head_broad_feature_audit as v222
import analyze_v223_3head_unused_feature_audit as v223

ROOT=Path(__file__).resolve().parent
SRC=ROOT/'analysis_v108_1head_feasibility.csv'
OUT=ROOT/'analysis_v224_3head_national_form_decompose.csv'
SUM=ROOT/'summary_v224_3head_national_form_decompose.md'
EVAL_MONTHS=v223.EVAL_MONTHS; CONTAM=v223.CONTAM; BANK=10000

def places(s): return [int(x) for x in re.findall(r'[1-6]',str(s or ''))]
def grade_score(g):
    g=str(g or '')
    if 'SG' in g:return 1.0
    if 'ＧⅠ' in g or 'G1' in g:return .85
    if 'ＧⅡ' in g or 'G2' in g:return .70
    if 'ＧⅢ' in g or 'G3' in g:return .55
    return .25 if g else np.nan

def met(a):
    if not a:return {'n':np.nan,'mean':np.nan,'win':np.nan,'top2':np.nan,'top3':np.nan,'bad56':np.nan}
    x=np.asarray(a,float)
    return {'n':len(x),'mean':x.mean(),'win':np.mean(x==1),'top2':np.mean(x<=2),'top3':np.mean(x<=3),'bad56':np.mean(x>=5)}

def add_decomp(d,dc):
    # Re-read clean national form only; v223 already guarantees source is pre-race program data.
    idx={}
    for ix,r in d.iterrows():
        dt=pd.to_datetime(r[dc],errors='coerce')
        if pd.notna(dt) and dt<CONTAM: idx.setdefault(str(r.get('race_code','')).zfill(12),[]).append(ix)
    cache={}; rows=[]
    for dt in sorted(set(pd.to_datetime(d[dc],errors='coerce').dropna().dt.date)):
        if pd.Timestamp(dt)>=CONTAM:continue
        y=dt.strftime('%Y/%m/%d')
        rs=v223.rows(f'data/programs/recent_national/{y}.csv'); m=v223.bycode(rs)
        for code,ixes in idx.items():
            if not code.startswith(dt.strftime('%Y%m%d')):continue
            r=m.get(code,{})
            q={}
            for b in range(1,7):
                meets=[places(r.get(f'艇{b}_前{k}節_着順列')) for k in range(1,6)]
                m1=met(meets[0]);m2=met(meets[1]);m12=met(meets[0]+meets[1]);m35=met(meets[2]+meets[3]+meets[4]);mall=met(sum(meets,[]))
                for tag,z in [('m1',m1),('m2',m2),('m12',m12),('m35',m35),('all',mall)]:
                    for k,val in z.items():q[f'f_b{b}_{tag}_{k}']=val
                # fixed trend: positive means recent form improved (lower finish mean / higher win/top2).
                q[f'f_b{b}_trend_mean']=(m35['mean']-m12['mean']) if np.isfinite(m35['mean']) and np.isfinite(m12['mean']) else np.nan
                q[f'f_b{b}_trend_win']=(m12['win']-m35['win']) if np.isfinite(m35['win']) and np.isfinite(m12['win']) else np.nan
                q[f'f_b{b}_trend_top2']=(m12['top2']-m35['top2']) if np.isfinite(m35['top2']) and np.isfinite(m12['top2']) else np.nan
                ends=[]; gs=[]
                for k in range(1,6):
                    ed=pd.to_datetime(r.get(f'艇{b}_前{k}節_終了日'),errors='coerce')
                    if pd.notna(ed):ends.append(max(0,(pd.Timestamp(dt)-ed).days))
                    z=grade_score(r.get(f'艇{b}_前{k}節_グレード'))
                    if np.isfinite(z):gs.append(z)
                q[f'f_b{b}_layoff']=min(ends) if ends else np.nan
                q[f'f_b{b}_grade']=np.mean(gs) if gs else np.nan
                q[f'f_b{b}_m1_grade']=grade_score(r.get(f'艇{b}_前1節_グレード'))
            # relative context for boat3 vs walls/outers; fixed formulas, no tuning.
            for metric in ['m1_win','m1_top2','m12_win','m12_top2','trend_win','trend_top2','all_win','all_top2']:
                v=q.get(f'f_b3_{metric}',np.nan); ins=[q.get(f'f_b1_{metric}',np.nan),q.get(f'f_b2_{metric}',np.nan)]; outs=[q.get(f'f_b{b}_{metric}',np.nan) for b in [4,5,6]]
                ins=[x for x in ins if np.isfinite(x)];outs=[x for x in outs if np.isfinite(x)]
                q[f'f_rel_in_{metric}']=v-max(ins) if np.isfinite(v) and ins else np.nan
                q[f'f_rel_out_{metric}']=v-max(outs) if np.isfinite(v) and outs else np.nan
            for ix in ixes: rows.append((ix,q))
    ex={ix:q for ix,q in rows};return d.join(pd.DataFrame.from_dict(ex,orient='index'),how='left')

def cols(d,p):return [c for c in d.columns if c.startswith(p)]
def main():
    raw=pd.read_csv(SRC,dtype={'race_code':str});dc=v165.pc(raw,['date','race_date','ymd']);vc=v165.pc(raw,['venue','jcd','stadium','place']);y,_=v165.target(raw);basefs=v165.feats(raw)
    raw['_date']=pd.to_datetime(raw[dc].astype(str),errors='coerce');raw['_y']=y;raw=raw[raw._date.notna()&raw._y.notna()&(raw._date<CONTAM)].copy()
    d=v221.build(raw,dc);d=v222.build_current(d,dc);d=v223.build_unused(d,dc);d=add_decomp(d,dc)
    if (d._date>=CONTAM).any():raise RuntimeError('CONTAMINATION')
    hist=v222.cols(d,'b3_vh_');rel=[c for c in d.columns if c.startswith(('c_b3_minus_','c_b3_inside_','c_b3_outside_'))]
    cur=[c for c in v222.cols(d,'c_b3_') if not c.startswith(('c_b3_minus_','c_b3_inside_','c_b3_outside_'))]
    cur += [c for c in d.columns if c.startswith(('c_wall','c_attack3','c_outer','c_ex_spread','c_st_spread','c_turn_spread','c_straight_spread'))]
    best=v223.uniq(list(basefs)+hist+cur+rel);nat223=[c for c in d.columns if c.startswith('u_nat')]
    m1=[c for c in d.columns if c.startswith('f_b3_m1_')];m12=[c for c in d.columns if c.startswith('f_b3_m12_')];m35=[c for c in d.columns if c.startswith('f_b3_m35_')]
    trend=[c for c in d.columns if c.startswith('f_b3_trend_')];lay=[c for c in d.columns if c in ['f_b3_layoff']];grade=[c for c in d.columns if c in ['f_b3_grade','f_b3_m1_grade']];rctx=cols(d,'f_rel_')
    groups={
      'V222_BEST':best,
      'V223_NATIONAL':v223.uniq(best+nat223),
      '+M1':v223.uniq(best+m1),
      '+M12':v223.uniq(best+m12),
      '+M1_M12':v223.uniq(best+m1+m12),
      '+TREND':v223.uniq(best+trend),
      '+M1_M12_TREND':v223.uniq(best+m1+m12+trend),
      '+LAYOFF':v223.uniq(best+lay),
      '+GRADE':v223.uniq(best+grade),
      '+RECENCY_CONTEXT':v223.uniq(best+m1+m12+trend+lay+grade+rctx),
      '+FULL_DECOMP':v223.uniq(best+m1+m12+m35+trend+lay+grade+rctx),
    }
    odds=v205.load_odds();oi=odds.set_index('race_code',drop=False);out=[]
    for mon in EVAL_MONTHS:
        first=pd.Timestamp(mon+'-01');nextm=first+pd.offsets.MonthBegin(1);tr=d[d._date<first];pair=v222.fit_pair(tr,'V221')
        base_te,_=v223.fit_head(d,list(basefs),vc,first,nextm);k=max(1,int((base_te._p>=.30).sum()))
        for name,fs in groups.items():
            te,nfeat=v223.fit_head(d,fs,vc,first,nextm);sel=te.nlargest(k,'_p');rv=[]
            for ix,r in sel.iterrows():
                if v223.ii(r.get('valid_result'))!=1 or v223.ii(r.get('course3'),3)!=3:continue
                act=v222.v166.combo(r.get('actual_combo'));actual='-'.join(map(str,act)) if len(act)==3 else '';code=str(r.get('race_code','')).zfill(12)
                if not actual or code not in oi.index:continue
                od=oi.loc[code];od=od.iloc[-1] if isinstance(od,pd.DataFrame) else od;ts=v222.order(r,pair,'V221');s=v222.settle(ts,od,actual)
                if s is None:continue
                rank=ts.index(actual)+1 if actual in ts else 0
                rv.append({'date':r._date.strftime('%Y-%m-%d'),'race_code':code,'y3':int(r._y),'rank':rank,'hit':s[0],'ret':s[1],'profit':s[2]})
            g=pd.DataFrame(rv)
            if g.empty:continue
            h=g[g.y3==1];cov=100*((h['rank']>0)&(h['rank']<=10)).mean() if len(h) else 0.;roi,md,rm1,rm3,rm5=v223.robust(g)
            out.append({'variant':name,'month':mon,'R':len(g),'head_rate':100*g.y3.mean(),'coverage10':cov,'hit10':100*g.hit.mean(),'roi':roi,'maxdd':md,'roi_rm1':rm1,'roi_rm3':rm3,'roi_rm5':rm5,'auc':v223.safe_auc(te._y.astype(int),te._p),'brier':float(brier_score_loss(te._y.astype(int),te._p)),'nfeat':nfeat})
    z=pd.DataFrame(out);z.to_csv(OUT,index=False)
    if z.empty or set(z.month)-set(EVAL_MONTHS):raise RuntimeError('bad output/contam')
    L=['# v224 national-form decomposition','', '- clean monthly prior-only 2025-12..2026-06; Jul/Aug excluded', '- v222 best base + v221 pair ranker fixed', '- historical odds settlement-only; fixed Top10 exact 10,000-yen Hamilton Dutch','', '|variant|R|3-head|cov10|hit|ROI|min month|prof months|rm5|AUC|Brier|features|','|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    agg=[]
    for v,g in z.groupby('variant'):
        R=int(g.R.sum());agg.append((v,R,np.average(g.head_rate,weights=g.R),np.average(g.coverage10,weights=np.maximum(g.R*g.head_rate/100,1e-9)),np.average(g.hit10,weights=g.R),np.average(g.roi,weights=g.R),g.roi.min(),int((g.roi>=100).sum()),np.average(g.roi_rm5,weights=g.R),g.auc.mean(),g.brier.mean(),int(g.nfeat.max())))
    agg.sort(key=lambda x:(-x[5],-x[8],-x[9]))
    for a in agg:L.append(f'|{a[0]}|{a[1]}|{a[2]:.2f}%|{a[3]:.2f}%|{a[4]:.2f}%|{a[5]:.2f}%|{a[6]:.2f}%|{a[7]}/7|{a[8]:.2f}%|{a[9]:.4f}|{a[10]:.5f}|{a[11]}|')
    L += ['','## Rule','- Decomposition audit only; no automatic production adoption.', '- Prefer replicated monthly and rm5 gains over one payout spike.']
    SUM.write_text('\n'.join(L)+'\n',encoding='utf-8');print('\n'.join(L))
if __name__=='__main__':main()
