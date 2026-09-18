from __future__ import annotations
import json
import pandas as pd

SRC="analysis_v289_3head_wave21_allrace_feature_settled.csv"

def main():
    df=pd.read_csv(SRC,nrows=50,low_memory=False)
    cols=list(df.columns)
    groups={}
    needles={
        "settlement":["settle","winner","payout","actual","hit"],
        "odds":["odds","odd","3t","trifecta","closing"],
        "v288_related":["c_","comp","top_n","raw_n","route","v243","buyable"],
        "pair":["pair","second","third","combo"],
    }
    for name,keys in needles.items():
        groups[name]=[c for c in cols if any(k.lower() in c.lower() for k in keys)]
    sample=None
    if "closing_odds__json" in df.columns:
        vals=df["closing_odds__json"].dropna().astype(str)
        if len(vals):
            raw=vals.iloc[0]
            try:
                parsed=json.loads(raw)
                sample={"type":type(parsed).__name__,"preview":parsed}
            except Exception:
                sample={"type":"raw","preview":raw[:1000]}
    out={
        "column_count":len(cols),
        "columns":cols,
        "groups":groups,
        "closing_odds_json_sample":sample,
    }
    with open("inspect_3head_a_ticket_source_result.json","w") as f:
        json.dump(out,f,ensure_ascii=False,indent=2)
    print(json.dumps(out,ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
