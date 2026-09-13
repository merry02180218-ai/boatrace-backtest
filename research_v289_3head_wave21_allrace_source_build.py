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

def fetch_rows(path):
    try:
        with urllib.request.urlopen(BASE+path,timeout=30) as r:
            s=r.read().decode('utf-8-sig')
        return list(csv.DictReader(io.StringIO(s)))
    except Exception:
        return []

def norm_code(x):
    s=''.join(ch for ch in str(x or '') if ch.isdigit())
    return s.zfill(12) if s else ''

def norm_combo(x):
    s=str(x or '').strip().replace(' ','').replace('‐','-').replace('－','-')
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

def day_bundle(day_s):
    d=date.fromisoformat(day_s); ymd=d.strftime('%Y/%m/%d')
    def get(kind): return fetch_rows(f'data/{kind}/{ymd}.csv')
    cards=get('programs/race_cards'); waku=get('programs/waku10')
    realtime=get('results/realtime'); payouts=get('results/payouts')
    return day_s,cards,waku,realtime,payouts

def asmap(rs):
    return {norm_code(r.get('レースコード','')):r for r in rs if norm_code(r.get('レースコード',''))}

def main():
    q=pd.read_csv(SRC,dtype=str).fillna('')
    if len(q)!=32111: raise RuntimeError(f'unexpected Wave20 rows {len(q)}')
    if q['date'].max()>'2026-08-31': raise RuntimeError('September forbidden')
    q['race_code_norm']=q['race_code'].map(norm_code)
    days=sorted(q['date'].unique())
    bundles={}
    with ThreadPoolExecutor(max_workers=12) as ex:
        fs={ex.submit(day_bundle,d):d for d in days}
        for f in as_completed(fs):
            d,c,w,r,p=f.result(); bundles[d]=(c,w,r,p)
    records=[]; missing_cards=0; result_present=0; payout_present=0; combo_match=0; exact_present=0
    for base in q.to_dict('records'):
        d=base['date']; code=base['race_code_norm']; cards,waku,res,pays=bundles[d]
        cm=asmap(cards); wm=asmap(waku); rm=asmap(res); pm=asmap(pays)
        c=cm.get(code,{}); w=wm.get(code,{}); rr=rm.get(code,{}); pr=pm.get(code,{})
        if not c: missing_cards+=1
        rec={'date':d,'race_code':base['race_code'],'race_code_norm':code,'venue':base.get('venue',''),'race':base.get('race','')}
        for k,v in c.items():
            if k!='レースコード': rec[f'card__{k}']=v
        for k,v in w.items():
            if k!='レースコード': rec[f'waku10__{k}']=v
        ac=result_combo(rr); pc=norm_combo(pr.get('3連単_組番',''))
        if rr: result_present+=1
        if pr: payout_present+=1
        if ac: exact_present+=1
        if ac and pc and ac==pc: combo_match+=1
        rec['settle__actual_combo']=ac
        rec['settle__winner']=ac.split('-')[0] if ac else ''
        rec['settle__head3_actual']=1 if ac.startswith('3-') else 0
        rec['settle__trifecta_combo']=pc
        rec['settle__trifecta_payout_100_yen']=money(pr.get('3連単_払戻金',''))
        rec['settle__result_present']=1 if rr else 0
        rec['settle__payout_present']=1 if pr else 0
        rec['settle__combo_match']=1 if ac and pc and ac==pc else 0
        records.append(rec)
    out=pd.DataFrame(records)
    out.to_csv(OUT,index=False,encoding='utf-8-sig')
    n=len(out)
    audit={
      'rows':n,'max_date':out.date.max(),'missing_card_rows':missing_cards,
      'result_rows':result_present,'result_share':result_present/n,
      'exact_order_rows':exact_present,'exact_order_share':exact_present/n,
      'payout_rows':payout_present,'payout_share':payout_present/n,
      'combo_match_rows':combo_match,'combo_match_share':combo_match/n,
      'head3_wins':int(out['settle__head3_actual'].sum()),
      'feature_columns':int(sum(c.startswith('card__') or c.startswith('waku10__') for c in out.columns)),
    }
    audit['decision']='ALLRACE_SETTLED_SOURCE_READY' if missing_cards==0 and audit['result_share']>=.98 and audit['exact_order_share']>=.98 and audit['payout_share']>=.98 and audit['combo_match_share']>=.98 else 'ALLRACE_SOURCE_AUDIT_FAIL_CLOSED'
    OUTJ.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    md='# Wave21 all-race feature + settlement source\n\n'+''.join([
      f"- rows: **{n}**\n",f"- feature columns: **{audit['feature_columns']}**\n",
      f"- result coverage: **{result_present}/{n} ({100*audit['result_share']:.3f}%)**\n",
      f"- exact-order coverage: **{exact_present}/{n} ({100*audit['exact_order_share']:.3f}%)**\n",
      f"- payout coverage: **{payout_present}/{n} ({100*audit['payout_share']:.3f}%)**\n",
      f"- result/payout combo agreement: **{combo_match}/{n} ({100*audit['combo_match_share']:.3f}%)**\n",
      f"- actual 3-head wins: **{audit['head3_wins']}**\n",f"- decision: **{audit['decision']}**\n"])
    OUTM.write_text(md,encoding='utf-8'); print(md)
    if audit['decision']!='ALLRACE_SETTLED_SOURCE_READY': raise RuntimeError(audit['decision'])
if __name__=='__main__': main()
