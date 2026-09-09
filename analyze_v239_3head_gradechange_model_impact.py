#!/usr/bin/env python3
"""v239: connect v237 same-racer grade changes to restored v234 model outcomes.
AUDIT ONLY. July/Aug NON-PRISTINE. No model/threshold tuning.
Uses normalized racer name because current BoatraceCSV race-card schema/parser exposes name but no registration number.
"""
import pandas as pd
import analyze_v234_3head_waku10_restored_replay as v234
import analyze_v237_3head_same_racer_halfyear_audit as v237
OUT='analysis_v239_3head_gradechange_model_impact.csv'; SUM='summary_v239_3head_gradechange_model_impact.md'
def norm(s): return ' '.join(str(s or '').replace('　',' ').split())
def main():
 v237.main(); same=pd.read_csv(v237.OUT,encoding='utf-8-sig'); changed=set(same.loc[same.grade_changed==1,'racer'].map(norm)); unchanged=set(same.loc[same.grade_changed==0,'racer'].map(norm))
 cov=v234.reconstruct(); common=v234.validate_parser();d,dc,vc,basefs=v234.build_restored();fs=v234.full_features(d,basefs);fs=[x for x in fs if x in d.columns]
 # Fit/select exactly as v234, but retain racer name and outcome for Jul1-14 only.
 import analyze_v222_3head_broad_feature_audit as v222, analyze_v223_3head_unused_feature_audit as v223, analyze_v205_3head_operational_replay as v205
 first=pd.Timestamp('2026-07-01'); nextm=pd.Timestamp('2026-08-01');tr=d[d._date<first];pair=v222.fit_pair(tr,'V221');base_te,_=v223.fit_head(d,list(basefs),vc,first,nextm);k=max(1,int((base_te._p>=.30).sum()));te,_=v223.fit_head(d,fs,vc,first,nextm);sel=te.nlargest(k,'_p').copy();sel=sel[sel._date<=pd.Timestamp('2026-07-14')]
 rows=[]
 for _,r in sel.iterrows():
  if v223.ii(r.get('valid_result'))!=1 or v223.ii(r.get('course3'),3)!=3: continue
  racer=norm(r.get('name3',r.get('b3_name',r.get('艇3_選手名',''))))
  group='changed' if racer in changed else ('unchanged' if racer in unchanged else 'unmatched')
  act=v222.v166.combo(r.get('actual_combo'));actual='-'.join(map(str,act)) if len(act)==3 else ''
  if not actual: continue
  ts=v222.order(r,pair,'V221');rank=ts.index(actual)+1 if actual in ts else 0
  rows.append({'date':r._date.strftime('%Y-%m-%d'),'race_code':str(r.get('race_code','')).zfill(12),'racer':racer,'group':group,'p3':float(r._p),'head_hit':int(r._y),'top10_hit':int(int(r._y)==1 and 0<rank<=10),'rank':rank})
 z=pd.DataFrame(rows);z.to_csv(OUT,index=False,encoding='utf-8-sig')
 L=['# v239 grade-change model-impact audit','', '- AUDIT ONLY; July is NON-PRISTINE. No tuning.', '- v234 restored-Waku10 frozen head/pair model; selected July races restricted to Jul1-14.', '- Identity uses normalized racer name because current race-card parser has no registration-number field.',f'- Waku10 parser validation: {common} races, 0 mismatches.','', '|group|R|avg p3|actual head hit|calibration gap|Top10 trifecta hit|','|---|---:|---:|---:|---:|---:|']
 for g in ['changed','unchanged','unmatched']:
  q=z[z.group==g]
  if len(q): L.append(f'|{g}|{len(q)}|{100*q.p3.mean():.2f}%|{100*q.head_hit.mean():.2f}%|{100*(q.p3.mean()-q.head_hit.mean()):+.2f}pp|{100*q.top10_hit.mean():.2f}%|')
 L += ['','Interpretation: if the changed group alone has materially larger positive calibration gap than unchanged, half-year grade transition is a plausible contributor; otherwise it is unlikely to be the main explanation. This is diagnostic evidence only.']
 open(SUM,'w',encoding='utf-8').write('\n'.join(L)+'\n');print('\n'.join(L))
if __name__=='__main__': main()
