#!/usr/bin/env python3
import json
from pathlib import Path
import run_v337_1head_head_cutoff_volume as v337
import run_v340_1head_adaptive_odds_dutch as v
import onehead_production_profile as prod
P=Path('/tmp/v340prep'); P.mkdir(parents=True,exist_ok=True)
base=v337.load_candidate_base(); y,_,_=v337.build_exhibition(base); v337.validate_no_sep(y)
_,s,_,_=v337.eval_cut(y,prod.HEAD_CUTOFF)
got=(len(s),int(s.head_hit.sum()),int(s.hit.sum()),v.identity_hash(s))
exp=(prod.EXPECTED_PASS_R,prod.EXPECTED_HEAD,prod.EXPECTED_EXACT3,prod.EXPECTED_PASS_ID_SHA256)
assert got==exp,(got,exp)
assert not any(str(x).startswith('2026-09') for x in s.month.astype(str))
r=v.full_rankings(s)
s[['month','race_code','actual_combo','head_hit','hit','tickets']].sort_values('race_code').to_csv(P/'selected.csv',index=False)
(P/'rankings.json').write_text(json.dumps(r),encoding='utf-8')
(P/'identity.json').write_text(json.dumps({'R':got[0],'head':got[1],'exact3_top3':got[2],'sha256':got[3],'SEPTEMBER_OUTCOMES_READ':False}),encoding='utf-8')
print(got,flush=True)
