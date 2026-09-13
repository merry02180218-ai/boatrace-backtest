#!/usr/bin/env python3
from pathlib import Path
import json
import pandas as pd
import run_v332_1head_attack_first_redesign as v332

OUT=Path('/tmp/v335'); OUT.mkdir(parents=True,exist_ok=True)
QS=[0.65,0.60,0.55,0.50,0.45]
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
        p=p.copy(); p['eval_month']=m
        selected.append(p)
        b=met(z); pm=met(p)
        monthly.append({'q':q,'month':m,**{f'base_{k}':v for k,v in b.items()},**{f'pass_{k}':v for k,v in pm.items()},
                        'pass_fraction_pct':pct(len(p),len(z)),
                        'head_lift_pp':pm['head_rate']-b['head_rate'],
                        'exact3_lift_pp':pm['exact3_rate']-b['exact3_rate']})
    s=pd.concat(selected,ignore_index=True)
    b=met(y); pm=met(s)
    return s, monthly, {'q':q,**pm,'races_per_month':len(s)/7.0,'pass_fraction_pct':pct(len(s),len(y)),
                         'base_head_rate':b['head_rate'],'base_exact3_rate':b['exact3_rate'],
                         'head_lift_pp':pm['head_rate']-b['head_rate'],'exact3_lift_pp':pm['exact3_rate']-b['exact3_rate']}

def main():
    y=v332.load_all().copy()
    results={}; monthly=[]; summary=[]
    for q in QS:
        s,m,sm=eval_q(y,q); results[q]=s; monthly.extend(m); summary.append(sm)
    ref=results[0.65]
    if len(ref)!=96 or int(ref.head_hit.sum())!=83 or int(ref.hit.sum())!=45:
        raise AssertionError(f'q=.65 identity drift R={len(ref)} head={int(ref.head_hit.sum())} exact3={int(ref.hit.sum())}')
    refcodes=set(ref.race_code.astype(str))
    bands=[]
    for q in QS[1:]:
        s=results[q]; added=s[~s.race_code.astype(str).isin(refcodes)].copy(); mm=met(added)
        bands.append({'q':q,'added_vs_q65_R':mm['R'],'added_head':mm['head'],'added_head_rate':mm['head_rate'],
                      'added_exact3':mm['exact3'],'added_exact3_rate':mm['exact3_rate']})
    pd.DataFrame(summary).to_csv(OUT/'analysis_v335_summary.csv',index=False)
    pd.DataFrame(monthly).to_csv(OUT/'analysis_v335_monthly.csv',index=False)
    pd.DataFrame(bands).to_csv(OUT/'analysis_v335_added_band.csv',index=False)
    result={'summary':summary,'added_bands':bands,'SEPTEMBER_OUTCOMES_READ':False}
    (OUT/'result_v335.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    lines=['# v335 v332 volume expansion audit','']
    for r in summary:
        lines.append(f"- q={r['q']:.2f}: PASS {r['R']} ({r['races_per_month']:.1f}/month), head {r['head']}/{r['R']}={r['head_rate']:.2f}%, exact3 {r['exact3']}/{r['R']}={r['exact3_rate']:.2f}%, lifts head {r['head_lift_pp']:+.2f}pp exact3 {r['exact3_lift_pp']:+.2f}pp")
    lines.append('')
    for r in bands:
        lines.append(f"- newly admitted at q={r['q']:.2f} vs q=.65: {r['added_vs_q65_R']}R, head {r['added_head_rate']:.2f}%, exact3 {r['added_exact3_rate']:.2f}%")
    lines += ['', '- September outcomes unread.']
    (OUT/'summary_v335.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print('\n'.join(lines))
if __name__=='__main__': main()
