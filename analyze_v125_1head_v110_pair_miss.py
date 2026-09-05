"""v125: diagnose v110 fixed7 opponent-pair misses without tuning Sep outcomes.

Goal
- Keep v109 head gate unchanged.
- Keep v110 lambda=.50 as baseline.
- Understand whether misses are caused by role omission or pair/order construction.
- Mar-Aug historical diagnostic + frozen Sep1-4 confirmation are reported separately.
- No odds are used for selection/ranking.
"""
# trigger: 2026-09-05 rerun
import csv
from collections import Counter

HIST='analysis_v110_1head_role_tickets.csv'
SEP='replay_v124_20260901_04_v123_frozen.csv'
OUT='summary_v125_1head_v110_pair_miss.md'

def read(path):
    with open(path,encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def F(r,k,d=0):
    try:return float(r.get(k,d))
    except:return d
def I(r,k,d=0):
    try:return int(float(r.get(k,d)))
    except:return d
def pct(a,b):return 100*a/b if b else 0

def order7_hist(r):
    s=r.get('order_l50','')
    return [x for x in s.split(';') if x][:7]
def order7_sep(r):
    s=r.get('top7','')
    return [x for x in s.split(';') if x][:7]

def diag(rs, orderfn, pcol, label):
    s=[r for r in rs if F(r,pcol)>=.72]
    head=[r for r in s if I(r,'head_hit')==1]
    miss=[]; c=Counter()
    for r in head:
        act=(r.get('actual_combo') or '').strip()
        if not act:continue
        t=orderfn(r)
        if act in t:continue
        a=act.split('-')
        if len(a)!=3:continue
        secs={x.split('-')[1] for x in t if len(x.split('-'))==3}
        thirds={x.split('-')[2] for x in t if len(x.split('-'))==3}
        s2=a[1] in secs;s3=a[2] in thirds
        if s2 and s3:c['both_roles_present_wrong_pair']+=1
        elif not s2 and not s3:c['both_roles_missing']+=1
        elif not s2:c['second_role_missing']+=1
        else:c['third_role_missing']+=1
        miss.append(r)
    return label,len(s),len(head),len(miss),c

def main():
    hist=read(HIST); sep=read(SEP)
    blocks=[diag(hist,order7_hist,'p109','Jun-Aug v110 holdout'),diag(sep,order7_sep,'p109','Sep1-4 frozen PRE sample')]
    L=['# v125 v110 fixed7 opponent-pair miss diagnostics','',
       '- v109 head gate remains **p109>=72%**.','- v110 baseline remains **lambda=.50 / fixed top7**.',
       '- This step is diagnostic only: no Sep result is used to tune a new ranking rule.','',
       '|period|S races|①head hits|head-hit fixed7 misses|miss rate among head hits|','|---|---:|---:|---:|---:|']
    for lab,n,h,m,c in blocks:L.append(f'|{lab}|{n}|{h}|{m}|{pct(m,h):.1f}%|')
    L+=['','## Miss decomposition','|period|both roles present / wrong pair|2nd role missing|3rd role missing|both roles missing|','|---|---:|---:|---:|---:|']
    for lab,n,h,m,c in blocks:
        L.append(f"|{lab}|{c['both_roles_present_wrong_pair']}|{c['second_role_missing']}|{c['third_role_missing']}|{c['both_roles_missing']}|")
    L+=['','## Next-step rule','- Do **not** change v109 or add another head filter from this analysis.',
        '- If pair/order misses dominate, next validation should change only the 20-combination pair scoring / top7 construction.',
        '- If role omissions dominate, improve second/third role features instead.',
        '- Any new v110 rule must be selected on an earlier development block and evaluated once on a later untouched block; Sep outcomes stay confirmation-only.']
    open(OUT,'w',encoding='utf-8').write('\n'.join(L)+'\n')
if __name__=='__main__':main()
