from __future__ import annotations
import json
from pathlib import Path
import numpy as np, pandas as pd
from research.run_3head_exhibition_ticket_rescue_march import build_month

MARGINS=[.0025,.005,.0075,.01,.015,.02,.03,.05,.075,.10]
MONTHS=[3,4,5,6,7,8]

def audit_month(x, margin):
    z=x.sort_values(['race_code','p','second','third'],ascending=[True,False,True,True]).copy()
    z['rank']=z.groupby('race_code').cumcount()+1
    top3=z[z['rank']<=3]
    base_hits=set(top3.loc[top3.y.eq(1),'race_code'])
    r3=z[z['rank']==3].set_index('race_code')
    r4=z[z['rank']==4].set_index('race_code')
    common=r3.index.intersection(r4.index)
    gaps=(r3.loc[common,'p']-r4.loc[common,'p']).astype(float)
    add=set(gaps[gaps<=margin].index)
    fourth=z[(z['rank']==4)&z.race_code.isin(add)]
    added_hits=set(fourth.loc[fourth.y.eq(1),'race_code'])-base_hits
    n_races=int(z.race_code.nunique())
    return {
      'races':n_races,'baseline_hits':len(base_hits),'baseline_capture':len(base_hits)/n_races if n_races else None,
      'fourth_added_races':len(add),'fourth_added_tickets':len(fourth),'incremental_hits':len(added_hits),
      'four_point_hits':len(base_hits|added_hits),'four_point_capture':len(base_hits|added_hits)/n_races if n_races else None,
      'incremental_hit_per_added_ticket':len(added_hits)/len(fourth) if len(fourth) else None,
      'total_tickets':3*n_races+len(fourth),'ticket_increase_pct':len(fourth)/(3*n_races) if n_races else None,
      'gap_mean_added':float(gaps[gaps<=margin].mean()) if len(add) else None,
    }

def main():
    data={m:build_month(m) for m in MONTHS}
    # March alone selects the threshold. Prefer incremental hits, then efficiency, then fewer added tickets.
    candidates=[]
    for mar in MARGINS:
      met=audit_month(data[3],mar)
      candidates.append({'margin':mar,**met})
    c=pd.DataFrame(candidates)
    c['_eff']=c.incremental_hit_per_added_ticket.fillna(-1)
    best=c.sort_values(['incremental_hits','_eff','fourth_added_tickets','margin'],ascending=[False,False,True,True]).iloc[0]
    frozen=float(best.margin)
    monthly={str(m):{**audit_month(data[m],frozen),'non_pristine':m in [7,8]} for m in MONTHS}
    out={
      'phase':'3HEAD_CLOSE_MARGIN_FOURTH_TICKET','selection_month':'March only','frozen_margin':frozen,
      'march_grid':c.drop(columns=['_eff']).to_dict('records'),'frozen_monthly':monthly,
      'apr_jun_incremental_hits':[monthly[str(m)]['incremental_hits'] for m in [4,5,6]],
      'apr_jun_all_nonnegative':all(monthly[str(m)]['incremental_hits']>=0 for m in [4,5,6]),
      'candidate_selected_using_apr_jun':False,'july_august_non_pristine':True,
      'september_outcomes_read':False,'production_changed':False,
      'note':'This audit adds rank-4 only when base rank3-rank4 probability margin is close; it does not replace existing top3.'
    }
    Path('research_v289_3head_close_margin_fourth_ticket.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
    c.drop(columns=['_eff']).to_csv('research_v289_3head_close_margin_fourth_ticket_march_grid.csv',index=False)
    print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
