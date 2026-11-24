"""Orchestrate one Research Radar run.

  fetch each stream -> drop seen ids -> score -> rank -> draft top N
  -> render report -> mark seen -> save state.

Flags:
  --dry-run   do everything except marking papers as seen (safe to re-run)
"""

from __future__ import annotations

import argparse

from . import config, deliver, drafter, relevance
from .openalex import Paper, fetch_stream
from .store import SeenStore


def run(dry_run: bool = False) -> str:
    store = SeenStore()

    # A paper can match several streams (e.g. an ontology author's paper also
    # lands in the semantic-web topic). Keep one entry per paper, attributed to
    # the stream that scored it highest, so it's drafted/listed only once.
    best: dict[str, Paper] = {}

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
            kept = best.get(p.short_id)
            if kept is None or p.score > kept.score:
                best[p.short_id] = p

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
    args = ap.parse_args()
    run(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
