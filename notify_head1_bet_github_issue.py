#!/usr/bin/env python3
"""Create one GitHub Issue only when a 1HEAD current-day decision is BET."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import requests

VENUE={
    1:"桐生",2:"戸田",3:"江戸川",4:"平和島",5:"多摩川",6:"浜名湖",
    7:"蒲郡",8:"常滑",9:"津",10:"三国",11:"びわこ",12:"住之江",
    13:"尼崎",14:"鳴門",15:"丸亀",16:"児島",17:"宮島",18:"徳山",
    19:"下関",20:"若松",21:"芦屋",22:"福岡",23:"唐津",24:"大村",
}


def api(method:str,url:str,token:str,**kwargs):
    headers={
        "Accept":"application/vnd.github+json",
        "Authorization":f"Bearer {token}",
        "X-GitHub-Api-Version":"2022-11-28",
    }
    r=requests.request(method,url,headers=headers,timeout=15,**kwargs)
    if r.status_code>=400:
        raise RuntimeError(f"GitHub API {method} {url} -> {r.status_code}: {r.text[:500]}")
    return r


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--decision-json",required=True)
    ap.add_argument("--dry-run",action="store_true")
    a=ap.parse_args()

    z=json.loads(Path(a.decision_json).read_text(encoding="utf-8"))
    if str(z.get("decision",""))!="BET":
        print(f"HEAD1_NOTIFY_SKIP decision={z.get('decision')}")
        return
    if z.get("target_race_result_used") is not False or z.get("payout_used") is not False:
        raise RuntimeError("unsafe decision artifact")

    code=str(z.get("race_code","")).zfill(12)
    if len(code)!=12 or not code.isdigit():
        raise RuntimeError("invalid race_code")
    day=code[:8]; jcd=int(code[8:10]); race=int(code[10:12])
    token=os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    repo=os.environ.get("GITHUB_REPOSITORY")
    owner=(repo or "").split("/",1)[0]
    if not token or not repo or not owner:
        raise RuntimeError("GITHUB_TOKEN/GITHUB_REPOSITORY missing")

    title=f"[1HEAD BET] {day} JCD{jcd:02d} {race}R"
    base=f"https://api.github.com/repos/{repo}"
    issues=api("GET",f"{base}/issues",token,params={"state":"all","per_page":100}).json()
    for it in issues:
        if "pull_request" not in it and it.get("title")==title:
            print(f"HEAD1_NOTIFY_DUPLICATE issue={it.get('number')}")
            return

    tickets=list(z.get("tickets") or [])
    odds=z.get("ticket_odds") or {}
    stakes=list(z.get("live_stakes_yen") or [])
    if len(stakes)!=len(tickets):
        stakes=[int((z.get("live_stake_map_yen") or {}).get(t,0)) for t in tickets]

    venue=VENUE.get(jcd,f"JCD{jcd:02d}")
    lines=[
        f"@{owner}","",
        f"# 1号艇 BET通知 — {venue} {race}R","",
        f"- 判定: **BET**",
        f"- 締切: **{z.get('deadline_jst','')} JST**",
        f"- lane: **{z.get('head_selection_lane','')}**",
        f"- head_prob: **{float(z.get('head_prob',0)):.3f}**",
        f"- opponent_mass: **{float(z.get('opponent_mass',0)):.3f}**",
        f"- b1 recent_p2: **{float(z.get('b1_pl_recent_p2',0)):.3f}**",
        f"- env_pair: **{z.get('env_pair')}**",
        f"- 注目タグ: volume_pickup={z.get('head_volume_pickup')} / opponent_pickup={z.get('head_volume_opponent_pickup')}",
        f"- composite_odds: **{float(z.get('composite_odds',0)):.2f}**","",
        "## 買い目",
    ]
    for i,t in enumerate(tickets):
        amount=int(stakes[i]) if i<len(stakes) else 0
        o=float(odds.get(t,0) or 0)
        payout=round(amount*o)
        lines.append(f"- **{t}** — {o:.1f}倍 — **{amount:,}円**（的中時 約{payout:,}円）")
    lines += [
        "",
        f"- 合計購入額: **{sum(int(x) for x in stakes):,}円**",
        "- 振分: オッズ逆数比例・100円単位（払戻均等化）",
        "",
        f"- decision_time: `{z.get('decision_time_jst','')}`",
        f"- odds source: `{z.get('odds_source','')}`",
        "- target result/payout: **未使用**",
    ]
    payload={"title":title,"body":"\n".join(lines)+"\n","assignees":[owner]}
    if a.dry_run:
        print("HEAD1_BET_GITHUB_ISSUE_DRY_RUN_OK")
        print(json.dumps(payload,ensure_ascii=False,indent=2))
        return
    out=api("POST",f"{base}/issues",token,json=payload).json()
    print(f"HEAD1_BET_GITHUB_ISSUE_NOTIFIED issue={out.get('number')} url={out.get('html_url')}")


if __name__=="__main__":
    main()
