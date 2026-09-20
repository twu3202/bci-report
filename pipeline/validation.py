"""Validate catalog data and the separate, site-verified result store."""
from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Iterable, Mapping
from urllib.parse import urlsplit

import yaml

PROTOCOL_FIELDS = (
    "protocol_id",
    "dataset_version",
    "split_id",
    "evaluation_mode",
    "preprocessing_id",
)
EVIDENCE_FIELDS = (
    "run_id",
    "verified_at",
    "verifier",
    "verification_method",
)
VERIFIED_COLUMNS = (
    "model_slug", "benchmark_slug", "metric", "value", "value_scale", "std",
    "uncertainty_type", "n_seeds", "tier", "run_by", *PROTOCOL_FIELDS,
    *EVIDENCE_FIELDS, "evidence_url", "artifact_sha256", "code_commit",
    "source_title", "source_url", "table_ref", "notes", "date_added",
)
EVALUATION_MODES = {
    "scratch",
    "zero_shot",
    "frozen_linear_probe",
    "partial_finetune",
    "full_finetune",
}


class ValidationError(ValueError):
    """Raised when source data cannot safely enter an export."""


@dataclass(frozen=True)
class Catalogs:
    models: list[dict]
    benchmarks: list[dict]

    @property
    def model_by_slug(self) -> dict[str, dict]:
        return {row["slug"]: row for row in self.models}

    @property
    def benchmark_by_slug(self) -> dict[str, dict]:
        return {row["slug"]: row for row in self.benchmarks}


def read_yaml_list(path: Path) -> list[dict]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or []
    if not isinstance(data, list) or not all(isinstance(x, dict) for x in data):
        raise ValidationError(f"{path}: expected a YAML list of objects")
    return data


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def validate_catalogs(models: list[dict], benchmarks: list[dict]) -> Catalogs:
    for label, rows in (("model", models), ("benchmark", benchmarks)):
        slugs = [str(row.get("slug", "")).strip() for row in rows]
        missing = [i + 1 for i, slug in enumerate(slugs) if not slug]
        duplicates = sorted({slug for slug in slugs if slugs.count(slug) > 1})
        if missing or duplicates:
            raise ValidationError(f"{label} catalog: missing slugs={missing}; duplicate slugs={duplicates}")
    for row in benchmarks:
        required = ("primary_metric", "task_family")
        absent = [key for key in required if not str(row.get(key, "")).strip()]
        if absent:
            raise ValidationError(f"benchmark {row['slug']}: missing {', '.join(absent)}")
        if row["primary_metric"] not in row.get("metrics", []):
            raise ValidationError(f"benchmark {row['slug']}: primary_metric is absent from metrics")
    return Catalogs(models, benchmarks)


def _require(row: Mapping[str, object], fields: Iterable[str], where: str) -> None:
    missing = [key for key in fields if not str(row.get(key, "")).strip()]
    if missing:
        raise ValidationError(f"{where}: missing required fields: {', '.join(missing)}")


def _number(value: object, name: str, where: str) -> float:
    try:
        parsed = float(str(value))
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{where}: {name} must be numeric") from exc
    if not math.isfinite(parsed):
        raise ValidationError(f"{where}: {name} must be finite")
    return parsed


def validate_legacy_results(rows: list[dict[str, str]], catalogs: Catalogs) -> None:
    """Validate literature rows without treating them as ranking evidence."""
    models, benchmarks = catalogs.model_by_slug, catalogs.benchmark_by_slug
    for index, row in enumerate(rows, 2):
        where = f"results.csv:{index}"
        _require(row, ("model_slug", "benchmark_slug", "metric", "value", "tier"), where)
        if row["model_slug"] not in models:
            raise ValidationError(f"{where}: unknown model_slug {row['model_slug']!r}")
        benchmark = benchmarks.get(row["benchmark_slug"])
        if not benchmark:
            raise ValidationError(f"{where}: unknown benchmark_slug {row['benchmark_slug']!r}")
        if row["metric"] not in benchmark.get("metrics", []):
            raise ValidationError(f"{where}: metric {row['metric']!r} is not registered for the benchmark")
        _number(row["value"], "value", where)
        if row.get("std"):
            _number(row["std"], "std", where)
        if row["tier"] not in {"reported", "reproduced", "verified"}:
            raise ValidationError(f"{where}: invalid tier {row['tier']!r}")


def validate_verified_results(rows: list[dict[str, str]], catalogs: Catalogs) -> None:
    """Require complete protocol identity and first-party verification evidence."""
    models, benchmarks = catalogs.model_by_slug, catalogs.benchmark_by_slug
    seen: set[tuple[str, ...]] = set()
    for index, row in enumerate(rows, 2):
        where = f"verified_results.csv:{index}"
        _require(row, (
            "model_slug", "benchmark_slug", "metric", "value", "value_scale",
            "tier", "run_by", *PROTOCOL_FIELDS, *EVIDENCE_FIELDS,
        ), where)
        if row["tier"] != "verified" or row["run_by"] != "bciarena":
            raise ValidationError(f"{where}: ranking evidence must be verified and run_by=bciarena")
        if row["model_slug"] not in models:
            raise ValidationError(f"{where}: unknown model_slug {row['model_slug']!r}")
        benchmark = benchmarks.get(row["benchmark_slug"])
        if not benchmark:
            raise ValidationError(f"{where}: unknown benchmark_slug {row['benchmark_slug']!r}")
        if row["metric"] != benchmark["primary_metric"]:
            raise ValidationError(f"{where}: only the registered primary_metric may enter ranking evidence")
        value = _number(row["value"], "value", where)
        if row["value_scale"] not in {"percent", "unit_interval", "raw"}:
            raise ValidationError(f"{where}: invalid value_scale {row['value_scale']!r}")
        if row["value_scale"] == "percent" and not 0 <= value <= 100:
            raise ValidationError(f"{where}: percent value must be between 0 and 100")
        if row["value_scale"] == "unit_interval" and not 0 <= value <= 1:
            raise ValidationError(f"{where}: unit_interval value must be between 0 and 1")
        if row["evaluation_mode"] not in EVALUATION_MODES:
            allowed = ", ".join(sorted(EVALUATION_MODES))
            raise ValidationError(f"{where}: evaluation_mode must be one of: {allowed}")
        if row.get("std"):
            std = _number(row["std"], "std", where)
            if std < 0 or row.get("uncertainty_type") != "standard_deviation":
                raise ValidationError(f"{where}: std requires uncertainty_type=standard_deviation")
        elif row.get("uncertainty_type"):
            raise ValidationError(f"{where}: uncertainty_type requires std")
        if row.get("n_seeds"):
            try:
                if int(row["n_seeds"]) < 1 or str(int(row["n_seeds"])) != row["n_seeds"].strip():
                    raise ValueError
            except ValueError as exc:
                raise ValidationError(f"{where}: n_seeds must be a positive integer") from exc
        try:
            verified_at = datetime.fromisoformat(row["verified_at"].replace("Z", "+00:00"))
            if verified_at.tzinfo is None:
                raise ValueError
        except ValueError as exc:
            raise ValidationError(f"{where}: verified_at must be an ISO 8601 timestamp with timezone") from exc
        if row.get("date_added"):
            try:
                date.fromisoformat(row["date_added"])
            except ValueError as exc:
                raise ValidationError(f"{where}: date_added must use YYYY-MM-DD") from exc
        for field in (*PROTOCOL_FIELDS, *EVIDENCE_FIELDS):
            if "\n" in row[field] or "\r" in row[field]:
                raise ValidationError(f"{where}: {field} must be a single line")
        if not row.get("evidence_url") and not row.get("artifact_sha256"):
            raise ValidationError(f"{where}: evidence_url or artifact_sha256 is required")
        for field in ("evidence_url", "source_url"):
            if row.get(field) and urlsplit(row[field]).scheme.lower() not in {"http", "https"}:
                raise ValidationError(f"{where}: {field} must be an HTTP(S) URL")
        if row.get("artifact_sha256") and (
            len(row["artifact_sha256"]) != 64
            or any(ch not in "0123456789abcdefABCDEF" for ch in row["artifact_sha256"])
        ):
            raise ValidationError(f"{where}: artifact_sha256 must be 64 hexadecimal characters")
        key = tuple(row[field] for field in (
            "model_slug", "benchmark_slug", "metric", *PROTOCOL_FIELDS,
        ))
        if key in seen:
            raise ValidationError(f"{where}: duplicate model result in one comparison protocol")
        seen.add(key)


def validate_repository(data_dir: Path) -> Catalogs:
    models = read_yaml_list(data_dir / "models.yaml")
    benchmarks = read_yaml_list(data_dir / "benchmarks.yaml")
    catalogs = validate_catalogs(models, benchmarks)
    validate_legacy_results(read_csv(data_dir / "results.csv"), catalogs)
    validate_verified_results(read_csv(data_dir / "verified_results.csv"), catalogs)
    return catalogs
