"""Export catalogs, protocol-local verified rankings, and approved news."""
from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path
from xml.sax.saxutils import escape

import yaml

from leaderboard import build_verified_leaderboard
from scoring import Result
from validation import read_csv, validate_repository

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SITE_DATA = ROOT / "site" / "src" / "data"
PUBLIC = ROOT / "site" / "public"

FAMILY_LABEL = {
    "abnormal_detection": "Abnormal EEG", "event_classification": "Event classification",
    "seizure": "Seizure detection", "sleep_staging": "Sleep staging", "motor_imagery": "Motor imagery",
    "emotion": "Emotion recognition", "erp_p300": "ERP / P300", "ssvep": "SSVEP",
    "imagined_speech": "Imagined speech", "cognitive_load": "Cognitive load", "clinical_other": "Clinical (other)",
}
METRIC_LABEL = {
    "balanced_accuracy": "Balanced Acc.", "accuracy": "Accuracy", "auc_pr": "AUC-PR", "auroc": "AUROC",
    "cohen_kappa": "Cohen's κ", "weighted_f1": "Weighted F1", "macro_f1": "Macro F1", "pearson_r": "Pearson r",
}


def _dump(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")


def load_catalogs():
    models = yaml.safe_load((DATA / "models.yaml").read_text(encoding="utf-8"))
    benchmarks = yaml.safe_load((DATA / "benchmarks.yaml").read_text(encoding="utf-8"))
    results = []
    with (DATA / "results.csv").open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            results.append(Result(
                model=row["model_slug"], benchmark=row["benchmark_slug"], metric=row["metric"],
                value=float(row["value"]), std=float(row["std"]) if row.get("std") else None,
                tier=row["tier"], run_by=row.get("run_by", ""), source_title=row.get("source_title", ""),
                source_url=row.get("source_url", ""), table_ref=row.get("table_ref", ""), notes=row.get("notes", ""),
            ))
    return models, benchmarks, results


def load_verified_results() -> list[dict[str, str]]:
    return read_csv(DATA / "verified_results.csv")


def _legacy_result_dict(result: Result) -> dict:
    row = result.__dict__.copy()
    row["evidence"] = {
        "status": "reported" if result.tier == "reported" else result.tier,
        "source_title": result.source_title or None,
        "source_url": result.source_url or None,
        "table_ref": result.table_ref or None,
        "ranking_eligible": False,
        "reason": "literature result; not a BCI Arena verified run",
    }
    row["protocol"] = {key: None for key in (
        "protocol_id", "dataset_version", "split_id", "evaluation_mode", "preprocessing_id",
    )}
    row["uncertainty"] = {
        "type": "standard_deviation" if result.std is not None else None,
        "value": result.std,
        "is_95_ci": False,
    }
    return row


def _verified_result_dict(row: dict[str, str]) -> dict:
    std = float(row["std"]) if row.get("std") else None
    return {
        "model": row["model_slug"], "benchmark": row["benchmark_slug"],
        "metric": row["metric"], "value": float(row["value"]), "std": std,
        "tier": "verified", "run_by": "bciarena",
        "source_title": row.get("source_title", ""), "source_url": row.get("source_url", ""),
        "table_ref": row.get("table_ref", ""), "notes": row.get("notes", ""),
        "value_scale": row["value_scale"],
        "protocol": {key: row[key] for key in (
            "protocol_id", "dataset_version", "split_id", "evaluation_mode", "preprocessing_id",
        )},
        "uncertainty": {"type": row.get("uncertainty_type") or None, "value": std, "is_95_ci": False},
        "evidence": {
            "status": "verified", "run_by": "bciarena", "ranking_eligible": True,
            "run_id": row["run_id"], "verified_at": row["verified_at"],
            "verifier": row["verifier"], "verification_method": row["verification_method"],
            "evidence_url": row.get("evidence_url") or None,
            "artifact_sha256": row.get("artifact_sha256") or None,
            "code_commit": row.get("code_commit") or None,
        },
    }


def export_all(news_items: list[dict] | None = None, run_at: str | None = None,
               with_ci: bool = True, output_dir: Path | None = None,
               feed_path: Path | None = None) -> dict:
    """Create compatible JSON artifacts without cross-task aggregate scoring.

    ``with_ci`` is retained for callers but ignored: standard deviation is never
    converted into a confidence interval.
    """
    run_at = run_at or datetime.now(timezone.utc).isoformat(timespec="seconds")
    validate_repository(DATA)
    models, benchmarks, literature_results = load_catalogs()
    verified_results = load_verified_results()
    output_dir = output_dir or SITE_DATA
    feed_path = feed_path or (PUBLIC / "feed.xml")
    m_by = {m["slug"]: m for m in models}
    b_by = {b["slug"]: b for b in benchmarks}
    families = {b["slug"]: b["task_family"] for b in benchmarks}
    board = build_verified_leaderboard(verified_results, b_by)

    # Literature measurements remain available in the catalog; only first-party
    # verified rows are handed to the leaderboard builder.
    by_model: dict[str, list[dict]] = {}
    by_bench: dict[str, list[dict]] = {}
    details = [_legacy_result_dict(row) for row in literature_results]
    details.extend(_verified_result_dict(row) for row in verified_results)
    for detail in details:
        detail["metric_label"] = METRIC_LABEL.get(detail["metric"], detail["metric"])
        by_model.setdefault(detail["model"], []).append(detail)
        by_bench.setdefault(detail["benchmark"], []).append(detail)

    lb_rows = []
    for row in board["models"]:
        m = m_by[row["slug"]]
        lb_rows.append({
            **row,
            "name": m["name"], "variant": m.get("variant"), "org": m.get("org"), "year": m.get("year"),
            "modality": m.get("modality"), "params_m": m.get("params_m"),
            "open_weights": bool(m.get("weights_url")), "license": m.get("license"),
            "reproducible": m.get("reproducible"), "baseline": bool(m.get("baseline", False)),
            "families": sorted({families[b] for b in {x["benchmark"] for x in by_model.get(row["slug"], [])}}),
        })

    # 没有任何 primary_metric 结果的模型也要出现在目录里（只是不进榜）
    listed = {r["slug"] for r in lb_rows}
    unranked = [m["slug"] for m in models if m["slug"] not in listed]

    stats = {
        "n_models": len(models), "n_ranked": len(listed), "n_benchmarks": len(benchmarks),
        "n_results": len(literature_results) + len(verified_results), "n_tasks_scored": len(board["tasks"]),
        "n_verified": len(verified_results),
        "n_reproduced": sum(1 for r in literature_results if r.tier == "reproduced"),
        "n_reported": sum(1 for r in literature_results if r.tier == "reported"),
    }

    _dump(output_dir / "leaderboard.json", {
        "generatedAt": run_at, "stats": stats, "rows": lb_rows, "unranked": unranked,
        "tasks": board["tasks"], "h2h": board["h2h"], "params": board["params"],
        "familyLabel": FAMILY_LABEL, "metricLabel": METRIC_LABEL,
        "evidencePolicy": {
            "rankingTier": "verified", "runBy": "bciarena",
            "requiredProtocolFields": [
                "protocol_id", "dataset_version", "split_id", "evaluation_mode", "preprocessing_id",
            ],
            "crossTaskAggregation": False,
            "literatureResultsRanked": False,
        },
    })
    _dump(output_dir / "models.json", {m["slug"]: {**m, "results": by_model.get(m["slug"], [])} for m in models})
    _dump(output_dir / "benchmarks.json", {b["slug"]: {**b, "family_label": FAMILY_LABEL.get(b["task_family"], b["task_family"]),
                                                     "results": by_bench.get(b["slug"], [])} for b in benchmarks})

    news = [item for item in (news_items or [])
            if item.get("approval_status") == "approved"
            and int(item.get("relevance", 0)) >= 2
            and item.get("curated_summary")]
    for item in news:
        item["summary"] = item["curated_summary"]
        item["llm_summary"] = None
    _dump(output_dir / "news.json", {"generatedAt": run_at, "items": news[:200]})
    _write_feed(feed_path, news[:50], run_at)
    return {"stats": stats, "news": len(news)}


def _write_feed(path: Path, items: list[dict], run_at: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    now = format_datetime(datetime.now(timezone.utc))
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<rss version="2.0"><channel>',
        "<title>BCI Report — BCI news digest</title>",
        "<link>https://bci.report/news/</link>",
        "<description>Headlines and links about brain-computer interfaces, aggregated daily. "
        "Summaries are short excerpts; follow the link for the full story.</description>",
        f"<lastBuildDate>{now}</lastBuildDate>",
    ]
    for it in items:
        pub = it.get("published")
        try:
            pub_rfc = format_datetime(datetime.fromisoformat(pub)) if pub else now
        except ValueError:
            pub_rfc = now
        desc = it.get("curated_summary") or ""
        parts.append(
            "<item>"
            f"<title>{escape(it['title'])}</title><link>{escape(it['link'])}</link>"
            f"<guid isPermaLink=\"false\">{escape(it['id'])}</guid><pubDate>{pub_rfc}</pubDate>"
            f"<source url=\"{escape(it['link'])}\">{escape(it['source'])}</source>"
            f"<description>{escape(desc)}</description></item>")
    parts.append("</channel></rss>")
    path.write_text("\n".join(parts), encoding="utf-8")
