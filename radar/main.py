"""Orchestrate one Research Radar run.

  fetch each stream -> drop seen ids -> score -> rank -> draft top N
  -> render report -> mark seen -> save state.

Flags:
  --dry-run    do everything except marking papers as seen (safe to re-run)
  --download   also save open-access PDFs (score >= DOWNLOAD_MIN_SCORE) locally
"""

from __future__ import annotations

import argparse
from pathlib import Path

from . import config, deliver, drafter, relevance
from .openalex import Paper, fetch_stream
from .store import SeenStore


def run(dry_run: bool = False, download: bool = False) -> str:
    store = SeenStore()

    # A paper can match several streams (e.g. an ontology author's paper also
    # lands in the semantic-web topic). Keep one entry per paper, attributed to
    # the stream that scored it highest, so it's drafted/listed only once.
    best: dict[str, Paper] = {}
    reasons: dict[str, list[str]] = {}  # short_id -> capture reason per match

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

    # A paper that trips several of your criteria (e.g. a watched author AND a
    # watched topic) is more clearly on-target: nudge its score up and record
    # every distinct reason it was captured.
    for sid, p in best.items():
        hits = list(dict.fromkeys(reasons.get(sid, [p.matched])))  # distinct, ordered
        p.matched = "  ·  ".join(hits)
        if len(hits) > 1:
            bonus = min((len(hits) - 1) * config.MULTI_MATCH_BONUS,
                        config.MULTI_MATCH_MAX)
            p.score += bonus
            p.why += f" · ✚ hits {len(hits)} of your criteria (+{bonus})"

    scored: list[Paper] = list(best.values())
    # Highest score first, then newest.
    scored.sort(key=lambda p: (p.score, p.date), reverse=True)

    # Draft the highest-quality papers first (scored is already best-first),
    # but cap how many come from any single stream so one busy topic can't take
    # every slot.
    PER_STREAM_CAP = 2
    top: list[Paper] = []
    per_stream: dict[str, int] = {}
    for p in scored:
        if len(top) >= config.MAX_DRAFTS:
            break
        if per_stream.get(p.stream, 0) >= PER_STREAM_CAP:
            continue
        top.append(p)
        per_stream[p.stream] = per_stream.get(p.stream, 0) + 1

    picked = {p.short_id for p in top}
    rest = [p for p in scored if p.short_id not in picked]

    # Optional: save open-access PDFs of the top-scoring papers locally. This
    # sets `local_path` on the Paper objects, so the report can link to them.
    if download:
        from . import download as dl
        got = dl.download_oa(scored, Path(config.DOWNLOAD_DIR),
                             config.DOWNLOAD_MIN_SCORE, config.DOWNLOAD_MAX,
                             config.DOWNLOAD_PREPRINT_MIN_SCORE,
                             config.PREPRINT_TOPICS, config.PREPRINT_STREAMS)
        print(f"[radar] downloaded {len(got)} open-access PDF(s) "
              f"(score >= {config.DOWNLOAD_MIN_SCORE}) to {config.DOWNLOAD_DIR}/")

    drafts = [(p, drafter.make_draft(p)) for p in top]
    markdown = deliver.render(drafts, rest)
    deliver.write_file(markdown)

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
    args = ap.parse_args()
    run(dry_run=args.dry_run, download=args.download)


if __name__ == "__main__":
    main()
