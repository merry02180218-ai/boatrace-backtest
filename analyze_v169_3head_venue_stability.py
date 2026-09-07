#!/usr/bin/env python3
"""v169: corrected venue stability review for frozen 3-head production candidate.

Fixes v168 venue parsing: use the explicit `venue` field carried by frozen v108/v166 rows,
not the first two characters of race_code (which are year digits in this dataset).
Candidate remains frozen at p3>=0.30 and v166 top10. No threshold/ticket retuning.
"""
from __future__ import annotations
import csv
from analyze_v166_3head_pair_direct import read, ff, ii, combo, choose, score_month, SRC, HEADSRC, TEST_MONTHS

OUT='analysis_v169_3head_venue_stability.csv'
SUMMARY='summary_v169_3head_venue_stability.md'
CUT=.30; N=10

def vcode(r):
    v=str(r.get('venue','')).strip()
    try:return f'{int(float(v)):02d}'
    except:return v or 'NA'

def metric(rs):
    q=[r for r in rs if ff(r.get('p3head'))>=CUT]
    h=[r for r in q if combo(r.get('actual_combo'))[:1]==[3]]
    settled=[r for r in q if ii(r.get('valid_payout'))==1]
    wins=[r for r in settled if 0<ii(r.get('v166_rank20'))<=N]
    ret=sum(ff(r.get('payout100')) for r in wins); inv=len(settled)*N*100
    return dict(races=len(q),head3=len(h),head_rate=100*len(h)/len(q) if q else 0,hits=len(wins),hit_rate=100*len(wins)/len(q) if q else 0,coverage=100*sum(1 for r in h if 0<ii(r.get('v166_rank20'))<=N)/len(h) if h else 0,investment=inv,return_yen=ret,roi=100*ret/inv if inv else 0)

def main():
    src=read(SRC); hp={int(r['source_index']):ff(r.get('p3head')) for r in read(HEADSRC)}
    for i,r in enumerate(src):r['p3head']=hp.get(i,'')
    lam,_=choose(src); out=[]
    for mo in TEST_MONTHS:out+=score_month(src,mo,lam)
    keyp={(r['date'],r.get('race_code')):hp.get(i,'') for i,r in enumerate(src)}
    for r in out:r['p3head']=keyp.get((r['date'],r.get('race_code')),'')

    venues=sorted(set(vcode(r) for r in out if ff(r.get('p3head'))>=CUT))
    rows=[]
    for v in venues:
        x=metric([r for r in out if vcode(r)==v]); x['venue']=v; rows.append(x)
    fields=['venue','races','head3','head_rate','hits','hit_rate','coverage','investment','return_yen','roi']
    with open(OUT,'w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
    overall=metric(out); eligible=[r for r in rows if r['races']>=5]
    low70=[r for r in eligible if r['roi']<70]; profitable=[r for r in eligible if r['roi']>=100]
    L=['# v169 3号艇 corrected venue stability','', '- v168 bug fixed: venue is read from explicit `venue` field, matching v166 feature encoding.',f'- Frozen candidate unchanged: p3 >= {CUT:.2f}, v166 top {N}.','- No Jun-Aug retuning; payout settlement-only.','', '## Overall cross-check',f"- R {overall['races']}, ③頭率 {overall['head_rate']:.2f}%, hit {overall['hit_rate']:.2f}%, coverage {overall['coverage']:.2f}%, ROI {overall['roi']:.1f}%.",'','## Venue diagnostics','|venue|R|③頭率|hit|coverage|ROI|','|---|---:|---:|---:|---:|---:|']
    for r in rows:L.append(f"|{r['venue']}|{r['races']}|{r['head_rate']:.2f}%|{r['hit_rate']:.2f}%|{r['coverage']:.2f}%|{r['roi']:.1f}%|")
    L += ['','## Stability flags',f'- Venues represented: **{len(rows)}**.',f'- Venues with >=5 candidate races: **{len(eligible)}**.',f'- Among >=5R venues, ROI >=100%: **{len(profitable)}/{len(eligible)}**.',f'- Among >=5R venues, ROI <70%: **{len(low70)}/{len(eligible)}**.','', 'Do not exclude or select venues from these Jun-Aug diagnostics. This is a stability check for the already frozen candidate, not a venue optimization.']
    open(SUMMARY,'w',encoding='utf-8').write('\n'.join(L)+'\n'); print('\n'.join(L))
if __name__=='__main__':main()
