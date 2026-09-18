from __future__ import annotations
import csv
import json
from pathlib import Path
import pandas as pd

SRC="analysis_v289_3head_wave21_allrace_feature_settled.csv"
OUT=Path("data/official_closing_odds3t")

def main():
    use=["date","race_code_norm","closing_odds__ok","closing_odds__json"]
    d=pd.read_csv(SRC,usecols=use,low_memory=False)
    d["date"]=pd.to_datetime(d.date,errors="coerce")
    d=d[(d.date>="2026-03-01")&(d.date<"2026-04-01")&(d.closing_odds__ok==1)].copy()
    written=0
    races=0
    for day,g in d.groupby(d.date.dt.normalize()):
        rows=[]
        for _,r in g.iterrows():
            code=str(int(r.race_code_norm)).zfill(12)
            try:
                om=json.loads(r.closing_odds__json)
            except Exception:
                continue
            if not isinstance(om,dict):
                continue
            clean={}
            for k,v in om.items():
                s=str(k)
                p=s.split("-")
                if len(p)!=3 or len(set(p))!=3 or any(x not in "123456" for x in p):
                    continue
                try:q=float(v)
                except:continue
                if q>0:clean[s]=q
            if len(clean)!=120:
                continue
            row={"jcd":int(code[8:10]),"rno":int(code[10:12])}
            row.update(clean)
            rows.append(row)
        if not rows:
            continue
        p=OUT/f"{day:%Y/%m/%d}.csv"
        p.parent.mkdir(parents=True,exist_ok=True)
        fields=["jcd","rno"]+sorted([k for k in rows[0] if k not in {"jcd","rno"}],
                                   key=lambda s:tuple(map(int,s.split("-"))))
        with p.open("w",newline="",encoding="utf-8-sig") as f:
            w=csv.DictWriter(f,fieldnames=fields)
            w.writeheader();w.writerows(rows)
        written+=1;races+=len(rows)
    if written<25 or races<3500:
        raise RuntimeError(f"March closing odds materialization too small days={written} races={races}")
    out={"marker":"3HEAD_A_MARCH_CLOSING_ODDS_READY","days":written,"races":races}
    Path("research_3head_a_march_closing_odds_manifest.json").write_text(
        json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"
    )
    print(json.dumps(out,ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
