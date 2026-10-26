#!/usr/bin/env python3
"""No-network fail-closed tests for original GH v351 PRE as-of replay harness."""
import csv,gzip,hashlib,tempfile,unittest
from datetime import date
from pathlib import Path
from v351_asof_shadow_gate_20261026 import validate_race_manifest,check_history,parse_jst,KIND_REQUIRED,sha_file

class AsOfTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        self.target=date(2026,10,26)
        self.race="202610260104"
        self.item={"race_code":self.race,
            "deadline_jst":"2026-10-26T12:00:00+09:00",
            "sources":{}}
        for kind in KIND_REQUIRED:
            filename=kind+".csv"
            (self.root/filename).write_text("verifiable pre-result record",encoding="utf-8")
            self.item["sources"][kind]={
                "file":filename,"sha256":sha_file(self.root/filename),
                "observed_at_jst":"2026-10-26T11:56:00+09:00"}

    def tearDown(self):
        self.tmp.cleanup()

    def test_causal_manifest_before_deadline(self):
        v=validate_race_manifest(self.item,self.target,self.root)
        self.assertTrue(v["ready"])
        self.assertEqual(v["issues"],[])
        self.assertEqual(len(v["observed_sources"]),5)

    def test_reject_observed_inside_three_minutes(self):
        self.item["sources"]["official_stt"]["observed_at_jst"]="2026-10-26T11:58:01+09:00"
        v=validate_race_manifest(self.item,self.target,self.root)
        self.assertFalse(v["ready"])
        self.assertIn("official_stt",v["issues"][0])

    def test_reject_snapshot_modified_after_capture(self):
        (self.root/"official_tkz.csv").write_text("changed result-dependent contents",encoding="utf-8")
        v=validate_race_manifest(self.item,self.target,self.root)
        self.assertFalse(v["ready"])
        self.assertTrue(any("sha256 drift" in s for s in v["issues"]))

    def test_no_path_traversal(self):
        self.item["sources"]["race_cards"]["file"]="../outside.csv"
        v=validate_race_manifest(self.item,self.target,self.root)
        self.assertFalse(v["ready"])
        self.assertTrue(any("outside evidence root" in s for s in v["issues"]))

    def test_missing_original_blocks(self):
        self.item["sources"].pop("boaters_original_exhibition")
        v=validate_race_manifest(self.item,self.target,self.root)
        self.assertFalse(v["ready"])
        self.assertTrue(any("original_exhibition" in s for s in v["issues"]))

    def test_offset_required(self):
        with self.assertRaises(ValueError):
            parse_jst("2026-10-26T11:57:00")
        with self.assertRaises(ValueError):
            parse_jst("2026-10-26T02:57:00+00:00")

    def history(self,dt="2026-08-20",month="2026-08"):
        file=self.root/"head.csv"
        with file.open("w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=["race_code","date","month","head_hit"])
            w.writeheader()
            for i in range(1001):
                w.writerow({"race_code":f"20260820{1+i%24:02d}01",
                            "date":dt,"month":month,"head_hit":i%2})
        return file

    def test_prior_month_history_passes(self):
        file=self.history()
        v=check_history(file,self.target)
        self.assertEqual(v["records"],1001)
        self.assertEqual(v["latest_training_date"],"2026-08-20")

    def test_gzipped_prior_history_passes(self):
        file=self.history()
        gz=self.root/"slim.csv.gz"
        with file.open("rb") as src, gzip.open(gz,"wb") as dst:
            dst.write(src.read())
        v=check_history(gz,self.target)
        self.assertEqual(v["records"],1001)
        self.assertEqual(v["latest_training_date"],"2026-08-20")

    def test_forbid_same_month_history(self):
        file=self.history(dt="2026-10-01",month="2026-10")
        with self.assertRaises(ValueError):
            check_history(file,self.target)

    def test_forbid_month_date_disagreement(self):
        file=self.history(month="2026-09")
        with self.assertRaises(ValueError):
            check_history(file,self.target)

if __name__=="__main__":
    unittest.main(verbosity=2)
