#!/usr/bin/env python3
"""Result-blind rescued-row long-survival SES auto seeding v17.

v16 showed that long-horizon template evidence must not override a row that
already passes the v13-equivalent short persistence+direction gate.  v17
therefore starts from v14 and leaves every non-rescued row completely unchanged.
Only rows that v14 had to rescue are revalidated through 1.2 s.  If the v14
chosen rescue does not survive, v17 re-ranks the bounded set of result-blind
2D rescue candidates already produced by v14.

No race result, boat-number special case, race-specific offset, or relaxed
tracker/quality threshold is used.
"""
from __future__ import annotations
import argparse, json, subprocess, sys, tempfile
from pathlib import Path
import cv2
import numpy as np
import auto_seed_exhibition_motion_v9 as v9
import auto_seed_exhibition_motion_v14 as v14

HORIZONS=(.15,.30,.45,.60,.90,1.20)


def long_gate(cap,sec,x,y,dx,width,height):
    ev=v9.eval_seed(cap,sec,x,y,dx,horizons=HORIZONS)
    samples=ev.get('samples',[])
    good=[s for s in samples if s.get('ok') and s.get('matched_center')]
    if not good:
        return ev,{'ok':False,'reason':'no_valid_matches','net_dx':0.0,'survives':False},False
    n_ok=len(good)
    ncc=np.array([float(s.get('ncc',0.0)) for s in samples],float)
    median=float(np.median(ncc)) if len(ncc) else 0.0
    min_ncc=float(np.min(ncc)) if len(ncc) else 0.0
    net=float(good[-1]['matched_center'][0])-float(x)
    if abs(float(dx))<2.5:
        dir_ok=True; reason='dominant_motion_near_zero'
    else:
        dir_ok=bool(net*float(dx)>0.0 and abs(net)>=4.0)
        reason='aligned' if dir_ok else 'opposite_or_static'
    # Last two successful long-horizon matches must remain usable for the later
    # SES tracker rather than drifting into an edge/rail/off-frame texture.
    survives=True
    for s in good[-2:]:
        mx,my=map(float,s['matched_center'])
        if not (30.0<=mx<=width-30.0 and 22.0<=my<=height-22.0):
            survives=False
    visual_ok=bool(n_ok>=5 and median>=.55 and min_ncc>=.35)
    meta={'ok':bool(visual_ok and dir_ok and survives),'reason':reason,'net_dx':round(net,3),
          'survives':bool(survives),'visual_ok':visual_ok,'ok_horizons':int(n_ok),
          'median_ncc':round(median,4),'min_ncc':round(min_ncc,4)}
    return ev,meta,bool(meta['ok'])


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('video',type=Path)
    ap.add_argument('--entry-order',required=True)
    ap.add_argument('--nominal-sec',type=float,default=29.0)
    ap.add_argument('--out',type=Path,default=Path('auto_seed_meta_v17.json'))
    ap.add_argument('--seed-out',type=Path,default=Path('auto_seeds_v17.json'))
    ap.add_argument('--near-best',type=float,default=.05)
    args=ap.parse_args()
    entry=[int(x) for x in args.entry_order.split(',')]
    if sorted(entry)!=[1,2,3,4,5,6]: raise SystemExit('--entry-order must contain 1..6 exactly once')

    with tempfile.TemporaryDirectory() as td:
        td=Path(td); m14=td/'meta14.json'; s14=td/'seeds14.json'
        p=subprocess.run([sys.executable,'auto_seed_exhibition_motion_v14.py',str(args.video),
            '--entry-order',args.entry_order,'--nominal-sec',str(args.nominal_sec),
            '--out',str(m14),'--seed-out',str(s14)])
        if p.returncode!=0 or not m14.exists(): raise SystemExit('FAIL_CLOSED: v14 base seeding failed')
        meta=json.loads(m14.read_text(encoding='utf-8')); seeds=json.loads(s14.read_text(encoding='utf-8'))

    width=float(meta['frame_size'][0]); height=float(meta['frame_size'][1]); sec=float(meta['selected_sec'])
    cap=cv2.VideoCapture(str(args.video))
    if not cap.isOpened(): raise SystemExit('cannot open video')
    xs=np.array([float(seeds[str(b)][0]) for b in entry],float)
    ys=np.array([float(seeds[str(b)][1]) for b in entry],float)
    xunit=float(meta.get('v14_x_unit_px',max(18.0,width/48.0)))
    yunit=float(meta.get('v14_y_unit_px',max(12.0,height/45.0)))
    details={}; reranked=0

    for i,b in enumerate(entry):
        vd=meta.get('v14_details',{}).get(str(b),{})
        if vd.get('decision')!='rescue_2d_direction_or_persistence_failure':
            details[str(b)]={'decision':'preserve_v14_healthy_row','seed':seeds[str(b)]}
            continue
        dx=float(meta['row_details'][str(b)]['dominant_dx'])
        bx,by=map(float,seeds[str(b)])
        raw=[(bx,by,'v14_chosen')]
        st=meta.get('v14_starting_seeds',{}).get(str(b))
        if st: raw.append((float(st[0]),float(st[1]),'v14_start'))
        for c in vd.get('rescue_candidates',[]):
            raw.append((float(c['x']),float(c['y']),'v14_top'))
        uniq=[];seen=set()
        for x,y,src in raw:
            k=(round(x,2),round(y,2))
            if k not in seen: seen.add(k);uniq.append((x,y,src))
        tested=[];passing=[]
        for x,y,src in uniq:
            tx=xs.copy();ty=ys.copy();tx[i]=x;ty[i]=y
            gok,gmeta=v14.row_geometry_ok(tx,ty,i,width,height,.015,.20,.20)
            if not gok: continue
            ev,gm,ok=long_gate(cap,sec,x,y,dx,width,height)
            ex,ey=v14.expected_xy(xs,ys,i,y)
            gres=((x-ex)/max(xunit,1.0))**2+((y-ey)/max(yunit,1.0))**2
            rec={'x':x,'y':y,'source':src,'eval':ev,'gate':gm,'geometry':gmeta,'geom_resid_norm':float(gres)}
            tested.append({'x':round(x,2),'y':round(y,2),'source':src,'ok':ok,
                'score':ev.get('score'),'ok_horizons':gm.get('ok_horizons'),'median_ncc':gm.get('median_ncc'),
                'min_ncc':gm.get('min_ncc'),'net_dx':gm.get('net_dx'),'survives':gm.get('survives'),
                'geom_resid_norm':round(gres,3)})
            if ok: passing.append(rec)
        if not passing:
            cap.release(); raise SystemExit(f'FAIL_CLOSED: no 1.2s surviving v14 rescue candidate for boat {b}')
        best=max(float(c['eval'].get('score',-999.0)) for c in passing)
        near=[c for c in passing if float(c['eval'].get('score',-999.0))>=best-args.near_best]
        chosen=min(near,key=lambda c:(c['geom_resid_norm'],-float(c['eval'].get('score',-999.0))))
        changed=(round(chosen['x'],2)!=round(bx,2) or round(chosen['y'],2)!=round(by,2))
        if changed: reranked+=1
        xs[i]=chosen['x'];ys[i]=chosen['y'];seeds[str(b)]=[round(chosen['x'],2),round(chosen['y'],2)]
        details[str(b)]={'decision':'long_survival_rerank_rescued_row','previous_v14_seed':[bx,by],
            'chosen':{'x':round(chosen['x'],2),'y':round(chosen['y'],2),'source':chosen['source'],
                      'gate':chosen['gate'],'validation':chosen['eval'],'geometry':chosen['geometry']},
            'tested':tested}

    cap.release()
    if not np.array_equal(np.argsort(ys),np.arange(6)): raise SystemExit('FAIL_CLOSED: v17 final y-order changed')
    payload=dict(meta)
    payload.update({'method':'v14 short-gate 2D rescue + 1.2s survival rerank ONLY on v14-rescued rows',
        'v17_result_blind':True,'race_results_read':False,'seeds':seeds,
        'v17_reranked_row_count':reranked,'v17_details':details,
        'warning':'EXPERIMENTAL result-blind seed v17; healthy v14 rows are frozen, only rescued rows receive long-horizon validation.'})
    args.out.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    args.seed_out.write_text(json.dumps(seeds,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(payload,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
