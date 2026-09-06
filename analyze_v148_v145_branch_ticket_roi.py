from __future__ import annotations
import csv
from collections import defaultdict,Counter

PRED='analysis_v145_one_gate_specialized_non1.csv'
SRC1='analysis_v110_1head_role_tickets.csv'
SRC35='analysis_v97_3head5head_second_third.csv'
SRC4='analysis_v93_4corner_second_third.csv'
OUT='analysis_v148_v145_branch_ticket_roi.csv'
SUMMARY='summary_v148_v145_branch_ticket_roi.md'


def ff(x,d=0.0):
    try:return float(x)
    except:return d

def ii(x,d=0):
    try:return int(float(x))
    except:return d

def read(path):
    with open(path,encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def code(r):return (r.get('race_code') or '').strip()
def idx(rows):
    d=defaultdict(list)
    for r in rows:
        if code(r):d[code(r)].append(r)
    return d

def combo(r):
    v=(r.get('actual_combo') or r.get('actual_trifecta') or '').strip()
    if v.count('-')==2:return v
    a,b,c=ii(r.get('winner')),ii(r.get('second')),ii(r.get('third'))
    return f'{a}-{b}-{c}' if a and b and c else ''
def payout(r):return ii(r.get('payout100'),0)
def ranked(r,key):return [ii(x) for x in (r.get(key) or '').split('-') if ii(x)]

def current6(head,rr):
    sec=rr[:2];third=rr[:4]
    return [f'{head}-{a}-{b}' for a in sec for b in third if a!=b]
def current7_4(rr):
    # CURRENT 4C: role/value shadowを使わず、現行相手順位のpair orderから7点。
    pairs=[f'4-{a}-{b}' for a in rr for b in rr if a!=b]
    return pairs[:7]
def pick35(rows,branch):
    want='5HEAD' if branch=='5頭' else '3HEAD'
    for r in rows or []:
        if (r.get('group_v97') or '').upper()==want:return r
    return None

def settle(p,i1,i35,i4):
    c=code(p);b=p.get('pred145','');conf=ff(p.get('conf145'))
    if b=='その他':return None
    if b=='1逃げ':
        src=(i1.get(c) or [None])[0]
        if not src:return {'race_code':c,'branch':b,'confidence':conf,'status':'NO_SOURCE'}
        act=combo(src);pay=payout(src);rk=ii(src.get('v110_rank20'),0)
        if not act or pay<=0 or rk<=0:return {'race_code':c,'branch':b,'confidence':conf,'status':'UNSETTLED'}
        tsn=7;hit=int(rk<=7);logic='v110_top7'
    elif b in ('3まくり','3まくり差し','5頭'):
        src=pick35(i35.get(c),b)
        if not src:return {'race_code':c,'branch':b,'confidence':conf,'status':'NO_SOURCE'}
        act=combo(src);pay=payout(src);rr=ranked(src,'ranked_others_v97')
        if not act or pay<=0 or len(rr)<5:return {'race_code':c,'branch':b,'confidence':conf,'status':'UNSETTLED'}
        ts=current6(3 if b!='5頭' else 5,rr);tsn=len(ts);hit=int(act in ts);logic='CURRENT_v51_6'
    elif b=='4カド':
        src=(i4.get(c) or [None])[0]
        if not src:return {'race_code':c,'branch':b,'confidence':conf,'status':'NO_SOURCE'}
        act=combo(src);pay=payout(src);rr=ranked(src,'ranked_others_v93')
        if not act or pay<=0 or len(rr)<5:return {'race_code':c,'branch':b,'confidence':conf,'status':'UNSETTLED'}
        ts=current7_4(rr);tsn=len(ts);hit=int(act in ts);logic='CURRENT_4C_7'
    else:return None
    inv=tsn*100;ret=pay if hit else 0
    return {'race_code':c,'branch':b,'confidence':conf,'status':'SETTLED','logic':logic,'points':tsn,'actual_combo':act,'hit':hit,'invest':inv,'return':ret,'payout100':pay}

def stats(rows):
    q=[r for r in rows if r.get('status')=='SETTLED'];n=len(q);h=sum(ii(r.get('hit')) for r in q);inv=sum(ii(r.get('invest')) for r in q);ret=sum(ii(r.get('return')) for r in q)
    return n,h,100*h/n if n else 0,100*ret/inv if inv else 0,inv,ret

def main():
    pred=read(PRED);i1=idx(read(SRC1));i35=idx(read(SRC35));i4=idx(read(SRC4));out=[]
    for p in pred:
        z=settle(p,i1,i35,i4)
        if z:out.append(z)
    fs=['race_code','branch','confidence','status','logic','points','actual_combo','hit','invest','return','payout100']
    with open(OUT,'w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fs);w.writeheader();w.writerows([{k:r.get(k,'') for k in fs} for r in out])
    L=['# v148 v145分岐 × 現行買い目 3連単ROI（修正版）','',
       '- 対象: v145の8月完全ホールドアウト。','- v145分岐は固定し、その後に現行ticket layerを接続。結果/払戻はticket freeze後のsettlementのみ。',
       '- ①逃げ: v110上位7点。','- ③頭: CURRENT v51 6点（v100 shadow不使用）。','- ④カド: CURRENT相手順位7点（v106 shadow不使用）。','- ⑤頭: CURRENT v51 6点。','- その他: SKIP。','',
       '## 全分岐 aggregate','|条件|R|的中|的中率|投資|払戻|ROI|','|---|---:|---:|---:|---:|---:|---:|']
    for th in [0,.30,.40,.50,.60]:
        q=[r for r in out if r.get('status')=='SETTLED' and ff(r.get('confidence'))>=th]
        n,h,hr,roi,inv,ret=stats(q);lab='全て' if th==0 else f'p>={th:.2f}';L.append(f'|{lab}|{n}|{h}|{hr:.1f}%|{inv:,}円|{ret:,}円|{roi:.1f}%|')
    L+=['','## 分岐別','|分岐|R|的中|的中率|投資|払戻|ROI|','|---|---:|---:|---:|---:|---:|---:|']
    for b in ['1逃げ','3まくり','3まくり差し','4カド','5頭']:
        n,h,hr,roi,inv,ret=stats([r for r in out if r.get('branch')==b]);L.append(f'|{b}|{n}|{h}|{hr:.1f}%|{inv:,}円|{ret:,}円|{roi:.1f}%|')
    bad=[r for r in out if r.get('status')!='SETTLED'];L+=['',f'- unsettled/source不足: **{len(bad)}R**']
    if bad:L.append('- 内訳: '+', '.join(f'{k}={v}' for k,v in Counter(r.get('status') for r in bad).items()))
    L+=['','※PRE日次top5/構造候補フィルタは含めないbranch-ticket層の検証。9/5実運用全体はv147で別評価。']
    open(SUMMARY,'w',encoding='utf-8').write('\n'.join(L)+'\n')

if __name__=='__main__':main()
