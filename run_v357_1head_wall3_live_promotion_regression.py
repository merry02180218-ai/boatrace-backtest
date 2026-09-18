#!/usr/bin/env python3
from __future__ import annotations
"""v357: final LIVE promotion regression for official WATCH wall3 ticket rerank."""
import argparse,json,subprocess,sys
from pathlib import Path
import onehead_production_profile as prod

CASES={
 'biwako7':{
  'code':'202609181107','attention':'WATCH',
  'pre':['1-3-5','1-3-2','1-2-3'],
  'official':['1-4-5','1-4-3','1-2-4'],
  'applied':True,
 },
 'naruto9':{
  'code':'202609181409','attention':'BASIC',
  'pre':['1-2-5','1-2-4','1-5-2'],
  'official':['1-2-5','1-2-4','1-5-2'],
  'applied':False,
 },
}

def run_case(name,cfg,base_dir,live_dir,outdir):
 code=cfg['code']
 b=json.loads((base_dir/f'{code}.json').read_text())
 g=json.loads((live_dir/f'gate_{code}.json').read_text())
 w=json.loads((live_dir/f'window_{code}.json').read_text())
 b.update(g)
 b.update({'exhibition_ready':True,'deadline_jst':w['deadline_jst'],'minutes_to_deadline':w['remaining_minutes'],
           'evaluated_at_jst':w.get('now_jst') or w.get('evaluated_at_jst'),'result_or_payout_used':False,'chronology_guard':True})
 inp=outdir/f'{name}_input.json'; out=outdir/f'{name}_final.json'
 inp.write_text(json.dumps(b,ensure_ascii=False,indent=2))
 subprocess.check_call([sys.executable,'run_1head_v351_live_finalize.py','--input',str(inp),'--out',str(out)])
 z=json.loads(out.read_text())
 if z['attention_level']!=cfg['attention']: raise RuntimeError(f'{name} attention drift {z["attention_level"]}')
 if z['pre_wall3_tickets']!=cfg['pre']: raise RuntimeError(f'{name} pre-wall3 drift {z["pre_wall3_tickets"]}')
 if z['tickets']!=cfg['official']: raise RuntimeError(f'{name} official tickets drift {z["tickets"]}')
 if bool(z['wall3_ticket_applied'])!=cfg['applied']: raise RuntimeError(f'{name} applied drift {z["wall3_ticket_applied"]}')
 if z.get('result_or_payout_used') is not False or not z.get('chronology_guard'): raise RuntimeError(f'{name} causality guard failed')
 return {'race_code':code,'attention_level':z['attention_level'],'pre_wall3_tickets':z['pre_wall3_tickets'],
         'official_tickets':z['tickets'],'wall3_ticket_applied':z['wall3_ticket_applied'],
         'ticket_profile':z['ticket_profile'],'risk':z['wall3_shadow_risk'],'result_or_payout_used':False}

def main():
 ap=argparse.ArgumentParser()
 ap.add_argument('--base-dir',required=True,type=Path)
 ap.add_argument('--biwako-live-dir',required=True,type=Path)
 ap.add_argument('--naruto-live-dir',required=True,type=Path)
 ap.add_argument('--outdir',required=True,type=Path)
 a=ap.parse_args(); a.outdir.mkdir(parents=True,exist_ok=True)
 # Historical production sentinel constants must remain frozen.
 frozen={
  'PROFILE_NAME':'1HEAD_PRODUCTION_20260915_HEAD078_V351_OPPONENTCORE_G2_045_G3_100',
  'HEAD_CUTOFF':.78,'PASS_R':276,'HEAD':241,'EXACT3':131,
  'RACE_SHA':'08eb41e04c36d25074d6a1e471ff9334fafd34c8306cd5d336923772b613b8bd',
  'TICKET_SHA':'21631473d2a8b82f4fe93d18f8292d777837c26a47c408917fd8b722d1898cd7',
 }
 got={'PROFILE_NAME':prod.PROFILE_NAME,'HEAD_CUTOFF':prod.HEAD_CUTOFF,'PASS_R':prod.PRODUCTION_EXPECTED_PASS_R,
      'HEAD':prod.PRODUCTION_EXPECTED_HEAD,'EXACT3':prod.PRODUCTION_EXPECTED_EXACT3,
      'RACE_SHA':prod.PRODUCTION_EXPECTED_PASS_ID_SHA256,'TICKET_SHA':prod.PRODUCTION_EXPECTED_TICKET_ID_SHA256}
 if got!=frozen: raise RuntimeError(f'historical production constants drift {got}')
 if not prod.WALL3_LIVE_TICKET_PROMOTED: raise RuntimeError('wall3 live ticket promotion flag is false')
 cases={
  'biwako7':run_case('biwako7',CASES['biwako7'],a.base_dir,a.biwako_live_dir,a.outdir),
  'naruto9':run_case('naruto9',CASES['naruto9'],a.base_dir,a.naruto_live_dir,a.outdir),
 }
 result={'promotion_profile':prod.WALL3_LIVE_TICKET_PROFILE_NAME,'historical_production_constants_frozen':True,
         'cases':cases,'SEPTEMBER_OUTCOMES_READ':False,'RESULT_OR_PAYOUT_USED':False,'AUDIT_OK':True}
 (a.outdir/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
 print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
