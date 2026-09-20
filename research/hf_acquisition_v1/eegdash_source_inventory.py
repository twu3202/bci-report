#!/usr/bin/env python3
"""Build revision-aware OpenNeuro S3 manifests from GitHub source archives."""

import argparse
import hashlib
import json
import os
import re
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path


ANNEX = re.compile(r"(?P<algo>SHA256E|MD5E)-s(?P<size>\d+)--(?P<hash>[0-9a-f]+)\.")


def s3_objects(xml_path: Path, dataset_id: str):
    ns = {"s3": "http://s3.amazonaws.com/doc/2006-03-01/"}
    out = {}
    xml_paths = sorted(xml_path.glob("*.xml")) if xml_path.is_dir() else [xml_path]
    for page in xml_paths:
        root = ET.parse(page).getroot()
        for item in root.findall("s3:Contents", ns):
            key = item.findtext("s3:Key", namespaces=ns)
            if not key.startswith(dataset_id + "/"):
                continue
            out[key[len(dataset_id) + 1 :]] = {
                "expected_bytes": int(item.findtext("s3:Size", namespaces=ns)),
                "md5": item.findtext("s3:ETag", namespaces=ns).strip('"'),
            }
    return out


def wanted(dataset_id: str, path: str):
    root_metadata = {
        "README", "README.md", "CHANGES", "dataset_description.json",
        "participants.tsv", "participants.json", "task-nback_events.json",
        "task-arithmetic_events.json",
    }
    if path in root_metadata:
        return True
    if "/" not in path and (re.match(r"task-.*\.json$", path) or path in {"eeg.json", "electrodes.tsv", "coordsystem.json"}):
        return True
    if dataset_id == "ds005028":
        return path.endswith("_eeg.edf")
    return bool(re.match(r"sub-[^/]+/(?:ses-[^/]+/)?eeg/", path))


def build(dataset_id: str, revision: str, source_dir: Path, s3_xml: Path):
    objects = s3_objects(s3_xml, dataset_id)
    assets = []
    mismatches = []
    for entry in sorted(source_dir.rglob("*")):
        if entry.is_dir():
            continue
        rel = entry.relative_to(source_dir).as_posix()
        if not wanted(dataset_id, rel):
            continue
        s3 = objects.get(rel)
        if s3 is None:
            mismatches.append({"relative_path": rel, "reason": "missing_current_s3_object"})
            continue
        asset = {
            "dataset_id": dataset_id,
            "relative_path": rel,
            "url": "https://s3.amazonaws.com/openneuro.org/" + urllib.parse.quote(dataset_id + "/" + rel),
            "expected_bytes": s3["expected_bytes"],
            "md5": s3["md5"],
            "source_revision": revision,
            "license_status": "verified_cc0",
        }
        if entry.is_symlink():
            match = ANNEX.search(os.readlink(entry))
            if not match:
                mismatches.append({"relative_path": rel, "reason": "unparsed_annex_pointer"})
                continue
            if match.group("algo") == "SHA256E":
                asset["sha256"] = match.group("hash")
            elif match.group("hash") != s3["md5"]:
                mismatches.append({
                    "relative_path": rel,
                    "reason": "git_annex_s3_md5_mismatch",
                    "git_md5": match.group("hash"),
                    "s3_md5": s3["md5"],
                })
                continue
            git_size = int(match.group("size"))
            if git_size != s3["expected_bytes"]:
                mismatches.append({
                    "relative_path": rel,
                    "reason": "git_annex_s3_size_mismatch",
                    "git_bytes": git_size,
                    "s3_bytes": s3["expected_bytes"],
                })
                continue
        else:
            data = entry.read_bytes()
            if len(data) != s3["expected_bytes"] or hashlib.md5(data).hexdigest() != s3["md5"]:
                mismatches.append({"relative_path": rel, "reason": "git_blob_s3_content_mismatch"})
                continue
            asset["sha256"] = hashlib.sha256(data).hexdigest()
        assets.append(asset)
    return {
        "dataset_id": dataset_id,
        "source_revision": revision,
        "status": "ready" if not mismatches else "hold",
        "asset_count": len(assets),
        "total_bytes": sum(x["expected_bytes"] for x in assets),
        "mismatches": mismatches,
        "assets": assets,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset_id")
    parser.add_argument("revision")
    parser.add_argument("source_dir", type=Path)
    parser.add_argument("s3_xml", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = build(args.dataset_id, args.revision, args.source_dir, args.s3_xml)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
