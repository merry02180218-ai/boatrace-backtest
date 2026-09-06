from __future__ import annotations
import csv
from collections import defaultdict

PRED='analysis_v145_one_gate_specialized_non1.csv'
SRC1='analysis_v110_1head_role_tickets.csv'
SRC35='analysis_v97_3head5head_second_third.csv'
SRC4='analysis_v93_4corner_second_third.csv'
OUT='analysis_v148_v145_branch_ticket_roi.csv'
SUMMARY='summary_v148_v145_branch_ticket_roi.md'
POINTS={'1逃げ':7,'3まくり':6,'3まくり差し':6,'4カド':7,'5頭':6}


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

def group_pick(rows,want):
    if not rows:return None
    if want in ('3まくり','3まくり差し'):
        for r in rows:
            if (r.get('group_v97') or r.get('group') or '').upper()=='3HEAD':return r
    if want=='5頭':
        for r in rows:
            if (r.get('group_v97') or r.get('group') or '').upper()=='5HEAD':return r
    return rows[0]

def parse_tickets(s):
    s=(s or '').replace('|',';').replace(',',';')
    return [x.strip() for x in s.split(';') if x.strip()]

def actual_combo(r):
    for k in ['actual_combo','result_combo','trifecta','actual']:
        v=(r.get(k) or '').strip()
        if v.count('-')==2:return v
    w=ii(r.get('winner'));s=ii(r.get('second'));t=ii(r.get('third'))
    return f'{w}-{s}-{t}' if w and s and t else ''

def payout(r):
    for k in ['payout100','trifecta_payout100','trifecta_payout','payout']:
        v=ii(r.get(k),0)
        if v>0:return v
    return 0

def rank_from(r,kind,act):
    # exact operational lineage first
    if kind=='1逃げ':
        v=ii(r.get('v110_rank20'),0)
        if v:return v,'v110_rank20'
        for k in ['v110_20','v11020']:
            ts=parse_tickets(r.get(k,''))
            if act in ts:return ts.index(act)+1,k
            if ts:return 999,k
    else:
        # current production order for non-1 branches; v100/v106 remain shadow.
        preferred=['current_rank20','current_rank','current_ticket_rank','rank_current','CURRENT_rank20']
        for k in preferred:
            v=ii(r.get(k),0)
            if v:return v,k
        for k in ['current20','current_20','CURRENT20','current_tickets','tickets_current']:
            ts=parse_tickets(r.get(k,''))
            if ts:return (ts.index(act)+1 if act in ts else 999),k
    return 0,''

def settle(pred, i1,i35,i4):
    c=code(pred); b=pred.get('pred145','')
    if b=='その他':return None
    if b=='1逃げ': src=(i1.get(c) or [None])[0]
    elif b in ('3まくり','3まくり差し','5頭'): src=group_pick(i35.get(c),b)
    elif b=='4カド': src=(i4.get(c) or [None])[0]
    else:return None
    if not src:return {'race_code':c,'branch':b,'confidence':ff(pred.get('conf145')),'status':'NO_SOURCE'}
    act=actual_combo(src);pay=payout(src);rk,col=rank_from(src,b,act);n=POINTS[b]
    if not act or pay<=0 or rk<=0:
        return {'race_code':c,'branch':b,'confidence':ff(pred.get('conf145')),'status':'UNSETTLED','rank_col':col,'actual_combo':act,'payout100':pay}
    hit=int(rk<=n);inv=n*100;ret=pay if hit else 0
    return {'race_code':c,'branch':b,'confidence':ff(pred.get('conf145')),'status':'SETTLED','points':n,'rank':rk,'rank_col':col,'actual_combo':act,'hit':hit,'invest':inv,'return':ret,'payout100':pay}

def stats(rows):
    q=[r for r in rows if r.get('status')=='SETTLED']
    n=len(q);h=sum(ii(r.get('hit')) for r in q);inv=sum(ii(r.get('invest')) for r in q);ret=sum(ii(r.get('return')) for r in q)
    return n,h,(100*h/n if n else 0),(100*ret/inv if inv else 0),inv,ret

def main():
    pred=read(PRED);i1=idx(read(SRC1));i35=idx(read(SRC35));i4=idx(read(SRC4))
    out=[]
    for p in pred:
        z=settle(p,i1,i35,i4)
        if z:out.append(z)
    fs=['race_code','branch','confidence','status','points','rank','rank_col','actual_combo','hit','invest','return','payout100']
    with open(OUT,'w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fs);w.writeheader();w.writerows([{k:r.get(k,'') for k in fs} for r in out])
    L=['# v148 v145分岐 × 現行買い目 3連単ROI','',
       '- 対象: v145の8月完全ホールドアウト。','- 分岐判定はv145のまま固定。結果/払戻は買い目順位確定後のsettlementだけに使用。',
       '- ①逃げ: 採用済みv110上位7点。','- ③頭: CURRENT 6点（v100はshadowのため使わない）。','- ④カド: CURRENT 7点（v106はshadowのため使わない）。','- ⑤頭: CURRENT v51 6点。','- その他: SKIP。','',
       '## 全分岐 aggregate','|条件|R|的中|的中率|投資|払戻|ROI|','|---|---:|---:|---:|---:|---:|---:|']
    for th in [0,.30,.40,.50,.60]:
        q=[r for r in out if r.get('status')=='SETTLED' and ff(r.get('confidence'))>=th]
        n,h,hr,roi,inv,ret=stats(q);label='全て' if th==0 else f'p>={th:.2f}'
        L.append(f'|{label}|{n}|{h}|{hr:.1f}%|{inv:,}円|{ret:,}円|{roi:.1f}%|')
    L+=['','## 分岐別','|分岐|R|的中|的中率|投資|払戻|ROI|','|---|---:|---:|---:|---:|---:|---:|']
    for b in ['1逃げ','3まくり','3まくり差し','4カド','5頭']:
        n,h,hr,roi,inv,ret=stats([r for r in out if r.get('branch')==b])
        L.append(f'|{b}|{n}|{h}|{hr:.1f}%|{inv:,}円|{ret:,}円|{roi:.1f}%|')
    bad=[r for r in out if r.get('status')!='SETTLED']
    L+=['',f'- unsettled/source不足: **{len(bad)}R**']
    if bad:
        from collections import Counter
        L.append('- 内訳: '+', '.join(f'{k}={v}' for k,v in Counter(r.get('status') for r in bad).items()))
    L+=['','※これは「v145分岐へ現行ticket layerを接続した場合」の検証。PRE日次top5/構造候補フィルタは別レイヤーなので、9/5実運用リプレイROI(v147)とは分けて評価する。']
    open(SUMMARY,'w',encoding='utf-8').write('\n'.join(L)+'\n')

if __name__=='__main__':main()
