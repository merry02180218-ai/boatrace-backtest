#!/usr/bin/env python3
"""Research-only LIVE PRE scanner for frozen HEAD4 120R line.

Target:
- emit a user-facing PRE shortlist before exhibition;
- keep a wider internal monitoring parent for later post-exhibition 120R scoring;
- never read target-day or September-2026 result files.

LIVE causal discipline
----------------------
The wide-parent motor/player histories may use completed prior dates, including
September, through target_date-1. Target-date results/payouts are never read.
Current race-card data is allowed because it is pre-result input.

The v250 PRE scorer keeps its frozen label-fit cutoff through 2026-06-30 for
research compatibility, while its causal feature state may advance through prior
completed dates.

User-facing display:
  monitoring_parent AND (head_prob >= .18 OR v250_PRE >= .12)
Missing head_prob is fail-open/displayed with a warning.

The display shortlist is NOT a hard final gate. Post-exhibition scoring must still
scan every monitoring_parent row.
"""
from __future__ import annotations

import argparse, csv, json, math
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from backtest import rows, race_features
from backtest_v4 import add_features, score4v4, clean_name
from analyze_v250_4head_rebuild_baseline import pre_features, make_model
import scan_4head_v291_pre_live as v291pre

ROOT=Path(__file__).resolve().parent
HEAD_ART=ROOT/'artifacts'/'head4_racecard_headprob_frozen_20260630.json'
STATE_START=date(2025,10,1)
STATE_END=date(2026,8,31)
WIN_CUT=-0.0299361318939513
REN2_CUT=-7.080000000000001
PLAYER_CUT=.215605
HEADPROB_DISPLAY=.18
V250_DISPLAY=.12
ULTRALOW_SHADOW_CUT=.10

VENUE_NAMES={
 1:'桐生',2:'戸田',3:'江戸川',4:'平和島',5:'多摩川',6:'浜名湖',
 7:'蒲郡',8:'常滑',9:'津',10:'三国',11:'びわこ',12:'住之江',
 13:'尼崎',14:'鳴門',15:'丸亀',16:'児島',17:'宮島',18:'徳山',
 19:'下関',20:'若松',21:'芦屋',22:'福岡',23:'唐津',24:'大村'
}

def ff(x, default=np.nan):
    try:
        if x is None:return default
        s=str(x).replace('%','').strip()
        if s=='':return default
        v=float(s)
        return v if np.isfinite(v) else default
    except Exception:
        return default

def ii(x, default=0):
    try:return int(float(str(x).strip()))
    except Exception:return default

def rc(x):
    s=str(x).strip()
    if s.endswith('.0'):s=s[:-2]
    return s.zfill(12)

def resolve_date(arg):
    s=arg or datetime.now(ZoneInfo('Asia/Tokyo')).strftime('%Y-%m-%d')
    return datetime.strptime(s,'%Y-%m-%d').date()

def local_rows(path):
    with Path(path).open(encoding='utf-8-sig',newline='') as f:
        return list(csv.DictReader(f))

def venue(card):
    return str(card.get('レース場コード','')).zfill(2)

def mkey(card,b):
    return venue(card),str(card.get(f'艇{b}_モーター番号','')).strip()

def load_daily_parent_state(path,day):
    obj=json.loads(Path(path).read_text(encoding='utf-8'))
    if obj.get('schema')!='head4_120r_daily_state_v1':
        raise RuntimeError('daily-state schema mismatch')
    if obj.get('target_date')!=str(day):
        raise RuntimeError(f"daily-state target mismatch {obj.get('target_date')} != {day}")
    if obj.get('target_date_results_used') is not False:
        raise RuntimeError('daily-state target-date contamination')
    mh={}
    for k,v in (obj.get('motors') or {}).items():
        if '|' not in k:
            continue
        venue_code,motor_no=k.split('|',1)
        mh[(venue_code,motor_no)]=[int(v.get('w',0)),int(v.get('n',0))]
    ph={}
    for reg,v in (obj.get('players') or {}).items():
        ph[str(reg)]=[int(v.get('w',0)),int(v.get('n',0))]
    return mh,ph,obj

def build_frozen_aug31_state():
    """Build player and motor win histories through Aug-31 only.

    This intentionally never opens any September results.
    """
    motor_hist=defaultdict(lambda:[0,0])
    player_hist=defaultdict(lambda:[0,0])
    d=STATE_START
    while d<=STATE_END:
        ymd=d.strftime('%Y/%m/%d')
        cards=rows(f'data/programs/race_cards/{ymd}.csv')
        rmap={rc(r.get('レースコード','')):r for r in rows(f'data/results/realtime/{ymd}.csv')}
        for card in cards:
            rr=rmap.get(rc(card.get('レースコード','')),{})
            winner=ii(rr.get('1着_艇番'))
            if winner not in range(1,7):
                continue
            for b in range(1,7):
                mk=mkey(card,b)
                if mk[1]:
                    motor_hist[mk][1]+=1
                    motor_hist[mk][0]+=int(winner==b)
                reg=str(card.get(f'艇{b}_登録番号','')).strip()
                if reg:
                    player_hist[reg][1]+=1
                    player_hist[reg][0]+=int(winner==b)
        d+=timedelta(days=1)
    return motor_hist,player_hist

def frozen_parent_features(card,motor_hist,player_hist):
    a4=motor_hist.get(mkey(card,4),(0,0)); a3=motor_hist.get(mkey(card,3),(0,0))
    mw4=a4[0]/a4[1] if a4[1] else np.nan
    mw3=a3[0]/a3[1] if a3[1] else np.nan
    motor_win_diff=mw4-mw3 if np.isfinite(mw4) and np.isfinite(mw3) else np.nan
    motor_2ren_diff=ff(card.get('艇4_モーター2連対率'))-ff(card.get('艇3_モーター2連対率'))
    reg4=str(card.get('艇4_登録番号','')).strip()
    ph=player_hist.get(reg4,(0,0))
    player4=ph[0]/ph[1] if ph[1] else np.nan
    miss_motor_win=not np.isfinite(motor_win_diff)
    miss_motor_2ren=not np.isfinite(motor_2ren_diff)
    miss_player=not np.isfinite(player4)
    missing=miss_motor_win or miss_motor_2ren or miss_player
    parent=(missing or (
        motor_win_diff>=WIN_CUT and motor_2ren_diff>=REN2_CUT and player4>=PLAYER_CUT
    ))
    return {
      'motor_win_diff_4v3':motor_win_diff,
      'motor_2ren_diff_4v3':motor_2ren_diff,
      'player4_all_win_prior':player4,
      'parent_missing_motor_win':int(miss_motor_win),
      'parent_missing_motor_2ren':int(miss_motor_2ren),
      'parent_missing_player':int(miss_player),
      'parent_feature_missing':int(missing),
      'monitoring_parent':int(parent),
    }

def raw_card_features(card):
    vals={}
    specs={
      'national_win':'全国勝率','national_top2':'全国2連対率','national_top3':'全国3連対率',
      'local_win':'当地勝率','local_top2':'当地2連対率','local_top3':'当地3連対率',
      'motor_top2':'モーター2連対率','motor_top3':'モーター3連対率',
      'boat_top2':'ボート2連対率','boat_top3':'ボート3連対率',
      'avg_st':'全国平均ST','flying':'F本数','late':'L本数',
    }
    for b in range(1,7):
        for key,jp in specs.items():
            vals[f'b{b}_{key}']=ff(card.get(f'艇{b}_{jp}'))
    return vals

def load_head_model():
    a=json.loads(HEAD_ART.read_text())
    assert a['feature_count']==78
    assert a['fit_period']['max_date']=='2026-06-30'
    assert a['jul_aug_labels_used_for_fit'] is False
    assert a['september_labels_used'] is False
    return a

def frozen_head_prob(card,a):
    raw=raw_card_features(card)
    z=0.0
    missing=0
    for i,f in enumerate(a['features']):
        v=raw.get(f,np.nan)
        if not np.isfinite(v):
            v=float(a['imputer_median'][i]); missing+=1
        v=(v-float(a['scaler_mean'][i]))/float(a['scaler_scale'][i])
        z+=float(a['coef'][i])*v
    z+=float(a['intercept'])
    p=1/(1+math.exp(-z))
    return p,missing

def v250_scores(day,cards,waku):
    # Existing audited frozen fit: labels through Jun-30 only.
    tr,cache,hist=v291pre.training_and_state(day)
    current=[]
    for r in cards:
        code=rc(r.get('レースコード',''))
        w=waku.get(code,{})
        x=add_features(race_features(r,w),r,cache,hist)
        s4=score4v4(x)
        z={'race_code':code}; z.update(pre_features(x,s4)); current.append(z)
    q=pd.DataFrame(current)
    if q.empty or tr.empty or tr.y4head.nunique()<2:
        raise RuntimeError('invalid v250 PRE fit/current rows')
    model=make_model(v291pre.PRE_COLS)
    model.fit(tr[v291pre.PRE_COLS],tr.y4head.astype(int))
    q['v250_PRE']=model.predict_proba(q[v291pre.PRE_COLS])[:,1]
    return dict(zip(q.race_code,q.v250_PRE))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--date');ap.add_argument('--daily-state');args=ap.parse_args()
    day=resolve_date(args.date)
    if day<date(2026,9,1):
        raise RuntimeError('LIVE trial scanner is intended for September+ only')
    day8=day.strftime('%Y%m%d')
    inp=ROOT/'current_input'/'v291'/day8
    cp=inp/'race_cards.csv'; wp=inp/'waku10.csv'
    if not cp.exists() or not wp.exists():
        raise RuntimeError(f'missing current PRE inputs under {inp}')

    cards=local_rows(cp)
    waku={rc(r.get('レースコード','')):r for r in local_rows(wp)}
    if not cards or len(waku)!=len(cards):
        raise RuntimeError(f'invalid current inputs cards={len(cards)} waku={len(waku)}')

    if args.daily_state:
        motor_hist,player_hist,daily_meta=load_daily_parent_state(args.daily_state,day)
        parent_state_cutoff=daily_meta.get('history_end')
        september_prior_history_allowed=bool(daily_meta.get('september_prior_results_allowed'))
    else:
        motor_hist,player_hist=build_frozen_aug31_state()
        daily_meta={}
        parent_state_cutoff='2026-08-31'
        september_prior_history_allowed=False
    ha=load_head_model()
    p250=v250_scores(day,cards,waku)

    out=[]
    for card in cards:
        code=rc(card.get('レースコード',''))
        row={
          'date':str(day),'race_code':code,
          'jcd':int(code[8:10]),'rno':int(code[10:12]),
          'venue':VENUE_NAMES.get(int(code[8:10]),f'JCD{code[8:10]}'),
          'boat4_name':str(card.get('艇4_選手名','')).strip(),
        }
        row.update(frozen_parent_features(card,motor_hist,player_hist))
        hp,miss=frozen_head_prob(card,ha)
        row['head_prob']=hp;row['headprob_missing_features']=miss
        row['v250_PRE']=float(p250.get(code,np.nan))
        display=(row['monitoring_parent']==1 and (
            hp>=HEADPROB_DISPLAY or row['v250_PRE']>=V250_DISPLAY or miss>0
        ))
        row['display_candidate']=int(display)
        if row['parent_feature_missing']:
            reason='PARENT_MISSING_FAIL_OPEN'
        elif hp>=HEADPROB_DISPLAY and row['v250_PRE']>=V250_DISPLAY:
            reason='HEADPROB+V250'
        elif hp>=HEADPROB_DISPLAY:
            reason='HEADPROB'
        elif row['v250_PRE']>=V250_DISPLAY:
            reason='V250_RESCUE'
        elif miss>0:
            reason='HEADPROB_MISSING_FAIL_OPEN'
        else:
            reason='WATCH_ONLY'
        row['pre_reason']=reason
        # Operational reporting class only: ultra-low head probability stays monitored,
        # but must never be mixed into normal newfeature BET performance.
        row['ultralow_shadow']=int(row['monitoring_parent']==1 and hp<ULTRALOW_SHADOW_CUT)
        row['operational_class']='超低頭確率Shadow' if row['ultralow_shadow'] else ('内部ウォッチ' if row['monitoring_parent']==1 else '見送り')
        out.append(row)

    df=pd.DataFrame(out).sort_values(['display_candidate','head_prob','v250_PRE'],
                                    ascending=[False,False,False]).reset_index(drop=True)
    disp=df[df.display_candidate.eq(1)].copy()
    watch=df[df.monitoring_parent.eq(1)].copy()

    outdir=ROOT/'live_outputs'/'head4_120r_pre'/day8
    outdir.mkdir(parents=True,exist_ok=True)
    df.to_csv(outdir/'pre_all.csv',index=False)
    disp.to_csv(outdir/'pre_display.csv',index=False)
    watch.to_csv(outdir/'pre_monitoring_parent.csv',index=False)

    audit={
      'policy':'HEAD4_120R_PRE_DISPLAY_RESEARCH',
      'target_date':str(day),
      'target_day_results_read':False,
      'target_day_results_read':False,
      'september_prior_history_allowed':september_prior_history_allowed,
      'motor_player_state_cutoff':parent_state_cutoff,
      'racecard_headprob_fit_cutoff':'2026-06-30',
      'v250_fit_label_cutoff':'2026-06-30',
      'current_exhibition_used':False,
      'current_odds_used':False,
      'current_rows':len(df),
      'monitoring_parent_R':len(watch),
      'display_R':len(disp),
      'parent_missing_any_R':int(df.parent_feature_missing.sum()),
      'parent_missing_motor_win_R':int(df.parent_missing_motor_win.sum()),
      'parent_missing_motor_2ren_R':int(df.parent_missing_motor_2ren.sum()),
      'parent_missing_player_R':int(df.parent_missing_player.sum()),
      'display_rule':'monitoring_parent AND (head_prob>=.18 OR v250_PRE>=.12); missing headprob fail-open',
      'ultralow_shadow_rule':'monitoring_parent AND head_prob < .10; reporting-only separation from normal newfeature performance',
      'ultralow_shadow_R':int(df.ultralow_shadow.sum()),
      'display_is_hard_gate':False,
      'production_changed':False,
    }
    (outdir/'audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n')

    L=[f'# {day} 4号艇120R 事前候補 LIVE試験','',
       f'- 全レース: {len(df)}R',
       f'- 内部監視候補: {len(watch)}R',
       f'- 表示用事前候補: **{len(disp)}R**',
       f'- 親条件欠損: {int(df.parent_feature_missing.sum())}R（motor_win {int(df.parent_missing_motor_win.sum())} / motor2連 {int(df.parent_missing_motor_2ren.sum())} / player {int(df.parent_missing_player.sum())}）',
       f'- 展示・直前オッズは不使用。親履歴は {parent_state_cutoff} までの完了レースを使用。',
       '- 表示外でも内部監視候補は展示後の最終判定対象。',
       '',
       '|場|R|4号艇|head_prob|v250 PRE|理由|',
       '|---|---:|---|---:|---:|---|']
    for _,r in disp.sort_values(['jcd','rno']).iterrows():
        L.append(f"|{r.venue}|{int(r.rno)}R|{r.boat4_name}|{r.head_prob:.3f}|{r.v250_PRE:.3f}|{r.pre_reason}|")
    md='\n'.join(L)+'\n'
    (outdir/'pre_display.md').write_text(md,encoding='utf-8')
    print(md)
    print('HEAD4_120R_PRE_LIVE_TRIAL_OK')
    print('TARGET_DAY_RESULTS_UNREAD')
    print('本番変更なし')

if __name__=='__main__':
    main()
