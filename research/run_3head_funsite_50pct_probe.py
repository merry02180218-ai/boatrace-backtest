from __future__ import annotations
import csv, io, json, urllib.request
from datetime import date, timedelta

BASE='https://boatracecsv.github.io/data'
KINDS=['programs/race_cards','programs/waku10','programs/recent_national','programs/recent_local','programs/motor_stats','estimate/racer_st','estimate/motor_pt/motors']
# February only: this probe MUST NOT read March/September outcomes.
START=date(2026,2,1); END=date(2026,3,1)

def get(kind,d):
    url=f"{BASE}/{kind}/{d:%Y/%m/%d}.csv"
    try:
        with urllib.request.urlopen(url,timeout=30) as r:
            raw=r.read().decode('utf-8-sig')
        rows=list(csv.DictReader(io.StringIO(raw)))
        return {'ok':True,'url':url,'rows':len(rows),'columns':list(rows[0].keys()) if rows else []}
    except Exception as e:
        return {'ok':False,'url':url,'error':f'{type(e).__name__}: {e}'}

def main():
    out={'policy':{'selection_period':'2026-02 only','march_outcomes_read':False,'september_outcomes_read':False},'days':[]}
    d=START
    while d<END:
        day={'date':d.isoformat(),'sources':{}}
        for k in KINDS: day['sources'][k]=get(k,d)
        out['days'].append(day); d+=timedelta(days=1)
    summary={k:{'ok_days':sum(x['sources'][k]['ok'] for x in out['days']),'rows':sum(x['sources'][k].get('rows',0) for x in out['days'])} for k in KINDS}
    out['summary']=summary
    with open('research_3head_funsite_50pct_probe.json','w',encoding='utf-8') as f: json.dump(out,f,ensure_ascii=False,indent=2)
    print(json.dumps({'policy':out['policy'],'summary':summary},ensure_ascii=False,indent=2))

if __name__=='__main__': main()
