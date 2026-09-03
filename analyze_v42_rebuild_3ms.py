import csv,itertools
from analyze_v37_environment import collect
from analyze_v41_lane_corrected_preview import add
from analyze_v40_wind_preview_interaction import add_preview

# v42 rebuild 3まくり差し.
# Base candidate population remains pre-deadline v37/v34 eligibility; actual entry/course never used.
# Exhibition information only reranks after exhibition. Wind is optional final correction only.

def rr(a):
 n=len(a);h=sum(x['target'] for x in a);return n,100*h/n if n else 0

def main():
 raw,q3=collect(); d=[x for x in raw if x['model']=='3まくり差し']; d=add(d); d=add_preview(d)
 # Candidate composite families. ST is exhibition ST; corrected lap/turn are emphasized.
 grids=[]
 for st in [.15,.20,.25,.30]:
  for lap in [.20,.25,.30,.35]:
   for turn in [.25,.30,.35,.40]:
    for ex in [.05,.10,.15]:
     straight=1-st-lap-turn-ex
     if .05<=straight<=.20: grids.append((st,lap,turn,ex,straight))
 for x in d:
  pass
 # Select weights ONLY on train: maximize shrunk lift of top 30%, require >=40 races.
 train=[x for x in d if x['period']=='train']; base=rr(train)[1]
 best=None
 for w in grids:
  st,lap,turn,ex,straight=w
  vals=[]
  for x in train:
   c=st*x['st_rank']+lap*x['lap_corr']+turn*x['turn_corr']+ex*x['ex_corr']+straight*x['straight_corr']; vals.append((c,x))
  vals.sort(key=lambda z:z[0],reverse=True); k=max(40,int(len(vals)*.30)); top=[x for _,x in vals[:k]]; n,r=rr(top)
  shr=(sum(x['target'] for x in top)+5*base/100)/(n+5); score=shr-base/100
  if best is None or score>best[0]:best=(score,w,vals[k-1][0])
 _,W,cut=best
 for x in d:
  st,lap,turn,ex,straight=W; x['v42_comp']=st*x['st_rank']+lap*x['lap_corr']+turn*x['turn_corr']+ex*x['ex_corr']+straight*x['straight_corr']; x['v42_pick']=int(x['v42_comp']>=cut)
 with open('races_v42_rebuild_3ms.csv','w',newline='',encoding='utf-8-sig') as fo:
  w=csv.DictWriter(fo,fieldnames=sorted(set().union(*(x.keys() for x in d))));w.writeheader();w.writerows(d)
 L=['# v42 3まくり差し 再構築','',f'学習のみで選択した重み: 展示ST={W[0]:.2f}, 枠補正一周={W[1]:.2f}, 枠補正回り足={W[2]:.2f}, 枠補正展示={W[3]:.2f}, 枠補正直線={W[4]:.2f}',f'学習上位30%相当 cutoff={cut:.3f}','', '実進入/艇N_コース不使用。事前候補は従来条件のまま、展示後にv42で格付け。風はこの選抜後の締切直前補正専用。','', '|期間|従来候補R|成立率|v42選抜R|成立率|差|','|---|---:|---:|---:|---:|---:|']
 for p in ['train','validation','latest_month']:
  a=[x for x in d if x['period']==p]; b=[x for x in a if x['v42_pick']]; n,r=rr(a);n2,r2=rr(b);L.append(f'|{p}|{n}|{r:.1f}%|{n2}|{r2:.1f}%|{r2-r:+.1f}pt|')
 # strength bands by train tertiles
 tv=sorted(x['v42_comp'] for x in train); q1=tv[len(tv)//3];q2=tv[2*len(tv)//3]
 L+=['','## 強度帯','|期間|帯|R|成立率|','|---|---|---:|---:|']
 for p in ['train','validation','latest_month']:
  a=[x for x in d if x['period']==p]
  bands=[('低',lambda v:v<q1),('中',lambda v:q1<=v<q2),('高',lambda v:v>=q2)]
  for name,fn in bands:
   z=[x for x in a if fn(x['v42_comp'])];n,r=rr(z);L.append(f'|{p}|{name}|{n}|{r:.1f}%|')
 L+=['','## 運用案','- v42は事前候補抽出を置き換えず、展示後の3まくり差し格付けに使用。','- 枠補正一周・回り足を中心に、展示ST・展示・直線を補完。','- validationで改善が再現しなければ正式採用しない。latest_monthは既に反復検証済みなので参考扱い。','- 風はv42選抜後、v38-v40と同方向の時だけ最終加減点する。']
 open('summary_v42_rebuild_3ms.md','w',encoding='utf-8').write('\n'.join(L)+'\n')
if __name__=='__main__':main()
