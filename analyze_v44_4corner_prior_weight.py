"""v44: optimize prior1/prior2 weighting for 4-corner makuri using v43 output.
Train chooses cutoff separately for each weighting; validation is primary decision set.
"""
import csv
WEIGHTS=[(1.0,0.0),(.8,.2),(.6,.4),(.4,.6)]

def read():
    with open('analysis_v43_prior2_lane_corrected.csv',encoding='utf-8-sig') as f:
        return [r for r in csv.DictReader(f) if r['model']=='4カドまくり' and int(r['has2'])]

def rate(a): return 100*sum(int(x['target']) for x in a)/len(a) if a else 0

def main():
    a=read(); results=[]
    for w1,w2 in WEIGHTS:
        key=f'{int(w1*100)}:{int(w2*100)}'
        for r in a:r[key]=w1*float(r['prior1'])+w2*float(r['prior2'])
        tr=sorted(float(r[key]) for r in a if r['period']=='train')
        cut=tr[int(.60*(len(tr)-1))] if tr else .5
        for p in ['train','validation','latest_month']:
            base=[r for r in a if r['period']==p]
            sel=[r for r in base if float(r[key])>=cut]
            results.append((key,cut,p,len(base),rate(base),len(sel),rate(sel)))
    # choose weight on train only: highest selected target rate, tie-break more samples
    trrows=[x for x in results if x[2]=='train']
    best=max(trrows,key=lambda x:(x[6],x[5]))[0]
    L=['# v44 4カドまくり 前走・前々走ウェイト最適化','',f'学習期間だけで選んだ最良ウェイト: **{best}**','上位40% cutoffは各ウェイトごとにtrainだけで決定。validationを採用判断の最優先とする。','','|前走:前々走|期間|母数R/率|上位R/率|差|','|---|---|---:|---:|---:|']
    for key,cut,p,n,br,sn,sr in results:
        L.append(f'|{key}|{p}|{n}R/{br:.1f}%|{sn}R/{sr:.1f}%|{sr-br:+.1f}pt|')
    L+=['','## 判定ルール','- trainで選択したウェイトがvalidationでも改善する場合のみ正式採用候補。','- latest_monthは反復検証済みのため参考値。','- 実進入・艇N_コースは使用しない。元データv43は過去走の当時枠で展示/オリジナル展示を補正済み。']
    open('summary_v44_4corner_prior_weight.md','w',encoding='utf-8').write('\n'.join(L)+'\n')
    with open('analysis_v44_4corner_prior_weight.csv','w',newline='',encoding='utf-8-sig') as f:
        w=csv.writer(f);w.writerow(['weight','cutoff','period','base_n','base_rate','selected_n','selected_rate']);w.writerows(results)
if __name__=='__main__':main()
