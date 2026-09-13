from __future__ import annotations
import csv, io, os, urllib.request, json
from datetime import date, timedelta
from collections import Counter

REF=os.environ.get('BOATRACECSV_REF','main')
BASE=f'https://raw.githubusercontent.com/BoatraceCSV/boatracecsv.github.io/{REF}/'
START=date(2026,2,1); END=date(2026,8,31)

def rows(path):
    try:
        with urllib.request.urlopen(BASE+path,timeout=30) as r:
            s=r.read().decode('utf-8-sig')
        return list(csv.DictReader(io.StringIO(s)))
    except Exception:
        return []

def main():
    out=[]; daily=START; missing=[]; per_month=Counter(); per_venue=Counter()
    while daily<=END:
        ymd=daily.strftime('%Y/%m/%d')
        cards=rows(f'data/programs/race_cards/{ymd}.csv')
        if not cards:
            missing.append(str(daily)); daily+=timedelta(days=1); continue
        seen=set()
        for r in cards:
            code=(r.get('レースコード') or '').strip()
            if not code or code in seen: continue
            seen.add(code)
            # race_cards are pre-deadline program data. Keep only rows that visibly contain boats 1..6.
            six=all((r.get(f'艇{b}_選手名') or '').strip() for b in range(1,7))
            if not six: continue
            venue=(r.get('レース場コード') or '').strip()
            race=(r.get('レース回') or '').strip()
            out.append({'date':str(daily),'race_code':code,'venue':venue,'race':race})
            per_month[daily.strftime('%Y-%m')]+=1; per_venue[venue]+=1
        daily+=timedelta(days=1)
    # Full population audit only. No outcomes are loaded here.
    report={'start':str(START),'end':str(END),'all_six_boat_races':len(out),'missing_program_dates':missing,'monthly':dict(sorted(per_month.items())),'venues':dict(sorted(per_venue.items())),'decision':'ALLRACE_UNIVERSE_READY' if len(out)>678 else 'ALLRACE_UNIVERSE_TOO_SMALL'}
    with open('analysis_v289_3head_wave20_allrace_universe.csv','w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=['date','race_code','venue','race']); w.writeheader(); w.writerows(out)
    with open('research_v289_3head_wave20_allrace_universe.json','w',encoding='utf-8') as f: json.dump(report,f,ensure_ascii=False,indent=2)
    with open('research_v289_3head_wave20_allrace_universe.md','w',encoding='utf-8') as f:
        f.write('# Wave20 Feb-Aug all-race universe audit\n\n')
        f.write(f"- all six-boat races: **{len(out)}**\n- missing program dates: **{len(missing)}**\n- decision: **{report['decision']}**\n\n## Monthly\n")
        for k,v in report['monthly'].items(): f.write(f'- {k}: {v}R\n')
    print(json.dumps(report,ensure_ascii=False))
    if report['decision']!='ALLRACE_UNIVERSE_READY': raise SystemExit(2)
if __name__=='__main__': main()
