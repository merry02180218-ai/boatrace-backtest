from datetime import date,timedelta
from collections import Counter,defaultdict
from backtest import rows,i

START=date(2025,11,1); END=date(2026,8,31)

def normkim(s): return (s or '').replace(' ','').replace('　','')

def main():
    total=0; wins=Counter(); routes=Counter(); bymonth=defaultdict(Counter); valid_days=0; missing=[]
    d=START
    while d<=END:
        ymd=d.strftime('%Y/%m/%d')
        rr=rows(f'data/results/realtime/{ymd}.csv')
        if not rr:
            missing.append(str(d)); d+=timedelta(days=1); continue
        valid_days+=1
        for r in rr:
            w=i(r.get('1着_艇番')); kim=normkim(r.get('決まり手'))
            if w not in range(1,7): continue
            total+=1; wins[w]+=1; bymonth[d.strftime('%Y-%m')][w]+=1; bymonth[d.strftime('%Y-%m')]['n']+=1
            if w==3:
                routes['3_win']+=1
                if kim=='まくり': routes['3_makuri']+=1
                if kim=='まくり差し': routes['3_ms']+=1
                if kim in ('まくり','まくり差し'): routes['3_attack']+=1
            if w==4:
                routes['4_win']+=1
                if kim=='まくり': routes['4_makuri']+=1
                if kim=='まくり差し': routes['4_ms']+=1
                if kim in ('まくり','まくり差し'): routes['4_attack']+=1
            if w==5: routes['5_win']+=1
        d+=timedelta(days=1)
    L=['# v75 10か月・モデル未使用の素の頭確率','',f'期間: {START}〜{END}',f'有効結果レース: **{total:,}R** / 有効日 {valid_days}日 / 結果欠損日 {len(missing)}日','',
       '## 艇番別の実際の1着率','|艇番|1着数|1着率|','|---:|---:|---:|']
    for b in range(1,7): L.append(f'|{b}号艇|{wins[b]:,}|{wins[b]/total*100:.2f}%|')
    L+=['','## 今のモデルと比較しやすい素の発生率','|事象|発生数|全レース比|','|---|---:|---:|',
        f"|3号艇1着|{routes['3_win']:,}|{routes['3_win']/total*100:.2f}%|",
        f"|3号艇まくり|{routes['3_makuri']:,}|{routes['3_makuri']/total*100:.2f}%|",
        f"|3号艇まくり差し|{routes['3_ms']:,}|{routes['3_ms']/total*100:.2f}%|",
        f"|3号艇まくり+まくり差し|{routes['3_attack']:,}|{routes['3_attack']/total*100:.2f}%|",
        f"|4号艇1着|{routes['4_win']:,}|{routes['4_win']/total*100:.2f}%|",
        f"|4号艇まくり|{routes['4_makuri']:,}|{routes['4_makuri']/total*100:.2f}%|",
        f"|4号艇まくり差し|{routes['4_ms']:,}|{routes['4_ms']/total*100:.2f}%|",
        f"|4号艇まくり+まくり差し|{routes['4_attack']:,}|{routes['4_attack']/total*100:.2f}%|",
        f"|5号艇1着|{routes['5_win']:,}|{routes['5_win']/total*100:.2f}%|",'',
        '## 月別の素の1着率（3/4/5号艇）','|月|全R|3号艇|4号艇|5号艇|','|---|---:|---:|---:|---:|']
    for m in sorted(bymonth):
        n=bymonth[m]['n']; L.append(f"|{m}|{n:,}|{bymonth[m][3]/n*100:.2f}%|{bymonth[m][4]/n*100:.2f}%|{bymonth[m][5]/n*100:.2f}%|")
    if missing: L+=['','結果欠損日: '+', '.join(missing)]
    open('summary_v75_raw_head_rates.md','w',encoding='utf-8').write('\n'.join(L)+'\n')

if __name__=='__main__': main()
