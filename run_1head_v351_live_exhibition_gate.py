#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from collections import defaultdict
from datetime import date,timedelta
from pathlib import Path
import numpy as np,pandas as pd
from backtest import rows
import onehead_production_profile as prod
import run_v326_1head_ticketaware_exhibition as v326
import run_v332_1head_attack_first_redesign as v332
import run_v337_1head_head_cutoff_volume as v337

def bias_before(target):
 sums=defaultdict(list);allv=[];d=v337.PRELOAD
 while d<target:
  strows=rows(f"data/previews/stt/{d.strftime('%Y/%m/%d')}.csv");v326.update_st(strows,sums,allv);d+=timedelta(days=1)
 return v326.st_bias(sums,allv)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--probe',type=Path,required=True);ap.add_argument('--base',type=Path,required=True);ap.add_argument('--history-cutoff',required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
 x=json.loads(a.probe.read_text());code=str(x['race_code']).zfill(12);target=date(int(code[:4]),int(code[4:6]),int(code[6:8]));cut=date.fromisoformat(a.history_cutoff)
 if cut>=target: raise RuntimeError('history cutoff must be before target date')
 if x.get('result_or_payout_used') is not False or not x.get('ready'): raise RuntimeError('unsafe/unready probe')
 base=pd.read_json(a.base,typ='series'); tickets=str(base['base_tickets']); audit=x['audit']
 tkz={code:x['tkz']};stt={code:x['stt']};orig={code:x['orig']};ex,st,os=v326.corrected_direct(code,tkz,stt,orig,bias_before(target))
 feat=v326.partial_feature_row({'tickets':tickets},ex,st,os,audit); feat.update(audit)
 feat['attack_ready']=bool(audit['tkz_all6'] and audit['stt_all6'] and audit['orig_straight_all6'] and audit['orig_avg_all6']);feat['env_ready']=bool(audit['tkz_all6'] and audit['stt_all6'] and audit['orig_turn_all6'] and audit['orig_straight_all6'])
 feat['attack_core']=prod.ATTACK_CORE_W_ONE_EX*feat['one_ex']+prod.ATTACK_CORE_W_ONE_ST*feat['one_st']+prod.ATTACK_CORE_W_ONE_STRAIGHT*feat['one_straight']+prod.ATTACK_CORE_W_ONE_ORIG_AVG*feat['one_orig_avg']
 feat['env_pair']=.30*feat['sec_ex_mean_margin']+.30*feat['sec_st_mean_margin']+.20*feat['third_turn_mean_margin']+.20*feat['third_straight_mean_margin'] if feat['env_ready'] else np.nan
 train=pd.read_csv(a.base.parent/'v351_exhibition_train.csv',dtype={'race_code':str}); train['race_code']=train.race_code.astype(str).str.zfill(12);train=train[pd.to_datetime(train['date']).dt.date<=cut].copy()
 if train.empty: raise RuntimeError('empty exhibition training cache')
 test=pd.DataFrame([{**feat,'race_code':code,'head_hit':0,'hit':0}]); passed,pars=v332.fit_apply(train,test,{'family':'ATTACK_ENV_SOFT','env_w':prod.LIVE_EXHIBITION_ENV_W,'q':prod.LIVE_EXHIBITION_Q})
 out={'race_code':code,'head_exhibition_pass':bool(len(passed)==1),'attack_core':float(feat['attack_core']),'corrected_ex':{str(b):float(ex[b]) for b in range(2,7)},'corrected_st':{str(b):float(st[b]) for b in range(2,7)},'corrected_straight':{str(b):float(os[b]['straight']) for b in range(2,7)},'corrected_orig_avg':{str(b):float(os[b]['avg']) for b in range(2,7)},'exhibition_hashes':x['sha256'],'training_cutoff':a.history_cutoff,'result_or_payout_used':False,'chronology_guard':True,'v332_params':pars,'live_operation_profile':prod.LIVE_OPERATION_PROFILE_NAME,'live_env_w':prod.LIVE_EXHIBITION_ENV_W,'live_q':prod.LIVE_EXHIBITION_Q}
 a.out.write_text(json.dumps(out,ensure_ascii=False,indent=2));print(json.dumps(out,ensure_ascii=False))
if __name__=='__main__':main()
