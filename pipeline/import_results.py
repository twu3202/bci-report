#!/usr/bin/env python3
"""Validate and append one manually reviewed result submission."""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import yaml

from validation import VERIFIED_COLUMNS, ValidationError, read_csv, validate_repository, validate_verified_results

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"


def expand_submission(document: dict) -> list[dict[str, str]]:
    if document.get("schema_version") != 1 or not isinstance(document.get("submission"), dict):
        raise ValidationError("submission must contain schema_version: 1 and a submission object")
    shared = document["submission"]
    result_fields = {
        "model_slug", "benchmark_slug", "metric", "value", "value_scale",
        "std", "uncertainty_type", "n_seeds",
    }
    shared_fields = set(VERIFIED_COLUMNS) - result_fields - {"tier", "run_by"}
    unknown_shared = sorted(set(shared) - shared_fields - {"results"})
    if unknown_shared:
        raise ValidationError(f"unknown submission fields: {', '.join(unknown_shared)}")
    measurements = shared.get("results")
    if not isinstance(measurements, list) or not measurements:
        raise ValidationError("submission.results must contain at least one measurement")
    rows = []
    for measurement in measurements:
        if not isinstance(measurement, dict):
            raise ValidationError("each submission result must be an object")
        unknown_result = sorted(set(measurement) - result_fields)
        if unknown_result:
            raise ValidationError(f"unknown result fields: {', '.join(unknown_result)}")
        merged = {key: shared.get(key, "") for key in VERIFIED_COLUMNS}
        merged.update(measurement)
        merged["tier"] = "verified"
        merged["run_by"] = "bciarena"
        merged.pop("results", None)
        rows.append({key: "" if merged.get(key) is None else str(merged.get(key, "")) for key in VERIFIED_COLUMNS})
    return rows


def import_file(source: Path, destination: Path, check_only: bool = False) -> int:
    catalogs = validate_repository(DATA)
    document = yaml.safe_load(source.read_text(encoding="utf-8")) or {}
    rows = expand_submission(document)
    existing = read_csv(destination)
    validate_verified_results(existing + rows, catalogs)
    if check_only:
        return len(rows)
    write_header = not destination.exists() or destination.stat().st_size == 0
    with destination.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=VERIFIED_COLUMNS)
        if write_header:
            writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("submission", type=Path)
    parser.add_argument("--check", action="store_true", help="validate without changing verified_results.csv")
    parser.add_argument("--output", type=Path, default=DATA / "verified_results.csv")
    args = parser.parse_args()
    count = import_file(args.submission, args.output, check_only=args.check)
    action = "validated" if args.check else "imported"
    print(f"{action} {count} verified measurement(s)")


if __name__ == "__main__":
    main()
