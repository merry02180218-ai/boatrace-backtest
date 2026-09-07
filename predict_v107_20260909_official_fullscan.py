"""2026-09-09 official pre-exhibition structural scan.

Uses the frozen v107 structural PRE gates for 3m/3ms/4c/5head, with BOAT RACE
Official racelist as the current program source. No current exhibition, result,
payout, or same-race odds are used. Prior same-frame waku history ends 2026-09-08.
"""
from datetime import date, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import predict_v107_20260905_official_fullscan as m

m.HD='20260909'

def load_waku_history(days=45):
    ds=[]; d=date(2026,9,8)
    for _ in range(days):
        ds.append(d); d-=timedelta(days=1)
    got=[]
    with ThreadPoolExecutor(max_workers=10) as ex:
        fut=[ex.submit(m.fetch_hist_day,d) for d in ds]
        for f in as_completed(fut):
            try: got.append(f.result())
            except Exception: pass
    got.sort(key=lambda z:z[0])
    lookup={}
    for _,items in got:
        for rid,b,z in items: lookup[(rid,b)]=z
    return lookup

m.load_waku_history=load_waku_history
m.main()

src_csv=Path('pred_v107_20260905_official_fullscan.csv')
src_md=Path('prediction_v107_20260905_official_fullscan.md')
out_csv=Path('pred_v107_20260909_official_fullscan.csv')
out_md=Path('prediction_v107_20260909_official_fullscan.md')
if src_csv.exists():
    src_csv.replace(out_csv)
if src_md.exists():
    txt=src_md.read_text(encoding='utf-8').replace('2026-09-05','2026-09-09').replace('9/4以前','9/8以前')
    out_md.write_text(txt,encoding='utf-8')
    src_md.unlink(missing_ok=True)
