from __future__ import annotations
import csv
from datetime import date
from collections import Counter,defaultdict
import analyze_v141_integrated_pre_scenario as v141
import analyze_v144_pre_final_scenario as v144
import analyze_v145_one_gate_specialized_non1 as v145
import analyze_v148_v145_branch_ticket_roi as v148

OUT='analysis_v152_jun_jul_strict_agreement_roi.csv'
SUMMARY='summary_v152_jun_jul_strict_agreement_roi.md'
S=67.0
FIXED_GATE=.40
NON1=('3まくり','3まくり差し','4カド','5頭')
S35='analysis_v90_exhibition_st_10month.csv'
S4='analysis_v91_st_weight_walkforward.csv'


def read(p):
    with open(p,encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def ff(x,d=None):
    try:
        if x is None or str(x).strip()=='':return d
        return float(x)
    except:return d
def ii(x,d=0):
    try:return int(float(x))
    except:return d
def code(r):return (r.get('race_code') or r.get('レースコード') or '').strip()
def exact_model(b):return {'3まくり':'3まくり','3まくり差し':'3まくり差し','4カド':'4カドまくり','5頭':'5頭展開'}[b]

def score_index():
    out={}
    for r in read(S35):
        c=code(r);m=(r.get('model') or '').strip();sc=ff(r.get('score'))
        if c and m in ('3まくり','3まくり差し','5頭展開') and sc is not None:
            k=(c,m)
            if k not in out or sc>out[k]['score']:out[k]={'score':sc,'entry':ii(r.get('entry_gate_keep'),1)}
    for r in read(S4):
        c=code(r);m=(r.get('model') or '').strip();sc=ff(r.get('score_CORR20_v91'))
        if c and m=='4カドまくり' and sc is not None:
            k=(c,m)
            if k not in out or sc>out[k]['score']:out[k]={'score':sc,'entry':ii(r.get('entry_gate_keep'),1)}
    return out

def month_pred(rows,start,end,train_end):
    q=[z for z in rows if start<=date.fromisoformat(z['date'])<=end]
    gate=v145.fit_gate(rows,train_end);non1=v145.fit_non1(rows,train_end)
    return v145.score_rows(q,gate,non1,FIXED_GATE)

def st(rows):
    q=[r for r in rows if r.get('status')=='SETTLED'];n=len(q);h=sum(ii(r.get('hit')) for r in q);inv=sum(ii(r.get('invest')) for r in q);ret=sum(ii(r.get('return')) for r in q)
    return n,h,100*h/n if n else 0,inv,ret,100*ret/inv if inv else 0

def main():
    hist=v141.build_history();rows=v144.build_final_rows(hist,.45,v141.TRAIN_END)
    jun=month_pred(rows,date(2026,6,1),date(2026,6,30),date(2026,5,31))
    jul=month_pred(rows,date(2026,7,1),date(2026,7,31),date(2026,6,30))
    sidx=score_index();i1=v148.idx(v148.read(v148.SRC1));i35=v148.idx(v148.read(v148.SRC35));i4=v148.idx(v148.read(v148.SRC4))
    out=[]
    for label,preds in [('2026-06',jun),('2026-07',jul)]:
        for p in preds:
            b=p.get('pred145','')
            if b not in NON1:continue
            c=code(p);sm=sidx.get((c,exact_model(b)))
            if not sm or sm['entry']!=1 or sm['score']<S:continue
            z=v148.settle(p,i1,i35,i4) or {'race_code':c,'branch':b,'confidence':p.get('conf145',0),'status':'NO_SOURCE'}
            z.update(month=label,dedicated_score=sm['score'],fixed_gate=FIXED_GATE)
            out.append(z)
    fs=['month','race_code','branch','confidence','dedicated_score','fixed_gate','status','logic','points','actual_combo','hit','invest','return','payout100']
    with open(OUT,'w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fs);w.writeheader();w.writerows([{k:r.get(k,'') for k in fs} for r in out])
    L=['# v152 6月・7月 strict agreement + S67 ROI replay','',
       '- v151で確定したルールを固定: v145非①分岐 + 同一専用モデル構造一致 + entry gate + 専用score S>=67。','- v145 1号艇gateは0.40固定。月ごとの予測モデルは必ず前月末までで学習。','- 6月は5/31までで学習、7月は6/30までで学習。','- ただしgate=0.40自体は後に7月で選ばれた設定なので、6/7月は独立untouched holdoutではなく固定ルールのretrospective再現性チェック。','- 買い目はv148と同じCURRENT ticket layerをそのまま使用。','',
       '## 月別','|月|購入候補|settled|的中|的中率|投資|払戻|ROI|','|---|---:|---:|---:|---:|---:|---:|---:|']
    for m in ('2026-06','2026-07'):
        q=[r for r in out if r['month']==m];n,h,hp,inv,ret,roi=st(q);L.append(f'|{m}|{len(q)}|{n}|{h}|{hp:.1f}%|{inv:,}円|{ret:,}円|{roi:.1f}%|')
    L+=['','## 分岐別（月合算）','|分岐|購入候補|settled|的中|的中率|投資|払戻|ROI|','|---|---:|---:|---:|---:|---:|---:|---:|']
    for b in NON1:
        q=[r for r in out if r['branch']==b];n,h,hp,inv,ret,roi=st(q);L.append(f'|{b}|{len(q)}|{n}|{h}|{hp:.1f}%|{inv:,}円|{ret:,}円|{roi:.1f}%|')
    q=out;n,h,hp,inv,ret,roi=st(q);L+=['',f'- 6-7月合計: 候補 **{len(q)}R** / settled **{n}R** / 的中 **{h}R** / 的中率 **{hp:.1f}%** / ROI **{roi:.1f}%**']
    bad=Counter(r.get('status') for r in out if r.get('status')!='SETTLED')
    if bad:L.append('- 未settled内訳: '+', '.join(f'{k}={v}' for k,v in bad.items()))
    open(SUMMARY,'w',encoding='utf-8').write('\n'.join(L)+'\n');print('\n'.join(L))
if __name__=='__main__':main()
