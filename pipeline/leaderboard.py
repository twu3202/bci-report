"""Build protocol-local rankings from first-party verified measurements only."""
from __future__ import annotations

from collections import defaultdict

from validation import PROTOCOL_FIELDS


def _group_id(row: dict[str, str]) -> tuple[str, ...]:
    # The numeric value is only comparable within one declared scale. A percent
    # value and a unit-interval value must never share ordering or rank.
    return (
        row["benchmark_slug"], row["metric"], row["value_scale"],
        *(row[field] for field in PROTOCOL_FIELDS),
    )


def build_verified_leaderboard(rows: list[dict[str, str]], benchmarks: dict[str, dict]) -> dict:
    """Rank only models measured under an identical, complete protocol.

    A group with fewer than two models is evidence for the catalog but is not a
    comparison and therefore produces no leaderboard row. No score is combined
    across datasets, tasks, metrics, or protocols.
    """
    groups: dict[tuple[str, ...], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[_group_id(row)].append(row)

    output_rows: list[dict] = []
    tasks: list[dict] = []
    for key in sorted(groups):
        group = groups[key]
        if len({row["model_slug"] for row in group}) < 2:
            continue
        (benchmark_slug, metric, value_scale, protocol_id, dataset_version,
         split_id, evaluation_mode, preprocessing_id) = key
        higher = bool(benchmarks[benchmark_slug].get("higher_is_better", True))
        ordered = sorted(group, key=lambda row: float(row["value"]), reverse=higher)
        comparison_id = "/".join(key)
        previous_value: float | None = None
        previous_rank = 0
        for position, row in enumerate(ordered, 1):
            value = float(row["value"])
            rank = previous_rank if previous_value == value else position
            previous_value, previous_rank = value, rank
            output_rows.append({
                # Existing leaderboard row keys remain available. Arena/Elo and
                # bootstrap CI are deliberately unset because this is a raw,
                # protocol-local metric rank.
                "slug": row["model_slug"], "rank": rank, "rating": None,
                "ci_low": None, "ci_high": None, "mean_norm": None,
                "n_tasks": 1, "best_tier": "verified", "provisional": False,
                "family_ratings": {},
                "score": value, "value_scale": value_scale,
                "std": float(row["std"]) if row.get("std") else None,
                "uncertainty_type": row.get("uncertainty_type") or None,
                "benchmark": benchmark_slug, "metric": metric,
                "comparison_id": comparison_id,
                "protocol": {field: row[field] for field in PROTOCOL_FIELDS},
                "evidence": {
                    "status": "verified", "run_by": "bciarena",
                    "run_id": row["run_id"], "verified_at": row["verified_at"],
                    "verifier": row["verifier"],
                    "verification_method": row["verification_method"],
                    "evidence_url": row.get("evidence_url") or None,
                    "artifact_sha256": row.get("artifact_sha256") or None,
                    "code_commit": row.get("code_commit") or None,
                },
            })
        tasks.append({
            "benchmark": benchmark_slug, "metric": metric,
            "n_models": len(ordered), "comparison_id": comparison_id,
            "value_scale": value_scale,
            "protocol": dict(zip(PROTOCOL_FIELDS, key[3:])),
        })
    return {
        "models": output_rows,
        "tasks": tasks,
        "h2h": {},
        "params": {
            "method": "within_protocol_raw_metric_rank",
            "cross_task_aggregation": False,
            "minimum_models_per_comparison": 2,
            "uncertainty": "std is displayed as standard deviation; no 95% CI is inferred",
        },
    }
