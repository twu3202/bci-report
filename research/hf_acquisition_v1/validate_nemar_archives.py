#!/usr/bin/env python3
"""Validate and safely publish a selected subset of one NEMAR ZIP archive."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import sys
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import BinaryIO, Iterable


CHUNK = 8 * 1024 * 1024
MAX_ARCHIVE_MEMBERS = 100_000
EEG_SUFFIXES = {".set", ".bdf"}
BIDS_SUFFIXES = {".json", ".tsv"}
DOC_NAMES = {"readme", "readme.md", "readme.txt", "license", "license.md", "license.txt"}
EXCLUDED_COMPONENTS = {
    ".git", ".github", ".nemar", "code", "derivative", "derivatives", "source", "sourcedata"
}


class ValidationError(RuntimeError):
    pass


@dataclass(frozen=True)
class Expected:
    path: PurePosixPath
    size: int
    algorithm: str
    checksum: str


def safe_path(value: object) -> PurePosixPath:
    if not isinstance(value, str) or not value or "\x00" in value or "\\" in value:
        raise ValidationError(f"unsafe archive path: {value!r}")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in ("", ".", "..") for part in path.parts):
        raise ValidationError(f"unsafe archive path: {value!r}")
    return path


def selected(path: PurePosixPath) -> bool:
    lowered = {part.lower() for part in path.parts}
    if lowered & EXCLUDED_COMPONENTS:
        return False
    suffix = path.suffix.lower()
    return suffix in EEG_SUFFIXES | BIDS_SUFFIXES or path.name.lower() in DOC_NAMES


def load_expected(path: Path) -> dict[PurePosixPath, Expected]:
    try:
        records = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValidationError(f"cannot read metadata manifest: {exc}") from exc
    if not isinstance(records, list):
        raise ValidationError("metadata manifest must be a JSON array")
    result: dict[PurePosixPath, Expected] = {}
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise ValidationError(f"metadata record {index} is not an object")
        member_path = safe_path(record.get("path"))
        if not selected(member_path):
            continue
        size = record.get("size")
        algorithm = record.get("checksum_algorithm")
        checksum = record.get("checksum")
        if isinstance(size, bool) or not isinstance(size, int) or size < 0:
            raise ValidationError(f"invalid size for {member_path}")
        lengths = {"sha256": 64, "git": 40}
        if algorithm not in lengths or not isinstance(checksum, str) or len(checksum) != lengths[algorithm]:
            raise ValidationError(f"unsupported or malformed checksum for {member_path}")
        try:
            int(checksum, 16)
        except ValueError as exc:
            raise ValidationError(f"non-hex checksum for {member_path}") from exc
        if member_path in result:
            raise ValidationError(f"duplicate metadata path: {member_path}")
        result[member_path] = Expected(member_path, size, algorithm, checksum.lower())
    eeg_count = sum(item.path.suffix.lower() in EEG_SUFFIXES for item in result.values())
    if not result or not eeg_count:
        raise ValidationError("selection is empty or contains no raw EEG files")
    return result


def regular_member(info: zipfile.ZipInfo) -> bool:
    mode = (info.external_attr >> 16) & 0xFFFF
    kind = stat.S_IFMT(mode)
    return kind in (0, stat.S_IFREG)


def inspect_archive(
    archive: zipfile.ZipFile, expected: dict[PurePosixPath, Expected]
) -> dict[PurePosixPath, zipfile.ZipInfo]:
    infos = archive.infolist()
    if len(infos) > MAX_ARCHIVE_MEMBERS:
        raise ValidationError(f"archive member limit exceeded: {len(infos)}")
    safe_infos: list[tuple[PurePosixPath, zipfile.ZipInfo]] = []
    seen_names: set[PurePosixPath] = set()
    for info in infos:
        member_path = safe_path(info.filename.rstrip("/"))
        if member_path in seen_names:
            raise ValidationError(f"duplicate archive member: {member_path}")
        seen_names.add(member_path)
        mode = (info.external_attr >> 16) & 0xFFFF
        if stat.S_IFMT(mode) == stat.S_IFLNK:
            raise ValidationError(f"archive contains symlink: {member_path}")
        if info.flag_bits & 0x1:
            raise ValidationError(f"archive contains encrypted member: {member_path}")
        if info.is_dir():
            continue
        safe_infos.append((member_path, info))

    # NEMAR ZIPs may wrap the repository in one top-level directory. Match each
    # metadata path exactly or beneath one common wrapper, with no ambiguity.
    by_path = {member_path: info for member_path, info in safe_infos}
    anchor = max(expected, key=lambda item: len(item.parts))
    candidate_wrappers: set[tuple[str, ...]] = set()
    for member_path in by_path:
        if member_path == anchor:
            candidate_wrappers.add(())
        elif (
            len(member_path.parts) > len(anchor.parts)
            and member_path.parts[-len(anchor.parts):] == anchor.parts
        ):
            candidate_wrappers.add(member_path.parts[:-len(anchor.parts)])
    valid_wrappers = [
        wrapper for wrapper in candidate_wrappers
        if all(PurePosixPath(*(wrapper + expected_path.parts)) in by_path for expected_path in expected)
    ]
    if len(valid_wrappers) != 1:
        raise ValidationError(
            f"cohort incomplete or ambiguous: found {len(valid_wrappers)} consistent archive roots"
        )
    wrapper = valid_wrappers[0]
    matched: dict[PurePosixPath, zipfile.ZipInfo] = {}
    for expected_path, record in expected.items():
        info = by_path[PurePosixPath(*(wrapper + expected_path.parts))]
        if not regular_member(info):
            raise ValidationError(f"selected member is not a regular file: {expected_path}")
        if info.file_size != record.size:
            raise ValidationError(
                f"size mismatch for {expected_path}: archive={info.file_size}, expected={record.size}"
            )
        matched[expected_path] = info

    # Any other eligible raw/BIDS member would make the selected cohort differ
    # from the pinned metadata manifest.
    reverse = {info.filename for info in matched.values()}
    for member_path, info in safe_infos:
        logical = PurePosixPath(*member_path.parts[len(wrapper):]) if tuple(member_path.parts[:len(wrapper)]) == wrapper else None
        if logical is not None and selected(logical) and info.filename not in reverse:
            raise ValidationError(f"unpinned selected member in archive: {logical}")
    return matched


def digest_stream(source: BinaryIO, output: BinaryIO, expected: Expected) -> str:
    if expected.algorithm == "sha256":
        digest = hashlib.sha256()
    else:
        digest = hashlib.sha1()  # nosec - Git object identity from pinned metadata
        digest.update(f"blob {expected.size}\0".encode("ascii"))
    written = 0
    while chunk := source.read(CHUNK):
        written += len(chunk)
        if written > expected.size:
            raise ValidationError(f"expanded size exceeds metadata for {expected.path}")
        output.write(chunk)
        digest.update(chunk)
    if written != expected.size:
        raise ValidationError(
            f"expanded size mismatch for {expected.path}: got={written}, expected={expected.size}"
        )
    return digest.hexdigest()


def reject_output_symlinks(path: Path) -> None:
    current = Path(path.anchor)
    for part in path.absolute().parts[1:]:
        current /= part
        if current.is_symlink():
            raise ValidationError(f"output path contains symlink: {current}")


def extract_archive(
    archive_path: Path, metadata_path: Path, destination: Path, inspect_only: bool = False
) -> dict[str, int | str]:
    if archive_path.is_symlink() or not archive_path.is_file():
        raise ValidationError("archive must be an existing regular non-symlink file")
    expected = load_expected(metadata_path)
    with zipfile.ZipFile(archive_path, "r") as archive:
        matched = inspect_archive(archive, expected)
        summary: dict[str, int | str] = {
            "status": "validated" if inspect_only else "extracted",
            "selected_files": len(expected),
            "raw_eeg_files": sum(x.path.suffix.lower() in EEG_SUFFIXES for x in expected.values()),
            "selected_bytes": sum(x.size for x in expected.values()),
        }
        if inspect_only:
            with open(os.devnull, "wb") as sink:
                for logical_path, info in matched.items():
                    with archive.open(info, "r") as source:
                        actual = digest_stream(source, sink, expected[logical_path])
                    if actual != expected[logical_path].checksum:
                        raise ValidationError(f"checksum mismatch for {logical_path}")
            return summary
        if destination.exists() or destination.is_symlink():
            raise ValidationError(f"destination already exists: {destination}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        reject_output_symlinks(destination.parent)
        staging = Path(tempfile.mkdtemp(prefix=f".{destination.name}.staging-", dir=destination.parent))
        try:
            for logical_path, info in matched.items():
                record = expected[logical_path]
                output_path = staging.joinpath(*logical_path.parts)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                reject_output_symlinks(output_path.parent)
                with archive.open(info, "r") as source, output_path.open("xb") as output:
                    actual = digest_stream(source, output, record)
                if actual != record.checksum:
                    raise ValidationError(f"checksum mismatch for {logical_path}")
            os.replace(staging, destination)
        except Exception:
            shutil.rmtree(staging, ignore_errors=True)
            raise
    return summary


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--metadata-manifest", required=True, type=Path)
    parser.add_argument("--destination", required=True, type=Path)
    parser.add_argument("--inspect-only", action="store_true")
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        result = extract_archive(
            args.archive, args.metadata_manifest, args.destination, args.inspect_only
        )
    except (ValidationError, OSError, zipfile.BadZipFile, RuntimeError) as exc:
        print(f"NEMAR archive validation failed; archive preserved: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
