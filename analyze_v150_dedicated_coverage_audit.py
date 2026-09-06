from __future__ import annotations
import csv
from collections import Counter,defaultdict

P145='analysis_v145_one_gate_specialized_non1.csv'
V148='analysis_v148_v145_branch_ticket_roi.csv'
S35='analysis_v90_exhibition_st_10month.csv'
S4='analysis_v91_st_weight_walkforward.csv'
OUT='analysis_v150_dedicated_coverage_audit.csv'
SUMMARY='summary_v150_dedicated_coverage_audit.md'
S=67.0
NON1=('3まくり','3まくり差し','4カド','5頭')


def read(path):
    with open(path,encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def ff(x,d=None):
    try:
        if x is None or str(x).strip()=='':return d
        return float(x)
    except Exception:return d
def ii(x,d=0):
    try:return int(float(x))
    except Exception:return d
def code(r):return (r.get('race_code') or r.get('レースコード') or '').strip()
def exact_model(b):return {'3まくり':'3まくり','3まくり差し':'3まくり差し','4カド':'4カドまくり','5頭':'5頭展開'}[b]

def build_idx():
    out={}
    by_model=Counter()
    for r in read(S35):
        c=code(r);m=(r.get('model') or '').strip()
        if not c or m not in ('3まくり','3まくり差し','5頭展開'):continue
        sc=ff(r.get('score'))
        if sc is None:continue
        by_model[m]+=1
        k=(c,m)
        if k not in out or sc>out[k]['score']:
            out[k]={'score':sc,'entry':ii(r.get('entry_gate_keep'),1),'source':'v90'}
    for r in read(S4):
        c=code(r);m=(r.get('model') or '').strip()
        if not c or m!='4カドまくり':continue
        sc=ff(r.get('score_CORR20_v91'))
        if sc is None:continue
        by_model[m]+=1
        k=(c,m)
        if k not in out or sc>out[k]['score']:
            out[k]={'score':sc,'entry':ii(r.get('entry_gate_keep'),1),'source':'v91_CORR20'}
    return out,by_model

def settle_stats(rows):
    q=[r for r in rows if ii(r.get('buy'))==1 and ii(r.get('settled'))==1]
    n=len(q);h=sum(ii(r.get('hit')) for r in q);inv=sum(ii(r.get('invest')) for r in q);ret=sum(ii(r.get('return')) for r in q)
    return n,h,(100*h/n if n else 0),(100*ret/inv if inv else 0),inv,ret

def main():
    p=[r for r in read(P145) if (r.get('pred145') or '').strip() in NON1]
    r148={code(r):r for r in read(V148) if code(r)}
    idx,global_counts=build_idx()
    out=[]
    for r in p:
        c=code(r);b=(r.get('pred145') or '').strip();m=exact_model(b);z=idx.get((c,m));s=r148.get(c)
        if z is None:
            status='NO_DEDICATED_CANDIDATE'
            sc='';entry=0;src=''
        elif z['entry']!=1:
            status='ENTRY_FAIL'
            sc=z['score'];entry=z['entry'];src=z['source']
        else:
            status='ELIGIBLE_SCORE'
            sc=z['score'];entry=1;src=z['source']
        buy=int(status=='ELIGIBLE_SCORE' and ff(sc,-999)>=S)
        q={'race_code':c,'branch':b,'dedicated_model':m,'agreement_status':status,'score_source':src,'dedicated_score':sc,'entry_gate':entry,'S67_buy':buy,
           'v148_status':(s or {}).get('status','NO_V148'),'settled':int(bool(s) and s.get('status')=='SETTLED')}
        if q['settled']:
            for k in ('hit','invest','return','points','payout100','actual_combo'):q[k]=(s or {}).get(k,'')
        else:
            for k in ('hit','invest','return','points','payout100','actual_combo'):q[k]=''
        out.append(q)
    fields=['race_code','branch','dedicated_model','agreement_status','score_source','dedicated_score','entry_gate','S67_buy','v148_status','settled','hit','invest','return','points','payout100','actual_combo']
    with open(OUT,'w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(out)

    L=['# v150 専用モデル coverage / agreement audit','',
       '- 対象: v145 8月完全ホールドアウトの非①予測。S=67は事前固定のまま。',
       '- v90はv83で事前固定された構造候補のみを引き継ぐ設計なので、v145分岐に対応するv90/v91行が無いケースを単純な「score欠損」とは扱わず、**専用モデル側が候補化していない=構造不一致**として分離する。',
       '- 結果/払戻はagreementとS判定を凍結した後にv148 settlementから結合。','',
       '## agreement coverage','|分岐|v145非①予測R|専用候補あり|構造一致率|entry fail|S67通過|',
       '|---|---:|---:|---:|---:|---:|']
    for b in NON1:
        q=[r for r in out if r['branch']==b];elig=[r for r in q if r['agreement_status']=='ELIGIBLE_SCORE'];ef=[r for r in q if r['agreement_status']=='ENTRY_FAIL'];sb=[r for r in q if ii(r['S67_buy'])]
        L.append(f'|{b}|{len(q)}|{len(elig)+len(ef)}|{100*(len(elig)+len(ef))/len(q) if q else 0:.1f}%|{len(ef)}|{len(sb)}|')
    L+=['','## S67 strict agreement settlement','|分岐|S67購入R|settled|的中|的中率|投資|払戻|ROI|','|---|---:|---:|---:|---:|---:|---:|---:|']
    for b in NON1:
        q=[r for r in out if r['branch']==b and ii(r['S67_buy'])];n,h,hp,roi,inv,ret=settle_stats(q)
        L.append(f'|{b}|{len(q)}|{n}|{h}|{hp:.1f}%|{inv:,}円|{ret:,}円|{roi:.1f}%|')
    q=[r for r in out if ii(r['S67_buy'])];n,h,hp,roi,inv,ret=settle_stats(q)
    L.append(f'|非①合計|{len(q)}|{n}|{h}|{hp:.1f}%|{inv:,}円|{ret:,}円|{roi:.1f}%|')
    L+=['','## 解釈','- v149で「score coverage」と呼んでいた低率の大部分が、データ欠損なのか専用構造モデルとの不一致なのかを分離するための監査。',
        '- 専用候補が無いレースにSスコアを人工的に補完して購入対象を増やすことはしない。これは現行専用モデルの構造ゲートを壊すため。',
        '- 本採用判断は、構造一致+Sで十分なサンプルが確保できるか、かつROIが期間を跨いで再現するかで行う。']
    open(SUMMARY,'w',encoding='utf-8').write('\n'.join(L)+'\n')
    print('\n'.join(L))

if __name__=='__main__':main()
