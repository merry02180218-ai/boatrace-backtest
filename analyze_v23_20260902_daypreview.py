import csv
from statistics import mean
from backtest import rows

DATE='2026-09-02'
YMD='2026/09/02'

# Fixed before reading 9/2 outcomes. Preview/venue are supplemental only, never hard candidate gates.
# Percentile-like race-relative scores: 1.0 = best in the six boats, 0.0 = worst.
def f(x):
    try:return float(x)
    except:return None

def rank_score(vals, boat, lower=True):
    arr=[(j,v) for j,v in vals.items() if v is not None]
    if boat not in vals or vals[boat] is None or len(arr)<2:return 0.5
    s=sorted(arr,key=lambda z:z[1],reverse=not lower)
    pos=[j for j,(b,_) in enumerate(s) if b==boat][0]
    return 1-pos/(len(s)-1)

def by_code(path):
    return {r['レースコード']:r for r in rows(path) if r.get('レースコード')}

def venue_map():
    out={}
    try:
        with open('venue_model_index_v22.csv',encoding='utf-8-sig') as fh:
            for r in csv.DictReader(fh):out[(r['model'],str(r['venue']).zfill(2))]=f(r['venue_index']) or 1.0
    except FileNotFoundError:pass
    return out

def venue_score(idx):
    return max(0.0,min(1.0,0.5+(idx-1.0)))

def original_scores(r,boat):
    if not r:return {'lap':0.5,'turn':0.5,'straight':0.5,'avg':0.5}
    labels=[r.get('計測項目1',''),r.get('計測項目2',''),r.get('計測項目3','')]
    scores=[]; ret={'lap':0.5,'turn':0.5,'straight':0.5}
    for k,label in enumerate(labels,1):
        if not label:continue
        vals={b:f(r.get(f'艇{b}_値{k}')) for b in range(1,7)}
        sc=rank_score(vals,boat,True)
        scores.append(sc)
        lab=label.replace(' ','').replace('　','')
        if '直線' in lab:ret['straight']=sc
        elif 'まわり' in lab or '回り' in lab or 'ターン' in lab:ret['turn']=sc
        elif '一周' in lab or '周' in lab or 'ラップ' in lab:ret['lap']=sc
    ret['avg']=mean(scores) if scores else 0.5
    return ret

def preview_for(model,code,venue,tkz,stt,orig,vidx):
    head=3 if model.startswith('3') else 4 if model=='4カドまくり' else 5
    tr=tkz.get(code,{}); sr=stt.get(code,{}); orr=orig.get(code,{})
    exvals={b:f(tr.get(f'艇{b}_展示タイム')) for b in range(1,7)}
    ex=rank_score(exvals,head,True)
    stvals={b:f(sr.get(f'艇{b}_スタート展示')) for b in range(1,7)}
    st=rank_score(stvals,head,True)
    actual_course={b:int(f(sr.get(f'艇{b}_コース')) or 0) for b in range(1,7)}
    entry=1.0 if actual_course.get(head)==head else 0.35
    os=original_scores(orr,head)
    vi=vidx.get((model,str(venue).zfill(2)),1.0); vs=venue_score(vi)
    if model=='3まくり':
        comp=.25*ex+.25*st+.20*os['straight']+.15*os['avg']+.10*entry+.05*vs
    elif model=='3まくり差し':
        comp=.15*ex+.20*st+.15*os['lap']+.25*os['turn']+.10*os['avg']+.10*entry+.05*vs
    elif model=='4カドまくり':
        comp=.25*ex+.25*st+.20*os['straight']+.15*os['avg']+.10*entry+.05*vs
    else:
        ex4=rank_score(exvals,4,True); st4=rank_score(stvals,4,True); o4=original_scores(orr,4)
        e45=1.0 if actual_course.get(4)==4 and actual_course.get(5)==5 else 0.35
        attack4=.30*ex4+.35*st4+.20*o4['straight']+.15*o4['avg']
        take5=.20*ex+.15*st+.25*os['lap']+.25*os['turn']+.15*os['avg']
        comp=.40*attack4+.45*take5+.10*e45+.05*vs
    adj=(comp-.5)*10.0
    grade='S' if comp>=.67 else ('A' if comp>=.55 else 'B')
    return {'preview_comp':comp,'preview_adj':adj,'grade':grade,'ex_score':ex,'st_score':st,'entry_score':entry,
            'orig_lap':os['lap'],'orig_turn':os['turn'],'orig_straight':os['straight'],'orig_avg':os['avg'],'venue_index':vi}

def main():
    with open('races_v20.csv',encoding='utf-8-sig') as fh:
        base=[r for r in csv.DictReader(fh) if r.get('date')==DATE]
    tkz=by_code(f'data/previews/tkz/{YMD}.csv'); stt=by_code(f'data/previews/stt/{YMD}.csv'); orig=by_code(f'data/previews/original_exhibition/{YMD}.csv'); vidx=venue_map()
    out=[]
    for r in base:
        p=preview_for(r['model'],r['race_code'],r.get('venue',''),tkz,stt,orig,vidx)
        z=dict(r);z.update({k:(round(v,3) if isinstance(v,float) else v) for k,v in p.items()});z['adjusted_score']=round((f(r.get('score')) or 0)+p['preview_adj'],2);out.append(z)
    if out:
        with open('races_v23_20260902.csv','w',newline='',encoding='utf-8-sig') as fh:
            w=csv.DictWriter(fh,fieldnames=sorted(set().union(*(r.keys() for r in out))));w.writeheader();w.writerows(out)
    L=['# v23 2026-09-02 当日展示・オリジナル展示・場補正 診断','',
       '対象はv20で結果確認前に候補化するルールを9/2へ適用した候補。9/2は既に開発期間で結果を見ているため、これは未使用ホールドアウトではなく診断。',
       '当日補正は候補の足切りには使わず、展示タイム・展示ST・実進入・オリジナル展示・v22場指数を固定ウェイトで合成し、基礎scoreへ最大およそ±5点の補助加点/減点。','',
       '## 全体/グレード別','|区分|R|狙い成立|成立率|3連単的中|的中率|払戻|回収率(5,000円/R換算)|','|---|---:|---:|---:|---:|---:|---:|---:|']
    def add(label,rs):
        n=len(rs);hh=sum(int(r.get('head_hit') or 0) for r in rs);bh=sum(int(r.get('bet_hit') or 0) for r in rs);ret=sum(int(float(r.get('return') or 0)) for r in rs);roi=100*ret/(n*5000) if n else 0
        L.append(f'|{label}|{n}|{hh}|{hh/n*100 if n else 0:.1f}%|{bh}|{bh/n*100 if n else 0:.1f}%|{ret:,}円|{roi:.1f}%|')
    add('全候補',out)
    for g in ['S','A','B']:add(g,[r for r in out if r['grade']==g])
    L+=['','## モデル別','|モデル|R|S/A|狙い成立|成立率|3連単的中|払戻|回収率|','|---|---:|---:|---:|---:|---:|---:|---:|']
    for m in ['3まくり','3まくり差し','4カドまくり','5頭展開']:
        rs=[r for r in out if r['model']==m];n=len(rs);sa=sum(r['grade'] in ('S','A') for r in rs);hh=sum(int(r.get('head_hit') or 0) for r in rs);bh=sum(int(r.get('bet_hit') or 0) for r in rs);ret=sum(int(float(r.get('return') or 0)) for r in rs);roi=100*ret/(n*5000) if n else 0
        L.append(f'|{m}|{n}|{sa}|{hh}|{hh/n*100 if n else 0:.1f}%|{bh}|{ret:,}円|{roi:.1f}%|')
    L+=['','## S/A候補一覧','|モデル|場|R|grade|基礎score|補正後|展示|展示ST|一周|回り足|直線|場指数|狙い成立|3連単的中|','|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for r in sorted([x for x in out if x['grade'] in ('S','A')],key=lambda x:(x['model'],-float(x['adjusted_score']))):
        L.append(f"|{r['model']}|{r.get('venue','')}|{r.get('race','')}|{r['grade']}|{r.get('score','')}|{r['adjusted_score']}|{r['ex_score']}|{r['st_score']}|{r['orig_lap']}|{r['orig_turn']}|{r['orig_straight']}|{r['venue_index']}|{r.get('head_hit','0')}|{r.get('bet_hit','0')}|")
    open('analysis_v23_20260902.md','w',encoding='utf-8').write('\n'.join(L)+'\n')
if __name__=='__main__':main()
