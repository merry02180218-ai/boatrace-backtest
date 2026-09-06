from __future__ import annotations
import csv

V150='analysis_v150_dedicated_coverage_audit.csv'
V149='analysis_v149_branch_agreement_gate.csv'
OUT='analysis_v151_fix_strict_agreement_settlement.csv'
SUMMARY='summary_v151_fix_strict_agreement_settlement.md'
NON1=('3まくり','3まくり差し','4カド','5頭')


def read(path):
    with open(path,encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def ii(x,d=0):
    try:return int(float(x))
    except Exception:return d
def code(r):return (r.get('race_code') or '').strip()

def main():
    # Selection is NOT redone here. Exact S67 buys are frozen by v150.
    selected=[r for r in read(V150) if ii(r.get('S67_buy'))==1]

    # Settlement repair: v149 already froze the same BRANCH+S gate before outcome join.
    # Join strictly by race_code + branch + mode=BRANCH+S and require SETTLED.
    idx={}
    for r in read(V149):
        if (r.get('mode') or '')!='BRANCH+S':continue
        k=(code(r),(r.get('branch') or '').strip())
        if not k[0]:continue
        if ii(r.get('settled'))==1:
            idx[k]=r
        elif k not in idx:
            idx[k]=r

    out=[]
    for r in selected:
        c=code(r);b=(r.get('branch') or '').strip();s=idx.get((c,b))
        q={
            'race_code':c,'branch':b,'dedicated_score':r.get('dedicated_score',''),
            'agreement_status':r.get('agreement_status',''),'S67_buy':1,
            'join_found':int(s is not None),'settled':int(bool(s) and ii(s.get('settled'))==1),
            'ticket_status':(s or {}).get('ticket_status','NO_V149')
        }
        if q['settled']:
            for k in ('points','actual_combo','hit','invest','return','payout100'):
                q[k]=(s or {}).get(k,'')
        else:
            for k in ('points','actual_combo','hit','invest','return','payout100'):q[k]=''
        out.append(q)

    fields=['race_code','branch','dedicated_score','agreement_status','S67_buy','join_found','settled','ticket_status','points','actual_combo','hit','invest','return','payout100']
    with open(OUT,'w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(out)

    def stats(q):
        settled=[r for r in q if ii(r.get('settled'))==1]
        n=len(settled);h=sum(ii(r.get('hit')) for r in settled)
        inv=sum(ii(r.get('invest')) for r in settled);ret=sum(ii(r.get('return')) for r in settled)
        return n,h,100*h/n if n else 0.0,inv,ret,100*ret/inv if inv else 0.0

    L=['# v151 S67 strict agreement settlement fix','',
       '- v150で凍結済みのS67購入29Rをそのまま使用。レース選択・閾値・scoreは一切再計算していない。',
       '- settlementのみ、同じBRANCH+S条件を凍結済みのv149行へ race_code + branch で厳密結合。',
       '- したがって今回の修正で的中/ROIを見て購入レースが変わることはない。','',
       '## 分岐別','|分岐|S67購入R|join|settled|的中|的中率|投資|払戻|ROI|',
       '|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for b in NON1:
        q=[r for r in out if r['branch']==b]
        n,h,hp,inv,ret,roi=stats(q)
        join=sum(ii(r.get('join_found')) for r in q)
        L.append(f'|{b}|{len(q)}|{join}|{n}|{h}|{hp:.1f}%|{inv:,}円|{ret:,}円|{roi:.1f}%|')
    n,h,hp,inv,ret,roi=stats(out);join=sum(ii(r.get('join_found')) for r in out)
    L.append(f'|非①合計|{len(out)}|{join}|{n}|{h}|{hp:.1f}%|{inv:,}円|{ret:,}円|{roi:.1f}%|')
    L += ['','## 整合性チェック',f'- v150 S67購入R: **{len(selected)}R**',f'- v149 settlement join: **{join}/{len(selected)}R**',f'- settled: **{n}/{len(selected)}R**']
    open(SUMMARY,'w',encoding='utf-8').write('\n'.join(L)+'\n')
    print('\n'.join(L))

if __name__=='__main__':main()
