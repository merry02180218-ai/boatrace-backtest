#!/usr/bin/env python3
"""Research a production-feasible S-only volume rescue using frozen head scores.

Only frozen S races that current N4/composite>=7 BASE passes are considered.
Rules use PRE/POST/ENV_ENTRY strength + frozen v283 ticket prefix + odds only.
No A_SCORE is required, so a passing rule can be operational once frozen
S downstream artifacts and official pre-deadline odds capture pass audit.

Jul/Aug/Sep outcomes are not used. v96 is not used. BASE bets are immutable.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parent
ALLN=ROOT/'analysis_v288_4head_composite_odds_alln_detail.csv'
HEAD=ROOT/'analysis_v271_4head_arank_races.csv'
OUT=ROOT/'analysis_4head_v291_s_strength_rescue_grid.csv'
MONTH=ROOT/'analysis_4head_v291_s_strength_rescue_monthly.csv'
LOMO=ROOT/'analysis_4head_v291_s_strength_rescue_lomo.csv'
SUM=ROOT/'summary_4head_v291_s_strength_rescue.md'
CAND=ROOT/'head4_v291_s_strength_rescue_candidate.json'
MONTHS=('2026-04','2026-05','2026-06');BANK=10000
FLOORS=(4.5,5.0,5.5,6.0,6.5,7.0);NS=(2,3,4,5,6,8,10)


def met(g):
    if len(g)==0:return {'R':0,'return_yen':0.,'profit_yen':0.,'roi_pct':np.nan,'head_rate_pct':np.nan,'hit_rate_pct':np.nan}
    ret=float(g.return_yen.sum());cost=len(g)*BANK
    return {'R':len(g),'return_yen':ret,'profit_yen':ret-cost,'roi_pct':100*ret/cost,
            'head_rate_pct':100*float(g.head4_win.mean()),'hit_rate_pct':100*float(g.hit.mean())}


def load():
    q=pd.read_csv(ALLN,dtype={'race_code':str});q['race_code']=q.race_code.astype(str).str.zfill(12)
    if set(q.month.astype(str).unique())!=set(MONTHS) or q.race_code.nunique()!=100 or len(q)!=1900:raise RuntimeError('bad all-N source')
    h=pd.read_csv(HEAD,dtype={'race_code':str});h['race_code']=h.race_code.astype(str).str.zfill(12)
    h=h[h.month.isin(MONTHS)].copy();is_s=h.is_S.astype(str).str.lower().isin(('true','1'))
    h=h[is_s][['month','race_code','PRE','POST','ENV_ENTRY']].copy()
    for c in ('PRE','POST','ENV_ENTRY'):h[c]=pd.to_numeric(h[c],errors='coerce')
    h=h.drop_duplicates('race_code')
    h['min_ratio']=np.minimum.reduce([h.PRE/.28,h.POST/.25,h.ENV_ENTRY/.224790])
    h['geom_ratio']=((h.PRE/.28)*(h.POST/.25)*(h.ENV_ENTRY/.224790)).clip(lower=0)**(1/3)
    z=q[q.layer=='S'].merge(h,on=['month','race_code'],how='inner',validate='many_to_one')
    if z.race_code.nunique()!=q[q.layer=='S'].race_code.nunique():raise RuntimeError('S score join coverage mismatch')
    return q,z


def base(z,months=MONTHS):return z[(z.month.isin(months))&(z.n==4)&(z.comp_odds>=7)].copy()

def rescue_u(z,months=MONTHS):
    b=set(base(z,months).race_code);return z[(z.month.isin(months))&(~z.race_code.isin(b))].copy()


def defs():
    gates=[]
    for x in (1.0,1.10,1.20,1.30,1.40,1.50):gates.append(('MIN_RATIO',x))
    for x in (1.0,1.10,1.20,1.30,1.40,1.50):gates.append(('GEOM_RATIO',x))
    for x in (.30,.33,.36,.39,.42):gates.append(('PRE',x))
    for x in (.28,.30,.33,.36,.40):gates.append(('POST',x))
    for x in (.25,.28,.31,.34,.37):gates.append(('ENV',x))
    return [(g,x,n,f) for g,x in gates for n in NS for f in FLOORS]


def select(u,gate,thr,n,floor):
    x=u[u.n==int(n)]
    if gate=='MIN_RATIO':x=x[x.min_ratio>=thr]
    elif gate=='GEOM_RATIO':x=x[x.geom_ratio>=thr]
    elif gate=='PRE':x=x[x.PRE>=thr]
    elif gate=='POST':x=x[x.POST>=thr]
    elif gate=='ENV':x=x[x.ENV_ENTRY>=thr]
    else:raise ValueError(gate)
    x=x[x.comp_odds>=floor].copy()
    if x.race_code.duplicated().any():raise RuntimeError('duplicate rescue')
    return x


def evaluate(z,gate,thr,n,floor,months=MONTHS):
    b=base(z,months);u=rescue_u(z,months);r=select(u,gate,thr,n,floor);c=pd.concat([b,r],ignore_index=True)
    ba,ra,ca=met(b),met(r),met(c);mrs=[]
    for m in months:
        bm,rm,cm=b[b.month==m],r[r.month==m],c[c.month==m];xb,xr,xc=met(bm),met(rm),met(cm)
        mrs.append({'gate':gate,'threshold':thr,'n':n,'floor':floor,'month':m,'base_R':xb['R'],'base_roi_pct':xb['roi_pct'],
                    'added_R':xr['R'],'added_return_yen':xr['return_yen'],'added_profit_yen':xr['profit_yen'],'added_roi_pct':xr['roi_pct'],
                    'R':xc['R'],'return_yen':xc['return_yen'],'profit_yen':xc['profit_yen'],'roi_pct':xc['roi_pct']})
    md=pd.DataFrame(mrs);valid=md[md.added_R>0]
    return {'gate':gate,'threshold':float(thr),'n':int(n),'floor':float(floor),'base_R':ba['R'],'base_roi_pct':ba['roi_pct'],
            'added_R':ra['R'],'added_roi_pct':ra['roi_pct'],'added_profit_yen':ra['profit_yen'],'R':ca['R'],'roi_pct':ca['roi_pct'],
            'profit_yen':ca['profit_yen'],'head_rate_pct':ca['head_rate_pct'],'hit_rate_pct':ca['hit_rate_pct'],
            'min_added_month_R':int(md.added_R.min()),'min_added_month_roi_pct':float(valid.added_roi_pct.min()) if len(valid) else np.nan,
            'min_combined_month_roi_pct':float(md.roi_pct.min())},mrs


def choose(t):
    common=(t.added_R>=9)&(t.min_added_month_R>=2)
    tiers=[('STRONG',common&(t.added_roi_pct>=140)&(t.min_added_month_roi_pct>=120)&(t.min_combined_month_roi_pct>=130)),
           ('SAFE',common&(t.added_roi_pct>=125)&(t.min_added_month_roi_pct>=110)&(t.min_combined_month_roi_pct>=120)),
           ('POSITIVE',common&(t.added_roi_pct>=115)&(t.min_added_month_roi_pct>=100)&(t.min_combined_month_roi_pct>=110))]
    for name,mask in tiers:
        z=t[mask].sort_values(['R','min_added_month_roi_pct','added_roi_pct'],ascending=False)
        if len(z):return name,z.iloc[0]
    return 'NO_SAFE_CANDIDATE',None


def lomo(z,D):
    out=[]
    for hold in MONTHS:
        train=tuple(m for m in MONTHS if m!=hold);rec=[evaluate(z,g,t,n,f,train)[0] for g,t,n,f in D]
        tier,ch=choose(pd.DataFrame(rec))
        if ch is None:out.append({'holdout_month':hold,'status':'NO_TRAIN_CANDIDATE'});continue
        s,_=evaluate(z,str(ch.gate),float(ch.threshold),int(ch.n),float(ch.floor),(hold,))
        out.append({'holdout_month':hold,'status':'OK','train_tier':tier,'gate':ch.gate,'threshold':float(ch.threshold),
                    'n':int(ch.n),'floor':float(ch.floor),'hold_added_R':int(s['added_R']),
                    'hold_added_roi_pct':float(s['added_roi_pct']) if pd.notna(s['added_roi_pct']) else np.nan,'hold_R':int(s['R']),'hold_roi_pct':float(s['roi_pct'])})
    return pd.DataFrame(out)


def main():
    _,z=load();D=defs();rs=[];ms=[]
    for g,t,n,f in D:
        s,m=evaluate(z,g,t,n,f);rs.append(s);ms.extend(m)
    A=pd.DataFrame(rs);M=pd.DataFrame(ms);tier,ch=choose(A);L=lomo(z,D)
    A.to_csv(OUT,index=False);M.to_csv(MONTH,index=False);L.to_csv(LOMO,index=False)
    b=met(base(z));payload={'schema':'head4_v291_s_strength_rescue_v1','jul_aug_outcomes_used':False,'september_outcomes_used':False,'v96_used':False,
      'base':{'policy':'HEAD4_V291_COMP7_S','R':b['R'],'immutable':True},'selection_tier':tier}
    lines=['# HEAD4 v291 S-layer head-strength rescue','',
      '- Universe is frozen S only; no A_SCORE is used.',
      '- BASE N4/composite>=7 bets are immutable; only BASE PASS races can be rescued.',
      '- Gates use PRE/POST/ENV_ENTRY already required by LIVE S inference + v283 prefix odds.',
      '- Jul/Aug/Sep outcomes excluded; no v96.','',f'- S BASE: **{b["R"]}R / ROI {b["roi_pct"]:.2f}%**.','',f'## Selection: {tier}']
    if ch is not None:
        payload['candidate']={'gate':str(ch.gate),'threshold':float(ch.threshold),'n':int(ch.n),'floor':float(ch.floor),
                              'added_R':int(ch.added_R),'added_roi_pct':float(ch.added_roi_pct),'combined_R':int(ch.R),
                              'combined_roi_pct':float(ch.roi_pct),'min_added_month_roi_pct':float(ch.min_added_month_roi_pct),
                              'min_combined_month_roi_pct':float(ch.min_combined_month_roi_pct),'status':'RESEARCH_CANDIDATE_NOT_FROZEN'}
        lines += ['',f'- Rule: **{ch.gate} >= {ch.threshold:.3f}, N={int(ch.n)}, composite>={ch.floor:.1f}**',
          f'- rescue standalone: **{int(ch.added_R)}R / ROI {ch.added_roi_pct:.2f}% / monthly floor {ch.min_added_month_roi_pct:.2f}%**',
          f'- combined S: **{int(ch.R)}R / ROI {ch.roi_pct:.2f}% / monthly floor {ch.min_combined_month_roi_pct:.2f}%**','',
          '|month|added R|added ROI|combined R|combined ROI|','|---|---:|---:|---:|---:|']
        mm=M[(M.gate==ch.gate)&(M.threshold==ch.threshold)&(M.n==ch.n)&(M.floor==ch.floor)].sort_values('month')
        for _,r in mm.iterrows():lines.append(f'|{r.month}|{int(r.added_R)}|{r.added_roi_pct:.2f}%|{int(r.R)}|{r.roi_pct:.2f}%|')
    lines += ['','## LOMO','','|holdout|train rule|added R|added ROI|combined ROI|','|---|---|---:|---:|---:|']
    for _,r in L.iterrows():
        if r.status!='OK':lines.append(f'|{r.holdout_month}|NO_TRAIN_CANDIDATE|-|-|-|')
        else:lines.append(f'|{r.holdout_month}|{r.gate} {r.threshold:.3f} N{int(r.n)} f{r.floor:.1f}|{int(r.hold_added_R)}|{r.hold_added_roi_pct:.2f}%|{r.hold_roi_pct:.2f}%|')
    ok=bool(len(L)==3 and L.status.eq('OK').all() and (L.hold_added_R>=1).all() and (L.hold_added_roi_pct>=100).all())
    payload['lomo_all_holdout_rescue_profitable']=ok
    lines += ['',f'- all held-out rescue profitable: **{"YES" if ok else "NO"}**','',
      '## Production gate','- Promotion requires safe fixed rule + all held-out LOMO rescue ROI >=100%.',
      '- If promoted, assign a new policy version and require frozen downstream parity + official pre-deadline odds audit before any formal OOS bet.']
    CAND.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    SUM.write_text('\n'.join(lines)+'\n',encoding='utf-8');print('\n'.join(lines))

if __name__=='__main__':main()
