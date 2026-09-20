#!/usr/bin/env python3
"""Validate data, optionally ingest news, then export reviewed artifacts.

用法:
  .venv/bin/python pipeline/run.py --validate-only
  .venv/bin/python pipeline/run.py --skip-news --output-dir /tmp/bci-report-export
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import export  # noqa: E402
import news  # noqa: E402
from validation import validate_repository  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-news", action="store_true")
    ap.add_argument("--validate-only", action="store_true")
    ap.add_argument("--max-per-source", type=int, default=40)
    ap.add_argument("--timeout", type=float, default=15.0)
    ap.add_argument("--output-dir", type=Path, default=export.SITE_DATA)
    ap.add_argument("--feed-path", type=Path, default=export.PUBLIC / "feed.xml")
    args = ap.parse_args()

    run_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    print(f"[run] {run_at}")
    validate_repository(export.DATA)
    print("[validate] catalogs, literature records, and verified result store are valid")
    if args.validate_only:
        return

    conn = news.connect()
    if not args.skip_news:
        print("[1/3] 抓取新闻源…")
        st = news.fetch_all(conn, max_per_source=args.max_per_source, timeout=args.timeout)
        print(f"      源 {st['sources']} 个，新增 {st['new']} 条，未变化 {st['not_modified']} 个，失败 {len(st['failed'])} 个")
        for f in st["failed"]:
            print(f"      ✗ {f['source']}: {f['error']}")
    else:
        print("[1/3] 跳过新闻抓取")

    approved = news.sync_curated_reviews(conn)
    print(f"      人工审核白名单匹配 {approved} 条")
    items = news.latest(conn, n=300)
    print("[2/3] 生成严格同协议的 verified 排名…")
    out = export.export_all(items, run_at=run_at, output_dir=args.output_dir, feed_path=args.feed_path)
    s = out["stats"]
    print(f"[3/3] 导出完成：模型 {s['n_models']}（进榜 {s['n_ranked']}）/ 基准 {s['n_benchmarks']} / "
          f"结果 {s['n_results']} / 计分任务 {s['n_tasks_scored']} / 新闻 {out['news']} 条")
    print(f"      → {args.output_dir}/*.json, {args.feed_path}")


if __name__ == "__main__":
    main()
