#!/usr/bin/env python3
from __future__ import annotations
"""Regression of research-only wall3 shadow on saved pre-race Biwako 7R inputs."""
import argparse,json,subprocess,sys
from pathlib import Path

EXPECTED_PRE_WALL3=['1-3-5','1-3-2','1-2-3']
EXPECTED_OFFICIAL=['1-4-5','1-4-3','1-2-4']

def main():
 ap=argparse.ArgumentParser()
 ap.add_argument('--base',required=True,type=Path);ap.add_argument('--gate',required=True,type=Path);ap.add_argument('--window',required=True,type=Path);ap.add_argument('--outdir',required=True,type=Path)
 a=ap.parse_args();a.outdir.mkdir(parents=True,exist_ok=True)
 b=json.loads(a.base.read_text());g=json.loads(a.gate.read_text());w=json.loads(a.window.read_text());b.update(g)
 b.update({'exhibition_ready':True,'deadline_jst':w['deadline_jst'],'minutes_to_deadline':w['remaining_minutes'],'evaluated_at_jst':w['now_jst'],'result_or_payout_used':False,'chronology_guard':True})
 inp=a.outdir/'final_input.json';out=a.outdir/'final.json';inp.write_text(json.dumps(b,ensure_ascii=False,indent=2))
 subprocess.check_call([sys.executable,'run_1head_v351_live_finalize.py','--input',str(inp),'--out',str(out)])
 z=json.loads(out.read_text())
 if z['tickets']!=EXPECTED_OFFICIAL: raise RuntimeError(f'official tickets drift {z["tickets"]}')
 if z.get('pre_wall3_tickets')!=EXPECTED_PRE_WALL3: raise RuntimeError(f'pre-wall3 tickets drift {z.get("pre_wall3_tickets")}')
 if not z.get('watch_pass'): raise RuntimeError('Biwako saved input no longer WATCH')
 if not z.get('wall3_ticket_promoted') or not z.get('wall3_ticket_applied'): raise RuntimeError(f'official wall3 not applied {z}')
 if not z.get('wall3_shadow_eligible') or not z.get('wall3_shadow_applied'): raise RuntimeError(f'compat wall3 fields not applied {z}')
 if abs(float(z.get('wall3_shadow_risk'))-.47)>1e-9: raise RuntimeError(f'risk drift {z.get("wall3_shadow_risk")}')
 if z.get('wall3_shadow_tickets')!=EXPECTED_OFFICIAL: raise RuntimeError(f'compat tickets drift {z.get("wall3_shadow_tickets")}')
 if z.get('ticket_profile')!='1HEAD_WATCH_WALL3_TICKET_V355_SCORE_A406_G2_300_G3_050': raise RuntimeError(f'ticket profile drift {z.get("ticket_profile")}')
 if z.get('result_or_payout_used') is not False or not z.get('chronology_guard'): raise RuntimeError('causality guard failed')
 result={'race_code':z['race_code'],'pre_wall3_tickets':z['pre_wall3_tickets'],'official_tickets':z['tickets'],'compat_shadow_tickets':z['wall3_shadow_tickets'],'ticket_profile':z['ticket_profile'],'wall3_ticket_applied':z['wall3_ticket_applied'],'risk':z['wall3_shadow_risk'],'wall_score':z['wall3_shadow_wall_score'],'attack4_score':z['wall3_shadow_attack4_score'],'official_promoted':True,'result_or_payout_used':False,'AUDIT_OK':True}
 (a.outdir/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
