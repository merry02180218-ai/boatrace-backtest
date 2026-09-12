#!/usr/bin/env python3
"""v302: ablate 3-head/4-head transferred feature families on top of v300 winner.

Development-only. Jul/Aug remain NON-PRISTINE; September outcomes unread.
Evaluation denominator stays frozen to the same 204 races and ticket policy stays
TOP2XTOP2 alpha=.60.  Unlike v301's all-at-once transfer, v302 adds one semantic
feature family at a time on top of the v300 winning model (SECOND L2=3, THIRD L2=.1),
then tests only combinations of individually non-harmful families.
"""
from __future__ import annotations
from pathlib import Path
import itertools
import numpy as np
import pandas as pd
from scipy.special import logsumexp

import analyze_v298_1head_threat_listwise_trifecta5 as v298
import run_v298_1head_v288v283_audited as fastbase
import run_v300_1head_trifecta3_feature_upgrade as v300
import run_v301_1head_trifecta3_transfer_3head4head_features as v301

ROOT=Path(__file__).resolve().parent
PREFIX=ROOT/'analysis_v302_1head_trifecta3_feature_ablation'
SUMMARY=ROOT/'summary_v302_1head_trifecta3_feature_ablation.md'
TM=list(v298.TEST_MONTHS)
SECOND_L2=3.0
THIRD_L2=.1

FAMILIES=('ST_EDGE','WALL','MOTOR','STMOTOR','TURN_FORM')


def family_of(c):
    x=c.lower()
    if 'v300_v301_' not in x:return None
    if 'stmotor' in x:return 'STMOTOR'
    if any(t in x for t in ('wall_adv','minus_inner','minus_outer')):return 'WALL'
    if 'motor' in x:return 'MOTOR'
    if any(t in x for t in ('turn','foot','mawari','exh','tenji','pl_','local','grade','racer','past','win','wr')):return 'TURN_FORM'
    if any(t in x for t in ('nst','st_','start','waku_st','hist_st')):return 'ST_EDGE'
    return None


def features_for(df, allowed):
    meta={'date','month','race_code','y2','actual2','actual3','boat','group_id','second_boat','third_boat','train_group','ycond'}
    fs=[]
    for c in df.columns:
        if c in meta:continue
        fam=family_of(c)
        if fam is not None and fam not in allowed:continue
        x=pd.to_numeric(df[c],errors='coerce')
        if x.notna().mean()>=.55 and x.nunique(dropna=True)>=2:fs.append(c)
    return fs


def p2_predict(sl,tm,allowed):
    tr=sl[sl.month<tm].copy();te=sl[sl.month==tm].copy();fs=features_for(tr,allowed)
    m=fastbase.FastSecond(SECOND_L2).fit(tr,fs,'y2');te['score']=m.score(te)
    out={}
    for code,g in te.groupby('race_code'):out[str(code).zfill(12)]=v298.v279.probs_within_race(g,'score')
    return out,len(fs)


def pc_predict(cl,tm,allowed):
    tr=cl[(cl.month<tm)&(cl.train_group==1)].copy();te=cl[cl.month==tm].copy();fs=features_for(tr,allowed)
    m=fastbase.FastConditional(THIRD_L2).fit(tr,fs);te['score']=m.score(te)
    out={}
    for code,g in te.groupby('race_code'):
        pc={}
        for s,gs in g.groupby('second_boat'):
            a=gs.score.to_numpy(float);pp=np.exp(a-logsumexp(a))
            for t,p in zip(gs.third_boat.astype(int),pp):pc[(int(s),int(t))]=float(p)
        out[str(code).zfill(12)]=pc
    return out,len(fs)


def prepare():
    v300.setup_v298()
    d,_=v298.v294.freeze_true_pre();d=v298.v294.add_prior_history(d);d=v298.v294.add_rel(d);d,threat=v298.add_threat(d)
    fams=v298.v296.clean_manifest(d)
    print('v302 PRE features frozen; audited settlement now',flush=True)
    d,cov=v298.v297.settle_full_after_freeze(d);d=d[(d.valid_result==1)&(d.combo_valid==1)].copy()
    sufs=v298.suffixes(d)
    sl=v301.augment_second(v298.second_long(d,sufs))
    cl=v301.augment_third(v298.conditional_long(d,sufs))
    return d,fams,threat,sl,cl


def head_frame(d,fams,threat,tm):
    tr=d[d.month<tm].copy();te=d[d.month==tm].copy()
    core0=list(dict.fromkeys(fams['CLEAN_STATIC6_PLAYER']+threat))
    guard0=[c for c in core0 if c.startswith(('b1_','b2_','b3_','b4_','rel_','attack23_','v298_'))]
    core=v298.v293.available(tr,core0,.55);guard=v298.v293.available(tr,guard0,.55)
    ph,pg,hc,gc,noh,nog=v298.head_fold(tr,te,core,guard)
    z=te[['date','month','race_code','venue','race','head_hit','actual_combo','combo_valid']].copy();z['test_month']=tm;z['p_head_hgb']=ph
    for q,c in hc.items():z[f'hgb_q{q}_sel']=(ph>=c).astype(int)
    return z


def eval_configs(d,fams,threat,sl,cl,configs):
    pred=[];folds=[]
    for tm in TM:
        z=head_frame(d,fams,threat,tm);feat={}
        for name,allowed in configs:
            p2,n2=p2_predict(sl,tm,allowed);pc,n3=pc_predict(cl,tm,allowed);feat[name]=(n2,n3)
            vals=[];masses=[]
            for _,r in z.iterrows():
                code=str(r.race_code).zfill(12)
                vals.append(v300.ticket3(p2[code],pc[code]))
                if name=='V300':masses.append(v300.base5(p2[code],pc[code])[1])
            z[f'top3_{name}']=vals
            z[f'hit3_{name}']=[int(bool(a) and a in t.split(';')) for a,t in zip(z.actual_combo,vals)]
            if name=='V300':z['base_top5_mass']=masses
        z['base_selected']=((z['hgb_q0.95_sel']==1)&(z.base_top5_mass>=v300.BASE_CONF)).astype(int)
        pred.append(z);folds.append({'month':tm,**{f'{n}_sfeat':feat[n][0] for n,_ in configs},**{f'{n}_tfeat':feat[n][1] for n,_ in configs}})
        print('v302 fold',tm,'done',flush=True)
    p=pd.concat(pred,ignore_index=True);s=p[p.base_selected==1].copy();rows=[];monthly=[]
    for name,allowed in configs:
        col=f'hit3_{name}';gm=s.groupby('test_month')[col].agg(['size','sum','mean'])
        rows.append({'config':name,'families':'+'.join(sorted(allowed)) if allowed else 'none','R':len(s),'hits':int(s[col].sum()),'hit_rate':float(s[col].mean()),'worst_month':float(gm['mean'].min())})
        for mo,r in gm.iterrows():monthly.append({'config':name,'month':mo,'R':int(r['size']),'hits':int(r['sum']),'hit_rate':float(r['mean'])})
    return p,s,pd.DataFrame(rows),pd.DataFrame(monthly),pd.DataFrame(folds)


def main():
    d,fams,threat,sl,cl=prepare()
    singles=[('V300',set())]+[(f'ONLY_{f}',{f}) for f in FAMILIES]
    p1,s1,r1,m1,f1=eval_configs(d,fams,threat,sl,cl,singles)
    base=float(r1.loc[r1.config=='V300','hit_rate'].iloc[0])
    keep=[f for f in FAMILIES if float(r1.loc[r1.config==f'ONLY_{f}','hit_rate'].iloc[0])>=base]
    combos=[]
    for k in (2,3):
        for xs in itertools.combinations(keep,k):combos.append(('COMBO_'+'_'.join(xs),set(xs)))
    configs=singles+combos
    if combos:
        p,s,r,m,folds=eval_configs(d,fams,threat,sl,cl,configs)
    else:p,s,r,m,folds=p1,s1,r1,m1,f1
    r['delta']=r.hit_rate-float(r.loc[r.config=='V300','hit_rate'].iloc[0])
    best=r.sort_values(['hit_rate','worst_month','hits'],ascending=False).iloc[0]
    p.to_csv(str(PREFIX)+'_pred.csv',index=False);r.to_csv(str(PREFIX)+'_configs.csv',index=False);m.to_csv(str(PREFIX)+'_monthly.csv',index=False);folds.to_csv(str(PREFIX)+'_folds.csv',index=False)
    L=['# v302 1HEAD 3-ticket transferred-feature ablation','', '- Development research only; production unchanged.','- Jul/Aug NON-PRISTINE; September outcomes unread.','- Same frozen 204-race denominator and TOP2XTOP2 alpha=.60 policy.','- Baseline is v300 winning regularization: SECOND L2=3, THIRD L2=.1.','', '## Results','|config|families|R|hits|hit rate|delta|worst month|','|---|---|---:|---:|---:|---:|---:|']
    for _,x in r.sort_values(['hit_rate','worst_month'],ascending=False).iterrows():L.append(f"|{x.config}|{x.families}|{int(x.R)}|{int(x.hits)}|{100*x.hit_rate:.2f}%|{100*x.delta:+.2f}pt|{100*x.worst_month:.2f}%|")
    L+=['','## Individually non-harmful families', '- '+(', '.join(keep) if keep else 'none'),'','## Best monthly audit','|month|R|hits|hit rate|','|---|---:|---:|---:|']
    for _,x in m[m.config==best.config].iterrows():L.append(f"|{x.month}|{int(x.R)}|{int(x.hits)}|{100*x.hit_rate:.2f}%|")
    L+=['','## Decision',f"- Best: **{best.config} = {100*best.hit_rate:.2f}% ({int(best.hits)}/{int(best.R)})**, delta vs v300 {100*best.delta:+.2f}pt.",'- Only individually non-harmful transferred families were eligible for combination search.','- Feb-Jun are reused development evidence; freeze any winner before prospective validation.']
    txt='\n'.join(L)+'\n';SUMMARY.write_text(txt,encoding='utf-8');print(txt,flush=True)

if __name__=='__main__':main()
