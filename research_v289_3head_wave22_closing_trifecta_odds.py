from __future__ import annotations
import csv, gzip, json, re, time, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import pandas as pd

SRC=Path('analysis_v289_3head_wave21_allrace_feature_settled.csv')
OUT=Path('analysis_v289_3head_wave22_closing_trifecta_odds.csv.gz')
OUTJ=Path('research_v289_3head_wave22_closing_trifecta_odds.json')
OUTM=Path('research_v289_3head_wave22_closing_trifecta_odds.md')
SLUG={'01':'kiryu','02':'toda','03':'edogawa','04':'heiwajima','05':'tamagawa','06':'hamanako','07':'gamagori','08':'tokoname','09':'tsu','10':'mikuni','11':'biwako','12':'suminoe','13':'amagasaki','14':'naruto','15':'marugame','16':'kojima','17':'miyajima','18':'tokuyama','19':'shimonoseki','20':'wakamatsu','21':'ashiya','22':'fukuoka','23':'karatsu','24':'omura'}
PAT=re.compile(r'<div id="dm-(\d+)"[^>]*>\s*([1-6]-[1-6]-[1-6])\s*</div>.*?<div id="od-\1"[^>]*>\s*([^<]+?)\s*</div>',re.S)

def final_url(code):
    code=str(code).strip()
    if len(code)<12 or code[8:10] not in SLUG:return None
    return f"https://odds.kyotei24.jp/odds3t-{SLUG[code[8:10]]}-{code[:8]}-{int(code[10:12])}.html"

def parse(html):
    if '締切時オッズ' not in html:return {},False
    vals={}
    for _,t,v in PAT.findall(html):
        try:
            z=float(v.replace(',','').strip())
            if z>1.0:vals[t]=z
        except Exception: pass
    return vals,True

def fetch_one(code):
    url=final_url(code)
    if not url:return code,{},False,'bad_code',''
    err=''
    for attempt in range(4):
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 (compatible; boatrace-backtest/1.0)'})
            with urllib.request.urlopen(req,timeout=25) as r: html=r.read().decode('utf-8','replace')
            vals,label=parse(html)
            if label and len(vals)>=100:return code,vals,True,'',url
            err=f'parsed={len(vals)} label={label}'
        except Exception as e: err=f'{type(e).__name__}: {e}'
        time.sleep(.35*(attempt+1))
    return code,{},False,err,url

def main():
    q=pd.read_csv(SRC,dtype=str).fillna('')
    if len(q)!=32111: raise RuntimeError(f'unexpected Wave21 rows {len(q)}')
    if q['date'].max()>'2026-08-31': raise RuntimeError('September forbidden')
    need=q[['date','race_code']].drop_duplicates('race_code').copy()
    codes=need['race_code'].astype(str).tolist()
    rows=[]; ok=0
    with ThreadPoolExecutor(max_workers=16) as ex:
        futs={ex.submit(fetch_one,c):c for c in codes}
        for i,f in enumerate(as_completed(futs),1):
            c,od,label,err,url=f.result()
            if od: ok+=1
            rows.append({'race_code':c,'odds_ok':1 if od else 0,'parsed_odds':len(od),'deadline_label':1 if label else 0,'odds_json':json.dumps(od,ensure_ascii=False,separators=(',',':')) if od else '', 'error':err,'url':url})
            if i%500==0 or i==len(codes): print(f'closing odds {i}/{len(codes)} ok={ok}',flush=True)
    out=pd.DataFrame(rows).merge(need,on='race_code',how='left').sort_values(['date','race_code'])
    out.to_csv(OUT,index=False,encoding='utf-8-sig',compression='gzip')
    n=len(out); full120=int((out['parsed_odds']==120).sum()); okn=int(out['odds_ok'].sum())
    by_month=out.assign(month=out['date'].str[:7]).groupby('month').agg(races=('race_code','size'),ok=('odds_ok','sum'),full120=('parsed_odds',lambda s:int((s==120).sum()))).reset_index()
    by_month['coverage_pct']=100*by_month['ok']/by_month['races']
    audit={'rows':n,'ok_rows':okn,'coverage_share':okn/n if n else 0,'full120_rows':full120,'full120_share':full120/n if n else 0,'max_date':out['date'].max(),'months':by_month.to_dict('records')}
    audit['decision']='CLOSING_ODDS_SOURCE_READY' if audit['coverage_share']>=.95 and audit['full120_share']>=.90 else 'CLOSING_ODDS_SOURCE_AUDIT_FAIL_CLOSED'
    OUTJ.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    L=['# Wave22 全母集団 締切時3連単オッズ監査','',f'- rows: **{n}**',f'- odds available: **{okn}/{n} ({100*audit["coverage_share"]:.3f}%)**',f'- full 120 odds: **{full120}/{n} ({100*audit["full120_share"]:.3f}%)**',f'- decision: **{audit["decision"]}**','','## Monthly coverage','']
    for r in audit['months']:L.append(f"- {r['month']}: {int(r['ok'])}/{int(r['races'])} ({r['coverage_pct']:.2f}%), full120={int(r['full120'])}")
    L += ['','- Source: Kyotei24 Odds Bank historical 3T pages explicitly labelled 締切時オッズ.','- Odds are kept separate from prediction features and are for staking/post-hoc ROI evaluation only.']
    OUTM.write_text('\n'.join(L)+'\n',encoding='utf-8'); print('\n'.join(L),flush=True)
    if audit['decision']!='CLOSING_ODDS_SOURCE_READY': raise RuntimeError(audit['decision'])
if __name__=='__main__':main()
