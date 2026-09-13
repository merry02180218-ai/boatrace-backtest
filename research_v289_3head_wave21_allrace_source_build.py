from __future__ import annotations
import csv, io, json, os, urllib.request, time
from datetime import date
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd

REF=os.environ.get('BOATRACECSV_REF','main')
BASE=f'https://raw.githubusercontent.com/BoatraceCSV/boatracecsv.github.io/{REF}/'
SRC=Path('analysis_v289_3head_wave20_allrace_universe.csv')
OUT=Path('analysis_v289_3head_wave21_allrace_feature_settled.csv')
OUTJ=Path('research_v289_3head_wave21_allrace_source_build.json')
OUTM=Path('research_v289_3head_wave21_allrace_source_build.md')

def fetch_rows(path, attempts=3):
    best=[]
    for i in range(attempts):
        try:
            with urllib.request.urlopen(BASE+path,timeout=30) as r:
                s=r.read().decode('utf-8-sig')
            got=list(csv.DictReader(io.StringIO(s)))
            if len(got)>len(best): best=got
            if got: return got
        except Exception: pass
        time.sleep(0.4*(i+1))
    return best

def norm_code(x):
    s=''.join(ch for ch in str(x or '') if ch.isdigit())
    return s.zfill(12) if s else ''

def norm_combo(x):
    s=str(x or '').strip().replace(' ','').replace('‐','-').replace('－','-').replace('―','-').replace('ー','-')
    try:a=[int(z) for z in s.split('-')]
    except:return ''
    return '-'.join(map(str,a)) if len(a)==3 and len(set(a))==3 and all(1<=z<=6 for z in a) else ''

def money(x):
    try:return int(float(str(x).replace(',','').replace('円','').strip()))
    except:return 0

def result_combo(r):
    vals=[]
    for k in ('1着_艇番','2着_艇番','3着_艇番'):
        try:v=int(float(r.get(k,'')))
        except:return ''
        if not 1<=v<=6:return ''
        vals.append(v)
    return '-'.join(map(str,vals)) if len(set(vals))==3 else ''

def asmap(rs):
    return {norm_code(r.get('レースコード','')):r for r in rs if norm_code(r.get('レースコード',''))}

def day_bundle(day_s):
    d=date.fromisoformat(day_s); ymd=d.strftime('%Y/%m/%d')
    def get(kind): return fetch_rows(f'data/{kind}/{ymd}.csv')
    return day_s,get('programs/race_cards'),get('programs/waku10'),get('results/realtime'),get('results/payouts')

def main():
    q=pd.read_csv(SRC,dtype=str).fillna('')
    if len(q)!=32111: raise RuntimeError(f'unexpected Wave20 rows {len(q)}')
    if q['date'].max()>'2026-08-31': raise RuntimeError('September forbidden')
    q['race_code_norm']=q['race_code'].map(norm_code)
    days=sorted(q['date'].unique()); expected=q.groupby('date').size().to_dict(); bundles={}
    with ThreadPoolExecutor(max_workers=8) as ex:
        fs={ex.submit(day_bundle,d):d for d in days}
        for f in as_completed(fs):
            d,c,w,r,p=f.result(); bundles[d]=(c,w,r,p)
    retry_days=[]
    for d in days:
        c,w,r,p=bundles[d]; exp=int(expected[d]); rm,pm=asmap(r),asmap(p)
        if len(rm)<max(1,int(exp*.95)) or len(pm)<max(1,int(exp*.95)):
            retry_days.append(d); dd=date.fromisoformat(d).strftime('%Y/%m/%d')
            r2=fetch_rows(f'data/results/realtime/{dd}.csv',attempts=5); p2=fetch_rows(f'data/results/payouts/{dd}.csv',attempts=5)
            if len(r2)>len(r): r=r2
            if len(p2)>len(p): p=p2
            bundles[d]=(c,w,r,p)
    maps={d:tuple(asmap(x) for x in bundles[d]) for d in days}
    records=[]; missing_cards=0; result_present=0; payout_present=0; exact_result=0; payout_combo_present=0; both_match=0; both_mismatch=0; settled_usable=0
    for base in q.to_dict('records'):
        d=base['date']; code=base['race_code_norm']; cm,wm,rm,pm=maps[d]
        c=cm.get(code,{}); w=wm.get(code,{}); rr=rm.get(code,{}); pr=pm.get(code,{})
        if not c: missing_cards+=1
        rec={'date':d,'race_code':base['race_code'],'race_code_norm':code,'venue':base.get('venue',''),'race':base.get('race','')}
        for k,v in c.items():
            if k!='レースコード': rec[f'card__{k}']=v
        for k,v in w.items():
            if k!='レースコード': rec[f'waku10__{k}']=v
        ac=result_combo(rr); pc=norm_combo(pr.get('3連単_組番','')); pay=money(pr.get('3連単_払戻金',''))
        if rr: result_present+=1
        if pr: payout_present+=1
        if ac: exact_result+=1
        if pc: payout_combo_present+=1
        if ac and pc:
            if ac==pc: both_match+=1
            else: both_mismatch+=1
        final_combo=ac or pc; usable=bool(final_combo and pay>0 and (not ac or not pc or ac==pc))
        if usable: settled_usable+=1
        rec['settle__actual_combo_result']=ac; rec['settle__trifecta_combo_payout']=pc
        rec['settle__actual_combo']=final_combo if usable else ''; rec['settle__winner']=final_combo.split('-')[0] if usable else ''
        rec['settle__head3_actual']=1 if usable and final_combo.startswith('3-') else 0
        rec['settle__trifecta_payout_100_yen']=pay if usable else 0
        rec['settle__result_present']=1 if rr else 0; rec['settle__payout_present']=1 if pr else 0
        rec['settle__both_match']=1 if ac and pc and ac==pc else 0; rec['settle__both_mismatch']=1 if ac and pc and ac!=pc else 0
        rec['settle__usable']=1 if usable else 0; records.append(rec)
    out=pd.DataFrame(records); out.to_csv(OUT,index=False,encoding='utf-8-sig')
    n=len(out); both=both_match+both_mismatch
    audit={'rows':n,'max_date':out.date.max(),'missing_card_rows':missing_cards,'retry_days':len(retry_days),'result_rows':result_present,'result_share':result_present/n,'exact_result_rows':exact_result,'exact_result_share':exact_result/n,'payout_rows':payout_present,'payout_share':payout_present/n,'payout_combo_rows':payout_combo_present,'payout_combo_share':payout_combo_present/n,'both_present_comparable_rows':both,'both_match_rows':both_match,'both_mismatch_rows':both_mismatch,'combo_agreement_when_both':both_match/both if both else 0.0,'settled_usable_rows':settled_usable,'settled_usable_share':settled_usable/n,'head3_wins':int(out['settle__head3_actual'].sum()),'feature_columns':int(sum(c.startswith('card__') or c.startswith('waku10__') for c in out.columns))}
    audit['decision']='ALLRACE_SETTLED_SOURCE_READY' if missing_cards==0 and audit['settled_usable_share']>=.98 and audit['combo_agreement_when_both']>=.998 else 'ALLRACE_SOURCE_AUDIT_FAIL_CLOSED'
    md='# Wave21 all-race feature + settlement source\n\n'+''.join([f"- rows: **{n}**\n",f"- feature columns: **{audit['feature_columns']}**\n",f"- retry days: **{audit['retry_days']}**\n",f"- result coverage: **{result_present}/{n} ({100*audit['result_share']:.3f}%)**\n",f"- payout coverage: **{payout_present}/{n} ({100*audit['payout_share']:.3f}%)**\n",f"- usable exact settlement: **{settled_usable}/{n} ({100*audit['settled_usable_share']:.3f}%)**\n",f"- agreement when both exact sources exist: **{both_match}/{both} ({100*audit['combo_agreement_when_both']:.4f}%)**\n",f"- true source mismatches: **{both_mismatch}**\n",f"- actual 3-head wins in usable rows: **{audit['head3_wins']}**\n",f"- decision: **{audit['decision']}**\n"])
    OUTJ.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); OUTM.write_text(md,encoding='utf-8'); print(md)
    if audit['decision']!='ALLRACE_SETTLED_SOURCE_READY': raise RuntimeError(audit['decision'])

    # Wave22: historical closing trifecta odds. Evaluation/staking only; never prediction features.
    from research_v289_3head_wave22_closing_trifecta_odds import main as wave22_main
    wave22_main()
    oj=json.loads(Path('research_v289_3head_wave22_closing_trifecta_odds.json').read_text(encoding='utf-8'))
    od=pd.read_csv('analysis_v289_3head_wave22_closing_trifecta_odds.csv.gz',dtype=str,compression='gzip').fillna('')
    keep=['race_code','odds_ok','parsed_odds','deadline_label','odds_json','error','url']
    merged=out.merge(od[keep],on='race_code',how='left').rename(columns={'odds_ok':'closing_odds__ok','parsed_odds':'closing_odds__parsed','deadline_label':'closing_odds__deadline_label','odds_json':'closing_odds__json','error':'closing_odds__error','url':'closing_odds__url'})
    merged.to_csv(OUT,index=False,encoding='utf-8-sig')
    audit['closing_odds']=oj; OUTJ.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    md += f"\n# Wave22 closing trifecta odds\n\n- odds available: **{oj['ok_rows']}/{oj['rows']} ({100*oj['coverage_share']:.3f}%)**\n- full 120 odds: **{oj['full120_rows']}/{oj['rows']} ({100*oj['full120_share']:.3f}%)**\n- decision: **{oj['decision']}**\n- closing odds are staking/post-hoc ROI only and excluded from prediction features.\n"
    OUTM.write_text(md,encoding='utf-8'); print(md.split('# Wave22')[-1],flush=True)
if __name__=='__main__': main()
