"""v127: optimize 1-head ticket count 1..7 using frozen v110 order.
Development Mar-May uses p1>=72 as in v110 validation; untouched Jun-Aug uses p109>=72.
No odds in ranking/selection; Sep outcomes unused.
Triggered after workflow creation.
"""
from analyze_v110b_1head_role_tickets import read_csv,prepare_month,ff,ii
SRC='analysis_v108_1head_feasibility.csv'; HEAD='analysis_v109_1head_monthly_walkforward.csv'
DEV=['2026-03','2026-04','2026-05']; TEST=['2026-06','2026-07','2026-08']; OUT='summary_v127_1head_ticket_count.md'

def order(r): return [x for x in (r.get('order_l50') or '').split(';') if x]
def metric(rs,n,phase):
 q=[]
 for r in rs:
  p=ff(r.get('p1' if phase=='dev' else 'p109'))
  if p>=.72 and ii(r.get('valid_payout'))==1:q.append(r)
 hit=head=ret=0
 for r in q:
  act=(r.get('actual_combo') or '').strip(); head += ii(r.get('head_hit'))==1
  if act in order(r)[:n]: hit+=1; ret+=ii(r.get('payout100'))
 return len(q),100*hit/len(q) if q else 0,100*hit/head if head else 0,100*ret/(len(q)*n*100) if q else 0

def main():
 src=read_csv(SRC); hp={(r.get('date'),r.get('race_code')):r.get('p109','') for r in read_csv(HEAD)}
 by={}
 for mo in DEV+TEST:
  print('prepare',mo,flush=True); by[mo]=prepare_month(src,mo)
  for r in by[mo]: r['p109']=hp.get((r.get('date'),r.get('race_code')),'')
 dev=sum((by[m] for m in DEV),[]); test=sum((by[m] for m in TEST),[])
 d={n:metric(dev,n,'dev') for n in range(1,8)}
 b7=d[7]; cand=[]
 for n,m in d.items():
  if b7[2] and m[2] >= .70*b7[2]:
   score=((m[1]/b7[1])*(m[3]/b7[3]))**0.5 if b7[1] and b7[3] else 0
   cand.append((score,-n,n))
 chosen=max(cand)[2] if cand else 7
 t={n:metric(test,n,'test') for n in range(1,8)}
 L=['# v127 1号艇 買い目点数最適化','', '- 頭判定と相手順位は固定。点数だけ1〜7点で比較。','- Mar-Mayで点数選択、Jun-Augは完全holdout。','- DEVはv110と同じp1>=72、TESTはp109>=72。オッズ・Sep結果は選定に不使用。','', '## Mar-May development','|点数|R|3連単的中率|①頭時coverage|ROI|','|---:|---:|---:|---:|---:|']
 for n in range(1,8):
  m=d[n]; L.append(f'|{n}|{m[0]}|{m[1]:.1f}%|{m[2]:.1f}%|{m[3]:.1f}%|')
 L += ['',f'選択点数 = **{chosen}点**','', '## Jun-Aug untouched holdout','|点数|R|3連単的中率|①頭時coverage|ROI|','|---:|---:|---:|---:|---:|']
 for n in range(1,8):
  m=t[n]; mark=' **←DEV選択**' if n==chosen else ''; L.append(f'|{n}|{m[0]}|{m[1]:.1f}%|{m[2]:.1f}%|{m[3]:.1f}%|{mark}')
 L += ['', '## Jun-Aug 月別安定性（選択点 vs 7点）','|月|点数|R|3連単的中率|coverage|ROI|','|---|---:|---:|---:|---:|---:|']
 for mo in TEST:
  for n in [chosen,7]:
   m=metric(by[mo],n,'test'); L.append(f'|{mo}|{n}|{m[0]}|{m[1]:.1f}%|{m[2]:.1f}%|{m[3]:.1f}%|')
 L += ['','## 判定',f'- 実運用推奨候補: **{chosen}点**（DEVで事前選択）', '- holdoutのROI・3連単的中率・coverage・月別安定性を見て最終採用判断する。']
 open(OUT,'w',encoding='utf-8').write('\n'.join(L)+'\n')
if __name__=='__main__':main()
