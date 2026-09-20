from __future__ import annotations

import sqlite3
import sys
import tempfile
import time
import unittest
from pathlib import Path

import yaml

PIPELINE = Path(__file__).resolve().parents[1]
ROOT = PIPELINE.parent
sys.path.insert(0, str(PIPELINE))

import news  # noqa: E402
from leaderboard import build_verified_leaderboard  # noqa: E402
from validation import Catalogs, ValidationError, read_csv, validate_repository, validate_verified_results  # noqa: E402


class LeaderboardPolicyTests(unittest.TestCase):
    def setUp(self):
        self.benchmarks = {"task": {"primary_metric": "accuracy", "higher_is_better": True}}

    @staticmethod
    def row(model: str, protocol: str = "p1") -> dict[str, str]:
        return {
            "model_slug": model, "benchmark_slug": "task", "metric": "accuracy",
            "value": "80", "value_scale": "percent", "std": "", "uncertainty_type": "",
            "tier": "verified", "run_by": "bciarena", "protocol_id": protocol,
            "dataset_version": "v1", "split_id": "loso-subjects-01-09", "evaluation_mode": "full_finetune",
            "preprocessing_id": "prep-a", "run_id": f"run-{model}",
            "verified_at": "2026-09-09T00:00:00Z", "verifier": "reviewer",
            "verification_method": "artifact review", "evidence_url": "https://example.test/evidence",
            "artifact_sha256": "", "code_commit": "abc", "source_title": "",
            "source_url": "", "table_ref": "", "notes": "", "date_added": "2026-09-09",
        }

    def test_incomparable_results_do_not_enter_leaderboard(self):
        board = build_verified_leaderboard([self.row("a", "p1"), self.row("b", "p2")], self.benchmarks)
        self.assertEqual(board["models"], [])
        self.assertEqual(board["tasks"], [])

    def test_same_protocol_results_are_ranked_without_elo_or_ci(self):
        first, second = self.row("a"), self.row("b")
        first["value"], second["value"] = "81", "79"
        board = build_verified_leaderboard([first, second], self.benchmarks)
        self.assertEqual([row["slug"] for row in board["models"]], ["a", "b"])
        self.assertEqual([row["rank"] for row in board["models"]], [1, 2])
        self.assertIsNone(board["models"][0]["rating"])
        self.assertIsNone(board["models"][0]["ci_low"])

    def test_different_value_scales_never_share_a_comparison(self):
        percent, unit = self.row("a"), self.row("b")
        percent["value"] = "90"
        unit["value"], unit["value_scale"] = "0.95", "unit_interval"
        board = build_verified_leaderboard([percent, unit], self.benchmarks)
        self.assertEqual(board["models"], [])
        self.assertEqual(board["tasks"], [])

    def test_missing_protocol_field_is_rejected(self):
        catalogs = Catalogs(
            [{"slug": "a"}],
            [{"slug": "task", "primary_metric": "accuracy", "metrics": ["accuracy"], "task_family": "x"}],
        )
        row = self.row("a")
        row["split_id"] = ""
        with self.assertRaisesRegex(ValidationError, "split_id"):
            validate_verified_results([row], catalogs)

    def test_non_http_evidence_url_is_rejected(self):
        catalogs = Catalogs(
            [{"slug": "a"}],
            [{"slug": "task", "primary_metric": "accuracy", "metrics": ["accuracy"], "task_family": "x"}],
        )
        row = self.row("a")
        row["evidence_url"] = "javascript:alert(1)"
        with self.assertRaisesRegex(ValidationError, "HTTP\\(S\\)"):
            validate_verified_results([row], catalogs)

    def test_checked_in_literature_has_no_verified_ranking_rows(self):
        validate_repository(ROOT / "data")
        verified = read_csv(ROOT / "data" / "verified_results.csv")
        self.assertEqual(verified, [])


class NewsSafetyTests(unittest.TestCase):
    def test_url_normalization_removes_tracking_and_sorts_query(self):
        raw = "HTTPS://Example.COM:443/a//b/?z=2&utm_source=x&a=1#fragment"
        self.assertEqual(news._norm_link(raw), "https://example.com/a/b?a=1&z=2")

    def test_url_normalization_is_idempotent(self):
        # A second pass used to return a different key, so a curated review could
        # attach to the wrong article — or, having missed, to none at all.
        for url in ("https://journal.test/a//b",
                    "https://journal.test/news%2F2026%2Fbci-implant",
                    "https://JOURNAL.test:443/a/b/",
                    "https://journal.test/p%C3%A1gina",
                    "https://journal.test/a/b?utm_source=x&id=7"):
            once = news._norm_link(url)
            self.assertEqual(once, news._norm_link(once), url)

    def test_escaped_slash_does_not_collide_with_a_real_path(self):
        self.assertNotEqual(news._norm_link("https://journal.test/a%2F%2Fb"),
                            news._norm_link("https://journal.test/a/b"))
        self.assertNotEqual(news._norm_link("https://j.test/news%2F2026%2Fx"),
                            news._norm_link("https://j.test/news/2026/x"))

    def test_feed_struct_time_is_converted_as_utc(self):
        parsed = time.struct_time((2026, 1, 2, 3, 4, 5, 4, 2, 0))
        self.assertEqual(news._iso({"published_parsed": parsed}), "2026-01-02T03:04:05+00:00")

    def test_only_whitelisted_relevant_news_is_returned(self):
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        conn.executescript(news.SCHEMA)
        link = news._norm_link("https://example.test/bci?utm_source=rss")
        conn.execute(
            "INSERT INTO items(id,source,category,lang,title,link,published,fetched,summary,tags,relevance) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            ("one", "test", "research", "en", "BCI result", link,
             "2026-09-09T00:00:00+00:00", "2026-09-09T00:01:00+00:00",
             "unreviewed feed excerpt", "[]", 3),
        )
        conn.execute(
            "INSERT INTO items(id,source,category,lang,title,link,published,fetched,summary,tags,relevance) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            ("two", "test", "media", "en", "Unrelated", "https://example.test/other",
             "2026-09-09T00:00:00+00:00", "2026-09-09T00:01:00+00:00", "feed", "[]", 0),
        )
        with tempfile.TemporaryDirectory() as tmp:
            curated = Path(tmp) / "curated.yaml"
            curated.write_text(yaml.safe_dump([{
                "link": "https://example.test/bci?utm_campaign=x", "approved": True,
                "summary": "Human reviewed summary.", "reviewer": "editor",
                "reviewed_at": "2026-09-09T01:00:00Z",
            }]), encoding="utf-8")
            self.assertEqual(news.sync_curated_reviews(conn, curated), 1)
        items = news.latest(conn)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["summary"], "Human reviewed summary.")
        self.assertIsNone(items[0]["llm_summary"])


if __name__ == "__main__":
    unittest.main()
