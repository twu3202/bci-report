"""Incremental RSS ingestion with a separate, manual publication gate.

Feed excerpts are retained as source material in SQLite. Only explicitly approved
items with a human-written curated summary are returned for site export.
"""
from __future__ import annotations

import calendar
import hashlib
import html
import json
import re
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import parse_qsl, quote, unquote, urlencode, urlsplit, urlunsplit
from urllib.request import Request, urlopen

import feedparser
import yaml

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "news.db"
SOURCES = ROOT / "pipeline" / "sources.yaml"
CURATED = ROOT / "data" / "news_curated.yaml"
UA = "bcireport-bot/0.1 (+https://bci.report; news aggregator, headlines+links only)"
MAX_FEED_BYTES = 8 * 1024 * 1024

SCHEMA = """
CREATE TABLE IF NOT EXISTS items (
  id TEXT PRIMARY KEY,            -- sha1(link 规范化)
  source TEXT NOT NULL,
  category TEXT NOT NULL,         -- company | research | policy | media | community
  lang TEXT NOT NULL,
  title TEXT NOT NULL,
  link TEXT NOT NULL,
  published TEXT,                 -- ISO 8601 UTC
  fetched TEXT NOT NULL,
  summary TEXT,                   -- 来源自带摘要（已去 HTML、截断）
  llm_summary TEXT,               -- 可选：LLM 两行摘要
  tags TEXT,                      -- JSON 数组
  relevance INTEGER NOT NULL DEFAULT 0,
  approval_status TEXT NOT NULL DEFAULT 'pending',
  curated_title TEXT,
  curated_summary TEXT,
  reviewed_at TEXT,
  reviewer TEXT
);
CREATE INDEX IF NOT EXISTS idx_items_pub ON items(published DESC);
CREATE TABLE IF NOT EXISTS feed_state (
  url TEXT PRIMARY KEY,
  etag TEXT,
  modified TEXT,
  checked TEXT NOT NULL
);
"""

TAG_RULES = [
    ("invasive", r"\b(implant|electrode array|Utah array|sEEG|ECoG|intracortical|Neuralink|Synchron|Paradromics|Precision Neuroscience|Blackrock)\b|植入|侵入式"),
    ("non-invasive", r"\bEEG\b|electroencephalog|fNIRS|MEG\b|non-?invasive|非侵入|脑电"),
    ("foundation-model", r"foundation model|large brain model|pretrain|self-supervised|transformer|基础模型|大模型|预训练"),
    ("clinical", r"\bFDA\b|clinical trial|patient|paralys|ALS\b|stroke|epilep|NMPA|临床|患者|药监"),
    ("policy", r"\bpolicy\b|regulat|standard|guideline|工信部|政策|标准|监管|医保"),
    ("funding", r"\braise[sd]?\b|funding|Series [A-E]|valuation|IPO|融资|估值"),
    ("dataset", r"\bdataset\b|corpus|benchmark|leaderboard|数据集|基准|榜"),
]


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(items)")}
    migrations = {
        "relevance": "INTEGER NOT NULL DEFAULT 0",
        "approval_status": "TEXT NOT NULL DEFAULT 'pending'",
        "curated_title": "TEXT",
        "curated_summary": "TEXT",
        "reviewed_at": "TEXT",
        "reviewer": "TEXT",
    }
    for name, declaration in migrations.items():
        if name not in columns:
            conn.execute(f"ALTER TABLE items ADD COLUMN {name} {declaration}")
    conn.commit()
    return conn


def load_sources(only_verified: bool = True) -> list[dict]:
    srcs = yaml.safe_load(SOURCES.read_text(encoding="utf-8")) or []
    return [s for s in srcs if s.get("type") in ("rss", "atom") and (s.get("verified", True) or not only_verified)]


def _norm_link(url: str) -> str:
    """Return a stable HTTP(S) URL for deduplication and review matching."""
    try:
        parts = urlsplit((url or "").strip())
        if parts.scheme.lower() not in {"http", "https"} or not parts.hostname:
            return ""
        host = parts.hostname.encode("idna").decode("ascii").lower()
        port = parts.port
        if port and not ((parts.scheme.lower() == "http" and port == 80) or
                         (parts.scheme.lower() == "https" and port == 443)):
            host = f"{host}:{port}"
        # Collapse only real separators, then normalise each segment on its own so
        # an escaped %2F stays escaped. Doing it the other way round made the
        # function non-idempotent (a second pass returned a different key, so a
        # curated review could attach to the wrong article or to none) and let
        # ".../a%2F%2Fb" collide with the distinct permalink ".../a/b".
        segments = re.sub(r"/{2,}", "/", parts.path or "/").split("/")
        path = "/".join(quote(unquote(s), safe=":@!$&'()*+,;=-._~") for s in segments)
        if path != "/":
            path = path.rstrip("/")
        tracking = {"fbclid", "gclid", "dclid", "ref", "ref_src", "mc_cid", "mc_eid"}
        query = []
        for key, value in parse_qsl(parts.query, keep_blank_values=True):
            lower = key.lower()
            if lower.startswith("utm_") or lower in tracking:
                continue
            query.append((key, value))
        return urlunsplit((parts.scheme.lower(), host, path, urlencode(sorted(query)), ""))
    except (UnicodeError, ValueError):
        return ""


def _strip_html(s: str, limit: int = 300) -> str:
    s = re.sub(r"<[^>]+>", " ", s or "")
    s = html.unescape(re.sub(r"\s+", " ", s)).strip()
    return s[:limit].rsplit(" ", 1)[0] + "…" if len(s) > limit else s


def _iso(entry) -> str | None:
    for k in ("published_parsed", "updated_parsed"):
        t = entry.get(k)
        if t:
            # Feedparser's struct_time is already UTC. mktime would reinterpret it
            # in the host's local timezone and silently shift publication times.
            return datetime.fromtimestamp(calendar.timegm(t), tz=timezone.utc).isoformat(timespec="seconds")
    return None


def _tags(text: str) -> list[str]:
    return [tag for tag, pat in TAG_RULES if re.search(pat, text, re.I)]


def _relevance(text: str) -> int:
    core = re.search(r"brain[- ]computer interface|\bBCI\b|脑机接口|neural implant|Neuralink|Synchron", text, re.I)
    eeg = re.search(r"\bEEG\b|electroencephalog|脑电|\bECoG\b|\bsEEG\b", text, re.I)
    benchmark = re.search(r"foundation model|pretrain|decoder|benchmark|clinical trial|神经解码|基础模型", text, re.I)
    if core:
        return 3
    if eeg and benchmark:
        return 2
    if eeg:
        return 1
    return 0


def _download_feed(conn: sqlite3.Connection, source: dict, timeout: float):
    state = conn.execute("SELECT etag, modified FROM feed_state WHERE url = ?", (source["url"],)).fetchone()
    headers = {"User-Agent": UA, "Accept": "application/atom+xml, application/rss+xml, application/xml, text/xml"}
    if state and state["etag"]:
        headers["If-None-Match"] = state["etag"]
    if state and state["modified"]:
        headers["If-Modified-Since"] = state["modified"]
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    try:
        with urlopen(Request(source["url"], headers=headers), timeout=timeout) as response:
            length = response.headers.get("Content-Length")
            if length and int(length) > MAX_FEED_BYTES:
                raise RuntimeError("feed exceeds size limit")
            payload = response.read(MAX_FEED_BYTES + 1)
            if len(payload) > MAX_FEED_BYTES:
                raise RuntimeError("feed exceeds size limit")
            etag = response.headers.get("ETag")
            modified = response.headers.get("Last-Modified")
    except HTTPError as exc:
        if exc.code != 304:
            raise
        conn.execute(
            "INSERT INTO feed_state(url,etag,modified,checked) VALUES(?,?,?,?) "
            "ON CONFLICT(url) DO UPDATE SET checked=excluded.checked",
            (source["url"], state["etag"] if state else None, state["modified"] if state else None, now),
        )
        return None
    conn.execute(
        "INSERT INTO feed_state(url,etag,modified,checked) VALUES(?,?,?,?) "
        "ON CONFLICT(url) DO UPDATE SET etag=excluded.etag, modified=excluded.modified, checked=excluded.checked",
        (source["url"], etag, modified, now),
    )
    return feedparser.parse(payload)


def fetch_all(conn: sqlite3.Connection, max_per_source: int = 40, verbose: bool = True,
              timeout: float = 15.0) -> dict:
    stats = {"sources": 0, "new": 0, "not_modified": 0, "failed": []}
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    for s in load_sources():
        stats["sources"] += 1
        try:
            feed = _download_feed(conn, s, timeout)
            if feed is None:
                stats["not_modified"] += 1
                continue
            if feed.bozo and not feed.entries:
                raise RuntimeError(str(getattr(feed, "bozo_exception", "bozo")))
        except Exception as e:  # noqa: BLE001
            stats["failed"].append({"source": s["name"], "error": str(e)[:160]})
            continue
        n_new = 0
        for e in feed.entries[:max_per_source]:
            link = _norm_link(e.get("link") or "")
            title = html.unescape((e.get("title") or "").strip())
            if not link or not title:
                continue
            iid = hashlib.sha1(link.encode()).hexdigest()[:16]
            summary = _strip_html(e.get("summary") or e.get("description") or "")
            text = f"{title} {summary}"
            tags = json.dumps(_tags(text), ensure_ascii=False)
            cur = conn.execute(
                "INSERT OR IGNORE INTO items(id,source,category,lang,title,link,published,fetched,summary,tags,relevance) "
                "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (iid, s["name"], s.get("category", "media"), s.get("lang", "en"), title, link,
                 _iso(e), now, summary, tags, _relevance(text)))
            n_new += cur.rowcount
        stats["new"] += n_new
        if verbose:
            print(f"  [news] {s['name']:<40} +{n_new:<3} ({len(feed.entries)} entries)")
        time.sleep(0.5)  # 抓取礼仪
    conn.commit()
    return stats


def sync_curated_reviews(conn: sqlite3.Connection, path: Path = CURATED) -> int:
    """Apply the checked-in URL whitelist as the complete publication approval set."""
    reviews = yaml.safe_load(path.read_text(encoding="utf-8")) or []
    if not isinstance(reviews, list):
        raise ValueError(f"{path}: expected a list")
    normalized: set[str] = set()
    approved = []
    for index, review in enumerate(reviews, 1):
        if not isinstance(review, dict) or review.get("approved") is not True:
            raise ValueError(f"{path}:{index}: every entry must explicitly set approved: true")
        link = _norm_link(str(review.get("link", "")))
        summary = str(review.get("summary", "")).strip()
        reviewer = str(review.get("reviewer", "")).strip()
        reviewed_at = str(review.get("reviewed_at", "")).strip()
        if not link or not summary or not reviewer or not reviewed_at:
            raise ValueError(f"{path}:{index}: link, summary, reviewer, and reviewed_at are required")
        try:
            stamp = datetime.fromisoformat(reviewed_at.replace("Z", "+00:00"))
            if stamp.tzinfo is None:
                raise ValueError
        except ValueError as exc:
            raise ValueError(f"{path}:{index}: reviewed_at must be an ISO 8601 timestamp with timezone") from exc
        if link in normalized:
            raise ValueError(f"{path}:{index}: duplicate normalized link")
        normalized.add(link)
        approved.append((review, link, summary, reviewer, reviewed_at))

    conn.execute(
        "UPDATE items SET approval_status='pending', curated_title=NULL, curated_summary=NULL, "
        "reviewed_at=NULL, reviewer=NULL WHERE approval_status='approved'"
    )
    item_ids: dict[str, list[str]] = {}
    for item in conn.execute("SELECT id, link FROM items"):
        item_ids.setdefault(_norm_link(item["link"]), []).append(item["id"])
    count = 0
    for review, link, summary, reviewer, reviewed_at in approved:
        for item_id in item_ids.get(link, []):
            cur = conn.execute(
                "UPDATE items SET approval_status='approved', curated_title=?, curated_summary=?, "
                "reviewed_at=?, reviewer=?, relevance=MAX(relevance, 2) WHERE id=?",
                (str(review.get("title", "")).strip() or None, summary, reviewed_at, reviewer, item_id),
            )
            count += cur.rowcount
    conn.commit()
    return count


def latest(conn: sqlite3.Connection, n: int = 200, approved_only: bool = True) -> list[dict]:
    where = "WHERE approval_status='approved' AND relevance >= 2 AND curated_summary IS NOT NULL" if approved_only else ""
    rows = conn.execute(
        f"SELECT * FROM items {where} ORDER BY COALESCE(published, fetched) DESC LIMIT ?", (n,)).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        if approved_only:
            d["title"] = d.get("curated_title") or d["title"]
            d["summary"] = d["curated_summary"]
            d["llm_summary"] = None
        d["tags"] = json.loads(d["tags"] or "[]")
        if not approved_only:
            d["llm_summary"] = json.loads(d["llm_summary"]) if d.get("llm_summary") else None
        d["evidence"] = {
            "approval_status": d.get("approval_status"),
            "reviewer": d.get("reviewer"),
            "reviewed_at": d.get("reviewed_at"),
            "summary_source": "human_curated" if approved_only else "source_feed",
        }
        out.append(d)
    return out
