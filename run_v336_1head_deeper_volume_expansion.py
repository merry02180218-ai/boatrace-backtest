#!/usr/bin/env python3
from pathlib import Path
import json
import pandas as pd
import run_v332_1head_attack_first_redesign as v332

OUT=Path('/tmp/v336'); OUT.mkdir(parents=True,exist_ok=True)
QS=[0.65,0.50,0.45,0.40,0.35,0.30,0.25]
MONTHS=v332.MONTHS_DEV+[v332.AUG]

def pct(n,d): return 100*n/d if d else float('nan')
def met(z):
    n=len(z); h=int(z.head_hit.sum()) if n else 0; e=int(z.hit.sum()) if n else 0
    return dict(R=n,head=h,head_rate=pct(h,n),exact3=e,exact3_rate=pct(e,n))

def eval_q(y,q):
    cfg={'family':'ATTACK_ENV_SOFT','env_w':0.1,'q':q}
    selected=[]; monthly=[]
    for m in MONTHS:
        if m==v332.AUG:
            tr=y[y.month.isin(v332.MONTHS_DEV)].copy()
        else:
            tr=y[y.month.isin([x for x in v332.MONTHS_DEV if x!=m])].copy()
        z=y[y.month.eq(m)].copy(); p,_=v332.fit_apply(tr,z,cfg)
        p=p.copy(); p['eval_month']=m; selected.append(p)
        b=met(z); pm=met(p)
        monthly.append({'q':q,'month':m,**{f'base_{k}':v for k,v in b.items()},**{f'pass_{k}':v for k,v in pm.items()},
                        'pass_fraction_pct':pct(len(p),len(z)),
                        'head_lift_pp':pm['head_rate']-b['head_rate'],
                        'exact3_lift_pp':pm['exact3_rate']-b['exact3_rate']})
    s=pd.concat(selected,ignore_index=True)
    b=met(y); pm=met(s)
    return s,monthly,{'q':q,**pm,'races_per_month':len(s)/7.0,'pass_fraction_pct':pct(len(s),len(y)),
                      'base_head_rate':b['head_rate'],'base_exact3_rate':b['exact3_rate'],
                      'head_lift_pp':pm['head_rate']-b['head_rate'],'exact3_lift_pp':pm['exact3_rate']-b['exact3_rate']}

def main():
    y=v332.load_all().copy(); results={}; monthly=[]; summary=[]
    for q in QS:
        s,m,sm=eval_q(y,q); results[q]=s; monthly.extend(m); summary.append(sm)
    r65=results[0.65]; r50=results[0.50]
    assert (len(r65),int(r65.head_hit.sum()),int(r65.hit.sum()))==(96,83,45)
    assert (len(r50),int(r50.head_hit.sum()),int(r50.hit.sum()))==(138,120,62)
    bands=[]
    refcodes=set(r65.race_code.astype(str))
    for q in QS[1:]:
        s=results[q]; add=s[~s.race_code.astype(str).isin(refcodes)].copy(); mm=met(add)
        bands.append({'kind':'vs_q65','q':q,'added_R':mm['R'],'head_rate':mm['head_rate'],'exact3_rate':mm['exact3_rate']})
    for prev,q in zip(QS[:-1],QS[1:]):
        prevcodes=set(results[prev].race_code.astype(str)); add=results[q][~results[q].race_code.astype(str).isin(prevcodes)].copy(); mm=met(add)
        bands.append({'kind':f'vs_q{prev:.2f}','q':q,'added_R':mm['R'],'head_rate':mm['head_rate'],'exact3_rate':mm['exact3_rate']})
    mdf=pd.DataFrame(monthly)
    monthly_flags=[]
    for q in QS:
        z=mdf[mdf.q.eq(q)]
        monthly_flags.append({'q':q,'min_month_head_rate':float(z.pass_head_rate.min()),'min_month_exact3_rate':float(z.pass_exact3_rate.min()),
                              'months_head_below70':int((z.pass_head_rate<70).sum()),'months_exact3_below30':int((z.pass_exact3_rate<30).sum())})
    pd.DataFrame(summary).to_csv(OUT/'analysis_v336_summary.csv',index=False)
    mdf.to_csv(OUT/'analysis_v336_monthly.csv',index=False)
    pd.DataFrame(bands).to_csv(OUT/'analysis_v336_added_bands.csv',index=False)
    pd.DataFrame(monthly_flags).to_csv(OUT/'analysis_v336_monthly_flags.csv',index=False)
    (OUT/'result_v336.json').write_text(json.dumps({'summary':summary,'bands':bands,'monthly_flags':monthly_flags,'SEPTEMBER_OUTCOMES_READ':False},indent=2),encoding='utf-8')
    lines=['# v336 deeper volume expansion audit','']
    for r in summary:
        lines.append(f"- q={r['q']:.2f}: PASS {r['R']} ({r['races_per_month']:.1f}/month), head {r['head']}/{r['R']}={r['head_rate']:.2f}%, exact3 {r['exact3']}/{r['R']}={r['exact3_rate']:.2f}%, lifts head {r['head_lift_pp']:+.2f}pp exact3 {r['exact3_lift_pp']:+.2f}pp")
    lines.append('')
    for r in bands:
        if r['kind']!='vs_q65':
            lines.append(f"- {r['kind']} -> q={r['q']:.2f}: +{r['added_R']}R, head {r['head_rate']:.2f}%, exact3 {r['exact3_rate']:.2f}%")
    lines += ['', '- September outcomes unread.']
    (OUT/'summary_v336.md').write_text('\n'.join(lines)+'\n',encoding='utf-8'); print('\n'.join(lines))
if __name__=='__main__': main()
