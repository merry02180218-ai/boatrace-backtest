from __future__ import annotations
import csv
from collections import Counter, defaultdict

P145='analysis_v145_one_gate_specialized_non1.csv'
V148='analysis_v148_v145_branch_ticket_roi.csv'
S35='analysis_v90_exhibition_st_10month.csv'
S4='analysis_v91_st_weight_walkforward.csv'
OUT='analysis_v149_branch_agreement_gate.csv'
SUMMARY='summary_v149_branch_agreement_gate.md'
A=55.0
S=67.0
NON1=('3まくり','3まくり差し','4カド','5頭')
ALL=('1逃げ',)+NON1


def read(path):
    with open(path,encoding='utf-8-sig',newline='') as f:
        return list(csv.DictReader(f))

def ff(x,d=None):
    try:
        if x is None or str(x).strip()=='': return d
        return float(x)
    except Exception:return d

def ii(x,d=0):
    try:return int(float(x))
    except Exception:return d

def code(r):return (r.get('race_code') or r.get('レースコード') or '').strip()

def exact_model(branch):
    return {'3まくり':'3まくり','3まくり差し':'3まくり差し','5頭':'5頭展開','4カド':'4カドまくり'}.get(branch,'')

def build_score_index():
    out={}
    # Exact 3m / 3ms / 5head rows from v90; no cross-route dedupe.
    for r in read(S35):
        c=code(r); m=(r.get('model') or '').strip()
        if not c or m not in ('3まくり','3まくり差し','5頭展開'):continue
        sc=ff(r.get('score'))
        if sc is None:continue
        key=(c,m)
        # If duplicate snapshots exist, keep the largest already-frozen pre-result score.
        if key not in out or sc>out[key]['score']:
            out[key]={'score':sc,'entry':ii(r.get('entry_gate_keep'),1),'source':'v90'}
    # Exact 4C current CORR20 score from v91.
    for r in read(S4):
        c=code(r); m=(r.get('model') or '').strip()
        if not c or m!='4カドまくり':continue
        sc=ff(r.get('score_CORR20_v91'))
        if sc is None:continue
        key=(c,m)
        if key not in out or sc>out[key]['score']:
            out[key]={'score':sc,'entry':ii(r.get('entry_gate_keep'),1),'source':'v91_CORR20'}
    return out

def stats(rows):
    q=[r for r in rows if r.get('buy')==1 and r.get('settled')==1]
    n=len(q); h=sum(ii(r.get('hit')) for r in q)
    inv=sum(ii(r.get('invest')) for r in q); ret=sum(ii(r.get('return')) for r in q)
    return {'r':n,'hit':h,'hitp':100*h/n if n else 0.0,'inv':inv,'ret':ret,'roi':100*ret/inv if inv else 0.0}

def main():
    p145={code(r):r for r in read(P145) if code(r)}
    r148={code(r):r for r in read(V148) if code(r)}
    sidx=build_score_index()
    out=[]
    # Freeze agreement/gates using only already-frozen prediction/model score fields.
    # Settlement columns are copied from v148 only after gate decisions are made.
    frozen=[]
    for c,p in p145.items():
        b=(p.get('pred145') or '').strip()
        if b not in ALL:continue
        z={'race_code':c,'branch':b,'confidence':ff(p.get('conf145'),0.0) or 0.0}
        if b=='1逃げ':
            z.update({'score_source':'v148-current-1head','dedicated_score':'','entry_gate':1,'score_found':1})
        else:
            sm=sidx.get((c,exact_model(b)))
            z.update({'score_source':sm['source'] if sm else '','dedicated_score':sm['score'] if sm else '',
                      'entry_gate':sm['entry'] if sm else 0,'score_found':int(sm is not None)})
        frozen.append(z)
    # Gate decisions are fixed before touching hit/return from v148.
    for z in frozen:
        b=z['branch']; sc=ff(z.get('dedicated_score'))
        base = True if b=='1逃げ' else bool(z['score_found'] and z['entry_gate']==1)
        gate={'BRANCH':base,
              'BRANCH+A':(base if b=='1逃げ' else base and sc is not None and sc>=A),
              'BRANCH+S':(base if b=='1逃げ' else base and sc is not None and sc>=S)}
        settled=r148.get(z['race_code'])
        for mode,buy in gate.items():
            q=dict(z);q['mode']=mode;q['buy']=int(buy)
            q['ticket_status']=(settled or {}).get('status','NO_V148')
            q['settled']=int(bool(settled) and settled.get('status')=='SETTLED')
            if q['settled']:
                q['points']=ii(settled.get('points'));q['actual_combo']=settled.get('actual_combo','')
                q['hit']=ii(settled.get('hit'));q['invest']=ii(settled.get('invest'));q['return']=ii(settled.get('return'));q['payout100']=ii(settled.get('payout100'))
            else:
                q.update({'points':'','actual_combo':'','hit':'','invest':'','return':'','payout100':''})
            out.append(q)

    fields=['race_code','branch','confidence','score_source','dedicated_score','entry_gate','score_found','mode','buy','ticket_status','settled','points','actual_combo','hit','invest','return','payout100']
    with open(OUT,'w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows([{k:r.get(k,'') for k in fields} for r in out])

    L=['# v149 v145分岐一致 + 専用モデル A/S ゲート','',
       '- 対象: v145の8月完全ホールドアウト。閾値は事前固定 A=55 / S=67。8月で再調整していない。',
       '- 非①のみ新ゲート: v145分岐と同じ専用モデルの frozen score が一致し、entry gateを通過した時だけ購入候補。',
       '- ③まくり/③差し/⑤頭の専用scoreはv90 exact route、④カドはv91 CORR20。',
       '- 買い目・払戻はv148で凍結済みのCURRENT ticket settlementを再利用。',
       '- ①逃げはv149では変更せず、v148 current 1-head layerをそのまま固定。',
       '- 欠損はSKIP利益扱いにせず、score coverage / ticket settlementを別表示。','']

    L += ['## 非①ゲート比較','|条件|購入判定R|settled R|的中|的中率|投資|払戻|ROI|score欠損|ticket未settled|',
          '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for mode in ('BRANCH','BRANCH+A','BRANCH+S'):
        rr=[r for r in out if r['mode']==mode and r['branch'] in NON1]
        buys=[r for r in rr if r['buy']==1]; st=stats(rr)
        miss=sum(1 for r in rr if not r['score_found'])
        un=sum(1 for r in buys if not r['settled'])
        L.append(f"|{mode}|{len(buys)}|{st['r']}|{st['hit']}|{st['hitp']:.1f}%|{st['inv']:,}円|{st['ret']:,}円|{st['roi']:.1f}%|{miss}|{un}|")

    L += ['','## BRANCH+S 分岐別','|分岐|予測R|score取得|S通過|settled|的中|的中率|投資|払戻|ROI|',
          '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for b in NON1:
        rr=[r for r in out if r['mode']=='BRANCH+S' and r['branch']==b]
        pred=len(rr); sf=sum(ii(r['score_found']) for r in rr); buys=[r for r in rr if r['buy']==1]; st=stats(rr)
        L.append(f"|{b}|{pred}|{sf}|{len(buys)}|{st['r']}|{st['hit']}|{st['hitp']:.1f}%|{st['inv']:,}円|{st['ret']:,}円|{st['roi']:.1f}%|")

    L += ['','## ①逃げを固定した全体比較','|条件|settled購入R|的中|的中率|投資|払戻|ROI|',
          '|---|---:|---:|---:|---:|---:|---:|']
    for mode in ('BRANCH','BRANCH+A','BRANCH+S'):
        rr=[r for r in out if r['mode']==mode];st=stats(rr)
        L.append(f"|{mode}|{st['r']}|{st['hit']}|{st['hitp']:.1f}%|{st['inv']:,}円|{st['ret']:,}円|{st['roi']:.1f}%|")

    # coverage diagnostics
    L += ['','## source coverage','|分岐|v145予測R|専用score取得|取得率|v148 settled|settled率|','|---|---:|---:|---:|---:|---:|']
    for b in NON1:
        rr=[r for r in out if r['mode']=='BRANCH' and r['branch']==b]
        sf=sum(ii(r['score_found']) for r in rr); ss=sum(ii(r['settled']) for r in rr)
        L.append(f"|{b}|{len(rr)}|{sf}|{100*sf/len(rr) if rr else 0:.1f}%|{ss}|{100*ss/len(rr) if rr else 0:.1f}%|")
    L += ['','## 判定ルール','- ROIを最優先し、次に3連単的中率、最後に購入R数を見る。','- source coverageが低い分岐は結論保留。欠損を除外しただけのROI上昇は採用理由にしない。']
    open(SUMMARY,'w',encoding='utf-8').write('\n'.join(L)+'\n')
    print('\n'.join(L),flush=True)

if __name__=='__main__':main()
