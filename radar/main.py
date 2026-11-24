"""Research Radar: run the pipeline and the CLI.

  fetch each stream -> drop seen ids -> score -> multi-match bonus -> rank
  -> draft top N -> render report -> (optionally download) -> mark seen -> save.

Also holds the two small bits of glue the pipeline needs: the seen-id dedupe
store and the optional open-access PDF download.

Flags:
  --dry-run    do everything except marking papers as seen (safe to re-run)
  --download   also save open-access PDFs locally (see config DOWNLOAD_* knobs)
  --canon      build the most-cited reading list instead (see report.py)
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path

import requests

from . import config, relevance, report
from .openalex import Paper, fetch_stream

SEEN_PATH = Path(__file__).resolve().parent.parent / "state" / "seen.json"


# --- Dedupe store ------------------------------------------------------------

class SeenStore:
    """Remember which OpenAlex work ids we've already reported (state/seen.json)."""

    def __init__(self, path: Path = SEEN_PATH):
        self.path = path
        self._seen: dict[str, str] = {}
        if path.exists():
            self._seen = json.loads(path.read_text(encoding="utf-8") or "{}").get("seen", {})

    def is_new(self, short_id: str) -> bool:
        return short_id not in self._seen

    def mark(self, short_id: str) -> None:
        self._seen[short_id] = date.today().isoformat()

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"updated": date.today().isoformat(), "seen": self._seen}
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


# --- Open-access PDF download (local --download only) ------------------------

def _safe(name: str, n: int = 60) -> str:
    s = re.sub(r"[^\w\- ]", "", name).strip().replace(" ", "-")
    return s[:n].rstrip("-") or "paper"


def _preprint(p: Paper) -> bool:
    return p.type == "preprint" or p.venue_type == "repository"


def _wanted_pdf(p: Paper) -> bool:
    """Peer-reviewed work clears DOWNLOAD_MIN_SCORE everywhere; a preprint also
    qualifies (down to DOWNLOAD_PREPRINT_MIN_SCORE) in the chosen preprint areas."""
    if p.score >= config.DOWNLOAD_MIN_SCORE:
        return True
    return (_preprint(p) and p.score >= config.DOWNLOAD_PREPRINT_MIN_SCORE
            and (p.topic_id in config.PREPRINT_TOPICS
                 or p.stream in config.PREPRINT_STREAMS))


def download_oa(papers: list[Paper]) -> list[Paper]:
    """Download qualifying open-access PDFs; set `local_path` on each; return them.
    Falls back to a small .link.txt when a URL is a landing page, not a PDF."""
    out_dir = Path(config.DOWNLOAD_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    sess = requests.Session()
    sess.headers.update({"User-Agent": "research-radar/0.1 (open-access PDF fetch)"})

    got: list[Paper] = []
    for p in papers:
        if len(got) >= config.DOWNLOAD_MAX:
            break
        if not p.is_oa or not p.pdf_url or not _wanted_pdf(p):
            continue

        stem = f"{p.date}__score{p.score}__{_safe(p.title)}__{p.short_id}"
        pdf = out_dir / f"{stem}.pdf"
        if pdf.exists():
            p.local_path = f"{out_dir.name}/{pdf.name}"
            got.append(p)
            continue
        try:
            r = sess.get(p.pdf_url, timeout=60, allow_redirects=True)
            r.raise_for_status()
            if r.content[:5] == b"%PDF-" or "application/pdf" in r.headers.get("content-type", "").lower():
                pdf.write_bytes(r.content)
                p.local_path = f"{out_dir.name}/{pdf.name}"
            else:
                link = out_dir / f"{stem}.link.txt"
                link.write_text(p.pdf_url + "\n", encoding="utf-8")
                p.local_path = f"{out_dir.name}/{link.name}"
            got.append(p)
        except Exception as e:  # best-effort — one failure shouldn't stop others
            print(f"[download] {p.short_id} failed: {e}")
    return got


# --- Pipeline ----------------------------------------------------------------

def run(dry_run: bool = False, download: bool = False) -> str:
    store = SeenStore()

    # A paper can match several streams (an ontology author's paper also lands in
    # the semantic-web topic). Keep one entry per paper (the highest-scoring), but
    # remember every reason it was caught.
    best: dict[str, Paper] = {}
    reasons: dict[str, list[str]] = {}

    for stream in config.STREAMS:
        try:
            papers = fetch_stream(stream, config.LOOKBACK_DAYS, config.PER_PAGE)
        except Exception as e:  # one stream failing shouldn't sink the run
            print(f"[warn] stream {stream.key} failed: {e}")
            continue
        for p in papers:
            if not store.is_new(p.short_id):
                continue
            p.score, p.why = relevance.assess(p, stream)
            if p.score < config.MIN_SCORE:
                continue
            p.matched = config.capture_reason(p, stream)
            reasons.setdefault(p.short_id, []).append(p.matched)
            kept = best.get(p.short_id)
            if kept is None or p.score > kept.score:
                best[p.short_id] = p

    # Reward papers that trip several of your criteria, and list every reason.
    for sid, p in best.items():
        hits = list(dict.fromkeys(reasons.get(sid, [p.matched])))
        p.matched = "  ·  ".join(hits)
        if len(hits) > 1:
            bonus = min((len(hits) - 1) * config.MULTI_MATCH_BONUS, config.MULTI_MATCH_MAX)
            p.score += bonus
            p.why += f" · ✚ hits {len(hits)} of your criteria (+{bonus})"

    scored = sorted(best.values(), key=lambda p: (p.score, p.date), reverse=True)

    # Draft the best of EACH kind (keywords / authors / topics), not the best
    # overall, so a broad topic can't crowd out your people or key terms: up to
    # DRAFTS_PER_KIND per kind, and within topics PER_TOPIC_CAP spreads the picks
    # across different topics instead of one busy one.
    top: list[Paper] = []
    per_kind: dict[str, int] = {}
    per_topic: dict[str, int] = {}
    for p in scored:
        kind = config.stream_kind(p.stream)
        if per_kind.get(kind, 0) >= config.DRAFTS_PER_KIND:
            continue
        if kind == "topic" and per_topic.get(p.stream, 0) >= config.PER_TOPIC_CAP:
            continue
        top.append(p)
        per_kind[kind] = per_kind.get(kind, 0) + 1
        per_topic[p.stream] = per_topic.get(p.stream, 0) + 1

    picked = {p.short_id for p in top}
    rest = [p for p in scored if p.short_id not in picked]

    if download:
        got = download_oa(scored)  # sets local_path, so the report can link them
        print(f"[radar] downloaded {len(got)} open-access PDF(s) to {config.DOWNLOAD_DIR}/")

    markdown = report.render([(p, report.make_draft(p)) for p in top], rest)
    report.write_report(markdown)

    if not dry_run:
        for p in scored:
            store.mark(p.short_id)
        store.save()

    print(f"[radar] {len(scored)} new papers; {len(top)} drafted; "
          f"{'DRY RUN (state unchanged)' if dry_run else 'state saved'}")
    return markdown


def main() -> None:
    ap = argparse.ArgumentParser(description="Research Radar")
    ap.add_argument("--dry-run", action="store_true",
                    help="don't mark papers as seen (safe to re-run)")
    ap.add_argument("--download", action="store_true",
                    help="save open-access PDFs of top-scoring papers to papers/")
    ap.add_argument("--canon", action="store_true",
                    help="build the most-cited reading list (state/reading_list.md) and exit")
    args = ap.parse_args()
    if args.canon:
        report.canon_run()
        return
    run(dry_run=args.dry_run, download=args.download)


if __name__ == "__main__":
    main()
