"""v351 joint ROI grid manifest; research-only, 2026-09-17 outcomes hard excluded."""
import csv,json,os
from pathlib import Path
OUT=Path('/tmp/v351-joint-roi-grid'); OUT.mkdir(parents=True,exist_ok=True)
HEAD=[.775,.7775,.780,.7825,.785,.7875,.790]
MASS=[.350,.3625,.375,.3875,.400,.4125,.425]
ENV_W=[.05,.10,.15]; ENV_Q=[.60,.65,.70]
if '20260917' in os.environ.get('ALLOW_RESULT_DATES',''): raise RuntimeError('20260917 result/payout must remain UNREAD')
if not Path('run_v351_1head_third_close_margin_audit.py').exists(): raise RuntimeError('canonical v351 audit missing')
rows=[{'head_cutoff':h,'opponent_mass_min':m,'env_w':w,'env_q':q} for h in HEAD for m in MASS for w in ENV_W for q in ENV_Q]
manifest={'profile':'1HEAD_PRODUCTION_20260915_HEAD078_V351_OPPONENTCORE_G2_045_G3_100','research_only':True,'grid_cells':len(rows),'head':HEAD,'mass':MASS,'env_w':ENV_W,'env_q':ENV_Q,'production_cell':{'head_cutoff':.78,'opponent_mass_min':.375,'env_w':.10,'env_q':.65},'formal_sentinel':{'R':276,'HEAD':241,'EXACT3':131},'TODAY_20260917_RESULT_OR_PAYOUT_USED':False,'status':'GRID_MANIFEST_OK'}
(OUT/'grid_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
with (OUT/'grid.csv').open('w',newline='',encoding='utf-8') as f:
 z=csv.DictWriter(f,fieldnames=rows[0]); z.writeheader(); z.writerows(rows)
print(json.dumps(manifest,indent=2)); print('MANIFEST ONLY: no ROI claim until canonical scoring stage is wired.')
