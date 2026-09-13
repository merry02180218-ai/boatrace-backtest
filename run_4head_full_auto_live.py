#!/usr/bin/env python3
"""Full one-command upstream orchestrator for frozen HEAD4 v291 VARN LIVE.

Required prepared same-day inputs are the already accepted result-blind PRE outputs:
- current race_cards.csv
- current waku10.csv
- pre_scan.csv (contains frozen PRE probability + causal PRE feature row)

From those, this command automatically performs:
  POST current-source fetch -> frozen POST inference
  current six-boat exhibition / frozen v90 ST-flat
  v74/v83/v91 ENV context+21 primitives -> frozen ENV_ENTRY
  v93 opponent primitives
  causal v221-style player history
  strict current source assembly
  frozen source adapter + A-LIVE/v283 input preparation
  optionally official pre-deadline 120-way odds -> VARN -> exact JPY10,000 Dutch

No target-day result or payout endpoint is read. Missing/unpublished inputs fail closed.
The final existing runner remains owner of official market acquisition and audit-before-result.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any, Mapping

from head4_v291_downstream_inference import load_artifact, score_post
from build_4head_post_live import fetch_and_build as build_post_features
from build_4head_v283_current_exhibition_live import fetch_and_build as build_exhibition
from build_4head_env_context_live import fetch_and_build as build_env_context
from build_4head_env_v91_primitives_live import build as build_env_primitives
from build_4head_env_entry_live import assemble as assemble_env
from build_4head_v93_primitives_live import build as build_v93
from build_4head_player_history_live import build as build_player
from assemble_4head_current_source import assemble as assemble_source

POLICY = 'HEAD4_V291_COMP7_VARN_F4_N16'
PRE_FEATURES = [
    'legacy_score4','racer4','hist_st_edge_4v3','wall3_weak','inner12_resistance',
    'motor4_2ren','motor4_hist','turnfoot4_prior','past_win4',
]
POST_EXHIBITION_FEATURES = [
    'ex_st_rank4','ex_st_4','ex_st_edge_4v3','orig_straight4','orig_lap4','orig_turn4','tilt4',
]
FORBIDDEN_TARGET_COLUMNS = ('winner','second','third','payout','kimarite','result','profit','return','odds')


class FullAutoLiveError(RuntimeError):
    pass


def _rows(path: str) -> list[dict[str,str]]:
    p=Path(path)
    if not p.is_file():
        raise FullAutoLiveError(f'missing input file: {path}')
    with p.open(encoding='utf-8-sig',newline='') as f:
        return list(csv.DictReader(f))


def _code(v: Any) -> str:
    c=str(v or '').zfill(12)
    if len(c)!=12 or not c.isdigit():
        raise FullAutoLiveError(f'invalid race_code: {v!r}')
    return c


def _target(rows: list[Mapping[str,Any]], code: str, label: str) -> dict[str,Any]:
    q=[dict(r) for r in rows if _code(r.get('race_code',r.get('レースコード',''))) == code]
    if len(q)!=1:
        raise FullAutoLiveError(f'{label} target row count={len(q)} for {code}')
    return q[0]


def _finite(name: str, v: Any) -> float:
    try:x=float(v)
    except Exception as e:raise FullAutoLiveError(f'invalid {name}') from e
    if not math.isfinite(x):raise FullAutoLiveError(f'non-finite {name}')
    return x


def _strip_forbidden(row: Mapping[str,Any]) -> dict[str,Any]:
    out={}
    for k,v in row.items():
        low=str(k).lower()
        if any(tok in low for tok in FORBIDDEN_TARGET_COLUMNS):
            continue
        out[str(k)]=v
    return out


def build_all(
    hd: str,
    jcd: int,
    rno: int,
    race_cards_path: str,
    waku10_path: str,
    pre_scan_path: str,
    artifact_path: str='artifacts/head4_v291_downstream_20260630.json',
    history_start: str='2025-10-01',
    timeout: int=20,
) -> dict[str,Any]:
    code=f'{hd}{int(jcd):02d}{int(rno):02d}'
    card=_target(_rows(race_cards_path),code,'race_cards')
    waku=_target(_rows(waku10_path),code,'waku10')
    pre_row=_target(_rows(pre_scan_path),code,'pre_scan')
    pre=_finite('PRE',pre_row.get('PRE'))
    if any(k not in pre_row for k in PRE_FEATURES):
        raise FullAutoLiveError('PRE scan missing frozen PRE features')

    artifact=load_artifact(artifact_path)

    # Exact 16-field frozen POST row = PRE causal 9 + current exhibition 7.
    post_payload=build_post_features(hd,jcd,rno,timeout)
    post_cur=post_payload.get('features') or {}
    if list(post_cur) != POST_EXHIBITION_FEATURES:
        raise FullAutoLiveError('POST current feature schema/order mismatch')
    post_row={k:_finite(k,pre_row[k]) for k in PRE_FEATURES}
    post_row.update({k:_finite(k,post_cur[k]) for k in POST_EXHIBITION_FEATURES})
    post=float(score_post(post_row,artifact))

    # Six-boat current exhibition is also the exact accepted v90 ST-flat source.
    exhibition=build_exhibition(hd,jcd,rno,timeout)

    # Exact v74 history replay + current entry/wind/tilt -> 21 v91/v83 primitives.
    context=build_env_context(hd,jcd,rno,race_cards_path,exhibition,timeout)
    primitives=build_env_primitives(exhibition,context)
    env_row=assemble_env(primitives,pre,post,artifact)
    from head4_v291_downstream_inference import score_env_entry
    env_score=float(score_env_entry(env_row,artifact))
    env_payload={
        'schema':'head4_env_entry_auto_live_v1','race_code':code,'policy':'HEAD4_V291_COMP7',
        'frozen_training_cutoff':'2026-06-30','result_blind':True,'odds_used':False,'payout_used':False,
        'same_day_results_used':False,'jul_aug_labels_used':False,'september_labels_used':False,'v96_used':False,
        'PRE':pre,'POST':post,'features':env_row,'ENV_ENTRY':env_score,
    }

    v93=build_v93(card,waku,exhibition)
    target_date=date(int(hd[:4]),int(hd[4:6]),int(hd[6:8]))
    hs=date.fromisoformat(history_start)
    player=build_player(card,target_date,hs)

    # The downstream bundle only needs causal PRE flat features plus generated
    # v93/player/ST/ENV overlays. Strip any accidental result/market columns.
    base_flat=_strip_forbidden(pre_row)
    source=assemble_source(code,pre,post,base_flat,env_payload,exhibition,v93,player)

    return {
        'schema':'head4_full_auto_live_v1','policy':POLICY,'race_code':code,
        'result_blind':True,'target_day_results_used':False,'odds_used_upstream':False,'payout_used':False,
        'PRE':pre,'POST':post,'ENV_ENTRY':env_score,
        'post_payload':post_payload,'env_context_audit':{
            'history_start':context.get('history_start'),'history_end':context.get('history_end'),
            'history_population_n':context.get('history_population_n'),
            'weather_source_kind':context.get('weather_source_kind'),
            'weather_snapshot_hhmm':context.get('weather_snapshot_hhmm'),
            'entry_source_kind':context.get('entry_source_kind'),
            'tilt_source_kind':context.get('tilt_source_kind'),
            'pinned_boatracecsv_commit':context.get('pinned_boatracecsv_commit'),
        },
        'source_json':source,
    }


def main() -> None:
    ap=argparse.ArgumentParser()
    ap.add_argument('--date',required=True,help='YYYYMMDD')
    ap.add_argument('--jcd',required=True,type=int)
    ap.add_argument('--race',required=True,type=int)
    ap.add_argument('--race-cards',required=True)
    ap.add_argument('--waku10',required=True)
    ap.add_argument('--pre-scan',required=True)
    ap.add_argument('--artifact',default='artifacts/head4_v291_downstream_20260630.json')
    ap.add_argument('--history-start',default='2025-10-01')
    ap.add_argument('--source-out',required=True)
    ap.add_argument('--audit',default='live_audit_4head_v291_varn.jsonl')
    ap.add_argument('--deadline-jst')
    ap.add_argument('--prepare-only',action='store_true')
    ap.add_argument('--prepared-out')
    ap.add_argument('--bundle-out')
    ap.add_argument('--timeout',type=int,default=20)
    a=ap.parse_args()

    z=build_all(a.date,a.jcd,a.race,a.race_cards,a.waku10,a.pre_scan,a.artifact,a.history_start,a.timeout)
    src=z['source_json']
    Path(a.source_out).write_text(json.dumps(src,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

    cmd=[sys.executable,'run_4head_v291_varn_auto_live.py','--source-json',a.source_out,
         '--date',a.date,'--jcd',str(a.jcd),'--race',str(a.race),'--audit',a.audit]
    if a.prepared_out:cmd += ['--prepared-out',a.prepared_out]
    if a.bundle_out:cmd += ['--bundle-out',a.bundle_out]
    if a.prepare_only:
        cmd.append('--prepare-only')
        # deadline is still a required CLI contract of the accepted runner; use a
        # non-market placeholder only in prepare-only mode because no odds fetch occurs.
        cmd += ['--deadline-jst',a.deadline_jst or '23:59:59']
    else:
        if not a.deadline_jst:
            raise FullAutoLiveError('--deadline-jst is required unless --prepare-only')
        cmd += ['--deadline-jst',a.deadline_jst]

    print(json.dumps({'status':'UPSTREAM_READY','race_code':z['race_code'],'PRE':z['PRE'],'POST':z['POST'],
                      'ENV_ENTRY':z['ENV_ENTRY'],'source_out':a.source_out,'prepare_only':a.prepare_only},ensure_ascii=False))
    cp=subprocess.run(cmd,check=False)
    raise SystemExit(cp.returncode)


if __name__=='__main__':
    main()
