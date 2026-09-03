import csv
from analyze_v23_20260902_daypreview import by_code, venue_map, preview_for, f
from backtest import rows
from backtest_v20_week import target
DATE='2026-09-03'; YMD='2026/09/03'
VEN={'08':'常滑','10':'三国','13':'尼崎','18':'徳山','22':'福岡'}
def main():
 with open('pred_v25_20260903_pre.csv',encoding='utf-8-sig') as fh: base=list(csv.DictReader(fh))
 tkz=by_code(f'data/previews/tkz/{YMD}.csv'); stt=by_code(f'data/previews/stt/{YMD}.csv'); orig=by_code(f'data/previews/original_exhibition/{YMD}.csv'); vidx=venue_map()
 res=by_code(f'data/results/realtime/{YMD}.csv'); out=[]
 for r in base:
  p=preview_for(r['model'],r['race_code'],r['venue'],tkz,stt,orig,vidx); z=dict(r); z.update(p); z['adjusted_score']=round((f(r['score']) or 0)+p['preview_adj'],2)
  rr=res.get(r['race_code'],{}); z['target_hit']=target(rr,r['model']); z['finish']=rr.get('3連単_組番') or rr.get('着順') or ''; z['kimarite']=rr.get('決まり手') or ''; out.append(z)
 with open('final_v26_20260903.csv','w',newline='',encoding='utf-8-sig') as fh:
  w=csv.DictWriter(fh,fieldnames=sorted(set().union(*(x.keys() for x in out)))); w.writeheader(); w.writerows(out)
 L=['# v26 2026-09-03 最終判定と結果','', 'v25事前候補7Rに、締切前取得の展示タイム・展示ST・オリジナル展示・v22場補正だけを固定式で適用。実進入は未使用。結果は判定後の検証用。','', '|場|R|モデル|事前score|最終score|grade|展示|展示ST|一周|回り足|直線|狙い成立|','|---|---:|---|---:|---:|---|---:|---:|---:|---:|---:|---:|']
 for r in sorted(out,key=lambda x:-float(x['adjusted_score'])):
  L.append(f"|{VEN.get(str(r['venue']).zfill(2),r['venue'])}|{r['race']}|{r['model']}|{float(r['score']):.2f}|{r['adjusted_score']:.2f}|{r['grade']}|{r['ex_score']:.2f}|{r['st_score']:.2f}|{r['orig_lap']:.2f}|{r['orig_turn']:.2f}|{r['orig_straight']:.2f}|{int(r['target_hit'])}|")
 sa=[r for r in out if r['grade'] in ('S','A')]; hits=sum(int(r['target_hit']) for r in sa)
 L+=['',f'S/A: {len(sa)}R / 狙い成立 {hits}R / 成立率 {hits/len(sa)*100 if sa else 0:.1f}%']
 open('final_v26_20260903.md','w',encoding='utf-8').write('\n'.join(L)+'\n')
if __name__=='__main__': main()
