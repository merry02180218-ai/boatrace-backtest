#!/usr/bin/env python3
"""Create one GitHub Issue notification when a HEAD4 live decision is BET.

- PASS / NO_BET_DATA_NOT_READY: no issue
- exact-title dedupe prevents duplicate notifications for the same race
- direct-mention repository owner in the Issue body for GitHub Mobile push
- also assign repository owner as a secondary notification path
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import requests

VENUE = {
    1:"桐生",2:"戸田",3:"江戸川",4:"平和島",5:"多摩川",6:"浜名湖",
    7:"蒲郡",8:"常滑",9:"津",10:"三国",11:"びわこ",12:"住之江",
    13:"尼崎",14:"鳴門",15:"丸亀",16:"児島",17:"宮島",18:"徳山",
    19:"下関",20:"若松",21:"芦屋",22:"福岡",23:"唐津",24:"大村",
}

def api(method: str, url: str, token: str, **kwargs):
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    r = requests.request(method, url, headers=headers, timeout=15, **kwargs)
    if r.status_code >= 400:
        raise RuntimeError(f"GitHub API {method} {url} -> {r.status_code}: {r.text[:500]}")
    return r

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--decision-json", required=True)
    ap.add_argument("--target-date", required=True)
    ap.add_argument("--jcd", required=True, type=int)
    ap.add_argument("--race", required=True, type=int)
    ap.add_argument("--deadline-jst", required=True)
    ap.add_argument("--dry-run", action="store_true")
    args=ap.parse_args()

    z=json.loads(Path(args.decision_json).read_text(encoding="utf-8"))
    decision=str(z.get("decision",""))
    if decision!="BET":
        print(f"HEAD4_NOTIFY_SKIP decision={decision}")
        return

    token=os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    repo=os.environ.get("GITHUB_REPOSITORY")
    owner=(repo or "").split("/",1)[0]
    if not token or not repo or not owner:
        raise RuntimeError("GITHUB_TOKEN/GITHUB_REPOSITORY missing")

    title=f"[4HEAD BET] {args.target_date} JCD{args.jcd:02d} {args.race}R"
    base=f"https://api.github.com/repos/{repo}"

    # Exact-title dedupe across recent open/closed issues.
    issues=api("GET", f"{base}/issues", token, params={"state":"all","per_page":100}).json()
    for it in issues:
        if "pull_request" not in it and it.get("title")==title:
            print(f"HEAD4_NOTIFY_DUPLICATE issue={it.get('number')}")
            return

    tickets=z.get("tickets") or []
    odds=z.get("ticket_odds") or {}
    venue=VENUE.get(args.jcd, f"JCD{args.jcd:02d}")
    lines=[
        f"@{owner}",
        "",
        f"# 4号艇 BET通知 — {venue} {args.race}R",
        "",
        f"- 判定: **{decision}**",
        f"- profile: `{z.get('profile','')}`",
        f"- 締切: **{args.deadline_jst} JST**",
        f"- head_prob: **{float(z.get('head_prob',0)):.3f}**",
        f"- opponent_mass: **{float(z.get('opponent_mass',0)):.3f}**",
        f"- composite_odds: **{float(z.get('composite_odds',0)):.2f}**",
        f"- base120_selected: `{z.get('base120_selected')}`",
        f"- newfeature_expanded_added: `{z.get('newfeature_expanded_added')}`",
        f"- newfeature_score: `{z.get('newfeature_score')}`",
        f"- newfeature_threshold: `{z.get('newfeature_threshold')}`",
        f"- legacy_156r_selected: `{z.get('legacy_156r_selected')}`",
        f"- ST advantage: `{z.get('st4_adv_inside')}`",
        f"- ORIG advantage: `{z.get('orig4_adv_inside')}`",
        "",
        "## 買い目",
    ]
    for t in tickets:
        lines.append(f"- **{t}** — {odds.get(t,'?')}倍")
    lines += [
        "",
        f"- decision_time: `{z.get('decision_time_jst','')}`",
        f"- odds source: `{z.get('odds_source','')}`",
        "- target result/payout: **未使用**",
    ]
    body="\n".join(lines)+"\n"

    payload={"title":title,"body":body,"assignees":[owner]}
    if args.dry_run:
        print("HEAD4_BET_GITHUB_ISSUE_DRY_RUN_OK")
        print(json.dumps(payload,ensure_ascii=False,indent=2))
        return
    out=api("POST", f"{base}/issues", token, json=payload).json()
    print(f"HEAD4_BET_GITHUB_ISSUE_NOTIFIED issue={out.get('number')} url={out.get('html_url')}")

if __name__=="__main__":
    main()
