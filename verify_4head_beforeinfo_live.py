#!/usr/bin/env python3
"""Offline fail-closed verifier for fetch_4head_beforeinfo_live.py."""
from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path

import fetch_4head_beforeinfo_live as m

SAMPLE = """<!doctype html><html><head><title>BOAT RACE beforeinfo</title></head><body>
<table><tr><th>枠</th><th>展示タイム</th><th>チルト</th></tr>
<tr><td>4</td><td>6.72</td><td>0.0</td></tr></table>
<table><tr><th>進入</th><th>ST</th></tr><tr><td>4</td><td>.08</td></tr></table>
</body></html>"""


def must_fail(fn, *a):
    try:
        fn(*a)
    except Exception:
        return
    raise AssertionError("expected fail-closed exception")


def main():
    url = m.build_url("20260630", 12, 7)
    assert url == "https://www.boatrace.jp/owpc/pc/race/beforeinfo?rno=7&jcd=12&hd=20260630"
    m.assert_result_blind_url(url)
    must_fail(m.validate_target, "2026-06-30", 12, 7)
    must_fail(m.validate_target, "20260630", 0, 7)
    must_fail(m.validate_target, "20260630", 12, 13)
    must_fail(m.assert_result_blind_url, "https://www.boatrace.jp/owpc/pc/race/raceresult?rno=7&jcd=12&hd=20260630")

    p = m.parse_beforeinfo_html(SAMPLE)
    assert p["table_count"] == 2
    assert p["tables"][0]["rows"][1] == ["4", "6.72", "0.0"]

    meta = {
        "schema": "head4_beforeinfo_snapshot_v1",
        "source_kind": "official_beforeinfo_only",
        "source_url": url,
        "hd": "20260630",
        "jcd": 12,
        "rno": 7,
        "fetched_at_jst": "2026-06-30T12:00:00+09:00",
        "sha256_html": hashlib.sha256(SAMPLE.encode("utf-8")).hexdigest(),
        "http_status": 200,
        "redirect_followed": False,
        "result_endpoint_requested": False,
        "payout_endpoint_requested": False,
        "parsed": p,
    }
    with tempfile.TemporaryDirectory() as td:
        hp, jp = m.persist_snapshot(Path(td), SAMPLE, meta)
        assert hp.is_file() and jp.is_file()
        got = json.loads(jp.read_text(encoding="utf-8"))
        assert got["sha256_html"] == meta["sha256_html"]
        assert got["result_endpoint_requested"] is False
        assert got["payout_endpoint_requested"] is False
        assert got["parsed"]["table_count"] == 2

    src = Path(m.__file__).read_text(encoding="utf-8")
    # Acquisition implementation must remain allow-list based and non-following.
    assert "allow_redirects=False" in src
    assert "BASE = \"https://www.boatrace.jp/owpc/pc/race/beforeinfo\"" in src
    assert "raceresult" not in src.lower()
    print("VERIFY_4HEAD_BEFOREINFO_LIVE_OK")


if __name__ == "__main__":
    main()
