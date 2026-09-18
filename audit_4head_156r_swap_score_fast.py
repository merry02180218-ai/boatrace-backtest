#!/usr/bin/env python3
"""Focused fast exact156 swap search.
Keeps base120 fixed and selects exactly 36 additions by causal score only.
Search evaluation is NON-PRISTINE Apr-Aug retrospective. September absent.
"""
from pathlib import Path
import itertools,json,os,hashlib
import numpy as np,pandas as pd

OUT=Path('/tmp/head4_156r_swap_score_fast');OUT.mkdir(parents=True,exist_ok=True)
MONTHS=('2026-04','2026-05','2026-06','2026-07','2026-08')
DEV=('2026-04','2026-05','2026-06');SUP=('2026-07','2026-08')

def rankpct(x,rev=False):
    s=pd.Series(x)
    if rev:s=-s
    return s.rank(method='average',pct=True).to_numpy(float)

def main():
    p=os.environ['RACE_DETAIL_226']
    z=pd.read_csv(p,dtype={'race_code':str});z['race_code']=z.race_code.astype(str).str.zfill(12)
    if any(z.month.astype(str).str.startswith('2026-09')):raise RuntimeError('SEPTEMBER ACCESS')
    b77=z.is_old164.eq(1)&(((z.composite_odds>=7)&(z.opponent_mass>=.425))|((z.composite_odds<7)&(z.head_prob>=.22)&(z.opponent_mass>=.375)&(z.composite_odds>=3)))
    b120=b77|(z.is_old164.eq(1)&(~b77)&z.composite_odds.ge(2.5)&z.quality.ge(.82))
    if int(b120.sum())!=120:raise RuntimeError('base120 drift')
    cur=(~b120)&z.composite_odds.ge(3.5)&z.quality.ge(.75)&z.head_prob.ge(.16)&z.opponent_mass.ge(.30)&z.st4_adv_inside.ge(-.80)&z.orig4_adv_inside.ge(-.35)
    if int(cur.sum())!=36:raise RuntimeError('current36 drift')

    nb=z.loc[~b120].copy().reset_index(drop=False)
    if len(nb)!=88:raise RuntimeError(f'nonbase {len(nb)}')
    hp=rankpct(nb.head_prob);ma=rankpct(nb.opponent_mass);st=rankpct(nb.st4_adv_inside)
    og=rankpct(nb.orig4_adv_inside);mk=rankpct(np.log(np.maximum(nb.composite_odds.to_numpy(float),1e-9)),True)
    bal=rankpct(np.minimum(hp,ma))
    floor_profiles=[
      ('none',0,0,-99,-99,0),('a',.16,.20,-.50,-.35,1.5),('a60',.16,.20,-.60,-.35,1.5),
      ('a70',.16,.20,-.70,-.35,1.5),('a80',.16,.20,-.80,-.35,1.5),
      ('m25',.16,.25,-.80,-.35,1.5),('m30',.16,.30,-.80,-.35,1.5),
      ('c20',.16,.20,-.80,-.35,2.0),('c25',.16,.20,-.80,-.35,2.5),('c30',.16,.20,-.80,-.35,3.0),
      ('h12',.12,.20,-.80,-.35,1.5),('h20',.20,.20,-.80,-.35,1.5),('o25',.16,.20,-.80,-.25,1.5),
    ]
    base_idx=np.where(b120.to_numpy())[0]
    head=z.head4.to_numpy(int);hit=z.raw_hit.to_numpy(int);pay=z.payout_if_bet.to_numpy(float);mon=z.month.to_numpy(str)
    def met(sel):
        q=np.array(sorted(set(base_idx.tolist()+sel)),dtype=int)
        n=len(q);d={'R':n,'head4':int(head[q].sum()),'head4_rate':100*head[q].mean(),'exact3':int(hit[q].sum()),'ROI':100*pay[q].sum()/(10000*n)}
        ro=[]
        for m in MONTHS:
            x=q[mon[q]==m];r=100*pay[x].sum()/(10000*len(x));d[m+'_R']=len(x);d[m+'_ROI']=r;ro.append(r)
        d['monthly_floor_ROI']=min(ro)
        for nm,mons in [('dev',DEV),('support',SUP)]:
            mask=np.isin(mon[q],mons);x=q[mask]
            d[nm+'_R']=len(x);d[nm+'_head4']=int(head[x].sum());d[nm+'_head4_rate']=100*head[x].mean();d[nm+'_ROI']=100*pay[x].sum()/(10000*len(x))
        return d
    curm=met(z.index[cur].tolist())
    seen={}
    weights=list(itertools.product((1,1.5,2,2.5,3),(.5,1,1.5,2),(.5,1,1.5,2,3),(0,.5,1),(0,.25,.5,1),(0,.5,1)))
    for wh,wm,ws,wo,wk,wb in weights:
        score=wh*hp+wm*ma+ws*st+wo*og+wk*mk+wb*bal
        for name,hf,mf,sf,of,cf in floor_profiles:
            elig=(nb.head_prob.to_numpy()>=hf)&(nb.opponent_mass.to_numpy()>=mf)&(nb.st4_adv_inside.to_numpy()>=sf)&(nb.orig4_adv_inside.to_numpy()>=of)&(nb.composite_odds.to_numpy()>=cf)
            ix=np.where(elig)[0]
            if len(ix)<36:continue
            order=sorted(ix,key=lambda i:(-score[i],-float(nb.iloc[i].head_prob),-float(nb.iloc[i].opponent_mass),str(nb.iloc[i].race_code)))[:36]
            global_sel=nb.iloc[order]['index'].astype(int).tolist()
            codes=tuple(sorted(nb.iloc[order].race_code.tolist()));h=hashlib.sha256(';'.join(codes).encode()).hexdigest()[:16]
            if h in seen:continue
            seen[h]={'set_hash':h,'floor_profile':name,'w_hp':wh,'w_mass':wm,'w_st':ws,'w_orig':wo,'w_mkt':wk,'w_bal':wb,**met(global_sel),'codes':';'.join(codes)}
    g=pd.DataFrame(seen.values())
    roi=g[g.ROI>=curm['ROI']-1e-9].copy()
    def best(df):
        if len(df)==0:return None
        return df.sort_values(['head4_rate','ROI','monthly_floor_ROI','support_ROI'],ascending=[False,False,False,False]).iloc[0]
    buckets={}
    for floor in (80,85,90,curm['monthly_floor_ROI']):
        q=roi[roi.monthly_floor_ROI>=floor]
        b=best(q)
        buckets[str(floor)]={'count':len(q),'best':None if b is None else b.drop(labels=['codes']).to_dict()}
    q90=roi[roi.monthly_floor_ROI>=90];b90=best(q90)
    swaps={}
    if b90 is not None:
        cc=set(g.loc[g.set_hash.eq(b90.set_hash),'codes'].iloc[0].split(';'));aa=set(z.loc[cur,'race_code'])
        cols=['date','month','race_code','head4','raw_hit','payout_if_bet','head_prob','opponent_mass','composite_odds','st4_adv_inside','orig4_adv_inside']
        swaps['removed_from_current']=z[z.race_code.isin(sorted(aa-cc))][cols].to_dict('records')
        swaps['added_vs_current']=z[z.race_code.isin(sorted(cc-aa))][cols].to_dict('records')
    g.drop(columns=['codes']).to_csv(OUT/'unique_sets.csv',index=False)
    res={'current156':curm,'unique_sets':len(g),'roi_preserving':len(roi),'best_roi_only':None if best(roi) is None else best(roi).drop(labels=['codes']).to_dict(),'floor_buckets':buckets,'floor90_swaps':swaps,'SEPTEMBER_OUTCOMES_READ':False,'PRODUCTION_CHANGED':False,'AUDIT_OK':True}
    (OUT/'result.json').write_text(json.dumps(res,ensure_ascii=False,indent=2,default=str)+'\n',encoding='utf-8')
    print(json.dumps(res,ensure_ascii=False,indent=2,default=str));print('HEAD4_156R_SWAP_SCORE_FAST_OK');print('SEPTEMBER_UNREAD')
if __name__=='__main__':main()
