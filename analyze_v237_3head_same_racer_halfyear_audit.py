#!/usr/bin/env python3
"""v237 same-racer half-year audit.
AUDIT ONLY. Jul/Aug 2026 remain NON-PRISTINE. No tuning.
Fetches race-card source directly and joins boat-3 by racer name across Jun17-30 vs Jul1-14.
The canonical parser already uses 艇3_選手名/級別/全国平均ST/全国勝率/当地勝率.
"""
import csv,io,urllib.request
from datetime import date,timedelta
from pathlib import Path
import pandas as pd, numpy as np
BASE='https://raw.githubusercontent.com/BoatraceCSV/boatracecsv.github.io/main/'
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'analysis_v237_same_racer_halfyear.csv'; SUM=ROOT/'summary_v237_3head_same_racer_halfyear_audit.md'
FIELDS={'grade':'艇3_級別','wr':'艇3_全国勝率','nst':'艇3_全国平均ST','local':'艇3_当地勝率'}
GS={'A1':1.0,'A2':.72,'B1':.38,'B2':.15}
def fetch_day(d):
 p=f'data/programs/race_cards/{d:%Y/%m/%d}.csv'
 try:
  with urllib.request.urlopen(BASE+p,timeout=30) as r:s=r.read().decode('utf-8-sig')
  return list(csv.DictReader(io.StringIO(s)))
 except Exception:return []
def num(x):
 try:return float(x)
 except:return np.nan
def main():
 rows=[]; d=date(2026,6,17)
 while d<=date(2026,7,14):
  for r in fetch_day(d):
   name=(r.get('艇3_選手名') or '').replace('　',' ').strip()
   if not name:continue
   rows.append({'date':str(d),'period':'pre' if d<date(2026,7,1) else 'post','racer':name,'grade':(r.get(FIELDS['grade']) or '').strip(),'grade_score':GS.get((r.get(FIELDS['grade']) or '').strip(),np.nan),'wr':num(r.get(FIELDS['wr'])),'nst':num(r.get(FIELDS['nst'])),'local':num(r.get(FIELDS['local']))})
  d+=timedelta(days=1)
 x=pd.DataFrame(rows); rec=[]
 for racer,g in x.groupby('racer'):
  a=g[g.period=='pre'];b=g[g.period=='post']
  if not len(a) or not len(b):continue
  r={'racer':racer,'pre_R':len(a),'post_R':len(b),'pre_grade':a.grade.mode().iloc[0] if len(a.grade.mode()) else '', 'post_grade':b.grade.mode().iloc[0] if len(b.grade.mode()) else ''}
  r['grade_changed']=int(r['pre_grade']!=r['post_grade'])
  for f in ['grade_score','wr','nst','local']:
   av=a[f].mean();bv=b[f].mean();r[f+'_pre']=av;r[f+'_post']=bv;r[f+'_delta']=bv-av
  rec.append(r)
 z=pd.DataFrame(rec);z.to_csv(OUT,index=False,encoding='utf-8-sig')
 L=['# v237 same-racer official half-year switch audit','', '- AUDIT ONLY; Jul/Aug are NON-PRISTINE. No tuning.',f'- Race-card rows fetched: {len(x)}; same boat-3 racers observed on both sides: {len(z)}.','']
 if len(z):
  L += [f'- Grade changed: {int(z.grade_changed.sum())}/{len(z)} ({100*z.grade_changed.mean():.1f}%).','', '## Same-racer median changes','|field|median delta|mean abs delta|','|---|---:|---:|']
  for f in ['grade_score','wr','nst','local']:
   q=z[f+'_delta'].dropna();L.append(f'|{f}|{q.median():+.4f}|{q.abs().mean():.4f}|')
  L += ['', '## Grade-change vs unchanged','|group|racers|mean ΔWR|mean ΔNST|mean Δlocal|','|---|---:|---:|---:|---:|']
  for label,q in [('changed',z[z.grade_changed==1]),('unchanged',z[z.grade_changed==0])]:
   if len(q):L.append(f'|{label}|{len(q)}|{q.wr_delta.mean():+.3f}|{q.nst_delta.mean():+.4f}|{q.local_delta.mean():+.3f}|')
 L += ['', '## Interpretation','A systematic same-racer jump across Jul1 supports the half-year source/reference-period-switch hypothesis. Stable same-racer values weakens it. This audit does not use Jul/Aug to select any model rule.']
 SUM.write_text('\n'.join(L)+'\n',encoding='utf-8');print('\n'.join(L))
if __name__=='__main__':main()
